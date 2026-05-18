# SIGNALINTEL: HANDOFF

**Tactical session state.** Updated end of each session. For stable
project context (who/what/how), see `PROJECT_CONTEXT.md`.

Last updated: 18 May 2026, end of session. Nine commits to origin/main today across three workstreams: morning FMP entitlement observability (three commits), afternoon design pass (one design-banking commit + earlier doc-banking + brand assets), and end-of-day banking. Mark away Tuesday 19 May + Wednesday 20 May, returning Thursday 21 May.
Next session: Monday 18 May overnight bulk-job verification (financial_statements landing makes Altman Z distribution check actionable Thursday) + Tuesday 06:30 BST economic_calendar cron observation under new run_log + Telegram escalation. FRESH CHAT recommended Thursday return.

---

## JUST SHIPPED — 18 May 2026

### Block 1: Morning — FMP entitlement observability (three commits, pushed)

- **7e8ce60** — feat(fmp): add FMPEntitlementError + Telegram alert dedup helper. New exception class mirrors FMPRateLimitError pattern. Rate-limited Telegram alert helper prevents repeat-notification floods.
- **d5dea2a** — feat(scheduler): wire FMPEntitlementError + run_log into FMP handlers. All three FMP jobs (economic_calendar, fmp_earnings, fmp_dividends) now write SUCCESS or FAILED to run_log on every run + fire rate-limited Telegram alert on HTTP 402.
- **9558e6a** — test(fmp): cover entitlement error escalation + Telegram dedup. Six new tests; total 247 passing (+6), 1 failed (test_fmp_economic_calendar_freshness, real production staleness, by-design red per P26), 1 skipped.

Diagnostic origin: 18 May 06:30 BST economic_calendar cron returned HTTP 402 (FMP plan entitlement issue), swallowed silently for 11 days. Three-layer swallow: _get() returns None → fetch coerces to [] → job logs "0 events saved" → no run_log entry. Fix is observability, not entitlement repair. Scheduler restart via launchctl kickstart to pick up new code: PID 32257 → 86234. Banner verified v0.13.0 + HEAD 9558e6a + 11:33 BST start.

Process notes from the morning block:
- Gate 4 paste of new Python code surfaced what looked like broken syntax (orphan log_run calls). Diagnostic prompt re-elicited via sed/cat + py_compile — chat client had truncated continuation lines, source on disk intact. Symmetric with 14 May "diagnose before alarming" lesson.
- CC condensed Gate 5 (test file paste) into a summary instead of pasting verbatim. Caught and corrected before commit — gate-report-condensation drift pattern from 14 May, mitigation held.

### Block 2: Afternoon — Design pass (one strategy commit + brand + two mockups, all pushed)

**Strategy session: Phase 2c + Phase 3 added to roadmap.** Beta tester Guy's feedback (5 points: bewildering terminology, markets page chart timespans unlabelled, no LSE, search clipped, /backtest purpose unclear) reframed positioning. Athena's first reflex was to dismiss Guy as outside the target user; Mark pushed back — tagline "institutional-grade tools for non-institutional traders" explicitly promises to serve him. Dismissal was positioning failure. Logged as P27 in PROJECT_CONTEXT (commit 09b6ab0). Phase 3 (LSE + HK markets, Lite ticker/dashboard, /learn hub, YouTube series) and Phase 2c (Multi-user notifications substrate: per-user Telegram + SendGrid) inserted before paywall.

Pricing question deferred. Don't ask Guy what he'd pay yet — answer worthless without seeing completed product, shifts beta→sales tone, methodology fit. Park as Phase 3 / pre-paywall problem.

Completeness audit: ~40% complete. Time-to-paid-launch 4-6 months. Phase 1 ~85%, Phase 2 paywall 0%, Phase 2c notifications 0% (~2-3 weeks), Phase 3 LSE/HK/Lite/Learn 0% (6-10 weeks core + 30-50 hrs video).

**Design brief locked across four sections.** Full content in PROJECT_CONTEXT under DESIGN BRIEF (LOCKED 17 MAY 2026, extended 18 May): Site Map (7 top-nav items + footer reference), Dashboard panel specs (13 panels), Marketing Homepage spec (8 sections, Public/Robinhood aesthetic), Brand System (Option C palette: green-gold gradient replacing teal-gold).

**Hero mockup v3 banked** (commit 3d4ca9a, earlier in session before banking discipline triggered). 27.8 KB. Locked aesthetic: Hybrid C palette (navy hero, off-white below-fold), two-tier nav (Signal Vault parent utility bar + SignalIntel primary), asymmetric composition (headline left, live 9-component radar scorecard right), Fraunces serif + Inter Tight + JetBrains Mono.

**Section 2 (Transparency) v1 + Section 3 (Methodology) v2 banked together** in commit 7f8014d as the consolidated design-pass commit.

