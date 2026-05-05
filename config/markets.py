"""
Market symbol definitions for the /markets page.

Tabs 1-3 (indices, sectors, currencies) use yfinance — 'yf' key.
Tab 4 (crypto) uses TradingView widgets — 'symbol' key.
"""

MAJOR_INDICES = [
    {"label": "S&P 500",                   "yf": "^GSPC"},
    {"label": "Nasdaq Composite",          "yf": "^IXIC"},
    {"label": "Dow Jones",                 "yf": "^DJI"},
    {"label": "CBOE VIX",                  "yf": "^VIX"},
    {"label": "S&P/TSX Canada",            "yf": "^GSPTSE"},
    {"label": "UK 100 (FTSE)",             "yf": "^FTSE"},
    {"label": "DAX Germany",               "yf": "^GDAXI"},
    {"label": "CAC 40 France",             "yf": "^FCHI"},
    {"label": "FTSE MIB Italy",            "yf": "FTSEMIB.MI"},
    {"label": "Nikkei 225 Japan",          "yf": "^N225"},
    {"label": "KOSPI S Korea",             "yf": "^KS11"},
    {"label": "SSE Composite China",       "yf": "000001.SS"},
    {"label": "Shenzhen Component",        "yf": "399001.SZ"},
    {"label": "ASX 200 Australia",         "yf": "^AXJO"},
    {"label": "IDX Composite Indonesia",   "yf": "^JKSE"},
    {"label": "STOXX 50 Europe",           "yf": "^STOXX50E"},
    {"label": "BIST 100 Turkey",           "yf": "XU100.IS"},
    {"label": "S Africa Top 40",           "yf": "^JTOPI"},
    {"label": "Nifty 50 India",            "yf": "^NSEI"},
]

SP_SECTORS = [
    {"label": "Consumer Discretionary",   "yf": "XLY"},
    {"label": "Consumer Staples",         "yf": "XLP"},
    {"label": "Health Care",              "yf": "XLV"},
    {"label": "Industrials",              "yf": "XLI"},
    {"label": "Information Technology",   "yf": "XLK"},
    {"label": "Materials",                "yf": "XLB"},
    {"label": "Real Estate",              "yf": "XLRE"},
    {"label": "Communication Services",   "yf": "XLC"},
    {"label": "Utilities",                "yf": "XLU"},
    {"label": "Financials",               "yf": "XLF"},
    {"label": "Energy",                   "yf": "XLE"},
]

CURRENCIES = [
    {"label": "US Dollar Index (DXY)",    "yf": "DX-Y.NYB"},
    {"label": "Euro / USD",               "yf": "EURUSD=X"},
    {"label": "GBP / USD",                "yf": "GBPUSD=X"},
    {"label": "USD / CHF",                "yf": "USDCHF=X"},
    {"label": "USD / JPY",                "yf": "USDJPY=X"},
    {"label": "USD / CAD",                "yf": "USDCAD=X"},
    {"label": "AUD / USD",                "yf": "AUDUSD=X"},
    {"label": "NZD / USD",                "yf": "NZDUSD=X"},
]

CRYPTO_TOP_10 = [
    {"label": "Bitcoin (BTC)",     "symbol": "BINANCE:BTCUSDT"},
    {"label": "Ethereum (ETH)",    "symbol": "BINANCE:ETHUSDT"},
    {"label": "Tether (USDT)",     "symbol": "BINANCE:USDTUSD"},
    {"label": "BNB",               "symbol": "BINANCE:BNBUSDT"},
    {"label": "Solana (SOL)",      "symbol": "BINANCE:SOLUSDT"},
    {"label": "XRP",               "symbol": "BINANCE:XRPUSDT"},
    {"label": "USD Coin (USDC)",   "symbol": "BINANCE:USDCUSD"},
    {"label": "Dogecoin (DOGE)",   "symbol": "BINANCE:DOGEUSDT"},
    {"label": "Cardano (ADA)",     "symbol": "BINANCE:ADAUSDT"},
    {"label": "TRON (TRX)",        "symbol": "BINANCE:TRXUSDT"},
]
