# Component 14: Short Interest Risk Penalty

> **STATUS: LIVE PENALTY.** This is an additive penalty, NOT a positively
> weighted component. `is_penalty=True`, `weight=0.0` in the registry.
> Introduced in SCORING_ENGINE_VERSION 0.19.0 (19 June 2026).
> Source of truth: `signals/scorer.py:score_short_interest_penalty`, applied
> on the additive line in `score_all_tickers`
> (`c_score_raw = _clamp(raw_composite + legal_penalty + altman_pen + si_pen)`),
> fed by `screener_snapshots.short_interest_pct` (FinViz "Short Float", already
> ingested by `scrapers/screener_scraper.py`).

## Thesis

Short interest as a percent of float is read as a smart-money RISK signal.
Heavy short interest means informed capital is actively betting against the
name, which is elevated downside risk, so it applies a drag on the composite.
The research basis: high short interest predicts subsequent underperformance,
and the effect is strongest in small-caps and weaker on a value-weighted
basis (large, heavily-shorted names are noisier signals). The component is
deliberately one-sided: it penalises heavy short interest but gives no reward
for low short interest, because the absence of shorts is not itself a positive
edge, it is just the absence of this particular risk.

## Identity

- Component name: Short Interest Risk Penalty
- Registry key: `short_interest`
- Component number: 14
- Registry entry: `signals/components.py` (key `short_interest`, `db_column='short_interest_penalty'`, `is_penalty=True`, `weight=0.0`, `introduced_version='0.19.0'`)
- Persisted column: `signal_scores.short_interest_penalty`

## Weight and role

- Composite weight: **0.0**. This is a **penalty**, not a positive weighted term.
- It does NOT pass through `compute_composite`. It is added additively to the composite after the weighted average, alongside the legal and Altman penalties: `c_score_raw = _clamp(raw_composite + legal_penalty + altman_pen + si_pen)`. The penalty values are negative composite-point offsets, so they subtract from the 0 to 100 composite before the final clamp.
- It is the third member of the additive penalty line, modelled exactly on `score_altman_penalty` (component 13): same `is_penalty=True` / `weight=0.0` registry shape, same "return <= 0, 0 = no penalty / missing" contract, same additive application point.

## Why a one-sided penalty, not a two-sided weighted component

A two-sided weighted 0 to 100 component (low short interest scores high, heavy
short interest scores low, weight 0.10) was BUILT FIRST and REJECTED on P29
evidence. The two-sided design inflated the composite: mean +0.99, 601 upgrades
versus 14 downgrades. The mechanism of the failure: extracting the old short
penalty from `score_quality` raised quality across the universe, while the new
low component score only bit the shorted tail; on the shorted names the two
effects cancelled, and on the lightly-shorted majority (who score high on a
two-sided short component) the composite was lifted universe-wide. The result
was broad inflation, the opposite of a risk signal.

The one-sided penalty fixes this. It captures the sharp tail-risk signal
cleanly (only heavily-shorted names are touched) without lifting the rest of
the universe. A penalty has no positive arm to inflate the majority.

## Inputs

- Source field: `short_interest_pct` on the screener row (FinViz "Short Float", mapped in `scrapers/screener_scraper.py`, persisted in `screener_snapshots.short_interest_pct`). Already ingested before 0.19.0; no new scrape was added for this component.
- Coverage: about 50 percent of the scored universe has a non-null `short_interest_pct`. Uncovered tickers receive no penalty (P5, below). FinViz short-float coverage is densest on the heavily-shorted tail, which is the population the penalty targets, so the coverage gap is least harmful where the signal matters most.
- Read directly from `row.get("short_interest_pct")` in `score_all_tickers`, no enrichment map.

## Algorithm (from the bytes)

`score_short_interest_penalty(short_interest_pct) -> int`:

