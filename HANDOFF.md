# SignalIntel Session Handoff

**Last updated:** end of Part 50 (26 June 2026)
**Engine:** SCORING_ENGINE_VERSION 0.19.0, UNCHANGED this session (Part 50 is analytics only, no scoring path touched; P18 did not trigger).
**Repo:** `main` advanced to `9c697fd` via a `--no-ff` merge of `feature/car-event-study` (Part 50), pushed, level with origin. The merge sits above `88593c8` and `b382175`, with `5bb81b3` (Part 49) beneath. The branch carried two commits: `b382175` (CAR harness) and `88593c8` (decile stratification).
**Suite:** 469 passed, 0 unexpected skips, exit 0.
**Runtime:** no runtime change this session (analytics modules, not loaded by any long-lived process). No gunicorn or scheduler restart required or performed. PIDs differ next session.

## Part 50 work (this session)

| Item | Commits | What shipped |
|---|---|---|
| 1. CAR event-study in-sourced | `b382175` | new `signals/event_study.py`. Analyst-PT events from `analyst_changes` grouped Raises/Maintains/Lowers, per-event 21-trading-day CAR against a computed per-sector per-day benchmark from `screener_snapshots` (source B), reuses `guarded_forward_return` per grid step, mirrors the IC-harness LOW_CONFIDENCE vocabulary. Matured-events-only, grid-clean per-ticker >=21 forward depth, min-constituent floor 5 (armed, did not bite this run). Lower-bound OUT_OF_SUBSTRATE and upper-bound future-date guards added beyond spec. Monotonic ordering replicated the external 25 May study on our own substrate: Raises +2.56% > Maintains +1.06% > Lowers -0.11%, PASS. 6 tests. |
| 2. Magnitude decile stratification | `88593c8` | new `signals/event_study_strata.py`. Deciles the matured OK cohort by signed PT percent-change (current vs prior target), pooled across actions, reusing `compute_event_car` verbatim. Magnitude-monotonic by RANK: Spearman rho(decile, CAR) 0.92 headline, 0.88 zero-bucket variant; 7 of 9 steps rise; 8.1pp spread (bottom decile -0.61% to top +7.53%). Two trivial middle-decile inversions (D2-D3, D6-D7) fail STRICT adjacency but do not dent the gradient; the honest characterisation is monotone-by-rank, not "monotone NO". Tie-robust (zero-bucket cut agrees, Maintains zero bucket +1.10% neutral midpoint). Label-vs-sign audit clean: 1 contradiction in 8,175 rows, genuine not artefact. Extracted `prepare_substrate` in `event_study.py` (behavior-preserving, headline aggregates byte-identical to `b382175`). 6 tests. |

## Part 49 work (prior session)

| Item | Commits | What shipped |
|---|---|---|
| 1. Corporate-action straddle guard | `6dcb8b6` | fix(backtester): same-day intraday-ratio guard (MAX/MIN > 2.0) plus cross-day overnight-split guard (ratio breach 3.0 symmetric), both SKIP, routed through one contract. Penny winsorization was investigated FIRST and rejected (penny names 2.08% of cohort, headline aggregates move <=0.07pp; the real distortion was corporate-action artefacts, not the penny band). Three KLAC split artefacts retired: N=1 worst -89.26 to -33.04, N=5 worst -88.95 to -43.0. Engine unchanged. 5 tests. |
| 2. Per-component IC harness (Item 2 Part 1) | `0154003` | feat(validation): new signals/validation.py. Canonical validation surface LOCKED as the screener-snapshot fixed-N backtester path (NOT the rating_changes web path). Straddle guard unified into one guarded_forward_return contract that both backtester and validation inherit (cross-day guard relocated from the backtester loop into the shared contract; backtester aggregates byte-identical to 6dcb8b6). Spearman IC at N=1/N=5 over 12 components plus composite, every result carries N and a LOW_CONFIDENCE flag. Engine unchanged. 6 tests. |

## Part 48 work (prior session)

Two-arc cleanup session (janitorial A-D + registry reconciliation), engine unchanged at 0.19.0.

