# config/settings.py
# ─────────────────────────────────────────────────
# Central config for the trading system.
# Copy this file to config/settings.py and fill in your values.
# ─────────────────────────────────────────────────

# ── Database ──────────────────────────────────────
DATABASE_PATH = "data/trading_system.db"

# ── Scraping schedule (24h format) ────────────────
SCREENER_SCRAPE_TIMES  = ["08:00", "12:00", "16:30"]   # market open, midday, close
INSIDER_SCRAPE_TIMES   = ["09:00", "17:00"]             # morning + after-hours sweep

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
    "Buy",
    "Sale",
    "Option Exercise",
]

INSIDER_CLUSTER_BUY_COUNT = 3
INSIDER_CLUSTER_DAYS      = 10

# ── Logging ──────────────────────────────────────
LOG_DIR   = "logs"
LOG_LEVEL = "INFO"   # DEBUG | INFO | WARNING | ERROR

# ── Request headers ───────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

REQUEST_DELAY_SECONDS = 2.5
REQUEST_TIMEOUT       = 20

# ── Alert settings ────────────────────────────────
ALERTS_ENABLED = False

ALERT_CONFIG = {
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 465,
    "smtp_user": "",
    "smtp_pass": "",
    "from_addr": "",
    "to_addrs":  [],
}

ALERT_MIN_COMPOSITE_SCORE  = 68.0
ALERT_MIN_CLUSTER_INSIDERS = 5
ALERT_STRONG_BUY_ONLY      = False

NEWS_SCRAPE_TIMES = ["08:30", "17:30"]

# ── Telegram alerts ───────────────────────────────
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID   = ""

# ── Financial Modeling Prep API ───────────────────
FMP_API_KEY = ""

# ── Stripe billing ────────────────────────────────
# STRIPE_SECRET_KEY: from Stripe Dashboard → Developers → API keys.
#   Test mode prefix: sk_test_*  Live mode prefix: sk_live_*
# STRIPE_WEBHOOK_SECRET: from Stripe Dashboard → Developers → Webhooks
#   → endpoint → signing secret. Prefix: whsec_*
# Both stay empty in this tracked template; populate locally in
# config/settings.py (gitignored).
STRIPE_SECRET_KEY     = ""
STRIPE_WEBHOOK_SECRET = ""
