# SignalIntel Session Handoff

**Last updated:** end of Part 43 (15 June 2026)
**Engine:** SCORING_ENGINE_VERSION 0.18.0 (bumped this session for the Piotroski P5 fix)
**Repo:** branch `feature/yahoo-pipeline`, cut fresh off `main` at `ba96ea8`. Five commits ahead of main: `6c67aa7` (methodology docs), `4f440ee` (Piotroski P5 fix, 0.18.0), `3830bef` (Elite sub-score surfacing), `528d9a7` (Part 43 close doc sync), `a3f34e9` (Telegram P13 fix). The doc commits cherry-pick to main; the code commits stay on the branch.
**Suite:** 418 passed, 3 skipped, exit 0. Skips: `fmp_price_targets` and `economic_calendar` (both known-empty), plus a data-conditional `test_themes.py` skip (no STRONG_BUY in the latest run; flips with DB state).
**Runtime:** gunicorn live, master launchd-managed (PPID 1) on 5001. Restarted twice this session, once after the Piotroski fix and once after the surfacing commit.

## Where we are

The Yahoo arc opened on `feature/yahoo-pipeline`. The Part 43 handover premise was WRONG and has been corrected in PROJECT_CONTEXT: the Yahoo Finance pipeline was already fully built, scheduled, and live (six Yahoo jobs in the scheduler), and components 9-13 already scored, persisted on `signal_scores`, and fed the composite. The arc was therefore not "build Yahoo ingest"; it became "reconcile the live components, fix a latent P5 bug, and surface the persisted sub-scores."

## Part 43 work (this session)

| Commit | Type | What shipped | Verified by |
|---|---|---|---|
| `6c67aa7` | docs only | Five reconciliation docs `docs/methodology/component_09..13` documenting actual live scorer behaviour from source bytes, plus `docs/methodology/FOLLOWUPS.md` banking divergence findings (one P5 violation, one stale docstring, latent tail) | reconciliation gates (line refs, glyph-clean, no .py touched) |
| `4f440ee` | scoring, 0.18.0 | Piotroski P5 fix: missing line items were counted as failed F-score criteria, producing sub-neutral scores from absent data. Now coverage-aware (absent inputs EXCLUDED, floor at 5 of 9 returns neutral 50, Option B humility cap at 6 for partial coverage, full-coverage identity preserved). Rider: corrected stale analyst_mom docstring to v0.17.0 hard-only. Added partial-coverage test | P29 probe first (about 2,332 sub-neutral scores, about 206 absent-data-driven), suite green, gunicorn restart |
| `3830bef` | render + gate | Elite-only "Advanced Signals" section on the ticker page: four sub-score chips plus the Altman distress flag (risk badge, only when penalty non-zero). Server-side Elite-strict gate (`strip_subscores_for_non_elite` + `ELITE_ONLY_SUBSCORE_FIELDS`) strips the five fields from `/api/ticker` JSON for non-Elite, price-independent. `subscores_locked` flag drives the teaser. No version bump | six browser walks, including the mandatory Pro leak check (five fields ABSENT from Pro `/api/ticker` JSON via Network tab on DPZ), suite green, gunicorn restart |
| `a3f34e9` | render fix | Telegram P13: `job_daily_summary` leaked the raw internal rating code (BUY, STRONG_BUY) into the subscriber-facing daily summary via `rating.replace('_',' ')`, while the watchlist builder already translated via `tier_short`. Fixed to route through `tier_short` (display labels: Strong, Very Strong), fixed the summary-header em-dash to a colon, added `tests/test_notification_labels.py` (P15 signal-and-silence: display label present, raw code absent). Display-only, no version bump | suite 418 green; deployed via SCHEDULER kickstart, NOT gunicorn (job runs in the scheduler process) |

## Queued work (next arc first)

