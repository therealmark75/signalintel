# SIGNALINTEL: HANDOFF

**Tactical session state.** Updated end of each session. For stable
project context (who/what/how), see `PROJECT_CONTEXT.md`.

Last updated: 18 May 2026, end of session. Mark away Tuesday 19 May and Wednesday 20 May. Next implementation session: Thursday 21 May.

---

## JUST SHIPPED — 18 May 2026

Two parallel tracks today: a morning implementation session (FMP entitlement observability shipped to production) and an afternoon strategy + design session (Phase 3 added, Phase 2c added, brand refresh, marketing homepage hero mockup locked).

### Morning implementation: FMP entitlement observability (3 commits, pushed)

Triggered by 18 May 06:30 BST economic_calendar cron firing red against real production staleness — the test_fmp_economic_calendar_freshness test (added 17 May) caught an 11-day silent failure. Empirical root cause: FMP returned HTTP 402 on /economic-calendar and the scraper layer treated it as "no data" rather than "entitlement broken." Three layers of swallow stacked: `_get()` returned None on the warning, `fetch_economic_calendar()` coerced None to `[]`, the job handler logged "0 events saved" and wrote nothing to run_log. 11 days of silence.

- **7e8ce60** — `feat(fmp): add FMPEntitlementError + Telegram alert dedup helper`. New `FMPEntitlementError` class in `scrapers/fmp_scraper.py` with `status_code` and `path` attributes. `_get()` raises on HTTP 401/402/403, mirrors the FMPRateLimitError 429-streak pattern. Branch order preserved: 200 → 429 → 401/402/403 → else. `notifications/telegram.py` gains `_last_fmp_alert_at` module-level dedup dict and `send_alert_rate_limited(key, message, min_interval_s=86400)` helper. In-memory dedup state is process-local — restart resets the dict, documented in the docstring.
- **d5dea2a** — `feat(scheduler): wire FMPEntitlementError + run_log into FMP handlers`. All three FMP job handlers (`job_economic_calendar`, `job_fmp_earnings`, `job_fmp_dividends`) edited to identical shape: SUCCESS log_run write on green runs, FMPEntitlementError except clause writes FAILED log_run + fires rate-limited Telegram alert, generic Exception catches other failures. job_name values locked: `economic_calendar`, `fmp_earnings`, `fmp_dividends`. Closes the 17 May "RUN_LOG OBSERVABILITY GAP ON job_economic_calendar" FOLLOWUP, extended to all three FMP jobs.
- **9558e6a** — `test(fmp): cover entitlement error escalation + Telegram dedup`. New `tests/test_fmp_entitlement_error.py` with 6 tests: 402/401/403 raise FMPEntitlementError; 500 does NOT raise (5xx stays in retry loop); job_economic_calendar writes FAILED on entitlement error; Telegram dedup boundary cases (first fire, within-window suppression, different-key fires, past-window re-fires). All stub requests.get + time.sleep, no real HTTP. economic_calendar handler test reconstructs the handler body locally because the real handler is nested inside main.py's scheduler setup — queued as FOLLOWUP to lift handlers to module-level.

### Scheduler restart, banner verified

Old PID 32257 (running since 15 May 20:57 BST) killed via `launchctl kickstart -k gui/501/io.thesignalvault.scheduler`. New PID 86234 started 18 May 11:33:23 BST. Startup banner confirmed SCORING_ENGINE_VERSION 0.13.0, git HEAD 9558e6a, ISO start time. Smoke-test imported FMPEntitlementError from running interpreter context, attributes resolved correctly, message format matches locked spec. Zero ERROR/FAILED/Traceback entries from the new process in first 10 seconds.

### Test count

239 → 247 passing (+6 new entitlement tests, +2 from prior session pickup, 0 regressions). 1 failed: `test_fmp_economic_calendar_freshness` against real production staleness — by-design red per P26, this commit adds observability not entitlement repair. The underlying FMP 402 is a vendor/plan decision pending Mark's account review. 1 skipped (fmp_price_targets empty).

### Afternoon strategy session (Athena chat, no code)

