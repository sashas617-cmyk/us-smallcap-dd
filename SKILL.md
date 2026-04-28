---
name: us-smallcap-dd
description: Run skeptical due diligence on US-listed small and mid-cap equities, especially semiconductors, AI and cloud infrastructure, crypto miners, growth tech, and small-cap biotech. Use when asked to analyze a US stock, detect value traps, assess dilution, short squeeze risk, options positioning, SEC governance signals, insider behavior, convertible debt, PIPEs, ATMs, warrants, SPAC history, or whether a US small-cap is DEEP VALUE, VALUE TRAP, or NOT INVESTABLE.
---

# US Small-Cap Stock Due Diligence

Use this skill to investigate US-listed small and mid-cap equities where the headline story may hide dilution, cash burn, weak governance, promotional financing, or a real mispriced asset. The output must reach one of three verdicts: **DEEP VALUE**, **VALUE TRAP**, or **NOT INVESTABLE**. Do not soften the call.

Proceed through six layers in order: Business Quality, Financial Performance, Cash Flow Reality, Debt and Capital Structure, Ownership and Governance, Valuation. Add Catalyst Assessment after valuation. For US small-caps, catalysts determine timing, but they do not rescue broken economics.

## Required Reference Files

Before writing narrative output, read `references/banned-words-en.md`. Read `references/sector-benchmarks.md` for sector ranges. Read `references/us-governance-checks.md` for SEC, insider, ownership, SPAC, poison pill, dual-class, and related-party checks. Read `references/us-debt-patterns.md` for converts, high-yield debt, PIPEs, ATMs, warrants, preferred stock, and dilution math.

## Writing Standards

Use clear professional English. No hype. No corporate filler. No invented numbers.

Rules:

- Never use em dashes. Use commas, colons, semicolons, parentheses, or separate sentences.
- Use real numbers only. If data is missing, say exactly what is missing and where you looked.
- Convert claims into measurable facts: revenue, backlog, contracted capacity, cash burn, runway, dilution, gross margin, customer concentration, FDA date, hash rate, megawatts, GPUs delivered.
- Separate fundamental value from trading setup. A squeeze candidate can still be trash.
- Avoid vague labels unless quantified. “High short interest” means little; “short interest is 28% of float with 3.6 days to cover” means something.
- Do not present snippets as facts. Fetch filings or full tables where possible.

Self-check before finalizing: banned words, em dashes, vague claims without numbers, passive voice where active works, and any stale or estimated data not labeled as such.

## Primary Data Sources

Use primary sources first, then cross-check with market data services.

SEC and company sources:

- SEC EDGAR: 10-K, 10-Q, 8-K, S-1, S-3, S-4, S-8, DEF 14A, 13D, 13G, Form 3, Form 4, Form 5, 13F, NT 10-K, NT 10-Q.
- Company investor relations: earnings releases, slide decks, transcripts, debt presentations, technical updates, FDA or clinical timelines.
- Exchange notices: Nasdaq deficiency notices, NYSE compliance warnings, reverse split approvals.

Financial tables and ownership:

- stockanalysis.com for annual and quarterly financial statements.
- macrotrends.net for long-run revenue, margins, shares, debt, and ratios.
- finviz.com for float, short float, institutional ownership, insider ownership, valuation, technicals.
- DEF 14A for share classes, board structure, pay, related-party transactions, poison pills, and voting control.

Options and positioning:

- Unusual Whales API for options flow, put/call ratio, unusual trades, dark pool, borrow and short data where available.
- Polygon.io options data for option chain, open interest, implied volatility, volume, expiries, and strike-level positioning.
- OCC or broker data where available for open interest and expiries.

Biotech sources: FDA calendars, company clinical trial pages, ClinicalTrials.gov, 10-K risk factors, press releases, and conference abstracts.

## Layer 1: Business Quality

Goal: establish what the company sells, why customers buy it, and whether the business can earn attractive returns without constant capital raises.

Find:

- Revenue model: product, service, subscription, transaction, licensing, hosting, mining rewards, milestone payments, royalties.
- Customer base: concentration, contract duration, renewal rates, churn, usage-based exposure.
- Competitive position: cost advantage, IP, switching cost, scale, regulatory exclusivity, power cost, site access, GPU supply, channel access.
- Unit economics: gross margin by segment, contribution margin, CAC payback, cost per BTC mined, revenue per megawatt, data center utilization, R&D intensity.
- Market structure: competitors, pricing power, cyclicality, barriers to entry.
- Execution dependency: fab partner, foundry allocation, power provider, hyperscaler customer, FDA decision, single trial, single token price, single exchange partner.

Sector checks:

