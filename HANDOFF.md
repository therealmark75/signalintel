# SignalIntel Session Handoff

**Last updated:** end of Part 39 night 1 (4 June 2026)
**Engine:** SCORING_ENGINE_VERSION 0.17.0 (unchanged)
**Repo:** Part 39 work on branch `refactor/component-registry`; commits 53ac17c, 2196ff4 pushed to origin/refactor/component-registry. main unchanged at e14534a.

## Where we are
Part 39 (component-rendering refactor, array-driven, hard prerequisite before Yahoo components 9-16) is in progress on a feature branch. Phase 1 inventory complete. Phase 2 design locked. Phase 3 implementation 2 of 16 steps shipped. Remaining 14 steps queued in defined order.

## Part 39 status

### Phase 1 (inventory): COMPLETE
Two-prompt diagnostic mapped every component-rendering surface, persistence shape, write path, read path, and runtime drift surface. Key findings: the 11 May 2026 ticker.html COMPONENTS registry covers ticker.html only; every other surface (screener, signals, dashboard, watchlist, industry, penny screener) is hardcoded column-by-column. Adding component 9 today would touch 8-11 files. signal_scores carries 11 per-component columns; sector_performance is the upstream source for sector_strength_score; no other table stores per-component scores. Backtest reads zero component columns (rating + composite only), so it's untouched by this refactor. Telegram alerts and top_signals_of_day are rating-only and intentionally out of scope.

### Phase 2 (design): LOCKED
- Q1: Python-side registry in `signals/components.py`, exposed to Jinja via context processor, exposed to JS via JSON injection.
- Q2: Wide-column persistence stays.
- Q3: v0.17.0 sub-scores (earnings, piotroski, inst_own, analyst_mom, altman_penalty) on ticker-page only; hidden on screener/dashboard/watchlist/industry/signals.
- Q4: Telegram alerts and top_signals_of_day stay rating-only, out of scope.
- Q5: `surfaces` field on each registry entry declares per-surface visibility.
- Q6: `signal_scores_projection()` helper centralises SELECT projections; SELECT * at ticker detail becomes explicit.
- Q7: Full sweep across all 11 files (not ticker-parity-only).
- Q8: Weights declarative metadata only this arc, not registry-driving. Strict visual parity, no restyling.

### Phase 3 (implementation): 2 of 16 steps shipped on `refactor/component-registry`

**Step 1: signals/components.py (commit 53ac17c).** 218-line canonical registry, 13 Component entries (8 from JS registry + 5 v0.17.0 sub-scores). Both `value` and `legal` carry db_column='' (computed client-side / sourced from legal_risk table respectively). `all_db_columns()` returns 11. Accessors: `components_for_surface(surface)`, `sortable_columns()`, `component_by_key(key)`, `to_json_dict()`. All 14 verification gates green. Suite 397/2.

**Step 2: database/db.py projection helper + insert_signal_scores rewire (commit 2196ff4).** New `signal_scores_projection(prefix='', extras=())` helper. `insert_signal_scores` rewired: component column list sourced from `all_db_columns()`, setdefault loop registry-driven, INSERT built as non_components + component_cols (19 columns), :named placeholders and executemany-over-dicts preserved. Behaviour-identical via named-parameter binding. Suite 397/2.

### Remaining 14 steps (in order, each its own CC prompt with verification gate)

| Step | File(s) | Change |
|------|---------|--------|
| 3 | signals/scorer.py | Test asserting every component db_column has a corresponding TickerSignal field |
| 4 | web/app.py | Context processor injecting components into Jinja + components_json |
| 5 | web/app.py | /api/screener projection switched to signal_scores_projection() |
| 6 | web/app.py | /api/signals, sector, rating projections switched |
| 7 | web/app.py | Dashboard top_strong/top_bearish + watchlist join projections switched |
| 8 | web/app.py | Group A SELECT * at ticker detail switched to explicit projection |
| 9 | web/app.py | allowed_sorts additive merge with sortable_columns() (preserves non-component sort keys) |
| 10 | web/templates/ticker.html | COMPONENTS array becomes window.COMPONENTS_DATA consumption + JS shim for render methods |
| 11 | web/templates/screener.html, penny_screener.html | Per-row component cells become registry loop |
| 12 | web/templates/index.html | Signals table + sector tab columns from registry |
| 13 | web/templates/dashboard.html | Spotlight breakdown loop from registry |
| 14 | web/templates/watchlist.html | Per-row component cells from registry |
| 15 | web/templates/industry.html | Per-row component cells from registry |
| 16 | Full integration walk + merge to main | Multi-tier browser sweep (mark2/markn), pixel-parity confirm, fast-forward or squash-merge by Mark's preference |

## Operational notes for the arc

- **Branch discipline:** `refactor/component-registry` is the working branch. GitHub Desktop and any other terminal session must stay on this branch (the Step 2 turn saw a silent HEAD drift back to main, caused most likely by GitHub Desktop checkout; cost a turn to recover). Do not switch branches in any tool until Step 16's merge.
- **P23 hook is content-scanning not path-matching.** Step 2 found this empirically: database/db.py edits did not trip the hook because the diff carried no auth tokens or dashes. Path-match was Athena's prior assumption; correct it in future drafts.
- **Athena prompt-drafting lesson banked.** Three of Step 1 + Step 2's STOPs were Athena prompt contradictions caught by CC (count mismatch, sub-score label/tooltip gap, INSERT ordering vs grouped expected list). Forward discipline: every verification gate's expected output must be cross-checked against the actual source bytes before the prompt fires, not against the Phase 1 inventory's natural-language summary. CC's empirical-first behaviour is what's keeping the arc honest.

## Infra
- Gunicorn last live master PID 99255 (per Part 38 close; Step 1 and Step 2 did not require restart, no scorer/scheduler/app.py touched yet).
- Suite: 397 passed, 2 skipped (unchanged).
- Stripe on TEST keys; thesignalvault.io live behind Cloudflare. Production-key flip remains unblocked on every technical axis, business call only.

## Next session
Resume on Step 3 (signals/scorer.py registry-consistency test). Read PROJECT_CONTEXT.md and HANDOFF.md as standard; the locked Phase 2 design carries forward unchanged.

## Test accounts (unchanged from Part 38)
- mark2 (id 6): stored free, no trial, effective free.
- beta2 (id 9): stored free, active trial, effective ELITE.
- markn (id 2): stored elite, effective elite.
- marktest1 (id 8): stored pro, mid-trial through approximately 2026-06-05, currently effective elite.

## Prior arcs
See PROJECT_CONTEXT.md and previous HANDOFF revisions in git history.