Beta feedback from Guy (friend, casual amateur trader, Trading212 pie-copier) triggered a 90-minute strategy session. 5 feedback points raised: (1) product feels bewildering / too much terminology; (2) markets page chart timespans unlabelled; (3) no LSE; (4) global search suggestions clipped; (5) /backtest page purpose unclear. Plus volunteered context: pulling out of stocks short-term due to Trump volatility.

Decisions locked (full content lives in PROJECT_CONTEXT after this update):

1. **New Phase 3 added**: LSE + HK markets, Lite ticker page + Lite dashboard + profile toggle (Lite default for new signups, Power view for current users), /learn hub with 10 modules, YouTube companion series (10 × 30min). Driver: tagline "institutional trading tools for non-institutional traders" only earns its keep if the surface is accessible to non-power-users. Existing Phase 3 renumbers to Phase 4, existing Phase 4 to Phase 5.
2. **New Phase 2c identified**: Multi-user notifications substrate. Current Telegram alerts fire only to Mark's chat_id (system-level secrets). Per-user Telegram linking flow + per-user alert routing + SendGrid email alerts bundled into one coherent notifications phase. Hard blocker for paywall — can't charge users for alerts they don't receive.
3. **LSE + HK must land before paywall.** Brand sits behind a UK Ltd; can't reasonably charge UK users for US-only product. Substrate work non-trivial: different ticker conventions, fundamentals sources, market hours, sector taxonomies. Yahoo covers globally which helps; FinViz substitute for UK/HK fundamentals is the open question.

Decisions deferred:

- **Pricing.** Don't ask Guy what he'd pay yet. Three reasons: answer is worthless without him seeing the completed product (anchored on current bewildering surface), shifts beta-test relationship into sales mode at wrong moment, real pricing signal comes from specific question ("would you pay £X?") asked of several beta testers post-Phase 3. Right pricing windows: pre-launch survey of 10-15 testers with specific number, or Van Westendorp 4-question survey if cohort grows to 30+. Park as Phase 3 / pre-paywall problem.

Completeness audit: SignalIntel is ~40% complete. Time-to-paid-launch estimate 4-6 months at current pace. Phase 1 substrate ~85%, Phase 2 paywall 0%, Phase 2c notifications 0% (~2-3 weeks), Phase 3 LSE/HK/Lite/Learn 0% (6-10 weeks core + 30-50 hrs video production), Phase 4 and 5 at 0%.

### Afternoon design session (mockup pass, locked)

Marketing homepage hero + above-fold mockup banked. Aesthetic direction: Hybrid C palette (navy hero, off-white below-fold). Two-tier nav: Signal Vault parent utility bar + SignalIntel primary nav. Hero composition asymmetric — headline left, live 9-component radar scorecard right with three floating data chips (rating change, insider cluster, Piotroski F-score). Type system: Fraunces serif display + Inter Tight body + JetBrains Mono stats. Green-to-gold gradient on the "No institution" headline accent ties product brand to parent brand. Static HTML/CSS, ~885 lines, lives at `docs/mockups/marketing_homepage_hero_v3.html`.

### Brand asset refresh

The 17 May logo PNGs are superseded. New unified vault-wheel family system locked: SignalIntel (green bar chart), Signal Vault (gold V/arrow), SignalCrypto (purple C), SignalForex (teal W), SignalCommodities (orange flame), SignalBonds (blue column). All products share concentric ring structure with product-specific centre glyph + colour. Old PNGs (`SignalIntel Logo Brand.PNG`, `The Signal Vault Logos.PNG`) deleted. New `The_Signal_Vault_Brand_Map.png` committed to `docs/brand/`. PROJECT_CONTEXT Section 4 palette corrected from teal/cyan to green-primary.

---

## CURRENT STATE (end of 18 May 2026)

