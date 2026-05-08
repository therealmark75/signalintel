"""
Creates the ticker_metadata table and backfills exchange from screener_snapshots.
Idempotent: safe to re-run. Re-running won't overwrite existing rows (INSERT OR IGNORE).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.constants import DATABASE_PATH
from database.db import get_connection


def run(db_path=DATABASE_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS ticker_metadata (
            ticker        TEXT PRIMARY KEY,
            exchange      TEXT,
            first_seen_at TEXT NOT NULL,
            updated_at    TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_ticker_metadata_exchange
            ON ticker_metadata(exchange);
    """)

    cur.execute("""
        INSERT OR IGNORE INTO ticker_metadata (ticker, exchange, first_seen_at, updated_at)
        SELECT
            ticker,
            exchange,
            MIN(scraped_at) AS first_seen_at,
            MAX(scraped_at) AS updated_at
        FROM screener_snapshots
        WHERE exchange IS NOT NULL
        GROUP BY ticker;
    """)

    conn.commit()
    count = cur.execute(
        "SELECT COUNT(*) FROM ticker_metadata WHERE exchange IS NOT NULL"
    ).fetchone()[0]
    conn.close()
    print(f"ticker_metadata: {count} tickers with exchange populated.")


if __name__ == "__main__":
    run()
