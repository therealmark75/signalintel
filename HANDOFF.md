# SignalIntel Session Handoff

**Last updated:** end of Part 45 (19 June 2026)
**Engine:** SCORING_ENGINE_VERSION 0.19.0, UNCHANGED this session (neither Part 45 commit touched scoring).
**Repo:** branch `feature/watchlist-earnings`, HEAD `3fe48bd`, level with origin. The Yahoo arc is CLOSED and merged to `main` at Part 45 open (merge commit `2d713c7`); `main` now carries the full Yahoo arc (ingest pipeline, components 9 to 14, price-target reroute). Two code commits this session, both deployed: `ab63a0d` (watchlist earnings notification job, Path A) and `3fe48bd` (economic_calendar full retirement).
**Suite:** 429 passed, 1 skipped, exit 0. The single remaining skip is `fmp_price_targets` (test_data_integrity.py:336, empty until the 02:30 job first fires). The `economic_calendar` skip is GONE (that test was removed in the retirement).
**Runtime:** scheduler live as `io.thesignalvault.scheduler`, last restarted this session to PID 43738, with the new job registered: `Watchlist Earnings Alerts 06:30` (id `watchlist_earnings_alerts`, Mon-Fri, fires right after the 06:05 `fmp_earnings` calendar refresh). gunicorn restarted this session to PID 47870 (carries the economic_calendar route removal). The `economic_calendar` table was physically DROPPED this session (manual one-line drop at deploy, not scripted into any init path).

## Where we are

Part 45 opened with the Yahoo arc closed and merged to `main` (merge commit `2d713c7`), so `main` now carries the full Yahoo work: the ingest pipeline, components 9 to 14, and the price-target reroute. Work then moved to a fresh branch, `feature/watchlist-earnings`, which shipped two commits this session. First, the watchlist earnings notification job (Path A): a daily scheduler job that sends one grouped Telegram digest naming watchlist-held tickers reporting the next day, with a net-new per-subscriber-shaped dedup table so each (subscriber, ticker, earnings_date) fires once. Second, the full retirement of the economic_calendar feature: Part 44 removed the engine side, and Part 45 removed the surviving web, dashboard, scraper, db, and table surface. Neither commit touched scoring, so the engine stays at 0.19.0.

## Part 45 work (this session)

| Commit | Type | What shipped | Verified by |
|---|---|---|---|
| `ab63a0d` | feature, scheduler | Watchlist earnings notification job (Path A). `job_watchlist_earnings_alerts` (cron `watchlist_earnings_alerts`, 06:30 Mon-Fri, after the 06:05 `fmp_earnings` refresh) queries tickers in alerts_enabled watchlists whose MIN(earnings_date) in FMP `earnings_calendar` equals a Python-injected target date (defaults to tomorrow), sends one grouped global-chat digest, then writes per-(user_id, ticker, earnings_date) rows to the net-new `earnings_notifications_sent` table via INSERT OR IGNORE on a truthy send only (send-then-record). New table created in initialise_schema, no FOREIGN KEY by design. 7 unit tests | suite 433 green at commit; live smoke test fired one digest for TSM at target 2026-07-16, wrote one dedup row, then row deleted to restore clean state; scheduler kickstart to PID 43738, job registered |
| `3fe48bd` | retirement | economic_calendar FULL retirement. Removed the `/events` page route and template, the three `/api/economic-calendar` routes, the dashboard CLI panel, the FMP `fetch`/`save`/`refresh_economic_calendar` helpers, the db.py `insert_calendar_events` and `get_upcoming_events` helpers, the CREATE in initialise_schema, and three stale `/events` nav/footer links. Table dropped manually at deploy (not scripted into init). General FMP entitlement tests kept and repointed to the live `/earnings-calendar`; only the economic-calendar-specific job test deleted | suite 429 green, exit 0; gunicorn kickstart to PID 47870, `/events` and `/api/economic-calendar` both return 404, `/markets` and `/dashboard` 302 (live); completeness grep clean of live wiring |

## Queued work

1. **Backtest validation harness.** Unblocked by sub-score persistence (0.17.0+), not yet scoped. Athena's recommended next build for Part 46.
2. **FOLLOWUPS latent tail.** ISO-date string-sort couplings (09/10/13), dead guard (09), 50.0 collision (10), init-as-upgrade (12), vestigial `total_revenue` in `ALTMAN_LOOKUPS` (13). Banked in `docs/methodology/FOLLOWUPS.md`, not urgent.
3. **Components 15/16 (News Sentiment, Options Flow).** Remain deferred, dashboard-only per the composite-purity invariant.
4. **Production Stripe flip** (P32, queued, unchanged).
5. **Short-interest strengthening** (NOT queued). A separate future deliberate decision, not a backlog item; Component 14 shipped at relocation parity, which was the calibration target, not a ceiling. Banked in FOLLOWUPS.
6. **Future Path B: per-subscriber earnings delivery.** The earnings job ships on Path A (global-chat, single recipient) because no per-user Telegram chat id exists. True per-subscriber delivery needs `users.telegram_chat_id` plus a bot linking flow, a real arc and P23 territory. The dedup table is already keyed per-subscriber, so it is shaped for Path B with no migration; only the delivery layer changes.

### Shipped this session (was queued)
- Watchlist-earnings mini-arc: shipped `ab63a0d`, Path A, live. Diagnosis corrected three premises from the original mini-arc note: the forward feed is FMP `earnings_calendar` not Yahoo component-11; no per-user chat id exists, so delivery is global-chat; no dedup precedent existed, so the table is net-new.
- economic_calendar web-side cleanup: shipped `3fe48bd` as a FULL retirement (not just the web routes the Part 44 note scoped). Feature now entirely gone.

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

- `feature/watchlist-earnings` code commits are pushed (HEAD `3fe48bd`, level with origin): `ab63a0d` (watchlist earnings job) and `3fe48bd` (economic_calendar full retirement). This Part 45 doc-sync commit lands on top and is NOT yet pushed, so the branch will be one commit ahead of origin until Mark pushes.
- `main` carries the full Yahoo arc as of Part 45 open (merge commit `2d713c7`). The two Part 45 code commits stay on the branch; this Part 45 doc-sync commit is the next cherry-pick candidate to `main`. Mark drives the push / cherry-pick / return sequence himself (this session STOPS at the docs commit, before any branch switch).
- Next active target: **backtest validation harness**, Athena's recommended next build for Part 46 (unblocked by sub-score persistence since 0.17.0, not yet scoped).