- Semiconductors: design wins, tape-outs, foundry dependency, inventory cycle, China exposure, end-market mix, customer concentration, backlog quality.
- AI and cloud infrastructure: contracted megawatts, power cost, GPU count, utilization, customer contracts, lease terms, capex per MW, delivery schedule, hosting margin.
- Crypto miners: hash rate, fleet efficiency in J/TH, power cost per kWh, BTC production cost, HODL policy, curtailment revenue, debt secured by machines, HPC conversion credibility.
- Growth tech: net revenue retention, gross retention, ARR quality, rule of 40, stock-based compensation, sales efficiency, cohort behavior.
- Small-cap biotech: cash runway, trial phase, probability-adjusted asset value, endpoint risk, prior FDA feedback, single-asset dependence.

Red flags: unclear segment revenue, one customer above 20% without protection, growth funded by financing rather than demand, weak gross margin paired with premium claims, and hidden economics in the promoted segment.

## Layer 2: Financial Performance, 5-Year Trend

Pull at least five years of annual income statement data and the latest four quarters where available.

| Year | Revenue | Revenue Growth | Gross Margin | EBITDA Margin | Operating Margin | Net Margin | EPS | Diluted Shares |
|------|---------|----------------|--------------|---------------|------------------|------------|-----|----------------|

Assess revenue CAGR, organic versus acquired growth, margin trend, operating leverage, one-time gains, warrant fair-value adjustments, crypto asset marks, tax valuation allowance releases, and EPS versus share count.

Red flags: diluted shares up more than 25% over two years without matching per-share economics, gross margin below sector weak range, revenue growth with widening operating losses, non-cash gains driving profit, and recurring “timing” excuses.

## Layer 3: Cash Flow Reality

Goal: decide whether the business funds itself or survives by selling stock, debt, converts, warrants, or dreams.

| Year | Operating CF | Capex | Free Cash Flow | FCF Margin | Net Income | FCF/NI | SBC | Share Issuance Proceeds |
|------|--------------|-------|----------------|------------|------------|--------|-----|-------------------------|

Compute FCF margin, FCF/NI, quarterly cash burn, cash runway, maintenance versus growth capex, and working capital drag.

US small-cap adjustments:

- AI infrastructure and miners: capex is not optional if the model requires more power sites, ASICs, GPUs, transformers, or data center buildout.
- Biotech: R&D burn is the business. Runway and catalyst timing matter more than current revenue.
- SaaS: positive operating cash flow can be flattered by deferred revenue. Check billings and renewal quality.
- Semis: inventory growth ahead of demand can turn a revenue slowdown into a margin wipeout.

Red flags: FCF negative for three consecutive years outside a funded clinical-stage biotech, runway under four quarters before a major catalyst, capex commitments above cash plus committed financing, one-time working capital boost, and SBC treated like free money while share count rises.

## Layer 4: Debt and Capital Structure

Goal: map every claim ahead of common equity and every instrument that can dilute common holders. Read `references/us-debt-patterns.md` when financing complexity exists.

| Year | Cash | Total Debt | Net Debt | EBITDA | Net Debt/EBITDA | Interest Expense | Interest Coverage | Diluted Shares |
|------|------|------------|----------|--------|-----------------|------------------|-------------------|----------------|

| Instrument | Amount | Coupon/Rate | Conversion/Exercise Price | Maturity | Security | Covenants | Dilution Risk |
|------------|--------|-------------|---------------------------|----------|----------|-----------|---------------|

Check high-yield bonds, convertible notes, PIPEs, ATM offerings, warrants, preferred stock, S-3 shelf capacity, prospectus supplements, and S-8 filings.

Red flags: convert conversion price near current share price, multiple ATM takedowns into retail volume, warrant overhang above 15% of basic shares, debt maturity inside 18 months with negative FCF, PIPE investors receiving warrants and registration rights, and reverse splits followed by new issuance.

Debt Quality Score:

- Clean: net cash or Net Debt/EBITDA below 1.5x, no near-term maturity wall, no major warrant or convert overhang.
- Elevated: manageable debt or dilution risk, with funding for at least six quarters.
- Stressed: negative FCF, limited runway, convert or ATM dependency, or refinancing needed inside 18 months.
- Distress: going concern language, failed refinancing, covenant pressure, distressed debt pricing, or financing terms that transfer most upside away from common shareholders.

## Layer 5: Ownership and Governance

Goal: determine who controls the company, who is selling, who is financing it, and whether common shareholders are exit liquidity. Read `references/us-governance-checks.md` before scoring.

Review DEF 14A, Forms 3/4/5, 13D, 13G, 13F, SPAC origin filings, share classes, auditor changes, late filings, material weaknesses, restatements, SEC comment letters, and related-party deals.

Governance red flags:

- Insiders sell repeatedly while using promotional language.
- 10b5-1 plans are adopted shortly before heavy selling or bad news.
- Board compensation is high relative to revenue, cash, or market cap.
- Dual-class structure gives insiders voting control with low economic ownership.
- SPAC sponsor or PIPE investors still hold cheap shares or warrants.
- Related-party agreements are material but poorly priced or weakly disclosed.
- Auditor resigns, the company files NT 10-K or NT 10-Q, or internal controls fail repeatedly.

