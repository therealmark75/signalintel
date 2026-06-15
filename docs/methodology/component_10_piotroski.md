# Component 10: Piotroski F-Score

> **STATUS: LIVE COMPONENT.** Positive weighted component in the composite.
> Reconciliation doc: describes what the code actually computes, read from
> the source bytes on 15 June 2026, not an idealised methodology.
> Source of truth: `signals/scorer.py:score_piotroski` (line 349),
> fed by `database/db.py:get_financials_enrichment_map` (line 1581),
> lookup vocabulary in `signals/line_item_keys.py:PIOTROSKI_LOOKUPS`.

## Identity

- Component name: Piotroski F-Score
- Registry key: `piotroski`
- Component number: 10
- Registry entry: `signals/components.py` (key `piotroski`, `db_column='piotroski_score'`, `introduced_version='0.13.0'`)
- Persisted column: `signal_scores.piotroski_score`

## Weight and role

- Composite weight: **0.125** (positive component).
- Effective share is 0.125 / 1.60, about 7.81 percent of the weighted composite (normaliser `total_w = 1.60`).
- Not a penalty, not a modifier.

## Inputs

- Source table: `financial_statements`.
- Columns consumed: `statement_type`, `fiscal_year`, `line_item_key`, `value`.
- Enrichment map: `get_financials_enrichment_map` (db.py:1581). Returns `{ticker: {statement_type: {fiscal_year: {line_item_key: value}}}}`. `line_item_key` is stored verbatim from yfinance in PascalCase.
- Line-item resolution: `PIOTROSKI_LOOKUPS` (line_item_keys.py:74) maps a canonical name to `(statement_type, raw_yfinance_key)`. The nine canonical lookups used are `net_income`, `total_assets`, `operating_cash_flow`, `long_term_debt`, `current_assets`, `current_liabilities`, `shares_outstanding`, `gross_profit`, `total_revenue`.
- Data origin: yfinance income statement, balance sheet, cash flow (scrapers/yahoo_scraper.py:120, statement types `INCOME`, `BALANCE`, `CASHFLOW`).

## Algorithm (from the bytes)

1. Collect all fiscal years present across every statement type for the ticker.
2. **Lock 1:** if fewer than 2 fiscal years are available, return `50.0` immediately. Change-based signals (F3, F5, F6, F7, F8, F9) need two years.
3. `y0, y1 = sorted_years[0], sorted_years[1]` where `sorted_years = sorted(all_years, reverse=True)`; y0 is the most recent year, y1 the prior year.
4. Compute up to 9 binary signals, each adding 1 to `f` only when its required inputs are present (guarded by `is not None` plus a truthy denominator where a ratio is taken):
   - **F1** ROA > 0: `net_income(y0) / total_assets(y0) > 0`
   - **F2** Operating cash flow > 0: `operating_cash_flow(y0) > 0`
   - **F3** ROA improvement: `ROA(y0) > ROA(y1)`
   - **F4** Accruals quality: `operating_cash_flow(y0) > net_income(y0)`
   - **F5** Long-term leverage decreased: `long_term_debt(y0)/total_assets(y0) < long_term_debt(y1)/total_assets(y1)`
   - **F6** Current ratio improved: `current_assets(y0)/current_liabilities(y0) > same(y1)`
   - **F7** No new dilution: `shares_outstanding(y0) <= shares_outstanding(y1)`
   - **F8** Gross margin improved: `gross_profit(y0)/total_revenue(y0) > same(y1)`
   - **F9** Asset turnover improved: `total_revenue(y0)/total_assets(y0) > same(y1)`
5. Map the integer `f` (0 to 9) to a score (literal cuts):
   - `f >= 7` to `80.0`
   - `f == 6` to `65.0`
   - `f == 5` to `50.0`
   - `f == 4` to `38.0`
   - else (`f <= 3`) to `20.0`

## NULL / missing-data handling (P5 check)

- Empty `financials` dict (ticker not yet scraped): returns 50.0. **Honours P5.**
- Fewer than 2 fiscal years: returns 50.0 (Lock 1). **Honours P5.**
- Per-signal missing line items: the individual `if ... is not None` guards mean a missing input simply does not increment `f`. See divergences: this is where partial data does NOT resolve to neutral.
- Output is always one of the five literal values; no clamp is applied (the map already bounds it).

## Output range and composite mapping

- Range: discrete set `{20.0, 38.0, 50.0, 65.0, 80.0}`, neutral midpoint 50.0.
- Enters the composite as a positively weighted term at weight 0.125.

## Known divergences / open questions

- **Partial-data downward bias (P5 tension).** Once a ticker clears Lock 1 (2+ years), every Piotroski signal whose inputs are missing simply fails to increment `f`. A ticker with two years on file but sparse line items can land at `f <= 3` to `20.0`, well below neutral, purely because data is absent rather than because fundamentals are weak. The docstring claims "Ignores: companies with < 2 years of data, treated as neutral, never penalised", but it is silent on the partial-data case past the 2-year gate, where missing inputs do drag the score down. This is the most material divergence in this component: it is the one place among the five where absent data can produce a sub-neutral score. Flagged for decision (no code change in this step).
- **Output collision at 50.0.** A genuine F-score of exactly 5 maps to 50.0, the same value used for the "insufficient history" neutral fallback. Two distinct meanings (a real middling F-score versus no-data neutral) are indistinguishable in the stored `piotroski_score`. Cosmetic for scoring, but it means the persisted value cannot by itself tell a backtest whether 50.0 meant "computed" or "skipped".
- **Year selection by string sort.** `sorted(all_years, reverse=True)` sorts `fiscal_year` as text. `fetch_financial_statements` writes `fiscal_year` as `col.strftime("%Y-%m-%d")` when the column is a datetime (yahoo_scraper.py:140), so ISO text sort equals chronological. Latent coupling to that date format, same as component 09.
