#!/usr/bin/env python3
"""US Small-Cap DD Scanner Architecture PDF — v4: deterministic layout, no overlaps.

Strategy: drop ReportLab Paragraph for body content. Use plain drawString with
manual word-wrap and explicit y-position tracking. Every element returns a
new y; we always advance downward; no element trusts another's wrapping math.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas
import os, datetime

OUT = '/home/openclaw/.openclaw/workspace/us_smallcap_dd_architecture_v4.pdf'
W, H = A4

NAVY = HexColor('#0a1929')
BLUE = HexColor('#1d9bf0')
RED = HexColor('#e63946')
ORANGE = HexColor('#f4a261')
GREEN = HexColor('#2a9d8f')
GREY = HexColor('#5a6c7d')
LIGHT = HexColor('#f0f4f8')
WHITE = white

MARGIN = 1.5 * cm
CW = W - 2 * MARGIN  # content width
BOTTOM = 1.6 * cm    # don't draw below this
SECTION_GAP = 6 * mm # gap below section header
LINE_GAP = 1.5 * mm  # gap between text lines


def wrap_text(c: canvas.Canvas, text: str, font: str, size: float, max_width: float) -> list[str]:
    """Word-wrap text to fit within max_width using the canvas font metrics."""
    if not text:
        return [""]
    words = text.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        candidate = (cur + " " + w).strip()
        if c.stringWidth(candidate, font, size) <= max_width:
            cur = candidate
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines if lines else [""]


def draw_text(c: canvas.Canvas, text: str, x: float, y: float,
              font: str = 'Helvetica', size: float = 8.5, color=black,
              max_width: float | None = None, leading: float | None = None) -> float:
    """Draw text (single or multiple wrapped lines). Returns y AFTER the last line.
    y is the BASELINE of the first line. Each subsequent line drops by `leading`."""
    if leading is None:
        leading = size + 3
    c.setFont(font, size)
    c.setFillColor(color)
    width = max_width if max_width is not None else CW
    lines = wrap_text(c, text, font, size, width)
    cur_y = y
    for line in lines:
        c.drawString(x, cur_y, line)
        cur_y -= leading
    # cur_y is one leading past the last line; pull back so caller's "next y"
    # is just below the last line.
    return cur_y + (leading - size)  # leaves a small gap; consistent


def draw_bullet(c: canvas.Canvas, text: str, x: float, y: float,
                font: str = 'Helvetica', size: float = 8, color=black,
                max_width: float | None = None) -> float:
    """Bullet circle + wrapped text. Returns y after."""
    leading = size + 3
    c.setFillColor(BLUE)
    # Circle slightly above first baseline
    c.circle(x + 1.5*mm, y + size*0.35, 1.1*mm, fill=1, stroke=0)
    text_x = x + 4.5*mm
    width = (max_width if max_width is not None else CW) - 4.5*mm
    return draw_text(c, text, text_x, y, font, size, color, width, leading)


def section(c: canvas.Canvas, title: str, y: float) -> float:
    """Section header with underline. Returns y `SECTION_GAP` below."""
    c.setFillColor(BLUE)
    c.setFont('Helvetica-Bold', 11)
    c.drawString(MARGIN, y, title)
    y -= 3 * mm
    c.setStrokeColor(BLUE)
    c.setLineWidth(1.2)
    c.line(MARGIN, y, MARGIN + CW, y)
    return y - SECTION_GAP


def header(c: canvas.Canvas, title: str, page_num: int) -> None:
    c.setFillColor(NAVY)
    c.rect(0, H - 1.8*cm, W, 1.8*cm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont('Helvetica-Bold', 13)
    c.drawString(MARGIN, H - 1.25*cm, title)
    c.setFont('Helvetica', 8)
    c.drawRightString(W - MARGIN, H - 1.25*cm, f"Page {page_num} of 6")


def pill(c: canvas.Canvas, x: float, y: float, text: str, color, font_size: float = 7.5) -> float:
    tw = c.stringWidth(text, 'Helvetica-Bold', font_size) + 6*mm
    c.setFillColor(color)
    c.roundRect(x, y, tw, 5.5*mm, 2*mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont('Helvetica-Bold', font_size)
    c.drawString(x + 3*mm, y + 1.7*mm, text)
    return x + tw + 3*mm


def footer(c: canvas.Canvas) -> None:
    c.setFillColor(GREY)
    c.setFont('Helvetica-Oblique', 7)
    c.drawString(MARGIN, 8*mm, "GitHub: sashas617-cmyk/us-smallcap-dd  |  Adapted from maulavista/stock-due-diligence-skill")
    c.drawRightString(W - MARGIN, 8*mm, f"Generated {datetime.datetime.now().strftime('%d %b %Y')}")


c = canvas.Canvas(OUT, pagesize=A4)


# ═══════════════════════════════════════════════════════════
# PAGE 1: TITLE
# ═══════════════════════════════════════════════════════════
c.setFillColor(NAVY)
c.rect(0, 0, W, H, fill=1, stroke=0)
c.setFillColor(BLUE)
c.rect(0, H*0.38, W, 2*mm, fill=1, stroke=0)

c.setFillColor(white)
c.setFont('Helvetica-Bold', 26)
c.drawCentredString(W/2, H*0.72, "US Small-Cap DD Scanner")
c.setFont('Helvetica-Bold', 22)
c.drawCentredString(W/2, H*0.72 - 12*mm, "Pipeline Architecture")

c.setFillColor(HexColor('#94a3b8'))
c.setFont('Helvetica', 12)
c.drawCentredString(W/2, H*0.72 - 24*mm, "Due Diligence Framework + Russell 2000 Screener")
c.setFont('Helvetica', 10)
c.drawCentredString(W/2, H*0.72 - 31*mm, "Adapted from maulavista/stock-due-diligence-skill")

c.setFillColor(HexColor('#64748b'))
c.setFont('Helvetica', 9)
c.drawCentredString(W/2, 1.5*cm, "6 pages  |  Data sources: FMP /stable/, Polygon, Unusual Whales, SEC EDGAR")
c.showPage()


# ═══════════════════════════════════════════════════════════
# PAGE 2: Pipeline Overview
# ═══════════════════════════════════════════════════════════
header(c, "Pipeline Overview", 2)
y = H - 2.5*cm

y = section(c, "Two Products", y)

# Product 1
c.setFont('Helvetica-Bold', 9.5)
c.setFillColor(NAVY)
c.drawString(MARGIN, y, "1. dd_scan.py — Individual Ticker DD")
y -= 5*mm
for item in [
    "Input: 1-10 ticker symbols (e.g. NBIS APLD CLSK)",
    "6-layer due diligence framework per ticker",
    "Output: DEEP_VALUE / VALUE_TRAP / NOT_INVESTABLE verdict",
    "Use: daily cron or ad-hoc analysis",
]:
    y = draw_bullet(c, item, MARGIN + 2*mm, y, max_width=CW - 4*mm)
    y -= LINE_GAP

y -= 4*mm

# Product 2
c.setFont('Helvetica-Bold', 9.5)
c.setFillColor(NAVY)
c.drawString(MARGIN, y, "2. russell_screener.py — Universe Screener")
y -= 5*mm
for item in [
    "Input: Russell 2000 holdings (iShares IWM ETF CSV)",
    "Phase 1: Filter by value metrics (P/E, P/B, FCF yield, debt)",
    "Phase 2: Full 6-layer DD on top 20 candidates",
    "Output: Ranked list with composite scores + verdicts",
    "Use: weekly cron for new value opportunities",
]:
    y = draw_bullet(c, item, MARGIN + 2*mm, y, max_width=CW - 4*mm)
    y -= LINE_GAP

y -= 6*mm

y = section(c, "Data Sources (all verified working)", y)

data_sources = [
    ("FMP /stable/", GREEN, "Profile, quote, financials, metrics, ratios (PRIMARY)"),
    ("Polygon.io", GREEN, "Prices, details, options contracts (PRIMARY)"),
    ("Unusual Whales", GREEN, "Max pain, option flow, sector ETFs (PRIMARY)"),
    ("SEC EDGAR", GREEN, "10-K/10-Q, CIK lookup, XBRL facts (FREE)"),
    ("Finviz", ORANGE, "Short float fallback (FALLBACK)"),
]
for name, color, desc in data_sources:
    pill(c, MARGIN, y - 1.5*mm, name, color, 7)
    c.setFont('Helvetica', 8)
    c.setFillColor(NAVY)
    c.drawString(MARGIN + 30*mm, y, desc)
    y -= 7*mm

y -= 2*mm
y = section(c, "API Key: FMP Endpoint Base URL", y)

# Warning red box
c.setFillColor(HexColor('#fef2f2'))
c.roundRect(MARGIN, y - 9*mm, CW, 9*mm, 2*mm, fill=1, stroke=0)
c.setFillColor(RED)
c.setFont('Helvetica-Bold', 9)
c.drawString(MARGIN + 3*mm, y - 5.5*mm, "/api/v3/ is LEGACY — returns 403 Forbidden.")
y -= 12*mm

# Success green box
c.setFillColor(HexColor('#f0fdf4'))
c.roundRect(MARGIN, y - 9*mm, CW, 9*mm, 2*mm, fill=1, stroke=0)
c.setFillColor(GREEN)
c.setFont('Helvetica-Bold', 9)
c.drawString(MARGIN + 3*mm, y - 5.5*mm, "/stable/ is CURRENT — returns 200 OK. All scripts use /stable/")
y -= 14*mm

y = section(c, "Output Formats", y)
for item in [
    "JSON: structured data (dd_results/{date}.json, {date}_screener.json)",
    "Excel: formatted .xlsx with color-coded verdicts (via json_to_xlsx.py)",
]:
    y = draw_bullet(c, item, MARGIN + 2*mm, y, size=8.5, max_width=CW - 4*mm)
    y -= LINE_GAP

footer(c)
c.showPage()


# ═══════════════════════════════════════════════════════════
# PAGE 3: Screener Filters & Scoring
# ═══════════════════════════════════════════════════════════
header(c, "Screener Filters & Scoring", 3)
y = H - 2.5*cm

y = section(c, "Phase 1: Screener Filters (must pass ALL)", y)

filters = [
    ("Market Cap", "$50M — $10B", "True small/mid cap"),
    ("P/E", "< 15 (or fwd P/E < 12)", "Cheap on earnings"),
    ("P/B OR P/FCF", "< 1.5 OR < 15", "At least one value metric"),
    ("Debt/Equity", "< 2.0", "Not overleveraged"),
    ("Current Ratio", "> 1.0", "Can cover short-term obligations"),
    ("Revenue YoY", "> 0%", "Not shrinking"),
    ("Sector Exclude", "Biotech with no revenue", "Pre-revenue = lottery"),
    ("Short Float", "< 15%", "Avoid crowded shorts"),
]
col_x1 = MARGIN
col_x2 = MARGIN + 38*mm
col_x3 = MARGIN + 88*mm
c.setFont('Helvetica-Bold', 7.5)
c.setFillColor(GREY)
c.drawString(col_x1, y, "METRIC")
c.drawString(col_x2, y, "THRESHOLD")
c.drawString(col_x3, y, "RATIONALE")
y -= 2.5*mm
c.setStrokeColor(HexColor('#e2e8f0'))
c.line(MARGIN, y, MARGIN + CW, y)
y -= 4*mm

for metric, threshold, rationale in filters:
    c.setFont('Helvetica-Bold', 8)
    c.setFillColor(NAVY)
    c.drawString(col_x1, y, metric)
    c.setFont('Helvetica', 7.5)
    c.drawString(col_x2, y, threshold)
    c.setFillColor(GREY)
    c.drawString(col_x3, y, rationale)
    y -= 5*mm

y -= 3*mm
y = section(c, "Composite Value Score Formula", y)

weights = [
    ("FCF Yield (FCF / Market Cap)", "30%", "Higher = cheaper"),
    ("Earnings Yield (E/P)", "20%", "Higher = cheaper"),
    ("P/B Discount vs Sector Median", "20%", "Cheaper than peers"),
    ("Debt/EBITDA (inverse)", "15%", "Lower leverage = better"),
    ("ROE", "15%", "Higher = better"),
]
for metric, weight, note in weights:
    pill(c, MARGIN, y - 1.5*mm, weight, BLUE, 7.5)
    c.setFillColor(NAVY)
    c.setFont('Helvetica', 8)
    c.drawString(MARGIN + 20*mm, y, metric)
    c.setFillColor(GREY)
    c.setFont('Helvetica-Oblique', 7.5)
    c.drawRightString(MARGIN + CW, y, note)
    y -= 6*mm

y -= 2*mm
y = section(c, "Phase 2: 6-Layer DD (applied to top 20)", y)

layers = [
    ("L1", GREEN, "Business Quality", "Moat, customer concentration, pricing power"),
    ("L2", BLUE, "Financial Performance", "5-year revenue/margin/EPS trends"),
    ("L3", ORANGE, "Cash Flow Reality", "FCF/NI, interest coverage, capex vs OCF"),
    ("L4", RED, "Debt & Capital Structure", "Net Debt/EBITDA, maturity, convertibles"),
    ("L5", HexColor('#7c3aed'), "Ownership & Governance", "13F, Form 4, dual-class, dilution"),
    ("L6", HexColor('#0891b2'), "Valuation", "P/E, P/FCF, EV/EBITDA, Altman Z, Piotroski F"),
]
for layer_id, color, name, desc in layers:
    pill(c, MARGIN, y - 1.5*mm, layer_id, color, 7)
    c.setFont('Helvetica-Bold', 8)
    c.setFillColor(NAVY)
    c.drawString(MARGIN + 14*mm, y, name)
    c.setFillColor(GREY)
    c.setFont('Helvetica', 7.5)
    c.drawRightString(MARGIN + CW, y, desc)
    y -= 6*mm

footer(c)
c.showPage()


# ═══════════════════════════════════════════════════════════
# PAGE 4: Debt Scores, Governance, Sector Benchmarks
# ═══════════════════════════════════════════════════════════
header(c, "DD Framework Details", 4)
y = H - 2.5*cm

y = section(c, "Debt Quality Score (Layer 4)", y)
debt_scores = [
    ("Clean", GREEN, "Net Debt/EBITDA < 2x, long-dated maturity, fixed rate, no FX mismatch"),
    ("Elevated", BLUE, "Net Debt/EBITDA 2-3x, some short-term concentration, ICR 2-3x"),
    ("Stressed", ORANGE, "Net Debt/EBITDA 3-4x, >30% current maturities, ICR < 2x"),
    ("Distress", RED, "Net Debt/EBITDA > 4x, >50% current maturities, going concern"),
]
for label, color, desc in debt_scores:
    pill(c, MARGIN, y - 1.5*mm, label, color, 7)
    c.setFont('Helvetica', 7.5)
    c.setFillColor(NAVY)
    # Wrap long descriptions
    lines = wrap_text(c, desc, 'Helvetica', 7.5, CW - 24*mm)
    for j, line in enumerate(lines):
        c.drawString(MARGIN + 24*mm, y - j*3.5*mm, line)
    y -= max(6*mm, len(lines)*3.5*mm + 2*mm)

y -= 2*mm
y = section(c, "Governance Red Flags (Layer 5)", y)
flags_data = [
    ("0 red flags", GREEN, "Acceptable governance"),
    ("1-2 red flags", BLUE, "Elevated caution, valuation discount required"),
    ("3-4 red flags", ORANGE, "Value trap likely, requires extraordinary discount"),
    ("5+ red flags", RED, "Uninvestable regardless of price"),
]
for flag, color, desc in flags_data:
    pill(c, MARGIN, y - 1.5*mm, flag, color, 7)
    c.setFont('Helvetica', 8)
    c.setFillColor(NAVY)
    c.drawString(MARGIN + 30*mm, y, desc)
    y -= 6*mm

y -= 2*mm
y = section(c, "US Sector Benchmarks", y)
sectors = [
    ("Semiconductors", "Gross >55%, Net >15%, FCF >10%, Debt/EBITDA <3x"),
    ("AI / Cloud Infra", "Gross >50%, Net >10%, FCF >8%, Rev growth >20%"),
    ("Crypto Miners", "Gross >30%, Watch FCF carefully, Debt/EBITDA <2x"),
    ("Growth Tech", "Gross >60%, Net >0%, FCF >5%, Rev growth >15%"),
    ("Small-cap Biotech", "Pre-revenue OK if cash > 2yr burn, check dilution"),
]
for sector, desc in sectors:
    c.setFont('Helvetica-Bold', 7.5)
    c.setFillColor(NAVY)
    c.drawString(MARGIN, y, sector)
    c.setFont('Helvetica', 7.5)
    c.setFillColor(GREY)
    c.drawString(MARGIN + 38*mm, y, desc)
    y -= 5*mm

y -= 3*mm
y = section(c, "Verdict Output Format", y)

verdict_lines = [
    "TICKER: [DEEP_VALUE / VALUE_TRAP / NOT_INVESTABLE]",
    "Business quality: [1-2 sentences]",
    "Financial trend: [1-2 sentences]",
    "Cash flow reality: [1-2 sentences]",
    "Debt: [1-2 sentences, Score: Clean/Elevated/Stressed/Distress]",
    "Governance risk: [1-2 sentences, red flag count]",
    "Valuation: [key metrics + risk/reward]",
    "One-line summary: [the plain-English answer]",
    "Conditions for re-evaluation: [what would need to change]",
]
line_h = 4*mm
box_h = (len(verdict_lines) + 1) * line_h + 3*mm
c.setFillColor(LIGHT)
c.roundRect(MARGIN, y - box_h, CW, box_h, 2*mm, fill=1, stroke=0)
c.setStrokeColor(BLUE)
c.setLineWidth(0.5)
c.roundRect(MARGIN, y - box_h, CW, box_h, 2*mm, fill=0, stroke=1)
c.setFont('Helvetica-Bold', 8)
c.setFillColor(NAVY)
c.drawString(MARGIN + 3*mm, y - 4*mm, "Verdict format per ticker:")
for i, line in enumerate(verdict_lines):
    c.setFont('Helvetica', 7.5)
    c.setFillColor(NAVY)
    c.drawString(MARGIN + 5*mm, y - 9*mm - i*line_h, line)

footer(c)
c.showPage()


# ═══════════════════════════════════════════════════════════
# PAGE 5: Cron Schedule & API Reference
# ═══════════════════════════════════════════════════════════
header(c, "Cron Schedule & API Reference", 5)
y = H - 2.5*cm

y = section(c, "Daily Cron Schedule", y)
crons = [
    ("06:00 ET / 11:00 London", "russell_screener --top 20", "Weekly value scan"),
    ("06:00 ET / 11:00 London", "dd_scan --watchlist", "DD on watchlist tickers"),
    ("09:30 ET / 14:30 London", "market-monitor", "US session (existing)"),
]
for time, cmd, desc in crons:
    c.setFont('Helvetica-Bold', 8)
    c.setFillColor(NAVY)
    c.drawString(MARGIN, y, time)
    c.setFont('Courier', 7.5)
    c.drawString(MARGIN + 50*mm, y, cmd)
    c.setFont('Helvetica', 7.5)
    c.setFillColor(GREY)
    c.drawRightString(MARGIN + CW, y, desc)
    y -= 6*mm

y -= 2*mm
y = section(c, "FMP /stable/ Endpoint Reference", y)

endpoints = [
    ("/stable/profile?symbol=T", "Profile, market cap, sector"),
    ("/stable/quote?symbol=T", "Real-time quote, price, volume"),
    ("/stable/income-statement?symbol=T", "5yr income statement"),
    ("/stable/balance-sheet-statement?symbol=T", "5yr balance sheet"),
    ("/stable/cash-flow-statement?symbol=T", "5yr cash flow"),
    ("/stable/key-metrics?symbol=T", "P/E, P/B, ROE, EV/EBITDA"),
    ("/stable/ratios-ttm?symbol=T", "TTM financial ratios"),
    ("/stable/analyst-estimates?symbol=T", "Analyst consensus"),
    ("/stable/financial-growth?symbol=T", "Growth rates"),
    ("/stable/stock-list", "All traded symbols"),
    ("/stable/stock_peers?symbol=T", "Peer companies"),
]
for ep, desc in endpoints:
    c.setFont('Courier', 7)
    c.setFillColor(BLUE)
    c.drawString(MARGIN, y, ep)
    c.setFont('Helvetica', 7.5)
    c.setFillColor(GREY)
    c.drawRightString(MARGIN + CW, y, desc)
    y -= 4.5*mm

y -= 2*mm
y = section(c, "Unusual Whales API Reference", y)
uw_endpoints = [
    ("/api/stock/{T}/max-pain", "Options max pain by expiry"),
    ("/api/stock/{T}/option-contracts", "IV, OI, volume per contract"),
    ("/api/option-trades/flow-alerts", "Unusual options flow"),
    ("/api/market/sector-etfs", "Sector ETF data"),
    ("/api/market/economic-calendar", "Upcoming econ events"),
]
for ep, desc in uw_endpoints:
    c.setFont('Courier', 7)
    c.setFillColor(BLUE)
    c.drawString(MARGIN, y, ep)
    c.setFont('Helvetica', 7.5)
    c.setFillColor(GREY)
    c.drawRightString(MARGIN + CW, y, desc)
    y -= 4.5*mm

y -= 2*mm
y = section(c, "Polygon.io (Rate Limited: 5/min)", y)
poly_endpoints = [
    ("/v2/aggs/ticker/{T}/prev", "Previous day OHLCV"),
    ("/v3/reference/options/contracts", "Options chain"),
    ("/v2/aggs/grouped/locale/us", "All stocks daily"),
]
for ep, desc in poly_endpoints:
    c.setFont('Courier', 7)
    c.setFillColor(BLUE)
    c.drawString(MARGIN, y, ep)
    c.setFont('Helvetica', 7.5)
    c.setFillColor(GREY)
    c.drawRightString(MARGIN + CW, y, desc)
    y -= 4.5*mm

footer(c)
c.showPage()


# ═══════════════════════════════════════════════════════════
# PAGE 6: Adaptation Notes
# ═══════════════════════════════════════════════════════════
header(c, "Adaptation from Original Skill", 6)
y = H - 2.5*cm

y = section(c, "What We Kept", y)
kept = [
    "6-layer DD: Business -> Financials -> Cash Flow -> Debt -> Governance -> Valuation",
    "Verdict: DEEP_VALUE / VALUE_TRAP / NOT_INVESTABLE",
    "Writing standards: no AI slop, no em dashes, real numbers only",
    "Cash flow as most important layer (FCF/NI ratio, interest coverage)",
    "P/B and EV/EBITDA mirage warnings in valuation",
    "Piotroski F-Score and Altman Z-Score",
]
for item in kept:
    if y < BOTTOM + 10*mm: break
    y = draw_bullet(c, item, MARGIN + 2*mm, y, size=8, max_width=CW - 4*mm)
    y -= LINE_GAP

y -= 4*mm
y = section(c, "What We Removed (Indonesia focus)", y)
removed = [
    "All IDX/OJK/Bahasa context (POJK, FCA board, PT structures)",
    "Emerging market governance (Indonesia, Malaysia, Vietnam, PH)",
    "Bahasa Indonesia banned words list",
    "Indonesian RPT rules and private placement exploitation",
    "Dual-currency debt focus (USD debt in local-currency earners)",
]
for item in removed:
    if y < BOTTOM + 10*mm: break
    y = draw_bullet(c, item, MARGIN + 2*mm, y, size=8, color=GREY, max_width=CW - 4*mm)
    y -= LINE_GAP

y -= 4*mm
y = section(c, "What We Added (US-specific)", y)
added_short = [
    "SEC EDGAR: 10-K/10-Q, CIK lookup, XBRL company facts",
    "13F institutional ownership + Form 4 insider detection",
    "Short interest via FMP profile + UW option flow proxy",
    "Options positioning: P/C ratio, max pain, IV rank, unusual flow",
    "Convertibles, PIPEs, ATMs, warrant overhang",
    "US benchmarks: Semis, AI/Cloud, Miners, Growth Tech, Biotech",
    "Python pipeline: dd_scan.py + russell_screener.py + json_to_xlsx.py",
    "Cron: daily DD on watchlist + weekly Russell 2000 screener",
    "JSON + Excel output with color-coded verdicts",
]
for item in added_short:
    if y < BOTTOM + 8*mm: break
    y = draw_bullet(c, item, MARGIN + 2*mm, y, size=8, max_width=CW - 4*mm)
    y -= LINE_GAP

footer(c)
c.showPage()
c.save()
print(f"PDF saved: {OUT}")
print(f"Size: {os.path.getsize(OUT)} bytes")
