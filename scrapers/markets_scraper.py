"""
Fetches 90 days of daily OHLC for market indices, sectors, and currencies
using yfinance and stores in the market_history SQLite table.
"""
import logging
import math
import sqlite3
import time

import yfinance as yf

from config.markets import CURRENCIES, MAJOR_INDICES, SP_SECTORS

logger = logging.getLogger(__name__)

ALL_SYMBOLS = (
    [e["yf"] for e in MAJOR_INDICES] +
    [e["yf"] for e in SP_SECTORS] +
    [e["yf"] for e in CURRENCIES]
)


def ensure_table(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS market_history (
            symbol  TEXT NOT NULL,
            date    TEXT NOT NULL,
            open    REAL,
            high    REAL,
            low     REAL,
            close   REAL,
            volume  REAL,
            PRIMARY KEY (symbol, date)
        )
    """)
    conn.commit()
    conn.close()


def _safe_float(v):
    try:
        f = float(v)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None


def scrape_markets(db_path, days=90):
    """
    Fetch `days` days of daily OHLC for all market symbols and upsert into
    market_history. Returns total rows upserted.
    """
    ensure_table(db_path)
    conn = sqlite3.connect(db_path)
    total = 0

    for symbol in ALL_SYMBOLS:
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=f"{days}d", interval="1d")
            if df.empty:
                logger.warning(f"[markets] No data for {symbol}")
                continue

            rows = []
            for idx, row in df.iterrows():
                date_str = idx.strftime("%Y-%m-%d")
                close = _safe_float(row.get("Close"))
                if close is None:
                    # Forming/partial bar (e.g. pre-close NaN from a same-day
                    # fetch): do not persist a NULL-close row, it would blank
                    # the dashboard Market State tile for that symbol.
                    logger.debug(f"[markets] {symbol}: skipping {date_str} row, close is None")
                    continue
                rows.append((
                    symbol,
                    date_str,
                    _safe_float(row.get("Open")),
                    _safe_float(row.get("High")),
                    _safe_float(row.get("Low")),
                    close,
                    _safe_float(row.get("Volume")),
                ))

            conn.executemany("""
                INSERT OR REPLACE INTO market_history
                    (symbol, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, rows)
            conn.commit()
            total += len(rows)
            logger.info(f"[markets] {symbol}: {len(rows)} rows upserted")
            time.sleep(0.3)

        except Exception as e:
            logger.error(f"[markets] Error fetching {symbol}: {e}")

    conn.close()
    logger.info(f"[markets] Scrape complete — {total} rows total")
    return total
