# SIGNALINTEL — HANDOFF

**Tactical session state.** Updated end of each session. For stable
project context (who/what/how), see `PROJECT_CONTEXT.md`.

Last updated: 11 May 2026, end of evening session.
Next session: 12 May 2026 — BUG A proper fix, then Yahoo Finance pipeline. **FRESH CHAT** for Yahoo.

---

## JUST SHIPPED — 11 May 2026

### Component registry refactor (6 commits, ticker.html only)

✅ **Commit A** `502f240` — Add COMPONENTS registry + helpers (genericStrip, genericChip, radarLegendRow) + radarLabels derivation. Removed first valueScore at line 450.

✅ **Commit B** `dea9a1c` — Replace scoreBars construction with COMPONENTS strip loop, filtered by `inStrip`.

✅ **Commit C** `c9ab101` — Replace scorecard chips with COMPONENTS chip loop, filtered by `chipRenderer !== ''` (handles Sector's conditional null return).

✅ **Commit D** `d0aa7a6` — Replace radar legend HTML with COMPONENTS legend loop filtered by `radarIndex !== null` and sorted by index.

✅ **Commit E** `2c72400` — Refactor initRadarChart to consume COMPONENTS and radarLabels as explicit params. Removed second valueScore at line 937.

✅ **Commit F** `c9f8851` — Fix `✓` glyph regression on Legal chip NONE state. Caught via browser walk on ATYR; pre-refactor inventory (Phase 1 Q4) had specified `'Clean ✓'` but Phase 2 implementation dropped the checkmark.

### Verification (all empirical, no hedge-words)

- **FLD walks 1-7**: strip count 6, chips 8 (Sector present on FLD), chip labels ordered correctly, radar legend 7 rows, dot colors all 7 hex values present in order, Chart.js labels match registry order. Pass.
- **ATYR walks 9-12** (Volume IS NULL): chip[4]='—', strip[4]='—', rd-volume color rgb(156, 163, 175) = `#9CA3AF`, datasets.length=2 (null-overlay dataset present). Pass.
- **9-16 extension test DT-1/2/3**: 
  - DT-1 `{strip:7, chips:9, legend:7, axes:7}` — dummy in strip+chips, absent from radar
  - DT-2 `{strip:7, chips:9, legend:8, axes:8}` — radarIndex:7 promoted dummy to radar via registry-derived radarLabels
  - DT-3 `{strip:6, chips:8, legend:7, axes:7}` — clean revert, no residual

### Audit closure

Tooltip verbatim assertion: 8/8 strings match pre-refactor `data-tip`. dotColor grep: all 7 locked hex values present exactly once. `git diff origin/main..HEAD --stat`: only `web/templates/ticker.html` modified across all 6 commits. pytest: 184/186 (2 freshness failures pre-existing per Option B baseline check — see BUG B below).

### Operational fixes (2 commits)

✅ **BUG B fix** `ec99570` — `database/db.py:244` removed `exchange` from screener_snapshots INSERT column list. The 9 May column drop migration (0b4d9a4) had dropped the column from the table but missed this CRUD path. Every screener scrape since 9 May failed silently. Caught by pytest freshness tests during Phase 2 audit. P19 codified into the invariants doc as a result.

✅ **BUG A workaround** `bde4aa4` — Disabled `job_refresh_dividends` cron in main.py. The dividend job had been stuck in a 44-hour FMP rate-limit retry loop, blocking job_generate_signals from firing. Disabled with a TODO referencing the proper fix (consecutive-429 circuit breaker in `scrapers/fmp_scraper.py _get()`).

### Push status

All 8 commits pushed to `origin/main` at end of session.

---

## CURRENT STATE (end of 11 May 2026)

- Scheduler restarted ~21:34 BST on fresh code with banner confirming SCORING_ENGINE_VERSION 0.12.0 + post-fix HEAD
- Signal scoring confirmed flowing immediately after restart (job_generate_signals fired clean)
- Screener scrape waiting on next SCREENER_SCRAPE_TIMES window — passive
- pytest: 184 passing + 2 freshness failures expected to clear after the next screener scrape lands
- Web server on `bde4aa4` (HEAD) with Phase 2 refactor live; ticker.html surfaces all driven by COMPONENTS registry

---

## DISCOVERIES THIS SESSION

Three new entries queued in FOLLOWUPS (see PROJECT_CONTEXT.md):

- **BUG A proper fix** — consecutive-429 circuit breaker in fmp_scraper. Pre-Yahoo priority.
- **Watchlist data-loss bug** — code-change-triggered reset (not plain restart). SQL diagnostic ruled out hypothesis 1 (session/user_id instability) and 3 (in-memory only). Likely startup-path init function with conditional DDL. Diagnostic queued — capture exact restart workflow on next occurrence.
- **scheduler.log orphan** — stale FileHandler in the codebase writing to a log file last touched 6 May. Low-risk grep-and-remove.

Two process invariant additions:

- **P19 codified** — schema migration inventory must enumerate every CRUD path, not just init code. Direct lesson from BUG B (9 May column drop missed `database/db.py:244` INSERT).

- **Verification gate hardened** — the Legal `✓` regression demonstrated that CC's "code review" audit entries are weaker evidence than empirical browser walks for any change touching rendering. P16 absolutism wins; updated in PROJECT_CONTEXT lessons section.

---

## NEXT SESSION — 12 May 2026

### Primary: BUG A proper fix (pre-Yahoo, ~30-60 min focused session)

Add consecutive-429 circuit breaker to `scrapers/fmp_scraper.py _get()`. Design notes:

- Module-level counter, resets on any 2xx
- Threshold: ~5 consecutive 429s (lockable in Phase 2 prompt)
- On trip: raise a custom exception (e.g. `FMPCircuitBreakerTripped`)
- Job callers (job_refresh_dividends) catch the exception and exit cleanly with a log line
- Re-enable `job_refresh_dividends` cron in main.py once breaker lands (one-line revert of the workaround commit)

Standard Phase 1 + Phase 2 pattern. Phase 1 inventories the current `_get()` retry path and proposes the breaker shape; Phase 2 implements with locked threshold and exception class.

### Then: Yahoo Finance pipeline + components 9-16 (FRESH CHAT)

This is the next major infrastructure session. Per PROJECT_CONTEXT this should be a **FRESH CHAT** — large in scope, deserves its own context. The component registry refactor is now in place, so 9-16 will land as registry additions, not template surgery.

### Scope to lock with Mark at session start

1. **Pipeline architecture**
   - Yahoo Finance data sources to integrate (yfinance lib? Paid API tier?)
   - How does Yahoo data flow — extend screener_snapshots or new yahoo_snapshots table
   - Schedule (cron timing relative to existing FinViz scrape)
   - Failure modes and fallback (and reuse of the BUG A circuit breaker pattern)

2. **Components 9-16 specification**
   - Which 8 components are landing
   - Which Yahoo data each component needs
   - Weights in compute_composite (additive vs weighted-average)
   - SCORING_ENGINE_VERSION bump: 0.12.0 → 0.13.0 minimum (component additions warrant MINOR per P18)

3. **Component rendering refactor** — **DONE 11 May 2026**. Components 9-16 are registry additions in the COMPONENTS array in ticker.html. No template surgery required. This is the win that makes Yahoo session land cleaner.

### Open questions to resolve at session start

- Yahoo Finance authentication: API key needed? Rate limits? Reuse the (about-to-be-built) FMP circuit breaker pattern as the rate-limit primitive?
- Component weighting: when 9-16 land, do existing weights adjust or do new components add additively?
- Storage: new Yahoo tables, or extend screener_snapshots, or separate yahoo_snapshots table?
- Scheduling: when does Yahoo scrape relative to FinViz? Does job_generate_signals wait for both before scoring?

These don't need answers tonight. Lock them at the start of next session.

### Watchlist data-loss bug — opportunistic

If Mark hits the bug between sessions (code change → restart → watchlists gone), capture the exact restart workflow before recreating the watchlists. That's the empirical data we need to audit the right startup path. Otherwise, it stays queued.

---

## SIDE OBSERVATIONS

- **Process win 1**: Verification gate caught the Legal `✓` regression mid-session. CC's audit table claimed verification via "code review of getValue implementations" — the browser walk on ATYR exposed the actual rendered output. P16 absolutism in action. Documented in PROJECT_CONTEXT lessons.

- **Process win 2**: pytest data-freshness tests caught BUG B's 48-hour silent regression. Without those two tests, the screener INSERT failure would have continued indefinitely until manual data inspection. Strong argument for expanding the freshness test pattern (insider_trades, legal_risk) and adding a daily Telegram alert as passive monitoring.

- **Process win 3**: The 9-16 extension test (DT-2 specifically, axes 7→8) was the highest-risk piece of the refactor — registry-driven Chart.js label derivation. Empirical pass with zero code change outside the COMPONENTS entry confirms the abstraction is sound. Components 9-16 will land as data additions.

- **Process gap**: 9 May column drop Phase 1 inventory missed `database/db.py:244`. CC found the ADD COLUMN guard in web/app.py (defensive prerequisite) but didn't enumerate the INSERT path. Phase 1 prompts for schema work going forward must explicitly request CRUD path enumeration per P19.

- **Operational**: The dividend job has been stuck since 10 May 03:00. ~44 hours of wasted FMP API calls hitting rate limits. The proper fix is small (circuit breaker) and the workaround is a one-line cron disable. Once the breaker is in, we can re-enable the dividend job and start backfilling missed dividend data — minor concern since dividends aren't currently in any composite component.

- **Cosmetic**: scheduler.log orphan is the kind of thing that's invisible until you look. Quick grep+remove next time someone touches main.py.

---

## OPENING MOVE FOR 12 MAY 2026

Fresh chat (or continued from this one if Mark prefers). Athena reads PROJECT_CONTEXT.md and this HANDOFF, then:

1. Acknowledges both have been read
2. Confirms understanding: BUG A circuit breaker first, then Yahoo session
3. Surfaces the four open questions for Yahoo to lock at session start
4. Asks Mark to confirm order (BUG A first / Yahoo first / watchlist bug interleaved)
5. If BUG A first: recommends Phase 1 diagnostic (inventory current `_get()` retry path) → lock threshold + exception class → Phase 2 implementation
6. If Yahoo first: recommends Phase 1A (Yahoo data inventory) → Phase 1B (components 9-16 design) → Phase 2 staged implementation

Match the established working rhythm. Direct, no preamble, no pacing.

---

*End handoff.*