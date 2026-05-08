SIGNALINTEL — SESSION HANDOFF
End of Fri 8 May 2026, ~13:30 BST → Pickup later today or tomorrow

==========================================================
WHO YOU ARE
==========================================================

Mark calls you "Athena" in this project. You are NOT Claude Code.
CC writes the code in Mark's terminal. You are the technical lead:
plan sessions, draft prompts, walk verification gates after CC
reports done, push back constructively, capture lessons.

Read PROJECT_CONTEXT.md alongside this handoff for full context on
the product, tech stack, communication preferences, and process
invariants.

==========================================================
SESSION SUMMARY (THIS CHAT, MORNING + EARLY AFTERNOON)
==========================================================

Mark woke up to verify last night's bulk exchange backfill. The
backfill completed cleanly (10:06h runtime, 11,109 tickers updated,
0 NULL_RESULTs, 55 errors all delisted 404s). But verification 
surfaced two architectural problems that stacked:

1. Exchange data was being stored on screener_snapshots (per-snapshot
   table). Every scheduler scrape created new rows with exchange=NULL,
   superseding backfilled data. Ticker pages still showed "—" for
   non-priority tickers despite 11,109 rows of metadata sitting in
   the DB.

2. The scheduler running in the GREEN terminal was started yesterday
   ~16:00 BST, before any of yesterday's commits (Volume Confirmation,
   rel_volume fix, config refactor) were on disk. It had been running
   stale in-memory code for ~24 hours, invisible in logs.

Both diagnosed, both fixed. Plus discovered a third structural issue
(scoring trigger fires mid-scrape) and fixed that too.

ACCOMPLISHED (in chronological order):

1. ✅ ticker_metadata table architectural fix (commit e83d8d6)
   - New ticker_metadata table keyed on ticker (PK), exchange + 
     timestamps
   - Migration backfills from existing screener_snapshots rows
   - api_screener route updated to LEFT JOIN ticker_metadata
   - api_ticker route updated to return tm.exchange
   - ticker.html template reads tm.exchange (not sc.exchange)
   - screener_snapshots.exchange column left in place but no longer
     written to (deprecation cleanup deferred)
   - 11,122 ticker_metadata rows post-migration, all populated
   - Verified: F (Ford, non-priority) renders NYSE on ticker page,
     proving the architectural fix works for the population that
     wasn't covered by yesterday's priority scrape

2. ✅ Scheduler restart at 10:59 BST
   - The 24-hour staleness was diagnosed by CC after Mark noticed
     volume_score was uniformly 50.0 (P5 default) across all tickers
   - Empirical proof: today's signal_scores rows stamped 0.9.0
     (pre-refactor), confirming the scheduler was running
     pre-yesterday code
   - Restart picked up f84b552 (Volume), 0977594 (rel_volume), 
     01e1e53 (config), e83d8d6 (ticker_metadata) commits

3. ✅ Volume rendering on ticker page (verified post-restart)
   - Reload of NVDA/F/SPY ticker pages showed Volume populated
     correctly (was rendering "-" before restart)

4. ✅ EXCHANGE column on main + penny screeners (commit before
   chaining commit; HEAD~2 from current)
   - api_screener LEFT JOIN ticker_metadata
   - Position 2 (after TICKER) per Mark's choice
   - Sort wired (header click → ASC/DESC, sort arrow updates)
   - Filter deferred to separate session
   - Both web/templates/screener.html and 
     web/templates/penny_screener.html updated
   - Verified: AAPL→NASDAQ, F→NYSE, KO→NYSE, NVDA→NASDAQ, SPY→NYSE
     populating correctly in browser

5. ✅ Job chaining: scoring chained to scrape completion 
   (commit HEAD~1)
   - Removed +30-min cron registrations for job_generate_signals
   - Added direct call to job_generate_signals() at end of 
     job_scrape_screener's success path, inside the existing try
     block, after prune_old_snapshots, before "JOB DONE" log
   - Startup DateTrigger registration (5 sec post-boot, fires once)
     preserved as fresh-data scoring path on scheduler start
   - Two-line addition + nine-line deletion
   - Standalone test with mocked scrape verified the chain produces
     correct log sequence
   - Root cause this fixes: scrape takes ~52 minutes end-to-end
     (sectors scraped sequentially, DB write at end), so the +30 min
     cron was firing scoring against the previous batch's data, not
     the current batch

