#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "beautifulsoup4", "tabulate"]
# ///
"""Single-name US small/mid-cap due-diligence scan.

Uses FMP /stable/ as the primary source, with Polygon, Unusual Whales, SEC EDGAR, and Finviz short-float fallback.
Legacy dead endpoints are not used.
"""
from __future__ import annotations

import argparse, json, math, os, re, sys, time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup
from tabulate import tabulate

WORKSPACE = Path(os.path.expanduser("~/.openclaw/workspace"))
COMMON_DIR = WORKSPACE / "skills" / "_common"
sys.path.insert(0, str(COMMON_DIR))
from api_keys import FMP_KEY, POLYGON_KEY, UW_KEY, polygon_get  # type: ignore

CACHE_DIR = WORKSPACE / "data" / "dd_cache"
RESULTS_DIR = WORKSPACE / "data" / "dd_results"
SEC_TICKERS = "https://www.sec.gov/files/company_tickers.json"
UA = "OpenClaw us-smallcap-dd scanner contact local-user@example.com"
FINVIZ_UA = "Mozilla/5.0"

_last_fmp = 0.0
_last_finviz = 0.0
_last_sec = 0.0


def _cache_path(key: str) -> Path:
    return CACHE_DIR / (re.sub(r"[^A-Za-z0-9_.-]", "_", key)[:180] + ".json")


def load_cache(key: str, ttl_hours: float) -> Any | None:
    p = _cache_path(key)
    if not p.exists():
        return None
    if time.time() - p.stat().st_mtime > ttl_hours * 3600:
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def save_cache(key: str, data: Any) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _cache_path(key).write_text(json.dumps(data, default=str))


def n(x: Any) -> float | None:
    if x in (None, "", "-", "N/A"):
        return None
    try:
        if isinstance(x, str):
            x = x.strip().replace(",", "").replace("%", "")
            mult = 1.0
            if x.endswith("B"):
                mult, x = 1e9, x[:-1]
            elif x.endswith("M"):
                mult, x = 1e6, x[:-1]
            elif x.endswith("K"):
                mult, x = 1e3, x[:-1]
            v = float(x) * mult
        else:
            v = float(x)
        return v if math.isfinite(v) else None
    except Exception:
        return None


