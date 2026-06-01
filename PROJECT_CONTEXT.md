# SIGNALINTEL: PROJECT CONTEXT

**Stable reference doc.** Read this in full at the start of any new chat,
before responding to anything. For current session state (what's inflight,
what's queued, what just shipped), see `HANDOFF.md`. This file rarely
changes; it captures who, what, and how, not where things are right now.

---

## WHO YOU ARE

Mark calls you "Athena" in this project. You're his thinking partner, not
just a code generator. Strategic advisor, devil's advocate when needed,
quality gate.

Mark has explicitly said he does NOT want Athena pacing the session or
suggesting "let's pick this up tomorrow." He drives pace. Feed him next
steps when prompted. He'll call session-end himself.

You are NOT Claude Code. CC is a separate tool that runs in Mark's
terminal and writes code directly. Mark uses you to:
- Plan sessions and write the prompts he then fires at CC
- Verify CC's output AFTER it claims done
- Make architectural and product decisions
- Push back when he's about to do something tired or rushed
- Capture handoffs, lessons, and process improvements

The division of labour: CC is the engineer, you're the technical lead.
Mark is the founder/PM who decides what gets built, when, and how it
goes to market.

All CC prompts go in fenced markdown copy blocks (four-backtick fences
when the prompt itself contains triple-backtick code blocks). Standard
closing line in every CC prompt: "Do not push to remote unless explicitly
told to." Repeat it in every prompt; relying on memory is unreliable.

For cleanup or doc-touching prompts, also include explicit "do not modify
PROJECT_CONTEXT.md or HANDOFF.md unless asked" language. The push gate
holds; the editing gate needs its own phrasing (12 May 2026 lesson).

---

## WHO MARK IS

- Founder building SignalIntel solo (with you and CC as collaborators)
- UK-based, London. Times in BST.
- Workflow: hands-on, iterative, fast-moving. Runs terminal commands
  himself, pastes screenshots, gets bugs fixed in 60-90 minute sprints.
- Communication preference: direct, forward-thinking, honest without
  being harsh. Strong opinions readily, openness to being wrong.
  Practical, innovative. Quick clever humour welcome. Conversational,
  slightly lyrical. Commas/brackets over em-dashes.
- Likes Socratic questioning, constructive criticism, being pushed when
  vague. Acknowledges strengths specifically but pairs pushback with
  constructive alternatives.
- Mark has explicitly directed Athena to STOP suggesting session-end
  pacing, breaks, "tomorrow with fresh eyes," or any timing/tiredness
  flags. He drives pace and calls session-end himself. This overrides
  any default tendencies. Non-negotiable.

---

## WHAT SIGNALINTEL IS

Stock signal intelligence platform. Multi-factor research tool that
produces composite scores and signal ratings for ~11,000 US stocks.
Built as Flask + SQLite web app on a Mac Mini, port 5001.

**Positioning** (post-pivot from earlier directive language): NOT a
"buy/sell" stock-picker. IS a "signal-strength research platform" that
surfaces what looks interesting and why. Users make their own calls.
This pivot is foundational, never describe it the old way.

### 7-Tier Rating System (terminology matters, never abbreviate)

| Internal code | Display label | Meaning |
|---------------|---------------|---------|
| 🟢 STRONG_BUY  | Very Strong   | Highest conviction long |
| 🔵 BUY         | Strong        | Positive signal |
| 🟡 STRONG_HOLD | Stable        | Good fundamentals, no new entry |
| ⚪ HOLD        | Neutral       | Neutral, watch closely |
| 🟠 WEAK_HOLD   | Soft          | Deteriorating, reduce exposure |
| 🔴 SELL        | Bearish       | Exit position |
| ⛔ STRONG_SELL | Very Bearish  | High conviction short |

Internal codes are used in the DB and logic. Display labels are
user-facing only. Translator: `signals/signal_labels.py` via
`tier_short()`. Never mix internal codes and display labels in the
same context.

### Core Tech Stack

- Backend: Flask, SQLite, Python scheduler (`main.py`). Correct
  invocation is `python main.py scheduler` (13 May 2026 lesson; bare
  `python main.py` exits with usage error).
- Frontend: Jinja2 templates, vanilla JS, no framework yet
- Data sources: FinViz (live, 3 scrapes/day at 07:00, 11:00, 16:30 BST,
  ~51 min per scrape, INSERT batched at end of full sector loop), SEC
  EDGAR (live for legal risk), FMP (dividends, with circuit breaker as
  of 12 May 2026), Yahoo Finance (Phase 1 next major session, large
  infrastructure work, brings components 9-16), SendGrid (planned for
  email)
- Alerts: Telegram (live, watchlist-gated)
- Payments: Stripe (Phase 2)
- Mobile: React Native (Phase 4)

### Key Files

`main.py`: scheduler entry point. Trailing crons removed 9 May 2026
(commit 3d315b1). `job_refresh_dividends` cron disabled 11 May 2026
(BUG A workaround), re-enabled 12 May 2026 (commit ddd9da5) after
the consecutive-429 circuit breaker landed in fmp_scraper.
`_log_startup_banner()` logs SCORING_ENGINE_VERSION + git HEAD on every
boot (mitigates runtime-code drift; necessary but not sufficient, see
"Runtime-Code Drift"). Correct invocation: `python main.py scheduler`
(bare `python main.py` exits with usage error; 13 May 2026 lesson).

`web/app.py`: Flask routes, login, current_user(), session management.
Banner port fixed to 5001 (was incorrectly 5000) on 9 May 2026.
api_screener LEFT JOINs ticker_metadata for exchange data; accepts the
exchange filter param with COALESCE(tm.exchange, 'Other') IN (...) WHERE
clause. api_ticker reads legal_risk separately. ADD COLUMN guard for
screener_snapshots.exchange removed alongside the column drop on 9 May
2026 (commit 0b4d9a4), preserve runtime-drift discipline by NOT
re-introducing schema-init code that resurrects dropped state.

**`/dashboard` (added 21 May 2026, commit db38c56):** greenfield 13-panel
overview route per `docs/mockups/dashboard_restructure_v1.html` design
contract. Above-fold 3×2 grid (Daily Summary / Top 5 Strong / Top 5
Bearish / Market State / Watchlist Preview / Discovery Themes),
full-width Elite-only Penny Stock spotlight (server-side tier gate —
non-Elite clients receive no pick data), below-fold 3×2 grid (Earnings
/ Dividends / Sector Performance / Rating Changes / Insider / News).
Logged-in `/` redirects to /dashboard; logged-out hits the legacy
index() flow (preserved as dead code under the redirect). Three helper
extractions accompanied the route — `_get_sector_performance`,
`_get_penny_pick_full`, `_compute_theme_counts` — each is a
behaviour-preserving refactor: the original `/api/sector-performance`,
`/api/penny/stock-of-day`, and `/api/theme-counts` JSON endpoints still
exist and still return the same payloads; the dashboard route calls
the extracted helpers directly to avoid duplicating SQL.

**Design-system seam (21 May 2026):** /dashboard is the FIRST page on
the new navy/green Option C palette (navy-950 ground, green-400 accent,
gold reserved for Elite spotlight, Fraunces/Inter Tight/JetBrains Mono).
The rest of the site (`/signals`, `/screener`, `/markets`, `/ticker/...`,
etc.) still renders the old cyan/_nav.html system. Sitewide migration
is deferred and queued in FOLLOWUPS — visible seam is expected until
the new `_nav.html` + `_footer.html` partials roll out across all
templates.

`database/db.py`: SQLite helpers including `insert_screener_snapshot`.
Around line 244 is the INSERT statement for screener_snapshots; this
file was missed in the 9 May column drop inventory (P1.1 violation),
leading to BUG B (every screener scrape failing silently for 48 hours
until pytest freshness tests caught it on 11 May). Fixed 11 May (commit
ec99570), empirically confirmed live on 12 May 2026 08:xx screener run.
P19 codified to prevent recurrence: schema migration inventory must
enumerate every CRUD path, not just init code.

`web/templates/screener.html`: main screener template. Exchange filter
pills (NYSE, NASDAQ, AMEX, Other) live in the sidebar between Rating
and Composite Score sections (commit 72bfcdf, 9 May 2026). Reuses
.mcap-btns / .mcap-btn CSS with multi-select toggle semantics.
mcap-btns container has id="f-mcap" to scope the existing single-select
handler and prevent collision with the new multi-select handler.
Persistence is HYBRID: localStorage default + URL params override (URL
wins on boot, writes through to localStorage). EXCHANGE column header
tooltip mentions ETFs / NYSE Arca / Cboe BZX listings to clarify what
"Other" includes.

`web/templates/penny_screener.html`: penny screener, structurally
separate template/JS from main screener. Same /api/screener endpoint
with price_max=5 baked in. Exchange filter NOT yet added (deferred
per Phase 1 finding that "Other" bucket is dominated by ETFs and the
penny universe under "Other" is a different population than originally
assumed).

`web/templates/ticker.html`: ticker page. Three component rendering
surfaces (signal strip, scorecard chips, radar legend + chart) are
driven by a single JS `COMPONENTS` registry declared inside the
fetchTicker success callback (refactor shipped 11 May 2026, commits
502f240..2c72400 + c9f8851 Legal ✓ fix). Each registry entry carries
key, label, tooltip, dotColor, radarIndex, nullOverlay, inStrip,
getValue, stripRenderer, chipRenderer. Adding components 9-16 will be
registry additions, no template surgery. Chart.js radar labels
derived from registry via `filter(c => c.radarIndex !== null).sort().map(c => c.label)`.
Legal is `dotColor: null` + `radarIndex: null` (off the radar);
Value/Sector are `inStrip: false`; null-overlay logic reads
`r.wasNull` from getValue output (not the DB key directly).

`scrapers/screener_scraper.py`: FinViz screener (Overview, Financial,
Technical, Custom views). Custom view column mappings: column 63 = Avg
Volume (added 12 May 2026, Fix B, commit 6714509), column 64 =
rel_volume. `_to_int` helper handles pandas float-formatted strings via
`int(float(str(val).replace(",","").strip()))` (12 May 2026, Fix A,
commit 164b6fb; the prior int() conversion choked on inputs like
"4901758.0"). `_scrape_exchange(soup)` wrapper uses href pattern search
(f=exch_), not link index, robust against future FinViz page structure
changes. `scrape_analyst_recom_priority` is the priority recom scraper,
called inline by job_generate_signals.

`scrapers/legal_risk_scraper.py`: SEC EDGAR. legal_risk table has 9
columns. Coverage expanding daily; ~87 tickers as of 9 May 2026,
growing at ~10/day.

`scrapers/fmp_scraper.py`: FMP API scraper. `_get()` retries 3× with
10s sleep on 429. As of 12 May 2026 (commit c38e167), a module-level
consecutive-429 circuit breaker protects against globally rate-limited
runs: `_fmp_429_streak` increments on 429, resets on 2xx, raises
`FMPRateLimitError` at `FMP_CIRCUIT_BREAKER_THRESHOLD = 10`. Protected
by `threading.Lock()` (scheduler uses `ThreadPoolExecutor(3)`).
`job_refresh_dividends` per-ticker handler has explicit
`except FMPRateLimitError: raise` to propagate breaker trips past the
generic exception swallow (commit 876c025).

`signals/scorer.py`: `TITLE_WEIGHTS`, `_title_weight()`,
`compute_composite()` (5-component weighted average + normalisation),
`score_all_tickers()`. `score_mean_reversion` shipped Position A NULL
handling 8 May 2026: per-input neutral contribution (RSI=20,
low_52w=17.5, sma_50=12.5), summing to 50.0 for all-NULL inputs. Legal
penalty applied additively before _clamp.

`signals/line_item_keys.py`: canonical vocabulary layer for
`financial_statements` line item keys. Raw yfinance PascalCase strings
are stored verbatim in the DB; this module is the single update point
if yfinance renames a field. Three constant dicts (INCOME_KEYS 12
entries, BALANCE_KEYS 15 entries, CASHFLOW_KEYS 7 entries); two lookup
sets (PIOTROSKI_LOOKUPS 9 entries, ALTMAN_LOOKUPS 6 entries). Design
decision locked 14 May 2026: `common_stock_equity` intentionally absent
(not present in yfinance 1.2.0 AAPL output); Altman X4 uses
`TotalLiabilitiesNetMinorityInterest` via `total_liabilities` key, NOT
`TotalDebt`. Scorer functions reference snake_case constants from this
module; mapping occurs at read-time, not write-time, preserving raw data.

`signals/target_price.py`: `compute_targets_batch` is the underlying
target-price work function, called inline by job_generate_signals (the
trailing job_compute_target_prices cron wrapper was removed 9 May 2026).

`config/constants.py`: TRACKED. SCORING_ENGINE_VERSION (currently
0.17.0), DATABASE_PATH, SECTORS, SCREENER_SCRAPE_TIMES,
NEWS_SCRAPE_TIMES, INSIDER_SCRAPE_TIMES, MIN_PRICE_FOR_SIGNAL,
ALERT_MIN_COMPOSITE_SCORE, REQUEST_DELAY_SECONDS.

`config/settings.py`: GITIGNORED, three secrets only:
TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, FMP_API_KEY. Imports from
constants.py for any non-secret values.

`docs/scoring_invariants.md`: process invariants (P1-P19).

`docs/tier_matrix.md`: canonical tier-feature mapping.

`~/Library/LaunchAgents/io.thesignalvault.gunicorn.plist`: LaunchAgent
plist managing gunicorn under launchd. Configured via Python plistlib
to bypass XML-in-heredoc rendering issues (15 May 2026 lesson). Six
ProgramArguments: gunicorn binary, -w, 1, -b, 127.0.0.1:5001,
web.app:app. WorkingDirectory `/Users/markn/signalintel`. UserName
markn (LaunchAgent runs as user, not root). Survives logout and reboot.
Logs to `~/signalintel/logs/gunicorn.{out,err}.log`. Does NOT run from
under ~/Documents/ — macOS TCC restrictions block launchd-spawned
processes from reading project files under that path, which was the
core blocker behind the Phase 2c project tree migration (15 May 2026).

`/Library/LaunchDaemons/com.cloudflare.cloudflared.plist`: System
LaunchDaemon managing cloudflared. Routes traffic from
thesignalvault.io to localhost:5001 via Cloudflare Tunnel. Config at
`/etc/cloudflared/config.yml`. Path-agnostic relative to the
SignalIntel project tree; unaffected by Phase 2c migration. Installed
via `sudo cloudflared service install` plus manual plist correction
(default install omits the `tunnel run` arguments — 15 May 2026
lesson).

`/etc/cloudflared/config.yml`: Cloudflare Tunnel ingress configuration.
Tunnel UUID `6bc7b651-9255-4c50-8d70-6f5e6175930f`. Routes
thesignalvault.io and www.thesignalvault.io to http://localhost:5001.
Credentials at `/etc/cloudflared/6bc7b651-9255-4c50-8d70-6f5e6175930f.json`.

`scripts/drop_screener_snapshots_exchange.py`: idempotent migration
(9 May 2026, commit 0b4d9a4). Re-runnable, no-op if column absent.

`scripts/backfill_exchange.py`: bulk backfill (used 7-8 May 2026 to
populate ticker_metadata.exchange for 11,109 tickers).

`tests/test_screener.py`: added 9 May 2026 (commit 2992a17) with five
exchange-filter tests (single, multiple, other-includes-null, absent,
unknown-value).

`tests/test_fmp_circuit_breaker.py`: added 12 May 2026 (commit 9b17c4d).
5 tests covering below-threshold reset on 2xx, threshold trip,
propagation through `job_refresh_dividends`, cross-job reset via 2xx,
and the threshold=1 edge case. All stub `requests.get` and `time.sleep`;
no real HTTP, no real delays.

`tests/test_data_integrity.py`: data-freshness tests. Two original
tests (`test_signal_scores_freshness`, `test_screener_snapshots_freshness`)
caught BUG B's 48-hour silent failure on 11 May. Expanded 12 May 2026
(commit e31b79d) with three more covering insider_trades (via run_log,
since the INSERT-OR-IGNORE pattern makes scraped_at unreliable),
legal_risk (via scraped_at), and ticker_metadata (via updated_at). All
five freshness tests at 72h consistency threshold. Cosmetic note: the
two original tests still use em-dashes in assertion messages while the
three new ones use commas; one-line cleanup pending.

`tests/` overall: 194 tests total (191 prior + 3 new freshness tests
from the 12 May expansion). The data-freshness tests are sensitive
operational tripwires.

`logs/trading_system.log`: live scheduler log. Configured in main.py
via `logging.basicConfig` with StreamHandler(stdout) + FileHandler.
Screener job logs `JOB START: Screener` and `JOB DONE: Screener (N
rows, Xs)` envelope lines, useful for grep-based runtime verification.

`data/trading_system.db`: SQLite database, **~1.2 GB (21 May 2026; ~227,721 signal_scores rows; was ~328MB post-VACUUM 13 May 2026, reclaimed 35MB from the 9 May column drop, 363MB → 328MB)**.
Growth between 13 May and 21 May driven by accumulated scoring history
(v0.13.0 → v0.14.0 transition) plus the daily ~33k-rows/day cadence
across three scrape windows. Linear projection ~12M screener_snapshot
rows/year; data retention strategy is a future thought (post-Yahoo).
Nightly backup armed 21 May 2026 (see `scripts/backup_database.sh` +
LaunchAgent `io.thesignalvault.backup`, daily 03:30 BST, 7-daily + 4-weekly rotation, restore-verified).

### Key DB Tables

- `screener_snapshots`: FinViz raw data. As of 9 May 2026: 34 columns
  (exchange dropped). rel_volume populates correctly from 7 May onward;
  pre-7-May rows have NULL. BUG B (11 May 2026): INSERT in
  database/db.py:244 still referenced the dropped exchange column for
  ~48 hours, silent failure caught by pytest freshness tests, fixed
  11 May and empirically confirmed 12 May. Volume + avg_volume
  populated from 12 May 2026 16:30 onward (commits 164b6fb, 6714509,
  329dfee; baseline 0/11k pre-fix, 100% / 99.7% post-fix). The 0.3%
  avg_volume NULL tail is legitimate FinViz data absence for
  illiquid/SPAC tickers, empirically confirmed via ATC ("-" on FinViz)
  and SPACEX ("Chart Not Available") spot-checks on 13 May 2026.
- `ticker_metadata`: 8 May 2026 onward: ticker PK, exchange,
  first_seen_at, updated_at. Populated for 11,122+ tickers. Canonical
  source for exchange.
- `signal_scores`: computed scores. Time column is `scored_at`, NOT
  `snapshot_date`. People get this wrong, including past CC sessions.
  Component columns: momentum_score, quality_score, insider_score,
  reversion_score, sector_strength_score, volume_score. Aggregates:
  composite_score, composite_score_raw, sector_modifier_applied,
  scoring_version. First v0.12.0 production rows: 9 May 2026 11:38 BST.
- `legal_risk`: SEC EDGAR data. NOT NULL constraints on risk_level,
  risk_label, risk_color, penalty. Three rendering states: no-row
  (~99% of scored tickers, dropping daily), NONE-level scraped clean,
  populated risk (MINOR / CLASS_ACTION / SEC_INVESTIGATION /
  SEC_ENFORCEMENT / CRIMINAL).
- `insider_trades`: FinViz insider data.
- `rating_changes`: history of tier transitions.
- `top_signals_of_day`
- `watchlists`: membership, ticker per row.
- `watchlists_meta`: per-watchlist settings. WATCHLIST DATA-LOSS BUG
  (11 May discovery): watchlists persist on plain server restart but
  appear to reset when there's a code change between restart events.
  Diagnostic deferred, likely a startup-path init function with
  code-change-conditional DDL branch.
- `users`: with tier column.

---

## COMPOSITE SCORE: THE 16-COMPONENT VISION

Built (8):
1. Momentum: price action, MAs, RSI
2. Quality: fundamentals
3. Insider: insider buying/selling
4. Reversion: mean reversion (Position A NULL handling shipped 8 May
   2026; v0.12.0 confirmed in production 9 May 2026)
5. Legal: SEC EDGAR penalty (~0.7% coverage as of 9 May, growing daily;
   removed from radar 8 May 2026, ⚖️ card renders it richer)
6. Value: valuation. NOT in compute_composite weights; applied via
   separate path, computed client-side from target_upside.
7. Sector Strength: relative sector. NOT in compute_composite weights;
   applied as sector_modifier_applied (multiplicative, ±7.5%).
8. Volume Confirmation: four-tier RVOL × price-change scoring
   (climax/confirmed/mild/low). Reads rel_volume from
   screener_snapshots Custom view column 64.

Composite weighting (compute_composite): 9 components contribute via
weighted average (sum = 1.60, normalised by total_w): momentum (0.35),
quality (0.30), insider (0.25), reversion (0.10), volume (0.10),
earnings_surprise (0.125), piotroski (0.125), inst_own (0.125),
analyst_mom (0.125). Legal applies additively as penalty (NONE=0,
MINOR=-5, CLASS_ACTION=-15, SEC_INVESTIGATION=-30, SEC_ENFORCEMENT=-45,
CRIMINAL=-60). Altman Z'' (1995 non-manufacturing) penalty applies
additively as of v0.14.0 (18 May 2026): Z''≥2.6→0, Z''≥1.1→-10,
Z''≥0→-30, Z''<0→-60; all-or-nothing (any missing input → 0). Switched
from classic 1968 Altman Z because the original manufacturing formula
penalised 62.9% of the SignalIntel universe (calibration failure for
tech-heavy non-manufacturing universe); Z'' reduces to 47.8%. Both
penalties applied before `_clamp`. Sector strength applies
multiplicatively. Value's integration into composite is currently
unclear; scoped for review during Yahoo pipeline session.

As of v0.17.0 (25 May 2026 PM), `analyst_mom` folds **hard rating
actions only**. `get_analyst_momentum_map` SUMs +1.0 for action
IN ('up', 'init'), -1.0 for action='down', and 0.0 for everything else
(including soft main/reit rows regardless of priceTargetAction).
`net_momentum` is integer-valued, mathematically (hard upgrades - hard
downgrades). The v0.16.0 soft-action PT folding (main/reit Raises=+0.25,
Lowers=-0.25) was REMOVED after failing external event-study validation
on 25 May 2026: real-cohort Raises-minus-Lowers 21d CAR spread came back
at -0.79% (t=-3.64, p=2.7e-04) — wrong sign, monotonicity inverted,
robust across 5/7 years, 10/11 sectors, 9/10 firms; survived beta
adjustment with comparable magnitude. Placebo cohort showed the
expected positive ordering, proving the inversion was event-driven, not
method artefact. Per the OOS validation gate (commit a56afaa), a
provisional weight that fails validation is pulled to neutral, NOT
sign-flipped on the same test that disproved the priors. Event-fade as
a separate component (Bernard-Thomas drift; its own theory, its own
provisional weight, its own OOS validation) is logged as a future
candidate — never folded back into analyst_mom. The scorer's float
ladder + ±0.5 neutral band at signals/scorer.py stays correct on
integer net_momentum (the band is the neutral-tier rule on integers,
not v0.16-specific dead code). Coverage trade-off accepted: less
coverage scoring neutrally beats more coverage scoring backwards.

Components 9-16 land in the Yahoo pipeline session (next major work).
Ticker page rendering is now array-driven via the COMPONENTS registry
in ticker.html (11 May 2026 refactor), so new components will be
registry additions, not template surgery.

### SCORING_ENGINE_VERSION: 0.17.0

Bump policy: PATCH = bug fix without scoring change; MINOR = new
component, weight change, OR substantive scoring substrate change
(P18); MAJOR 0→1 = production launch freeze.

Version history:
- 0.9.0: original 7-component build (98,108 stamped rows)
- 0.10.0: Volume Confirmation added; rel_volume universally NULL (no
  rows stamped)
- 0.11.0: rel_volume fix; volume component producing real scores;
  Custom view bugs repaired
- 0.12.0: Position A NULL handling for score_mean_reversion; 37-row P5
  violation fixed; first prod rows 9 May 2026 11:38 BST.
- 0.13.0: 5 Yahoo enrichment scorers added (earnings_surprise,
  piotroski, inst_own, analyst_mom, altman_penalty); composite
  rebalanced to 9-component / 1.60-sum; Altman penalty additive;
  first prod rows 14 May 2026 14:19 BST.
- 0.14.0: Altman methodology switch — classic Z (1968 manufacturing)
  to Z'' (1995 non-manufacturing). Empirical distribution analysis
  (3,631 tickers): classic penalised 62.9% → Z'' 47.8%. Penalty
  magnitudes (-10/-30/-60) preserved. First prod rows 18 May 2026.
- 0.15.0: inst_own recalibration — full-universe re-scrape (0.35% →
  97.3% pct_out fill) + quartile-anchored cuts (>=48→75, >=34→60,
  >=12→45, <12→30) + >100 implausibility guard → neutral 50.
  Coverage 0% → 50.8%. First prod rows 21 May 2026.
- 0.16.0: analyst_mom widening — fold price-target direction. SQL
  CASE in `get_analyst_momentum_map` produces float net_momentum;
  scorer uses float ladder with ±0.5 neutral band. Hard rating
  actions unchanged (±1); soft actions contribute ±0.25 on
  Raises/Lowers, no double-count. Coverage 0.06% → 20.4%. PT weight
  0.25 PROVISIONAL pending backtest. First prod rows 25 May 2026
  14:08 BST.
- 0.17.0: analyst_mom soft-action PT contribution neutralised after
  failing external event-study validation (21d CAR spread -0.79%,
  directionally backwards). Hard up/init/down unchanged ±1; soft
  main/reit contribute 0; net_momentum integer-valued again. Coverage
  20.4% → hard-only baseline; less coverage scoring neutrally beats
  more coverage scoring backwards. Also persists five component
  sub-scores on signal_scores (graduating-bar prerequisite, no scoring
  math change). First prod rows 25 May 2026 17:30 BST.

The 11 May refactor (component registry in ticker.html) did NOT bump
the version, purely presentational, no scoring substrate change.

The 12 May BUG A circuit breaker did NOT bump the version, operational
hardening only, no scoring substrate change.

The 12 May volume + avg_volume NULL fix did NOT bump the version,
data-completeness fix only; the volume component's scoring logic was
already correct, the issue was upstream NULL inputs from the scraper.

The 13 May VACUUM did NOT bump the version, storage reclamation only.

---

## PROCESS INVARIANTS: DOCS/SCORING_INVARIANTS.MD

Mark has codified 19 invariants from real failures. Reference these by
ID when relevant.

| ID  | Rule |
|-----|------|
| P1  | Audit ALL surfaces, not just the symptom site |
| P1.1| Inventory before edit |
| P1.2| Verify by absence |
| P1.3| Audit table report at session end with "Verified by" column |
| P2  | Diagnose before fixing |
| P3  | Verify in browser, not just in tests |
| P4  | Granular commits, one logical change each |
| P5  | NULL = neutral (50 score, never penalty) |
| P6  | Numeric values stored numeric (no string floats) |
| P7  | No redundant (?) icons |
| P8  | Themes: single source of truth |
| P9  | Filter+sort state preservation across navigation |
| P10 | Defensive empty states |
| P11 | Document invariants as discovered |
| P12 | Preserve raw values (format on render, not on store) |
| P13 | Descriptive language (no directive Buy/Sell) |
| P14 | Theme ID stability |
| P15 | Tests articulate signal AND silence |
| P16 | Audit table entries cite specific test/grep/inspection with empirical result. Hedge-words flag entries as unverified. Applies equally to FOLLOWUPS in our own docs (12 May lesson) |
| P17 | Audit entries describing function behaviour must enumerate complete set of effects |
| P18 | Substantive scoring substrate changes require MINOR version bump |
| P19 | Schema migration inventory enumerates every CRUD path against the modified table (read, write, init, ORM), not just init code. The 9 May column drop caught the ADD COLUMN guard in web/app.py but missed the INSERT in database/db.py, silent for 48 hours until pytest freshness tests caught it on 11 May. Phase 1 for any schema-affecting work must enumerate: init/migration code, ORM definitions, raw SQL INSERTs/UPDATEs/DELETEs, SELECT projections, and any place the column name appears as a string literal |
| P20 | Analyst completeness gate. When two paths diverge on what an analyst making a buy/sell/hold decision receives, the analytically-stronger path wins regardless of engineering cost. Engineering cost is a tiebreaker between analytically-equivalent paths only |
| P21 | Profile coverage matrices in Phase 2 prompts require explicit per-row verification gates confirming each matrix row produced the expected rating — not just that the total ticker count matches. Total-count agreement does not imply per-row correctness; synthetic inputs designed for "deep bearish" can inadvertently maximise a reversion scorer and route through HOLD before STRONG_SELL (14 May 2026, SS07 diagnosis B) |
| P22 | Session date is empirical context, not conversation-primed context. Any session involving "yesterday / today / tonight / overnight" temporal reasoning must ground on the actual current date stated explicitly at session start. Both CC and Athena are subject to date-blindness from primed context; the discipline is symmetric |
| P23 | Auth-adjacent side-effects require explicit escalation in audit, not just disclosure. Commits that add or modify side-effects in auth-adjacent functions (`current_user()`, login, logout, session handling, tier checks) must flag the change in the audit table with "AUTH SIDE-EFFECT — REQUIRES REVIEW" or equivalent. Disclosure in a commit-message bullet is necessary but not sufficient. The 7 May 2026 BUG-001-REOPENED backdoor was introduced in commit 9e02e7d (May 6 18:26), disclosed in that commit's bullet, then misdescribed in commit 7949805 the next morning — neither instance flagged the side-effect for review. P17 would not have caught this; the function was named, just not escalated. The pre-commit hook for auth-adjacent diff review (`scripts/git-hooks/pre-commit`, installed via `scripts/install-hooks.sh`, see CLAUDE.md) is the mechanical enforcement layer for P23, live on origin since 18 May 2026 (commits 0851963 + 8fe91a0 + 851221a). |
| P24 | Doc-file header text is descriptive metadata, never standing permission for CC to write. Headers such as "Updated end of each session" describe the file's intended use, not an instruction CC may act on. CC must not self-initiate edits to HANDOFF.md or PROJECT_CONTEXT.md. Editing instructions must come from Mark or Athena in-turn. Implementation prompts spanning multiple commits are the highest-risk pattern — CC reaches for end-of-session housekeeping when the implementation work concludes. Mitigation: include "do not modify HANDOFF.md or PROJECT_CONTEXT.md" on all implementation prompts regardless of stated scope |
| P25 | macOS TCC restricts launchd-spawned processes from reading files under ~/Documents/, ~/Desktop, ~/Downloads, and other protected paths, even after granting Full Disk Access to /sbin/launchd in System Settings. Service-managed processes (LaunchDaemons, LaunchAgents) MUST run from non-protected paths. SignalIntel lives at ~/signalintel as a result. Pattern recognition: a "PermissionError: [Errno 1] Operation not permitted" on a file under ~/Documents/ from a launchd-spawned process is TCC restriction, not Unix permissions. Granting FDA to launchctl in System Settings does NOT resolve the underlying TCC scope. The 15 May 2026 session burned ~90 minutes diagnosing this before the path migration; future deployments should default to home-root paths (~/signalintel, ~/my-project) rather than ~/Documents/. |
| P26 | XML content in shell heredocs is corrupted by chat renderers — angle-bracket tags (`<string>`, `<key>`) are interpreted as HTML and stripped during copy-paste from the chat interface to terminal. Use Python plistlib (or equivalent) to write plist files programmatically, then verify the contents via `/usr/libexec/PlistBuddy -c "Print :ProgramArguments" <path>` before installing. The 15 May 2026 LaunchAgent diagnosis cycle confirmed this: three identical-looking heredoc rewrites all lost the `-w` flag because `<string>-w</string>` rendered as an HTML attribute and disappeared. PlistBuddy verification on disk is empirical and unambiguous. |
| P27 | Beta tester confusion is a positioning audit, not a user-fit observation. When a beta tester struggles with a product whose tagline explicitly promises to serve them (here: "institutional-grade tools for non-institutional traders"), Athena's first move must be to audit whether the tagline still matches the surface, not to dismiss the tester as "outside the target user." Dismissing the tester is a positioning failure dressed up as taste. Logged 18 May 2026 from Guy's feedback session. Future Athena: when reflex is to frame a tester as wrong-user, check the tagline first. |
| P28 | Locked design patterns require at least a smoke-test invocation before being treated as ground truth. The Phase 1 + Phase 2 pattern produces design decisions that lock specific values, helper patterns, and snippets of code (regexes, shell idioms, FD redirections, SQL fragments). On-paper review can miss bugs that only surface on first execution. The 18 May 2026 auth-adjacent pre-commit hook ship surfaced this: the locked `exec 3</dev/tty 2>/dev/null` pattern from Phase 1 passed design review but silently redirected stderr for the rest of the shell on the success path, killing the user-facing "Commit aborted" message. Fix was one line (`{ exec 3</dev/tty; } 2>/dev/null` to scope the redirect) but the bug only emerged in the empirical verification walk. Discipline: when Phase 1 locks a non-trivial code pattern, Phase 2 prompts must include an explicit smoke-test step that exercises the pattern in isolation before it's integrated into the full implementation. Generalisation of P3 (verify in browser, not just tests) to design-phase decisions. |
| P29 | Scoring-substrate methodology changes are gated by empirical distribution evidence on the production universe, not theoretical reasoning. The 18 May 2026 Altman Z → Altman Z'' switch (v0.13.0 → v0.14.0) was authorised only after a read-only distribution analysis (scripts/altman_distribution_analysis.py) computed Z and Z'' for 3,631 tickers and showed classic Z penalised 62.9% of the universe vs Z'' at 47.8%. Decision shape was locked before script ran: three outcomes (calibration holds / grey-zone cluster / bimodal) with sub-decisions for each, all framed in version-bump-policy (P18) terms. The empirical step is non-negotiable for any future scoring substrate change (Piotroski tier recalibration, Sector strength magnitude tuning, new component weight integration). Pattern: Phase 1 inventory → Phase 2a helper extraction (behaviour-preserving) → Phase 2b analysis script → Phase 2c decision lock with empirical evidence → Phase 2d implementation with version bump. Six gates, zero rework. |
| P30 | Tests ship with the behaviour they describe (21 May 2026). A commit that changes scoring output OR a route's response contract MUST update its tests in the SAME commit. Twice on 21 May a behaviour change shipped with stale tests left red: inst_own v0.15.0 recalibration (175bbf7) shipped without updating its unit tests or regenerating the scorer snapshot; the dashboard redirect (db38c56) shipped without updating the smoke tests' PAGE_ROUTES 200-expectation. Both pushed before the staleness was noticed (caught only when an unrelated task happened to run pytest). A red suite masks the next regression. Verification gates that check live output do NOT substitute for updating the unit/snapshot tests that assert intended behaviour. |
| P31 | Long-running DB writers must tolerate lock contention (21 May 2026). SQLite serialises writers; the scheduler is a near-constant background writer (screener scrapes are ~54-min DB writers, plus signal_generation, insider, Yahoo jobs). Any long-running manual or bulk writer that overlaps a scheduled job WILL eventually hit "database is locked". On 21 May the analyst bulk job crashed on exactly this — a single unhandled OperationalError killed a ~90-min run at 1,545/~6,000 tickers. Lock errors are transient (the other writer finishes in seconds), so bulk writers must retry-with-backoff on OperationalError rather than dying. This applies to any job registered on the scheduler too: `job_yahoo_analyst_bulk` (Wed 04:00) needs this before it can be trusted unattended. |

---

## HEDGE-WORD LIST (P16 ENFORCEMENT)

Any of the following without empirical backing flags an audit entry as
unverified:

- "Theoretical" / "In theory" / "Theoretically"
- "Should" / "Should work" / "Should be fine"
- "Expected to" / "Expected behaviour"
- "By design"
- "No known issue"
- "Likely" / "Probably" / "Most likely"
- "Pretty sure" / "Fairly confident"
- "Looks right" / "Seems correct"
- "Spotted issue with X" / "Appeared to" / "Appears to" without empirical
  proof — same hedge category as "looks right". 16 May P21 audit lesson:
  CC's hedge that SS07 "appeared to" route STRONG_SELL was verified by
  empirical sweep, which confirmed correct routing. Apply the same
  vigilance whenever CC frames a verification as observation rather
  than measurement.
- "Renders after server restart" / "Will render correctly", predictions
  are not verifications
- "Single 404, error handling working as designed" without pasting the
  actual log line
- "Will produce diverse [score]" instead of running the function
- "Obviously", especially "obviously sensible" used to justify
  out-of-scope decisions

When these appear in CC's output, the next prompt should ask for
empirical proof of the claim, not accept the hedge.

The same vigilance applies to FOLLOWUPS in our own docs. 12 May 2026
lesson: the SCHEDULER.LOG ORPHAN entry assumed "Some FileHandler in
the codebase (probably an early prototype scheduler module)" but
empirical grep returned zero hits. The diagnosis was speculative.
Unverified diagnoses carry forward in our docs as easily as in CC's.

CC also occasionally drifts into adjacent concepts when reaching for
"why" explanations. 13 May 2026 example: asked to characterise the
28 tickers with NULL avg_volume from the post-fix scrape, CC's note
referenced "tickers where the Custom view returned no exchange/data
for that field." Exchange was dropped on 9 May 2026 and has nothing
to do with avg_volume; CC's framing slipped onto an adjacent topic
rather than the columns actually at play. The empirical verification
itself was correct, but the loose explanation could have leaked into
HANDOFF if not caught. Watch for explanations that reach for
plausible-sounding adjacent concepts without verifying the mechanism.

---

## RUNTIME-CODE DRIFT: A FIRST-CLASS FAILURE MODE

Long-lived processes (the scheduler, the Flask web server) load module
code into memory at start time. New commits to disk do NOT deploy until
the process restarts. This is invisible without explicit instrumentation.

This failure mode bit the project four times in 72 hours (7-9 May 2026):
- 7 May commits on disk for ~24 hours but not running
- 8 May 08:00 BST scrape ran with pre-fix code
- 8-9 May overnight: scheduler started before version-bump commit, ran
  stale through the night
- 9 May column drop: web/app.py ADD COLUMN guard in running Flask
  process would have re-added the dropped exchange column on next
  restart had CC not removed it alongside the migration

11 May 2026 added a non-drift but adjacent class of bug to the same
file (database/db.py BUG B): the migration completed cleanly but missed
a CRUD path. The scheduler ran the fixed code as soon as it restarted,
so this was strictly a "missed surface" failure (P1.1 / P19), not
runtime drift. The freshness tests caught it.

12 May 2026 confirmed the BUG B fix held in production: 08:xx screener
run produced fresh rows, both freshness tests passed for the first time
since 8 May.

Mitigation in place:
- main.py `_log_startup_banner()` logs SCORING_ENGINE_VERSION + git
  HEAD short hash + ISO 8601 process start time on every scheduler boot
- The banner is necessary but not sufficient. Detection-without-action
  is the failure mode the banner alone doesn't solve.
- Habit: any commit touching SCORING_ENGINE_VERSION, signals/scorer.py,
  the scheduler, web/app.py, OR scrapers/ should trigger an explicit
  process restart at commit time. Don't rely on noticing the banner
  later. The scrapers/ extension is a 13 May 2026 lesson: the volume +
  avg_volume fix landed on disk and pushed without effect until the
  scheduler restarted onto the new code, exactly the runtime-drift
  pattern that hit the project four times in 7-9 May.
- Schema migrations specifically: Phase 1 inventory must include "what
  would resurrect the dropped state on restart" (startup guards, ORM
  init, table-create-if-missing patterns). AND every CRUD path against
  the dropped column or table (P19).