6. ✅ Scheduler startup banner logging (commit HEAD)
   - New _log_startup_banner() function in main.py
   - Logs SCORING_ENGINE_VERSION, git HEAD short hash, ISO 8601
     process start timestamp
   - Subprocess call to git rev-parse --short HEAD with try/except
     fallback to "unknown"
   - Called as first statement in scheduler command branch, before
     any job registration
   - Boot-only logging (no per-job lines) per the design rationale
     that a process running stale code was born stale and cannot
     become stale mid-run
   - Verified: scheduler restart at 13:25 BST produced banner
     showing 0.11.0 on 1ea7cf6 in logs/trading_system.log

PUSHED TO origin/main (in order):
- e83d8d6 — Introduce ticker_metadata table; migrate exchange off
  screener_snapshots
- (commit hash) — Add EXCHANGE column to main and penny screeners
- 1d753c5 — Chain job_generate_signals to scrape completion
- 1ea7cf6 — Add scheduler startup banner logging version and git HEAD

==========================================================
EMPIRICAL VERIFICATION (END OF SESSION)
==========================================================

Three architectural fixes shipped today, all empirically verified:

1. ticker_metadata: F (Ford) renders NYSE on ticker page, was "—"
   yesterday. Architectural fix delivered.

2. Causal chaining: scheduler restart's startup signal generation
   ran at 13:25:33, scored against the 12:00 BST scrape's data
   (rel_volume populated correctly post-rel_volume-fix), produced
   diverse volume_score values.

3. Scheduler banner: grep "Scheduler boot" logs/trading_system.log
   returns the banner with SCORING_ENGINE_VERSION=0.11.0, git
   HEAD=1ea7cf6.

Volume Confirmation (component 8) producing real production scores
for the first time:
- avg volume_score = 48.5 (not 50.0)
- min = 20.0 (full "confirmed down" rubric floor)
- max = 80.0 (full "confirmed up" rubric ceiling)
- null_vs = 0 across 10,773 scored tickers

This is the first time in the project's history that scheduled
production scoring has produced diverse Volume Confirmation values.
Yesterday's "diverse 23.8-78.6" was a manual run during the session,
not the scheduler's behaviour.

==========================================================
INFLIGHT (carried over to next session)
==========================================================

NONE. Today's session closed cleanly with all four commits pushed,
scheduler restarted, banner verified, volume scoring verified.

Next session can pick from the queue below in any order.

==========================================================
QUEUED SESSIONS (in priority order)
==========================================================

1. EXCHANGE filter UI on screener (small, 30-45 min)
   Sort already shipped; filter is a separate UI decision (dropdown,
   text input, multi-select). UX decisions before implementation.

2. Trailing-cron cleanup (small, 30-45 min)
   job_compute_target_prices (+33 min) and job_recom_priority 
   (+35 min) cron jobs duplicate work that job_generate_signals now
   does inline via the chained call. Both can be removed.

3. REVERSION 0.0 prevalence investigation (urgent, pre-launch)
   33% of v0.11.0 rows score 0.0 on Reversion (P5 violation or
   genuine domain output, needs diagnosis). Reversion has weight
   0.10, so the difference between 0.0 and P5-correct 50.0 is
   ~5 composite points across a third of the universe.

4. LEGAL NULL UX decision (small, pre-launch)
   With 99.7% of tickers having NULL legal data, the radar plots
   Legal at axis-100 ("clean") for nearly every ticker. False
   confidence. Pick one of: leave at 100, render at 50 (P5-strict),
   visual distinction (greyed/dashed). Decision before launch.

5. Yahoo Finance pipeline + components 9-16 (FRESH CHAT)
   Mark explicitly requested fresh chat for context cleanliness.
   4-6 hours for pipeline alone before any of components 9-16 are
   written.

6. Component rendering refactor (post-Yahoo, pre-launch)
   Convert hardcoded 8-component rendering on ticker page (radar,
   scorecard, top strip) to array-driven before adding components
   9-16. Natural batch boundary.

