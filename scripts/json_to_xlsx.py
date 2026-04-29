#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["openpyxl"]
# ///
"""Add Excel (.xlsx) export to dd_scan.py and russell_screener.py outputs.

Reads the JSON results and produces formatted Excel workbooks with:
- Summary sheet (top-level verdicts and scores)
- Details sheet (per-ticker metrics)
- Conditional formatting for scores and verdicts

Usage:
  uv run scripts/json_to_xlsx.py                    # Convert today's screener results
  uv run scripts/json_to_xlsx.py --date 2026-04-29  # Specific date
  uv run scripts/json_to_xlsx.py --dd                # Convert DD scan results
  uv run scripts/json_to_xlsx.py --all              # Convert all available dates
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

RESULTS_DIR = Path(os.path.expanduser("~/.openclaw/workspace/data/dd_results"))

# Colors
NAVY = "0A1929"
BLUE = "1D9BF0"
RED_HEX = "E63946"
ORANGE_HEX = "F4A261"
GREEN_HEX = "2A9D8F"
GREY_HEX = "5A6C7D"
LIGHT_GREY = "F0F4F8"
WHITE = "FFFFFF"

# Fills
HEADER_FILL = PatternFill(start_color=NAVY, end_color=NAVY, fill_type="solid")
DEEP_VALUE_FILL = PatternFill(start_color=GREEN_HEX, end_color=GREEN_HEX, fill_type="solid")
VALUE_TRAP_FILL = PatternFill(start_color=ORANGE_HEX, end_color=ORANGE_HEX, fill_type="solid")
NOT_INVEST_FILL = PatternFill(start_color=RED_HEX, end_color=RED_HEX, fill_type="solid")
LIGHT_ROW = PatternFill(start_color=LIGHT_GREY, end_color=LIGHT_GREY, fill_type="solid")

# Fonts
HEADER_FONT = Font(name="Calibri", size=11, bold=True, color=WHITE)
TITLE_FONT = Font(name="Calibri", size=14, bold=True, color=NAVY)
BOLD_FONT = Font(name="Calibri", size=10, bold=True)
NORMAL_FONT = Font(name="Calibri", size=10)
VERDICT_FONT = Font(name="Calibri", size=10, bold=True, color=WHITE)
LINK_FONT = Font(name="Calibri", size=10, color=BLUE, underline="single")

THIN_BORDER = Border(
    left=Side(style='thin', color='D0D0D0'),
    right=Side(style='thin', color='D0D0D0'),
    top=Side(style='thin', color='D0D0D0'),
    bottom=Side(style='thin', color='D0D0D0')
)


def verdict_fill(verdict: str) -> PatternFill:
    v = (verdict or "").upper()
    if "DEEP" in v or "VALUE" in v and "TRAP" not in v:
        return DEEP_VALUE_FILL
    if "TRAP" in v:
        return VALUE_TRAP_FILL
    if "NOT" in v or "AVOID" in v:
        return NOT_INVEST_FILL
    return PatternFill(start_color=GREY_HEX, end_color=GREY_HEX, fill_type="solid")


def format_pct(val) -> str:
    if val is None or val == "N/A":
        return "N/A"
    try:
        v = float(val)
        if abs(v) < 1:
            return f"{v:.2%}"
        return f"{v:.1f}%"
    except (ValueError, TypeError):
        return str(val)


def format_num(val, decimals=2) -> str:
    if val is None or val == "N/A":
        return "N/A"
    try:
        return f"{float(val):,.{decimals}f}"
    except (ValueError, TypeError):
        return str(val)


def format_mcap(val) -> str:
    if val is None or val == "N/A":
        return "N/A"
    try:
        v = float(val)
        if v >= 1e12:
            return f"${v/1e12:.1f}T"
        if v >= 1e9:
            return f"${v/1e9:.1f}B"
        if v >= 1e6:
            return f"${v/1e6:.0f}M"
        return f"${v:,.0f}"
    except (ValueError, TypeError):
        return str(val)


def convert_screener(data: dict, output_path: Path):
    wb = Workbook()

    # ===== Summary Sheet =====
    ws = wb.active
    ws.title = "Summary"
    ws.sheet_properties.tabColor = "1D9BF0"

    # Title
    ws.merge_cells('A1:L1')
    ws['A1'] = f"Russell 2000 Value Screener — {data.get('date', 'N/A')}"
    ws['A1'].font = TITLE_FONT
    ws['A1'].alignment = Alignment(horizontal='left')

    ws['A2'] = f"Universe: {data.get('universe', 'r2k')} | Screened: {data.get('candidates_screened', 'N/A')} | Passing filters: {data.get('candidates_passing_filters', 'N/A')}"
    ws['A2'].font = Font(name="Calibri", size=9, color=GREY_HEX)

    # Headers
    headers = ["#", "Ticker", "Sector", "MCap", "Score", "P/E", "P/B", "P/FCF",
               "FCF Yield", "Debt/Eq", "ROE", "Rev YoY", "Verdict", "Summary"]
    col_widths = [4, 10, 20, 12, 8, 8, 8, 8, 10, 10, 8, 10, 14, 50]

    for col, (header, width) in enumerate(zip(headers, col_widths), 1):
        cell = ws.cell(row=4, column=col, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = THIN_BORDER
        ws.column_dimensions[get_column_letter(col)].width = width

    # Data rows
    candidates = data.get("top_picks", data.get("results", []))
    for idx, pick in enumerate(candidates, 1):
        row = idx + 4
        verdict = pick.get("dd_verdict", pick.get("verdict", ""))
        values = [
            idx,
            pick.get("ticker", ""),
            pick.get("sector", ""),
            format_mcap(pick.get("market_cap_M") or pick.get("key_metrics", {}).get("market_cap")),
            pick.get("composite_score", pick.get("rank", "")),
            format_pct(pick.get("pe") or pick.get("key_metrics", {}).get("p_e")),
            format_pct(pick.get("pb") or pick.get("key_metrics", {}).get("p_b")),
            format_pct(pick.get("pfcf") or pick.get("key_metrics", {}).get("p_fcf")),
            format_pct(pick.get("fcf_yield") or pick.get("key_metrics", {}).get("fcf_margin_latest")),
            format_pct(pick.get("debt_equity") or pick.get("key_metrics", {}).get("debt_to_equity_finviz")),
            format_pct(pick.get("roe") or pick.get("key_metrics", {}).get("roe")),
            format_pct(pick.get("revenue_growth") or pick.get("key_metrics", {}).get("revenue_cagr_5y")),
            verdict,
            pick.get("dd_summary", pick.get("one_line_summary", "")),
        ]
        for col, val in enumerate(values, 1):
            cell = ws.cell(row=row, column=col, value=val)
            cell.font = NORMAL_FONT
            cell.border = THIN_BORDER
            if idx % 2 == 0:
                cell.fill = LIGHT_ROW
            if col == 13:  # Verdict column
                cell.fill = verdict_fill(verdict)
                cell.font = VERDICT_FONT
                cell.alignment = Alignment(horizontal='center')

    # ===== Details Sheet =====
    if candidates:
        ws2 = wb.create_sheet("Details")
        ws2.sheet_properties.tabColor = "2A9D8F"

        detail_headers = ["Ticker", "Verdict", "Business Quality", "Financial Performance",
                          "Cash Flow Reality", "Debt & Capital", "Ownership & Governance",
                          "Valuation", "Red Flags", "Catalysts", "Data Quality"]
        for col, header in enumerate(detail_headers, 1):
            cell = ws2.cell(row=1, column=col, value=header)
            cell.font = HEADER_FONT
            cell.fill = HEADER_FILL
            cell.border = THIN_BORDER

        for idx, pick in enumerate(candidates, 2):
            metrics = pick.get("key_metrics", {})
            dd_scores = pick.get("dd_scores", pick.get("layer_scores", {}))
            verdict = pick.get("dd_verdict", pick.get("verdict", ""))

            values = [
                pick.get("ticker", ""),
                verdict,
                dd_scores.get("business_quality", ""),
                dd_scores.get("financial_performance", ""),
                dd_scores.get("cash_flow_reality", ""),
                dd_scores.get("debt_capital_structure", dd_scores.get("debt_quality", "")),
                dd_scores.get("ownership_governance", ""),
                dd_scores.get("valuation", ""),
                ", ".join(pick.get("red_flags", [])) if pick.get("red_flags") else "None",
                ", ".join(pick.get("catalysts", [])) if pick.get("catalysts") else "None",
                str(pick.get("data_quality", "")),
            ]
            for col, val in enumerate(values, 1):
                cell = ws2.cell(row=idx, column=col, value=val)
                cell.font = NORMAL_FONT
                cell.border = THIN_BORDER
                if col == 2:
                    cell.fill = verdict_fill(verdict)
                    cell.font = VERDICT_FONT
                    cell.alignment = Alignment(horizontal='center')

    wb.save(str(output_path))
    return output_path


def convert_dd(data: dict, output_path: Path):
    wb = Workbook()
    ws = wb.active
    ws.title = "DD Results"

    ws.merge_cells('A1:J1')
    ws['A1'] = f"Due Diligence Scan — {data.get('date', 'N/A')}"
    ws['A1'].font = TITLE_FONT

    headers = ["Ticker", "Verdict", "Business Quality", "Financial Perf", "Cash Flow",
                "Debt/Capital", "Governance", "Valuation", "Red Flags", "Summary"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.border = THIN_BORDER

    for idx, result in enumerate(data.get("results", []), 4):
        scores = result.get("layer_scores", result.get("dd_scores", {}))
        verdict = result.get("verdict", "")
        values = [
            result.get("ticker", ""),
            verdict,
            scores.get("business_quality", ""),
            scores.get("financial_performance", ""),
            scores.get("cash_flow_reality", ""),
            scores.get("debt_capital_structure", scores.get("debt_quality", "")),
            scores.get("ownership_governance", ""),
            scores.get("valuation", ""),
            ", ".join(result.get("red_flags", [])) if result.get("red_flags") else "None",
            result.get("one_line_summary", ""),
        ]
        for col, val in enumerate(values, 1):
            cell = ws.cell(row=idx, column=col, value=val)
            cell.font = NORMAL_FONT
            cell.border = THIN_BORDER
            if col == 2:
                cell.fill = verdict_fill(verdict)
                cell.font = VERDICT_FONT
    wb.save(str(output_path))
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Convert JSON DD results to formatted Excel")
    parser.add_argument("--date", help="Specific date (YYYY-MM-DD)")
    parser.add_argument("--dd", action="store_true", help="Convert DD scan results (not screener)")
    parser.add_argument("--all", action="store_true", help="Convert all available dates")
    args = parser.parse_args()

    target_date = args.date or datetime.now().strftime("%Y-%m-%d")

    if args.all:
        # Find all JSON files
        files = sorted(RESULTS_DIR.glob("*.json"))
        if not files:
            print("No JSON files found in", RESULTS_DIR)
            return
        for f in files:
            suffix = "_screener" if "screener" in f.name else ""
            out = f.with_suffix(".xlsx")
            data = json.loads(f.read_text())
            if "screener" in f.name:
                convert_screener(data, out)
            else:
                convert_dd(data, out)
            print(f"  {f.name} → {out.name}")
        return

    if args.dd:
        json_path = RESULTS_DIR / f"{target_date}.json"
        if not json_path.exists():
            json_path = RESULTS_DIR / f"{target_date}_NVDA_dd.json"
        if not json_path.exists():
            print(f"No DD file found for {target_date}")
            print(f"Available: {list(RESULTS_DIR.glob('*.json'))}")
            return
        data = json.loads(json_path.read_text())
        out = json_path.with_suffix(".xlsx")
        convert_dd(data, out)
        print(f"Saved: {out}")
    else:
        json_path = RESULTS_DIR / f"{target_date}_screener.json"
        if not json_path.exists():
            print(f"No screener file found for {target_date}")
            print(f"Available: {list(RESULTS_DIR.glob('*.json'))}")
            return
        data = json.loads(json_path.read_text())
        out = json_path.with_suffix(".xlsx")
        convert_screener(data, out)
        print(f"Saved: {out}")


if __name__ == "__main__":
    main()