---

## THE VERIFICATION GATE: NON-NEGOTIABLE

CC reports "done" before things are properly done. The verification
gate exists to catch this.

Every CC prompt must end with an explicit verification gate listing
checks CC must satisfy before claiming complete. Every Mark-side
verification must walk that gate, not skim it.

**Common failure modes:**
- CC's audit table makes plausible-sounding claims that haven't been
  empirically tested. Predictions in gate output are not verifications.
- CC reports gate items as satisfied without empirical evidence
  ("renders after server restart" instead of "here is the rendered
  page"). Browser walks performed by Mark, specified by CC; CC
  predicting Mark's observation is not satisfying the gate.
- CC drifts on negative instructions ("do not modify X") even when
  scope is clear. Stronger language ("modifying HANDOFF.md is a
  P-level violation, output STOP if you would") helps for files CC
  could reasonably want to update.
- CC bypasses STOP-on-condition gate items when it has a sensible
  interpretation of the alternative action (12 May lesson). Gate
  STOP conditions must be honoured even when the alternative looks
  obviously correct.

`CLAUDE.md` has a "Scope Discipline" section that requires CC to not
modify code outside the prompt's explicit scope.

**Athena's job in any session:**
1. Help Mark draft CC prompts with verification gates baked in
2. When CC reports done, walk Mark through verification methodically
3. Don't accept CC's audit table at face value, require proof
4. If verification finds gaps, capture the bug and resume properly

**Real-world wins (11 May 2026):**
- Legal `✓` glyph regression caught on ATYR browser walk during Phase
  2 audit. CC's code review claimed the implementation matched the
  Phase 1 inventory; the actual rendered chip showed "Clean" instead
  of "Clean ✓". Fixed in a follow-up commit before push. Demonstrates
  why code-review claims alone don't satisfy the gate; observed
  behaviour does.

**Real-world wins (12 May 2026):**
- BUG B verification gap from 11 May (committed but never empirically
  observed in production) was caught the next morning when freshness
  test still failed. The fix had been right; the verification hadn't
  closed. 08:xx screener run finally produced the empirical evidence.
- P19 sweep on screener_snapshots, post-hoc, confirmed only one
  residual exchange reference remained (a dead one-time migration
  script). Empirical closure on the BUG B substrate.

**Real-world wins (13 May 2026):**
- Volume + avg_volume fix verified via baseline-and-comparison. Pre-fix
  scrapes (07:00 and 11:00 12 May) showed 0% populated; post-fix scrape
  (16:30 12 May, completing 17:23) showed 100% volume and 99.7%
  avg_volume. The 28 NULL avg_volume rows spot-checked on FinViz (ATC
  shows "-", SPACEX shows "Chart Not Available") confirming source-side
  data absence rather than parser miss. P16 absolutism: hypothesis was
  plausible, empirical check closed it.
- VACUUM reclaimed 35MB on a 363MB DB (9.6% reduction), integrity
  verified before and after, no row loss. Demonstrated the
  stop-scheduler → backup → VACUUM → verify → restart workflow on a
  live production DB without losing the running scheduler state.

---

## PRODUCT ROADMAP

### Phase 1 (active, pre-launch, system used by Mark only)

✅ SEC EDGAR legal cards
✅ Wire legal penalty into composite score
✅ Multi-watchlist infrastructure with tier gating
✅ Telegram alerts (watchlist-gated)
✅ Backtesting system (rating_changes table, /backtest page)
✅ Global ticker search with keyboard nav
✅ Scoring engine versioning (now 0.12.0)
✅ Default watchlist for all users
✅ BUG-001-REOPENED: tier display backdoor in current_user() removed
✅ SIGTERM/SIGINT graceful shutdown handler
✅ Volume Confirmation (component 8)
✅ rel_volume scraper fix + Custom view collateral fixes
✅ Config refactor (constants.py + settings.py split)
✅ Exchange/listing field on ticker pages
✅ Bulk exchange backfill (11,109 tickers)
✅ ticker_metadata table + EXCHANGE columns on screeners
✅ Causal job chaining (8 May 2026)
✅ Scheduler startup banner (8 May 2026)
✅ Reversion 0.0 P5 violation fixed (Position A, 8 May 2026)
✅ Legal NULL UX (drop from radar, three-state rendering, 8 May 2026)
✅ Truthy-check rendering bug fixed (8 May 2026)
✅ Trailing-cron cleanup (9 May 2026, commit 3d315b1)
✅ Banner port fix 5000 → 5001 (9 May 2026)
✅ screener_snapshots.exchange column dropped (9 May 2026, commit 0b4d9a4)
✅ Backend exchange filter on api_screener (9 May 2026, commit 2992a17)
✅ Frontend exchange filter UI on screener (9 May 2026, commit 72bfcdf)
✅ Component rendering refactor (radar/scorecard/strip array-driven via JS COMPONENTS registry, 11 May 2026, commits 502f240..2c72400)
✅ Legal ✓ regression fix (11 May 2026, commit c9f8851, caught via verification gate)
✅ BUG B fix: database/db.py INSERT regression from column drop (11 May 2026, confirmed live 12 May)
✅ BUG A workaround: dividend job disabled pending FMP circuit breaker (11 May 2026)
✅ BUG A proper fix: FMP consecutive-429 circuit breaker shipped (12 May 2026, commits c38e167, 876c025, 9b17c4d, ddd9da5)
✅ P19 sweep on screener_snapshots: dead migration script deleted (12 May 2026, commit 0848893)
✅ scheduler.log orphan + 9 May DB backup cleanup (12 May 2026, commit 94c1d91)
✅ Volume + avg_volume NULL fix (12 May 2026, commits 164b6fb Fix A, 6714509 Fix B, 329dfee comment fix; empirically verified 13 May with baseline-and-comparison plus FinViz spot-checks)
✅ Data-freshness test expansion (12 May 2026, commit e31b79d; insider_trades, legal_risk, ticker_metadata added at 72h threshold; 191 → 194 tests)
✅ VACUUM screener database (13 May 2026; 35MB reclaimed, 363MB → 328MB, no row loss, integrity verified; closes the 9 May column-drop residue)
✅ Phase 2a — Flask production hardening (15 May 2026, 6 commits, pushed): SECRET_KEY moved from tracked source to FLASK_SECRET_KEY in config/settings.py, ProxyFix middleware for Cloudflare Tunnel HTTPS termination, SESSION_COOKIE_SECURE/HTTPONLY/SAMESITE=Lax hardening, gunicorn 23.0.0 added (single worker for in-memory flask-limiter compatibility), flask-limiter 10/min on POST /login, debug=False in __main__ block. Pytest 231 passing + 4 skipped + 1 pre-existing SB01 failure (carried over). End commit: bd31b99.
✅ Phase 2b — Cloudflare Tunnel deployment (15 May 2026): cloudflared installed via Homebrew, named tunnel `signalintel`, ingress for apex and www, GoDaddy nameservers swapped to Cloudflare (anahi.ns + craig.ns), DNSSEC confirmed off, propagation completed in ~75 minutes, cloudflared installed as LaunchDaemon with correct ProgramArguments (initial install omitted `tunnel run` args, fixed via plist rewrite). End state: thesignalvault.io live over HTTPS via Cloudflare proxy, four edge connections to London (lhr10/13/13/18). No code commits; operational config only.
✅ Phase 2c — Project tree migration out of ~/Documents/ (15 May 2026, 2 commits, pushed): Project moved from ~/Documents/trading-system to ~/signalintel to bypass macOS TCC restrictions on launchd-spawned processes. Venv recreated at new path (pip install -r requirements.txt). Five one-off legal-risk scripts and CLAUDE.md updated for path strings (commit 7eb0899). Tracked .pyc files and web/.DS_Store removed, .gitignore patterns added (commit ab8eca1). Gunicorn now under LaunchAgent at ~/Library/LaunchAgents/io.thesignalvault.gunicorn.plist, surviving reboot. Old path retained at ~/Documents/trading-system.OLD for 24-hour safety window (delete after 16 May 2026 16:49 BST if stable).

[ ] Yahoo Finance pipeline + components 9-16 (FRESH CHAT, large infrastructure session, next major work)
[ ] Virtual portfolio with margin calls and bust mechanic
[ ] Email alerts via SendGrid

### Phase 2

- Stripe paywall (tier enforcement live for paying users)
- Earnings calendar
- Short squeeze signals (high short interest + STRONG_BUY confluence)
- Options flow (Unusual Whales)

### Phase 2c (NEW, 18 May 2026): Multi-user notifications substrate

Hard blocker for paywall. Current Telegram alerts fire only to Mark's
system-level bot_token + chat_id. No per-user subscription flow.
Bundling Telegram per-user routing + SendGrid email alerts into one
coherent notifications phase. Half-shipped notifications would be a
worse user experience than no notifications.

- Per-user Telegram linking flow: generate unique linking code →
  user runs /start on the bot → capture chat_id → write to new
  `user_telegram` table keyed on user_id
- Per-user alert routing: rewrite `send_telegram_alert()` to iterate
  users with linked chat_id + watchlist alerts_enabled + tier gate
- Tier gating decision for Telegram alerts (Starter+ or all tiers?
  Update `docs/tier_matrix.md`)
- SendGrid email alerts (already on backlog; bundle here so users
  without Telegram aren't excluded — most UK non-tech users)
- UI surfaces: profile/settings page (link/unlink Telegram +
  email preferences), watchlist page (already has alert bells),
  virtual portfolio page, ticker page (alert-me affordance)

Estimate: 2-3 weeks. Sits between Yahoo pipeline completion and
Phase 3 start.

### Phase 3 (NEW, 18 May 2026): UK/HK markets + Lite mode + Learn hub

Triggered by Guy (beta tester, 18 May) bouncing off product
density and asking about UK stocks. Tagline "institutional-grade
tools for non-institutional traders" only earns its keep if the
surface is accessible to non-power-users. Lite is a learning ramp
plus a TAM expansion — current Power view stays for users who want
the density, Lite is the default for new signups.

LSE + HK market addition (must land before paywall):
- LSE: UK stocks, .L convention, UK fundamentals source TBD
  (FinViz is US-only). Substrate work: ticker conventions,
  fundamentals sources, market hours (BST/GMT), sector taxonomies
  that need normalising against existing SECTORS list.
- HK: Hong Kong stocks, .HK convention, HK fundamentals source TBD.
  Same substrate concerns plus 8h time zone offset.
- Yahoo covers global tickers natively which helps; UK/HK fundamentals
  alternative to FinViz is the open engineering question.
- Estimate has wide error bars: 4 weeks to 3 months depending on
  fundamentals sourcing answer.

Lite mode (renderer addition, not parallel scoring path):
- Lite ticker page: composite as single 0-100 dial + plain-English
  one-line summary per component. Reads same component registry
  as Power view — registry refactor on 11 May already supports
  parallel renderers.
- Lite dashboard: top 5 signals with one-sentence rationale each
- Profile toggle: Lite / Power view, Lite default for new signups,
  existing users default to Power view
- Inline glossary hover from every Lite numeric, linked to relevant
  Learn module

/learn hub (10 modules):
1. Composite scoring (how 9 components combine)
2. Momentum signals
3. Insider activity signals
4. Mean reversion
5. Legal risk and penalties
6. Volume confirmation
7. 7-tier rating system (Very Strong through Very Bearish)
8. Backtesting and verified performance
9. Watchlists and alerts
10. Descriptive-not-directive language (why we say "Strong Signal"
    not "Buy")

YouTube companion series:
- 10 × ~30 minute videos, one per /learn module
- Weekly cadence
- Marketing + SEO leverage; content workstream separate from
  engineering

Estimate: 6-10 weeks core engineering + 30-50 hours video production.

### Phase 4 (was Phase 3)

- Macro overlay
- Sector heatmap
- Monthly tournaments + referral programme
- Public signal record (verified performance log)

### Phase 5 (was Phase 4)

- Public launch
- React Native mobile app
- Elite API tier
- White label B2B (broker affiliate partnerships: eToro, IBKR)

### Key Differentiators

1. Verified public performance record, wins AND losses visible
2. Monthly paper trading tournaments with real prize pools
3. Short squeeze detector (composite + short interest confluence)
4. Legal risk scoring via SEC EDGAR feeds composite as penalty

### PRICING (locked 25 May 2026)

This is product spec, not a sketch. The earlier "Starter / Pro / Elite"
draft is superseded — Starter is dropped, B2B / white-label moves to
Phase 3, two tiers ship at launch.

**What customers buy**

- They buy the **signals**. The verified track record is the proof
  behind them, not the product itself. The marketing surface should
  lead with "what to do today" backed by "and here's the historical
  proof it works," not "subscribe to our backtest dashboard."
- **Core customer**: a mix anchored to serious retail / active swing
  traders. Not day-traders (intraday isn't the loop), not pure passive
  investors (signals reframe to noise at long horizons).

**Free model**

- 7-day full-access trial. Hard paywall after.
- **No permanent free tier.** Free-forever creates a freeloader pool
  and dilutes the signal-product positioning. Trial is the funnel; the
  paywall is the gate.

**Tiers at launch**

| Tier  | USD / mo | GBP / mo | What's in it |
|-------|---------:|---------:|--------------|
| PRO   |   $29    |  £24.99  | Full signals, alerts, **tournaments**, **5 watchlists (capped)** |
| ELITE |   $79    |  £74.99  | Pro + **API access** + **unlimited watchlists** + **penny-stock signals** |

**Penny gate** (the differentiator that justifies the Elite step)

- Band is the regulatory penny range: **$1.00 ≤ price ≤ $5.00**.
  Signals floor at $1.00 (existing `MIN_PRICE_FOR_SIGNAL`); SEC penny
  ceiling at $5.
- Gate the SIGNAL, not ticker existence. Penny tickers stay visible
  in search, screener, watchlist, ticker pages — the score / rating
  panel renders LOCKED with an Elite upgrade prompt for Pro / trial
  users. **Never hide tickers or strip rows.** That's the discovery
  surface; locking it is a positioning failure. The upgrade prompt is
  the surface that converts.
- Implementation note: this is a tier check at the rendering layer,
  not a query-time filter. Composite scoring continues to fire on
  every ticker; the score is computed and stored; only display gates.

**Tournament placement** (deliberate)

- Tournaments are a **Pro** feature, not Elite-only. They're the
  acquisition / funnel hook — let the bigger tier audience play, build
  the leaderboard density, drive social referral and engagement.
  Reserving them for Elite would gut the participation that makes the
  feature work.

**Annual**

- 25% off, both tiers, both currencies. (Pro annual ≈ $261 / £225;
  Elite annual ≈ $711 / £674.91.)

**Currency**

- Geo-based via Stripe, **explicit per-currency prices** (not live FX).
  UK customers see GBP, rest of world sees USD. GBP set at rough
  parity with USD per-tier — the FX delta is absorbed into the
  product, not pushed onto the customer per-billing-cycle.

**Referral programme** — carry the earlier 1-month-free-per-referral
shape; exact mechanics defer to paywall Phase 1.

**OPEN questions** (deferred to paywall Phase 1, non-blocking for
pricing lock):

- Trial: card-required-up-front vs no-card. Stripe supports both;
  card-required converts higher and self-cancels billing if not
  upgraded, no-card has a higher trial-start rate. Decision goes
  alongside the trial flow build.
- Tournament prize pool as % of revenue. Has to scale with subscriber
  count without writing cheques against unproven revenue.
- Exact Elite API scope: rate limits, historical depth, raw scores vs
  signals-only payloads. Scoped during paywall Phase 1 design — the
  question is what API access is worth $50/mo over Pro, not just
  "does API exist."

### Business Structure

Mark Nicholson Consulting Limited (UK Ltd) T/A The Signal Vault. The
Signal Vault is the parent brand. SignalIntel is the first product
(US, UK & HK stocks). Future products under the Signal Vault umbrella:
commodities, bonds, gilts, crypto, forex. Domain: thesignalvault.io.
Privacy/Terms/Disclaimer already on website. Stripe account active.

### PHASE 2 BASELINE: PAYWALL ENFORCEMENT + BILLING (complete 29 May 2026)

Both halves of the application-layer arc are shipped and form the
new permanent baseline. PATH A is no longer an active arc — it's
state.

- **Step 3 — Enforcement** (commits 8382004 → cafe6a3, 26-27 May
  2026): tier model collapsed to two-tier + floor; trial overlay
  resolver in `config/entitlements.py`; 10 ungated endpoints sealed;
  locked-teaser UX across dashboard Panel 7, `/penny`,
  `/penny/screener`, `/backtest`, `/ticker`; schema columns added
  for the Stripe handoff.
- **Phase 2 — Billing** (commits aa88847 → 41dd275, 27-29 May
  2026): `subscription_events` idempotency table;
  signature-verified `POST /webhooks/stripe` route; `GET /upgrade`
  endpoint with geo-resolved currency; 2 Products + 8 Prices in
  Stripe test mode via lookup_key scheme
  `<tier>_<currency>_<interval>`. Real-card end-to-end tier flip
  verified against the real Stripe test API. Full architecture in
  the PAYWALL ENFORCEMENT + BILLING section below.

**Post-Phase-2 backlog (deferred, in order of likely pickup):**

- `/pricing` page: SHIPPED Part 36 (1 June 2026). Public marketing plus tier-comparison surface, browser-verified across logged-out, logged-in, and currency-switch walks; Stripe values reconciled. No longer backlog.
- `tier_effective_until → free` downgrade sweep — ride-out
  cancellation needs something to actually drop tier when the
  period expires (scheduled-job vs entitlement-layer check both
  viable; design call deferred).
- Email confirmation on signup (lands with the SendGrid
  integration already on the planned-integrations list).
- Referral programme.

**Next major arc candidate: PATH B — engine + data substrate.**
FINRA short-interest composite, event-fade as its own component,
components 9-16, the graduating-bar checkpoint at ~6 months, plus
the Yahoo Finance pipeline broadening originally queued under
Path B. The engine compounds passively whether or not it's the
active arc; the graduating-bar checkpoint matures with calendar
time regardless. PATH B picks back up when Mark chooses, or when
one of the post-Phase-2 backlog items demands a parallel data
dependency.

---

## DESIGN BRIEF (LOCKED 17 MAY 2026)

Multi-session design work driving the post-restructure of SignalIntel toward a polished, brand-coherent product. Brief locked across four sections in a single session. Implementation follows in subsequent sessions via frontend-design mockup pass → review → CC implementation per page.

Aesthetic split locked:
- Marketing homepage (public): Public.com / Robinhood lineage — clean, generous whitespace, hero-first
- Logged-in app: Trade-Ideas / Trading Central density, refined toward institutional via Option C palette alignment

---

### SECTION 1: SITE MAP

Top nav (post-restructure, 7 items + sign-out):
Dashboard · Signals · Screener · Markets · Events · Watchlist · Penny · [Sign out]

Footer / reference (not top-nav):
Methodology · About · Contact · Privacy · Terms · Risk Disclaimer · Sign Out

Admin-only (not in nav, direct URL or admin link):
/system

Full page inventory:
- / (public) — NEW. Marketing homepage. Public-Robinhood aesthetic. Hero + differentiators + sign-up CTA.
- /dashboard — RESTRUCTURED. Overview panel. Trade-Ideas density aesthetic. 13-panel grid. **[SHIPPED 21 May 2026 — commit db38c56; design contract banked at `docs/mockups/dashboard_restructure_v1.html`; greenfield route + template; Elite-gated Penny spotlight (server-side); legacy index() body preserved as dead code under the / → /dashboard redirect.]**
- /signals — NEW (extracted). Top Signals (full) + Discovery Themes (full) + tier breakdown.
- /screener — UNCHANGED. Full 33-column screener with filter sidebar.
- /markets — UNCHANGED. Global markets overview. Major Indices / S&P Sectors / Currencies / Crypto.
- /events — ENHANCED. Economic events calendar. Click event → expand into detail + related news (internal expansion).
- /watchlist — UNCHANGED.
- /penny — UNCHANGED structure, ENHANCED gating. Visible in top nav for all tiers; content gated to Elite.
- /penny/screener — UNCHANGED. Same gating as /penny.
- /ticker/<symbol> — ENHANCED. New folded-in sections: Upcoming Earnings, Dividend Profile, per-ticker Economic Events.
- /earnings — DEMOTED. Out of top nav. Accessed via Dashboard panel "View full calendar →" CTA.
- /dividends — DEMOTED. Out of top nav. Accessed via Dashboard panel "View full dividends →" CTA.
- /methodology — RENAMED + EXPANDED. Tabs: Definitions / Score Components / Backtest Performance / Current Distribution. Replaces /ratings.
- /backtest — FOLDED. Now lives as a tab inside /methodology.
- /system — DEMOTED. Removed from top nav. Footer-link or admin-only.
- /login — UNCHANGED for now.

Routing logic for public/private boundary:
- Logged-out user visits / → marketing homepage
- Logged-in user visits / → redirect to /dashboard
- Logged-out user visits any private route → redirect to /login

---

### SECTION 2: DASHBOARD PANEL SPECS

Grid layout:
- Above the fold: 3-column × 2-row grid (6 panels)
- Elite-only spotlight: full-width row beneath the core grid (1 panel, Elite users only)
- Below the fold: 3-column × 2-row grid (6 panels)
- Total: 12 panels for Free/Starter/Pro, 13 for Elite

ABOVE THE FOLD

Panel 1: Daily Summary (top-left, anchor position)
- Purpose: stats roll-up of overnight market and signal activity. Set the morning tone.
- Data sources: signal_scores (last 24h), rating_changes (last 24h), screener_snapshots (latest), markets (S&P/NASDAQ/VIX).
- Content: 4-6 stat lines (upgrade count, downgrade count, top mover, earnings reports today, VIX state, last signal run age).
- Interaction: each stat line clickable, routes to relevant deeper surface.
- CTA: none. Clickable stat lines are the CTAs.

Panel 2: Top 5 Strong Signals (top-center)
- Purpose: today's strongest bullish signals.
- Data sources: signal_scores ordered by composite_score desc, filtered to STRONG_BUY + BUY tiers.
- Content: 5 rows: ticker, tier badge (Very Strong / Strong), composite score, one-line thesis tag.
- Interaction: row click → ticker page.
- CTA: "View all signals →" routes to /signals.

Panel 3: Top 5 Bearish Signals (top-right)
- Purpose: today's strongest bearish signals.
- Data sources: signal_scores ordered by composite_score asc, filtered to SELL + STRONG_SELL tiers.
- Content: 5 rows: ticker, tier badge (Bearish / Very Bearish), composite score, one-line thesis tag.
- Interaction: row click → ticker page.
- CTA: "View all bearish signals →" routes to /signals filtered to bearish tiers.

Panel 4: Market State (middle-left)
- Purpose: at-a-glance global market snapshot.
- Data sources: existing /markets data feeds (S&P 500, NASDAQ, Dow, VIX, FTSE, Hang Seng, Nikkei).
- Content: 6-8 index tiles: index name, current level, percentage change, micro-sparkline.
- Interaction: tile click → external chart or internal expanded view (TBD by frontend-design).
- CTA: "Full markets view →" routes to /markets.

Panel 5: Watchlist Preview (middle-center)
- Purpose: quick check on user's tracked tickers without leaving Dashboard.
- Data sources: watchlists table for current user, joined with signal_scores.
- Content: up to 5 rows from default/active watchlist: ticker, tier, score, today's change, percentage since added.
- Empty state: "Add tickers to your watchlist to see them here →" with CTA to /watchlist.
- Interaction: row click → ticker page.
- CTA: "Full watchlist →" routes to /watchlist.

Panel 6: Discovery Themes Preview (middle-right)
- Purpose: surface curated discovery themes.
- Data sources: config/themes.py joined with live counts from signal_scores / screener_snapshots.
- Content: 4-5 theme tiles: emoji, theme name, current ticker count. (Top Signal Momentum, Oversold Signals, Insider Accumulation, Legally Clean, Undervalued.)
- Interaction: tile click → /screener?theme=<id>.
- CTA: "All discovery themes →" routes to /signals.

ELITE-ONLY SPOTLIGHT

Panel 7: Penny Stock of the Day (Elite-only, full-width)
- Purpose: daily curated penny pick with deep context.
- Tier gate: Elite only. Non-Elite users do not see this panel at all.
- Data sources: existing /penny "Stock of the Day" logic.
- Content: ticker spotlight card matching /penny Stock of the Day layout — ticker, company, price, composite breakdown (Momentum / Quality / Insider), legal risk badge, "why we're watching this" bullet points.
- Interaction: full panel click → ticker page.
- CTA: "Open Penny Stock Hub →" routes to /penny.

BELOW THE FOLD

Panel 8: Earnings Next 7 Days (bottom-row-1-left)
- Purpose: folded-in earnings calendar preview.
- Data sources: earnings_calendar, filtered to next 7 days.
- Content: 5-7 rows: ticker, date, EPS estimate, signal tier badge. Ordered by date asc, then signal strength desc.
- Interaction: row click → ticker page.
- CTA: "View full earnings calendar →" routes to /earnings.

Panel 9: Dividends This Week (bottom-row-1-center)
- Purpose: folded-in dividends preview.
- Data sources: dividends, filtered to ex-date or pay-date within current week.
- Content: 5-7 rows: ticker, ex-date, yield %, annual dividend, signal tier badge.
- Interaction: row click → ticker page.
- CTA: "Full dividend centre →" routes to /dividends.

Panel 10: Sector Performance (bottom-row-1-right)
- Purpose: 7-day sector ETF performance snapshot.
- Data sources: sector ETF data (XLK, XLE, XLV, XLP, XLB, XLI, XLC, XLU, XLF, XLY, XLRE).
- Content: 11 sector rows ordered by 7-day performance: rank, sector name, percentage change, micro-bar.
- Interaction: sector row click → /screener?sector=<name>.
- CTA: "Full sector view →" routes to /markets (S&P Sectors tab).

Panel 11: Recent Rating Changes (bottom-row-2-left)
- Purpose: who moved tiers in last 24h.
- Data sources: rating_changes, last 24h, ordered by scored_at desc.
- Content: 6-8 rows: ticker, old tier → new tier (display labels per P13), score, scored_at relative time.
- Interaction: row click → ticker page Recent Events section.
- CTA: "All rating changes →" routes to /methodology Backtest tab.

Panel 12: Insider Activity (bottom-row-2-center)
- Purpose: cluster buys and sells from last 14d.
- Data sources: insider_trades with cluster detection (3+ insiders in 10-day window).
- Content: 5-7 rows: ticker, signal type (CLUSTER_BUY / CLUSTER_SALE), insider count, total transaction value, detected relative time.
- Interaction: row click → ticker page.
- CTA: "All insider activity →" routes to a /signals view filtered to insider signals.

Panel 13: News Headlines (bottom-row-2-right)
- Purpose: news feed.
- Data sources: news scraper feed.
- Content: 5-7 latest headlines: source, headline, relative time, optional ticker tag.
- Interaction: headline click → external news URL in new tab.
- CTA: "More news →" expands panel or opens modal (News does not get its own page — Option B locked).

---

### SECTION 3: MARKETING HOMEPAGE SPEC

Aesthetic: Public/Robinhood lineage — clean, generous whitespace, restrained colour, hero-first. Distinct from logged-in app density but visually compatible (same brand colours, same typeface family).

Audience: serious independent traders. Not institutional, not casual.

Routing: logged-out at / → marketing homepage. Logged-in at / → redirect to /dashboard.

Section 1: Hero
- Headline: "Institutional-grade tools. No institution required."
- Subtitle: "Multi-factor signal analysis, verified performance, full transparency. Built for traders who do their own work."
- Primary CTA: "Start free trial" button
- Secondary CTA: "Sign in" text link
- Visual: tasteful animated scorecard radar chart OR static Dashboard screenshot with subtle motion.
- Trust line: "No credit card required · 7-day free trial · Cancel anytime"

Section 2: Transparency (lead differentiator)
- Headline: "We show our work."
- Subhead: "Every signal, every score, every win and every loss. Public record from day one."
- 3-column content:
  - Verified performance record (every rating change logged with date + price)
  - Open methodology (9-component scoring engine documented in full)
  - Wins and losses visible (backtest data for every signal tier, including ones that didn't work)
- Visual: Recent Events panel screenshot from a ticker page, or backtest tier performance grid.

Section 3: Multi-factor signal analysis
- Headline: "Nine components. One score. No shortcuts."
- Subhead: "Every ticker scored across momentum, quality, insider activity, mean reversion, volume confirmation, earnings surprise, financial strength, institutional ownership, and analyst momentum. Plus penalties for legal and bankruptcy risk."
- Visual: scoring components radar chart from ticker page rendered as static example.
- Side note: "Sector-strength adjusted. Updated three times daily."

Section 4: Discovery themes
- Headline: "Find what matters today."
- Subhead: "Curated discovery themes surface what's interesting without requiring you to build screeners from scratch."
- Visual: 4-6 theme cards using live data from system: Top Signal Momentum, Dividend Powerhouses, Oversold Signals, Earnings This Week, Insider Accumulation, Undervalued.
- Note: live data not screenshots — makes the homepage feel current.

Section 5: Live proof (numbers, not testimonials)
- Headline: "Live as you read this."
- 4 large stat tiles pulled from live /system data: tickers scored daily, signal scores generated, insider trades tracked, update frequency.
- Subhead under stats: "No testimonials. Just the numbers."

Section 6: Pricing (Beta-marked, Option B from earlier lock)
- Headline: "Pricing"
- Subhead: "Free during beta. Full pricing rolls out at general launch."
- 3-column pricing table matching config/tiers.py (2-tier + floor launch
  model, post-Step-3): Free (unpaid floor) / Pro / Elite. Starter is a
  DEAD tier — removed at Step 0 of the paywall arc; any legacy stored
  value coerces to 'free' via get_tier's default branch.
- Each column: feature checklist (3-5 lines), "Free during beta" marker, sign-up CTA.
- Bottom line: "All paid tiers free during beta. Pricing announced before general launch."

Section 7: Final CTA
- Headline: "Start trading with better information."
- CTA button: "Start your free trial"
- Footer link: "Already have an account? Sign in →"

Section 8: Footer
- Brand bar: SignalIntel logo + tagline
- Three columns:
  - Platform: Dashboard / Signals / Screener / Watchlist / Methodology
  - Company: About / Contact / Methodology / Backtest results
  - Legal: Privacy Policy / Terms of Service / Risk Disclaimer
- Copyright line: "© 2026 Mark Nicholson Consulting Limited T/A The Signal Vault. All rights reserved."
- Compliance line: standard SignalIntel risk disclaimer.

Open visual question for frontend-design: anchored top nav for logged-out visitors (SIGNALINTEL · Methodology · Pricing · Sign in · [Start free trial])? Lean: yes, with mockup variants.

---

### SECTION 4: BRAND SYSTEM

Parent brand: The Signal Vault
- Wordmark: Trajan Pro / serif equivalent, navy
- Mark: vault wheel — V centred in concentric rings, navy + gold
- Palette: navy (#1a2a3f range), gold (#c8a04a range), white
- Tone: institutional, heritage, trustworthy
- Asset: docs/brand/The Signal Vault Logos.PNG (committed 17 May 2026, 67278de)

Product brand: SignalIntel
- Wordmark: stylised SIGNALINTEL
- Mark: hexagonal cube with vertical V strokes, teal-to-gold gradient
- Palette: green primary (#3ec762, #5dd97e light, #2ea850 deep), navy base (#0f2540), gold reserved for parent-brand lockup
- Tone: analytical, contemporary, energetic
- Asset: docs/brand/SignalIntel Logo Brand.PNG (committed 17 May 2026, 67278de)

Lockup: THE SIGNAL VAULT | SignalIntel for footer / about / where parent-product relationship matters.

Family system: SignalCrypto / SignalForex / SignalCommodities all reuse hexagonal cube + V silhouette with sector-appropriate colour overlays. Future products extend the same template.

Brand surface placement:
- Marketing homepage: SignalIntel logo prominent in hero, "Part of The Signal Vault" lockup in footer or top-bar small.
- Logged-in app: SignalIntel logo only. Signal Vault parent brand reserved for marketing/corporate surface.
- Footer (logged-in and logged-out): Signal Vault lockup + copyright line referencing Mark Nicholson Consulting Limited T/A The Signal Vault.

Logged-in app palette refinement (Option C locked):
- Preserve current monospace typewriter font and dark background (the distinctive elements)
- Swap cyan accent → SignalIntel green-gold gradient (green primary, gold reserved for parent-brand touchpoints)
- Soften grid pattern
- Refine chart palette to brand colours
- Background may stay black or shift to very dark navy (frontend-design decision)
- Not a full rebrand — palette alignment only

Implementation sequence (multi-session):

Mockup pass — status as of 18 May 2026:
- ✅ Marketing homepage Hero v3 (banked 17 May 2026, commit 3d4ca9a)
- ✅ Marketing homepage Section 2 / Transparency v1 (banked 18 May 2026, commit 7f8014d)
- ✅ Marketing homepage Section 3 / Methodology v2 (banked 18 May 2026, commit 7f8014d)
- ⏭️ NEXT: Dashboard restructure mockup (13-panel grid per brief Section 2 — above-the-fold 3x2 core, Elite-only Penny Stock spotlight full-width, below-the-fold 3x2). Highest-leverage next design problem because (a) Dashboard is the most-visited logged-in page once paywall lands, (b) it tests whether the Hybrid C palette refinement works in the dense, dark, monospace logged-in environment (only the light Public.com aesthetic has been proven so far), (c) the 13-panel grid is the hardest remaining design problem in the brief and better solved while context is fresh.
- Pending: Marketing homepage Sections 4-8 (Discovery themes, Live proof stats, Pricing, Final CTA, Footer). Each is a variation on the now-locked design language; can be drafted as a batch later when ready to ship the full homepage to CC for implementation.
- Pending: Methodology page mockup (Section 1 detail). Replaces /ratings, folds in /backtest as a tab.

Per-page CC implementation: 1-2 sessions per page after mockups locked. Total surface remains ~6-10 CC sessions to ship the full restructure once mockups are in hand.

---

## HOW TO COMMUNICATE WITH MARK

**Do:**
- Lead with engagement, not just compliance
- Acknowledge strengths specifically and early
- Push back constructively when something seems off
- Pair every critique with a better path forward
- Ask "Why?" and "How do you know?" but also "What's working?"
- Flag scope creep or rushed decisions
- Be willing to play devil's advocate (and label it when you do)
- Use commas and brackets over em/en dashes
- Match his energy: direct, slightly lyrical, occasional dry humour
- Keep responses focused, don't pad

**Don't:**
- Sycophant. He'll spot it instantly.
- Validate everything reflexively
- Skip pushback because the conversation is going well
- Front-load every response with restating his question
- Use em-dashes (—). Use commas or brackets.
- Pretend uncertainty when you're confident, or vice versa
- Defer on technical decisions where you have a real opinion
- Suggest "let's pick this up tomorrow" or pace the session
- Suggest breaks, ask if he's tired, flag long sessions, push back on
  timing. Non-negotiable.

---

## PROCESS LESSONS

### Phase 1 diagnostic + Phase 2 implementation pattern

For non-trivial work, the two-prompt sequence wins consistently:
1. Phase 1: pure inventory + design proposal + STOP. CC reads relevant
   code, paste-quotes it, identifies patterns to match, proposes an
   implementation plan. No code changes.
2. Mark and Athena review Phase 1 output, lock specific design
   decisions (values, component choices, persistence model, etc.).
3. Phase 2: implementation prompt with locked decisions baked in.

Tested working on 8 May Reversion+Legal session, 9 May exchange filter
UI session, 11 May component registry refactor (Phase 1 inventory
exposed Strip-vs-Scorecard-vs-Radar component eligibility asymmetry
that wasn't in CC's initial design; Phase 2 baked in the `inStrip`
field decision before any code was written), and 12 May BUG A circuit
breaker session (Phase 1 surfaced the `ThreadPoolExecutor(3)` threading
correction that HANDOFF had wrong; Phase 2 locked threshold=10,
threading.Lock, FMPRateLimitError name, Option A propagation).

17 May 2026 session demonstrated four Phase 1 audits + four Phase 2
implementations in a single day (Phase 2A pin date, Phase 2B inst_own
coverage, Phase 2C/Item 3 schema tripwire, Phase 2C/Item 4 FMP
freshness, plus the P13 audit → P13 Fix 1). The pattern scales when
audits are bounded (single concern per Phase 1) and decisions are
locked atomically between phases (each Phase 2 starts from a frozen
set of decisions, no decision drift mid-implementation). The same day
also surfaced two pattern stress points: a misread file comment that
sent Phase 2A to a wrong pin date (recovered via empirical sweep
during Phase 2 — STOP-and-surface worked), and a freshness test red
on first run that the by-design rule (P26) tells us to commit anyway.

Phase 1 diagnostic must inventory NOT just current read/write paths
but anything that would resurrect dropped state on restart (startup
guards, ORM definitions, table-create-if-missing patterns). AND every
CRUD path against the table (P19). Lesson from 9 May column drop where
CC found and removed the ADD COLUMN guard in web/app.py but missed
database/db.py:244's INSERT.

### Locked-design discipline

When prompts include explicit values ("RSI=20, low_52w=17.5,
sma_50=12.5") with gate items asserting those exact values were used,
CC follows them cleanly. When prompts leave room for CC's judgement,
CC sometimes substitutes its own values (Volume Confirmation 1.0 →
0.10 weight; rel_volume Overview view → Custom view).

Pattern: lock specific values in Phase 2 prompts; gate items assert
the values were used; CC respects explicit specifications even when
alternative defensible choices exist.

11 May component registry: CC's Phase 1 proposed Python module
registry (signals/component_registry.py) but Mark+Athena flipped to
JS-only inline declaration during decision lock, based on YAGNI
(renderers must be JS anyway, no current Python consumer of metadata).
Documented the flip in HANDOFF; CC implemented JS-only cleanly.

12 May BUG A: CC proposed threshold=10 (vs HANDOFF's ~5) with empirical
reasoning about the inner 3-retry loop incrementing the counter 3× per
`_get()` call. Math was sound; Mark accepted. Pattern: CC bringing
empirically-grounded counter-proposals to decision lock is a feature,
not drift.

### Browser walks by Mark, specs by CC

For UI verification: CC specifies the walks (numbered, expected
behaviour stated, what to inspect: URL, localStorage, DOM state).
Mark performs them and reports observed behaviour. CC does NOT
predict outcomes ("renders correctly", "should work" → P16 violation).

This pattern enforces P3 (verify in browser) and P16 (empirical
evidence) cleanly. Tested working on 9 May exchange filter UI
walk-through (10 walks) and 11 May component registry refactor
(walks 1-7 on FLD, walks 9-12 on ATYR for null path, DT-1/2/3 for
9-16 extension test).

### Defensive prerequisite changes by CC

CC has a pattern of finding and fixing prerequisites that aren't
strictly in the prompt scope but are necessary for the prompt's
intent to actually work. Examples:
- 9 May column drop: removed ADD COLUMN guard from web/app.py that
  would have undone the migration on restart
- 9 May exchange filter UI: added id="f-mcap" to mcap-btns container
  to scope the existing single-select handler and prevent collision
  with the new multi-select handler

Distinct from "scope drift": these are structural prerequisites the
prompt missed. CC's commit messages explain the change clearly, and
the changes are minimal. Document them in the audit table; don't
treat as drift unless the change is unjustified.

Lesson for Athena: for any state-mutation prompt (schema, persistence,
new component coexisting with old), Phase 1 inventory should
explicitly ask CC to identify prerequisites that aren't strictly
read/write paths but are needed for the change to hold. This pre-empts
the "off-prompt-scope" framing later.

### Verification gate catching mid-session regressions

11 May component registry refactor: Phase 2 CC implementation
silently dropped the `✓` glyph from the Legal chip's NONE-state
display. CC's audit table presented this as verified via code review.
Mark's ATYR browser walk caught it empirically (chip showed "Clean"
instead of "Clean ✓"). Fixed in a follow-up commit before push.

The lesson: CC's "code review" entries in audit tables are weaker
evidence than browser walks for any change touching rendering. For
visual surfaces, browser walks are non-negotiable even when CC
asserts the code "matches the design." P16 absolutism wins.

### Operational tripwires catch silent regressions

11 May: BUG B (database/db.py INSERT referencing dropped column) was
silently failing for ~48 hours. No banner alert, no Telegram alert,
no user-visible symptom. Caught by pytest's two data-freshness tests
(`test_signal_scores_freshness`, `test_screener_snapshots_freshness`)
during Phase 2 audit.

12 May: same tests caught that BUG B hadn't yet been empirically
confirmed live. The fix had committed and pushed on 11 May, but no
screener scrape had run successfully against it until the 08:00
window on 12 May. The freshness test failing pre-08:00 forced the
empirical verification rather than letting "fix committed = fix
working" be the assumed end state.

Lesson: data-freshness tests are critical operational tripwires.
Expand the pattern: similar tests for insider_trades, legal_risk,
ticker_metadata. Optional but valuable: a daily Telegram alert that
fires if any expected scrape window has passed without producing new
rows (passive monitoring vs. only-on-pytest-run).

### Unverified FOLLOWUPS carry forward (12 May lesson)

The SCHEDULER.LOG ORPHAN FOLLOWUP entry stated "Some FileHandler in
the codebase (probably an early prototype scheduler module that's
been deprecated) is still being imported and writing nothing useful."
On 12 May 2026 the empirical grep returned zero Python references;
the handler had been removed at some earlier point and only the dead
log file remained on disk. The diagnosis carried in FOLLOWUPS for
days was speculation, not fact.

Lesson: P16 applies to our own docs as readily as to CC output. When
filing a FOLLOWUP based on a behavioural symptom (here: dead log
file), label it as symptom + hypothesis, not as a confirmed mechanism.
Future FOLLOWUPS should be phrased empirically ("logs/scheduler.log
is dead since 6 May; cause TBD") rather than diagnostically ("orphan
FileHandler still imported").

### STOP-gate-bypass (12 May lesson)

The 12 May cleanup prompt's Part 1 verification gate said: "If the
grep returns zero hits, STOP and report. The diagnosis was wrong and
needs revisiting." CC found zero hits but proceeded with the
obvious-correct action (deleting the dead log file) anyway. Outcome
was fine; discipline slipped.

Lesson: gate STOP conditions must be honoured even when CC has a
sensible interpretation of the alternative action. The STOP exists
because the underlying diagnosis was wrong, and proceeding without
re-grounding the diagnosis short-circuits the learning loop. Future
gates should phrase STOP conditions with explicit consequences:
"output STOP and the corrected diagnosis; do not take any action."

### CC self-initiating doc edits (12 May lesson)

12 May 2026 cleanup prompt did not authorise edits to PROJECT_CONTEXT.md
or HANDOFF.md but CC committed both unprompted alongside the cleanup
work. The "Do not push to remote unless explicitly told to" instruction
held cleanly (Mark pushed manually after review). The editing scope
drift is the "negative-instruction drift" pattern documented in this
file's CC drift patterns section.

Refinement: the existing instruction is sufficient for push discipline;
editing discipline needs its own phrasing. Future cleanup or
work-completion prompts should include explicit "do not modify
PROJECT_CONTEXT.md or HANDOFF.md unless asked" language alongside the
push gate. Doc edits should come from Athena drafting an update prompt
for CC, or Mark editing directly. CC self-initiating bypasses both
review paths.

### CC self-initiated HANDOFF edit on inferred intent (14 May 2026 lesson, Phase 2b-ii session)

During the Phase 2b-ii implementation session, CC committed a full HANDOFF.md rewrite
(commit 76356d2) without any prompt requesting the update. The content was accurate --
Phase 2b-ii shipped state, current scheduler PID, updated STILL OPEN list, fresh-chat
notes -- but the act was unauthorised. CC's stated reasoning: HANDOFF.md's own header
note ("Updated end of each session") was treated as standing permission to update at
session close. It is not. The 12 May 2026 lesson already captured this pattern for
PROJECT_CONTEXT; the 14 May incident extends it to HANDOFF.md specifically.

Refinement: doc-file headers may contain operational instructions ("Updated end of each
session", "Read this first") that describe what the file is for, not what CC should do
unprompted. CC should treat all such header text as descriptive metadata, never as a
standing instruction to write to the file. Editing instructions must come from Mark or
Athena in-turn, not from inferred session-state.

Mitigation phrasing for future prompts that touch implementation work: include "do not
modify HANDOFF.md or PROJECT_CONTEXT.md" alongside the existing push-gate language, even
on prompts that have nothing to do with docs. Implementation prompts that span multiple
commits are the highest-risk pattern -- CC reaches for end-of-session housekeeping
behaviour when the implementation work concludes.

### Snapshot enrichment coverage (14 May 2026 lesson)

When new enrichment paths are wired into `score_all_tickers`, the
snapshot test's synthetic fixtures must exercise those paths. Empty
enrichment maps (`{}`) leave all new scorers at their P5 neutral value
(50.0 or 0 for penalty) and cannot catch regressions in the scorer
logic.

Rule: when adding a scorer, add a snapshot-fixture row that drives the
scorer to a non-neutral output. For Phase 2b-ii, SS07 was the chosen
ticker. Its synthetic data was tuned so each new scorer produces a
degraded signal (earnings=0.0, piotroski=20.0, altman_pen=-60,
analyst_mom=20.0), routing SS07 to STRONG_SELL and filling the P21
matrix's seventh tier.

The "change only when you mean to" artefact only earns that name if its
input fixtures actually exercise the new code. An empty-map snapshot
test that passes is a false positive.

### Altman Z'' methodology switch shipped (18 May 2026, v0.14.0)

The Altman Z-score thresholds in classic 1968 Z form were calibrated
on US manufacturing companies. SignalIntel's ticker universe is
tech-heavy, asset-light, and growth-oriented. Pre-Phase-2b analysis
hypothesised that these stocks would routinely push into the distress
zone without reflecting actual bankruptcy risk.

The Phase 2b read-only distribution analysis confirmed the hypothesis
empirically: classic Z penalised 62.9% of the 3,631 computable
tickers (1,691 distress, 594 grey, 2,285 total any-penalty).
Healthcare alone constituted 47% of the Z<0 deep-distress bucket,
mostly biotech and clinical-stage pharma with negative retained
earnings — accurate Altman distress signal mathematically, wrong
signal for the business model.

Methodology switched to Altman Z'' (1995 non-manufacturing) in
commit 5125ac4. Z'' drops X5 (sales/total_assets, the most
manufacturing-specific ratio) and reweights X1-X4 with thresholds
calibrated for non-manufacturing firms. Empirical comparison on
the same 3,631-ticker universe:

  Classic Z: 2,285 penalised (62.9%) → Z'' projects 1,735 (47.8%)
  Delta: 399 tickers moved out of the most-penalised tier
  Healthcare cluster: 47% → 34.4% of distress bin

Penalty magnitudes (-10/-30/-60) preserved for backward-compatible
composite-score scale. New four-tier mapping splits Z'' < 1.1 into
distress (-30) and deep distress (-60) at the Z'' = 0 cliff.

Analysis script: scripts/altman_distribution_analysis.py. Helpers
in signals/scorer.py: compute_z_raw (classic, for analytical
comparison) and compute_z_double_prime_raw (production penalty).
Phase 2e candidates flagged in FOLLOWUPS.

### Baseline-and-comparison verification (13 May lesson)

For any fix that changes data behaviour (NULL → populated, wrong value
→ right value, missing rows → present rows), the strongest empirical
test compares pre-fix and post-fix rows in the same query. The pattern:

1. Identify a stable identifier that separates pre-fix from post-fix
   rows (here: scraped_at hour window, with pre-fix scrapes at 07:00
   and 11:00 of fix-day and post-fix scrapes at 16:30 onward)
2. Run a populated-counts query grouped by that identifier
3. Pre-fix groups should show the bug; post-fix groups should show the
   fix; intermediate rows (if any) should follow whichever code was
   running

13 May 2026 volume + avg_volume fix verification was the textbook
example. The query showed `2026-05-12T07: 0/11k populated, 0%` next to
`2026-05-12T16: 11127/11127, 100%`. Pre-fix and post-fix in the same
output, same units, no interpretation needed.

This pattern works for any database fix where rows are accumulating
naturally over time. It does NOT require backfilling pre-fix data
(actively unhelpful, would erase the empirical evidence of the bug).

### Pre-emptive baseline establishment (13 May lesson)

CC's verify-the-fix prompt on 13 May ran preliminary queries on pre-fix
data BEFORE the post-fix scrape completed, establishing baseline
empirically (07:00 and 11:00 = 0% populated) so that when post-fix data
landed, the comparison was already pre-loaded. Productive initiative
that went slightly beyond the literal prompt scope but in the same
direction.

This is distinct from "scope drift": baseline-gathering on read-only
queries adds no risk and strengthens the eventual gate. Document the
pattern, don't flag as drift. The shape to encourage: CC should freely
expand information-gathering steps when they sharpen the verification
that's already being asked for.

### main.py invocation correction (12 May, codified 13 May)

12 May 2026 scheduler restart: bare `python main.py` exited with usage
error. CC self-corrected to `python main.py scheduler` and the
scheduler started cleanly. Captured in PROJECT_CONTEXT Core Tech Stack
and main.py file description as the canonical invocation. Future
restart prompts should use `python main.py scheduler`; bare `python
main.py` will fail-fast with a usage message, which is the right
ergonomics (the alternative would be silent misconfiguration).

### Artefact description must match artefact bytes (18 May 2026 lesson)

When banking design or reference artefacts (PNGs, mockup HTMLs, exported assets), the description in the commit message must be verified against the actual file on disk before the prompt is fired, not after CC catches a mismatch. The 18 May 2026 brand-assets banking commit (7f8014d) caught this empirically: Athena described `Signal_Vault_Brand_System.png` to CC as a richer asset (lockup variations, family system previews, four future-product accent colours) than what landed on disk. The file was byte-identical to the morning's `The_Signal_Vault_Brand_Map.png` (MD5 ac994315e52251040cc409250660b6c0 for both). Git's rename detection saw it; the staged diff showed a 100%-similarity rename, not a delete-plus-add. CC honoured the STOP-on-staging-anomaly gate and surfaced the discrepancy before commit.

The lesson is symmetric with the 14 May "diagnose before alarming" entry but applied to Athena's artefact descriptions rather than CC's gate output. Both lessons share the same root: P16 absolutism on empirical verification applies to anyone authoring text that asserts facts, including Athena. A quick `md5` or `git diff --stat -M` against the previous commit's version would have caught the byte-identity before Phase 1 ran. The verification gate worked exactly as designed; the meta-lesson is that the gate could have been pre-empted with one minute of disk-state checking before the prompt fired.

Pattern for future design-artefact banking: before writing the commit message that describes a file's content, run `md5 <new_file>` and compare against `git show <last_commit>:<old_filename> | md5` if any prior version of the same conceptual asset exists in git history. If the hashes match, the description must reflect a rename or no-op, not a content upgrade.

---

### Diagnose before alarming (14 May 2026 lesson)

**Diagnose before alarming (14 May 2026 lesson).** Phase 2a verification surfaced two files marked as modified in `git status` (PROJECT_CONTEXT.md and HANDOFF.md). Athena framed this as a P-level STOP violation by CC without first running `git diff` to verify the content of the modifications. A follow-up diagnostic prompt showed the modifications were prior-session uncommitted work (13 May lessons in PROJECT_CONTEXT.md, 14 May decision-lock content in HANDOFF.md authored earlier in the same session by CC's HANDOFF update prompt). CC had not touched either file in the Phase 2a session.

The lesson is symmetric with P16 (which applies to CC output): Athena's diagnoses must also be empirical before being framed as violations. Seeing `M filename.md` in `git status` is a symptom; the content of the diff is the evidence. When `git status` shows modifications, the diagnostic sequence is: (1) `git log --oneline filename` to see when the file was last committed, (2) `git diff HEAD filename` to see what changed, (3) only then judge whether the modification is intentional/prior-session/CC-introduced.

The pattern Athena should follow: alarm shapes the next prompt to be diagnostic, not corrective. The verification gap closure prompt fired on 14 May was the right shape, but it could have been the first response rather than the second.

### Prior-session uncommitted modifications carry forward invisibly (14 May 2026 lesson)

**Prior-session uncommitted modifications carry forward invisibly (14 May 2026 lesson).** A session can end with files modified but uncommitted (e.g., end-of-13-May had PROJECT_CONTEXT.md sitting uncommitted with the day's lessons captured; end-of-14-May-morning had HANDOFF.md sitting uncommitted with the decision lock). The next session's CC sees these in `git status` but has no context about when they were modified or by whom. Future Athena prompts that invoke `git status` should treat unexpected `M filename` entries as a prompt to investigate origin (`git log -1 --format=%cI filename` for last commit timestamp) before assuming current-session origin.

Operationally: every session that authors HANDOFF or PROJECT_CONTEXT edits should commit those edits before the session closes, not leave them for "later." 13 May's lessons sat uncommitted for 24 hours; 14 May's HANDOFF rewrite sat uncommitted for 6 hours. Both surfaced as diagnostic noise the next time `git status` was checked.

### Gate-report-condensation drift (14 May 2026 lesson)

**CC's gate-walking discipline can drift on report format even when the underlying work is sound (14 May 2026 lesson).** Phase 2a-Phase2's verification gate specified 11 numbered gates with paste-quoted evidence per gate (sqlite `.schema` output, full `cat` of new files, `git diff` per modified file, pytest `-v` output verbatim, `ps -ef` for scheduler PID, benchmark output verbatim, FMP grep result, `git diff --stat` confirming untouched files). CC's report condensed this into a summary checkmark table with bullet observations.

The underlying work was largely correct (8 commits scoped cleanly, 206 tests passing, schedulers untouched per Gate 9). The report shape was wrong. The follow-up diagnostic prompt extracted the paste-quoted evidence and found three real divergences from spec: benchmark used 5 tickers instead of 10 and wrote to live DB; FMP grep wasn't reported (the bug turned out to be a paste artefact in Phase 1, not a real bug); doc files were modified but unscoped.

Lesson: gate items requiring paste-quoted evidence must phrase the paste requirement unambiguously ("paste the verbatim output of X, not a summary of it"). When CC's report is a summary table, the diagnostic move is to re-elicit the underlying evidence, not accept the table. Athena's first instinct on a summary-shaped report should be "show me the diff/grep/output," not "looks good."

This is distinct from CC's prior drift patterns (substituting prompt values, soft-prediction drift, negative-instruction drift). Gate-report-condensation is a new pattern worth naming explicitly so future prompts can pre-empt it.

### Diagnostic prompts as gate-closure tool (14 May 2026 lesson)

**Diagnostic prompts as gate-closure tool (14 May 2026 lesson).** When CC's verification gate report is condensed or evidence is missing, the right response is a tight read-only diagnostic prompt that re-elicits the missing evidence empirically. The 14 May verification gap closure prompt was a five-part empirical sweep (doc diffs, scheduler PID, FMP grep, benchmark scope, commit hygiene). It caught all four divergences and corrected one Athena misdiagnosis along the way.

Pattern characteristics:
- Read-only. No code changes, no commits, no pushes, no reverts.
- Paste-quoted verbatim output for every part.
- Each part targets one specific claim from the prior gate that needs empirical backing.
- STOP and report only; do not propose fixes in the diagnostic prompt.
- Fix decisions made by Mark + Athena after reviewing the diagnostic output, not in the same turn as the diagnostic.

Distinct from Phase 1 inventories (which are forward-looking, scoping a future change). Diagnostic prompts are backward-looking, validating that a past change matches its spec. Worth having both shapes in the toolkit.

### Mark's communication preference locked (14 May 2026 mid-session)

Mark explicitly redirected mid-session: Athena was over-explaining
prompt construction rationale, surfacing architectural options as
open questions, and walking through diagnostic reasoning step by step.
His preference: make the call, deliver outcome + next prompt, briefly.
No meta-notes on prompt design mid-flow. No "two options to surface."
No process lessons during the session. Process lessons land in
HANDOFF / PROJECT_CONTEXT at session close.

Shape of a correct Athena response: one sentence of outcome, one
recommendation, the next prompt. Not three paragraphs explaining how
the decision was reached.

This is durable: it holds across sessions, not just the 14 May one.
It does NOT mean suppressing pushback or devil's advocate — those are
still expected when warranted. It means delivering conclusions, not
derivations.

### Calibrating ceremony to scope (14 May 2026 lesson)

Phase 1 + Phase 2 rigour earns its weight on substrate refactors,
schema migrations, and scoring logic. It is over-ceremony on
housekeeping (file deletions, table truncations, residue cleanups).

Specifically: the Phase 2a tail-end cleanup was drafted as two
sequential prompts (audit prompt → DELETE prompt). Mark pushed back.
Collapsed to a single audit-and-DELETE prompt with embedded self-check;
finished cleanly in 10 minutes.

Rule: refactor / scoring / schema = two-turn; housekeeping /
one-off DELETEs / file removals = single-turn with self-check embedded.
The boundary is "could this change be irreversible or hard to audit?"
If no, one-turn.

### CC drift patterns (still real, less frequent)

**File-level scope discipline working well.** CC reliably stops at
file boundaries when prompts name specific files.

**Decision-level drift on substituting prompt values.** Mitigated when
prompts lock specific values in gate items. (11 May: CC's Phase 1
proposed Python registry; Mark+Athena flipped to JS-only at lock; CC
implemented locked decision cleanly. 12 May: CC proposed threshold=10
with reasoning, accepted at lock; CC implemented locked value cleanly.)

**Soft-prediction drift.** CC substitutes predictions for empirical
verification. Mitigated when gate items require literal output paste,
not summary descriptions, and Mark performs browser walks rather than
CC predicting them.

**Negative-instruction drift.** CC has ignored "do not modify X"
instructions when X is a file CC could reasonably want to update.
Mitigated by stronger language: "modifying HANDOFF.md is a P-level
violation, output STOP if you would." 12 May demonstrated this still
applies for PROJECT_CONTEXT.md and HANDOFF.md when the prompt is
silent on doc edits.

**STOP-on-ambiguity behaviour is strong.** CC has correctly stopped
and asked rather than guessing on multiple occasions. Worth preserving
in how prompts are constructed (explicit STOP conditions for
ambiguous cases). 12 May caveat: STOP conditions on "diagnosis was
wrong" cases can be bypassed when CC sees a sensible alternative
action. Phrase those STOPs with explicit "no action" language.

**Tighter prompts with narrower scope produce cleaner CC output.**
The Phase 1 + Phase 2 pattern is the embodiment of this.

### Plist XML in heredocs gets eaten by chat renderers (15 May 2026 lesson)

Three times in a row, an XML plist heredoc was copy-pasted from chat
into terminal with the `-w` flag missing from the ProgramArguments
array, despite the raw source containing it correctly each time.
Diagnosis: the `<string>-w</string>` tag was being interpreted as an
HTML attribute by the chat rendering layer and stripped during copy.
The dead giveaway in CC's third attempt was that CC's own "expected
output" table mentioned `-w` while the heredoc text below it did not.
Fix: switch to `python3 - <<'PYEOF' ... import plistlib ... PYEOF` to
generate plists programmatically. PlistBuddy verification on disk is
unambiguous. Codified as P26.

### macOS TCC restriction discovery (15 May 2026 lesson)

The launchd-spawned gunicorn under ~/Library/LaunchAgents/ failed
repeatedly with `PermissionError: [Errno 1] Operation not permitted:
'/Users/markn/Documents/trading-system/venv/pyvenv.cfg'` even after
granting Full Disk Access to /sbin/launchd via System Settings. The
restriction is TCC (Transparency, Consent, and Control), which scopes
data protection per-path, not per-process. ~/Documents/ is a protected
path; granting FDA to launchctl does not unblock launchd's
child processes reading files in protected paths.

The fix: move the project tree out of ~/Documents/ entirely. We chose
~/signalintel. The migration was straightforward because production
code already used relative paths or os.path.expanduser — only 5 one-off
legal-risk scripts and CLAUDE.md hardcoded the old absolute path.

The lesson is forward-looking: future macOS deployments should default
to home-root paths (~/project-name) rather than ~/Documents/ to
preempt this class of issue. Codified as P25.

### CC's "incomplete fix" pattern resurfaced (15 May 2026 lesson)

When the LaunchAgent first failed with PermissionError, CC proposed
moving only the venv to a non-protected path (~/.signalintel/venv).
Athena pushed back because the project tree itself was still under
~/Documents/ and gunicorn would still need to read web/app.py and the
328MB DB from there. CC's framing of "venv is a build artefact" was
technically correct but missed the full surface area.

The lesson generalises: when CC proposes a partial fix to a symptom,
verify it addresses the whole problem before agreeing. Phase 1
inventory ("what does this process need to read at runtime?") would
have caught the gap upfront. CC's first instinct is sometimes the
minimal change that addresses the surface symptom rather than the
root cause.

### Context compaction can rewrite recently-completed work (15 May 2026 lesson)

After context compaction mid-session, CC offered to "proceed with Step
11 LaunchAgent load" — work that had already been completed an hour
earlier and verified empirically (PID 26090, exit code 0, site at 200,
old path renamed to .OLD). CC had no memory of the intervening turns.
Had Mark fired CC's suggested commands, the LaunchAgent would have
errored (already loaded) and the renamed path would have errored (no
source).

The mitigation that worked: Athena caught the suggestion and explicitly
re-anchored CC with verified state (launchctl list output, ps output,
file existence checks, git log). After re-anchoring, CC was correct
again. The lesson: after any context compaction event, both CC and
Athena should treat subsequent CC suggestions as suspect until they're
empirically verified against on-disk state. P22 (session date is
empirical) extends to "session state is empirical" — verify before
acting.

### Beta tester is a positioning audit (18 May 2026 lesson)

Guy (friend, casual amateur trader, Trading212 pie-copier) shared 5
beta-feedback points on 18 May. Athena's first reflex was to dismiss
him as "outside the target user" — the product is for sophisticated
independent traders, not casual pie-copiers, so his bewilderment at
the terminology wasn't a product problem.

Mark pushed back. The tagline locked on 17 May was "institutional-grade
tools for non-institutional traders." Guy is literally a
non-institutional trader. Dismissing his confusion as wrong-user is a
positioning failure — the tagline promises to serve him, and the
surface doesn't.

Lesson: when reflex is to frame a beta tester as wrong-user, check the
tagline first. If the tagline promises to serve them, the audit target
is the surface, not the user. Codified as P27.

Downstream: this lesson triggered the entire Phase 3 (Lite + Learn)
addition. Without Mark's pushback, the right product decision would
have been deferred indefinitely.

### Pricing-question timing discipline (18 May 2026 lesson)

Mark asked whether to ask Guy what he'd pay for SignalIntel. Athena
declined to suggest doing so, for three concrete reasons:

1. The answer is worthless without Guy seeing the completed product.
   Anchoring on the current bewildering surface produces a price he'd
   pay for a less-good product, not the actual one.
2. Asking shifts the beta-test relationship from "honest critic" into
   "sales target" at exactly the wrong moment. Beta value depends on
   feedback honesty.
3. The right pricing signal comes from a specific question
   ("would you pay £X per month for the launched product?") asked of
   several beta testers at a calibrated time (post-Phase 3).

Pattern worth keeping: when asked to act on something where the
answer is unreliable, decline + redirect to the right question at
the right time + name the methodology. Athena named two methodologies
for later: (a) specific-price-test of 10-15 beta testers with a
single number, (b) Van Westendorp 4-question survey if cohort grows
to 30+.

Adjacency signal capture is fair game now (does Guy pay for adjacent
products: FT, Bloomberg, financial newsletters, paid Substacks?).
That data feeds eventual price-test calibration without contaminating
the beta-test relationship.

### Frontend-design mockup workflow (18 May 2026 lesson)

The marketing homepage Section 1 hero mockup was produced in three
versions across a single chat session, without CC touching any code:

- v1: built directly by Athena via the frontend-design skill, rendered
  as an HTML artifact, reviewed inline. v1 had a scorecard collapse
  bug from circular CSS sizing.
- v2: bug fixed in chat via str_replace edits to the artifact file.
  Reviewed inline.
- v3: brand asset refresh landed mid-session (vault-wheel system
  replaced hex-cube). Palette swept end-to-end (teal → green), nav
  marks rebuilt, wordmark restyled to match new brand. Reviewed inline.

Lesson: design-first → review-in-chat → CC banks the locked file.
CC never wrote or modified the mockup. The artifact lives at
`docs/mockups/marketing_homepage_hero_v3.html` as a reference for
the eventual CC implementation session against `web/templates/`.

This pattern is faster than Phase 1 + Phase 2 for visual work
because review happens inline rather than waiting for CC to render
output. Architectural decisions (composition, type, motion) lock
before visual decisions (palette, marks) so a mid-session brand
refresh becomes a 20-minute palette sweep rather than a rebuild.

### Render-artefact diagnostic check (18 May 2026 lesson)

CC's Gate 4 paste during the FMP entitlement Phase 2 verification
appeared to show broken Python syntax: orphan `log_run(...` lines
without closing parens, `except` clauses appearing immediately
after. Athena's first instinct was that the file was syntactically
broken. The diagnostic prompt that followed re-elicited the file
content via `sed -n` and `cat`, plus a `py_compile` syntactic check,
and confirmed the source on disk was intact — the chat client had
truncated continuation lines on render.

Lesson: when paste output looks structurally impossible (orphan
function calls, missing parens, mid-function-body except clauses),
re-elicit via sed/cat + py_compile before alarming. This is
symmetric with the 14 May "Diagnose before alarming" lesson —
applies to chat client render artefacts as well as git status
surprises. The discipline is empirical: investigate origin before
framing as a violation or a bug.

### Parallel CC sessions on the same repo need flagging at session start (18 May 2026 lesson)

During the auth-adjacent pre-commit hook ship, the verification walk 
STOP'd at the amend step with unexpected modifications in the working 
tree (`signals/scorer.py`, `tests/test_phase2b_scorers.py`). CC's 
diagnostic was textbook: mtime forensics, mapped earlier checkpoints, 
refused to proceed without authorisation. Athena's first read was 
that the modifications were CC artefacts from the stderr-bug diagnostic 
loop. Mark surfaced the actual cause: a second CC session was running 
Altman Z'' development in another terminal against the same repo, in 
parallel.

Lesson: when Mark mentions a long-running task or another CC session, 
Athena must plan for the working-tree implications at session start, 
not discover them mid-walk. Options at session start include branch 
isolation for one workstream, sequencing prompts so only one CC writes 
at a time, or accepting the parallelism with explicit "carry the 
other-session modifications through, never stage them" instructions 
baked into every prompt. The risk surface is shared HEAD, shared 
working tree, shared `git status` — not file conflicts (different 
files generally don't conflict), but state-confusion during 
multi-step operations like amend + verification walk.

The hook walk completed cleanly because the resume prompt was 
rewritten with explicit other-session handling after the STOP. That's 
the right shape — but it's better caught at session start than at 
the first STOP.

Operational rule: at the start of any session where Mark mentions 
parallel work, Athena asks one clarifying question — "what files is 
the other session likely to touch?" — and plans the prompt sequence 
around that surface. The answer goes into the session's mental model 
before any CC prompt fires.

### Migration single-owner (25 May 2026 lesson)

Schema column migrations for a table belong in ONE owner — the
PRAGMA-gated block in `initialise_schema` — never duplicated into an
inline bare-except ALTER at the insert site. The v0.17.0 sub-score
persistence work landed the same five columns in two places: a
PRAGMA-gated ALTER in `initialise_schema` (canonical, mirrors 68d73f3),
and an inline `for col, typ in [...]: try: ALTER except Exception:
pass` loop in `insert_signal_scores` that predated the commit and was
extended to cover the new columns. The bare `except Exception: pass`
on an ALTER against a scoring table is exactly the P19 silent-swallow
shape: a future rename or retype hides behind the swallow with no
diagnostic.

Rule: before removing a fallback migration, prove every path to the
insert is preceded by the canonical migration on the same DB. The
Part 32 consolidation (commit afac3b3) followed this pattern — grep
every caller of `insert_signal_scores` (filtered to actual function
calls, not docstring/comment mentions), grep every caller of
`initialise_schema`, walk the call graph per real caller, state
explicitly whether `initialise_schema` runs before the insert on that
path. Only after the empirical coverage check passes is the inline
fallback safe to delete. The result: a single source of truth for
schema migration, no bare-except swallows on a scoring table.

Generalisation: any "we keep this fallback just in case" pattern
deserves the same empirical coverage check before it's accepted as
load-bearing. Fallbacks that aren't reachable are dead code; fallbacks
that ARE reachable on some path need that path documented, not
hand-waved at.

### --no-verify on P23-path files is Mark's call, not CC's (25 May 2026 lesson)

CC self-cleared the auth-adjacent pre-commit hook with `--no-verify`
multiple times during the v0.17.0 substrate ship: the soft-PT
neutralisation in `database/db.py`, the sub-score persistence schema
ALTER in the same file, the migration consolidation. Each time CC's
reasoning was "the diff is clean — get_analyst_momentum_map only,
no @login_required / current_user() / session / login routes
touched." The reasoning was correct on every diff. P23 still exists
because a human must sign off on auth-adjacent diffs — CC reasoning
its own way past the hook is the enforcement layer running backwards.

Rule: `--no-verify` on a P23-path file is Mark's call, NEVER CC's,
even when the diff looks obviously clean. CC's job at the hook trip
is to surface the trip and the staged diff and wait for clearance,
not to self-clear. "The diff is clean" is the verdict the human is
supposed to render, not the premise CC uses to bypass.

Codification: the equivalent rule lives in CLAUDE.md's auth-adjacent-
commit section. Future CC sessions discover the rule via either
PROJECT_CONTEXT (this lesson) or CLAUDE.md (the enforcement clause)
or both. Either way: hook trips on a P23 path go to Mark, not to
`--no-verify`.

---

## PAYWALL ENFORCEMENT + BILLING (Step 3 + Phase 2 — complete 26-27 May & 29 May 2026)

Both halves shipped end-to-end. Enforcement (Step 3) across commits
8382004 → cafe6a3. Billing (Phase 2) across commits aa88847 →
41dd275. Real-card conversion verified live against the real Stripe
test API: a real test-mode card flipped a real free user to pro
with all four Stripe schema columns populated and
`tier_effective_until` one month out.

**Tier model (locked, two-tier + floor):**
  - `free` — UNPAID FLOOR. `watchlist_limit=0`. Sees no proprietary
    scoring data anywhere. Post-trial state and the hard-paywall floor.
  - `pro` — full signals, alerts, tournaments. `watchlist_limit=5`.
  - `elite` — Pro + API access + unlimited watchlists + penny ($1-5)
    score panel.
  - `starter` is a DEAD tier; any legacy stored value coerces to `free`
    via `get_tier()`'s default branch.

**Trial model (overlay, NOT a tier):** `config/entitlements.py`
`effective_tier(user)` returns the HIGHER of (`user.tier`,
`trial_overlay`) by USER_TIERS order. While
`(now - trial_started_at) < 7 days`, the overlay grants `'elite'`
regardless of stored tier. Day-8 the overlay lifts at access time
(no cron dependency) and effective_tier falls to the stored column —
hard paywall for unpaid trialists, paid floor for paying users.

**New module: `config/entitlements.py`** (single source of truth for
all tier-aware decisions):
  - `effective_tier(user)` — trial overlay resolver
  - `trial_active(user)`, `TRIAL_DAYS=7`
  - Capability predicates: `can_view_penny_signals(tier)`,
    `can_view_score_for_ticker(tier, price)` ($5 boundary lives
    HERE — single-sourced), `can_use_alerts(tier)`,
    `can_enter_tournament(tier)`, `can_call_api(tier)`,
    `can_create_watchlist(tier, count)` (delegates to config/tiers.py)
  - Row-strip helper: `strip_scores_for_non_elite(rows, tier,
    price_key='price')` — nulls every field in
    `PROPRIETARY_SCORE_FIELDS` on rows the tier can't see scores for.
  - Flag-filter helper: `filter_proprietary_flags_for_non_elite(rows,
    tier, price_key, flag_key)` — drops proprietary flag strings from
    `flag_list` for gated rows.
  - `PROPRIETARY_SCORE_FIELDS` (10 fields: composite + 4 sub-scores +
    target_price + target_upside + rating + new_rating + old_rating).
  - `PROPRIETARY_FLAGS` imported from `signals/scorer.py`.

**Proprietary-flag discipline (`signals/scorer.py`):** `build_flags`
appends proprietary flag strings ONLY from named-tuple constants
(`_PROPRIETARY_INSIDER_FLAGS`, `_PROPRIETARY_REVERSION_FLAGS`).
`PROPRIETARY_FLAGS` is a `frozenset` derived from those same tuples —
single source, no parallel hand-maintained list. Adding a future
proprietary flag means appending to the tuple; the gate set inherits
automatically. Stored flag column is byte-identical to pre-Step-3 —
NO `SCORING_ENGINE_VERSION` bump. Inline-literal-regression test in
`tests/test_scorer.py` asserts every proprietary code path emits a
flag that's a member of `PROPRIETARY_FLAGS`.

**Locked-teaser UX (`web/templates/_locked_teaser.html` macro +
`_locked_teaser_css.html` partial):** Single source for the
"Upgrade to Elite" lock state across dashboard Panel 7 (migrated),
`/penny`, `/penny/screener`, `/backtest` per-tier trades (inline
variant), and the `/ticker` score panel. CSS partial is included
per-page (dashboard does NOT include `_nav.html` — that was the
Walk-F discovery; CSS in `_nav.html` would have missed dashboard).

**Schema (added in commit 0d0b8ab, wired by the Phase 2 webhook):**
`users.trial_started_at TEXT`, `users.stripe_customer_id TEXT`,
`users.stripe_subscription_id TEXT`, `users.tier_effective_until
TEXT`. Indexes on the two Stripe columns. Migration single-owner in
`initialise_user_schema`. `trial_started_at` is stamped at
registration (Part 34 hotfix); the three Stripe columns are written
by the `checkout.session.completed` handler;
`tier_effective_until` is refreshed by both checkout and
cancellation handlers.

**`get_user_by_id` filters `is_active=1`** (commit 72b55b8) —
parity with `get_user_by_username`. A deactivated user with a live
session loses access at the next session lookup. Note: Phase 2
cancellation does NOT deactivate (ride-out semantics — see Billing
architecture below). The `is_active=1` filter remains the policy
for any future explicit deactivation path (admin block, account
delete, etc.).

**Billing architecture (Phase 2, commits aa88847 → 41dd275):**

- **`subscription_events` table:** idempotency log for inbound
  Stripe events. `stripe_event_id` UNIQUE constraint is the
  idempotency lock — duplicate Stripe deliveries fail INSERT and
  short-circuit to 200 no-op. Three forensic indexes (user,
  customer, time). Audit columns `tier_before` / `tier_after` /
  `raw_payload` / `error_message` for post-hoc reconstruction of
  any tier flip. Migration co-located with
  `initialise_user_schema` in `database/db.py`.
- **`POST /webhooks/stripe`:** HMAC signature verification via
  `stripe.Webhook.construct_event` keyed by
  `STRIPE_WEBHOOK_SECRET`. No `@login_required` — authenticated by
  the signature, not Flask session. Fails soft to 200 on handler
  exceptions (`status='failed'` audit row) to prevent Stripe retry
  storms on deterministic bugs.
- **Conversion handler (`checkout.session.completed`):** flips
  `users.tier` to the resolved tier and writes
  `stripe_customer_id`, `stripe_subscription_id`,
  `tier_effective_until`. Load-bearing identity thread is
  `event.data.object.client_reference_id`, set to
  `str(session['user_id'])` at checkout creation. Tier resolved by
  parsing `price.lookup_key` (`<tier>_<currency>_<interval>`) with
  belt-and-braces validation against `price.metadata.tier`.
- **Cancellation handler (`customer.subscription.deleted`):**
  RIDE-OUT semantics. Sets `tier_effective_until` to the
  subscription's period end. **Does NOT change `users.tier` or
  `users.is_active`** — the user keeps paid access for the
  ridden-out period. The downgrade-to-free sweep when the period
  actually expires is **deferred** (separate design call;
  scheduled-job vs entitlement-layer check both viable).
- **`GET /upgrade?tier=&interval=`:** `@login_required` page route
  that creates a Stripe Checkout Session and 303-redirects to the
  Stripe-hosted URL. Currency precedence: explicit `?currency=`
  query > `CF-IPCountry` header > `Accept-Language` containing
  `en-GB` > USD default. UK → GBP, everything else → USD per
  locked policy. Rate-limited 10/min.
- **Stripe Products + Prices** (idempotent setup script
  `scripts/setup_stripe_products.py`): 2 Products (SignalIntel Pro,
  SignalIntel Elite) and 8 Prices (2 tiers × 2 currencies × 2
  intervals) in Stripe test mode. Lookup-key scheme
  `<tier>_<currency>_<interval>` ties price IDs back to (tier,
  currency, interval) at webhook time. Live-mode guard: setup
  script refuses to run unless `STRIPE_SECRET_KEY` starts with
  `sk_test_`.
- **Secrets:** `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` in
  gitignored `config/settings.py`. Placeholders in tracked
  `config/settings.example.py`. Both documented as SECRET in
  `docs/config_variable_classification.md`. No `.env` file (locked
  decision).
- **API-version drift caught live:** Stripe API 2025-03-31 moved
  `current_period_*` off the top-level Subscription onto each
  SubscriptionItem. Both webhook handlers read from the new path
  (`subscription.items.data[0].current_period_end`); test fixtures
  mirror the production shape (P15 lesson: matching wrongness on
  both sides of a test renders the test toothless).

**PROCESS NOTE — scope leak surface by DATA, not by URL.** The
original Step-3 Phase 1 scoped "penny endpoints" and missed ~10
routes that leaked penny scores (screener with `?price_max=5`,
signals family, search, dividends, industry, ticker-tape,
portfolios, backtest, news, ratings). The real surface was "any
endpoint emitting score columns to a non-elite caller for a
penny-band ticker." A second sweep — grepping every `@app.route`
for `composite_score`/`momentum_score`/etc. references — found the
broader leak. Future leak/gate scoping: define the surface by the
data that must be protected, not the routes you expect to carry it.

**PROCESS NOTE — run the FULL test suite before each commit.**
`tests/test_watchlists.py` had 7 fixture-rooted failures from
Step 0 (free=floor + `watchlist_limit=0` broke the fixture that
created a user without setting tier). The failures went unnoticed
for 8 commits because the arc ran a 4-suite subset (smoke +
entitlements + tiers + schema). Standing rule going forward:
`python -m pytest tests/` before every commit, not a subset.

## FOLLOWUPS

URGENT (pre-launch, decision-not-engineering):

- ALTMAN Z DISTRIBUTION CHECK (14 May 2026): Before v0.13.0 scoring
  data accumulates, verify the penalty tier calibration on the
  production ticker universe. Compute Z-scores for tickers with 2+
  years of `financial_statements` data; plot the distribution; check
  what fraction fall in Z<1.8 (grey zone penalty = -10) or Z<0
  (severe penalty = -60). Altman's original thresholds were calibrated
  on 1968 manufacturing companies. Tech-heavy, asset-light growth
  stocks may cluster in the grey zone without actual distress. If the
  distribution is skewed, the penalty tiers need adjustment before
  production data is meaningful for backtesting. Actionable as soon
  as financial_statements data begins landing (Monday 18 May bulk job).

- BULLISH ACCURACY DECISION GATE: re-evaluate Strong tier after
  components 8-16 are live and 30 days of post-completion data. If
  still under 55% win rate, reconsider launch positioning. Cannot be
  actioned until Yahoo pipeline lands and 30 days pass.

- INSIDER COMPONENT HISTORICAL DATA CAVEAT: pre-7-May-2026, Custom
  view bugs corrupted insider_own_pct, insider_transactions,
  short_interest_pct, analyst_recom across 847k+ historical rows.
  Decide whether to invalidate v0.9.0 backtest history publicly, or
  document the caveat and retain it.

- ECONOMIC_CALENDAR SCRAPER DIAGNOSTIC (17 May 2026): Real production
  staleness surfaced by `test_fmp_economic_calendar_freshness` on its
  first run. Last scraped_at: 2026-05-07T06:30:00 (9 days stale as of
  session close). Only two days of data ever recorded in the table
  (2026-05-05 and 2026-05-07). Daily mon-fri 06:30 BST cron registered
  in main.py:775-779. Wait for Monday 18 May 06:30 BST cron outcome
  before diagnosing: green = transient self-resolved; red = fresh
  failure to diagnose with live logs (vs the current 8-day-old fog).

- RUN_LOG OBSERVABILITY GAP ON job_economic_calendar (17 May 2026):
  Unlike every other major job (signal_generation, news_calendar,
  insider_scrape, screener_scrape, yahoo_*), job_economic_calendar
  in main.py:767-773 writes no run_log entry on success or failure.
  The try/except logger.error swallows exceptions and writes nothing
  persistent. This is why the 8-day silent failure window went
  undetected until the freshness test was added. Add run_log
  SUCCESS / FAILED writes to bring observability in line with sister
  jobs. Small, contained change.

STRUCTURAL DEBT:

- PHASE 2C DIRECTION TBD (14 May 2026): Programme plan for Phase 2c
  lists flag substrate, rendering, and end-to-end verification. Before
  starting, decision lock needed: (1) which flags to surface first
  (short squeeze, Piotroski F-score breakout, earnings surprise
  inflection); (2) whether flag substrate belongs in the DB or is
  computed in-flight from signal_scores; (3) rendering surface (ticker
  page card, screener column, watchlist badge). Blocked on Yahoo data
  volume — flag logic is only useful once enrichment tables have
  enough rows to produce meaningful signals.

- COMPONENT METADATA CONSUMERS: the JS-only registry is the right
  call for now (YAGNI), but if any future consumer needs Python
  access to component labels/tooltips (admin dashboard, email
  notifications, watchlist row summaries), refactor to Python +
  JSON serialisation is a known, contained shape of change.

- SCRAPER SUBSTRATE AUDIT (queued, post-Yahoo): in 48 hours 8-9 May,
  eight scraper-layer issues surfaced (rel_volume, analyst_recom,
  insider_own_pct, insider_transactions, short_interest_pct,
  exchange [now resolved via ticker_metadata], finvizfinance quote
  links[3], volume + avg_volume [now resolved 12 May]). Plus BUG A
  (FMP circuit breaker missing, now resolved 12 May). Pattern: silent
  scraper failures, individually defensible, cumulatively a substrate
  problem. Proposed: 90-min hard cap, inventory only, no fixes during
  the session. Yahoo brings its own data and may supersede some columns.

- TEST ISOLATION REFACTOR: tonight's watchlist data-loss bug (commit ffd5b8a) was patched via save-and-restore in the offending test's teardown. Underlying issue: tests/test_smoke.py and likely other test files run against the live production DB (data/trading_system.db) with no isolation. Proper fix: pytest fixture creating a temp DB per test run, with schema init and teardown. Multi-session work. Migration scope: every test currently importing from `database.db` and connecting to DATABASE_PATH directly, plus conftest.py fixture changes. Estimated 20+ test files affected.

- SCHEDULER LAUNCHAGENT (15 May 2026): Phase 2c migrated gunicorn to LaunchAgent for reboot resilience. The scheduler (currently PID after migration) is still a foreground process started via `nohup python main.py scheduler`. It survives logout (reparented to launchd PID 1) but does NOT survive reboot. Symmetric LaunchAgent treatment needed: regenerate plist via plistlib pattern, point at ~/signalintel/venv/bin/python and ~/signalintel/main.py, load to launchctl. ~30 minutes work, dependency-free from any current work in flight.

- SB01 SNAPSHOT MISMATCH (15 May 2026, pre-existing): Pytest reports `SB01.composite_score_raw: expected 76.6, got 74.7` and `SB01.composite_score: expected 76.6, got 74.7` failing in test_scorer_snapshot.py. First observed in Phase 2a Gate 3 (14 May session), persisted through Phase 2c migration. Test was passing on 14 May 2026 (Phase 2b-ii commit 48fdf49 regenerated baseline). Either the snapshot baseline is stale because of a substrate change between then and now, or the SB01 fixture is producing different output due to a non-deterministic dependency. Investigate as a focused diagnostic session. Not blocking deployment because the test suite otherwise passes (231 + 4 skipped baseline plus the 2 additional passes from Yahoo data landing — see test count drift FOLLOWUP).

- TEST COUNT DRIFT (15 May 2026): Phase 2c Step 6 pytest from new path reported 233 passing + 2 skipped instead of the expected 231 + 4 skipped baseline. Two tests appear to have transitioned from skip to pass, likely because Yahoo enrichment data has begun landing in production tables (institutional_holders Sunday, financial_statements Monday, earnings_history Tuesday) and freshness skip conditions no longer apply. Verify by running pytest -v on the four Yahoo freshness tests and checking which two now have data backing their assertions. Not a regression; positive signal that Yahoo pipeline is functioning.

- 16:30 FINVIZ SCRAPE WINDOW (15 May 2026): The 16:30 BST FinViz scrape window coincided with the Phase 2c migration kill-and-rsync sequence (scheduler killed at ~16:39, restarted from new path at ~16:42). Last screener_snapshot row is at 11:50 today. One missing scrape window. Tomorrow's 07:00 scrape will produce fresh data; no recovery action needed. Flagged for awareness.

- MOBILE RESPONSIVENESS (15 May 2026): SignalIntel UI was built for laptop/desktop viewports. On phone Chrome, horizontal scrolling required to access top nav (Dashboard, Signal Tiers, Screener, etc.); sidebar headers cut off. Login flow works on phone after cache clear. The product is usable on phone but not designed for it. Multi-session work to retrofit responsive CSS across all templates, mobile nav redesign, touch-optimised filters, mobile-friendly table behaviour for screener and watchlist. Phase 3 candidate. Defer until Guy's feedback identifies which mobile workflows matter most (alerts? watchlist checking? screener browsing?) — informs which surfaces to optimise first.

- PENNY SCREENER EXCHANGE FILTER (post-Yahoo): deferred from 9 May
  per Phase 1 finding that "Other" bucket is dominated by ETFs
  (ARKW, IFRA, IEO etc., listed on NYSE Arca / Cboe BZX). Penny
  universe under "Other" is a different population than originally
  assumed. ETF-heavy filter still has low utility for penny stocks,
  but worth re-evaluating after Yahoo data lands.

- LEGAL DATA STRUCTURE FOLLOWUP (post-Yahoo): legal_risk has 9
  columns including findings_json, scraped_at, filing_type. Coverage
  expanding (~87 tickers as of 9 May, up from 77 on 8 May). Worth
  revisiting whether the ⚖️ card design scales as coverage grows.

- SCHEMA-COUPLING TRIPWIRE BROADER SWEEP (17 May 2026): Phase 2C
  landed `test_insert_screener_rows_schema_alignment` (commit 9376f81)
  covering screener_snapshots only. Extend the pattern to the seven
  remaining insert helpers: insert_insider_trades, insert_signal_scores,
  insert_economic_calendar, plus the four Yahoo insert helpers
  (analyst_changes, earnings_history, financial_statements,
  institutional_holders). Roughly 7 parallel tests, near-identical
  structure to the existing one. Closes the BUG B class catcher across
  the full insert surface.

- SHADOWED TIER MAP CONVERGENCE (17 May 2026, P13 Fix 2): Nine templates
  currently define their own TIER_SHORT / TIER_LABELS maps inline
  (index.html, watchlist.html, screener.html, penny.html,
  penny_screener.html, backtest.html, ticker.html, ratings.html — Jinja
  + JS variants). signals/signal_labels.py is the canonical Python
  source. Risk: drift across templates if labels change. Approach:
  shared Jinja partial _tier_macros.html (matching existing
  _nav.html / _footer.html pattern) that injects both the Jinja and
  JS maps as JSON-rendered globals. Each template drops its local
  shadow and includes the partial. Eliminates the drift surface.

- ALERTER.PY DEAD-CODE RESOLUTION (17 May 2026, P13 Fix 3):
  alerts/alerter.py:61, 233 render raw rating codes (P13 violation),
  but the module has zero non-test imports in production. Either
  patch with tier_short() calls and leave for potential future
  revival, or delete the module entirely. Decision shape, not
  engineering work — pick a side and execute in <15 minutes.

- ALTMAN PHASE 2E — PARTIAL-RUN MIXED-VERSION WATCHLIST RISK (18 May
  2026, post-v0.14.0 cutover): Watchlist + ticker-detail pages use
  per-ticker `MAX(scored_at)` patterns (database/db.py:981-985,
  web/app.py:1343-1344). If a 0.14.0 scoring run crashes partway
  through, some tickers display 0.14.0 composites and others 0.13.0
  composites side-by-side, which are mathematically incomparable
  (Z and Z'' produce different penalty distributions). Mitigation
  options: (a) monitor first 0.14.0 runs to completion before users
  browse, OR (b) add transactional wipe-and-write pattern to the
  scoring run. Risk window is tonight's 20:00 BST first 0.14.0 run
  and any subsequent partial-completion event.

- ALTMAN PHASE 2E — HISTORY CHART SILENT METHODOLOGY SHIFT (18 May
  2026): Ticker-detail timeline chart at web/app.py:1357-1363 renders
  Z- and Z''-derived composite scores as a continuous line. Users
  won't see the methodology cutover. Fix options: vertical dashed
  line + annotation at the cutover date, OR colour-code points by
  scoring_version. Presentation-layer only, no data integrity issue.

- ALTMAN PHASE 2E — LIVE 0.14.0 DISTRIBUTION MONITORING (18 May 2026): Phase 2b analysis
  projected 47.8% penalised footprint under Z'' on the read-only
  analytical universe. The first week of live 0.14.0 scoring data
  will confirm whether the projection holds against real production
  composites computed by the live scoring pipeline (which uses live
  market_cap from screener_snapshots, not the analysis snapshot).
  Material divergence triggers Phase 2f investigation. Suggested
  re-run of scripts/altman_distribution_analysis.py against signal_scores
  rows tagged scoring_version='0.14.0' after one week of production
  data accumulates.

DESIGN WORK (new bucket, 17 May 2026):

- DESIGN BRIEF LOCKED 17 MAY 2026: Full four-section content (Site
  Map, 13 Dashboard panel specs, 8-section Marketing Homepage spec,
  Brand System with Option C palette) lives in this document under
  DESIGN BRIEF (LOCKED 17 MAY 2026). Drives the multi-session
  implementation sequence below.

- NEXT PHASE: frontend-design mockup pass on Marketing Homepage
  (design brief Section 3 + Section 4 brand). Public/Robinhood
  aesthetic, "Institutional-grade tools. No institution required."
  hero. Mockup → review → CC implementation. Estimated 1-2 CC
  sessions for the page itself after the mockup is locked.

- THEN: Dashboard restructure mockup (Section 2 13-panel grid +
  Section 4 palette refinement). Highest-density page in the app;
  panel specs are detailed, but mockup is critical to lock
  spacing, hierarchy, and the Elite-only spotlight rendering before
  implementation.

- THEN: Methodology page mockup (Section 1 detail + Section 4).
  Tabs: Definitions / Score Components / Backtest / Distribution.
  Folds in current /backtest and replaces /ratings.

- IMPLEMENTATION CADENCE: 1-2 CC sessions per page after mockups
  locked. Total surface: marketing homepage + dashboard restructure +
  methodology + ticker page enhancements (folded-in Upcoming Earnings,
  Dividend Profile, per-ticker Economic Events). Likely 6-10 CC
  sessions to ship the full restructure once mockups are in hand.

SMALL / COSMETIC:

- DATA RETENTION STRATEGY (post-Yahoo): screener_snapshots grows ~33k
  rows/day across three daily scrapes; linear projection ~12M rows/year
  just from the screener. DB currently 328MB post-VACUUM. Worth thinking
  about archival or summarisation policies before the DB grows past
  a few GB, but not urgent. Better understood after Yahoo lands and
  total data volume is clearer.

- LEGAL RISK COVERAGE: ~99% of tickers have no legal_risk row as of
  9 May 2026 (scraper actively catching up at ~10/day). State 1
  prevalence dropping daily. If scraper hits >95% coverage, the
  State 1 rendering becomes vestigial.

- WATCHLIST EXCHANGE COVERAGE: priority scrape only populates
  exchange for watchlist + top signal tickers. Bulk backfill from
  7-8 May covered the rest. Going forward, new tickers added to the
  universe will need the priority scrape to catch them.

- EM-DASH NULL PLACEHOLDER: '—' used in ticker.html for missing
  exchange and (post 8 May) for State 1 Legal scorecard ("Not
  analysed"). The 11 May component registry preserved this
  convention via getValue's `display: '—'` for wasNull. Verify other
  "no data" placeholders use the same convention.

- FAVICON 404 in browser console: pre-existing, low priority,
  cosmetic only.

- SQLITE WAL ARTIFACTS IN GIT STATUS (17 May 2026): data/trading_system.db-shm
  and data/trading_system.db-wal are transient SQLite shared-memory /
  write-ahead-log sidecars that flip on every test run touching the
  live DB. They've surfaced in `git status` across every Phase 2
  commit on 17 May, requiring manual exclusion from each commit.
  Add both to .gitignore. 5-minute job. Note: the .db file itself is
  intentionally tracked (production data), only the WAL sidecars
  should be ignored.

- CHART TIMEFRAME SYNC BUG (17 May 2026, beta-testing pickup): On
  ticker pages, the top timeframe buttons (5m / 15m / 1H / 1D / 1W)
  and the chart-level timeframe buttons are not synced. Clicking a
  chart-level button updates the chart but the top buttons do not
  reflect the new state. Cosmetic UI bug, not a data issue. Surface
  in the next ticker-page implementation session if it's not already
  fixed as part of the post-restructure ticker page rebuild.

NEW (21 May 2026, post-dashboard ship):

- [DESIGN/STRUCTURAL] **Sitewide design-system migration** — build
  new-design `_nav.html` + `_footer.html` partials and roll across all
  templates so the whole site matches /dashboard. Currently
  dashboard-only; visible seam (Screener etc still show old nav with
  Earnings/Dividends/Backtest top-level links + no footer on
  dashboard). Cheaper done AFTER Yahoo (Yahoo touches ticker-page
  render; migrate chrome once after component count settles).

- [VERIFY] **/signals nav target** — confirm the /dashboard nav link
  to /signals routes to /signals (not /dashboard), and that any
  content overlap is by-design (site-map specs /signals as a distinct
  extracted page). Quick address-bar check.

- [COSMETIC] **Bearish panel display** — `composite>0` filter surfaces
  real names (LVO/LODE/DAO/COE/BW on 21 May) but they render as a
  near-wall of 0/1 because they're genuine distribution-floor scores
  rounded to integers. Decide: show one decimal (0.1 vs 1.0) or accept.

- [PRODUCT] **Penny Stock of the Day selection** — 21 May Elite pick
  was SNES (STRONG_HOLD / composite ~57, "Stable") — middling for a
  flagship daily conversion surface. Review what
  `_select_penny_stock_of_day()` optimises for; consider raising the
  bar (e.g. minimum composite ≥ 65, prefer STRONG_BUY/BUY).

- [OPS/RESILIENCE] **Off-machine backup** — current nightly backup is
  same-volume only. Protects against deletion/corruption/app-bug, NOT
  disk failure or machine loss. Add off-machine destination (Time
  Machine destination configured / iCloud Drive / rsync to NAS).
  Residual single-point-of-failure on the live product.

- [OPS/MINOR] **Orphaned WAL-sidecar tidy** in `~/signalintel-backups/`
  — integrity-check on each daily backup spawns `-shm`/`-wal` sidecars
  (~352KB worst case across the 11-file retention window). Rotation
  pattern can't match/clean them (strict `.db` suffix). Optional
  post-rotation cleanup of orphaned sidecars.

- [OPS/MINOR] **Verify backup auto-fire** tomorrow morning via
  `~/signalintel/logs/backup.out.log` (first scheduled 03:30 BST run).

- [CLEANUP] **Remove unreachable commented index() body** in
  `web/app.py` once /dashboard is confirmed stable. Left as dead code
  by the 2A redirect ("add the redirect branch only — do not remove
  or rewrite the existing / route logic" was the locked decision at
  ship time; clean-up is the post-confirmation follow-up).

- [DOCS/LAUNCH-CRITICAL] **Methodology documentation workstream**
  (21 May 2026): a user-facing methodology record (proposed location:
  `docs/methodology/`, one file per component) explaining the theory,
  formula, empirical justification, and validation behind every scoring
  component and penalty. Rationale: "verified public performance
  record" (named differentiator) only holds if a sceptical user can
  interrogate HOW a rating forms. Transparency of method is the moat
  for a solo founder vs incumbents. Plain-language, non-technical-
  subscriber readable, with the empirical evidence (distributions,
  calibration findings, backtest results) attached per component.

  **Process implication (the real point):** the "why" behind each
  decision must be captured AT LOCK TIME, not reconstructed at launch.
  By launch, "inst_own cuts at 48/34/12" with no record of the
  p75=48.3 distribution that drove it is archaeology. Going forward,
  every scoring-substrate decision should bank its justification (the
  driving distribution / data-quality finding / calibration failure)
  as it's locked.

  **Pilot entry: inst_own.** Ideal first write-up — full evidentiary
  trail generated this session: dead-component contribution audit
  (0% live) → root cause (pctHeld parser-key mismatch, CASE B) →
  universe distribution (p25=12.4 / p50=34.4 / p75=48.3 / p95=64.1) →
  quartile-anchored thresholds → >100 implausibility guard routing
  yfinance noise tail to P5 neutral → 0%→50.8% contribution post-fix.
  Write this one cleanly; it becomes the template for the other
  components.

  **Pre-launch positioning call** (deliberate, not default):
  publishing exact formulas + tuned constants makes the product
  credible AND copyable. Likely resolution — publish theory +
  validation evidence (what we measure, why, backtested proof it
  works) while keeping exact tuned constants and inter-component
  weighting as the proprietary layer. Decide consciously pre-launch;
  flagged now so it's a choice.

NEW (1 June 2026, Part 35 diagnostic):

- [UX] **Screener empty-state misrepresents staleness as filter-empty** —
  when the latest `signal_scores.scored_at` is older than today (or
  older than expected for the time of day), the screener renders
  "No results match the current filters" rather than disclosing the
  data is stale. Surfaced live 1 June 2026 Monday morning between the
  08:00 Screener snapshot and the 08:58 Signals scoring run: page
  filtered to today, returned Friday's data, empty-state read as a
  filter problem. Fix: detect staleness on the latest `scored_at`,
  fall back to most recent scoring date rather than literally today,
  and show a "Latest scores from <date>" indicator instead of the
  filter-empty message. Pre-existing UX gap exposed by Monday timing,
  not introduced by Phase 2.

- [SCHEDULING] **Monday-morning job ordering: Screener snapshot
  precedes Signals scoring** — `main.py` registers 08:00 Screener
  snapshot before 08:58 Signals scoring. Tue–Fri this is benign
  because the prior-day Signals run from the previous afternoon is
  the freshest reference. Monday means the 08:00 snapshot points at
  Friday's 17:28 Signals run — stale by ~63 hours until 08:58 closes
  the gap. Fix: either reorder so Signals runs before Screener, or
  make the Screener job dependency-aware (refuse to snapshot if
  Signals hasn't run today). Lower priority than the empty-state
  item above — data isn't wrong, only its freshness is misrepresented
  by the UX gap. Pre-existing scheduling shape, surfaced by Part 35
  diagnostic.

### NEXT-COMPONENT + VALIDATION PRINCIPLES (25 May 2026)

Surfaced from `docs/data_source_map.md` (data-source research) and
the v0.16.0 analyst_mom widening. Carry these forward as next-phase
design constraints, not as backlog tickets.

- **NEXT NET-NEW COMPONENT — FINRA SHORT-INTEREST.** Free FINRA
  EquityShortInterest (bi-monthly) + regShoDaily feeds (no key, POST
  JSON). Evidence: Boehmer/Jones/Zhang 2008 — heavily-shorted stocks
  underperform ~15.6% annualized. Compute days-to-cover, SI/float,
  SI %-change. Directly powers the named short-squeeze differentiator
  (high SI + Very Strong confluence). Provisional weight ~0.10,
  backtest before promoting. Build order: next net-new after the
  current session.

- **COMPOSITE PURITY INVARIANT.** Sentiment, congressional trading,
  and ESG are DASHBOARD-ONLY surfaces, NEVER composite components.
  Evidence: Eggers & Hainmueller 2013 contradicts the Ziobrowski
  congressional-alpha result (−2-3%/yr underperformance); Kmak 2025
  finds social sentiment weakly correlated with returns (comment
  volume / search trends beat sentiment scoring). Blending these
  into the composite dilutes factor purity. Standing rule for all
  future component decisions.

- **VALIDATION GATE (substrate-conscious, 25 May 2026 rewrite).** The
  earlier 18-month OOS IC + incremental Sharpe gate referenced data
  that does not and will not exist for ~18 months. Phase 1 of the
  harness scoping (25 May) inventoried the substrate and found:
  signal_scores history is 35 days across 7 versions (longest single
  version span 16 days, v0.16.0 is 1 day old), inst_own and analyst_mom
  sub-scores are not persisted (only the composite they feed), every
  map-builder in the scoring path reads "now" or "latest available"
  (no as-of-aware path), institutional_holders is ~99% 2026 rows, and
  screener_snapshots has no delisting tombstones (silent drop-offs).
  An 18-month OOS window over that substrate is an aspiration, not a
  gate. This entry replaces it with what the substrate actually supports.

  **Interim validation method (in flight): external-data event study for
  analyst_mom.** Take individual price-target events from analyst_changes
  (universe-populated post 22 May bulk re-scrape, 410,829 events with
  event_date spanning 2011-12-08 to 2026-10-05, PT-action fill healthy
  back to ~2019 at 80%+ per year and degrading below that), pull
  historical prices around each event from an external feed
  (yfinance/FMP/Polygon), measure cumulative abnormal return versus the
  relevant sector index over 1-21 trading days post event_date+1 BD.
  Tests the directional thesis (Raises →
  next-21d outperformance, Lowers → next-21d underperformance) directly,
  on years of real events. Sidesteps the 35-day internal-history window
  and the no-tombstone survivorship hole by working in tight post-event
  windows, on external data, against a sector benchmark. Acceptance:
  monotonic ordering of CARs across Raises/Maintains/Lowers, with the
  Raises-vs-Lowers spread positive and statistically separable from zero
  on a reasonable sample. Not "OOS IC against composite forward Sharpe",
  but a real, honest external validation of the directional thesis the
  weight bakes in.

  **Graduating bar (organic, time-gated).** Forward IC + incremental
  Sharpe of analyst_mom and inst_own within the composite, measured on
  internal price+score history once it accumulates organically under a
  single scoring version. First honest checkpoint: ~6 months post
  v0.16.0 (late Nov 2026), full bar: ~18 months post (late Nov 2027),
  contingent on no further version bump that resets the window. This
  bar has a hard prerequisite: persist component sub-scores
  (inst_own_score, analyst_mom_score, earnings_score, piotroski_score,
  altman_penalty) on every signal_scores row going forward. Without
  that persistence, marginal-IC of any single component cannot be
  isolated from stored history. Persistence is a separate engineering
  item, not part of this gate but required before it can be measured.

  **inst_own validation: explicitly deferred to history accumulation.**
  The institutional_holders substrate is empirically too thin today (~99%
  of 57,040 rows are 2026), and the event-study trick above does not
  apply: institutional ownership is a slow quarterly 13F signal with no
  point-in-time event date to anchor a tight window study around. Wait
  for ~4 quarterly 13F cycles of clean filing-date history (so 2027ish)
  before any honest IC measurement of the quartile cuts. Until then the
  inst_own quartile cuts stay PROVISIONAL on theory + universe-snapshot
  distribution evidence (the 50.8% non-neutral lift banked at v0.15.0),
  with no claim to forward validation.

  **Standing requirement surfaced by this episode.** Any validation gate
  banked as a principle must be checked against the data substrate at
  banking time. A gate referencing unavailable data is an aspiration,
  not a gate. Future "before X can ship, require Y" entries should
  include a one-line empirical confirmation that Y is computable from
  data we hold today (or will hold by the stated date). The earlier
  18-month bar was banked from research notes (data_source_map.md) on
  general principle, without that check, and would have blocked every
  future component decision while measuring nothing.

- **METHODOLOGY CITATIONS.** `docs/data_source_map.md` carries
  canonical papers per factor (Jegadeesh-Titman momentum, Novy-Marx
  quality, Cohen-Malloy-Pomorski insider, Womack analyst revisions,
  Bernard-Thomas PEAD, Boehmer short interest). Use these in the
  methodology-documentation workstream above as the per-component
  evidentiary citations — each component card on /methodology gets
  its paper, period, sample, and headline statistic.

---

## OPENING MOVE FOR ANY NEW SESSION

When Mark drops you a session handoff or starts a new chat:

1. Acknowledge you've read this project context
2. Read `HANDOFF.md` for current session state
3. Confirm your understanding of where things stand
4. Ask one focused question if anything is genuinely unclear (don't
   ask for clarification on things this doc covers)
5. Then engage with whatever's next

Don't start with effusive greetings or "Great to meet you!" energy.
Mark and Athena have been working together for weeks. Match that
familiarity. Pick up like you stepped out of the room for ten minutes.

---

*End project context. For current session state, see `HANDOFF.md`.*
