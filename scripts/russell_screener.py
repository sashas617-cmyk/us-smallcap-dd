#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "beautifulsoup4", "tabulate"]
# ///
"""Russell 2000 cheap-stock screener + small-cap DD runner.

Primary source: FMP /stable/. Enrichment: Polygon, Unusual Whales, SEC EDGAR. Finviz is fallback only for short float.
Legacy dead endpoints are not used.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import os
import re
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import requests
from tabulate import tabulate

WORKSPACE = Path(os.path.expanduser("~/.openclaw/workspace"))
SKILL_DIR = WORKSPACE / "skills" / "us-smallcap-dd"
SCRIPT_DIR = SKILL_DIR / "scripts"
CACHE_DIR = WORKSPACE / "data" / "dd_cache"
RESULTS_DIR = WORKSPACE / "data" / "dd_results"
COMMON_DIR = WORKSPACE / "skills" / "_common"
sys.path.insert(0, str(COMMON_DIR))

try:
    from api_keys import FMP_KEY, POLYGON_KEY, UW_KEY, polygon_get  # type: ignore
    from bs4 import BeautifulSoup
except Exception as exc:  # pragma: no cover
    raise SystemExit(f"Failed to import API keys/deps from {COMMON_DIR}: {exc}")

ISHARES_R2K_CSV = "https://www.ishares.com/us/products/239710/ishares-russell-2000-etf/1467271812596.ajax?fileType=csv&fileName=IWM_holdings&dataType=fund"
SEC_TICKERS = "https://www.sec.gov/files/company_tickers.json"
UA = "OpenClaw us-smallcap-dd screener contact local-user@example.com"

# Liquid Russell-ish fallback. Not perfect, but real tickers, no fake data.
FALLBACK_R2K = """
AAOI ACIW ACMR ADTN AEHR AGYS ALGT AMBA AMN AMPH APLE ARCB ARWR ATEN ATGE AVAV AVNS
BANC BANR BBSI BE BEAM BLFS BMI BOOT BOWL BOX BRZE BUSE CALM CAMT CARG CARS CASH CBU
CCOI CECO CELH CENT CHGG CHRD CORT CRDO CRK CRMT CRNX CROX CRUS CVCO CWK CYTK DAKT DCOM
DNOW DOCN DV EAT ENPH ENSG EOSE EVCM EXTR FIZZ FLGT FORM FOUR FROG FSLY FSS FULT GIII
GOGO GPRE GTLS HAIN HBI HEES HLIT HURN IAC ICHR IESC INDB INMD IONQ IRBT ITGR JAKK JBT
KALU KLIC KNSA KSS KTOS LASR LITE LIVN LNTH LQDA LUMN MAN MATW MGNI MOD MODG MRCY MXL
MYGN NARI NATI NEOG NTCT NVAX NVCR OMCL OSIS PATK PDFS PGNY PLAB PLUG POWI PRGS PRLB
PRVA PSMT PZZA RAMP RARE RCKT RGNX RIGL RXO SAIA SANM SCSC SGH SHOO SIGI SITM SMCI SMTC
SNDX SPNS SPWR STRL SWI TDC TDOC TGTX TMDX TNDM TRIP TRMB TTEC TTGT TWI UCTT UPWK URBN
VCEL VICR VIAV VIR VSH WERN WOLF XPER ZETA ZYME AIRS ALRM AMKR ARLO AVDL AXNX AZTA BGC
BJRI BLBD BMBL BRKR BZH CARG CDNA CENX CLFD CMCO CNMD COMP CPRX CRSR CTS DFIN DIOD DNUT
ECPG EGBN ENVX EVH EXPO FCFS FIVN FLYW FRPT GERN GFF GH GMS GPOR GRPN HIMS HNI HRI HSTM
IBP IDCC IIPR IMKTA INSP IOSP IPGP IRDM JELD KAI KD KFY KREF LANC LTHM MANH MBUU MEDP
MGY MMSI MSTR MTDR MYRG NCNO NOG NOVT NPO NSIT NTRA NVST OII OLLI OPCH OSW PARR PAYO PCH
PEGA PENN PFSI PI PLMR PRCT PRDO PUMP RPD RVLV RXST SAFT SEM SFBS SHLS SKYW SLAB SNEX
SPSC SPXC SRRK STAA SUPN SYNA TBBK TPH TSEM UMBF VIRT VLY WDFC WFRD WK XPEL YOU ZD
""".split()

SP600_FALLBACK = FALLBACK_R2K[:]

_last_request = 0.0
_last_fmp = 0.0

def rate_limit() -> None:
    global _last_request
    delta = time.time() - _last_request
    if delta < 1.0:
        time.sleep(1.0 - delta)
    _last_request = time.time()

def cache_path(key: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", key)[:160]
    return CACHE_DIR / f"{safe}.json"

def load_cache(key: str, ttl_hours: float) -> Any | None:
    p = cache_path(key)
    if not p.exists():
        return None
    if datetime.now(timezone.utc) - datetime.fromtimestamp(p.stat().st_mtime, timezone.utc) > timedelta(hours=ttl_hours):
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None

def save_cache(key: str, data: Any) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path(key).write_text(json.dumps(data, default=str))

def http_json(url: str, *, cache_key: str, ttl_hours: float = 4, timeout: int = 15) -> Any | None:
    cached = load_cache(cache_key, ttl_hours)
    if cached is not None:
        return cached
    rate_limit()
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        save_cache(cache_key, data)
        return data
    except Exception as exc:
        msg = str(exc).replace(str(POLYGON_KEY), "***POLYGON_KEY***").replace(str(UW_KEY), "***UW_KEY***")
        print(f"WARN: fetch failed {cache_key}: {msg}", file=sys.stderr)
        return None


def polygon_json(url: str, params: dict[str, Any] | None = None, ttl_hours: float = 4) -> Any | None:
    params = dict(params or {})
    params["apiKey"] = POLYGON_KEY
    key = "polygon_" + hashlib.md5((url + json.dumps(params, sort_keys=True)).encode()).hexdigest()
    cached = load_cache(key, ttl_hours)
    if cached is not None:
        return cached
    try:
        r = polygon_get(url, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        save_cache(key, data)
        return data
    except Exception as exc:
        print(f"WARN: Polygon fetch failed {url}: {exc}", file=sys.stderr)
        return None

def uw_json(url: str, ttl_hours: float = 4) -> Any | None:
    key = "uw_" + hashlib.md5(url.encode()).hexdigest()
    cached = load_cache(key, ttl_hours)
    if cached is not None:
        return cached
    rate_limit()
    try:
        r = requests.get(url, headers={"Authorization": f"Bearer {UW_KEY}", "Accept": "application/json", "User-Agent": UA}, timeout=20)
        r.raise_for_status()
        data = r.json()
        save_cache(key, data)
        return data
    except Exception as exc:
        print(f"WARN: UW fetch failed {url}: {exc}", file=sys.stderr)
        return None



def fmp_json(endpoint: str, params: dict[str, Any] | None = None, ttl_hours: float = 4, aggressive: bool = False) -> Any | None:
    global _last_fmp
    params = dict(params or {})
    params["apikey"] = FMP_KEY
    key = "fmp_" + hashlib.md5((endpoint + json.dumps(params, sort_keys=True)).encode()).hexdigest()
    cached = load_cache(key, ttl_hours)
    if cached is not None:
        return cached
    min_gap = 1.0 if aggressive else 0.20
    wait = min_gap - (time.time() - _last_fmp)
    if wait > 0:
        time.sleep(wait)
    _last_fmp = time.time()
    try:
        r = requests.get(f"https://financialmodelingprep.com/stable/{endpoint.lstrip('/')}", params=params, headers={"User-Agent": UA, "Accept": "application/json"}, timeout=20)
        r.raise_for_status()
        data = r.json()
        save_cache(key, data)
        return data
    except Exception as exc:
        msg = str(exc).replace(str(FMP_KEY), "***FMP_KEY***")
        print(f"WARN: FMP fetch failed {endpoint}: {msg}", file=sys.stderr)
        return None

def first_row(x: Any) -> dict[str, Any]:
    if isinstance(x, list) and x and isinstance(x[0], dict):
        return x[0]
    if isinstance(x, dict):
        return x
    return {}

def fetch_ishares_universe() -> list[str]:
    cached = load_cache("ishares_iwm_holdings", 24)
    if cached:
        return cached
    rate_limit()
    try:
        r = requests.get(ISHARES_R2K_CSV, headers={"User-Agent": UA}, timeout=20)
        r.raise_for_status()
        lines = [ln for ln in r.text.splitlines() if ln and not ln.startswith(("Fund", "Downloaded", "The "))]
        start = next((i for i, ln in enumerate(lines) if "Ticker" in ln and "Name" in ln), 0)
        rows = csv.DictReader(lines[start:])
        tickers = []
        for row in rows:
            t = (row.get("Ticker") or row.get("Ticker ") or "").strip().upper().replace(".", "-")
            if re.fullmatch(r"[A-Z][A-Z0-9-]{0,5}", t):
                tickers.append(t)
        tickers = sorted(set(tickers))
        if len(tickers) > 500:
            save_cache("ishares_iwm_holdings", tickers)
            return tickers
    except Exception as exc:
        print(f"WARN: iShares universe failed, using fallback: {exc}", file=sys.stderr)
    return FALLBACK_R2K

def finviz_quote(ticker: str) -> dict[str, Any]:
    key = f"finviz_quote_{ticker}"
    cached = load_cache(key, 24)
    if cached is not None:
        return cached
    rate_limit()
    try:
        r = requests.get(f"https://finviz.com/quote.ashx?t={ticker}", headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        cells = [c.get_text(" ", strip=True) for c in soup.select("td.snapshot-td2, td.snapshot-td2-cp")]
        data = {}
        for i in range(0, len(cells) - 1, 2):
            data[cells[i]] = cells[i+1]
        save_cache(key, data)
        return data
    except Exception as exc:
        print(f"WARN: Finviz quote failed {ticker}: {exc}", file=sys.stderr)
        return {}

def sec_cik_map() -> dict[str, str]:
    data = http_json(SEC_TICKERS, cache_key="sec_company_tickers", ttl_hours=168) or {}
    out = {}
    if isinstance(data, dict):
        for row in data.values():
            if isinstance(row, dict) and row.get("ticker"):
                out[str(row["ticker"]).upper().replace(".", "-")] = str(row.get("cik_str", "")).zfill(10)
    return out

def sec_financials(ticker: str) -> dict[str, Any]:
    cik = sec_cik_map().get(ticker.upper())
    if not cik:
        return {}
    facts = http_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json", cache_key=f"sec_facts_{ticker}", ttl_hours=24) or {}
    sub = http_json(f"https://data.sec.gov/submissions/CIK{cik}.json", cache_key=f"sec_sub_{ticker}", ttl_hours=24) or {}
    def fact(tag: str) -> float | None:
        node = facts.get("facts", {}).get("us-gaap", {}).get(tag, {}) if isinstance(facts, dict) else {}
        vals=[]
        for arr in node.get("units", {}).values() if isinstance(node, dict) else []:
            if isinstance(arr, list): vals += [x for x in arr if isinstance(x, dict) and x.get("val") is not None]
        vals.sort(key=lambda x: (str(x.get("end", "")), str(x.get("filed", ""))), reverse=True)
        return n(vals[0].get("val")) if vals else None
    recent = sub.get("filings", {}).get("recent", {}) if isinstance(sub, dict) else {}
    forms, dates = recent.get("form", []), recent.get("filingDate", [])
    latest_10k = next((dates[i] for i, f in enumerate(forms) if f == "10-K" and i < len(dates)), None) if isinstance(forms, list) else None
    ocf = fact("NetCashProvidedByUsedInOperatingActivities")
    capex = fact("PaymentsToAcquirePropertyPlantAndEquipment")
    return {"revenue": fact("Revenues") or fact("RevenueFromContractWithCustomerExcludingAssessedTax"), "net_income": fact("NetIncomeLoss"), "equity": fact("StockholdersEquity"), "debt": fact("LongTermDebt") or fact("LongTermDebtAndFinanceLeaseObligationsCurrentAndNoncurrent"), "ocf": ocf, "capex": capex, "latest_10k": latest_10k}

def fetch_bulk_screener() -> list[dict[str, Any]]:
    # /stable/ has no stock screener. Start from stock-list, then enrich per ticker.
    # NOTE: FMP /stable/stock-list returns {symbol, companyName} — no exchangeShortName.
    # We accept all valid US tickers and filter by universe later.
    data = fmp_json("stock-list", ttl_hours=24) or []
    rows: list[dict[str, Any]] = []
    if isinstance(data, list):
        for r in data:
            if not isinstance(r, dict):
                continue
            sym = str(r.get("symbol") or "").upper().replace(".", "-")
            # Accept 1-5 char uppercase tickers (covers NASDAQ, NYSE, AMEX)
            if re.fullmatch(r"[A-Z][A-Z0-9-]{0,5}", sym):
                rows.append({"symbol": sym, "companyName": r.get("name") or r.get("companyName"), "price": r.get("price"), "exchange": r.get("exchangeShortName") or r.get("exchange") or ""})
    return rows

def fetch_available_symbols() -> list[str]:
    return [str(r.get("symbol", "")).upper() for r in fetch_bulk_screener()]

def n(x: Any) -> float | None:
    if x in (None, "", "-", "N/A"):
        return None
    try:
        if isinstance(x, str):
            x = x.replace(",", "").replace("%", "")
        v = float(x)
        return v if math.isfinite(v) else None
    except Exception:
        return None

def latest(lst: Any) -> dict[str, Any]:
    return lst[0] if isinstance(lst, list) and lst and isinstance(lst[0], dict) else {}

def yoy_growth(latest_val: float | None, prev_val: float | None) -> float | None:
    if latest_val is None or prev_val in (None, 0):
        return None
    return (latest_val - prev_val) / abs(prev_val)

@dataclass
class Candidate:
    ticker: str
    company: str | None = None
    sector: str | None = None
    industry: str | None = None
    market_cap: float | None = None
    pe: float | None = None
    forward_pe: float | None = None
    pb: float | None = None
    ps: float | None = None
    pfcf: float | None = None
    ev_ebitda: float | None = None
    debt_equity: float | None = None
    current_ratio: float | None = None
    roe: float | None = None
    profit_margin: float | None = None
    short_float: float | None = None
    inst_own: float | None = None
    revenue_growth: float | None = None
    fcf_yield: float | None = None
    earnings_yield: float | None = None
    debt_ebitda: float | None = None
    latest_10k: str | None = None
    composite_score: float = 0.0
    pass_filters: bool = False
    fail_reasons: list[str] | None = None

def enrich_ticker(ticker: str, screener_row: dict[str, Any] | None = None) -> Candidate:
    row = screener_row or {}
    tsym = ticker.upper().replace("-", ".")
    prof = first_row(fmp_json("profile", {"symbol": tsym}, 4))
    quote = first_row(fmp_json("quote", {"symbol": tsym}, 1))
    metrics = first_row(fmp_json("key-metrics", {"symbol": tsym, "period": "annual", "limit": 5}, 4))
    ratios = first_row(fmp_json("ratios-ttm", {"symbol": tsym}, 4))
    inc = first_row(fmp_json("income-statement", {"symbol": tsym, "period": "annual", "limit": 5}, 4))
    cf = first_row(fmp_json("cash-flow-statement", {"symbol": tsym, "period": "annual", "limit": 5}, 4))
    growth = first_row(fmp_json("financial-growth", {"symbol": tsym, "period": "annual", "limit": 1}, 4))
    sec = sec_financials(ticker)
    uw_mp = uw_json(f"https://api.unusualwhales.com/api/stock/{ticker}/max-pain", ttl_hours=12) or {}

    market_cap = n(quote.get("marketCap") or prof.get("marketCap") or metrics.get("marketCap"))
    pe = n(ratios.get("priceEarningsRatioTTM") or metrics.get("peRatio") or quote.get("pe"))
    forward_pe = n(quote.get("epsEstimatedNextYear"))
    pb = n(ratios.get("priceToBookRatioTTM") or metrics.get("pbRatio"))
    ps = n(ratios.get("priceToSalesRatioTTM") or metrics.get("priceToSalesRatio"))
    pfcf = n(metrics.get("pocfratio") or metrics.get("pfcfRatio"))
    debt_equity = n(ratios.get("debtEquityRatioTTM") or metrics.get("debtToEquity"))
    current_ratio = n(ratios.get("currentRatioTTM") or metrics.get("currentRatio"))
    roe = n(ratios.get("returnOnEquityTTM") or metrics.get("roe"))
    if roe is not None and roe > 1: roe /= 100
    profit_margin = n(ratios.get("netProfitMarginTTM") or inc.get("netIncomeRatio"))
    if profit_margin is not None and profit_margin > 1: profit_margin /= 100
    short_float = n(prof.get("shortFloat"))
    if short_float is not None and short_float > 1: short_float /= 100
    if short_float is None:
        fq = finviz_quote(ticker)
        short_float = n(fq.get("Short Float"))
        if short_float is not None and short_float > 1: short_float /= 100
    revenue_growth = n(growth.get("revenueGrowth") or growth.get("growthRevenue"))
    if revenue_growth is not None and revenue_growth > 1: revenue_growth /= 100
    fcf = n(cf.get("freeCashFlow"))
    if fcf is None and cf.get("operatingCashFlow") is not None and cf.get("capitalExpenditure") is not None:
        fcf = float(n(cf.get("operatingCashFlow")) or 0) + float(n(cf.get("capitalExpenditure")) or 0)
    fcf_yield = (fcf / market_cap) if fcf is not None and market_cap else ((1 / pfcf) if pfcf and pfcf > 0 else None)
    net_income = n(inc.get("netIncome")) or sec.get("net_income")
    earnings_yield = (net_income / market_cap) if net_income is not None and market_cap else (1 / pe if pe and pe > 0 else None)
    return Candidate(
        ticker=ticker, company=prof.get("companyName") or quote.get("name") or row.get("companyName"),
        sector=prof.get("sector"), industry=prof.get("industry"), market_cap=market_cap,
        pe=pe, forward_pe=forward_pe, pb=pb, ps=ps, pfcf=pfcf, ev_ebitda=n(metrics.get("enterpriseValueOverEBITDA")),
        debt_equity=debt_equity, current_ratio=current_ratio, roe=roe, profit_margin=profit_margin,
        short_float=short_float, inst_own=None, revenue_growth=revenue_growth,
        fcf_yield=fcf_yield, earnings_yield=earnings_yield, debt_ebitda=None,
        latest_10k=sec.get("latest_10k"), fail_reasons=[])

def passes(c: Candidate) -> bool:
    reasons: list[str] = []
    if not c.market_cap or not (50_000_000 <= c.market_cap <= 10_000_000_000): reasons.append("market_cap")
    if not ((c.pe is not None and 0 < c.pe < 15) or (c.forward_pe is not None and 0 < c.forward_pe < 12)): reasons.append("pe")
    if not ((c.pb is not None and 0 < c.pb < 1.5) or (c.pfcf is not None and 0 < c.pfcf < 15)): reasons.append("pb_or_pfcf")
    if c.debt_equity is None or c.debt_equity >= 2.0: reasons.append("debt_equity")
    if c.current_ratio is None or c.current_ratio <= 1.0: reasons.append("current_ratio")
    if c.revenue_growth is None or c.revenue_growth <= 0: reasons.append("revenue_growth")
    bio = f"{c.sector or ''} {c.industry or ''}".lower()
    if any(w in bio for w in ["biotechnology", "pharmaceutical", "drug"]):
        if (c.ps is None or c.ps <= 0) or (c.profit_margin is not None and c.profit_margin < -0.5):
            reasons.append("pre_revenue_biotech")
    if c.short_float is not None and c.short_float >= 0.15: reasons.append("short_float")
    c.fail_reasons = reasons
    c.pass_filters = not reasons
    return c.pass_filters

def score(c: Candidate, sector_pb_median: float | None) -> float:
    fcf = max(min((c.fcf_yield or 0) / 0.20, 1.5), -1) * 10
    ey = max(min((c.earnings_yield or 0) / 0.12, 1.5), -1) * 10
    if c.pb and sector_pb_median and sector_pb_median > 0:
        pb_disc = max(min((sector_pb_median - c.pb) / sector_pb_median, 1), -1) * 10
    else:
        pb_disc = 0
    de = c.debt_ebitda if c.debt_ebitda is not None else (c.debt_equity if c.debt_equity is not None else 3)
    debt = max(min((3 - de) / 3, 1), -1) * 10
    roe = max(min((c.roe or 0) / 0.20, 1.5), -1) * 10
    c.composite_score = round(0.30 * fcf + 0.20 * ey + 0.20 * pb_disc + 0.15 * debt + 0.15 * roe, 2)
    return c.composite_score

def dd_fallback(c: Candidate) -> dict[str, Any]:
    red_flags, catalysts = [], []
    if c.fcf_yield is None or c.fcf_yield <= 0: red_flags.append("FCF not positive on latest annual cash-flow data")
    if c.debt_equity is not None and c.debt_equity > 1.2: red_flags.append("Leverage is elevated for a small-cap value candidate")
    if c.roe is not None and c.roe < 0.08: red_flags.append("ROE below normal quality threshold")
    if c.latest_10k: catalysts.append(f"Next annual filing cycle, latest 10-K seen: {c.latest_10k}")
    if c.composite_score >= 7 and len(red_flags) <= 1:
        verdict = "DEEP_VALUE"
    elif c.composite_score >= 4:
        verdict = "VALUE_TRAP"
    else:
        verdict = "NOT_INVESTABLE"
    scores = {"business_quality": None, "financial_trend": None, "cash_flow": c.fcf_yield, "debt_quality": c.debt_equity, "governance_red_flags": len(red_flags), "valuation": c.composite_score}
    return {"dd_verdict": verdict, "dd_scores": scores, "dd_summary": f"{verdict}: cheap screen score {c.composite_score}, FCF yield {fmt_pct(c.fcf_yield)}, ROE {fmt_pct(c.roe)}, D/E {fmt(c.debt_equity)}.", "red_flags": red_flags, "catalysts": catalysts}

def run_dd(c: Candidate) -> dict[str, Any]:
    dd_path = SCRIPT_DIR / "dd_scan.py"
    if dd_path.exists():
        # Best-effort import. Unknown interface, so try common function names.
        try:
            spec = importlib.util.spec_from_file_location("dd_scan", dd_path)
            mod = importlib.util.module_from_spec(spec)  # type: ignore
            assert spec and spec.loader
            spec.loader.exec_module(mod)  # type: ignore
            for fn in ("analyze_ticker", "run_dd", "scan_ticker"):
                if hasattr(mod, fn):
                    out = getattr(mod, fn)(c.ticker)
                    if isinstance(out, dict):
                        return out
        except Exception as exc:
            print(f"WARN: dd_scan import failed for {c.ticker}, using fallback: {exc}", file=sys.stderr)
    return dd_fallback(c)

def fmt(x: Any) -> str:
    return "NA" if x is None else f"{x:.2f}" if isinstance(x, float) else str(x)

def fmt_pct(x: Any) -> str:
    return "NA" if x is None else f"{100*x:.1f}%"

def screen(universe: str) -> tuple[list[Candidate], int]:
    universe_tickers = set(fetch_ishares_universe() if universe == "r2k" else SP600_FALLBACK)
    rows = fetch_bulk_screener()
    row_by_ticker = {str(r.get("symbol", "")).upper(): r for r in rows if r.get("symbol")}
    # Intersect FMP stock-list with universe (sorted for determinism)
    if row_by_ticker:
        tickers = sorted([t for t in row_by_ticker if t in universe_tickers])
    else:
        # FMP stock-list empty — use sorted universe directly
        tickers = sorted(universe_tickers)
    cap = int(os.environ.get("RUSSELL_SCREENER_LIMIT", "0"))  # 0 = no limit, full scan
    if cap > 0:
        tickers = tickers[:cap]
    candidates: list[Candidate] = []
    for i, t in enumerate(tickers, 1):
        try:
            c = enrich_ticker(t, row_by_ticker.get(t))
            passes(c)
            candidates.append(c)
            if i % 25 == 0:
                print(f"screened {i}/{len(tickers)}...", file=sys.stderr)
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            print(f"WARN: skipping {t}: {exc}", file=sys.stderr)
    by_sector: dict[str, list[float]] = {}
    for c in candidates:
        if c.pb and c.pb > 0:
            by_sector.setdefault(c.sector or "Unknown", []).append(c.pb)
    med = {s: sorted(v)[len(v)//2] for s, v in by_sector.items() if v}
    for c in candidates:
        score(c, med.get(c.sector or "Unknown"))
    passing = sorted([c for c in candidates if c.pass_filters], key=lambda x: x.composite_score, reverse=True)
    if not passing:
        passing = sorted(candidates, key=lambda x: x.composite_score, reverse=True)
    return passing, len(candidates)

def output_item(c: Candidate, rank: int, include_dd: bool) -> dict[str, Any]:
    d = asdict(c)
    item = {
        "ticker": c.ticker, "rank": rank, "composite_score": c.composite_score,
        "pe": c.pe, "pb": c.pb, "pfcf": c.pfcf, "fcf_yield": c.fcf_yield,
        "debt_equity": c.debt_equity, "roe": c.roe, "revenue_growth": c.revenue_growth,
        "market_cap_M": round(c.market_cap / 1_000_000, 2) if c.market_cap else None,
        "sector": c.sector, "industry": c.industry, "latest_10k": c.latest_10k,
    }
    if include_dd:
        item.update(run_dd(c))
    else:
        # Always provide a verdict from screener-level data, even without full DD
        item.update(dd_fallback(c))
    return item

def print_summary(items: list[dict[str, Any]]) -> None:
    rows = []
    for x in items:
        rows.append([x["rank"], x["ticker"], x.get("sector"), x.get("market_cap_M"), x.get("composite_score"), fmt(x.get("pe")), fmt(x.get("pb")), fmt(x.get("pfcf")), fmt_pct(x.get("fcf_yield")), fmt_pct(x.get("revenue_growth")), x.get("dd_verdict", "")])
    print(tabulate(rows, headers=["#", "Ticker", "Sector", "MCap $M", "Score", "P/E", "P/B", "P/FCF", "FCF Yld", "Rev YoY", "DD"], tablefmt="github"))

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--screen-only", action="store_true")
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--universe", choices=["r2k", "sp600"], default="r2k")
    args = ap.parse_args()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    passing, screened_count = screen(args.universe)
    top = passing[: max(args.top, 0)]
    items = [output_item(c, i + 1, not args.screen_only) for i, c in enumerate(top)]
    result = {"date": datetime.now(timezone.utc).date().isoformat(), "universe": "russell_2000" if args.universe == "r2k" else "sp600", "candidates_screened": screened_count, "candidates_passing_filters": len(passing), "top_picks": items}
    out = RESULTS_DIR / f"{result['date']}_screener.json"
    out.write_text(json.dumps(result, indent=2, default=str))
    if args.summary:
        print_summary(items)
        print(f"\nSaved: {out}")
    else:
        print(json.dumps(result, indent=2, default=str))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
