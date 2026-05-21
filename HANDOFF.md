# SIGNALINTEL: HANDOFF

**Tactical session state.** Updated end of each session. For stable
project context (who/what/how), see `PROJECT_CONTEXT.md`.

Last updated: 21 May 2026, end of session. Substantial day: fourteen commits to origin/main across five workstreams. Morning FMP entitlement observability (3 commits), afternoon design pass (1 design + brand commit), end-of-day banking (1 commit), parallel-session auth-adjacent pre-commit hook with P23 mechanical enforcement (5 commits), housekeeping cleanup (2 commits), and the Altman methodology switch from classic Z (1968 manufacturing) to Altman Z'' (1995 non-manufacturing) — three Phase 2 sub-phases (3 commits) bumping SCORING_ENGINE_VERSION 0.13.0 → 0.14.0. Mark drove the session through to end-of-day without break.

Next session: Yahoo Finance pipeline + next scoring component(s), fresh chat. Dashboard + nightly backup shipped and pushed 21 May.

---

## JUST SHIPPED — 21 May 2026

- /dashboard greenfield build (Phase 2A+2B), commit **db38c56**, pushed. Net-new route + template (no prior /dashboard existed; old / did dashboard-ish work into index.html). 13-panel grid, Option C dark palette (navy-950/green-400; gold reserved for Elite). Above-fold 6 panels; Elite-gated Penny Stock spotlight (server-side gated — free clients receive NO pick data, verified via page-source check on free account mark2); below-fold 6 panels. Logged-in `/` now redirects to /dashboard (legacy index() body preserved as commented dead code). Bearish panel excludes composite=0 (penalty-floored). Design contract: `docs/mockups/dashboard_restructure_v1.html`. Helper extractions in web/app.py: `_get_sector_performance`, `_get_penny_pick_full`, `_compute_theme_counts` (behaviour-preserving; original routes unchanged).
- Nightly DB backup, commit **0933f13**, pushed (script only; plist + backup dir machine-local, out of repo). `scripts/backup_database.sh`: WAL-aware `sqlite3 .backup`, integrity-gated, atomic promotion, 7-daily + 4-weekly rotation. LaunchAgent `io.thesignalvault.backup`, daily 03:30 BST. Restore-verified (row parity 227,721). First auto-run tonight.
- Auth-adjacent pre-commit hook (P23) fired on the dashboard commit and was HONOURED — committed interactively via TTY, not bypassed with `--no-verify`. The hook caught us at speed on a deadline day; correct path taken.

## CURRENT STATE (end of 21 May 2026)

- HEAD: `0933f13`, pushed to origin/main. Local-only commits: zero.
- gunicorn restarted twice today (dashboard route deploys): final PIDs 53900/53903. scheduler PID 10325. cloudflared running.
- SCORING_ENGINE_VERSION: **0.14.0** (unchanged today).
- DB: **~1.2 GB** (21 May 2026; ~227,721 signal_scores rows; was ~328MB post-VACUUM 13 May 2026).
- Site live: /dashboard reachable logged-in; / redirects logged-in users to /dashboard; logged-out / still serves legacy home flow.
- Backup: first automated 03:30 BST run pending tonight — verify via `~/signalintel/logs/backup.out.log` tomorrow.

## STILL OPEN — 21 May 2026

CARRY FORWARD (flagged for today in the 18 May handoff, NOT addressed — today went to dashboard + backup; these remain open):

- FMP economic_calendar 402 — DECIDED 21 May: do not upgrade FMP plan. Reroute economic-calendar data via Yahoo (try first) or other free source; FMP paid upgrade only if all free options fail. Execution folded into the Yahoo pipeline scope. `economic_calendar` job still 402-failing daily until rerouted — acceptable known-red until then.

NEW today:

- (see FOLLOWUPS in PROJECT_CONTEXT — appended this session)

## NOTES FOR FRESH-CHAT ATHENA (Yahoo session)

