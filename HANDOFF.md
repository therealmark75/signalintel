# SIGNALINTEL: HANDOFF

**Tactical session state.** Updated end of each session. For stable
project context (who/what/how), see `PROJECT_CONTEXT.md`.

Last updated: 17 May 2026, end of session (six commits to origin/main across morning push + P13 fix, design brief locked across four sections in the afternoon, brand assets committed, trading-system.OLD moved to Trash).
Next session: Monday 18 May overnight bulk-job verification (Altman Z analysis now actionable once financial_statements lands) + economic_calendar 06:30 BST cron observation. FRESH CHAT recommended.

---

## JUST SHIPPED — 17 May 2026

### Morning push: six commits, all pushed to origin/main

- **48db573** — test(snapshot): pin datetime.now() to 2026-05-16 for insider window stability (Phase 2A). FakeDatetime subclass monkeypatch on signals.scorer.datetime, pinned to 2026-05-16 12:00 UTC. Eliminates the 2026-05-28 time-bomb where SS07's trade window would have expired and the snapshot test would have gone red on a clock-driven schedule. No new dependency. Locked pin date corrected from the original 2026-05-14 spec after empirical sweep showed the EXPECTED_SNAPSHOT was calibrated against a 2026-05-15..19 band.
- **b4826b0** — test(snapshot): add inst_own coverage for SS07 to close P21 gap (Phase 2B). Added `{"total_pct_held": 15.0, "holder_count": 8, "filing_date": "2026-02-15"}` for SS07. Drives `score_inst_ownership` into the `pct <= 20 → 35.0` weak-institutional-ownership branch. Composite delta is absorbed by the existing -60 Altman clamp, so SS07 stays at composite_score_raw 0.0 and rating STRONG_SELL; the new non-neutral score is asserted via a sixth field `inst_own_score: 35.0` on the SS07 row of EXPECTED_SNAPSHOT.
- **9376f81** — test(integrity): add schema-coupling tripwire test for insert_screener_rows (Phase 2C / Item 3). `test_insert_screener_rows_schema_alignment` builds a tmp_path SQLite file via production `initialise_schema()`, calls `insert_screener_rows()` with a minimal valid row, asserts insert returns 1. BUG B class catcher: INSERT statements referencing columns the schema no longer has, or NOT NULL columns the dict doesn't populate. Scope is screener_snapshots only; broader sweep across the 7 other insert helpers queued as STRUCTURAL DEBT.
- **a25e39d** — test(integrity): add FMP output table freshness tests, 4 new (Phase 2C / Item 4). Four tests: `test_fmp_earnings_calendar_freshness` (last_updated, 72h), `test_fmp_dividends_freshness` (last_updated, 14d), `test_fmp_price_targets_freshness` (last_updated, 14d), `test_fmp_economic_calendar_freshness` (scraped_at, 72h — economic_calendar uses scraped_at not last_updated; defined in database/db.py not scrapers/fmp_scraper.py). All four use the existing conditional-skip pattern matching test_yahoo_*_freshness. Caught real production staleness on first run, see below.
- **cd14074** — fix(api): translate rating codes to display labels in ticker events feed (P13). One-line fix in `web/app.py:1530` replacing `(r['old_rating'] or '?').replace('_',' ')` with `tier_short()` calls from `signals.signal_labels`. NULL-aware branching: first-ever rating reads "Rating set: Stable" instead of "Rating changed: ? → STRONG HOLD". Regression test added in `tests/test_api_rating_display.py` covering both branches. Gunicorn reloaded at 10:59 BST via `launchctl kickstart -k gui/501/io.thesignalvault.gunicorn` (PID flip 30323 → 55935), browser walk on https://thesignalvault.io/ticker/LESL confirmed labels render correctly.
- **67278de** — docs: add Signal Vault + SignalIntel brand assets. Two PNG logo files committed to docs/brand/ (4.2 MB total). Locks the brand asset reference for the design brief.

### Test count

234 → 239 passing (5 new tests added across Phase 2 commits, 0 regressions). 1 failed: `test_fmp_economic_calendar_freshness` against real production staleness, see below. 3 skipped (financial_statements + institutional_holders + fmp_price_targets — pre-existing conditional skips on empty tables).

### Three Phase 1 audits banked (read-only, feeding future implementation sessions)

- **Altman Z-score distribution analysis prep** — Phase 1 inventory laid out compute_z_raw() helper extraction approach. Actionable once financial_statements bulk job lands Monday 18 May overnight.
- **Scraper substrate audit** — Class A dominance pattern identified: FinViz Custom view fragility is a substrate problem, not individual scraper bugs. Inventory of recurring failure modes banked for a future hardening session.
- **P21 snapshot coverage backfill audit** — surfaced 4 items, all 4 closed in this session's Phase 2 commits (inst_own gap closed in 2B; insider time-decay locked via pin date in 2A; schema-coupling tripwire in 2C/Item 3; FMP freshness coverage in 2C/Item 4).

### Real production bug surfaced by the new test

