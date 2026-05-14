# SIGNALINTEL: HANDOFF

**Tactical session state.** Updated end of each session. For stable
project context (who/what/how), see `PROJECT_CONTEXT.md`.

Last updated: 14 May 2026, end of session (Phase 2a shipped).
Next session: Phase 2b: scoring substrate refactor + components 10-14 + Altman penalty path. FRESH CHAT recommended (large infrastructure session).

---

## JUST SHIPPED -- 14 May 2026 (Phase 2a: Yahoo scraper substrate)

### Database (commit 20c0148)

- 5 new tables added to `database/db.py:initialise_schema`: `earnings_history`, `financial_statements` (one row per line item per statement per fiscal year), `institutional_holders`, `analyst_changes`, `external_scrape_log` (PK ticker+data_type, no autoincrement)
- All Yahoo data tables have UNIQUE constraints with source column for future multi-sourcing
- 5 insert helpers + `get_active_tickers(db_path, days=7)` + `upsert_external_scrape_log()` added to `database/db.py`
- All insert helpers use `INSERT OR IGNORE` for idempotency; `upsert_external_scrape_log` uses `ON CONFLICT DO UPDATE` to always overwrite

### Scraper module (commit 1f848da)

- New file `scrapers/yahoo_scraper.py`, 286 lines
- yfinance 1.2.0 wrapper with consecutive-rate-limit circuit breaker (`YahooRateLimitedError`, `YAHOO_CIRCUIT_BREAKER_THRESHOLD = 10`, `threading.Lock`)
- Detection of rate-limit failures via string-match on exception messages ("rate limit", "too many requests", "429", "try again"). Empty DataFrame is NOT a rate-limit signal (legitimate "no data" tickers exist).
- 4 fetcher functions (one per Yahoo data type) + 2 priority-set helpers (`get_priority_tickers`, `get_upcoming_earnings_tickers`)

### Scheduler (commit 962b68b)

- 5 new job functions in `main.py`, all following the existing JOB START / JOB DONE envelope with `log_run` integration
- Resume-from-checkpoint logic on the 3 bulk jobs: skip tickers where `external_scrape_log.last_success_at >= datetime('now', '-6 days')`
- All 5 jobs registered via `scheduler.add_job` between `market_history` and the job listing log line
- Daily priority (Mon-Fri): `yahoo_analyst_02:00`, `yahoo_earnings_02:15`
- Weekly bulk (locked design, spread across Sun-Tue, NOT Sunday-only): `yahoo_institutional_sun_04:00`, `yahoo_financials_mon_04:00`, `yahoo_earnings_tue_04:00`
- All bulk jobs at 04:00 BST on their respective days

### Config (commit 7073db4)