- **IGNORE the archived 18 May notes below — superseded.** Read THIS section + PROJECT_CONTEXT first.
- Next session: **Yahoo Finance pipeline + next scoring component(s)** toward the 16-component vision (8 built). Large session, fresh chat by design.
- Dashboard + backup banked and pushed; site on a known-good restore point.
- Live state: engine 0.14.0, DB ~1.2GB, /dashboard live, nightly backup armed.
- Two carry-forward decisions waiting (FMP plan, Altman Z) — surface them but don't let them derail the Yahoo session unless Mark picks them up.

---

## ARCHIVE — 18 May 2026 handoff (superseded by 21 May)

## JUST SHIPPED — 18 May 2026

### Block 1: Morning — FMP entitlement observability (three commits, pushed)

- **7e8ce60** — feat(fmp): add FMPEntitlementError + Telegram alert dedup helper. New exception class mirrors FMPRateLimitError pattern. Rate-limited Telegram alert helper prevents repeat-notification floods.
- **d5dea2a** — feat(scheduler): wire FMPEntitlementError + run_log into FMP handlers. All three FMP jobs (economic_calendar, fmp_earnings, fmp_dividends) now write SUCCESS or FAILED to run_log on every run + fire rate-limited Telegram alert on HTTP 402.
- **9558e6a** — test(fmp): cover entitlement error escalation + Telegram dedup. Six new tests; total 247 passing, 1 failed (P26 by-design red), 1 skipped.

Diagnostic origin: 18 May 06:30 BST economic_calendar cron returned HTTP 402, swallowed silently for 11 days. Three-layer swallow pattern. Fix is observability. Scheduler restart via launchctl kickstart: PID 32257 → 86234. Banner v0.13.0 + HEAD 9558e6a + 11:33 BST.

### Block 2: Afternoon — Design pass (one strategy + brand + two mockups commit, pushed)

**Strategy session: Phase 2c + Phase 3 added to roadmap.** Beta tester Guy feedback reframed positioning (P27 logged). Phase 3 (LSE + HK markets, Lite ticker/dashboard, /learn hub, YouTube series) and Phase 2c (multi-user notifications: per-user Telegram + SendGrid) inserted before paywall. Pricing question deferred to pre-paywall. Completeness audit: ~40% complete, time-to-paid-launch 4-6 months.

**Design brief locked across four sections.** Site Map, Dashboard panel specs (13 panels), Marketing Homepage spec (8 sections), Brand System (Option C green-gold palette). Full content in PROJECT_CONTEXT.

**Hero mockup v3 banked** earlier (commit 3d4ca9a).

**Section 2 (Transparency) v1 + Section 3 (Methodology) v2 + brand asset refresh** banked in commit **7f8014d**: 1 rename + 3 additions, 1,471 lines across two HTMLs and one PNG.

### Block 3: End-of-day banking (commit c27ba4e)

HANDOFF rewrite + PROJECT_CONTEXT targeted edits (new PROCESS LESSON for artefact-bytes verification + DESIGN BRIEF implementation sequence update).

### Block 4: End-of-day cleanup — repo rename + stale folder deletion (commit 1f49ef9)

GitHub repo renamed `trading-system` → `signalintel`. Stale `~/trading-system` folder (10.4 MB, last modified 24 April 2026) deleted. Local remote updated explicitly. PROJECT_CONTEXT required no edits — Phase 2c migration already documented.

### Block 5: WAL sidecars to .gitignore (commit 2d23c28)

`data/trading_system.db-shm` and `data/trading_system.db-wal` added to .gitignore + untracked from index. Sidecars stay on disk; git status no longer flutters on every DB read. Behaviour-preserving verification: WAL flutter touched mtime but git status stayed clean.

### Block 6: Parallel session — Auth-adjacent pre-commit hook (five commits, pushed)

Parallel CC session shipped the auth-adjacent pre-commit hook that was queued in structural debt since 17 May. P23 mechanical enforcement now live. Five commits to origin/main: **f72d8b4, 0851963, 8fe91a0, 851221a, 0d0ff43**. New section added to CLAUDE.md telling CC how to handle auth-adjacent commits. P28 documented in PROJECT_CONTEXT (the auth-related P28; Altman invariant added separately as P29).