`test_fmp_economic_calendar_freshness` fires red on first run. economic_calendar has no rows since 2026-05-07 (9 days stale as of session close, vs the daily mon-fri cadence). Caught immediately by the freshness test the same day it was added. Read-only diagnostic was performed (run_log has no entries for `job_economic_calendar`, external_scrape_log has no economic entries, distribution shows only two days of data ever recorded). Root cause not investigated this session — observation-only. Test left red on origin/main by design (per the new P26 invariant). See STILL OPEN.

### Afternoon work: design brief locked across four sections

Full content captured in PROJECT_CONTEXT.md under DESIGN BRIEF (LOCKED 17 MAY 2026). Summary:

- **Section 1: Site Map** — post-restructure 7 top-nav items (Dashboard / Signals / Screener / Markets / Events / Watchlist / Penny) + footer reference (Methodology / About / Contact / Privacy / Terms / Risk Disclaimer / Sign Out) + admin-only /system. /earnings and /dividends demoted to Dashboard panel CTAs. /ratings renamed to /methodology with tabs (Definitions / Score Components / Backtest / Distribution); /backtest folded in as a tab. Marketing homepage now lives at / for logged-out visitors.
- **Section 2: Dashboard Panel Specs** — 13 panel specs locked. Above-the-fold 3×2 grid (Daily Summary, Top 5 Strong Signals, Top 5 Bearish Signals, Market State, Watchlist Preview, Discovery Themes Preview). Elite-only spotlight (Penny Stock of the Day full-width). Below-the-fold 3×2 (Earnings 7d, Dividends This Week, Sector Performance, Recent Rating Changes, Insider Activity, News Headlines). Each panel has documented data sources, content rows, interactions, and CTAs.
- **Section 3: Marketing Homepage Spec** — 8 sections locked, Public.com / Robinhood aesthetic. Hero ("Institutional-grade tools. No institution required."), Transparency (lead differentiator), Multi-factor analysis, Discovery themes, Live proof stats, Pricing (Beta-marked Option B), Final CTA, Footer.
- **Section 4: Brand System** — Parent brand: The Signal Vault (navy + gold, Trajan serif, vault wheel mark). Product brand: SignalIntel (teal/cyan + gold, hexagonal cube + V mark). Family system: SignalCrypto / SignalForex / SignalCommodities extend same template. Logged-in app palette refinement: Option C — preserve monospace + dark, swap cyan accent → SignalIntel teal-gold gradient, refine chart palette to brand colours. Not a full rebrand, palette alignment only.

### Brand assets committed (commit 67278de)

`docs/brand/SignalIntel Logo Brand.PNG` and `docs/brand/The Signal Vault Logos.PNG` (4.2 MB total). Locked brand references for the design brief.

### Trading-system.OLD cleanup

Verified via 6-gate read-only audit: tip commit `bd31b99` propagated to origin/main, no orphaned commits, no symlinks pointing into the old folder, remote unrelated to local path. One untracked `.claude/settings.local.json` (183 bytes, 5 permission rules) declared redundant under the global bypassPermissions mode. Moved to ~/.Trash/ via `mv` (not `rm -rf`). 610 MB recoverable until Trash empty. Verified Trash presence via `test -d` and `stat` (TCC blocks `ls ~/.Trash`).

---

## CURRENT STATE (end of 17 May 2026)

