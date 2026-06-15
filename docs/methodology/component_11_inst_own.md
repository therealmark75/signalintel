# Component 11: Institutional Ownership

> **STATUS: LIVE COMPONENT.** Positive weighted component in the composite.
> Reconciliation doc: describes what the code actually computes, read from
> the source bytes on 15 June 2026, not an idealised methodology.
> Source of truth: `signals/scorer.py:score_inst_ownership` (line 574),
> fed by `database/db.py:get_inst_ownership_map` (line 1604).

## Identity

- Component name: Institutional Ownership
- Registry key: `inst_own`
- Component number: 11
- Registry entry: `signals/components.py` (key `inst_own`, `db_column='inst_own_score'`, `introduced_version='0.13.0'`)
- Persisted column: `signal_scores.inst_own_score`

## Weight and role

- Composite weight: **0.125** (positive component).
- Effective share is 0.125 / 1.60, about 7.81 percent of the weighted composite.
- Not a penalty, not a modifier.

## Inputs

- Source table: `institutional_holders`.
- Columns consumed: `ticker`, `pct_out`, `filing_date` (the map also returns a `holder_count` via `COUNT(*)`, which the scorer does not use).
- Enrichment map: `get_inst_ownership_map` (db.py:1604). For each ticker it selects the most recent `filing_date` (an inner join on `MAX(filing_date)` per ticker), then `SUM(pct_out)` across all holders on that date. Returns `{ticker: {total_pct_held, holder_count, filing_date}}`. The scorer reads `total_pct_held` only.
- Data origin: yfinance `get_institutional_holders()` (scrapers/yahoo_scraper.py:160). `pct_out` is stored as a percentage (yfinance `pctHeld` fraction times 100). yfinance returns roughly the top 10 holders, so `total_pct_held` is a top-10 SUM, not total institutional ownership.

## Algorithm (from the bytes)

1. If `inst_data is None` (ticker not in the map), return `50.0`.
2. `pct = inst_data.get("total_pct_held")`; if `None`, return `50.0`.
3. Coerce `pct = float(pct)`.
4. **Data-quality guard:** if `pct > 100`, return `50.0`. A per-ticker SUM above 100 percent is treated as yfinance normalisation noise (the code cites a max observed SUM of 522.51 for DUOT), routed to neutral rather than a phantom top tier. This is documented in-code as a data-quality guard, NOT a scoring rule.
5. Tier cuts (literal, quartile-anchored as of v0.15.0, 21 May 2026):
   - `pct >= 48` to `75.0`
   - `pct >= 34` to `60.0`
   - `pct >= 12` to `45.0`
   - else (`pct < 12`) to `30.0`

The cuts were moved off the original 60/40/20 ladder to quartile anchors on the real top-10-SUM distribution (cited percentiles p25=12.4, p50=34.4, p75=48.3).

## NULL / missing-data handling (P5 check)

- `inst_data is None` (not yet scraped, `inst_own_map.get(ticker)` returns None): returns 50.0. **Honours P5.**
- `total_pct_held is None` (for example, all holders on the latest date had NULL `pct_out`, so SQL `SUM` returns NULL): returns 50.0. **Honours P5.**
- `pct > 100`: returns 50.0 (data-quality guard, also neutral).
- Present-but-low ownership is scored on its merits (see divergences for the floor).

## Output range and composite mapping

- Range: discrete set `{30.0, 45.0, 50.0, 60.0, 75.0}`, neutral midpoint 50.0.
- Enters the composite as a positively weighted term at weight 0.125.

## Known divergences / open questions

- **Sub-neutral floor for thin-but-present data.** A ticker WITH institutional data whose top-10 SUM is below 12 percent scores `30.0`, which is below neutral. This is intended (low institutional conviction is a real signal), and it is distinct from the P5 missing-data path which returns 50.0. Worth stating explicitly so it is not mistaken for a P5 violation: 30.0 means "present and low", not "missing".
- **Provisional validation, by project record.** Per PROJECT_CONTEXT, the quartile cuts are PROVISIONAL on theory plus a universe-snapshot distribution (the 50.8 percent non-neutral lift banked at v0.15.0), with inst_own forward-IC validation explicitly deferred to roughly 2027 (about 4 quarterly 13F cycles of clean filing-date history). No forward-return validation backs these cuts yet. Not a code divergence; a maturity caveat.
- **Top-10 SUM proxy, not true float ownership.** `total_pct_held` is the sum of the holders yfinance returns (about 10), not the true institutional ownership of float. The thresholds are calibrated to that proxy distribution, so the score is only as comparable across tickers as yfinance's holder-count consistency.
- **`holder_count` computed but unused.** The map returns `holder_count` (`COUNT(*)`), but the scorer never reads it. Dead output today; a candidate input if the component is ever refined.