### Block 7: Altman methodology switch — Z (1968) → Z'' (1995), v0.14.0 (three commits, pushed)

Phase 1 (read-only inventory, no commit) confirmed 3,655 of 4,703 tickers have complete six Altman financial inputs. Phase 2a, 2b, 2d landed across three commits:

- **8df05c8** — refactor(scorer): extract compute_z_raw helper for Altman Z math. Kwargs-only signature prevents silent argument-swap. 8 new tests (14 cases via parametrize). Behaviour-preserving refactor — existing 5 Altman tests + SS07 snapshot pass unchanged. No SCORING_ENGINE_VERSION bump.
- **74a0228** — feat(scorer): add compute_z_double_prime_raw + analysis script Z'' extension. Adds Altman Z'' (1995 non-manufacturing) helper alongside classic. New scripts/altman_distribution_analysis.py runs distribution analysis across the production universe. 6 new tests (12 cases via parametrize), 273 total passing. CSV output: data/altman_distribution_2026-05-18.csv (gitignored).
- **5125ac4** — feat(scorer): switch Altman penalty to Z'' (1995 non-manufacturing) [v0.14.0]. score_altman_penalty now calls compute_z_double_prime_raw. SCORING_ENGINE_VERSION 0.13.0 → 0.14.0 MINOR per P18. Test updates: grey-zone test inputs changed to land in Z''=2.0795 (preserves -10 coverage); other Altman tests pass under Z'' unchanged. SS07 snapshot row unchanged (Z''=-6.20, still -60). P27 added to docs/scoring_invariants.md. Scheduler restarted: PID 97826 → 10325 under v0.14.0 + HEAD 5125ac4.

**Empirical justification for the methodology switch (Phase 2b analysis):**

| Tier | Classic Z (1968) | Altman Z'' (1995) |
|---|---|---|
| Distress (most penalised) | 1,691 (46.6%) | 1,292 (35.6%) |
| Grey | 594 (16.4%) | 443 (12.2%) |
| Safe | 1,346 (37.1%) | 1,896 (52.2%) |
| **Any penalty** | **2,285 (62.9%)** | **1,735 (47.8%)** |

Classic Z penalised 62.9% of the SignalIntel ticker universe — a calibration failure for a tech-heavy non-manufacturing universe. Z'' reduces this to 47.8% with thresholds appropriate for non-manufacturing companies. Healthcare sector concentration in distress dropped from 47% to 34.4%. Penalty magnitudes (-10/-30/-60) preserved.

Process notes from the Altman thread:
- Phase 1 + Phase 2 pattern with intermediate mini-gate (Phase 1.5) for test-input decisions worked cleanly. CC stopped at every gate, escalated decisions correctly, no scope drift.
- CC self-flagged hedge words per P16 throughout.
- One false-alarm CC catastrophising on a "1.29 GB tracked binary" turned out to be untracked (already in .gitignore since commit 73ab9c0). Lesson banked: when CC describes a state as anomalous, check the prediction not the alarm.
- Verbose CC output containing summary tables in place of verbatim diff/stdout was caught twice and re-elicited. Same gate-condensation pattern as 14 May.
- Query inventory before commit caught two Phase 2e candidates (partial-run watchlist mixed-version risk; history chart silent cutover annotation) — neither blocks 2d shipping.

### Test count at session close

273 passing, 1 failed (test_fmp_economic_calendar_freshness — real production staleness by design per P26), 1 skipped. Net +26 from morning's 247 baseline: 6 FMP tests + 14 compute_z_raw cases + 12 compute_z_double_prime cases − 6 (existing Altman tests with updated inputs/docstrings rather than additions).

---

## CURRENT STATE (end of 18 May 2026)

