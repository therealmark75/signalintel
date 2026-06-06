# SignalIntel Session Handoff

**Last updated:** end of Part 42 (6 June 2026)
**Engine:** SCORING_ENGINE_VERSION 0.17.0 (unchanged)
**Repo:** component-rendering refactor arc COMPLETE and MERGED to main. `main` carries the arc via the `--no-ff` merge commit `6c43330` (pushed, `22824d1..6c43330`). Feature branch `refactor/component-registry` tip `736cc2c`, fully merged into main. HEAD returned to `refactor/component-registry` at session close.
**Suite:** 409 passed, exit 0, 2 known skips (`fmp_price_targets`, `economic_calendar`).
**Runtime:** gunicorn live, master launchd-managed (PPID 1) on 5001.

## Where we are

The component-rendering refactor (registry-driven rendering, the hard prerequisite before the Yahoo Finance pipeline and components 9-16) is **DONE and MERGED**. All canonical steps shipped across Parts 39-42; the arc is on main.

Rendering is now the canonical component registry (`signals/components.py`) projected to handlers via `signal_scores_projection(surface=...)` and to templates via the injected `components` Jinja var / `window.COMPONENTS_DATA` shim.

The next arc (Yahoo Finance pipeline + components 9-16) is now **UNBLOCKED** (this refactor was its hard prerequisite).

## Component-rendering refactor: COMPLETE + MERGED

Steps 1-7 + 5.5 + 9.5 shipped in Parts 39-41 (registry, projection helper, context processor, surface filter, handler migrations, surface corrections). Part 42 shipped the remaining handler steps and the entire template sub-arc:

| Canonical step | SHA | What shipped | Verified by |
|---|---|---|---|
| Step 8 | `ed5e354` | `api_ticker` signal_scores read: `SELECT *` to `signal_scores_projection(surface='ticker')` | JSON-shape gate (16-key `payload.signal`, all required columns present) |
| Step 9 | `20dcd4f` | `api_screener` sort gate derived from `sortable_columns()` + explicit `screener_extras` (composed set proven identical to the prior 25-key literal) | set-equality gate |
| Step 10 | `841f83f` | `ticker.html` rendering driven by `window.COMPONENTS_DATA` + a behaviour table keyed by `key`; same 8 components, pixel-identical | browser walk (ticker) |
| Step 11 | `b819164` | `dashboard.html` spotlight breakdown via the `components` Jinja var, explicit 3-key allowlist (momentum/quality/insider), no reversion added | byte-diff of both tiers (elite + non-elite) |
| Step 12 | `6524106` | `industry.html` cells via the `window.COMPONENTS_DATA` shim, 3-key allowlist, reversion excluded | browser walk (industry) |
| Step 13 | `736cc2c` | `penny.html` SOTD cells via a shim gated inside `{% if not locked %}`, 3-key allowlist; byte-identical both tiers | browser walk (penny, Elite + non-Elite) |
| Step 16 (merge) | `6c43330` | `--no-ff` merge to main; one additive PROJECT_CONTEXT.md conflict resolved (Filing Narrative Component block kept); main pushed | merge + suite + runtime |

Verification rhythm: handler steps (8, 9) by JSON-shape / set-equality gates; template Steps 10, 12, 13 by browser walks; Step 11 by byte-diff of both rendered tiers.

## Surfaces deliberately NOT migrated (reasons recorded so a future session does not re-litigate)

| Surface | Reason |
|---|---|
| `watchlist.html` | Heterogeneous Jinja cells (sector uses bespoke `round\|int` + color logic; momentum/quality/insider uniform). The real coupling lives in `database/db.py:get_watchlist`, which hand-lists the columns, NOT in the template. A template-only loop would not decouple the data layer. Out of arc scope. |
| `screener.html` | Renders only the `composite_score` aggregate + a single bespoke `sector_strength_score` cell. No core component-cell SET to collapse. Not analogous to ticker/industry/penny. |
| `index.html` | DEAD CODE. The `/` route unconditionally `redirect`s to `/dashboard` at `app.py:221`, before the only `render_template("index.html")` at line 240. Never served. Its signals/sector tables are not replicated on any live surface. Do not migrate dead code. |
| `penny_screener.html` | Component-column names appear only as sort `<option>` values and preset configs, not as rendered score cells. Nothing to migrate. |

The reachable surfaces that genuinely render a core component-cell set are exactly ticker.html, dashboard.html, industry.html, penny.html (all migrated), plus the dead index.html (skipped).

## Queued work (next arc first)

1. **Yahoo Finance pipeline + components 9-16 (NEXT, now unblocked).** The component-rendering refactor was the hard prerequisite and is done. This arc adds the next sub-score components and their data source.
2. **Backtest harness.** Blocked on persisting the five v0.17.0 sub-scores (earnings, piotroski, inst_own, analyst_mom, altman_penalty) as their own `signal_scores` columns first; the harness needs sub-score history to backtest against. Sequence the persistence-columns change ahead of it.
3. **FINRA short-interest** integration (queued, unchanged).
4. **Production Stripe flip** (queued, unchanged).

## Operational notes (carry forward)

- **Branch discipline:** the arc is merged, but until the next arc's branch is cut the session-open baseline still asserts `git branch --show-current`. GitHub Desktop branch clicks caused silent HEAD drifts earlier in the arc; keep the rule.
- **P23 hook:** `web/app.py` is path-matching (any touch trips the hook). Each `web/app.py` commit needs Mark's explicit `--no-verify` in his own terminal after he reviews the auth-clean diff. CC surfaces the trip and the staged diff and waits; CC does not self-clear. `database/db.py`, `signals/components.py`, and `tests/` commit cleanly on auth-clean diffs.
- **Runtime drift:** any `web/app.py` commit needs a gunicorn restart (`launchctl kickstart -k gui/$(id -u)/io.thesignalvault.gunicorn`); verify the master is launchd-managed (PPID 1) and owns 5001 post-restart. `launchd last exit code` is backward-looking; assert "current PID stable AND no recent err.log entries" instead.
- **Registry-vs-reality audits** use the Step 5.5 carried-response lens (a column belongs on a surface if the API response carries it, not only if a cell renders it). Applied at 5.5 (sector_strength on signals) and 9.5 (reversion on dashboard/industry).

## Known pre-existing FOLLOWUPS (unchanged this session)

- Dormant `initialise_schema` gap (does not provision volume_score or scoring_version on fresh-DB init). P19-class fix when prioritised. Not in this arc.
- AGENTS.md + docs/dash_sweep_plan.md tracked since Part 38 close. PROJECT_CONTEXT.md still carries pre-existing em/en dashes; a full sweep is the tracked task (not done this session).
- Orphan-gunicorn baseline check: assert "exactly one master with launchd-managed PPID chain bound to 5001", not "at least one gunicorn process".

## Working-style standing instruction (in effect from Part 42)

- Replies are prompts-only: when handing Mark something to run or paste, give the literal block with no surrounding narration of steps taken.
- Label every copy block as **CC-prompt** (paste into a Claude Code session) or **Terminal** (run in his own shell).
- Lead with the artifact or result; do not narrate the work step by step.

## Branch state (for the next fresh chat)

- Arc fully merged: `main` at `6c43330` (merge commit, pushed); feature branch `refactor/component-registry` at `736cc2c`, merged in.
- Next session opens on `refactor/component-registry` (or a fresh branch cut for the Yahoo arc). Confirm `git branch --show-current` before any work.
- Next active target: **Yahoo Finance pipeline + components 9-16** (unblocked).
