> **Session bootstrap.** At the start of any session, read these two files in order before doing anything else:
>
> 1. `PROJECT_CONTEXT.md` — stable project context (Athena's role, SignalIntel overview, 7-tier rating system, P1-P17 invariants, communication norms, roadmap). Rarely changes.
> 2. `HANDOFF.md` — current session state (what's running, inflight, queued, recent session log). Updated every session.
>
> `HANDOFF.md` contains its own update instructions. When Mark says "update the handoff" or similar, follow those instructions exactly. Do not modify `PROJECT_CONTEXT.md` or this file unless explicitly told to.

# SignalIntel — Project Context for Claude Code

> **Before making changes, consult `docs/scoring_invariants.md`** for both data correctness rules (invariants 1–11) and development process rules (P1–P15). These rules apply to every change made in this project.
>
> **For any migration, refactor, or multi-surface change, apply P1.1 (inventory before edit), P1.2 (verify by absence), and P1.3 (audit table, not narrative). These are not optional.**
>
> **When writing tests, apply P15 — every test must articulate what it catches AND what it intentionally ignores. Both examples go in the test docstring.**
>
> **When auditing a config-touching commit for secrets leakage, grep against `docs/config_variable_classification.md` FIRST, not against literal patterns like `TOKEN|API_KEY|PASSWORD|SECRET|CHAT_ID`. Pattern greps miss variables whose names contain none of those keywords (e.g. `ALERT_CONFIG` holds smtp credentials but matches no standard pattern). The classification file is the authoritative enumeration of every tracked config variable and its SECRET/NON_SECRET status.**

## What This Project Is
SignalIntel is a stock signal intelligence web application. Currently used as a personal backtesting and trading signal tool, with a roadmap to launch as a paid SaaS product for serious traders. The AI assistant working on this project is referred to as **Athena**.

## Server & Environment
- **Host:** Mac Mini (local server)
- **Port:** 5001
- **Virtual environment:** `~/signalintel/venv`
- **Activate venv:** `source ~/signalintel/venv/bin/activate`
- **Database:** `data/trading_system.db` (SQLite)
- **Run app:** `python web/app.py`
- **Run scheduler:** `python main.py`

## Project Root
```
~/signalintel/
```

## File Structure
```
trading-system/
├── main.py                          # Scheduler entry point, runs all jobs
├── web/
│   ├── app.py                       # Flask routes and API endpoints
│   └── templates/                   # Jinja2 HTML templates
├── scrapers/
│   └── screener_scraper.py          # FinViz data scraping
├── database/
│   └── db.py                        # SQLite helper functions
├── config/
│   └── constants.py                 # Constants and configuration (NEWS_SCRAPE_TIMES etc.)
└── data/
    └── trading_system.db            # SQLite database
```

## Tech Stack
- **Backend:** Python, Flask
- **Database:** SQLite
- **Templating:** Jinja2
- **Data source:** FinViz (screener + individual quote pages via `finvizfinance` library)
- **Scheduler:** APScheduler (jobs wired in main.py)
- **Frontend:** Vanilla JS + HTML/CSS in Jinja2 templates

## Database Tables
| Table | Purpose |
|---|---|
| `screener_snapshots` | Raw FinViz screener data per ticker, timestamped |
| `signal_scores` | Composite signal scores per ticker per run |
| `insider_trades` | Insider buying/selling activity |
| `rating_changes` | Historical log of rating tier changes with price at change |
| `top_signals_of_day` | Daily top-ranked signals |
| `watchlists` | User watchlist tickers |
| `legal_risk` | SEC EDGAR legal risk scores per ticker |

## Signal Rating System (7 Tiers)
| Rating | Meaning |
|---|---|
| 🟢 Strong Buy | Highest conviction long |
| 🔵 Buy | Positive signal, enter or hold |
| 🟡 Strong Hold | Good fundamentals, no new entry |
| ⚪ Hold | Neutral, watch closely |
| 🟠 Weak Hold | Deteriorating, reduce exposure |
| 🔴 Sell | Exit position |
| ⛔ Strong Sell | High conviction short, get out |

## Composite Score Components
The composite score is built from these sub-scores:
- **MOMENTUM** — price momentum, RSI, SMA signals
- **QUALITY** — fundamentals (P/E, EPS, sector comparison)
- **INSIDER** — insider trade signals
- **REVERSION** — mean reversion signals
- **LEGAL** — SEC EDGAR risk penalty (6-tier classification)

Rating changes are detected and logged immediately after every signal generation run (not as a separate job).

## Scheduler Jobs (main.py)
- Signal scoring runs on schedule and triggers `detect_rating_changes` after every run
- News scraping is configurable via `NEWS_SCRAPE_TIMES` in `config/constants.py`
- 11 jobs registered total

## Key Patterns & Principles
- **Configuration over hardcoding**: times, thresholds, and settings belong in `config/constants.py`
- **Automated fix scripts preferred** over manual edits
- **Commit working code to git** between feature sets as checkpoints
- **FinViz individual ticker page scraping** (`finviz.com/quote.ashx?t=TICKER`) is used for high-priority tickers (watchlist + top signals) for data not available in bulk screener views (e.g. analyst recommendations)

## Planned Integrations (not yet built)
- **SendGrid** — email alerts
- **Stripe** — paywall and subscription management
- **Unusual Whales** — options flow data
- **SEC EDGAR** — legal risk scoring (scraper built, wiring in progress)

## Business Model (Roadmap)
- 7-day full-access trial → hard paywall. No permanent free tier.
- Two tiers at launch (locked 25 May 2026): **Pro** and **Elite**. Starter is dropped; B2B / white-label deferred to Phase 3.
  - **Pro**: $29 / £24.99 per month — full signals, alerts, tournaments, 5 watchlists (capped)
  - **Elite**: $79 / £74.99 per month — Pro + API access + unlimited watchlists + penny-stock signals
- Geo-based dual currency (UK = GBP, rest = USD). Explicit per-currency prices, not live FX conversion.
- Annual billing at 25% discount
- Monthly paper trading tournaments with prize pool (% of subscription revenue)
- Referral programme (1 month free per referral)
- React Native mobile app post-web launch
- Future: UK stocks, crypto, forex, options flow, white label B2B

## Current Development Phase
**Phase 1 (active):**
- [ ] Wire SEC EDGAR legal penalty into composite_score (LEGAL score in breakdown block)
- [ ] Virtual portfolio system with margin calls and bust mechanic
- [ ] Email alerts via SendGrid

**Phase 2 (next):**
- [ ] Stripe paywall
- [ ] Earnings calendar
- [ ] Short squeeze signals
- [ ] Options flow (Unusual Whales)

**Phase 3:**
- [ ] Macro overlay, sector heatmap
- [ ] Monthly tournaments + referral programme
- [ ] Public signal performance record

**Phase 4:**
- [ ] Full launch
- [ ] React Native mobile app
- [ ] Elite API tier
- [ ] White label B2B

## Virtual Portfolio System (design spec)
Margin call mechanic:
- 1x = no margin
- 2x = 50% margin requirement
- 5x = 20% margin requirement
- 10x = 10% margin requirement
- 20x = 5% margin requirement (elite tier only)
- Margin call triggers at 50% of margin requirement
- Warning at 75%
- If user can't cover → position auto-liquidates → if cash goes negative → **BUST**
- Busted portfolios stay visible on leaderboard (💀 marker)

## Key Differentiators
1. Verified public performance record — all signals logged with date + price, wins AND losses visible
2. Monthly paper trading tournaments with real prizes
3. Short squeeze detector — high short interest + STRONG_BUY confluence
4. Legal risk scoring via SEC EDGAR feeds into composite score as penalty

## Scoring Engine Versioning
- **`SCORING_ENGINE_VERSION`** lives in `config/constants.py`
- Every `signal_scores` row and every `rating_changes` row is stamped with the version that produced it
- The `/backtest` page filters all stats by version; a dropdown appears automatically when multiple versions exist in the data
- **Bump policy:**
  - `PATCH` (0.9.0 → 0.9.1): bug fixes that do NOT change scoring output
  - `MINOR` (0.9.0 → 0.10.0): new component added OR weight adjustment
  - `MAJOR` (0.9.x → 1.0.0): engine frozen for production launch
  - `MAJOR` (1.0.0 → 2.0.0): post-launch, breaking changes to scoring methodology
- **⚠ Bump the version BEFORE shipping any change that affects scoring output.** New data tagged with the old version is permanently mis-stamped and will pollute backtest comparisons.

### Before committing scoring changes
- [ ] Did this change affect signal scoring output? If yes, bump `SCORING_ENGINE_VERSION` in `config/constants.py` first.

## Signal Universe Constraints
- **`MIN_PRICE_FOR_SIGNAL = 1.00`** (defined in `config/constants.py`)
- Tickers below this price are excluded from new signal scoring. The filter lives in `signals/scorer.py` — tickers with `price < MIN_PRICE_FOR_SIGNAL` are skipped before any sub-score is computed.
- Existing watchlist entries that fall below threshold are **mark-and-hold**: visible on the watchlist with a greyed "BELOW $1" badge, no new signals generated.
- Rationale: sub-$1 percentage returns are mathematically distorting (penny-stock asymmetry). VEEE at $0.15 was producing +4,380% theoretical returns that are untradeable due to bid-ask spreads and liquidity.
- Threshold is provisional and may be raised. To change it: update `MIN_PRICE_FOR_SIGNAL` in `config/constants.py`, then re-run `scripts/purge_sub_threshold_rating_changes.py` to clean historical data, then re-run `scripts/rebuild_rating_changes.py` to regenerate transitions.

## Signal Terminology: Internal Codes vs Display Labels

Two separate vocabularies exist for the 7-tier signal system. **Never mix them.**

### Internal codes (storage layer)
```
STRONG_BUY  BUY  STRONG_HOLD  HOLD  WEAK_HOLD  SELL  STRONG_SELL
```
- Stored in the database: `signal_scores.rating`, `rating_changes.old_rating`, `rating_changes.new_rating`
- Used in scoring logic, SQL queries, theme/filter comparisons, test assertions
- Produced by `signals/scorer.py`

### Display labels (presentation layer)
```
Very Strong  Strong  Stable  Neutral  Soft  Bearish  Very Bearish
```
- User-facing only — appear in templates, Telegram alerts, and JSON responses to the frontend
- Translated from internal codes via `signals/signal_labels.py`:
  - `tier_label(rating)` → full label e.g. "Very Strong Signal"
  - `tier_short(rating)` → short label e.g. "Very Strong"

### The rule
- Internal codes never appear in user-visible output.
- Display labels never enter the database, queries, or scoring logic.
- When adding new code that touches signals, identify which layer you're in and use the appropriate vocabulary. If you're writing a query or scorer condition, use `STRONG_BUY`. If you're rendering a template or composing a message, call `tier_short()`.

## Per-Watchlist Alert Toggle

- `watchlists_meta.alerts_enabled` (INTEGER, DEFAULT 1) controls whether Telegram alerts fire for a watchlist.
- Users toggle it via `POST /api/watchlists/<id>/toggle_alerts`; the watchlist page shows a 🔔/🔕 bell inline in each tab.
- `get_watchlist_tickers(db_path, alerts_only=True)` returns only tickers from watchlists where `alerts_enabled = 1`. OR semantics: a ticker on multiple watchlists fires alerts if **any** of its containing watchlists has alerts on.
- `get_watchlist_tickers(alerts_only=False)` (default) returns all tickers regardless of alert state — used for non-alert UI surfaces.
- If all watchlists are muted, `alerts_only=True` returns an empty set and no Telegram alerts fire.

## Watchlist-Add UX: Picker

- Watchlist-add is via a shared dropdown picker (`_watchlist_picker.html`), included once in `_nav.html` — available on every page.
- Trigger: any element with class `wl-picker-btn` calling `WlPicker.open(el, ticker)`. Clicking outside or pressing Escape closes it. Only one picker open at a time.
- Picker lists the user's watchlists with per-watchlist checked/unchecked state; each click is an immediate add or remove. Inline "Create new watchlist" expands a form in-place.
- `POST /api/watchlists` accepts an optional `add_ticker` body param — creates the watchlist and adds the ticker in one round trip.
- `GET /api/watchlists/membership?ticker=<TICKER>` returns per-watchlist membership for a single ticker.
- **Watchlist membership set:** pages load a `window._wlAllTickers` Set (either from server-passed JSON or via `GET /api/watchlists/all-tickers`). Picker mutations update this set in-place so re-rendered tables reflect the current state without a reload.
- **Surfaces with WL column:** Screener, Penny Screener, Dashboard (All Signals, Sector drilldown, Insiders, Today's Top 10). Ticker detail page has its own dedicated WL button.
- **Surfaces without WL:** Search results (navigational dropdown, not a data table), Events/Earnings/Dividends (read-only `wl-dot` indicator only), Watchlist page itself (recursive), News, System.

## Content and writing conventions

No em-dashes or en-dashes in prose. The em-dash character (Unicode U+2014) and the en-dash character (Unicode U+2013) must not appear in any prose you write: copy, page titles, headings, comments, docstrings, commit messages, and documentation. In prose use commas, periods, semicolons, colons, or brackets. This is the AI-tell to eliminate and it has no exceptions.

Legitimate typographic uses still must not use those two glyphs, but the replacement must be a deliberate equivalent, never a blank and never a mangled sentence:
- Numeric ranges: use the word 'to' or a hyphen (U+002D), for example '1 to 5' or '0-100'.
- 'No data' cell placeholders: use a hyphen (U+002D) or 'n/a'.

Before committing any file you created or edited, grep it for U+2014 and U+2013. The count of both must be zero. If a match is a genuine numeric range or placeholder, convert it to the deliberate equivalent above. Never delete the surrounding content to make the grep pass.

## Authorisation honesty

Do not claim the user authorised something unless there is an explicit instruction you can point to. Absence of objection is not authorisation, and silence is not authorisation. Do not write "you said proceed" or "you approved this" for anything the user did not explicitly instruct. If you are about to make a behavioural change and have not been told to, surface it and wait. Do not proceed and then describe it as authorised.

## Scope Discipline

CC must not modify code outside the explicit scope of the prompt. If you discover something during the work that seems like it should be fixed, surface it as a finding in your audit table or response. Do not silently include it in the diff.

Diff hygiene matters: a commit titled "X" must contain only changes that implement X. Out-of-scope modifications, even small ones, even helpful ones, must be raised to the user before being made.

This applies especially to security-sensitive areas:
- Authentication and session handling (web/app.py login routes, current_user, session writes)
- Tier checking and access control
- Database schema modifications
- User table modifications

If a prompt's stated scope is "X" and you believe a change to one of these areas would help, STOP and ask. Do not commit the change unprompted.

Origin: BUG-001-REOPENED (7 May 2026). A "watchlist picker UI" commit included an unprompted modification to `current_user()` that hardcoded `tier='elite'` for a specific username, with a comment acknowledging it was wrong ("one-time fixup that also writes to DB"). The change was disclosed in the diff but not raised to the user before commit. Out-of-scope modifications, even when disclosed, violate this principle.

## Pre-commit hook for auth-adjacent changes (P23 mechanical enforcement)

A pre-commit hook (`scripts/git-hooks/pre-commit`, symlinked into
`.git/hooks/pre-commit` via `scripts/install-hooks.sh`) inspects every
staged commit for auth-adjacent changes. If matched, it prints the
staged diff and demands interactive `y/N` confirmation from the
developer's terminal. `N`, empty input, EOF, or any non-interactive
context (CC's shell, CI, scripted commits) blocks the commit with
exit 1.

**What triggers the hook**

File paths (any staged file matching):
- `web/app.py` (sole production auth surface today)
- `config/tiers.py` (tier-key source of truth)
- `tests/conftest.py` (auth-injection fixture)
- Glob fallbacks for future extractions: `web/auth*.py`,
  `web/login*.py`, `web/session*.py`

Diff content (any added/modified line in the staged diff for files
under `web/`, `config/`, `tests/`, `signals/`, `scrapers/`,
`database/`, or `main.py`):
- `current_user`, `@login_required`, `session[`
- `.session_transaction`, `sess[` (test-side session injection)
- `def login(`, `def logout(`, `def register(`, `def authenticate(`,
  `def login_required(`, `def current_user(`
- `def _set_user_tier(`, `def _get_user_tier(`
- `app.route(...)` lines containing `/login`, `/logout`, or `/register`

Files under `scripts/` are excluded from content matching so the
hook does not fire on its own development.

**What CC must do**

Auth-adjacent commits will **always block CC** because CC has no
controlling terminal. This is intentional. The flow is:

1. BEFORE staging an auth-adjacent change, add a row to the commit's
   audit table flagged `AUTH SIDE-EFFECT — REQUIRES REVIEW`. State
   what the side-effect is, why it is necessary, and what
   alternative was considered. (P23.)
2. Surface the audit to Mark in-turn: paste the actual `git diff
   --cached` of the auth-adjacent files into the chat, name the
   side-effect explicitly in plain English, and wait for Mark's
   explicit "approved" or equivalent confirmation. Do not commit
   pending acknowledgement. Surfacing means showing the diff, not
   summarising it.
3. After explicit approval, commit with `git commit --no-verify`.
   The `--no-verify` flag is the audit signal — its presence in
   shell history marks the commit as having bypassed the gate by
   design, not by accident.
4. Never default to `--no-verify` for auth-adjacent commits. The
   decision to bypass comes from Mark, not from CC. **"The diff is
   clean" is NOT a CC self-justification for `--no-verify`** (25 May
   2026 lesson). The hook fires on path-match precisely because P23
   exists for a human to render the verdict — CC reasoning its own
   way past the hook is the enforcement layer running backwards. On
   a hook trip, CC's job is to surface the trip and the staged diff
   and wait for Mark's clearance, not to self-clear because the diff
   looks obviously clean. Even on diffs that ARE empirically clean
   (e.g. a scoring-map change in `database/db.py` with zero
   `current_user()` / `session[` / `@login_required` references),
   the clearance is Mark's call.

**What the hook does NOT do**

It catches *un-escalated changes to auth code*, not logic errors
inside auth code. P23 is a process gate, not a correctness gate.
P17 and the BUG-001 regression tests in `tests/test_smoke.py` are
the correctness layer.

**Installation**

Run `scripts/install-hooks.sh` once after clone. Idempotent. The
hook is symlinked, not copied — updates to
`scripts/git-hooks/pre-commit` take effect immediately without
reinstallation.

**Bypass discipline**

`--no-verify` is the *only* bypass. It is loud (visible in shell
history; visible in the absence of any hook-trace in commit
metadata). Adding a path-exception list to the hook itself is
**not** an acceptable evolution — exceptions belong in audit-table
review, not in the gate's source code.

## Session ergonomics

- **Terminal bell on turn completion.** At the very end of every turn,
  as the final action before returning control, emit a terminal bell
  so Mark hears completion from across the room: run `printf '\a'` (or
  `tput bel`). This applies to every turn in every session, including
  diagnostics, implementations, and short replies. If a turn ends in a
  STOP gate, ring the bell after printing the STOP.

## Notes for Claude Code Sessions
- Always activate the venv before running Python scripts
- SQLite DB path is relative: `data/trading_system.db` from project root
- Flask runs on port 5001
- When editing scrapers, be mindful of FinViz rate limits — add delays between requests
- `rating_changes` table should be populated via `detect_rating_changes()` called after every signal run, not as a standalone job
- Check `config/constants.py` before hardcoding any values
- **Ratings Guide has been removed.** The "Ratings Guide" modal and button no longer exist in the nav. `/ratings` (Rating Tiers page) is the single reference for all rating and scoring information. Do not re-add a Ratings Guide button or modal.
- **Nav bar order** (defined in `web/templates/_nav.html`): Dashboard · Rating Tiers · Screener · Earnings · Dividends · Events · Markets · Watchlist · Backtest · Sign out