- `YAHOO_PRIORITY_TIMES = ["02:00", "02:15"]` and `YAHOO_BULK_DAYS = ["sun", "mon", "tue"]` (documentation-only constants)
- `YAHOO_REQUEST_DELAY_SECONDS = 1.0` (per-ticker delay in Yahoo loops; tighter than `REQUEST_DELAY_SECONDS = 2.5` for FinViz because yfinance's free-tier ~1.5 req/sec ceiling is HTTP-level, not server-side throttled)
- `YAHOO_CIRCUIT_BREAKER_THRESHOLD` stays module-level in `scrapers/yahoo_scraper.py`, matching FMP pattern (not a shared config constant)

### Tests (commits 7579239, 520b623, 02b32c6)

- New file `tests/test_yahoo_circuit_breaker.py`: 5 tests mirroring `test_fmp_circuit_breaker.py` structure (mock `yf.Ticker`, stub `time.sleep`, autouse fixture resets `_yahoo_429_streak`)
- New file `tests/test_yahoo_scraper.py`: 3 tests (active-tickers window respected, insert idempotency, scrape-log upsert overwrites)
- `tests/test_data_integrity.py` extended with 4 new Yahoo freshness tests at 14-day threshold; each skips if its table is empty (handles gradual fill period)
- Total test count: 206 passing (191 prior + 5 circuit breaker + 3 scraper + 4 freshness + 3 already-existing freshness that had not been counted in prior tallies)

### Benchmark script (commit 7f091d8)

- New file `scripts/benchmark_yahoo.py`
- IMPORTANT: original benchmark wrote 9,117 rows to live DB across 5 tickers (scope drift from prompt spec of 10 tickers, read-only). Rows were subsequently DELETEd from production tables and the script patched to be read-only (timings only, no DB writes). Phase 2a-cleanup commit landed the patch.
- Empirical timing observed during benchmark: ~3.7s per ticker covering all 4 Yahoo data types. Sustained throughput slightly under the assumed 1.5 req/sec ceiling but in the same order of magnitude.

### Scheduler restart (manual, end-of-session)

- Old PID 89425 stopped, new scheduler started 14 May 2026 07:29:53 BST
- All 21 jobs registered cleanly (16 prior + 5 new Yahoo)
- Startup signal generation fired at 07:29:58, scored 10,793 tickers
- No errors or import failures on boot
- New code is running in production; first daily priority Yahoo jobs fire tomorrow 15 May at 02:00 + 02:15 BST

---

## CURRENT STATE (end of 14 May 2026)

- Scheduler running on new code (Phase 2a live)
- HEAD on local main, all 8 Phase 2a commits + benchmark cleanup commit landed; not yet pushed to origin (push when Mark is ready)
- pytest: 206 passing; 4 Yahoo freshness tests SKIPPED (tables empty, expected behaviour until first scheduled scrape populates them tomorrow)
- 5 Yahoo data tables exist, all empty
- `external_scrape_log` exists, empty
- SCORING_ENGINE_VERSION unchanged at 0.12.0 (Phase 2a was substrate only; version bump lands in Phase 2b)
- Database backup `data/trading_system.db.backup_pre_vacuum_20260513_064920` still pending deletion (criterion: 24h of clean post-VACUUM scrape cycles, met as of 14 May ~07:00 BST; small single-file deletion commit pending)

---

## PROCESS TELLS -- 14 May 2026 (Phase 2a session)

- **Decision-lock pattern worked.** Two Phase 1 inventories (substrate-level + flag-rendering recon), seven sequential decision locks (#1 partitioning through #7 deferred), then split Phase 2 into the program-not-prompt shape. Lock #3 pivoted from "piggyback flags column" to "build proper flag substrate" when the recon showed `signal_scores.flags` was substring-matched on one page and ignored on the rest. P20 invariant emerged organically from this pivot.

- **CC's Phase 2a verification gate report was light on evidence.** The prompt required paste-quoted output per gate (sqlite `.schema`, full `cat`, pytest `-v` verbatim, `ps -ef`, `git diff --stat`, FMP grep). CC reported a summary table with checkmarks. Athena raised this as a possible P-level STOP violation on the doc files; a follow-up empirical diagnostic prompt corrected that diagnosis. Doc files were actually prior-session uncommitted work, not anything CC touched today. Two distinct lessons: (1) CC's gate-walking discipline slipped -- summary table without paste-quoted evidence is exactly the P16 hedge-word pattern, future verification gates should phrase paste requirements with explicit "paste verbatim, not a summary" language; (2) Athena's diagnosis was wrong -- saw `M PROJECT_CONTEXT.md` and `M HANDOFF.md` in `git status`, framed as "P-level STOP violation" without checking when the modifications dated from, the right diagnostic move was `git diff` first, alarm second.

- **The diagnostic prompt did the right work.** Five-part empirical sweep (doc diffs, scheduler PID, FMP grep, benchmark scope, commit hygiene) caught all four divergences from the original prompt: doc files were prior-session work, scheduler was alive (pgrep false negative; ps -ef showed it), FMP `streak` was a local copy in the lock (no bug), benchmark wrote to production. Verification gates work; this was the gate doing its job, including on Athena.

- **Three real divergences from the Phase 2a-Phase2 prompt:** (1) Benchmark used 5 tickers, not 10, and wrote to live DB rather than running read-only -- cleaned up post-hoc. (2) CC's gate walk was a summary rather than paste-quoted evidence per gate -- resolved via follow-up diagnostic. (3) CC's final `git status` output did not flag the prior-session uncommitted changes to HANDOFF.md and PROJECT_CONTEXT.md -- not a CC failure per se, but the failure mode where unstaged-from-prior-session changes are invisible in the next session's hand-off.

- **Scheduler restart workflow proven on this phase.** Old PID stopped, banner confirmed new code loaded, all jobs registered, startup signal generation ran clean. Pattern that worked: kill PID, sleep 5, nohup python main.py scheduler, disown, tail logs. Worth codifying for Phase 2b end-of-session.

---

## STILL OPEN

- **Phase 2b (next session, fresh chat):** scoring substrate refactor (`screener_rows -> ticker_data_rows`, pre-enrichment pattern collapsing `legal_risk_map` and `sector_strength_map`), 5 new scorer functions (Earnings Surprise, Piotroski F-Score, Altman additive penalty, Institutional Ownership, Analyst Momentum), composite weight rebalance (1.10 -> 1.60 sum, normalised), SCORING_ENGINE_VERSION bump 0.12.0 -> 0.13.0.
- **Phase 2b prerequisite:** design canonical `line_item_key` vocabulary for `financial_statements` mapping layer. Yahoo field names vary across statements and yfinance versions. Phase 2b Phase 1 inventory should propose the canonical vocabulary; Phase 2b Phase 2 implements it.
- **Phase 2b prerequisite:** lock Altman penalty tiers (e.g. Z >= 3.0 = 0, 1.8 <= Z < 3.0 = -5, Z < 1.8 = -20, Z < 0 = -40). Numbers are draft.
- **Phase 2d, 2e, 2f** queued per program plan (flag substrate, rendering, end-to-end verification).
- **Backup file deletion:** `data/trading_system.db.backup_pre_vacuum_20260513_064920` (363MB) eligible for deletion as of 14 May ~07:00 BST. Three clean post-VACUUM scrape cycles observed (13 May 07:00, 11:00, 16:30), pytest green. Small single-file deletion commit pending.
- **Push to remote:** 9 Phase 2a commits (8 implementation + 1 benchmark cleanup) sit on local main, not yet pushed. Push when Mark is ready.
- **End-of-session doc update:** P20 invariant needs to land in `docs/scoring_invariants.md` AND in PROJECT_CONTEXT.md's PROCESS INVARIANTS table. Additional process lessons from today (Athena's misdiagnosis, CC's gate-walking slip, the prior-session uncommitted files pattern) should be folded into PROJECT_CONTEXT.md alongside P20.

---

## NOTES FOR FRESH-CHAT ATHENA (Phase 2b)

If starting Phase 2b in a fresh chat:

- Read PROJECT_CONTEXT.md first (stable), then this HANDOFF for current state
- Phase 2b is a LARGE session: scoring substrate refactor + 5 new scorers + version bump + tests. Plan accordingly.
- The pre-enrichment refactor touches existing scoring code paths (`legal_risk_map`, `sector_strength_map`). Phase 1 inventory must enumerate every call site of `score_all_tickers` to ensure clean signature migration.
- All 5 Yahoo data tables exist and may or may not be populated by the time Phase 2b runs (depends on how many days pass between today and the next session). Phase 2b scorers must handle empty-table cases gracefully via P5 NULL handling.
- The flag system (Phase 2d) is NOT touched in 2b. Short Squeeze waits.

---

*End handoff.*