- gunicorn: PID 55935 (unchanged from 17 May)
- scheduler: PID 10325 (restarted 18 May ~17:30 BST after Phase 2d; banner verified v0.14.0 + HEAD 5125ac4)
- HEAD: 5125ac4 + whichever commit lands from this end-of-day doc-banking turn
- 14 commits pushed to origin/main today (3 FMP + 1 strategy/design + 1 banking + 1 cleanup + 1 WAL + 5 parallel auth-hook + 3 Altman)
- pytest: 273 passing, 1 failed (by-design red), 1 skipped
- SCORING_ENGINE_VERSION: 0.14.0 (bumped from 0.13.0 in commit 5125ac4)
- economic_calendar: 11 days stale at session start; new observability shipped this morning. Tuesday 06:30 BST cron tomorrow fires under the new logging for the first time.
- Yahoo enrichment tables: continuing daily feed. financial_statements bulk job populated overnight Sunday→Monday (3.5M rows across 4,703 tickers, 5-year coverage). Altman Z distribution check completed today using this data.
- Site live: HTTP/2 via Cloudflare → /login; auth-adjacent pre-commit hook now mechanically enforces P23.
- venv.OLD: DELETED today (135 MB reclaimed); replaced trading-system folder also DELETED (10.4 MB).
- Local-only commits: zero. All 14 of today's commits pushed.

---

## PROCESS TELLS — 18 May 2026

- **Artefact-bytes verification (morning).** Athena described the new brand PNG to CC as a richer asset than what landed. CC's git rename detection caught byte-identity with the morning's PNG (MD5 match) and STOPPED the commit. Logged as PROCESS LESSON in PROJECT_CONTEXT.
- **Positioning audit on beta feedback.** Athena's first reflex on Guy's confusion was dismissal; Mark pushed back; logged as P27 in PROJECT_CONTEXT. Pattern: beta-tester confusion is a positioning failure, not a user failure.
- **Pricing question timing.** Don't ask beta testers what they'd pay before product is complete. Phase 3 / pre-paywall problem.
- **False-alarm catastrophising (Athena and CC both).** Athena flagged the 1.29 GB DB as a tracked-binary problem; CC compounded the alarm. Five minutes of empirical inventory showed it was already gitignored and untracked since commit 73ab9c0. Lesson: check the actual `git ls-files` output before catastrophising on size alone. Same family as 14 May "diagnose before alarming."
- **Gate-report condensation persists.** CC condensed pytest output to summary tables instead of pasting verbatim during Phase 2b verification and Phase 2d verification. Caught both times and re-elicited. Mitigation works but the pattern is recurring — worth a CLAUDE.md note for CC next session.
- **Multi-phase Phase 1 + 2 pattern scales.** Altman work used Phase 1 (inventory) → Phase 1.5 (mini-gate for test-input decisions) → Phase 2a (refactor) → Phase 2b (analysis) → Phase 2c (decision lock) → Phase 2d (implementation). Six staged gates, zero rework. Worth banking as the template for any future methodology change.
- **Empirical-evidence-over-prediction discipline held.** Every decision point in the Altman thread had numbers behind it: 62.9% / 47.8% / 399-ticker delta / Z''=2.0795 for grey-zone fixture / Z''=-6.20 for SS07. No "should work" handwaving accepted.
- **Parallel CC sessions work.** Auth-adjacent pre-commit hook ran in a separate CC session while Altman occupied the main session. Five commits cleanly interleaved with three Altman commits on origin/main. No merge conflicts. Pattern viable for future independent workstreams.

---

## STILL OPEN

### Tuesday 19 May verification

- **economic_calendar 06:30 BST cron** under new observability. Will write SUCCESS or FAILED to run_log + fire rate-limited Telegram alert if HTTP 402 persists.
- **fmp_earnings 06:05 BST cron** same observability.
- **First 0.14.0 scoring run tonight** (20:00 BST scheduled scoring job). Watch tomorrow morning's run_log for clean completion. The first production-universe Z''-based composite scores will land in signal_scores tagged scoring_version='0.14.0'.

### Tuesday 19 May actionable

- **FMP plan tier decision.** Based on Tuesday morning observation: if 402 persists, decision on whether to upgrade FMP plan (cost vs entitlement value) or drop economic_calendar from feature set. Phase 1 inventory queued (cost-vs-value framing already shaped).
- **Dashboard restructure mockup** is next in the design queue. Most-visited logged-in page, tests Option C palette in dense dark monospace, hardest remaining design problem.
- **Engineering pivot option** if design momentum shifts. Candidates: schema-coupling tripwire broader sweep (7 more insert helpers per FOLLOWUPS), shadowed tier map convergence (9 templates), scheduler LaunchAgent symmetric treatment, mobile responsiveness retrofit, SB01 snapshot mismatch diagnostic.