- gunicorn: PID 55935 under io.thesignalvault.gunicorn LaunchAgent (restarted today 10:59 BST to pick up P13 fix; PID flip 30323 → 55935)
- scheduler: PID 32257 under io.thesignalvault.scheduler LaunchAgent (unchanged since 15 May)
- HEAD: 67278de — docs: add Signal Vault + SignalIntel brand assets (will move to the doc-banking commit after this session's edits)
- 0 commits ahead of remote: all six morning commits pushed to origin/main; brand-assets commit (67278de) and doc-banking commit (to land at end of this prompt) are local-only until Mark confirms push
- pytest: 239 passing, 1 failed (test_fmp_economic_calendar_freshness — real production staleness, by-design red), 3 skipped (financial_statements + institutional_holders + fmp_price_targets, pre-existing empty-table conditional skips)
- SCORING_ENGINE_VERSION: 0.13.0 (unchanged)
- Yahoo enrichment tables: analyst_changes + earnings_history continue daily feed; institutional_holders / financial_statements / earnings_history bulk still empty pending Mon/Tue runs
- economic_calendar: 9 days stale (last scraped 2026-05-07), red test surfaced this; root cause not investigated
- Site live: HTTP/2 302 via Cloudflare → /login; P13 ticker events fix verified empirically on /ticker/LESL
- trading-system.OLD: moved to ~/.Trash/ (610 MB recoverable until emptied), confirmed via test -d + stat
- venv.OLD: still untracked in ~/signalintel/venv.OLD (out of scope for the 15 May 72h timer, can fire any time from Mon 18 May)

---

## PROCESS TELLS — 15 May 2026

- **Phase 1 + Phase 1-follow-up sequence on Yahoo verification.** Two short read-only diagnostic rounds beat one large one. First round confirmed crons fired and produced data, surfaced two open questions (yahooquery_raw, last_error_at). Follow-up grep round closed both empirically in 2 minutes. Cleaner than batching into a single multi-part prompt with branching gates.

- **P16 absolutism on SB01.** The snapshot recorded 76.6 with a "Do NOT modify — fix the refactor instead" comment. The arithmetic said 74.7. Trusting the arithmetic (not the comment, not the recorded baseline) was the right call. Future-Athena: comments asserting a value is correct do not make the value correct.

- **ExitTimeOut: 90 explicit note in HANDOFF.** Without this, future-Athena sees the number, doesn't know why it's not the launchd default 20s, and may second-guess. The line "ExitTimeOut: 90 lets scheduler.shutdown(wait=True) complete a worst-case ~50s signal generation cleanly" is the rationale, and the rationale belongs in HANDOFF, not in the plist as a comment (launchctl is picky about plist XML).

- **Venv rebuild Phase 1 inventory found zero project-code contamination.** Confirmed empirically before touching anything. Without that sweep we'd have been guessing whether a full rebuild was sufficient or whether other project-side path references needed cleanup. Phase 1 read-only diagnostics earn their weight on any environmental change with potential for hidden references.

- **CC discipline held cleanly across the day.** No scope drift, no negative-instruction failures, no doc edits. The venv rebuild (12-step Phase 2) and scheduler LaunchAgent install (8-step Phase 2) both ran end-to-end without stops. STOP-on-broken-venv at Gate 2 of the SB01 prompt was correctly observed (CC did the edit, hit the broken venv, stopped, reported — did not try to fix the venv mid-prompt).

- **Pre-existing CC plugin terminal noise.** Throughout the day every Bash tool call surfaced "Failed with non-blocking status code: /bin/sh: node: command not found" and "Bun not found" warnings. These are pre-tool / post-tool hook errors from the Superpowers plugin that was installed but not enabled in the project. Non-blocking, no functional impact, ignorable. Worth knowing about so future sessions don't waste time investigating.

- **Mid-session terminal-window confusion (caught early).** A paste from a different project (Betfair / greyhound stats) landed in the SignalIntel chat. Caught and discarded before any action. Adds nothing to process — just a reminder that the multi-terminal workflow has the risk surface of "right command, wrong window." Athena response should always be to demand a `pwd` + `git remote -v` confirmation before touching anything if the output looks unfamiliar.

---

## STILL OPEN

### Monday 18 May verification

- **financial_statements bulk job.** Verify `sqlite3 data/trading_system.db "SELECT COUNT(*) FROM financial_statements;"` returns nonzero overnight Sun→Mon. Once that lands, the **Altman Z distribution analysis** from URGENT FOLLOWUPS is actionable Tuesday morning (compute Z-scores for tickers with 2+ years of data, plot distribution, verify -10 / -60 penalty tiers calibrated for the production universe before v0.13.0 backtest data accumulates).
- **economic_calendar 06:30 BST cron — observation window.** The scheduled run will or will not produce a fresh row Monday morning. If green, the 9-day staleness was a transient failure that has already self-resolved. If red, fresh empirical logs are available to diagnose against (vs the current 8-day-old fog).
- **venv.OLD deletion (72h timer from 15 May).** Eligible for deletion any time from Monday 18 May onwards.

### LAUNCH PREP (new bucket)

- **Google Search Console indexing setup at site launch.** sitemap.xml, robots.txt, domain verification. Required before marketing homepage goes public.
- **Open Graph / social preview meta tags on marketing homepage.** og:title, og:description, og:image. Needed for social link previews to render coherently.
- **Analytics decision: Plausible / Fathom / GA4.** Decision shape: a privacy-friendly analytics provider (Plausible / Fathom) fits the transparency-first brand positioning locked in Section 3 of the design brief. GA4 is the conventional default but conflicts with the "we show our work" stance. Decision needed before public launch.

---

## NOTES FOR FRESH-CHAT ATHENA

- Read PROJECT_CONTEXT.md first (stable), then this HANDOFF.
- Today's three substantive pieces of work: Yahoo verification (read-only, no commits), SB01 snapshot fix (commit 0290c10 pushed), venv rebuild (environment-only, no commits), scheduler LaunchAgent (system config, no commits).
- Both gunicorn and scheduler are now reboot-resilient under LaunchAgents. The Mac Mini can reboot and the platform self-heals.
- If continuing on Sunday: first action is the institutional_holders bulk-job verification query in STILL OPEN above. Run before anything else to bank or surface that result.
- If continuing on Monday: same pattern, plus the Altman Z distribution check is now actionable (it was queued from 14 May and gated on financial_statements data).
- The Superpowers plugin is installed in CC but not enabled. Athena flagged it as a candidate for Phase 2c implementation work or for the Altman Z distribution analysis. Re-evaluate when one of those sessions starts.
- venv.OLD still on disk. Don't delete without 72h+ confidence interval on the new venv.

---

*End handoff.*
