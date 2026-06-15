# Methodology Reconciliation FOLLOWUPS

This file tracks findings surfaced when methodology docs are reconciled against
the live scorer code (the actual source bytes), but which are NOT actioned in
the documentation pass that found them. Each entry records the divergence
between what the code does and what is sound or intended, so a future scorer arc
can pick it up deliberately rather than rediscovering it.

Severity legend:

- **PRIORITY**: queued as the next scorer arc step. A correctness concern
  (often a P5 violation) live in production.
- **DOC-FIX**: a wrong comment or docstring; no behaviour change. Fold into the
  next commit that touches the same file for a scoring reason.
- **LATENT**: banked, not urgent. Revisit opportunistically. Mostly dead code,
  cosmetic collisions, or format couplings that are correct today but fragile.

Nothing in this file is a green light to change scorer code. Any scorer change
still follows the version-bump policy (P18) and the empirical-evidence gate
(P29) where scoring output is affected.

---

## 15 June 2026: components 9 to 13 reconciliation pass

Source: reconciliation of `docs/methodology/component_09_earnings.md` through
`component_13_altman_penalty.md` against `signals/scorer.py`,
`database/db.py`, and `signals/line_item_keys.py`. Read-only; no code changed.

### PRIORITY

- **Component 10 (Piotroski), P5 VIOLATION.**
  - What the code does: once a ticker clears Lock 1 (2 or more fiscal years,
    `score_piotroski`, scorer.py:364), each of the nine F-score signals only
    increments `f` when its inputs are present. Missing line items silently
    fail to increment. A low `f` then maps to a sub-neutral score
    (`f <= 3` to `20.0`, `f == 4` to `38.0`, scorer.py:428-432).
  - Why it is a concern: a ticker with two years on file but sparse line items
    can score as low as `20.0` purely because data is absent, not because
    fundamentals are weak. P5 requires NULL inputs to resolve to neutral
    (50), never a penalty. This depresses composites for thinly-reported
    tickers, which skews the small-cap and penny band where yfinance financial
    coverage is weakest. Live in production.
  - Proposed action: scorer fix so absent line items are treated as
    neutral/unknown rather than scored as a failed F-score criterion (for
    example, compute the F-score over only the signals whose inputs are
    present, or fall back to neutral 50 when coverage is below a threshold).
    Affects scoring output: requires a version bump (P18) and a gunicorn
    restart, and its own diagnostic-then-implement arc step (P29 empirical
    distribution check before locking the fix shape).

### DOC-FIX

- **Component 12 (analyst_mom), stale docstring.**
  - What the code does: `score_analyst_momentum` docstring (scorer.py:613-616)
    still advertises the v0.16.0 soft price-target folding (soft `main`/`reit`
    actions with `priceTargetAction` Raises/Lowers contributing plus or minus
    0.25) as live. The actual map, `get_analyst_momentum_map`
    (db.py:1671-1689), folds hard actions only: `up`/`init` to +1, `down`
    to -1, everything else to 0 (v0.17.0). The map's own docstring
    (db.py:1638-1664) records that the soft-PT contribution was removed on
    25 May 2026 after failing external event-study validation.
  - Why it is a concern: the bytes are correct, the scorer comment is wrong.
    A future reader trusting the scorer docstring would believe soft-PT
    folding is live when it is not.
  - Proposed action: correct the `score_analyst_momentum` docstring the next
    time `scorer.py` is opened for a scoring reason. Cleanest to fold into the
    Piotroski PRIORITY fix commit, since that already touches `scorer.py`. No
    behaviour change, no version bump on its own.

### LATENT

- **Components 09 / 10 / 13: ISO-date string-sort couplings.**
  - 09 (earnings): `get_earnings_enrichment_map` (db.py:1565) orders quarters
    by `fiscal_quarter DESC` as a text column; the decay weighting assumes
    most-recent-first. Correct only while `fiscal_quarter` is ISO
    `YYYY-MM-DD` (written by `fetch_earnings_history`, yahoo_scraper.py:103).
  - 10 (piotroski): `sorted(all_years, reverse=True)` (scorer.py:363) sorts
    `fiscal_year` as text to pick y0/y1.
  - 13 (altman): `y0 = max(all_years)` (scorer.py:551) takes the lexical max
    of `fiscal_year` text. (Note: 10 and 13 use different idioms,
    `sorted(...)[0]` versus `max(...)`, for the same "most recent year"
    selection in the same file.)
  - Concern: all three are correct for ISO date strings but silently break if
    a future yfinance shape ever yields a non-ISO `fiscal_quarter` /
    `fiscal_year` string. Latent format coupling, not a live bug.
  - Action: none now; revisit if the yfinance date shape changes, or
    centralise the most-recent-period selection.

- **Component 09 (earnings): dead guard.**
  - The `if total_w == 0: return 50.0` branch (scorer.py:342) is unreachable:
    the function already returns at scorer.py:316 when `earnings_list` is
    empty, and any non-empty list gives `total_w >= 4`. Harmless defensive
    code that can never fire. Action: drop opportunistically.

- **Component 10 (piotroski): output collision at 50.0.**
  - A genuine F-score of exactly 5 maps to `50.0` (scorer.py:430), the same
    value used for the two neutral fallbacks (empty financials and fewer than
    2 fiscal years, scorer.py:357/365). Three distinct input conditions yield
    an identical stored `piotroski_score` of 50.0, so the persisted value
    cannot tell a backtest whether 50.0 meant "computed middling" or
    "skipped / insufficient history". Cosmetic for scoring; relevant for
    backtest interpretability. Action: consider a sentinel or NULL for the
    skipped case when the backtest harness lands.

- **Component 11 (inst_own): init-equivalent caveat and unused field.**
  - Sub-neutral floor: a ticker with present-but-thin top-10 ownership SUM
    below 12 percent scores `30.0` (scorer.py:607). This is intended (low
    institutional conviction is a real signal) and is distinct from the P5
    missing-data path which returns 50.0; recorded so 30.0 is not mistaken
    for a P5 violation.
  - Unused field: `get_inst_ownership_map` returns `holder_count`
    (`COUNT(*)`, db.py:1616), but `score_inst_ownership` never reads it. Dead
    output today; a candidate input if the component is refined.
  - Action: none now.

- **Component 12 (analyst_mom): init-as-upgrade, and unused count fields.**
  - `init` (coverage initiation) is folded into `upgrades_90d` and
    contributes +1.0 in `get_analyst_momentum_map` (db.py:1674/1681),
    treating every initiation as bullish. A modelling assumption worth
    confirming (most initiations are at buy-equivalent grades, so likely
    fine).
  - `upgrades_90d` / `downgrades_90d` are carried for display and reporting
    but unused by the scorer, which derives the score from `net_momentum`
    only. Activity magnitude beyond the net is invisible to the score.
  - Action: none now; revisit if analyst_mom is re-specified.

- **Component 13 (altman penalty): vestigial total_revenue in ALTMAN_LOOKUPS.**
  - `ALTMAN_LOOKUPS` (line_item_keys.py:92-100) still defines `total_revenue`
    (the classic Z X5 = sales/total_assets ratio), but the live Z'' path
    (`compute_z_double_prime_raw`, scorer.py:477) drops X5 entirely and has no
    `total_revenue` parameter. The key is only consumed by the classic
    `compute_z_raw` and the Phase 2b distribution-analysis script, not by the
    live penalty. Harmless, but it can mislead a reader into thinking X5 still
    feeds the penalty. Action: annotate or remove from the live lookup set
    opportunistically.