### Phase 2e candidates (Altman cutover follow-ups)

- **Partial-run mixed-version watchlist risk.** Watchlist + ticker-detail "latest per ticker" patterns can show some tickers at 0.13.0 and others at 0.14.0 if a scoring run crashes partway through. Mixed-version composite_scores are mathematically incomparable (Z and Z'' produce different penalty distributions). Mitigation: monitor first 0.14.0 run to completion before users browse, OR add transactional "wipe-and-write" pattern for the scoring run.
- **History chart silent methodology shift.** Ticker-detail timeline at web/app.py:1357-1363 will render Z- and Z''-derived composites as a continuous line. Users won't see the cutover. Phase 2e: vertical dashed line + annotation at cutover date, OR colour-code points by scoring_version.

### Live 0.14.0 distribution monitoring

The Phase 2b analysis projected 47.8% penalised footprint under Z''. The first week of live 0.14.0 scoring data will confirm whether the projection holds against real production composites. If the live distribution diverges materially, Phase 2e or 2f investigation needed.

### LAUNCH PREP (carried forward from 17 May)

- Google Search Console indexing setup (sitemap.xml, robots.txt, domain verification).
- Open Graph / social preview meta tags on marketing homepage.
- Analytics decision: Plausible / Fathom / GA4. Privacy-friendly fit for transparency-first brand vs GA4 conventional default.

---

## NOTES FOR FRESH-CHAT ATHENA TUESDAY

- Read PROJECT_CONTEXT.md first (stable), then this HANDOFF.
- 14 commits to origin/main today, five workstreams: FMP observability, design pass, banking, auth-adjacent pre-commit hook, Altman Z → Z'' methodology switch with version bump to 0.14.0.
- Both gunicorn (PID 55935) and scheduler (PID 10325) under LaunchAgents survive reboot. Scheduler restarted twice today: once for FMP code (86234), once for Altman Phase 2a refactor (97826), once for Phase 2d methodology switch (10325).
- First action Tuesday: empirical read of run_log for Tuesday morning's FMP crons (06:05, 06:30 BST) AND tonight's 20:00 BST first-0.14.0 scoring run. Three SQL queries:
```
  sqlite3 data/trading_system.db "SELECT job_name, run_at, status, substr(error_message,1,80) AS err FROM run_log WHERE job_name IN ('economic_calendar','fmp_earnings','fmp_dividends','score_all_tickers') AND run_at >= '2026-05-18 19:00' ORDER BY run_at DESC LIMIT 20;"
```
- Second priority Tuesday: based on FMP outcomes, either FMP plan tier decision (if persistent 402) OR move to Dashboard restructure mockup (next in design queue) OR engineering pivot.
- Phase 2e candidates from the Altman cutover: partial-run watchlist mixed-version risk; history chart cutover annotation. Both presentation-layer, neither blocking.
- v0.14.0 is the new scoring substrate. All composite_score values in signal_scores tagged scoring_version='0.14.0' use Z'' methodology. Pre-cutover 0.13.0 rows preserved for historical reference; backtest endpoint at web/app.py:1800-1881 lets users compare both versions.
- Parallel-session housekeeping landed five commits for the P23 auth-adjacent pre-commit hook. CC now has a CLAUDE.md section on handling auth-adjacent commits. P28 in PROJECT_CONTEXT covers this. Altman invariant separately covered by P29 in PROJECT_CONTEXT (and P27 in scoring_invariants.md, independent numbering).
- Both `~/trading-system` (stale) and `venv.OLD` deleted today. Local-only `~/Documents/trading-system.OLD` from 15 May Phase 2c migration may still exist; not verified today.
- The Superpowers plugin in CC remains installed but not enabled. Re-evaluate when a session opens that genuinely needs it.

---

*End handoff.*