1. If `short_interest_pct is None`, return `0` (no penalty).
2. Coerce to float `si`.
3. If `si > 100`, return `0` (implausible source noise guard).
4. Penalty tiers (literal):
   - `si > 30` to `-3`
   - `si > 20` to `-2`
   - `si > 10` to `-1`
   - else (`si <= 10`) to `0`

## Calibration (relocate, not amplify)

The pre-0.19.0 short signal lived INSIDE `score_quality` as a `-15 / -10 / -5`
block at the same `> 30 / > 20 / > 10` breakpoints. Because quality is a
0.30-weighted sub-score normalised by total weight 1.60, the old `-15` moved
the composite only about `-15 * 0.30 / 1.60 = -2.8` at the top tier. The new
penalty lands on `c_score_raw` directly, so the additive `0 / -1 / -2 / -3`
ladder reproduces that same composite impact. The change is therefore a true
RELOCATION of short interest out of quality, not a re-weighting of its force.

P29 on the final penalty design (against the stored pre-change composites):
composite mean change `-0.004`, 14 rating-label changes (6 up, from the handful
of `> 100` percent noise tickers that lost their old unfair `-15` quality
penalty under the new `> 100` guard; 8 down, on the legitimate shorted tail).
The composite is effectively unchanged, which is the intended outcome of
relocation parity.

## NULL / missing-data handling (P5 check)

- `short_interest_pct is None`: returns `0`. **Honours P5** (missing data is never a penalty). About half the universe falls here and is untouched.
- `short_interest_pct > 100`: returns `0`. Implausible values (the live universe has a handful up to about 319 percent, FinViz source noise) apply no penalty rather than the maximum, mirroring the `> 100` data-quality guard in `score_inst_ownership` (component 11). Note this differs from the old `score_quality` block, which had no `> 100` guard and penalised those tickers `-15`.
- For a penalty the neutral value is `0` (no subtraction), the correct P5 analogue of "neutral 50" for a positive component.

## Output range and composite mapping

- Output: one of `{0, -1, -2, -3}` (integer composite-point penalty).
- Applied additively: `c_score_raw = _clamp(raw_composite + legal_penalty + altman_pen + si_pen)`, clamped to `[0, 100]`. A composite already near the floor cannot be pushed below 0 by the penalty.

## Surfacing

- All-tiers RISK FLAG. `short_interest_penalty` is intentionally EXCLUDED from both `ELITE_ONLY_SUBSCORE_FIELDS` and `PROPRIETARY_SCORE_FIELDS` in `config/entitlements.py`. It is served to Free, Pro, and Elite alike: a risk warning, not a premium analytic. Both leak-guard strip helpers are opt-in (they only strip listed fields), so an unlisted field reaches all tiers automatically; the `/api/ticker` payload is registry-driven via `signal_scores_projection`, so the column flows into the response with no per-route edit.
- A comment at the `PROPRIETARY_SCORE_FIELDS` definition records the deliberate exclusion so a future reader does not "fix" the omission.

## Version

- Introduced 0.19.0 (MINOR per P18: a new component that changes composite output). The same-commit removal of the short block from `score_quality` is part of the same logical change (extract-and-promote), so the composite is never double-counting short interest at any point.

## Known divergences / open questions

- **Relocation parity is the calibration target, not a ceiling.** The `0 / -1 / -2 / -3` ladder was chosen to preserve the historical composite impact. IF the historical force is later judged too weak, strengthening the penalty is a separate deliberate decision (an amplification) with its own P29 evidence against the 0.19.0 baseline. Banked in FOLLOWUPS so a future reader does not assume parity was the intended maximum.
- **Coverage asymmetry.** About half the universe has no `short_interest_pct` and is untouched. This is acceptable (FinViz coverage is densest on the shorted tail the penalty targets), but it means the penalty is silent on uncovered names rather than conservatively assuming a value. Consistent with P5.
- **Source freshness.** FinViz short float reflects the bi-monthly FINRA settlement cycle with a reporting lag, so the value is days to a couple of weeks stale by construction. Expected for short-interest data, not a fault.
