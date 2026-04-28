# US Small-Cap Debt and Dilution Patterns

Use this file to analyze capital structure traps in US-listed small and mid-cap equities. The common equity is only worth what remains after debt, converts, preferred stock, warrants, earnouts, lease obligations, and future dilution. In weak small-caps, the real business is often selling securities.

---

## 1. Capital Structure Map

Build the capital stack from the latest 10-Q, 10-K, 8-Ks, S-3, S-1 resale filings, and prospectus supplements.

Required table:

| Claim | Amount / Shares | Price / Strike | Maturity / Expiry | Security / Priority | Cash Cost | Dilution Impact |
|-------|-----------------|----------------|-------------------|---------------------|-----------|-----------------|
| Cash | | | | | | |
| Revolver | | | | | | |
| Term loan | | | | | | |
| High-yield notes | | | | | | |
| Convertible notes | | | | | | |
| Preferred stock | | | | | | |
| PIPE shares | | | | | | |
| Warrants | | | | | | |
| Earnouts | | | | | | |
| Options / RSUs | | | | | | |
| ATM remaining capacity | | | | | | |

Always reconcile:

- Basic shares outstanding.
- Diluted shares from the latest 10-Q.
- Treasury stock method if options and warrants are in the money.
- If-converted shares for converts and preferred stock.
- Earnout shares and sponsor shares for de-SPAC companies.
- Shares registered but not yet sold under S-3, S-1, or ATM programs.

---

## 2. High-Yield Bonds and Secured Notes

Small-cap high-yield debt can be survivable if maturities are long and the business throws off cash. It becomes toxic when the company has negative FCF and near-term maturities.

Check:

- Principal amount.
- Coupon, cash versus PIK interest.
- Maturity date and call schedule.
- Secured or unsecured status.
- Collateral package: assets, IP, equipment, mining rigs, data centers, subsidiaries.
- Covenants: leverage, interest coverage, restricted payments, asset sales, debt incurrence.
- Trading price and yield if bonds are publicly quoted.
- Rating actions or withdrawn ratings.
- Make-whole provisions and change-of-control puts.

Red flags:

- Notes trade below 80 cents on the dollar while equity still prices in growth.
- Secured notes cover the assets that bulls use for sum-of-parts valuation.
- PIK interest grows the claim faster than the business.
- Maturity wall inside 24 months with negative FCF.
- Company issues equity to pay interest or retire debt at distressed prices.

Interpretation:

- Debt trading at distressed levels is a market signal. Equity holders are last in line.
- A low market cap against large debt is not hidden upside unless asset value clearly exceeds debt and liquidation costs.

---

## 3. Convertible Notes

Converts are common in small-cap tech, biotech, miners, and AI infrastructure. They look cheaper than straight debt but sell future upside.

Extract:

- Principal amount.
- Coupon.
- Maturity.
- Initial conversion price and conversion rate.
- Conversion premium at issuance.
- Settlement method: cash, shares, or combination.
- Capped call or hedge transaction.
- Make-whole table.
- Fundamental change repurchase rights.
- Anti-dilution adjustments.
- Conversion price resets or ratchets.
- Holder put rights.

Basic dilution math:

```text
If-converted shares = principal amount / conversion price
Dilution percentage = if-converted shares / (basic shares + if-converted shares)
```

Example:

- $150 million principal.
- $5.00 conversion price.
- Basic shares: 80 million.
- If-converted shares: 30 million.
- Dilution: 30 / (80 + 30) = 27.3%.

For multiple converts, compute each tranche separately and sum the shares. If conversion prices are below current price, treat dilution as real. If conversion prices are above current price but the company needs refinancing, treat dilution as potential.

Capped call treatment:

- A capped call can reduce dilution between the conversion price and cap price.
- It does not eliminate debt maturity risk.
- Check the cap price and whether the company paid cash upfront for the hedge.
- Do not assume capped calls matter if the stock trades far below the conversion price.

Red flags:

- Conversion price near or below current share price.
- Reset clause lowers conversion price after future issuance.
- Company repeatedly exchanges old converts into new converts with lower strike and more shares.
- Convertible maturity occurs before the business reaches FCF breakeven.
- Make-whole or fundamental-change provisions give convert holders most takeover upside.

---

## 4. PIPE Deals

PIPE means private investment in public equity. It can be legitimate rescue capital or structured extraction from public holders.

Extract from 8-K, securities purchase agreement, and registration rights agreement:

- Buyer names and affiliations.
- Common shares or preferred shares issued.
- Purchase price versus prior close and VWAP.
- Warrant coverage.
- Warrant strike, expiry, cashless exercise.
- Registration rights and filing deadline.
- Lock-up or leak-out restrictions.
- Board seats or consent rights.
- Most-favored-nation clauses.
- Reset or full-ratchet anti-dilution.

PIPE dilution math:

```text
New share dilution = new PIPE shares / (pre-PIPE shares + new PIPE shares)
Warrant dilution = warrant shares / (post-PIPE shares + warrant shares)
Total potential dilution = (PIPE shares + warrant shares) / (pre-PIPE shares + PIPE shares + warrant shares)
```

Example:

- Pre-PIPE shares: 50 million.
- PIPE shares: 20 million.
- Warrants: 20 million.
- Total potential shares: 90 million.
- Potential dilution: 40 / 90 = 44.4%.

Red flags:

- PIPE priced more than 15% below market with full warrant coverage.
- Buyers receive registration rights allowing rapid resale.
- PIPE investors are related parties, sponsors, or lenders.
- Preferred shares carry liquidation preference and conversion rights.
- Company announces strategic capital but filing shows punitive terms.

