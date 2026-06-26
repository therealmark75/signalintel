# SignalIntel Session Handoff

**Last updated:** end of Part 47 (25 June 2026)
**Engine:** SCORING_ENGINE_VERSION 0.19.0, UNCHANGED this session (no scoring change in Part 47).
**Repo:** branch `feature/eco-screen`, one feature commit `ee21fbd` ahead of `main`, merging to `main` at this close.
**Suite:** 446 passed, 0 skipped, exit 0. Baseline correction: Part 46 closed reporting 441 passed / 1 skipped; at Part 47 open the suite read 442 passed / 0 skipped (the lone `fmp_price_targets` skip now has data and passes). After the Values screen build: 446 passed / 0 skipped.
**Runtime:** gunicorn restarted onto the committed feature this session, fresh pid 24056 (was 65239); scheduler untouched this session (still 61983), no scheduler-job change.

## Part 47 work (this session)

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
6. feature/eco-screen merged to main at Part 47 close (merge commit 4dbdbf5); main is live (no separate deploy step, deploy = gunicorn restart on main). Suite floor 446 passed / 0 skipped.

## Part 46 new FOLLOWUPS (banked, not urgent)

- **test_data_integrity.py content tests have no mid-scoring-cycle guard:** any pytest run roughly 14:00-15:20 BST shows phantom failures because the content gates snapshot a half-written scoring run. Skip-guard when `latest_run_date` scoring is incomplete. (Surfaced at Part 46 open when a 15:23 run showed 2 false failures.)
- **markets_scraper.py line ~100 carries a pre-existing em-dash** in a log string (the `Scrape complete` line). One-character dash-sweep when convenient.
- **app.py ~line 2744 references a `logger` not defined at module scope:** latent NameError on the backtest-stats error path. Pre-existing, not triggered normally.
- **Backtester penny-name spot-price tails:** unadjusted intraday spot on thin names produces noise outliers (e.g. a +95.9 pct one-day move). Consider a price-floor or winsorization filter before trusting tail stats; separate decision, own evidence.
- **PRODUCT: Market State tiles link to TradingView's own chart widget** (third-party surface). Works for beta, but it sends the user off our surface and ties charting to a vendor. Revisit before paid launch (own charting vs embed).
- **PRE-BETA OPS: the running server currently serves a feature branch in production** (single-machine setup, Cloudflare tunnel to localhost:5001). Before testers land, make `main` the deployed branch so "what's live" has a clean answer (merge-then-restart as the deploy discipline). The Part 46 close merges the branch to main, which begins this.
- **Eco/ethical screen page (product idea, post-beta):** a curated green/ethical universe (companies that do not harm environment/animals) analysed with the SAME SignalIntel scoring. Scope as a SCREENER-PRESET / filtered universe, NOT a scoring-component change (keep the composite defensible and free of contested moral judgments). The make-or-break is the ethical-data substrate (curated exclusion list vs public ESG dataset vs vendor scores vs SEC-filing signals), resolve that FIRST in a Phase 1 scope before any build. Potential USP: ethical universe + genuine signal intelligence, the intersection most ESG tools and most signal tools each miss.

## Part 47 new FOLLOWUPS (banked, not urgent)

- **Stale invariant-range citations in PROJECT_CONTEXT.md and CLAUDE.md.** Both still cite the old P1-P17 / P1-P15 invariant ranges and the Path A/B framing; `docs/scoring_invariants.md` (P1-P32) is the canonical, current list. Pre-beta doc-cleanup candidate, not done this session.

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
- PROJECT_CONTEXT.md still carries pre-existing em/en dashes; a full sweep is the tracked task (not done this session). The Piotroski and surfacing commits added only glyph-clean content.
- Orphan-gunicorn baseline check: assert "exactly one master with launchd-managed PPID chain bound to 5001", not "at least one gunicorn process".

## Working-style standing instruction (in effect from Part 42)

- Replies are prompts-only: when handing Mark something to run or paste, give the literal block with no surrounding narration of steps taken.
- Label every copy block as **CC-prompt** (paste into a Claude Code session) or **Terminal** (run in his own shell).
- Lead with the artifact or result; do not narrate the work step by step.

## Branch state (for the next fresh chat)

- Part 47 closes by merging feature/eco-screen into main (merge commit 4dbdbf5) and restarting gunicorn on main, so local working tree, main, and the live site (thesignalvault.io via the Cloudflare tunnel to localhost:5001) are the same state. There is no separate deploy step; a gunicorn restart on the latest code IS the live deploy. Suite floor 446 passed / 0 skipped.
