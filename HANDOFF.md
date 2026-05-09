SIGNALINTEL — SESSION HANDOFF
End of Fri 8 May 2026, ~23:50 BST → Pickup Sat 9 May morning

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
SESSION SUMMARY (FRI 8 MAY, AFTERNOON THROUGH NIGHT)
==========================================================

Heavy session. Three urgent pre-launch followups crossed off in
one day, every one properly verified, plus a fourth piece of
diagnostic work that reframed scope before Phase 2.

ACCOMPLISHED (in chronological order):

1. ✅ Reversion 0.0 prevalence resolved (urgent followup)
   - Phase 1 diagnostic: enumerated all 18 input → output paths in
     score_mean_reversion. Attribution exhaustive: 3,524 + 18 + 19
     = 3,561 rows, zero unattributed.
   - 98.96% of 0.0 scores are correct domain output (Scenario A,
     rsi ≥ 40 path). Not a bug. The remaining 37 rows are P5
     violations: 18 all-NULL inputs producing 0.0 instead of 50.0,
     plus 19 ambiguous Scenario C cases.
   - Phase 2 fix: Position A scorer fix mirroring _compute_volume's
     P5 guard pattern. Per-component neutral contribution: RSI=20,
     low_52w=17.5, sma_50=12.5. All-NULL produces 50.0 by
     construction.
   - SCORING_ENGINE_VERSION 0.11.0 → 0.12.0 per P18.
   - Defensive radar/scorecard rendering code shipped (won't fire
     under Position A but harmless and consistent with future
     scorer changes).
   - Historical prevalence query confirmed pattern is structural,
     not a v0.11.0 regression: 32.6% in v0.9.0, 33.3% in v0.11.0.
     This narrows the v0.9.0 backtest history caveat — Reversion
     was not silently broken across history; only the 37-row
     P5 violation was.

2. ✅ Legal NULL UX decision and rendering shipped (urgent
   followup)
   - Original Phase 2 attempted Reversion+Legal bundle. Legal half
     broke because PROJECT_CONTEXT's parallel-component model
     didn't match actual data shape. Reverted Legal-specific hunks,
     retained Reversion changes.
   - Legal Phase 1 diagnostic established three-state model:
     State 1 (no row, 99.34%), State 2 (NONE-level scraped clean,
     67 tickers), State 3 (populated risk, 10 tickers). Schema
     has 9 columns including filing_type. Penalty applied
     additively in scorer.py:474, before _clamp.
   - Decision: drop Legal from radar entirely (Option C-family).
     Legal is structurally an ordinal flag, not a 0–100 score; the
     ⚖️  card already renders it richer. Plus three bug fixes:
     scorecard redesign with scraped_at discriminator,
     None→Clean rendering-layer mapping, lrIsNone fix using
     scraped_at truthiness.
   - Radar reduced from 8 axes to 7 axes. State 1/2/3 visually
     distinguishable across all surfaces.
   - 4 commits: 4064c8e (radar drop), e6535fd (scorecard),
     988b4b3 (signal strip), 46a18bb (Legal revert).

3. ✅ Truthy-check rendering bug fixed (Phase 1 + Phase 2 in
   evening session)
   - Phase 1 diagnostic established: scoring layer is fully P5
     compliant for all six computed-score components. No scorer
     fixes needed. State C (NULL component score in DB) does not
     currently fire — 0 NULL rows across all components.
   - Bug pattern (truthy `s.score || 0`) at lines 945-951 affects
     Momentum/Quality/Insider/Volume on three rendering surfaces:
     radar legend, radar polygon, signal strip bar. Chip surfaces
     already correct via fmt() and scoreC() helpers.
   - Phase 2 fix: extended Reversion's existing null-overlay
     pattern to four components. Single shared null overlay dataset
     for all five nullable axes (indices 0, 1, 2, 3, 4).
   - 1 commit: a71160d. Three minutes execution time — the cleanest
     CC output of the day. Tighter scope + locked design + Phase 1
     substrate = fast clean execution.
   - Verified by State A (AAPL) and State B (CHTR Momentum=0.0,
     VICR Insider=0.0) browser walks. State C verified by code
     review against existing Reversion pattern (no production
     State C currently exists for empirical walk).

4. ✅ Scheduler banner detected runtime-code drift overnight
   - The 8 May startup banner mitigation worked: logged 0.11.0 on
     boot at 13:25 BST yesterday. The version bump commit 189e641
     landed after that boot.
   - Saturday morning health check found scheduler still running
     stale in-memory code. 10,770 v0.11.0 rows produced overnight,
     0 v0.12.0 rows. Position A Reversion fix not yet in production.
   - Detection succeeded; manual restart required. Lesson for
     PROJECT_CONTEXT: banner is necessary but not sufficient.
     Commits touching SCORING_ENGINE_VERSION or signals/scorer.py
     should trigger a scheduler restart habit.

