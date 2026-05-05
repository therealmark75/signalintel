"""
Market symbol definitions for the /markets page.

Tabs 1-3 (indices, sectors, currencies) use yfinance — 'yf' key.
Tab 4 (crypto) uses TradingView widgets — 'symbol' key.
All entries carry a 'tv' key for the full TradingView Advanced Chart page.
"""

MAJOR_INDICES = [
    {"label": "S&P 500",             "yf": "^GSPC",      "tv": "TVC:SPX"},
    {"label": "Nasdaq Composite",    "yf": "^IXIC",      "tv": "TVC:IXIC"},
    {"label": "Dow Jones",           "yf": "^DJI",       "tv": "TVC:DJI"},
    {"label": "CBOE VIX",            "yf": "^VIX",       "tv": "CBOE:VIX"},
    {"label": "S&P/TSX Canada",      "yf": "^GSPTSE",    "tv": "TSX:TSX"},
    {"label": "UK 100 (FTSE)",       "yf": "^FTSE",      "tv": "TVC:UKX"},
    {"label": "DAX Germany",         "yf": "^GDAXI",     "tv": "XETR:DAX"},
    {"label": "CAC 40 France",       "yf": "^FCHI",      "tv": "EURONEXT:PX1"},
    {"label": "FTSE MIB Italy",      "yf": "FTSEMIB.MI", "tv": "TVC:FTMIB"},
    {"label": "Nikkei 225 Japan",    "yf": "^N225",      "tv": "TVC:NI225"},
    {"label": "KOSPI S Korea",       "yf": "^KS11",      "tv": "TVC:KOSPI"},
    {"label": "SSE Composite China", "yf": "000001.SS",  "tv": "SSE:000001"},
    {"label": "ASX 200 Australia",   "yf": "^AXJO",      "tv": "ASX:XJO"},
    {"label": "STOXX 50 Europe",     "yf": "^STOXX50E",  "tv": "TVC:SX5E"},
    {"label": "Nifty 50 India",      "yf": "^NSEI",      "tv": "NSE:NIFTY"},
]

SP_SECTORS = [
    {"label": "Consumer Discretionary",  "yf": "XLY",  "tv": "AMEX:XLY"},
    {"label": "Consumer Staples",        "yf": "XLP",  "tv": "AMEX:XLP"},
    {"label": "Health Care",             "yf": "XLV",  "tv": "AMEX:XLV"},
    {"label": "Industrials",             "yf": "XLI",  "tv": "AMEX:XLI"},
    {"label": "Information Technology",  "yf": "XLK",  "tv": "AMEX:XLK"},
    {"label": "Materials",               "yf": "XLB",  "tv": "AMEX:XLB"},
    {"label": "Real Estate",             "yf": "XLRE", "tv": "AMEX:XLRE"},
    {"label": "Communication Services",  "yf": "XLC",  "tv": "AMEX:XLC"},
    {"label": "Utilities",               "yf": "XLU",  "tv": "AMEX:XLU"},
    {"label": "Financials",              "yf": "XLF",  "tv": "AMEX:XLF"},
    {"label": "Energy",                  "yf": "XLE",  "tv": "AMEX:XLE"},
]

CURRENCIES = [
    {"label": "US Dollar Index (DXY)", "yf": "DX-Y.NYB",  "tv": "TVC:DXY"},
    {"label": "Euro / USD",            "yf": "EURUSD=X",  "tv": "FX:EURUSD"},
    {"label": "GBP / USD",             "yf": "GBPUSD=X",  "tv": "FX:GBPUSD"},
    {"label": "USD / CHF",             "yf": "USDCHF=X",  "tv": "FX:USDCHF"},
    {"label": "USD / JPY",             "yf": "USDJPY=X",  "tv": "FX:USDJPY"},
    {"label": "USD / CAD",             "yf": "USDCAD=X",  "tv": "FX:USDCAD"},
    {"label": "AUD / USD",             "yf": "AUDUSD=X",  "tv": "FX:AUDUSD"},
    {"label": "NZD / USD",             "yf": "NZDUSD=X",  "tv": "FX:NZDUSD"},
    {"label": "Euro / GBP",            "yf": "EURGBP=X",  "tv": "FX:EURGBP"},
    {"label": "Euro / AUD",            "yf": "EURAUD=X",  "tv": "FX:EURAUD"},
    {"label": "Euro / CAD",            "yf": "EURCAD=X",  "tv": "FX:EURCAD"},
    {"label": "Euro / JPY",            "yf": "EURJPY=X",  "tv": "FX:EURJPY"},
    {"label": "GBP / JPY",            "yf": "GBPJPY=X",  "tv": "FX:GBPJPY"},
    {"label": "GBP / AUD",            "yf": "GBPAUD=X",  "tv": "FX:GBPAUD"},
    {"label": "AUD / JPY",            "yf": "AUDJPY=X",  "tv": "FX:AUDJPY"},
]

CRYPTO_TOP_10 = [
    {"label": "Bitcoin (BTC)",   "symbol": "BINANCE:BTCUSDT",  "tv": "BINANCE:BTCUSDT"},
    {"label": "Ethereum (ETH)",  "symbol": "BINANCE:ETHUSDT",  "tv": "BINANCE:ETHUSDT"},
    {"label": "Tether (USDT)",   "symbol": "BINANCE:USDTUSD",  "tv": "BINANCE:USDTUSD"},
    {"label": "BNB",             "symbol": "BINANCE:BNBUSDT",  "tv": "BINANCE:BNBUSDT"},
    {"label": "Solana (SOL)",    "symbol": "BINANCE:SOLUSDT",  "tv": "BINANCE:SOLUSDT"},
    {"label": "XRP",             "symbol": "BINANCE:XRPUSDT",  "tv": "BINANCE:XRPUSDT"},
    {"label": "USD Coin (USDC)", "symbol": "BINANCE:USDCUSD",  "tv": "BINANCE:USDCUSD"},
    {"label": "Dogecoin (DOGE)", "symbol": "BINANCE:DOGEUSDT", "tv": "BINANCE:DOGEUSDT"},
    {"label": "Cardano (ADA)",   "symbol": "BINANCE:ADAUSDT",  "tv": "BINANCE:ADAUSDT"},
    {"label": "TRON (TRX)",      "symbol": "BINANCE:TRXUSDT",  "tv": "BINANCE:TRXUSDT"},
]
