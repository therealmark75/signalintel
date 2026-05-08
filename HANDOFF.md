SIGNALINTEL — SESSION HANDOFF
End of Fri 8 May 2026, ~23:15 BST → Pickup next session

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
SESSION SUMMARY (THIS CHAT)
==========================================================

Two tracks completed this session:

TRACK 1 — Reversion scorer + UX (from previous session, committed
earlier today):
- score_mean_reversion: P5 NULL inputs now score neutral (50.0)
  per-component rather than 0.0 penalty. All-NULL tickers score 50.0.
- SCORING_ENGINE_VERSION bumped 0.11.0 → 0.12.0
- Radar: Legal axis dropped (8 → 7 axes). Reversion null overlay
  retained at index 3 (grey dashed indicator when reversion_score
  is null).
- Commits: e20f41c (scorer fix), 189e641 (version bump),
  4064c8e (drop Legal from radar), ba02258 + 46a18bb (Legal UX
  attempt + revert)

TRACK 2 — Legal rendering cleanup (this chat, four commits):

1. ✅ 4064c8e — Drop Legal axis from radar (already listed above)

2. ✅ e6535fd — Scorecard Legal row redesigned
   - .score-item Legal row now uses scraped_at as State 1/2
     discriminator
   - State 1 (no DB row, no scraped_at): "Not analysed" in grey
   - State 2 (scraped, NONE level): "Clean" in green
   - State 3 (scraped, non-NONE): risk_label in risk_color

3. ✅ 988b4b3 — Signal strip Legal bar fixed (combined C+D)
   - lrIsNone changed from `!lr.risk_level || risk_level==='NONE'
     || risk_label==='None'` to `lr.scraped_at && risk_level==='NONE'`
   - lrDisplayLabel + lrDisplayColor variables added
   - State 1: "Not analysed" in grey, no ✓, no penalty sub-row
   - State 2: "Clean ✓" in green, no penalty sub-row
   - State 3: risk_label in risk_color, penalty sub-row shown
   - Penalty sub-row gated on `lr.scraped_at && !lrIsNone`
     (was `!lrIsNone` alone — would have shown for State 1)

4. No fifth commit — header ribbon Legal (line 511, .signal-scores
   div) was already fixed by e6535fd (Part B). The "header ribbon"
   and "scorecard" are the same rendering surface.

DESIGN DECISION CAPTURED:
- Header ribbon shows "Clean" (no ✓); signal strip shows "Clean ✓"
- Asymmetry is intentional: header ribbon is compact summary,
  signal strip is detail surface. Mirrors State 3 pattern where
  header shows "Criminal / DOJ" alone; signal strip adds penalty
  sub-row. Position B confirmed by Mark.

EMPIRICAL VERIFICATION (browser walks by Mark):
- Radar: 7 axes, no Legal label on AAPL, MKSI, RGS, DAL, EME ✓
- Scorecard Legal: AAPL "Clean" green, MKSI "Criminal / DOJ" dark
  red, RGS "Not analysed" grey ✓
- Signal strip: AAPL "Clean ✓" green, DAL "Criminal / DOJ" dark red
  (DAL scraped today at 22:40 BST, CRIMINAL), AA "Not analysed" grey ✓
- Header ribbon (line 511): same fix as scorecard, confirmed correct ✓

NOTE ON LEGAL SCRAPER ACTIVITY:
The EDGAR scraper has been running live during this session.
Several tickers that were State 1 earlier today (KSPI, SCZM, DAL)
now have legal_risk rows. AA confirmed State 1 as of session close.
The State 1 population is shrinking as the scraper covers more
tickers.

==========================================================
INFLIGHT
==========================================================

NONE. Legal rendering session closed cleanly. Four commits (three
meaningful + one revert) pushed to origin/main. 181 tests passing.

==========================================================
QUEUED SESSIONS (in priority order)
==========================================================

1. REVERSION 0.0 prevalence investigation (urgent, pre-launch)
   v0.11.0 data showed 33% of rows scoring 0.0 on Reversion.
   v0.12.0 fix deployed but no v0.12.0 scoring rows yet (scheduler
   hasn't completed a full run with the new version). First v0.12.0
   scoring run will confirm the fix is producing diverse values.
   Verify: SELECT MIN(reversion_score), MAX(reversion_score),
   AVG(reversion_score), COUNT(*) FROM signal_scores WHERE
   scoring_version='0.12.0';

2. EXCHANGE filter UI on screener (small, 30-45 min)
   Sort already shipped; filter is a separate UI decision (dropdown,
   text input, multi-select). UX decision before implementation.

3. Trailing-cron cleanup (small, 30-45 min)
   job_compute_target_prices (+33 min) and job_recom_priority
   (+35 min) cron jobs duplicate work that job_generate_signals
   now does inline via chained call. Both can be removed.

4. Yahoo Finance pipeline + components 9-16 (FRESH CHAT)
   Mark explicitly requested fresh chat for context cleanliness.
   4-6 hours for pipeline alone before any of components 9-16 are
   written.

5. Component rendering refactor (post-Yahoo, pre-launch)
   Convert hardcoded 8-component rendering on ticker page (radar,
   scorecard, top strip) to array-driven before adding components
   9-16. Natural batch boundary.

6. Scraper substrate audit (post-Yahoo, 90-min hard cap)
   Inventory only, no fixes. Eight scraper-layer issues surfaced
   in the last 48 hours. Document the debt before deciding fix order.

==========================================================
KEY ARCHITECTURAL FACTS LEARNED THIS SESSION
==========================================================

- The "header ribbon" (COMPOSITE SCORE + component strip) and the
  "scorecard" (.signal-scores div) are the same rendering surface.
  Line 511 in ticker.html is the Legal element for both. There is
  no separate header ribbon code path.

- legal_risk.scraped_at is the correct State 1/2 discriminator.
  The API always returns a non-null object; the fallback dict for
  no-row tickers has no scraped_at field. Risk_level alone cannot
  discriminate (both State 1 and State 2 resolve to NONE). The
  string "None" stored in risk_label is the scraper's output for
  verified-clean tickers, not Python None.

- The EDGAR scraper is actively running. State 1 population is
  shrinking. Tickers assumed State 1 at query time may be State 2
  or 3 by browser walk time. Always re-verify with a live DB query.

- ✓ suffix on "Clean" is signal-strip-only by design. Header ribbon
  is compact summary; signal strip is detail surface. This asymmetry
  is intentional and confirmed.

==========================================================
CURRENT WORKSPACE STATE
==========================================================

Tests: 181 passing
Branch: main, all commits pushed to origin
HEAD: 988b4b3 (Fix signal strip Legal rendering)
SCORING_ENGINE_VERSION: 0.12.0

Web server: running on port 5001 (RED terminal)
Scheduler: running (started ~13:25 BST), GREEN terminal
markn DB tier: ELITE

v0.12.0 signal_scores rows: 0 (scheduler has not yet completed
  a full scoring run with the new version)
legal_risk rows: growing (EDGAR scraper active)

If new chat resumes:
- git status (clean expected)
- pytest --tb=no -q (181 expected)
- SELECT COUNT(*) FROM signal_scores WHERE scoring_version='0.12.0';
  (should be >0 once scheduler has run)
- SELECT MIN(reversion_score), MAX(reversion_score), AVG(reversion_score)
  FROM signal_scores WHERE scoring_version='0.12.0';
  (confirm diverse values, not 0.0 floor)

==========================================================
END HANDOFF
==========================================================