| Item | Commits | What shipped |
|---|---|---|
| 1. Mid-cycle skip-guard | `ab181b5` | test: scoring_run_complete fixture, skips four content gates during mid-cycle scoring window (watermark sentinel, 90-min recency bound) |
| 2. app.logger NameError fix | `fb1ea76` | fix: app.logger on backtest-stats error path (was undefined logger, latent NameError) |
| 3. markets_scraper dash fix | `d620e84` | chore: em-dash to comma in markets_scraper log string |
| 4. Doc cleanup | `4cc6f50` | docs: P1-P32 citation fix, P16 sync into scoring_invariants.md, dash sweep, HANDOFF refresh |
| 5. Registry reconciliation | `c6b6e3a` | docs: registry reconciliation (PROJECT_CONTEXT.md is canonical P1-P32 registry; scoring_invariants.md reframed as partial rationale; stale Part 47 FOLLOWUP retired) |

## Part 47 work (prior session)

Shipped the Values screen: an exclusion screener-preset (new `exclude_ethical` param on `/api/screener` plus a sidebar toggle) excluding 10 industry strings across 4 categories (tobacco, gambling, alcohol, fossil-fuel extraction), exact-match against `screener_snapshots.industry`, no scoring change, commit `ee21fbd`. Live-verified: 10,940 results unfiltered to 10,768 filtered.

## Part 46 work (prior session)

| Item | Commits | What shipped |
|---|---|---|
| 1. Backtester rewire | `0c92d6d` | Backtester rewired to persisted screener prices, version-segmented, short-horizon only. Retired the live-yfinance fetch path; forward prices now from `screener_snapshots.price` (intraday spot, N=1/N=5 directional only, not corporate-action adjusted). Horizons [1,5], N=20 removed. Runs scoped to one scoring_version cohort; `backtest_results` / `backtest_trades` gained an idempotent scoring_version column. First persisted cohort baseline v0.17.0 BUY full pool: N=1 win 52.3 pct avg +0.21 pct, N=5 win 49.2 pct avg flat. 7 tests. |
| 2. Sitewide design-system migration | `d29ab30`, `1c16997`, `a26225d` (plus prior `1e9439b` "web design" that committed the Phase 2 partials) | Promoted the new nav into the shared `_nav.html` partial; utility strip (The Signal Vault / Commodities / Crypto / Forex / Account) folded into the partial so it renders sitewide, with the three product links inert/coming-soon and Account inert (no routes exist yet). Dropped the Signals nav link (routed to dashboard, redundant with Screener); five-link nav. Green hexagon logo canonical. Migrated industry.html and ticker_news.html off bespoke headers onto the shared partial, preserving their back-links and adding the footer. 17 pages auto-migrated via the partial; 20 pages now include the shared nav. |
| 3. Nav-contract test updates + em-dash sweep | `cbbda9c` | Four stale nav tests retargeted to the new contract (nav-tier to tier-pill, FREE to Free casing, Signal-Tiers link asserted via footer); full em-dash sweep of tests/test_smoke.py and tests/test_signal_labels.py. BUG-001 and P15 security assertions byte-identical, only message/docstring text changed. |
| 4. Market State NULL-close fix | writer `4c83bd6`, reader `00e3ce6` | Root cause: the 07:00 BST markets job runs pre-US-close, yfinance returns a forming bar with NaN close, persisted as a NULL-close row; the dashboard reader took the latest row by date and blanked the S&P/NASDAQ/DOW tiles. Writer now skips NULL-close bars; reader query adds `AND close IS NOT NULL`. Tiles populate. 4 tests. |
| 5. Market State chart-link fix | `f420a38` | Tiles linked `/markets/<yf-symbol>` (`^GSPC`), which the TradingView widget rejects. Now resolve the tv symbol from `config.markets.MAJOR_INDICES` (single-source) and link with that, keeping yf for the data read; hardcoded VIX stat-line fixed to `CBOE:VIX`. 1 test. |

## Part 45 (prior session)

Part 45 (prior session): watchlist earnings job (`ab63a0d`) + economic_calendar full retirement (`3fe48bd`) + docs (`c811e51`), all now merged to main via the Part 46 close. See git history for detail.

## Queued work