---

## 5. ATM Offerings

ATM programs let companies sell stock into the market over time. For cash-burning small-caps, ATM capacity is a standing dilution machine.

Check:

- Sales agreement date and agent.
- Maximum gross proceeds authorized.
- Amount already sold.
- Remaining capacity.
- Average price of shares sold.
- Commission rate.
- Use of proceeds.
- Whether sales accelerated during retail price spikes.

ATM analysis:

```text
Estimated remaining shares to sell = remaining ATM capacity / current share price
Potential dilution = estimated remaining shares / (current basic shares + estimated remaining shares)
```

Adjust for liquidity. If remaining ATM capacity equals several weeks or months of normal trading volume, the overhang is real.

Red flags:

- Company sells aggressively into every rally.
- ATM proceeds fund operating losses rather than defined growth projects.
- Remaining ATM capacity is large relative to market cap.
- Company files a new shelf soon after exhausting the prior ATM.
- Management highlights cash balance without mentioning shares sold to create it.

---

## 6. Warrants

Warrants can dominate the cap table in SPACs, PIPEs, restructurings, biotech financings, and miner deals.

Extract:

- Public warrants and private warrants.
- Exercise price.
- Expiration date.
- Cash or cashless exercise.
- Redemption trigger and forced exercise provisions.
- Anti-dilution adjustments.
- Beneficial ownership blockers, often 4.99% or 9.99%.
- Registration status of underlying shares.

Warrant overhang calculation:

```text
Warrant overhang = total warrant shares / basic shares outstanding
In-the-money warrant dilution = in-the-money warrant shares / (basic shares + in-the-money warrant shares)
Cash proceeds if exercised = warrant shares x exercise price
```

Example:

- Basic shares: 60 million.
- Warrants: 18 million.
- Strike: $2.50.
- Current price: $4.00.
- Warrant overhang: 18 / 60 = 30%.
- Potential dilution: 18 / 78 = 23.1%.
- Cash proceeds if exercised: $45 million, if cash exercise is required.

Interpretation:

- In-the-money warrants cap upside because holders can sell stock or hedge.
- Out-of-the-money warrants still matter if a catalyst can push the stock above strike.
- Cashless exercise creates dilution without cash inflow.

Red flags:

- Warrant overhang above 15% of basic shares.
- Strike prices cluster near current stock price.
- Reset provisions lower strike after new financings.
- Public warrants trade cheaply while common bulls ignore dilution.

---

## 7. Preferred Stock and Structured Equity

Preferred stock can sit ahead of common while still being sold as equity financing.

Check:

- Liquidation preference.
- Dividend rate: cash, PIK, or cumulative.
- Conversion price.
- Voting rights.
- Redemption rights.
- Mandatory conversion triggers.
- Protective provisions.
- Participation rights.
- Change-of-control treatment.

Red flags:

- Preferred holders get liquidation preference plus conversion upside.
- Dividends accrue in kind, increasing the senior claim.
- Company must redeem preferred before common holders see value.
- Conversion price resets after future issuance.
- Preferred holders control financing, sale, or board decisions.

---

## 8. SPAC Earnouts and Sponsor Overhang

For de-SPAC companies, include earnout and sponsor shares in the dilution table.

Check:

- Sponsor promote shares.
- Private placement warrants.
- Earnout share count and trigger prices.
- Lock-up expiry.
- Redemption rate at closing.
- PIPE terms.
- Resale registration status.

Red flags:

- Earnout triggers start near current price, adding supply into the first real rally.
- Sponsor basis is near zero while public holders paid $10.
- High redemptions left the company short of promised cash.
- Sponsor or PIPE resale registration creates large sellable float.

---

## 9. Typical Small-Cap Capital Structure Traps

### The endless ATM trap

The company burns cash each quarter, sells stock through ATM after every promotional announcement, reports a higher cash balance, then repeats. Revenue may grow, but per-share value falls.

Signal: cash rises while share count rises faster than revenue, and FCF remains negative.

### The convert spiral

Old converts approach maturity. The company cannot repay in cash, so it exchanges into new converts with lower conversion price, more shares, or warrants. Common holders keep rolling the creditor's option.

Signal: principal stays flat or rises while conversion prices fall.

### The PIPE plus warrant trap

A weak company announces a financing as a strategic investment. Filing terms show discounted stock, full warrant coverage, registration rights, and anti-dilution. PIPE buyers get cheap optionality; public holders get the press release.

Signal: total potential dilution exceeds 25% and investors can resell quickly.

### The asset-backed growth trap

A miner, AI infrastructure company, or equipment-heavy semi company borrows against assets, then uses EBITDA before depreciation to argue leverage is safe. But capex and machine replacement consume the cash.

Signal: EV/EBITDA looks cheap while EV/FCF is negative or meaningless.

### The biotech runway trap

A company has a trial readout in nine months and cash for six months. Positive data may still be followed by dilution because the company cannot fund the next trial.

Signal: cash runway ends before or shortly after the catalyst.

---

## 10. Debt Quality Score

Assign one score and explain it with numbers.

| Score | Definition |
|-------|------------|
| Clean | Net cash or low leverage, no near-term maturity wall, no large warrant or convert overhang, funded for at least six quarters |
| Elevated | Some leverage or dilution risk, but cash runway and refinancing path are credible |
| Stressed | Negative FCF, financing need inside 18 months, meaningful convert, ATM, PIPE, or warrant overhang |
| Distress | Going concern language, covenant pressure, maturity wall, debt trading distressed, punitive financing, or common equity likely impaired |

Debt score can be worse than operating quality. A decent business with a broken capital structure can still be a value trap.
