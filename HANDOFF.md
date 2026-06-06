# SignalIntel Session Handoff

**Last updated:** end of Part 41 (6 June 2026)
**Engine:** SCORING_ENGINE_VERSION 0.17.0 (unchanged)
**Repo:** Part 41 work on branch `refactor/component-registry`. Local HEAD `d3919a1`, 7 commits ahead of `origin/refactor/component-registry` (`66db8da`) pre-push; level after this session's push. `origin/main` at `c3c0e54`, and carries docs-only after this session's cherry-pick (no arc code on main).
**Suite:** 409 passed, 2 skipped (pre-existing `fmp_price_targets` + `economic_calendar` skips).

## Where we are
Parts 39/40/41 (component-rendering refactor, array-driven, hard prerequisite before Yahoo components 9-16) in progress on a feature branch. Phase 1 inventory complete. Phase 2 design locked (two amendments banked Part 40). Phase 3 implementation in progress.

Phase 3 status at Part 41 close: canonical **Step 6 full** (impl + test) and canonical **Step 7a** (dashboard panels) done. Two handlers the original plan omitted were also migrated this session (`api_industry`, `_get_penny_pick_full`), plus one Step-5.5-class registry correction (Step 9.5, reversion surface set). This is **NOT** the full SQL-handler half complete: canonical **Step 8** (ticker `/api/ticker` SELECT* to `surface='ticker'`) and canonical **Step 9** (`allowed_sorts` additive merge) remain OUTSTANDING handler work before the template sub-arc begins. Roughly 7 of 17 canonical steps shipped, with two handler steps still live.

## Part 39/40/41 status

### Phase 1 (inventory): COMPLETE
Two-prompt diagnostic from Part 39 night 1; details in PROJECT_CONTEXT.

### Phase 2 (design): LOCKED, with amendments
Original Q1-Q8 locks held (see PROJECT_CONTEXT). Two amendments banked in Part 40:

- **Amendment A (Step 4.5):** `signal_scores_projection()` accepts an opt-in keyword-only `surface=` argument. Default behaviour (surface=None) byte-identical to Step 2. With surface set, filters via `components_for_surface(surface)`. Raises ValueError on invalid surface. Three tests lock the contract.
- **Amendment B (Step 5.5 audit lens):** A column belongs on a surface if the API response for that surface carries it, not only if the consumer renders it as a visible cell. Server-side sort and filter inputs count as carries because the response must include the column. Ticker's 5 sub-scores count as carries because /api/ticker is SELECT * and Step 10 will render them in JS. This is the canonical lens for any future registry-vs-reality audit. Applied a second time in Part 41 (Step 9.5, reversion correction).

### Phase 3 (implementation): canonical Step 6 + 7a shipped, plus extras, on `refactor/component-registry`

Steps 1 through 5.5 shipped in Parts 39/40 (commits 53ac17c, 2196ff4, 6d57ae7, e1eb2aa, 6d32096, 37cd4a5, acf12b6). Suite at Part 40 close: 403 passed, 2 skipped.

**Part 41 commit-to-canonical-step mapping.** The commit-message "Step N" labels are this session's local working sequence and do NOT map 1:1 to canonical plan steps. Reconciled below by mapping table, canonical numbering preserved as the spine (audit-trail rule).

| SHA | Commit subject | Migrated | Canonical step | Completeness |
|------|----------------|----------|----------------|--------------|
| `8536b8a` | Phase 3 Step 6: switch three /api/signals* handlers to registry-driven projection | `/api/signals`, `/api/signals/sector/<sector>`, `/api/signals/<rating>` to `surface='signals'` | Step 6 | full |
| `fdffad2` | Phase 3 Step 6: shape-lock test for registry-driven signals endpoints | `tests/test_signals.py` (5 cases) locking the signals surface | Step 6 (test) | full (test half) |
| `91376a0` | Phase 3 Step 7: switch api_industry handler to registry-driven projection | `api_industry` (`/api/industry/<name>`), later `surface='industry'` | none | extra, not in plan (handler the original plan omitted; caught by Step 7 inventory) |
| `b39f3b8` | Phase 3 Step 7: shape-lock test for api_industry registry projection | `tests/test_signals.py` 6th case for `api_industry` | none | extra, not in plan (test for the extra handler) |
| `b04d032` | Phase 3 Step 8: switch dashboard top_strong/top_bearish queries to registry-driven projection | `dashboard()` `top_strong` + `top_bearish`, later `surface='dashboard'` | Step 7a | partial (dashboard half of canonical Step 7; watchlist half = Step 7b not addressed) |
| `01606c3` | Phase 3 Step 9: switch _get_penny_pick_full to registry-driven projection | `_get_penny_pick_full` (penny spotlight, `/api/penny/stock-of-day`), `surface='signals'` deliberate alias | none | extra, not in plan (handler the original plan omitted; caught by Step 7 inventory) |
| `d3919a1` | Phase 3 Step 9.5: correct reversion surface set (add dashboard+industry per 5.5 lens), re-point handlers to semantic surfaces | registry `reversion` surfaces += `dashboard`, `industry`; re-point dashboard to `surface='dashboard'`, api_industry to `surface='industry'`; industry test bound to `components_for_surface("industry")` | new, 5.5-class | extra, registry correction (mirrors Step 5.5) |

Net against the canonical plan: Step 6 full (impl + test); Step 7a (dashboard) done, Step 7b (watchlist) not done; plus three out-of-plan-but-correct items (`api_industry`, `_get_penny_pick_full`, the reversion surface correction). No canonical step beyond 7a was advanced.

### Remaining Phase 3 work (canonical order)

