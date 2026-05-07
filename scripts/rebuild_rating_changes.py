"""
scripts/rebuild_rating_changes.py
─────────────────────────────────
Rebuild rating_changes from scratch using clean signal_scores data.

Rules:
  - Only genuine rating transitions are logged (consecutive rows per ticker
    where the rating changed).
  - The first signal_scores row for each ticker is NOT a transition (no prior
    state exists), so it is skipped.
  - Price is resolved from screener_snapshots: the closest snapshot scraped
    at or before the transition's scored_at.
  - Idempotent: running twice produces the same final state (truncate +
    rebuild each time).
  - Runs in a single transaction; rolls back on any error.
  - After rebuild, updates the detect_rating_changes watermark in
    scheduler_meta so the guard doesn't re-fire for already-processed data.

Usage:
  python scripts/rebuild_rating_changes.py
  python scripts/rebuild_rating_changes.py --db path/to/trading_system.db
"""

import sys
import sqlite3
import argparse
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("rebuild_rating_changes")


def rebuild(db_path: str) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    stats = {}

    try:
        # ── Pre-rebuild counts ───────────────────────────────────────
        cur.execute("SELECT COUNT(*) AS n FROM rating_changes")
        stats["rows_before"] = cur.fetchone()["n"]

        cur.execute("SELECT COUNT(*) AS n FROM signal_scores")
        stats["signal_rows"] = cur.fetchone()["n"]

        cur.execute(
            "SELECT MIN(DATE(scored_at)) AS oldest, MAX(DATE(scored_at)) AS newest,"
            " COUNT(DISTINCT ticker) AS tickers FROM signal_scores"
        )
        r = cur.fetchone()
        stats["signal_date_range"] = f"{r['oldest']} → {r['newest']}"
        stats["signal_tickers"] = r["tickers"]

        cur.execute("SELECT MAX(scored_at) AS max_ts FROM signal_scores")
        stats["watermark"] = cur.fetchone()["max_ts"]

        logger.info(
            "signal_scores: %d rows, %d tickers, %s",
            stats["signal_rows"],
            stats["signal_tickers"],
            stats["signal_date_range"],
        )
        logger.info(
            "rating_changes rows before truncation: %d", stats["rows_before"]
        )

        # ── Truncate ─────────────────────────────────────────────────
        cur.execute("DELETE FROM rating_changes")
        logger.info("rating_changes truncated")

        # ── Walk signal_scores per ticker, oldest→newest ─────────────
        # Fetch all (ticker, scored_at, rating, composite_score) in one shot,
        # ordered so we can iterate with a simple prev-state tracker.
        cur.execute("""
            SELECT ticker, scored_at, rating, composite_score
            FROM signal_scores
            ORDER BY ticker, scored_at
        """)
        rows = cur.fetchall()

        transitions = []
        prev_ticker = None
        prev_rating = None

        for row in rows:
            ticker = row["ticker"]
            rated_at = row["scored_at"]
            rating = row["rating"]
            score = row["composite_score"]

            if ticker != prev_ticker:
                # New ticker — first row, no prior state, skip
                prev_ticker = ticker
                prev_rating = rating
                continue

            if rating != prev_rating:
                transitions.append({
                    "ticker": ticker,
                    "old_rating": prev_rating,
                    "new_rating": rating,
                    "scored_at": rated_at,
                    "composite_score": score,
                })

            prev_rating = rating

        logger.info("Detected %d genuine transitions", len(transitions))

        # ── Resolve prices from screener_snapshots ───────────────────
        # Build a lookup: for each transition find the screener row with
        # the latest scraped_at that is ≤ the transition's scored_at.
        # We do this in Python (one query per transition) — acceptable for
        # a one-shot script over ~few-thousand transitions.
        inserted = 0
        for t in transitions:
            cur.execute("""
                SELECT price FROM screener_snapshots
                WHERE ticker = ?
                  AND scraped_at <= ?
                ORDER BY scraped_at DESC
                LIMIT 1
            """, (t["ticker"], t["scored_at"]))
            price_row = cur.fetchone()
            price = price_row["price"] if price_row else None

            change_date = t["scored_at"][:10]  # DATE portion only

            cur.execute("""
                INSERT INTO rating_changes
                    (ticker, old_rating, new_rating, price_at_change, change_date, composite_score)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                t["ticker"],
                t["old_rating"],
                t["new_rating"],
                price,
                change_date,
                t["composite_score"],
            ))
            inserted += 1

        stats["rows_after"] = inserted

        # ── Count unique tickers with ≥1 transition ──────────────────
        stats["tickers_with_transitions"] = len({t["ticker"] for t in transitions})

        # ── Advance watermark ────────────────────────────────────────
        if stats["watermark"]:
            cur.execute("""
                INSERT INTO scheduler_meta (key, value)
                VALUES ('rating_changes_watermark', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (stats["watermark"],))
            logger.info("Watermark advanced to %s", stats["watermark"])

        conn.commit()
        logger.info("Rebuild committed successfully")

    except Exception as e:
        conn.rollback()
        logger.error("Rebuild FAILED — rolled back: %s", e)
        raise
    finally:
        conn.close()

    return stats


def main():
    parser = argparse.ArgumentParser(description="Rebuild rating_changes from signal_scores")
    parser.add_argument("--db", default="data/trading_system.db", help="Path to SQLite DB")
    args = parser.parse_args()

    logger.info("Starting rating_changes rebuild from: %s", args.db)
    stats = rebuild(args.db)

    print("\n" + "=" * 55)
    print("REBUILD REPORT")
    print("=" * 55)
    print(f"  signal_scores rows      : {stats['signal_rows']:,}")
    print(f"  signal_scores tickers   : {stats['signal_tickers']:,}")
    print(f"  signal_scores date range: {stats['signal_date_range']}")
    print(f"  rating_changes before   : {stats['rows_before']:,}")
    print(f"  rating_changes after    : {stats['rows_after']:,}")
    print(f"  tickers with transitions: {stats['tickers_with_transitions']:,}")
    print(f"  watermark set to        : {stats['watermark']}")
    print("=" * 55)


if __name__ == "__main__":
    main()