1. **Backtest validation harness next steps.** The 0.17.0 composite/tier baseline is live; per-sub-score and N=20 harness blocked on accumulation, earliest ~late June when 0.17.0+ rows clear a 20-trading-day forward window. Run 0.18.0/0.19.0 cohorts once they have forward depth (noise today).
2. **FOLLOWUPS latent tail** (unchanged): ISO-date string-sort couplings (09/10/13), dead guard (09), 50.0 collision (10), init-as-upgrade (12), vestigial `total_revenue` in `ALTMAN_LOOKUPS` (13).
3. **Components 15/16 (News Sentiment, Options Flow)**, deferred, dashboard-only.
4. **Production Stripe flip** (P32), queued.
5. **Future Path B: per-subscriber earnings delivery** (needs `users.telegram_chat_id` plus bot linking, P23).
6. **Part 49 open question: negative component IC.** `sector_strength_score` and `composite_score` read NEGATIVE IC within the v0.17.0 BUY cohort (sector_strength t=-20 at N=5). One-month / 47-date restricted-range within-cohort window, NOT a scoring verdict. P29-gated: no reweight off this run. Re-examine on a fuller cross-version substrate when 0.18/0.19 forward depth clears.
7. **Part 49 carry: /backtest page reconciliation.** The web page computes returns live from `rating_changes` transition pairs, a DIFFERENT surface from the now-canonical screener-snapshot backtester. Reconcile so the page reads the canonical engine. Touches P23-protected `web/app.py`. Sequenced AFTER the harness core proves out.
8. **Part 49 carry: run_at accretion.** `backtest_results` / `backtest_trades` are append-only (`save_backtest_results` INSERTs). Resolved as leave-append-only; reads key by scoring_version plus MAX(run_at). No leak today (web `/api/backtest/stats` does not read these tables, only CLI `backtest.py --show` does, via MAX(run_at)). Purge of stale same-version runs is a later nicety.

## Part 46 new FOLLOWUPS (banked, not urgent)

- **test_data_integrity.py content tests have no mid-scoring-cycle guard:** any pytest run roughly 14:00-15:20 BST shows phantom failures because the content gates snapshot a half-written scoring run. Skip-guard when `latest_run_date` scoring is incomplete. (Surfaced at Part 46 open when a 15:23 run showed 2 false failures.) [RESOLVED Part 48: scoring_run_complete fixture]
- **markets_scraper.py line ~100 carries a pre-existing em-dash** in a log string (the `Scrape complete` line). One-character dash-sweep when convenient. [RESOLVED Part 48]
- **app.py ~line 2744 references a `logger` not defined at module scope:** latent NameError on the backtest-stats error path. Pre-existing, not triggered normally. [RESOLVED Part 48: app.logger fix]
- **Backtester penny-name spot-price tails:** unadjusted intraday spot on thin names produces noise outliers (e.g. a +95.9 pct one-day move). Consider a price-floor or winsorization filter before trusting tail stats; separate decision, own evidence. [RESOLVED Part 49 Item 1: winsorization investigated and rejected; penny band is 2.08% of cohort moving headline <=0.07pp, the real distortion was corporate-action straddle artefacts, fixed by the guard 6dcb8b6]
- **PRODUCT: Market State tiles link to TradingView's own chart widget** (third-party surface). Works for beta, but it sends the user off our surface and ties charting to a vendor. Revisit before paid launch (own charting vs embed).
- **PRE-BETA OPS: the running server currently serves a feature branch in production** (single-machine setup, Cloudflare tunnel to localhost:5001). Before testers land, make `main` the deployed branch so "what's live" has a clean answer (merge-then-restart as the deploy discipline). The Part 46 close merges the branch to main, which begins this. [SATISFIED: main is the deployed branch, live]
- **Eco/ethical screen page (product idea, post-beta):** a curated green/ethical universe (companies that do not harm environment/animals) analysed with the SAME SignalIntel scoring. Scope as a SCREENER-PRESET / filtered universe, NOT a scoring-component change (keep the composite defensible and free of contested moral judgments). The make-or-break is the ethical-data substrate (curated exclusion list vs public ESG dataset vs vendor scores vs SEC-filing signals), resolve that FIRST in a Phase 1 scope before any build. Potential USP: ethical universe + genuine signal intelligence, the intersection most ESG tools and most signal tools each miss.

## Part 47 new FOLLOWUPS (banked, not urgent)

- (none outstanding; the invariant-citation cleanup shipped in Part 48.)

## Part 48 new FOLLOWUPS (banked, not urgent)

- Penny-name winsorization in the backtester (tail outliers). Needs its own evidence and a real filter-design decision. See the Part 46 penny-name FOLLOWUP for the same ground. [RESOLVED Part 49 Item 1: rejected with evidence; real fix was the corporate-action straddle guard, not a penny filter]
- Eco follow-ons: curated list for defence / adult / predatory-lending exclusion categories; positive green-screen product. Parked.
- Optional: wholesale em/en-dash sweep of docs/scoring_invariants.md body (pre-existing dashes, harmless but inconsistent now its header is glyph-clean).

## Part 49 new FOLLOWUPS (banked, not urgent)