| Step | File(s) | Status | Change |
|------|---------|--------|--------|
| 7b | web/app.py | RESERVED, parked | watchlist join projection to `surface='watchlist'`. No code target exists today (no watchlist SQL hand-lists component columns). The `watchlist` surface (momentum, quality, insider, sector_strength; no reversion) is wired for future sub-score rendering, not active. |
| 8 | web/app.py | OUTSTANDING, next target | ticker detail `/api/ticker` `SELECT *` to explicit `signal_scores_projection(surface='ticker')`. Highest value: the `ticker` surface carries the full component set including the five v0.17.0 sub-scores (earnings, piotroski, inst_own, analyst_mom, altman_penalty) plus value/sector/volume/legal. Prerequisite for canonical Step 10's JS consumption. |
| 9 | web/app.py | OUTSTANDING | `allowed_sorts` additive merge with `sortable_columns()` (preserves non-component sort keys). |
| 10-15 | web/templates/ | NOT STARTED | Template-loop sub-arc. Per-file breakdown below is INDICATIVE, to be confirmed by each step's own Phase 1 inventory, NOT canonical. Verification rhythm changes from JSON key-checks to numbered visual browser walks (free/pro/elite), pixel-parity confirm. |
| 16 | merge to main | END OF ARC | Multi-tier browser sweep (free/pro/elite), pixel-parity confirm, fast-forward or squash-merge by Mark's preference. |

INDICATIVE template breakdown for Steps 10-15 (confirm per step, do not treat as canonical): 10 = ticker.html (window.COMPONENTS_DATA + JS render shim, largest single step); 11 = screener.html + penny_screener.html per-row cells; 12 = index.html signals + sector tabs; 13 = dashboard.html spotlight breakdown; 14 = watchlist.html per-row cells; 15 = industry.html per-row cells.

### Surface strategy (settled this session)

- Per-surface component sets are real and now correct. `reversion_score` carries on: **ticker, screener, signals, dashboard, industry** (corrected from a 3-surface under-listing in Step 9.5, per the Step 5.5 carried-response lens; the dashboard and industry responses already carried reversion, and dashboard `_thesis()` consumes it).
- Penny: deliberate `surface='signals'` alias. No penny surface exists by design.
- Watchlist surface tag (momentum, quality, insider, sector_strength) reserved for future sub-score rendering. No current code target.

### Reconciliation note (process working as designed)

The Step 7 inventory-driven approach FOUND the original plan's handler-list gaps: `api_industry` and `_get_penny_pick_full` were omitted from the canonical Phase 1 enumeration. The two-phase process (inventory before edit) surfaced and closed those gaps in-session. Record this as the method working as intended, not a plan failure.

## Operational notes for the arc

- **Branch discipline:** `refactor/component-registry` is the working branch. GitHub Desktop and any other terminal session must stay on this branch for the whole arc. Three silent HEAD drifts in an earlier part were caused by GitHub Desktop branch clicks; none since the operational rule landed. Baseline verification at session open includes `git branch --show-current` against this exact string.
- **P23 hook is path-matching for web/app.py and content-scanning for everything else.** Confirmed empirically across Steps 4 through 9.5: every web/app.py touch trips the hook regardless of diff content. Each web/app.py commit needs Mark's explicit `--no-verify` authorisation after Athena confirms the diff is auth-clean and Mark reviews it. database/db.py, signals/components.py, and tests/ do not trip on clean diffs (Steps 2, 4.5, 5.5, plus the Step 6/7/9.5 test commits all committed cleanly; Step 9.5 bundled a web/app.py change so it took the `--no-verify` path).
- **Runtime drift:** any web/app.py commit needs a gunicorn restart at commit time. `launchctl kickstart -k gui/$(id -u)/io.thesignalvault.gunicorn`. Verify post-restart that the master is launchd-managed (PPID 1) and owns 5001. Clean restarts throughout Part 41 (master plus worker, `-w 1`).
- **launchd `last exit code` is backward-looking, not a current-health signal.** Assert "current PID stable AND no recent err.log entries" rather than reading the exit-code field.
- **Step 4.5 / 5.5 amendments in effect:** any surface-projection switch uses `signal_scores_projection(surface='<name>', ...)`. Any registry-vs-reality discrepancy is resolved by the response-carries lens, not the render-cell lens. Applied twice now (5.5 sector_strength on signals, 9.5 reversion on dashboard/industry).

## Known pre-existing FOLLOWUPS unchanged this session

- Dormant `initialise_schema` gap (does not provision volume_score or scoring_version on fresh-DB init). P19-class fix when prioritised. Not in this arc.
- AGENTS.md + docs/dash_sweep_plan.md tracked since Part 38 close.
- Orphan-gunicorn diagnosis (Part 40): session-open baseline check should be strengthened from "at least one gunicorn process" to "exactly one master with launchd-managed PPID chain bound to 5001". Pre-existing condition, fixed in-session, worth codifying.
- PROJECT_CONTEXT Amendment B paragraph records the Step 5.5 lens as correcting "one discrepancy". Part 41 applied the same lens a second time (Step 9.5, reversion). Optional one-line addendum next docs-sync; not a contradiction.

## Branch state (explicit, for the next fresh chat)

- All Step 6 through 9.5 CODE commits live on `refactor/component-registry` and are NOT in main: `8536b8a`, `fdffad2`, `91376a0`, `b39f3b8`, `b04d032`, `01606c3`, `d3919a1`.
- `main` carries ONLY the docs-sync commit (HANDOFF + PROJECT_CONTEXT) from this session's cherry-pick. No arc code on main.
- Next session opens with the 7-gate baseline. `git branch --show-current` MUST return `refactor/component-registry` before any work. GitHub Desktop stays on the feature branch for the whole arc.
- Next active target: canonical **Step 8** (ticker detail `/api/ticker` SELECT* to `surface='ticker'`).
