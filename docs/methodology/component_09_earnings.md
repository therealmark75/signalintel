# Component 09: Earnings Surprise (PEAD)

> **STATUS: LIVE COMPONENT.** Positive weighted component in the composite.
> Reconciliation doc: describes what the code actually computes, read from
> the source bytes on 15 June 2026, not an idealised methodology.
> Source of truth: `signals/scorer.py:score_earnings_surprise` (line 308),
> fed by `database/db.py:get_earnings_enrichment_map` (line 1554).

## Identity

- Component name: Earnings Surprise
- Registry key: `earnings`
- Component number: 09
- Registry entry: `signals/components.py` (key `earnings`, `db_column='earnings_score'`, `introduced_version='0.13.0'`)
- Persisted column: `signal_scores.earnings_score`

## Weight and role

- Composite weight: **0.125** (positive component).
- The composite normalises by the sum of all weights (`compute_composite`, scorer.py:719: `total_w = sum(weights.values())`), currently 1.60, so this component's effective share is 0.125 / 1.60, about 7.81 percent of the weighted composite.
- Not a penalty, not a modifier.

## Inputs

- Source table: `earnings_history`.
- Columns consumed: `fiscal_quarter`, `eps_actual`, `eps_estimate`, `surprise_pct`, `reported_at`. The scorer only reads `surprise_pct`; the others travel in the map but are not used by the algorithm.
- Enrichment map: `get_earnings_enrichment_map` (db.py:1554). Returns `{ticker: [ {fiscal_quarter, eps_actual, eps_estimate, surprise_pct, reported_at}, ... ]}` ordered `fiscal_quarter DESC` (most recent quarter first), via SQL `ORDER BY ticker, fiscal_quarter DESC`.
- Data origin: yfinance `get_earnings_history()` (scrapers/yahoo_scraper.py:96), where `surprise_pct` maps from the `surprisePercent` field.

## Algorithm (from the bytes)

1. If `earnings_list` is empty, return `50.0` (neutral) immediately.
2. Take up to the first 4 quarters (`earnings_list[:4]`), which are the most recent 4 given the DESC ordering.
3. Decay weights, most recent first: `[4, 3, 2, 1]`.
4. Per-quarter contribution from `surprise_pct` (the `_contribution` ladder, literal constants):
   - `surprise_pct is None` to `0.0`
   - `> 10` to `+25.0`
   - `> 3` to `+15.0`
   - `> 0` to `+7.0`
   - `> -3` (that is, -3 percent < surprise <= 0 percent) to `0.0` (neutral zone)
   - `>= -10` to `-15.0`
   - else (`< -10`) to `-25.0`
5. Accumulate `total_w += w` and `total_c += w * contribution` over the quarters.
6. If `total_w == 0`, return `50.0`.
7. `weighted_avg = total_c / total_w`, mathematically bounded to `[-25, +25]`.
8. Final: `_clamp((weighted_avg + 25.0) * 2.0)`, where `_clamp(val, 0.0, 100.0) = max(0, min(100, val))`.

A weighted_avg of 0 maps to exactly 50.0. The most recent quarter dominates at weight 4 of 10.

## NULL / missing-data handling (P5 check)

- Empty `earnings_list` (ticker not yet scraped, scorer receives `earnings_map.get(ticker, [])`): returns 50.0. **Honours P5.**
- A present quarter with `surprise_pct = NULL`: contributes `0.0` but its decay weight is still added to `total_w`. A ticker with quarters present but all `surprise_pct` NULL yields `weighted_avg = 0` to score 50.0. **Honours P5** (missing surprise data resolves to neutral, never a penalty).
- Output is always in `[0, 100]` by the clamp.

## Output range and composite mapping

- Range: `[0.0, 100.0]`, neutral midpoint 50.0.
- Enters the composite as a positively weighted term at weight 0.125 inside `compute_composite`, before any legal or Altman penalty and before the sector multiplier.

## Known divergences / open questions

- **Dead guard.** The `if total_w == 0: return 50.0` branch (scorer.py:342) is unreachable in practice: the function already returns at line 316 when `earnings_list` is empty, and any non-empty list gives `total_w >= 4`. Harmless, but it is defensive code that can never fire.
- **Ordering relies on `fiscal_quarter` string sort.** The map orders by `fiscal_quarter DESC` as a text column. `fetch_earnings_history` writes `fiscal_quarter` as `idx.strftime("%Y-%m-%d")` when the index is a datetime, else `str(idx)` (yahoo_scraper.py:103). For ISO `YYYY-MM-DD` strings text-DESC equals chronological-DESC, so the decay weighting is correct. If a future yfinance shape ever yields a non-ISO `fiscal_quarter` string, the "most recent first" assumption silently breaks. Not a live bug today; a latent coupling to the date format.
- **Neutral-zone asymmetry.** The ladder treats `-3 percent < surprise <= 0 percent` as neutral (0 contribution) but `0 < surprise <= 3 percent` as `+7.0`. A tiny beat scores positive while a tiny miss scores neutral. This is a deliberate asymmetry in the constants, not obviously wrong, but the boundary at exactly 0 is worth a sanity note: a 0.0 percent surprise lands in the neutral zone (the `> 0` test is strict).