- CAR event-study module: in-source per Mark's call. Opens Part 50 Phase 1 to lock the benchmark source (sector_performance table vs computed sector-average from screener_snapshots). [RESOLVED Part 50: source B (computed sector-average from screener_snapshots) locked; CAR harness (b382175) and magnitude decile stratification (88593c8) both shipped.]
- Penny-winsorization FOLLOWUP (Parts 46/48) is now RESOLVED (Part 49 Item 1): investigated and rejected with evidence; the real distortion was corporate-action artefacts, fixed by the straddle guard.

## Part 50 new FOLLOWUPS (banked, not urgent)

- Emit Spearman rho per decile-cut directly from `signals/event_study_strata.py` output, so the headline rank statistic is self-documenting in the artifact rather than hand-derived at read time. Action when next in this module.

## Test accounts (for tier-gated walks)

- `markn` = elite
- `beta2` = pro
- `mark2` = free

## Operational notes (carry forward)

- **Branch discipline:** confirm `git branch --show-current` before any work. GitHub Desktop branch clicks have caused silent HEAD drifts before.
- **P23 hook:** `web/app.py` is path-matching (any touch trips the hook). The hook reads `[y/N]` from `/dev/tty`, so an auth-adjacent commit can only be confirmed from Mark's own terminal; from CC's non-interactive shell it exits 1 with "No controlling terminal". CC stages, surfaces the diff, and hands Mark the literal `git commit` to run himself. CC does not use `--no-verify` unless Mark explicitly authorises it. Docs-only and `database/db.py` / `signals/components.py` / `tests/` commits on auth-clean diffs pass the hook silently.
- **Hook Pass 0 (dash check):** the pre-commit hook rejects any ADDED line containing an em-dash (U+2014) or en-dash (U+2013) on ANY staged path, including docs. Keep added content glyph-clean or the commit blocks.
- **Runtime drift:** any `web/app.py` or scorer commit needs a gunicorn restart (`launchctl kickstart -k gui/$(id -u)/io.thesignalvault.gunicorn`); verify the master is launchd-managed (PPID 1) and owns 5001 post-restart. Assert "current PID stable AND no recent err.log entries", not the backward-looking launchd exit code.
- **Scheduler vs gunicorn are TWO separate launchd processes (not interchangeable).** The scheduler runs as `io.thesignalvault.scheduler` (launchd, `venv/bin/python main.py scheduler`), distinct from the gunicorn web worker (`io.thesignalvault.gunicorn`). Changes to scheduler jobs (daily summary, scrapers, scoring jobs, anything in `main.py`'s job functions) deploy via `launchctl kickstart -k gui/$(id -u)/io.thesignalvault.scheduler`; changes to web routes (`web/app.py`) deploy via the gunicorn kickstart. A gunicorn restart does NOT deploy a scheduler-job change and vice versa. Near-miss this session: the Telegram fix lives in a scheduler job, so a gunicorn restart would not have shipped it. Confirm a fresh PID with PPID 1 after either kickstart.
- **Registry-vs-reality audits** use the Step 5.5 carried-response lens (a column belongs on a surface if the API response carries it, not only if a cell renders it).

## Known pre-existing FOLLOWUPS (unchanged this session)

- Dormant `initialise_schema` gap (does not provision volume_score or scoring_version on fresh-DB init). P19-class fix when prioritised.
- PROJECT_CONTEXT.md dash sweep DONE (Part 48; only the AUTH-token exception remains). The remaining body-dash candidate is docs/scoring_invariants.md (banked Part 49).
- Orphan-gunicorn baseline check: assert "exactly one master with launchd-managed PPID chain bound to 5001", not "at least one gunicorn process".

## Working-style standing instruction (in effect from Part 42)

- Replies are prompts-only: when handing Mark something to run or paste, give the literal block with no surrounding narration of steps taken.
- Label every copy block as **CC-prompt** (paste into a Claude Code session) or **Terminal** (run in his own shell).
- Lead with the artifact or result; do not narrate the work step by step.

## Branch state (for the next fresh chat)

- Part 50 closed with `feature/car-event-study` merged to main (`9c697fd`, `--no-ff`), pushed to origin and level; local working tree, main, origin, and the live site (thesignalvault.io via the Cloudflare tunnel to localhost:5001) are the same state. There is no separate deploy step; a gunicorn restart on the latest code IS the live deploy (no restart needed this session, analytics only, no long-lived process loads the new modules). Suite floor 469 passed / 0 skipped.