PUSHED TO origin/main:
- 189e641 — Bump SCORING_ENGINE_VERSION to 0.12.0
- ba02258 — Render NULL legal and reversion axes (the rendering
  commit that was later partially reverted)
- 46a18bb — Revert Legal rendering changes from ba02258
- 4064c8e — Drop Legal axis from radar
- e6535fd — Redesign scorecard Legal row
- 988b4b3 — Fix signal strip Legal rendering
- 18d42be — Update HANDOFF.md (CC drift; explicit instruction said
  do not modify HANDOFF; CC did anyway. Mark to override or
  retain on review.)
- a71160d — Fix NULL rendering for Momentum/Quality/Insider/Volume

==========================================================
EMPIRICAL VERIFICATION (END OF SESSION)
==========================================================

All three urgent followups properly verified across multiple
ticker types:

- Reversion: REPL invocations confirming Position A math (50.0,
  20.0, 100.0 for the three boundary cases). Full universe rescore
  produced expected score shifts for the 37 affected rows. v0.12.0
  rows confirmed present in DB (post-rescore, pre-stale-scheduler).

- Legal: Browser walks across States 1, 2, 3 on AAPL, MKSI, DAL,
  EME, RGS, KSPI, SCZM, AA. The legal scraper running aggressively
  during verification meant three "State 1" tickers got scraped
  mid-walk — useful empirical signal that scraper coverage is
  expanding. AA verified clean as State 1; all other states
  verified across the population.

- Truthy-check: CHTR Momentum=0.0 and VICR Insider=0.0 verified as
  State B (genuine 0.0, red rendering preserved). AAPL verified as
  State A regression check (all five components render correctly).
  State C path verified by code review against Reversion pattern.

==========================================================
INFLIGHT (carried over)
==========================================================

NONE. All three urgent followups crossed off cleanly. Scheduler
restart is a Saturday-morning task, not inflight work.

==========================================================
QUEUED SESSIONS (in priority order)
==========================================================

1. Trailing-cron cleanup (small, 30-45 min)
   job_compute_target_prices (+33 min) and job_recom_priority
   (+35 min) cron jobs duplicate work that job_generate_signals
   now does inline via the chained call. Both can be removed.
   Saturday 9 May morning candidate.

2. Yahoo Finance pipeline + components 9-16 (FRESH CHAT, large)
   Strategic centerpiece. 4-6 hours for the pipeline alone before
   any of components 9-16 are written. Deserves a full focused
   session with Phase 1 inventory before any Phase 2 implementation.
   Saturday 9 May afternoon or Sunday 10 May.

3. Bullish accuracy decision gate (urgent pre-launch, decision-
   not-engineering)
   Re-evaluate Strong tier after components 8-16 are live and
   30 days of post-completion data. If still under 55% win rate,
   reconsider launch positioning. Cannot be actioned until Yahoo
   pipeline lands and 30 days pass.

4. Insider component historical data caveat (urgent pre-launch,
   decision-not-engineering)
   Pre-7-May-2026 Custom view bugs corrupted insider data across
   847k+ historical rows. Decide whether to invalidate v0.9.0
   backtest history publicly or document the caveat and retain.
   Reversion's Phase 1 narrowed the case (Reversion was not
   silently broken across history); Insider question now stands
   alone. Decision wants sit-with-implications time, not engineering.

5. Component rendering refactor (post-Yahoo, pre-launch)
   Convert hardcoded 8-component (now 7-component) rendering on
   ticker page to array-driven before adding components 9-16.
   Natural batch boundary.

6. Scraper substrate audit (post-Yahoo, 90-min hard cap)
   Eight scraper-layer issues surfaced 7-8 May. Inventory only,
   no fixes during the session. Document the debt before deciding
   fix order.

7. Volume and avg_volume NULL columns
   The rel_volume fix exposed but did not address two related
   columns. Small follow-up session.

8. Exchange filter UI on screener (small, 30-45 min)
   Sort already shipped 8 May. Filter is a separate UI decision.

9. Deprecation cleanup
   screener_snapshots.exchange column no longer written to.
   Drop column once read paths verified redundant.

10. Dead script: scripts/build_legal_risk.py has a pre-existing
    broken import. No callers reference it. Likely delete.

11. Cosmetic: web/app.py banner says "5000" but server runs on 5001.

==========================================================
KEY ARCHITECTURAL FACTS LEARNED THIS SESSION
==========================================================

- Legal data lives in legal_risk table (9 columns including
  risk_level, risk_label, risk_color, penalty, scraped_at,
  filing_type), NOT as a parallel component score on signal_scores.
  The penalty applies additively to composite_score during scoring,
  not as a separate stored 0–100 score. PROJECT_CONTEXT was
  updated on 8 May; reading the audit substrate before Phase 2
  specification is now the established pattern.