def finviz_quote(ticker: str) -> dict[str, Any]:
    global _last_finviz
    key = f"finviz_quote_{ticker.upper()}"
    cached = load_cache(key, 6)
    if cached is not None:
        return cached
    wait = 1.5 - (time.time() - _last_finviz)
    if wait > 0:
        time.sleep(wait)
    _last_finviz = time.time()
    url = f"https://finviz.com/quote.ashx?t={ticker.upper()}"
    r = requests.get(url, headers={"User-Agent": FINVIZ_UA}, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    data: dict[str, Any] = {"ticker": ticker.upper()}
    cells = [c.get_text(" ", strip=True) for c in soup.select("td.snapshot-td2, td.snapshot-td2-cp")]
    for i in range(0, len(cells) - 1, 2):
        data[cells[i]] = cells[i + 1]
    title = soup.find("title")
    if title:
        data["title"] = title.get_text(strip=True)
    save_cache(key, data)
    return data



def fmp_json(endpoint: str, params: dict[str, Any] | None = None, ttl_hours: float = 4, aggressive: bool = False) -> Any | None:
    """Fetch FMP /stable/ JSON with cache and safe throttle."""
    global _last_fmp
    params = dict(params or {})
    params["apikey"] = FMP_KEY
    url = f"https://financialmodelingprep.com/stable/{endpoint.lstrip('/')}"
    key = "fmp_" + re.sub(r"[^A-Za-z0-9]", "_", endpoint + json.dumps(params, sort_keys=True))
    cached = load_cache(key, ttl_hours)
    if cached is not None:
        return cached
    min_gap = 1.0 if aggressive else 0.20  # 1/sec aggressive, otherwise max 5/sec
    wait = min_gap - (time.time() - _last_fmp)
    if wait > 0:
        time.sleep(wait)
    _last_fmp = time.time()
    try:
        r = requests.get(url, params=params, headers={"User-Agent": UA, "Accept": "application/json"}, timeout=20)
        r.raise_for_status()
        data = r.json()
        save_cache(key, data)
        return data
    except Exception as exc:
        msg = str(exc).replace(str(FMP_KEY), "***FMP_KEY***")
        print(f"WARN: FMP failed for {endpoint}: {msg}", file=sys.stderr)
        return None

def first_row(x: Any) -> dict[str, Any]:
    if isinstance(x, list) and x and isinstance(x[0], dict):
        return x[0]
    if isinstance(x, dict):
        return x
    return {}

def fmp_bundle(ticker: str) -> dict[str, Any]:
    t = ticker.upper().replace("-", ".")
    return {
        "profile": first_row(fmp_json("profile", {"symbol": t}, 4)),
        "quote": first_row(fmp_json("quote", {"symbol": t}, 1)),
        "metrics": first_row(fmp_json("key-metrics", {"symbol": t, "period": "annual", "limit": 5}, 4)),
        "ratios": first_row(fmp_json("ratios-ttm", {"symbol": t}, 4)),
        "income": first_row(fmp_json("income-statement", {"symbol": t, "period": "annual", "limit": 5}, 4)),
        "balance": first_row(fmp_json("balance-sheet-statement", {"symbol": t, "period": "annual", "limit": 5}, 4)),
        "cashflow": first_row(fmp_json("cash-flow-statement", {"symbol": t, "period": "annual", "limit": 5}, 4)),
        "growth": first_row(fmp_json("financial-growth", {"symbol": t, "period": "annual", "limit": 1}, 4)),
    }

def polygon_json(url: str, params: dict[str, Any] | None = None, ttl_hours: float = 4) -> Any | None:
    params = dict(params or {})
    params["apiKey"] = POLYGON_KEY
    key = "polygon_" + re.sub(r"[^A-Za-z0-9]", "_", url + json.dumps(params, sort_keys=True))
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
        print(f"WARN: Polygon failed for {url}: {exc}", file=sys.stderr)
        return None


def uw_json(url: str, ttl_hours: float = 2) -> Any | None:
    key = "uw_" + re.sub(r"[^A-Za-z0-9]", "_", url)
    cached = load_cache(key, ttl_hours)
    if cached is not None:
        return cached
    try:
        r = requests.get(url, headers={"Authorization": f"Bearer {UW_KEY}", "Accept": "application/json", "User-Agent": UA}, timeout=20)
        r.raise_for_status()
        data = r.json()
        save_cache(key, data)
        return data
    except Exception as exc:
        print(f"WARN: UW failed for {url}: {exc}", file=sys.stderr)
        return None


def sec_get_json(url: str, ttl_hours: float = 24) -> Any | None:
    global _last_sec
    key = "sec_" + re.sub(r"[^A-Za-z0-9]", "_", url)
    cached = load_cache(key, ttl_hours)
    if cached is not None:
        return cached
    wait = 0.25 - (time.time() - _last_sec)
    if wait > 0:
        time.sleep(wait)
    _last_sec = time.time()
    try:
        r = requests.get(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip, deflate"}, timeout=20)
        r.raise_for_status()
        data = r.json()
        save_cache(key, data)
        return data
    except Exception as exc:
        print(f"WARN: SEC failed for {url}: {exc}", file=sys.stderr)
        return None


def cik_for_ticker(ticker: str) -> str | None:
    data = sec_get_json(SEC_TICKERS, ttl_hours=168)
    if not isinstance(data, dict):
        return None
    t = ticker.upper().replace("-", ".")
    for row in data.values():
        if isinstance(row, dict) and str(row.get("ticker", "")).upper() == t:
            return str(row.get("cik_str", "")).zfill(10)
    return None


def fact_latest(facts: dict[str, Any], tag: str) -> float | None:
    usgaap = facts.get("facts", {}).get("us-gaap", {}) if isinstance(facts, dict) else {}
    node = usgaap.get(tag, {})
    units = node.get("units", {}) if isinstance(node, dict) else {}
    vals = []
    for arr in units.values():
        if isinstance(arr, list):
            vals += [x for x in arr if isinstance(x, dict) and x.get("val") is not None and x.get("fy")]
    vals.sort(key=lambda x: (str(x.get("end", "")), str(x.get("filed", ""))), reverse=True)
    return n(vals[0].get("val")) if vals else None


def sec_financials(ticker: str) -> dict[str, Any]:
    cik = cik_for_ticker(ticker)
    if not cik:
        return {}
    sub = sec_get_json(f"https://data.sec.gov/submissions/CIK{cik}.json", ttl_hours=24) or {}
    facts = sec_get_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json", ttl_hours=24) or {}
    recent = sub.get("filings", {}).get("recent", {}) if isinstance(sub, dict) else {}
    forms = recent.get("form", []) if isinstance(recent, dict) else []
    dates = recent.get("filingDate", []) if isinstance(recent, dict) else []
    latest_10k = next((dates[i] for i, f in enumerate(forms) if f == "10-K" and i < len(dates)), None)
    return {
        "cik": cik,
        "latest_10k": latest_10k,
        "revenue": fact_latest(facts, "Revenues") or fact_latest(facts, "RevenueFromContractWithCustomerExcludingAssessedTax"),
        "net_income": fact_latest(facts, "NetIncomeLoss"),
        "assets": fact_latest(facts, "Assets"),
        "liabilities": fact_latest(facts, "Liabilities"),
        "equity": fact_latest(facts, "StockholdersEquity"),
        "cash": fact_latest(facts, "CashAndCashEquivalentsAtCarryingValue"),
        "debt": fact_latest(facts, "DebtCurrent") or 0,
        "long_term_debt": fact_latest(facts, "LongTermDebtAndFinanceLeaseObligationsCurrentAndNoncurrent") or fact_latest(facts, "LongTermDebt"),
        "operating_cash_flow": fact_latest(facts, "NetCashProvidedByUsedInOperatingActivities"),
        "capex": fact_latest(facts, "PaymentsToAcquirePropertyPlantAndEquipment"),
    }


def polygon_profile_price(ticker: str) -> dict[str, Any]:
    t = ticker.upper()
    prev = polygon_json(f"https://api.polygon.io/v2/aggs/ticker/{t}/prev", ttl_hours=1) or {}
    detail = polygon_json(f"https://api.polygon.io/v1/meta/symbols/{t}/company", ttl_hours=24) or {}
    price = None
    results = prev.get("results") if isinstance(prev, dict) else None
    if isinstance(results, list) and results:
        price = n(results[0].get("c"))
    return {"price": price, "company": detail.get("name") if isinstance(detail, dict) else None, "sector": detail.get("sector") if isinstance(detail, dict) else None, "industry": detail.get("industry") if isinstance(detail, dict) else None}


def uw_options(ticker: str) -> dict[str, Any]:
    t = ticker.upper()
    mp = uw_json(f"https://api.unusualwhales.com/api/stock/{t}/max-pain", ttl_hours=6) or {}
    contracts = uw_json(f"https://api.unusualwhales.com/api/stock/{t}/option-contracts", ttl_hours=6) or {}
    alerts = uw_json("https://api.unusualwhales.com/api/option-trades/flow-alerts?limit=200", ttl_hours=1) or {}
    relevant = []
    arr = alerts.get("data", alerts) if isinstance(alerts, dict) else alerts
    if isinstance(arr, list):
        for a in arr:
            if isinstance(a, dict) and str(a.get("ticker") or a.get("underlying_symbol") or "").upper() == t:
                relevant.append(a)
    max_pain = None
    if isinstance(mp, dict):
        d = mp.get("data", mp)
        if isinstance(d, dict):
            max_pain = n(d.get("max_pain") or d.get("maxPain") or d.get("strike"))
    return {"max_pain": max_pain, "flow_alert_count": len(relevant), "option_contract_count": len(contracts.get("data", [])) if isinstance(contracts, dict) else None}


@dataclass
class DDResult:
    ticker: str
    company: str | None
    price: float | None
    market_cap: float | None
    sector: str | None
    pe: float | None
    pb: float | None
    ps: float | None
    debt_equity: float | None
    current_ratio: float | None
    short_float: float | None
    fcf_yield: float | None
    roe: float | None
    latest_10k: str | None
    max_pain: float | None
    flow_alert_count: int
    verdict: str
    score: float
    red_flags: list[str]
    summary: str


def pct_from_finviz(v: Any) -> float | None:
    x = n(v)
    return x / 100 if x is not None else None


def analyze_ticker(ticker: str) -> dict[str, Any]:
    t = ticker.upper().replace(".", "-")
    fmp = fmp_bundle(t)
    prof, quote, metrics, ratios, inc, bal, cf = (fmp[k] for k in ("profile", "quote", "metrics", "ratios", "income", "balance", "cashflow"))
    # Finviz is fallback only for fields FMP lacks or occasionally omits, chiefly short float.
    fv: dict[str, Any] = {}
    sec = sec_financials(t)
    uw = uw_options(t)
    market_cap = n(quote.get("marketCap") or prof.get("marketCap") or metrics.get("marketCap"))
    price = n(quote.get("price") or prof.get("price"))
    pe = n(ratios.get("priceEarningsRatioTTM") or metrics.get("peRatio") or quote.get("pe"))
    pb = n(ratios.get("priceToBookRatioTTM") or metrics.get("pbRatio"))
    ps = n(ratios.get("priceToSalesRatioTTM") or metrics.get("priceToSalesRatio"))
    de = n(ratios.get("debtEquityRatioTTM") or metrics.get("debtToEquity"))
    cr = n(ratios.get("currentRatioTTM") or metrics.get("currentRatio"))
    sf = n(prof.get("shortFloat"))
    if sf is not None and sf > 1: sf = sf / 100
    if sf is None:
        fv = finviz_quote(t)
        sf = pct_from_finviz(fv.get("Short Float"))
    roe = n(ratios.get("returnOnEquityTTM") or metrics.get("roe"))
    if roe is not None and roe > 1: roe = roe / 100
    fcf = n(cf.get("freeCashFlow"))
    if fcf is None and cf.get("operatingCashFlow") is not None and cf.get("capitalExpenditure") is not None:
        fcf = float(n(cf.get("operatingCashFlow")) or 0) + float(n(cf.get("capitalExpenditure")) or 0)
    if fcf is None and sec.get("operating_cash_flow") is not None and sec.get("capex") is not None:
        fcf = float(sec["operating_cash_flow"]) - abs(float(sec["capex"]))
    fcf_yield = fcf / market_cap if fcf is not None and market_cap else None
    red = []
    if pe is None or pe <= 0: red.append("no positive P/E")
    elif pe > 25: red.append("valuation not obviously cheap on P/E")
    if de is not None and de > 2: red.append("high debt/equity")
    if cr is not None and cr < 1: red.append("current ratio below 1")
    if sf is not None and sf > 0.15: red.append("short float above 15%")
    if fcf_yield is not None and fcf_yield < 0: red.append("negative FCF yield")
    score = 0.0
    if pe and 0 < pe < 15: score += 2
    if pb and 0 < pb < 2: score += 1.5
    if ps and 0 < ps < 2: score += 1
    if fcf_yield and fcf_yield > 0.05: score += 2
    if de is not None and de < 1: score += 1
    if roe and roe > 0.10: score += 1
    if sf is not None and sf < 0.10: score += .5
    verdict = "DEEP_VALUE" if score >= 6 and len(red) <= 1 else "VALUE_TRAP" if score >= 3.5 else "NOT_INVESTABLE"
    res = DDResult(t, prof.get("companyName") or quote.get("name") or fv.get("title"), price, market_cap, prof.get("sector"), pe, pb, ps, de, cr, sf, fcf_yield, roe, sec.get("latest_10k"), uw.get("max_pain"), int(uw.get("flow_alert_count") or 0), verdict, round(score, 2), red, f"{verdict}: score {score:.1f}/9, P/E {pe}, P/B {pb}, short float {sf}, max pain {uw.get('max_pain')}.")
    d = asdict(res)
    d["dd_verdict"] = verdict
    d["dd_summary"] = res.summary
    d["red_flags"] = red
    d["source_primary"] = "FMP /stable/"
    return d

def print_summary(d: dict[str, Any]) -> None:
    print(tabulate([[d.get("ticker"), d.get("price"), d.get("market_cap"), d.get("pe"), d.get("pb"), d.get("ps"), d.get("fcf_yield"), d.get("short_float"), d.get("max_pain"), d.get("verdict")]], headers=["Ticker", "Price", "MCap", "P/E", "P/B", "P/S", "FCF Yld", "Short", "MaxPain", "Verdict"], tablefmt="github"))
    print(d.get("summary"))
    if d.get("red_flags"):
        print("Red flags: " + "; ".join(d["red_flags"]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", required=True)
    ap.add_argument("--summary", action="store_true")
    args = ap.parse_args()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = analyze_ticker(args.ticker)
    path = RESULTS_DIR / f"{datetime.now(timezone.utc).date().isoformat()}_{args.ticker.upper()}_dd.json"
    path.write_text(json.dumps(out, indent=2, default=str))
    if args.summary:
        print_summary(out)
        print(f"Saved: {path}")
    else:
        print(json.dumps(out, indent=2, default=str))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