7. Scraper substrate audit (post-Yahoo, 90-min hard cap)
   Inventory only, no fixes. Eight scraper-layer issues surfaced in
   the last 48 hours. Document the debt before deciding fix order.

==========================================================
KEY ARCHITECTURAL FACTS LEARNED THIS SESSION
==========================================================

- screener_snapshots.exchange was 100% NULL across 903,037 historical
  rows. Backfill last night populated it. This morning's architectural
  fix moved exchange to a dedicated ticker_metadata table (write-once,
  read-forever pattern).

- Long-lived scheduler processes silently run stale in-memory code.
  Today's banner logging makes this visible going forward. The class
  of bug was previously invisible.

- The +30-minute scoring offset was structurally wrong (scrape takes
  ~52 minutes end-to-end). Causal chaining replaces time-based
  triggering, so scoring fires when scrape data is actually available.

- Volume Confirmation has been producing real scheduled production
  scores only since today's scheduler restart at 10:59 BST. Yesterday's
  "diverse values 23.8-78.6" was a one-off manual test run, not the
  scheduler's behaviour. PROJECT_CONTEXT updated to reflect.

- The 12:00 BST scrape's data shows rel_volume now populating from
  the Custom view fix (post-restart scheduler), confirming yesterday's
  rel_volume fix is in production for the first time today.

==========================================================
PROCESS LESSONS CAPTURED THIS SESSION
==========================================================

1. CC's verification gate predictions ("renders after server restart")
   are not the same as verifications ("here is the rendered page").
   This morning's Volume regression was caught by Mark's manual
   browser walk, not by CC's gate output. Going forward, gate output
   that says "will render after restart" is incomplete; the empirical
   walk is required before commit.

2. The runtime-code drift problem is real and hits invisibly. Today
   it surfaced twice in different forms (volume_score=50.0 from
   stale scoring engine, then volume_score=50.0 from stale scrape
   substrate). Both were the same root cause: long-lived scheduler
   running pre-commit code. Mitigation now shipped: startup banner.

3. CC's "single 404, error handling working" pattern (twice today)
   is a soft drift from showing empirical evidence (the actual log
   line) to summarising it. P16 hedge. Worth naming when it happens.

4. CC offered a carry-forward fix as the obvious solution to the
   exchange-NULL-on-every-snapshot problem. The carry-forward was
   the patch on a patch. The architectural fix (ticker_metadata) is
   the right answer. Devil's advocate framing surfaced this; pure
   "ship the fast fix" mode would have missed it.

5. The Phase 1/Phase 2 split pattern continues to be load-bearing.
   Five Phase 1 diagnostics today (exchange field corrections,
   ticker_metadata, screener column, volume_score=50.0, scheduler
   logging, job chaining), all surfaced material findings before
   Phase 2 implementation. The pattern is now proven across ten+
   sessions.

==========================================================
CURRENT WORKSPACE STATE
==========================================================

Tests: 181 passing
Branch: main, all today's code work pushed to origin
HEAD: 1ea7cf6 (Add scheduler startup banner logging)
SCORING_ENGINE_VERSION: 0.11.0 (in config/constants.py, in git)

Web server: running on port 5001 (RED terminal)
Scheduler: restarted at 13:25 BST (GREEN terminal), PID rotated, banner
  visible in logs/trading_system.log, scoring 11,184 tickers cleanly
  on the chained startup run
markn DB tier: ELITE
DB row counts: signal_scores has new v0.11.0 rows from this morning's
  restart producing diverse volume_score values for the first time

If new chat resumes:
- git status (clean expected)
- pytest --tb=no -q (181 expected)
- ps aux | grep main.py (scheduler should be running, started 13:25 BST)
- tail -7 logs/trading_system.log | head -7 (should show banner if 
  scheduler hasn't restarted; if scheduler has restarted, banner 
  will be at the top of the latest boot block)
- sqlite3 data/trading_system.db "SELECT MIN(volume_score), 
  MAX(volume_score), AVG(volume_score) FROM signal_scores WHERE 
  scored_at >= datetime('now', '-2 hours');" (should show diverse
  range, not 50.0 uniformly)

==========================================================
END HANDOFF
==========================================================