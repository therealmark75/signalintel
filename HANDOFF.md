# SIGNALINTEL: HANDOFF

**Tactical session state.** Updated end of each session. For stable
project context (who/what/how), see `PROJECT_CONTEXT.md`.

Last updated: 12 May 2026, end of session.
Next session: Yahoo Finance pipeline + components 9-16. **FRESH CHAT** recommended.

---

## JUST SHIPPED: 12 May 2026

### BUG A: FMP consecutive-429 circuit breaker (full fix)

✅ **Circuit breaker** `c38e167`: `scrapers/fmp_scraper.py` added `FMPRateLimitError`, module-level `_fmp_429_streak` + `_fmp_429_lock`, increments on 429, resets on 2xx, raises at `FMP_CIRCUIT_BREAKER_THRESHOLD = 10`. Threading.Lock protects the counter (scheduler uses `ThreadPoolExecutor(3)`, surfaced during Phase 1 inventory).

✅ **Propagation fix** `876c025`: `job_refresh_dividends` per-ticker loop got explicit `except FMPRateLimitError: raise` before the generic handler, so breaker trips propagate to caller cleanly.

✅ **Tests** `9b17c4d`: `tests/test_fmp_circuit_breaker.py`, 5 tests, all passing. Covers below-threshold reset on 2xx, trip at threshold, propagation through job_refresh_dividends, cross-job reset, threshold=1 edge case. All stub `requests.get` and `time.sleep`; no real HTTP, no real delays.

✅ **Cron re-enabled** `ddd9da5`: `main.py` `job_fmp_dividends` cron uncommented with updated comment referencing the breaker.

### BUG B verification: Screener INSERT regression confirmed live

The 11 May fix `ec99570` (removed `exchange` from `database/db.py:244` INSERT) was empirically confirmed live on 12 May. The 08:xx screener run produced fresh `screener_snapshots` rows and `test_screener_snapshots_freshness` passed for the first time since 8 May. BUG B is now fully closed: fix in place, fix observed working.

### P19 sweep: screener_snapshots CRUD audit

✅ **Dead script** `0848893`: `scripts/migrate_ticker_metadata.py` deleted. One-time bootstrap that SELECTed the dropped `exchange` column; would fail with "no such column" if re-run. Identified during the post-hoc P19 sweep that grep'd every CRUD path against screener_snapshots. Sweep otherwise clean: 90 references classified, no remaining live exchange dependencies.

### Cleanup: scheduler.log orphan + 9 May DB backup

✅ **Deleted** `94c1d91`: `logs/scheduler.log` (2.6MB, last written 6 May) and `data/trading_system.db.backup_20260509_122258` (322MB, 9 May pre-migration safety backup). Two FOLLOWUP entries scrubbed from PROJECT_CONTEXT.md.

---

## CURRENT STATE (end of 12 May 2026)

- Scheduler running: PID 73415, PPID=1, properly daemonised, writing to `logs/trading_system.log`
- HEAD: latest pushed; local main in sync with `origin/main`
- pytest: 191 passing (186 prior + 5 new FMP circuit breaker tests). Both freshness tests green as of the 12 May 08:xx screener run.
- `job_fmp_dividends` cron re-enabled; next fires Sunday 03:00
- SCORING_ENGINE_VERSION: 0.12.0 (no bump this session; all changes operational hardening or cleanup, not scoring substrate)
- No active blockers; opportunistic and structural items remain in PROJECT_CONTEXT FOLLOWUPS

---

## PROCESS TELLS: 12 May 2026

- **The scheduler.log "orphan" was less than we thought.** The FOLLOWUP entry assumed a stale FileHandler in the codebase. Empirically the grep returned zero Python references; the handler had been removed at some earlier point and only the dead log file remained on disk. P16 applies to FOLLOWUPS, not just to CC output: unverified diagnoses carry forward in our own docs as easily as in CC's. Captured as the "Unverified FOLLOWUPS carry forward" lesson in PROJECT_CONTEXT.

- **STOP gate bypassed.** The cleanup prompt's Part 1 verification gate said "If the grep returns zero hits, STOP and report." CC found zero hits but proceeded with the obvious-correct action (deleting the dead log file) anyway. Outcome fine, discipline slipped. Gate STOP conditions should be honoured even when CC has a sensible interpretation of an alternative action; the STOP exists because the underlying diagnosis was wrong, and proceeding short-circuits the learning loop. Captured as the "STOP-gate-bypass" lesson in PROJECT_CONTEXT.

- **CC self-initiated both doc commits.** The cleanup prompt didn't authorise edits to PROJECT_CONTEXT.md or HANDOFF.md but CC committed both unprompted. The "Do not push to remote unless explicitly told to" instruction held (Mark pushed manually), but editing-side scope drift is the "negative-instruction drift" pattern documented in PROJECT_CONTEXT itself. Future cleanup or work-completion prompts should include explicit "do not modify PROJECT_CONTEXT.md or HANDOFF.md unless asked" language alongside the push gate. Captured as the "CC self-initiating doc edits" lesson in PROJECT_CONTEXT.

---

## NEXT SESSION: Yahoo Finance pipeline + components 9-16

**FRESH CHAT recommended.** Large scope, deserves its own context.

### Open questions to lock at session start

1. **Yahoo Finance authentication**: API key needed? Rate limits? Reuse the FMP circuit breaker pattern (now in production) as the rate-limit-aware retry primitive, or build Yahoo-specific?
2. **Storage**: extend `screener_snapshots`, or new `yahoo_snapshots` table?
3. **Scheduling**: when does Yahoo scrape relative to FinViz? Does `job_generate_signals` wait for both?
4. **Component weighting**: when 9-16 land, do existing weights adjust or do new components add additively?

### Components 9-16

- Which 8 components are landing
- Which Yahoo data each needs
- `SCORING_ENGINE_VERSION` bump: 0.12.0 → 0.13.0 minimum (P18: component additions warrant MINOR)
- Rendering: registry additions only, no template surgery (COMPONENTS array in ticker.html already proven via DT-2/3 extension tests)

### Watchlist data-loss bug: opportunistic

If Mark hits the bug between sessions (code change → restart → watchlists gone), capture the exact restart workflow before recreating the watchlists. That's the empirical data needed to audit the right startup path.

---

## OPEN FOLLOWUPS

See `PROJECT_CONTEXT.md` FOLLOWUPS. Nothing actioned this session beyond:
- BUG A proper fix (FMP circuit breaker)
- P19 sweep on screener_snapshots (dead migration script deletion)
- Cleanup (scheduler.log + 9 May DB backup)

---

*End handoff.*