- `section2_transparency_v1.html` (23.0 KB) — Light Public.com aesthetic. "We show our work" headline left + supporting prose right. Recent Rating Changes events panel as anchor visual (6 rows: 3 wins NVDA / MSFT / TSM + 3 losses PLTR / AAPL / RIVN, "since launch" scope, "11,807 changes logged" stat). Three numbered proof columns (Verified record / Open methodology / Wins and losses). Pull-quote attributed to "Mark Nicholson · Founder, The Signal Vault". Final stat in column 3 is "7 Signal tiers, all independently tracked" — real-today metric, replaces the placeholder "58.3% Strong-tier win rate" until BULLISH ACCURACY DECISION GATE fires post-Phase 3 + 30 days.
- `section3_methodology_v2.html` (22.8 KB) — "Nine components. One score. No shortcuts." headline at 64px (shrunk from 80px in v1 for better visual balance against the radar below). Full-width radar centrepiece showing AAPL scoring breakdown (composite 61.2, Stable tier badge) with deliberately asymmetric polygon shape: strong on Quality (82), Inst. Own (88), Analyst Mom (74); soft on Momentum (38), Reversion (32), Earnings (45); middling on Insider (52), Volume (58), Piotroski (71). Story-shape demonstrates engine honesty — even AAPL isn't automatically Very Strong. Live v0.13.0 components in green, v0.14 future components (Earnings, Piotroski, InstOwn, Analyst Mom) marked in Signal Vault gold with v0.14 suffix on score labels. Caption: "AAPL · Apple Inc · A 'Stable' call — strong on quality and institutional backing, soft on momentum and mean reversion. The engine doesn't care about brand recognition." Nine-cell what-we-measure grid below radar. Modifiers row covers Legal risk (additive, -5 to -60), Bankruptcy risk (additive, 0 to -60), Sector strength (multiplicative, ±7.5%). Closing strip with version-stamped methodology framing.

**Brand assets refreshed.** The earlier morning's interim PNG (`The_Signal_Vault_Brand_Map.png`, committed 91ca685) was renamed on disk to `Signal_Vault_Brand_System.png` for a more accurate filename — content unchanged from 91ca685, verified by MD5 (ac994315e52251040cc409250660b6c0). Additionally `SignalIntel_Infographic_v3.png` (1.75 MB) added: full Signal Vault platform vision infographic. Vertical layout, 12 sections covering master brand, positioning, product family grid, SignalIntel deep-dive, 7-tier signal system, four-feature highlights, performance record placeholder (Q3 2026 launch), virtual portfolio + leverage tiers, monthly tournament leaderboard, subscription pricing tiers, 9-milestone roadmap, footer. Infographic status: ready for internal use (pitch decks, investor conversations, recruiting, partner pitches); external/public use pending lawyer sign-off on bottom disclaimer line.

Banked together in commit 7f8014d as: 1 rename + 3 additions, 1,471 lines added across the two HTMLs and one PNG.

### Block 3: End-of-day banking

Current commit covers HANDOFF rewrite (this file) + PROJECT_CONTEXT targeted edits (new PROCESS LESSON for artefact-bytes verification + DESIGN BRIEF implementation sequence update reflecting Section 2/3 banked and Dashboard as next).

### Test count at session close

