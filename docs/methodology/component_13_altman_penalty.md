# Component 13: Altman Z'' Distress Penalty

> **STATUS: LIVE PENALTY.** This is an additive penalty, NOT a positively
> weighted component. `is_penalty=True`, `weight=0.0` in the registry.
> Reconciliation doc: describes what the code actually computes, read from
> the source bytes on 15 June 2026, not an idealised methodology.
> Source of truth: `signals/scorer.py:score_altman_penalty` (line 521) and
> `compute_z_double_prime_raw` (line 477), fed by
> `database/db.py:get_financials_enrichment_map` (line 1581) plus screener
> market cap; lookup vocabulary in `signals/line_item_keys.py:ALTMAN_LOOKUPS`.

## Identity

- Component name: Altman Z'' Distress Penalty
- Registry key: `altman_penalty`
- Component number: 13
- Registry entry: `signals/components.py` (key `altman_penalty`, `db_column='altman_penalty'`, `is_penalty=True`, `weight=0.0`, `introduced_version='0.13.0'`)
- Persisted column: `signal_scores.altman_penalty`

## Weight and role

- Composite weight: **0.0**. This is a **penalty**, not a positive weighted term.
- It does NOT pass through `compute_composite`. Instead it is added additively to the composite after the weighted average, alongside the legal penalty: `c_score_raw = _clamp(raw_composite + legal_penalty + altman_pen)` (scorer.py:914). The penalty values are negative composite-point offsets, so they subtract from the 0 to 100 composite before the final clamp.
- Methodology: Altman Z'' (1995 non-manufacturing variant). Switched from classic 1968 Z in SCORING_ENGINE_VERSION 0.14.0 (18 May 2026) because the 1968 manufacturing formula penalised 62.9 percent of the universe; Z'' reduces that to 47.8 percent.

## Inputs

- Source tables: `financial_statements` (the four Z'' ratios) plus the screener market cap text (X4 numerator).
- Enrichment map: `get_financials_enrichment_map` (db.py:1581), the same `{ticker: {statement_type: {fiscal_year: {line_item_key: value}}}}` structure used by Piotroski.
- Line-item resolution: `ALTMAN_LOOKUPS` (line_item_keys.py:92): `working_capital`, `total_assets`, `retained_earnings`, `ebit`, `total_liabilities`. (`total_revenue` is also defined in ALTMAN_LOOKUPS but is unused by the Z'' path; see divergences.)
- Market cap: `row.get("market_cap")` from the screener row, parsed by `_parse_market_cap_text` (scorer.py:293), which converts text like `1.5B` to `1.5e9` using multipliers `{T: 1e12, B: 1e9, M: 1e6, K: 1e3}`, returning None on failure.
- `total_liabilities` uses `TotalLiabilitiesNetMinorityInterest` (classic Altman X4 convention preserved).

## Algorithm (from the bytes)

1. Collect all fiscal years across statement types; if none, return `0` (no penalty).
2. `y0 = max(all_years)` (most recent year).
3. Hydrate the five Z'' inputs from y0 via `ALTMAN_LOOKUPS`, plus the parsed market cap.
4. Compute Z'' via `compute_z_double_prime_raw`. It returns `None` if **any** input is None, or if `total_assets == 0` or `total_liabilities == 0` (division guard).
   - Formula: `Z'' = 6.56*x1 + 3.26*x2 + 6.72*x3 + 1.05*x4`
   - `x1 = working_capital / total_assets`
   - `x2 = retained_earnings / total_assets`
   - `x3 = ebit / total_assets`
   - `x4 = market_cap / total_liabilities`
5. If `z is None`, return `0` (no penalty). All-or-nothing: any missing input means no penalty.
6. Penalty tiers (literal):
   - `z >= 2.6` to `0` (safe)
   - `z >= 1.1` to `-10` (grey zone)
   - `z >= 0.0` to `-30` (distress)
   - `z < 0.0` to `-60` (deep distress)

## NULL / missing-data handling (P5 check)

- Empty financials, no fiscal years: returns `0`. **Honours P5** (missing data is never a penalty).
- Any of the five financial inputs missing, or market cap unparseable to None, or total_assets / total_liabilities zero: `compute_z_double_prime_raw` returns None to penalty `0`. **Honours P5.**
- For a penalty the neutral value is `0` (no subtraction), which is the correct P5 analogue of "neutral 50" for a positive component: missing data must not punish.

## Output range and composite mapping

- Output: one of `{0, -10, -30, -60}` (integer composite-point penalty).
- Applied additively: `c_score_raw = _clamp(raw_composite + legal_penalty + altman_pen)`, clamped to `[0, 100]`. A composite already near the floor cannot be pushed below 0 by the penalty.

## Known divergences / open questions

- **Vestigial `total_revenue` in ALTMAN_LOOKUPS.** `ALTMAN_LOOKUPS` still defines `total_revenue` (the classic Z X5 = sales/total_assets ratio), but the live Z'' path drops X5 entirely (`compute_z_double_prime_raw` has no `total_revenue` parameter). The key is unused by the live penalty and is only consumed by the classic `compute_z_raw` and the Phase 2b distribution-analysis script. Harmless, but it can mislead a reader into thinking X5 still feeds the penalty.
- **Year selection by string `max`.** `y0 = max(all_years)` takes the lexical max of `fiscal_year` text values. For ISO `YYYY-MM-DD` strings this is chronological, so it picks the most recent year correctly. Same latent date-format coupling noted in components 09 and 10. Note also that Piotroski uses `sorted(..., reverse=True)[0]` while Altman uses `max(...)`; both pick the most recent year, but via different idioms in the same file.
- **All-or-nothing versus partial-data Piotroski.** This penalty is strictly all-or-nothing (one missing input means no penalty at all), which fully honours P5. That is a deliberate contrast with Piotroski (component 10), where partial data past the 2-year gate can drag the score down. The two fundamentals-based components handle missing data with opposite philosophies; worth noting when reasoning about data-coverage effects across the composite.
- **Market cap provenance differs from the other financial inputs.** Four ratios come from yfinance financial statements (weekly cadence), but X4's numerator is the screener market cap text (FinViz, far more frequent). The penalty therefore mixes a slow fundamentals snapshot with a fresher market-cap reading. Defensible, but the inputs are not all as-of the same moment.