1. **Scheduler rescore on 0.18.0.** Code is live but the persisted `piotroski_score` values in the DB are still 0.17.0 numbers until the scheduler rescores on its next cycle. No action needed; recorded so a backtest reader does not mistake stale rows for the new logic.
2. **Component 14, FINRA short-interest.** The genuine net-new build and the next arc. Probe-first, correlation gate (|r| >= 0.6 is a stop-and-discuss threshold), version bump, its own diagnostic-then-implement sequence.
3. **fmp_price_targets yahoo reroute.** The table has NO writer wired (`fetch_price_target` / `save_price_target` have no caller; empty by construction), so the Value component (#6) scores on an empty table. Reroute decision LOCKED: source price targets from yfinance `Ticker.info` `targetMeanPrice` and retire the FMP path. Not yet implemented; queued.
4. **FOLLOWUPS latent tail.** ISO-date string-sort couplings (09/10/13), dead guard (09), 50.0 collision (10), init-as-upgrade (12), vestigial `total_revenue` in `ALTMAN_LOOKUPS` (13). Banked in `docs/methodology/FOLLOWUPS.md`, not urgent.
5. **Components 15/16 (News Sentiment, Options Flow).** Remain deferred, dashboard-only per the composite-purity invariant.
6. **Production Stripe flip** (queued, unchanged).

## Test accounts (for tier-gated walks)

- `markn` = elite
- `beta2` = pro
- `mark2` = free

## Operational notes (carry forward)

- **Branch discipline:** confirm `git branch --show-current` before any work. GitHub Desktop branch clicks have caused silent HEAD drifts before.
- **P23 hook:** `web/app.py` is path-matching (any touch trips the hook). The hook reads `[y/N]` from `/dev/tty`, so an auth-adjacent commit can only be confirmed from Mark's own terminal; from CC's non-interactive shell it exits 1 with "No controlling terminal". CC stages, surfaces the diff, and hands Mark the literal `git commit` to run himself. CC does not use `--no-verify` unless Mark explicitly authorises it. Docs-only and `database/db.py` / `signals/components.py` / `tests/` commits on auth-clean diffs pass the hook silently.
- **Hook Pass 0 (dash check):** the pre-commit hook rejects any ADDED line containing an em-dash (U+2014) or en-dash (U+2013) on ANY staged path, including docs. Keep added content glyph-clean or the commit blocks.
- **Runtime drift:** any `web/app.py` or scorer commit needs a gunicorn restart (`launchctl kickstart -k gui/$(id -u)/io.thesignalvault.gunicorn`); verify the master is launchd-managed (PPID 1) and owns 5001 post-restart. Assert "current PID stable AND no recent err.log entries", not the backward-looking launchd exit code.
- **Scheduler vs gunicorn are TWO separate launchd processes (not interchangeable).** The scheduler runs as `io.thesignalvault.scheduler` (launchd, `venv/bin/python main.py scheduler`), distinct from the gunicorn web worker (`io.thesignalvault.gunicorn`). Changes to scheduler jobs (daily summary, scrapers, scoring jobs, anything in `main.py`'s job functions) deploy via `launchctl kickstart -k gui/$(id -u)/io.thesignalvault.scheduler`; changes to web routes (`web/app.py`) deploy via the gunicorn kickstart. A gunicorn restart does NOT deploy a scheduler-job change and vice versa. Near-miss this session: the Telegram fix lives in a scheduler job, so a gunicorn restart would not have shipped it. Confirm a fresh PID with PPID 1 after either kickstart.
- **Registry-vs-reality audits** use the Step 5.5 carried-response lens (a column belongs on a surface if the API response carries it, not only if a cell renders it).

## Known pre-existing FOLLOWUPS (unchanged this session)

- Dormant `initialise_schema` gap (does not provision volume_score or scoring_version on fresh-DB init). P19-class fix when prioritised.
- PROJECT_CONTEXT.md still carries pre-existing em/en dashes; a full sweep is the tracked task (not done this session). The Piotroski and surfacing commits added only glyph-clean content.
- Orphan-gunicorn baseline check: assert "exactly one master with launchd-managed PPID chain bound to 5001", not "at least one gunicorn process".

## Working-style standing instruction (in effect from Part 42)

- Replies are prompts-only: when handing Mark something to run or paste, give the literal block with no surrounding narration of steps taken.
- Label every copy block as **CC-prompt** (paste into a Claude Code session) or **Terminal** (run in his own shell).
- Lead with the artifact or result; do not narrate the work step by step.

## Branch state (for the next fresh chat)

- `feature/yahoo-pipeline` is five commits ahead of `main` (`6c67aa7`, `4f440ee`, `3830bef`, `528d9a7`, `a3f34e9`) plus this post-close doc-sync commit; not pushed, not cherry-picked. Mark drives the push / cherry-pick / return sequence.
- The doc-sync commits (`528d9a7` and this one, HANDOFF.md / PROJECT_CONTEXT.md / FOLLOWUPS.md) are the cherry-pickable-to-main ones; the code commits (`4f440ee`, `3830bef`, `a3f34e9`) stay on the branch. FOLLOWUPS.md and the methodology docs were first added in code-adjacent commit `6c67aa7`.
- Next active target: **Component 14 (FINRA short-interest)**, the next net-new build.
