# SIGNALINTEL — HANDOFF

**Tactical session state.** Updated end of each session. For stable
project context (who/what/how), see `PROJECT_CONTEXT.md`.

Last updated: 12 May 2026, end of morning session.
Next session: Yahoo Finance pipeline + components 9-16. **FRESH CHAT** recommended.

---

## JUST SHIPPED — 12 May 2026

### BUG A — FMP consecutive-429 circuit breaker (full fix)

✅ **Circuit breaker** `c38e167` — `scrapers/fmp_scraper.py`: added `FMPRateLimitError`, module-level `_fmp_429_streak` + `_fmp_429_lock`, incremented on 429, reset on 2xx, raises at `FMP_CIRCUIT_BREAKER_THRESHOLD = 10`.

✅ **Propagation fix** `876c025` — `job_refresh_dividends` per-ticker loop: explicit `except FMPRateLimitError: raise` before generic handler so breaker trips propagate to caller.

✅ **Tests** `9b17c4d` — `tests/test_fmp_circuit_breaker.py`: 5 tests, all passing. Covers: below-threshold reset on 2xx, trip at threshold, propagation through job_refresh_dividends, cross-job reset, threshold=1 edge case.

✅ **Cron re-enabled** `ddd9da5` — `main.py`: `job_fmp_dividends` cron uncommented with updated comment referencing the circuit breaker.

### BUG B — Screener INSERT regression (already shipped 11 May)

✅ **Fix** `ec99570` — `database/db.py:244`: removed `exchange` from screener_snapshots INSERT (column dropped 9 May migration, INSERT missed). Both freshness tests now passing (confirmed 12 May 08:xx).

### P19 sweep — screener_snapshots CRUD audit

✅ **Dead script** `0848893` — `scripts/migrate_ticker_metadata.py` deleted. One-time migration that SELECTed `exchange` column; would fail if re-run.

### Cleanup — scheduler.log orphan + DB backup

✅ **Deleted** `94c1d91` — `logs/scheduler.log` (2.6MB, last written 6 May, code reference already gone) and `data/trading_system.db.backup_20260509_122258` (322MB, 9 May pre-migration backup). FOLLOWUP entries scrubbed from PROJECT_CONTEXT.md.

---

## CURRENT STATE (end of 12 May 2026 morning session)

- Scheduler running: PID 73415, PPID=1, daemonized, `logs/trading_system.log`
- HEAD: `94c1d91` — all commits pushed to `origin/main`
- pytest: 186 passing (both freshness tests green as of 12 May 08:xx screener run)
- `job_fmp_dividends` cron re-enabled — will next fire Sunday 03:00
- No known open bugs

---

## NEXT SESSION — Yahoo Finance pipeline + components 9-16

**FRESH CHAT** — large scope, deserves its own context.

### Open questions to lock at session start

1. **Yahoo Finance authentication** — API key needed? Rate limits? Reuse FMP circuit breaker pattern?
2. **Storage** — extend `screener_snapshots`, or new `yahoo_snapshots` table?
3. **Scheduling** — when does Yahoo scrape relative to FinViz? Does `job_generate_signals` wait for both?
4. **Component weighting** — when 9-16 land, do existing weights adjust or do new components add additively?

### Components 9-16

- Which 8 components are landing
- Which Yahoo data each needs
- `SCORING_ENGINE_VERSION` bump: 0.12.0 → 0.13.0 minimum (P18: component additions warrant MINOR)
- Rendering: registry additions only — no template surgery (COMPONENTS array in ticker.html already proven via DT-2/3)

### Watchlist data-loss bug — opportunistic

If Mark hits the bug between sessions (code change → restart → watchlists gone), capture the exact restart workflow before recreating the watchlists.

---

## OPEN FOLLOWUPS (PROJECT_CONTEXT.md)

- Expand freshness test pattern to `insider_trades`, `legal_risk` tables
- Daily Telegram alert as passive monitoring for scraper failures
- Scraper substrate audit (post-Yahoo): 8 issues surfaced 8-9 May, queued
- Virtual portfolio system (Phase 1)
- Email alerts via SendGrid (Phase 1)

---

*End handoff.*