Governance scoring: 0 red flags is acceptable; 1-2 means discount valuation and monitor; 3-4 means value trap risk rises sharply; 5 or more means not investable unless a near-term sale, liquidation, or court-supervised outcome changes the math.

## Layer 6: Valuation

Goal: decide whether price compensates for business, cash flow, debt, governance, dilution, and timing risk.

| Metric | Value | Sector Context | Interpretation |
|--------|-------|----------------|----------------|
| Market Cap | | | |
| Enterprise Value | | | |
| P/E | | | |
| EV/Revenue | | | |
| EV/EBITDA | | | |
| P/FCF | | | |
| EV/FCF | | | |
| Price/Book | | | |
| FCF Yield | | | |
| Net Cash / Market Cap | | | |
| Revenue Growth | | | |
| Dilution, 3-year | | | |

Use `references/sector-benchmarks.md`. Do not use one multiple across all small-caps.

Valuation traps: low EV/Revenue with weak gross margin, low P/B against specialized equipment or failed clinical IP, low P/E from one-time gains, negative enterprise value when cash is committed to burn or capex, and cheap common stock with convert holders, warrants, preferred, or lenders taking the upside first.

## Options Positioning and Short Squeeze Risk

Run this section for US small-caps with listed options, high retail attention, or short interest above 10% of float.

Options checks: put/call ratio by volume and open interest, max pain by nearest monthly expiry and next catalyst expiry, IV rank or percentile, skew, unusual flow, opening versus closing trades, bid or ask side, expiry, strike, implied move, and gamma concentration near spot.

Short squeeze checks: short interest as percentage of float, days to cover, borrow cost, share availability, two-period SI trend, institutional ownership versus short interest, locked-up ownership, and upcoming catalysts.

Interpretation: bullish call flow without open-interest confirmation can be churn; high put/call into earnings can be hedging; high short interest can be correct. A squeeze setup changes timing risk; it does not make a bad business good.

## Catalyst Assessment

List dated catalysts where possible.

| Catalyst | Expected Date | Source | Bull Case Impact | Bear Case Impact | Confidence |
|----------|---------------|--------|------------------|------------------|------------|

Check earnings dates, guidance resets, investor days, product launches, FDA decisions, PDUFA dates, advisory committees, clinical readouts, contract renewals, power agreements, hosting contracts, GPU deliveries, data center energization, BTC halving effects, hashprice, lock-up expiries, warrant redemptions, convert maturities, ATM capacity, S-3 effectiveness, Nasdaq compliance deadlines, reverse split votes, and shareholder meetings.

Score each catalyst as positive asymmetric, binary, financing catalyst, or fake catalyst.

## Final Verdict Framework

Use this exact verdict label set:

- **DEEP VALUE**: FCF positive or credibly turning positive, dilution controlled, governance acceptable, valuation below realistic intrinsic value, and a catalyst can unlock value within 6-18 months.
- **VALUE TRAP**: stock looks cheap on P/E, P/B, EV/Revenue, or asset value, but cash flow, dilution, governance, or debt prevents common shareholders from earning the apparent upside.
- **NOT INVESTABLE**: common equity has no reliable path to value due to governance abuse, severe dilution, insolvency risk, broken business quality, clinical binary with poor odds, or financing terms that make common holders the product.

Inline summary format:

```text
VERDICT: [DEEP VALUE / VALUE TRAP / NOT INVESTABLE]

Business quality: [1-2 sentences with numbers]
Financial trend: [1-2 sentences with 5-year or TTM data]
Cash flow reality: [1-2 sentences with FCF, burn, runway]
Debt and capital structure: [1-2 sentences including Debt Quality Score]
Governance risk: [1-2 sentences including red flag count]
Valuation: [key metrics and whether they compensate for risk]
Options and short interest: [P/C, max pain, IV, unusual flow, SI % float, days to cover if available]
Catalysts: [dated catalysts and whether they are real or fake]

One-line summary: [plain-English answer]
Conditions for re-evaluation: [specific events or numbers that would change the verdict]
```

## Default Report Structure

If the user asks for a full report, produce a professional `.docx` report after the inline verdict. Use Arial, US Letter, one-inch margins, page numbers, navy headings, blue table headers, and alternating table rows.

Sections: Cover page, Executive Summary, Business Quality, Financial Performance, Cash Flow Reality, Debt and Capital Structure, Ownership and Governance, Valuation, Options Positioning and Short Squeeze Risk, Catalyst Assessment, Verdict and Conditions for Re-evaluation, Disclaimer.

Disclaimer: "This report is prepared for informational purposes only and does not constitute investment advice or a solicitation to buy or sell any security. The analysis is based on publicly available information and may contain errors or omissions. Readers should conduct their own due diligence before making any investment decision."

Output path for reports: `/mnt/user-data/outputs/[TICKER]_us_smallcap_dd_report.docx`.