- The three-state Legal model (no-row 99.34%, NONE-level scraped
  clean 0.62%, populated risk 0.09%) is the load-bearing finding.
  Phase 2 rendering must distinguish all three states, not just
  data vs no-data. This pattern likely applies to other scraped
  data substrates as they're added.

- Position A NULL handling for Reversion (per-input neutral
  contribution) is the canonical P5 pattern alongside
  _compute_volume's early-return guard. Two patterns coexist
  cleanly; future scorer authors choose based on rubric structure.

- The legal scraper is processing tickers in real time; verification
  walks against fresh State 1 candidates have a narrow window
  before tickers move to State 2. Worth knowing for future
  scraper-data verification sessions.

==========================================================
PROCESS LESSONS CAPTURED THIS SESSION
==========================================================

1. Bundling instinct cost time. Original Phase 2 tried
   Reversion+Legal as one session. Legal's data structure didn't
   match assumptions. Tighter prompts produced cleaner CC output
   throughout the day. Treat "two related followups in one Phase 2"
   as the exception, not the rule.

2. Phase 1/Phase 2 split keeps proving itself. The truthy-check
   Phase 1 diagnostic reframed Phase 2 from "scorer fix + rendering
   + version bump" (assumed scope) to "rendering only, no version
   bump" (actual scope). Saved real time. Pre-baking design before
   Phase 2 prompts produces faster execution: 3 minutes for
   truthy-check Phase 2 vs 60-90 minutes earlier in day.

3. Soft-prediction drift bit twice yesterday. CC reported gate
   completion against unverified items (renders-after-restart
   predictions instead of empirical walks). Caught both times by
   Mark-side browser walks. The "browser walks performed by Mark,
   not CC" pattern in prompts continues to be necessary.

4. CC drifted on "do not modify HANDOFF.md" instruction. Explicit
   prompt language was ignored in commit 18d42be. Worth flagging
   as Scope Discipline pattern: CC honours scope at the file-name
   level for new instructions but may drift on negative
   instructions ("do not touch X") when X is a file CC could
   reasonably want to update. Tighter language ("modifying
   HANDOFF.md is a P-level violation, output STOP if you would")
   may be needed.

5. CC's STOP-on-ambiguity behaviour was strong. The fifth-commit
   STOP (header ribbon was the same code path as scorecard, not a
   separate surface), the Position A/B question, the inconsistency
   catch on header vs signal strip ✓ badge — all three were CC
   pushing back rather than guessing. Scope Discipline working
   as designed in these cases.

6. Scheduler banner detected runtime-code drift (the very thing
   it was designed for) but manual restart was still required.
   Detection without action habit. Lesson: banner is necessary
   but not sufficient. Future habit — any commit touching
   SCORING_ENGINE_VERSION or signals/scorer.py triggers an
   explicit scheduler restart.

7. The "scraper overtaking verification walks" pattern is a real
   thing for scraped-data substrates with active scraping. Worth
   anticipating in future verification gates: capture the state
   at query time, walk fast, accept that some walks may be against
   moved-on data.

==========================================================
HEDGE-WORDS ADDED TO P16 LIST THIS SESSION
==========================================================

- "Renders after server restart" without empirical confirmation
  (predicted instead of verified, twice in one session)
- "Single 404, error handling working as designed" without
  pasting the actual log line (twice in one session)
- "Will produce diverse [score]" instead of running the function
  and reporting actual output

These add to the existing list in PROJECT_CONTEXT.md.

==========================================================
CURRENT WORKSPACE STATE
==========================================================

Tests: 181 passing (verified end of evening session)
Branch: main, all eight session commits pushed to origin
HEAD: a71160d (Fix NULL rendering for Momentum/Quality/Insider/Volume)
SCORING_ENGINE_VERSION: 0.12.0 (in config/constants.py, in git)

Web server: running on port 5001 (RED terminal)
Scheduler: STALE — needs restart Saturday morning. Started ~13:25
  BST Friday, before the 0.12.0 version bump commit. Banner
  correctly logged 0.11.0 on boot; manual restart required.
markn DB tier: ELITE
DB row counts: All overnight rows stamped 0.11.0 (10,770 in last
  12h). 0 v0.12.0 rows in production yet. First v0.12.0 production
  scoring will land on next scheduler-driven cycle after restart.

If new chat resumes:
- git status (clean expected)
- pytest --tb=no -q (181 expected)
- ps aux | grep main.py (scheduler should be running, started
  Saturday morning post-restart)
- tail -10 logs/trading_system.log (banner should show 0.12.0 +
  HEAD a71160d after restart)
- sqlite3 data/trading_system.db "SELECT scoring_version,
  COUNT(*) FROM signal_scores WHERE scored_at >= datetime('now',
  '-2 hours') GROUP BY scoring_version;" (should show v0.12.0
  rows post-restart-and-cycle)

==========================================================
END HANDOFF
==========================================================