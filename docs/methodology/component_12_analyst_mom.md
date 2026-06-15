# Component 12: Analyst Momentum

> **STATUS: LIVE COMPONENT.** Positive weighted component in the composite.
> Reconciliation doc: describes what the code actually computes, read from
> the source bytes on 15 June 2026, not an idealised methodology.
> Source of truth: `signals/scorer.py:score_analyst_momentum` (line 610),
> fed by `database/db.py:get_analyst_momentum_map` (line 1635). The map's SQL
> is authoritative for the per-row contribution rules, NOT the scorer docstring.

## Identity

- Component name: Analyst Momentum
- Registry key: `analyst_mom`
- Component number: 12
- Registry entry: `signals/components.py` (key `analyst_mom`, `db_column='analyst_mom_score'`, `introduced_version='0.13.0'`)
- Persisted column: `signal_scores.analyst_mom_score`

## Weight and role

- Composite weight: **0.125** (positive component).
- Effective share is 0.125 / 1.60, about 7.81 percent of the weighted composite.
- Not a penalty, not a modifier.

## Inputs

- Source table: `analyst_changes`.
- Columns consumed: `ticker`, `action`, `event_date`.
- Enrichment map: `get_analyst_momentum_map` (db.py:1635), default `window_days=90`. Returns `{ticker: {upgrades_90d, downgrades_90d, net_momentum}}`. The scorer reads `net_momentum` only.
- Window: `WHERE event_date >= date('now', '-90 days')`.
- Data origin: yfinance `get_upgrades_downgrades()` (scrapers/yahoo_scraper.py:198). `action` is the yfinance action verb stored lower-case (for example `up`, `down`, `init`, `main`, `reit`).

## Algorithm (from the bytes)

### Map side (the live contribution rules, v0.17.0)

The SQL aggregates per ticker over the 90-day window:

- `upgrades_90d = COUNT(CASE WHEN action IN ('up', 'init') THEN 1 END)`
- `downgrades_90d = COUNT(CASE WHEN action = 'down' THEN 1 END)`
- `net_momentum = SUM(CASE WHEN action IN ('up','init') THEN 1.0 WHEN action = 'down' THEN -1.0 ELSE 0.0 END)`

So `net_momentum` is mathematically (hard upgrades plus initiations) minus (hard downgrades), integer-valued. Soft actions (`main`, `reit`) and anything else contribute exactly `0.0`. `net_momentum` is cast to float for the scorer ladder but carries integer values; NULL `SUM` becomes `0.0`.

### Scorer side (the ladder)

1. If `mom_data is None`, return `50.0`.
2. `net = mom_data.get("net_momentum")`; if `None`, return `50.0`.
3. Ladder (literal thresholds, with a plus or minus 0.5 neutral band):
   - `net >= 3.0` to `80.0`
   - `net >= 1.5` to `70.0`
   - `net >= 0.5` to `60.0`
   - `net <= -3.0` to `20.0`
   - `net <= -1.5` to `30.0`
   - `net <= -0.5` to `40.0`
   - else (`abs(net) < 0.5`) to `50.0` (neutral band)

On integer net this resolves cleanly: 1 to 60, 2 to 70, 3+ to 80; -1 to 40, -2 to 30, -3 or lower to 20; 0 to 50.

## NULL / missing-data handling (P5 check)

- `mom_data is None` (no analyst rows in window, ticker absent from map): returns 50.0. **Honours P5.**
- `net_momentum is None`: returns 50.0. In practice the map never emits None (NULL SUM is coerced to 0.0), but the scorer guards it anyway.
- A ticker with only soft actions (`main`/`reit`) in window: `net_momentum = 0.0` to 50.0 neutral. **Honours P5** (soft-only activity is neutral, not a penalty).

## Output range and composite mapping

- Range: discrete set `{20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0}`, neutral midpoint 50.0.
- Enters the composite as a positively weighted term at weight 0.125.

## Known divergences / open questions

- **Stale scorer docstring (headline divergence for this step).** The `score_analyst_momentum` docstring (scorer.py:613-616) still describes the v0.16.0 behaviour: "net_momentum is now a FLOAT ... soft actions (main/reit) with priceTargetAction Raises/Lowers contribute plus or minus 0.25 ... PT weight 0.25 PROVISIONAL." That soft-PT folding is NOT what the live code does. The actual map (get_analyst_momentum_map SQL) folds hard actions only and contributes 0 for soft actions; its own docstring (db.py:1638-1664) records that the v0.16.0 soft-PT contribution was REMOVED on 25 May 2026 after failing external event-study validation (real-cohort Raises-minus-Lowers 21d CAR spread of -0.79 percent, t=-3.64, p=2.7e-4, wrong sign, monotonicity inverted). Net effect: the live component is hard-actions-only; the scorer docstring documents a superseded design. The bytes are correct; the scorer comment is the thing that is wrong. No code change in this step, but the docstring should be corrected when the file is next touched for a scoring reason.
- **`init` counted as an upgrade.** Initiations (`init`) are folded into `upgrades_90d` and contribute `+1.0`. An initiation is a new coverage start, not strictly a rating raise; treating every initiation as bullish is a modelling choice worth confirming. Not obviously wrong (most initiations are at buy-equivalent grades), but it is an assumption baked into the SQL.
- **`upgrades_90d` / `downgrades_90d` carried but unused by the scorer.** They exist for display and reporting; the score derives only from `net_momentum`. So two upgrades and zero downgrades scores identically to a net of +2 reached any other way; magnitude of activity beyond the net is invisible to the score.
- **Event-fade as a separate component is logged, not built.** Per PROJECT_CONTEXT, Bernard-Thomas style event-fade (its own theory, weight, and validation) is a future candidate and must never be folded back into analyst_mom. Recorded here so the boundary is not blurred later.