- gunicorn: PID 55935 under io.thesignalvault.gunicorn LaunchAgent (unchanged from 17 May P13 restart)
- scheduler: PID 86234 under io.thesignalvault.scheduler LaunchAgent (restarted today 11:33 BST onto v0.13.0 + entitlement observability code)
- HEAD on origin/main: 9558e6a (test(fmp): cover entitlement error escalation + Telegram dedup) — push tonight's doc-and-asset commits when ready
- 0 commits ahead of remote for the FMP entitlement work (already pushed)
- 4 commits ahead of remote pending push (this session): brand assets, mockup, PROJECT_CONTEXT update, HANDOFF update
- pytest: 247 passing, 1 failed (test_fmp_economic_calendar_freshness — real production staleness), 1 skipped (fmp_price_targets empty)
- SCORING_ENGINE_VERSION: 0.13.0 (unchanged)
- Yahoo enrichment tables: analyst_changes + earnings_history continue daily feed; financial_statements bulk job running today, 3.5M rows / 4,703 distinct tickers populated as of 07:56 BST; institutional_holders + earnings_history bulk pending Tue/Wed
- economic_calendar: still 11 days stale at last scrape, but now under observability — next 06:30 BST fire (Tuesday) will write FAILED to run_log + fire Telegram alert if 402 persists; SUCCESS to run_log if entitlement restored
- Site live: HTTP/2 302 via Cloudflare → /login
- venv.OLD: 72h timer elapsed today, safe to delete
- trading-system.OLD: already emptied from Trash (610 MB recovered)

---

## PROCESS TELLS — 18 May 2026

- **402 observability fix sequence ran clean Phase 1 + Phase 2.** Phase 1 inventory identified the three-layer swallow chain (_get → fetch → refresh → job handler) and proposed the FMPEntitlementError-mirrors-FMPRateLimitError shape. Decision lock collapsed six open questions to locked answers in a single exchange. Phase 2 implemented to spec with one Gate 5 condensation hiccup (CC summarised the test file paste instead of pasting) — caught via the diagnostic gap-closure prompt pattern from 14 May. Resolved before commit.
- **Gate 4 paste appeared to show broken Python syntax (orphan `log_run(...` lines without closing parens, `except` immediately following). Diagnostic prompt confirmed source on disk was intact — chat client rendering had truncated continuation lines.** Lesson: when paste output looks structurally impossible (orphan calls, missing parens), re-elicit via `sed -n` or `cat` before alarming. Symmetric with the 14 May "Diagnose before alarming" lesson — applies to render artefacts as well as git status surprises.
- **Athena's first reflex on Guy's bewilderment was to frame him as "outside the target user."** Mark pushed back correctly. The product tagline explicitly promises to serve non-institutional traders; dismissing a non-institutional trader's confusion is a positioning failure, not a user-fit observation. Lesson: when a beta tester's struggle is in tension with what the tagline promises, the tagline is the audit target. Logged as P27.
- **Pricing instinct was right — declined to give Guy a "what would you pay" question on demand.** Three concrete reasons given (anchoring on current surface, beta→sales tone shift, methodology fit). Specific later-stage methodologies queued (specific-price-test of 10-15 testers, or Van Westendorp if 30+). Pattern worth keeping: when asked to act on something where the answer is unreliable, decline + redirect to the right question at the right time + name the methodology.
- **Brand-asset mid-session refresh handled cleanly.** v2 mockup locked, brand assets refreshed underneath, v3 mockup rebuilt in ~20 minutes (palette sweep + SVG mark swap + wordmark restyle). Lesson: skin-changes on a locked composition are cheap when the composition decisions are isolated from the colour decisions in the first place. CSS variables + isolated SVG marks earned their architecture here.
- **Frontend-design skill produced an artifact directly in chat rather than handing to CC.** Mark and Athena reviewed inline, locked v3, then prepared a single banking prompt for CC to commit the artifact alongside brand and doc changes. Pattern: design-first → review-in-chat → CC commits the file. CC never touched the mockup HTML, only banked it.
- **Doc consolidation timing decision.** Two parallel sessions (implementation + strategy + design) produced enough decisions that targeted str_replace edits to PROJECT_CONTEXT carried real risk of conflict. Athena drafted full rewrites of both HANDOFF (full) and targeted PROJECT_CONTEXT insertions (Phase 2c block, Phase 3 block + renumbering, Section 4 palette correction, 2 new process lessons, P27 invariant). Single banking prompt fires all changes atomically.

---

## STILL OPEN

