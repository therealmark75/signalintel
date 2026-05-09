"""
Idempotent migration: drop screener_snapshots.exchange column.

The exchange column has been 100% NULL since ticker_metadata.exchange became
the canonical source. The ADD COLUMN guard in web/app.py was removed alongside
this migration to prevent the column being re-added on server restart.

Safe to re-run: exits cleanly if column doesn't exist.
Requires SQLite >= 3.35.0 (ALTER TABLE ... DROP COLUMN).
"""
import sqlite3
import sys
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "trading_system.db")

def main():
    conn = sqlite3.connect(DB_PATH)
    try:
        cols = [row[1] for row in conn.execute("PRAGMA table_info(screener_snapshots)")]
        if "exchange" not in cols:
            print("exchange column not present — nothing to do.")
            return

        print(f"exchange column found — {cols.index('exchange')+1}/{len(cols)} columns")
        conn.execute("ALTER TABLE screener_snapshots DROP COLUMN exchange")
        conn.commit()
        cols_after = [row[1] for row in conn.execute("PRAGMA table_info(screener_snapshots)")]
        assert "exchange" not in cols_after, "DROP failed: column still present"
        print(f"Done. screener_snapshots now has {len(cols_after)} columns: {cols_after}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