247 passing, 1 failed (test_fmp_economic_calendar_freshness — real production staleness by design per P26), 1 skipped (4 prior + Yahoo gains − adjustments from this morning's commits). Test count drift from earlier sessions tracked in STILL OPEN.

---

## CURRENT STATE (end of 18 May 2026)

- gunicorn: PID 55935 (unchanged from 17 May)
- scheduler: PID 86234 (restarted 18 May 11:33 BST to pick up FMP entitlement code; banner verified v0.13.0 + HEAD 9558e6a + 11:33 BST start)
- HEAD: 7f8014d (or this commit's hash after end-of-day banking)
- 9 commits pushed to origin/main today (3 FMP + 2 doc-banking from yesterday's pattern + 4 design-pass and brand)
- pytest: 247 passing, 1 failed (by-design red), 1 skipped
- SCORING_ENGINE_VERSION: 0.13.0 (unchanged)
- economic_calendar: 11 days stale at session start; new observability shipped this morning. Tuesday 06:30 BST cron will write SUCCESS or FAILED to run_log + fire Telegram alert if 402 persists.
- Yahoo enrichment tables: continuing daily feed. financial_statements bulk job lands overnight Sunday→Monday and continues; earnings_history bulk lands Tuesday. Altman Z distribution check now data-ready as of Monday morning.
- Site live: HTTP/2 via Cloudflare → /login; P13 ticker events fix verified empirically on 17 May still holding.
- venv.OLD: still untracked, 72h timer elapsed Sunday 17 May, eligible for deletion any time.
- Local-only commits: zero. All 9 of today's commits pushed to origin/main.

---

## PROCESS TELLS — 18 May 2026

- **Artefact-bytes verification.** Athena described the new brand PNG to CC as a richer asset than what landed on disk. CC's git rename detection saw byte-identity with the morning's Brand_Map PNG (MD5 match) and STOPPED the commit before the misleading description landed in git history. Pattern banked as new PROCESS LESSON in PROJECT_CONTEXT. Lesson: verify file bytes against description before firing banking prompt, not after CC catches the gap. Same family as 14 May "diagnose before alarming" but applied to Athena's artefact authorship rather than CC's gate output.

- **Positioning audit on beta feedback.** Athena's first reflex on Guy's confusion was to dismiss him as outside target user. Mark pushed back; "institutional-grade tools for non-institutional traders" explicitly promises to serve users like Guy. Reflex was a positioning failure. Codified as P27. Pattern: when a beta tester struggles with terminology or onboarding, the question is never "is this user wrong?" — it's "where in our positioning are we writing a cheque the product can't cash?"

- **Pricing question timing.** Don't ask beta testers what they'd pay before the product is complete. Answer is worthless; shifts beta→sales tone; methodology fit is wrong. Park as Phase 3 / pre-paywall problem when full feature set exists to anchor the price test. Banked.

- **Single-prompt vs Phase 1+2 calibration on housekeeping.** End-of-session work-completion housekeeping (committing both mockups + brand work + HANDOFF + PROJECT_CONTEXT) ran as Phase 1 audit + Phase 2 banking. Right ceremony for the scope — 4 file changes across three categories with one byte-identity surprise that proved out the gate. Single-prompt would have committed the wrong description against the right file.

- **Design queue prioritisation.** Athena recommended Dashboard restructure as next mockup over completing remaining marketing homepage sections (4-8). Rationale: Dashboard is the most-visited logged-in page once paywall lands, tests whether Option C palette refinement works in dense dark monospace environment (only light Public.com proven so far), and is the hardest remaining design problem so better solved while brief is fresh. "Finish the marketing homepage for completeness" rejected as tidying instinct rather than value-driven prioritisation.

- **CC discipline held cleanly throughout the day.** Banking gate STOPs on staging-anomaly worked at 7f8014d (rename detection); diagnostic re-elicitations (Gate 4 syntax / Gate 5 paste) handled cleanly without scope drift. No negative-instruction failures. No unauthorised doc edits.

---

## STILL OPEN

### Tuesday 19 May verification (Mark away)

- **economic_calendar 06:30 BST cron** under new observability. Will write SUCCESS or FAILED to run_log + fire Telegram alert if HTTP 402 persists. First fire under the new logging.
- **fmp_earnings 06:05 BST cron** same observability. First fire under new logging.

### Wednesday 20 May verification (Mark away)

- **earnings_history bulk job** lands overnight. Verify rows populated Wednesday morning when Mark checks in.

### Thursday 21 May return

- **FMP plan tier decision.** Based on Tuesday observation: if 402 persists, decision needed on whether to upgrade FMP plan (cost vs entitlement value) or drop economic_calendar from feature set. Current Phase 1 inventory queued.
- **Altman Z distribution check NOW DATA-READY.** financial_statements bulk job lands Sunday→Monday overnight; Thursday return has full data to run distribution analysis. Verify -10 / -60 penalty tiers calibrated for the production universe before v0.13.0 backtest data accumulates. compute_z_raw() helper extraction queued from 17 May Phase 1 audit.
- **Marketing homepage Section 4+ design or Dashboard mockup.** Per the new design queue prioritisation in PROJECT_CONTEXT: Dashboard restructure is the next design session. Marketing Sections 4-8 deferred as a later batch.
- **venv.OLD deletion** eligible (72h+ elapsed).

### LAUNCH PREP (carried forward from 17 May)

- Google Search Console indexing setup at site launch (sitemap.xml, robots.txt, domain verification).
- Open Graph / social preview meta tags on marketing homepage.
- Analytics decision: Plausible / Fathom / GA4. Privacy-friendly fit for transparency-first brand positioning vs GA4 conventional default. Decision needed before public launch.

---

## NOTES FOR FRESH-CHAT ATHENA THURSDAY

- Read PROJECT_CONTEXT.md first (stable), then this HANDOFF.
- Today's three substantive blocks: morning FMP entitlement observability (3 commits, all pushed), afternoon design pass (Phase 3 strategy add, Hero v3 mockup carried over from 17 May, Section 2 v1 + Section 3 v2 + brand asset refresh in one commit), end-of-day banking (this commit).
- Both gunicorn and scheduler under LaunchAgents survive reboot. Scheduler PID changed today (32257 → 86234) due to restart for new FMP code.
- First action Thursday: check Tuesday + Wednesday cron outcomes via run_log queries. If economic_calendar still 402-ing, FMP plan decision needs to happen. If fresh rows landed, transient self-resolved.
- Second priority Thursday: Altman Z distribution check. Now actionable (financial_statements data ready).
- Third priority Thursday: Dashboard restructure mockup if design session resumes, or one of the engineering items above.
- venv.OLD still on disk; eligible for deletion at any point Thursday onwards.
- The Superpowers plugin is installed in CC but not enabled. Athena flagged it as a candidate for Phase 2c implementation work or the Altman Z distribution analysis. Re-evaluate when one of those sessions opens.

---

*End handoff.*
