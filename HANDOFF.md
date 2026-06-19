# SignalIntel Session Handoff

**Last updated:** end of Part 44 (19 June 2026)
**Engine:** SCORING_ENGINE_VERSION 0.19.0 (bumped this session for Component 14, the short-interest penalty)
**Repo:** branch `feature/yahoo-pipeline`, HEAD `4d9b3ca`, level with origin. `main` still at `8bab92d` (Part 43 docs already cherry-picked there; this Part 44 doc-sync commit is the next cherry-pick candidate). Three feature commits this session, all deployed: `29ab9d4` (economic_calendar retirement), `f16f8d7` (price-target reroute, 0.18.1), `4d9b3ca` (Component 14 short-interest penalty, 0.19.0).
**Suite:** 426 passed, 2 skipped, exit 0. Skips: `fmp_price_targets` empty until the new 02:30 job first fires, `economic_calendar` empty (retired this session).
**Runtime:** scheduler live as `io.thesignalvault.scheduler` on PID 37251 (PPID 1, launchd-managed), 22 jobs including the new `Yahoo Price Targets (priority)` 02:30 Mon-Fri job. Latest scoring run stamped 0.19.0 with `short_interest_penalty` populated on all 11,091 scored rows (min -3.0). gunicorn separately live on 5001.

## Where we are

Part 44 closed the Yahoo arc's remaining items and shipped Component 14. Three commits, all deployed and live: the economic_calendar retirement (dead FMP `job_economic_calendar` plus its daily false 402 alert plus the FinViz writer removed), the price-target reroute (`fmp_price_targets` now sourced from yfinance `Ticker.info` `targetMeanPrice` via a dedicated 02:30 priority job, the dead FMP writer retired), and Component 14 (short interest promoted out of `score_quality` into a standalone all-tiers additive penalty). Component 14 was the genuine net-new scoring work; the other two were cleanup and a write-source swap.

## Part 44 work (this session)

| Commit | Type | What shipped | Verified by |
|---|---|---|---|
| `29ab9d4` | scheduler retire | economic_calendar retirement: removed `job_economic_calendar` (dead FMP path, false 402 alert on every run), its daily Telegram entitlement alert, and the FinViz `scrape_economic_calendar` writer inside the news job. Table, web routes, and the FMP `refresh_economic_calendar` helper retained for a separate web-side cleanup (see FOLLOWUPS). News path intact | suite green, scheduler kickstart to a fresh PID, no economic_calendar job in registration |
| `f16f8d7` | reroute, 0.18.1 | price-target reroute to yfinance: new `job_yahoo_price_targets` (02:30 Mon-Fri, priority universe) fetches `targetMeanPrice` plus `numberOfAnalystOpinions` into the existing `fmp_price_targets` table; dead FMP `fetch_price_target` / `save_price_target` removed. Reader and target-price blend untouched (PATCH, cache-source swap). 4 unit tests | suite 423 green, scheduler kickstart, job registered at 02:30 |
| `4d9b3ca` | scoring, 0.19.0 | Component 14: short interest extracted from `score_quality` and promoted to `score_short_interest_penalty` (additive 0 / -1 / -2 / -3 at >10 / >20 / >30 percent of float), calibrated to reproduce the prior quality-embedded composite impact (relocate, not amplify). All-tiers risk flag, excluded from the proprietary and Elite-only field sets. New `short_interest_penalty` column | two-sided design built then rejected on P29 (+0.99 inflation, 601 upgrades vs 14 downgrades); penalty P29 mean -0.004, 14 label changes; suite 426 green; live-DB migrated; scheduler kickstart, 0.19.0 stamped |

## Queued work

1. **economic_calendar web-side cleanup.** The retirement (`29ab9d4`) left the web routes (`/api/economic-calendar/refresh`, the `/events` read and banner routes in `web/app.py`), the FMP `refresh_economic_calendar` helper in `fmp_scraper.py`, the dead `db.py` `insert_calendar_events` helper, and the empty `economic_calendar` table. Harmless (the job is gone, nothing repopulates the table), but a future cleanup. Touches `web/app.py` so it trips P23 (Mark's terminal). Banked in FOLLOWUPS. Separate commit when convenient.
2. **Watchlist-earnings Telegram mini-arc.** Notify watchlist subscribers about 24h before a held ticker reports earnings, reusing the already-ingested component-11 Yahoo earnings timestamps. Needs dedup-state design to avoid re-alerting the same earnings date daily. Banked in FOLLOWUPS.
3. **FOLLOWUPS latent tail.** ISO-date string-sort couplings (09/10/13), dead guard (09), 50.0 collision (10), init-as-upgrade (12), vestigial `total_revenue` in `ALTMAN_LOOKUPS` (13). Banked in `docs/methodology/FOLLOWUPS.md`, not urgent.
4. **Components 15/16 (News Sentiment, Options Flow).** Remain deferred, dashboard-only per the composite-purity invariant.
5. **Production Stripe flip** (queued, unchanged).

### Shipped this session (was queued)
- Component 14 short-interest penalty: shipped `4d9b3ca`, 0.19.0, live. Built two-sided first, rejected on P29 inflation, reshaped to a one-sided additive penalty at relocation parity.
- fmp_price_targets yahoo reroute: shipped `f16f8d7`, 0.18.1, live.
- Scheduler rescore on the new engine: done. The restart this session triggered a 0.19.0 scoring run, so persisted rows are now 0.19.0 (no longer stale 0.18.0 / 0.17.0).

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

- `feature/yahoo-pipeline` code commits are pushed (HEAD `4d9b3ca`, level with origin). This Part 44 doc-sync commit lands on top and is NOT yet pushed, so the branch will be one commit ahead of origin until Mark pushes. `main` is at `8bab92d` (Part 43 docs already cherry-picked there). The Part 44 doc-sync commit is the next cherry-pick candidate to `main`; the three Part 44 feature commits (`29ab9d4`, `f16f8d7`, `4d9b3ca`) stay on the branch. Mark drives the push / cherry-pick / return sequence.
- The doc-sync commits (`528d9a7` and this one, HANDOFF.md / PROJECT_CONTEXT.md / FOLLOWUPS.md) are the cherry-pickable-to-main ones; the code commits (`4f440ee`, `3830bef`, `a3f34e9`) stay on the branch. FOLLOWUPS.md and the methodology docs were first added in code-adjacent commit `6c67aa7`.
- Next active target: **Component 14 (FINRA short-interest)**, the next net-new build.