### Tuesday 19 May (while Mark away)

- **economic_calendar 06:30 BST cron — observation.** First fire under new observability. If green: 11-day staleness self-resolved, FMP entitlement restored. If red: Telegram alert + run_log FAILED row written, audit trail intact, decision queued for Mark's return on FMP plan tier.
- **fmp_earnings 06:05 BST cron — observation.** First fire under new observability. Same pattern: SUCCESS or FAILED row, alert if entitlement broken.
- **institutional_holders bulk job (Sunday → Monday overnight run).** Already partially populated per 18 May query. Will continue accumulating.
- **earnings_history bulk job (Tuesday overnight).** Verify Wednesday morning that the bulk job has populated rows. Check `external_scrape_log` for EARNINGS entries dated 2026-05-20 and `SELECT COUNT(*) FROM earnings_history`.

### Wednesday 20 May (while Mark away)

- **fmp_dividends weekly cron is Sunday 03:00 BST**, so not relevant this week — next fire 25 May.
- **No active monitoring needed.** All observability is now passive (run_log writes + Telegram alerts on failure).

### Thursday 21 May (Mark returns)

- **FMP plan tier decision.** Based on Tuesday + Wednesday cron outcomes, decide: (a) upgrade FMP plan to restore /economic-calendar entitlement, (b) swap economic_calendar to alternative source, (c) drop the economic_calendar feature. The 402 detector now buys observability without enforcing a decision.
- **Altman Z distribution check.** financial_statements bulk job populated 3.5M rows today; the queued URGENT FOLLOWUP from 14 May is now actionable. Compute Z-scores for production tickers with 2+ years data, plot distribution, verify -10 / -60 penalty tier calibration before v0.13.0 backtest data accumulates meaningfully. Phase 1 audit already banked from 17 May session.
- **Marketing homepage Section 2 mockup pass.** Locked aesthetic from Section 1 (this session). Section 2 is the Transparency / "We show our work" differentiator section. Aesthetic flips from dark hero to light Public.com territory. Frontend-design produces, review inline, lock.
- **venv.OLD deletion.** 72h elapsed Monday afternoon, safe to delete any time Thursday.

### Queued (no fixed date)

- **HANDOFF self-edit discipline.** P24 holds. Both docs updated only via explicit Mark-or-Athena-initiated CC prompts.
- **Mark replied to Guy** covering all 5 feedback points + 5 beta-test asks + coffee invite. Awaiting Guy's response. Beta-tester correspondence will feed Phase 3 design decisions.

---

## NOTES FOR FRESH-CHAT ATHENA (THURSDAY 21 MAY)

- Read PROJECT_CONTEXT.md first (stable), then this HANDOFF. PROJECT_CONTEXT was updated 18 May with: Phase 2c notifications block, Phase 3 LSE/HK + Lite + Learn block, Phase 4 + 5 renumbering, Section 4 palette correction (green-primary, not teal), four new process lessons (positioning-not-user-fit, pricing-question-timing, frontend-design workflow, render-artefact diagnostic), and new invariant P27.
- Two days of Yahoo + FMP cron observation logs will be waiting. First action: query run_log for Tue + Wed entries on fmp_earnings, economic_calendar, fmp_dividends. Check Telegram alerts received during the window. This empirically validates the 18 May entitlement observability work.
- Marketing homepage hero mockup v3 is locked. Lives at `docs/mockups/marketing_homepage_hero_v3.html`. Brand assets at `docs/brand/The_Signal_Vault_Brand_Map.png` are canonical. Next design work: Section 2 mockup pass (Transparency differentiator, "We show our work" headline). Aesthetic flips from dark hero to light below-fold per Hybrid C lock.
- Phase 3 is now the largest pre-paywall workstream. LSE + HK + Lite + Learn + YouTube. 6-10 weeks core engineering + 30-50 hours video production. Phase 2c (notifications) sits between Yahoo completion and Phase 3 start.
- Altman Z distribution check is now data-ready (3.5M financial_statements rows landed today). Highest-leverage analytical work available; should fire before deeper v0.13.0 backtest analysis begins.

---

*End handoff.*
