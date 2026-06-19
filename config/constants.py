# config/constants.py
# ─────────────────────────────────────────────────
# Non-secret shared constants for the trading system.
# Secrets (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, FMP_API_KEY)
# live in config/settings.py which is gitignored.
# ─────────────────────────────────────────────────

# ── Database ──────────────────────────────────────
DATABASE_PATH = "data/trading_system.db"

# ── Scraping schedule (24h format) ────────────────
SCREENER_SCRAPE_TIMES  = ["08:00", "12:00", "16:30"]   # market open, midday, close
INSIDER_SCRAPE_TIMES   = ["09:00", "17:00"]             # morning + after-hours sweep
YAHOO_PRIORITY_TIMES   = ["02:00", "02:15"]             # daily Mon-Fri analyst + earnings
YAHOO_BULK_DAYS        = ["sun", "mon", "tue"]          # weekly bulk jobs spread Sun-Tue

# ── FinViz sectors to track (one at a time, Phase 1) ──
SECTORS = [
    "Technology",
    "Healthcare",
    "Financial",
    "Consumer Cyclical",
    "Industrials",
    "Energy",
    "Real Estate",
    "Utilities",
    "Communication Services",
    "Consumer Defensive",
    "Basic Materials",
]

# ── Screener columns to capture ──────────────────
# Full list: ticker, company, sector, industry, country, market cap,
# P/E, price, change, volume and key technicals
SCREENER_COLUMNS = [
    "Ticker", "Company", "Sector", "Industry", "Country",
    "Market Cap", "P/E", "Price", "Change", "Volume",
    "EPS growth this year", "EPS growth next year",
    "Sales growth past 5 years", "Return on Equity",
    "Insider Ownership", "Insider Transactions",
    "Short Interest", "Analyst Recom",
    "RSI (14)", "Rel Volume", "Avg Volume",
    "50-Day SMA", "200-Day SMA",
    "52-Week High", "52-Week Low",
    "Beta",
]

# ── Insider trading filters ───────────────────────
INSIDER_TRANSACTION_TYPES = [
    "Buy",          # open-market purchases (strongest signal)
    "Sale",         # open-market sales
    "Option Exercise",
]

# Flag a cluster buy signal when N insiders buy in X days
INSIDER_CLUSTER_BUY_COUNT = 3
INSIDER_CLUSTER_DAYS      = 10

# ── Logging ──────────────────────────────────────
LOG_DIR   = "logs"
LOG_LEVEL = "INFO"   # DEBUG | INFO | WARNING | ERROR

# ── Request headers (rotate to avoid blocks) ─────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

REQUEST_DELAY_SECONDS       = 2.5   # polite crawl delay between requests
YAHOO_REQUEST_DELAY_SECONDS = 1.0   # yfinance free-tier: ~1.5 req/sec empirical ceiling
REQUEST_TIMEOUT       = 20

# ── Scoring engine version ────────────────────────
# Bump policy:
#   PATCH  (0.9.0 → 0.9.1)  : bug fixes that do NOT change scoring output
#   MINOR  (0.9.0 → 0.10.0) : new component added OR weight adjustment
#   MAJOR  (0.9.x → 1.0.0)  : engine frozen for production launch
#   MAJOR  (1.0.0 → 2.0.0)  : post-launch, breaking changes to scoring methodology
# ⚠  Bump BEFORE shipping any change that affects scoring output.
#    New data tagged with the old version is permanently mis-stamped.
SCORING_ENGINE_VERSION = "0.18.1"
# v0.18.1 (19 June 2026): price-target writer rerouted from the dead FMP path
# to yfinance Ticker.info targetMeanPrice via a dedicated daily priority job.
# PATCH: the fmp_price_targets schema, reader, and target-price blend are
# unchanged, so scoring output is not altered; only the cache source differs.
# v0.18.0 (15 June 2026): score_piotroski made coverage-aware (P5 fix). A
# Piotroski signal whose inputs are absent is now EXCLUDED rather than
# scored as a failed criterion. Below 5 of 9 computable signals returns
# neutral 50.0 (missing data must never penalise, P5); at or above the
# floor the passes are normalised over the present signals and capped at 6
# for partial coverage (only full 9-of-9 coverage reaches the 80.0 top
# tier). Full coverage is the identity case, so previously well-covered
# tickers are unchanged; thinly-reported tickers that were scored sub-
# neutral purely from absent line items now resolve toward neutral.
#
# v0.17.0 (25 May 2026 PM): analyst_momentum soft-action PT contribution
# NEUTRALISED to 0 after failing external event-study validation. The
# v0.16.0 ±0.25 soft weighting (main/reit Raises/Lowers) returned a
# Raises-Lowers 21d CAR spread of -0.79% (t=-3.64, p=2.7e-04) — wrong
# sign, monotonicity inverted, robust across 5/7 years, 10/11 sectors,
# 9/10 firms. Survived beta adjustment. Placebo cohort showed the
# expected positive ordering, confirming the inversion was event-driven.
# Per the OOS gate (commit a56afaa), a provisional weight that fails
# validation is pulled to neutral, NOT sign-flipped on the same test
# that disproved the priors. Hence: hard up/init/down stay at ±1, soft
# main/reit contribute 0. net_momentum reverts to integer-valued (hard
# upgrades - hard downgrades), mathematically equivalent to v0.15.0.
# The scorer's ±0.5 neutral band stays correct on integer net (it's the
# neutral-tier rule on integers, not v0.16-specific). Coverage trade-off:
# v0.16's 13.3% → 20.4% non-neutral lift reverts toward the hard-only
# baseline. The lift was real but pushed the composite the wrong
# direction; less coverage scoring neutrally beats more coverage scoring
# backwards. Event-fade as a separate component (its own theory, its own
# OOS validation) is logged as a future candidate; not folded back into
# analyst_mom (that would launder the failed test into a pass on the
# same data).
#
# v0.17.0 also persists the five component sub-scores (earnings_score,
# piotroski_score, inst_own_score, analyst_mom_score, altman_penalty) on
# every signal_scores row going forward. Pure persistence change (no
# scoring math change); prerequisite for the OOS gate's graduating bar
# of forward IC + incremental Sharpe, ~6mo / ~18mo checkpoints.

# ── Signal universe constraints ───────────────────
# Floor for NEW signals only. Tickers below this price are not scored
# and will not generate new rating_changes entries. Existing watchlist
# entries that drop below threshold remain visible (mark-and-hold) but
# are flagged and receive no new signals.
# Adjust upward if backtest data shows continued distortion.
MIN_PRICE_FOR_SIGNAL = 1.00

# ── Alert thresholds ─────────────────────────────
# ALERTS_ENABLED and ALERT_CONFIG (smtp credentials) live in
# config/settings.py (gitignored) to prevent credential leakage.
# Alert thresholds - only alert when these conditions are met
ALERT_MIN_COMPOSITE_SCORE = 68.0    # minimum score for signal alert
ALERT_MIN_CLUSTER_INSIDERS = 5      # minimum insiders for cluster alert
ALERT_STRONG_BUY_ONLY = False       # True = only alert STRONG_BUY, False = BUY too

NEWS_SCRAPE_TIMES     = ["08:30", "17:30"]          # market open + close

# ── Telegram alerts ───────────────────────────────
# Max individual ticker alerts per scoring run; exceeded → summary message only
TELEGRAM_ALERT_MAX_PER_RUN = 20
