# SignalIntel Session Handoff

**Last updated:** end of Part 40 (5 June 2026)
**Engine:** SCORING_ENGINE_VERSION 0.17.0 (unchanged)
**Repo:** Part 39+40 work on branch `refactor/component-registry`; commits 53ac17c through acf12b6 pushed to origin/refactor/component-registry. main unchanged at e14534a.

## Where we are
Part 39/40 (component-rendering refactor, array-driven, hard prerequisite before Yahoo components 9-16) in progress on a feature branch. Phase 1 inventory complete. Phase 2 design locked. Phase 3 implementation 7 of 17 steps shipped (one Step 4.5 helper enhancement plus one Step 5.5 registry correction inserted into the original 16-step plan). 10 steps remaining (numbering preserved from original plan: 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16; renumbering deferred to keep audit trail).

## Part 39/40 status

### Phase 1 (inventory): COMPLETE
Two-prompt diagnostic from Part 39 night 1; details in PROJECT_CONTEXT.

### Phase 2 (design): LOCKED, with amendments
Original Q1-Q8 locks held (see PROJECT_CONTEXT). Two amendments banked in Part 40:

- **Amendment A (Step 4.5):** `signal_scores_projection()` accepts an opt-in keyword-only `surface=` argument. Default behaviour (surface=None) byte-identical to Step 2. With surface set, filters via `components_for_surface(surface)`. Raises ValueError on invalid surface. Three tests lock the contract.
- **Amendment B (Step 5.5 audit lens):** A column belongs on a surface if the API response for that surface carries it, not only if the consumer renders it as a visible cell. Server-side sort and filter inputs count as carries because the response must include the column. Ticker's 5 sub-scores count as carries because /api/ticker is SELECT * and Step 10 will render them in JS. This is the canonical lens for any future registry-vs-reality audit.

### Phase 3 (implementation): 7 of 17 steps shipped on `refactor/component-registry`

| Step | Commit | Summary |
|------|--------|---------|
| 1 | 53ac17c | `signals/components.py` canonical registry, 13 Component entries, 11 db_columns, accessors |
| 2 | 2196ff4 | `database/db.py` `signal_scores_projection()` helper + `insert_signal_scores` rewired to read column list from registry |
| 3 | 6d57ae7 | `tests/test_components_registry.py` registry-consistency test (2 tests, locks every db_column has a TickerSignal field) |
| 4 | e1eb2aa | `web/app.py` `inject_component_registry` context processor (Jinja `components` + JSON-string `components_json`) |
| 4.5 | 6d32096 | `database/db.py` `signal_scores_projection()` accepts opt-in `surface=` keyword; 3 new tests lock default + surface-filtered + invalid-surface contracts |
| 5 | 37cd4a5 | `/api/screener` in `web/app.py` switched to `signal_scores_projection(prefix='sig.', surface='screener', extras=...)` in both subquery and outer SELECT; `tests/test_screener.py` shape-lock test added |
| 5.5 | acf12b6 | Registry correction: `sector_strength_score` removed from `signals` surface (audit found never carried by /api/signals* responses; Step 5.5 amendment lens applied) |

Suite at session close: 403 passed, 2 skipped.

### Remaining 10 steps (in order, original numbering preserved)

| Step | File(s) | Change |
|------|---------|--------|
| 6 | web/app.py | /api/signals, /api/signals/sector/<sector>, /api/signals/<rating> projections switched to signal_scores_projection(surface='signals', ...). 4-component surface (post-Step-5.5). Three handlers in one prompt. Shape lock test required. |
| 7 | web/app.py | Dashboard top_strong/top_bearish + watchlist join projections switched to signal_scores_projection(surface='dashboard' / surface='watchlist') |
| 8 | web/app.py | Group A SELECT * at ticker detail switched to explicit projection via signal_scores_projection(surface='ticker') |
| 9 | web/app.py | allowed_sorts additive merge with sortable_columns() (preserves non-component sort keys) |
| 10 | web/templates/ticker.html | COMPONENTS array becomes window.COMPONENTS_DATA consumption + JS shim for render methods (largest single step in the arc) |
| 11 | web/templates/screener.html + penny_screener.html | Per-row component cells become registry loop |
| 12 | web/templates/index.html | Signals tab + sector tab from registry |
| 13 | web/templates/dashboard.html | Spotlight breakdown loop from registry |
| 14 | web/templates/watchlist.html | Per-row component cells from registry |
| 15 | web/templates/industry.html | Per-row component cells from registry |
| 16 | Full integration walk + merge to main | Multi-tier browser sweep (free/pro/elite), pixel-parity confirm, fast-forward or squash-merge by Mark's preference |

## Operational notes for the arc

- **Branch discipline:** `refactor/component-registry` is the working branch. GitHub Desktop and any other terminal session must stay on this branch. Three silent HEAD drifts last session caused by GitHub Desktop branch clicks; Part 40 saw none after the operational rule landed. Baseline verification at session open includes `git branch --show-current` against this exact string.
- **P23 hook is path-matching for web/app.py and content-scanning for everything else.** Confirmed empirically across Steps 4, 5: every web/app.py touch trips the hook regardless of diff content. Each Step 6+ web/app.py commit needs Mark's explicit --no-verify authorisation after Athena confirms the diff is auth-clean. database/db.py and signals/components.py do not trip on clean diffs (Steps 2, 4.5, 5.5 all committed cleanly).
- **Runtime drift:** any web/app.py commit needs a gunicorn restart at commit time. `launchctl kickstart -k gui/$(id -u)/io.thesignalvault.gunicorn`. Verify post-restart that the master is launchd-managed (PPID 1) and owns 5001 via lsof. The orphan-gunicorn-squatter (99255/99900) that blocked Step 4's restart was killed at 16:31 on 5 June; clean restarts since.
- **launchd `last exit code` is backward-looking, not a current-health signal.** Step 4's gate G8 had to accept `last exit code = 1` because the field reports the most recently exited process, which was a crash-loop casualty before the current master bound. Future gates should assert "current PID stable AND no recent err.log entries" rather than reading the exit-code field.
- **Step 4.5 / 5.5 amendments now in effect:** any future surface-projection switch (Steps 6-9) uses `signal_scores_projection(surface='<name>', ...)`. Any future registry-vs-reality discrepancy is resolved by the response-carries lens, not the render-cell lens.

## Known pre-existing FOLLOWUPS unchanged this session

- Dormant `initialise_schema` gap (does not provision volume_score or scoring_version on fresh-DB init). P19-class fix when prioritised. Not in this arc.
- AGENTS.md + docs/dash_sweep_plan.md tracked since Part 38 close.
- Orphan-gunicorn diagnosis (Part 40): session-open baseline check should be strengthened from "at least one gunicorn process" to "exactly one master with launchd-managed PPID chain bound to 5001 per lsof". Pre-existing condition, fixed in-session but worth codifying.
