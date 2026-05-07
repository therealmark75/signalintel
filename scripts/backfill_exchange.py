"""
One-off bulk backfill: populate screener_snapshots.exchange for all tickers
whose latest snapshot row has exchange IS NULL.

Resume-safe: queries NULL rows fresh on every run, so kill/restart picks up
where it left off. Idempotent: skips tickers that already have a value.

Run from project root:
    python scripts/backfill_exchange.py

Background run (logs go to file):
    nohup python scripts/backfill_exchange.py > /dev/null 2>&1 &
"""

import logging
import os
import random
import signal
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────────────
# Allow imports from project root when run as a standalone script.
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.constants import DATABASE_PATH, REQUEST_DELAY_SECONDS
from database.db import get_connection
from finvizfinance.quote import finvizfinance
from scrapers.screener_scraper import _scrape_exchange

# ── Logging ──────────────────────────────────────────────────────────────────
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

log_file = logs_dir / f"backfill_exchange_{datetime.now().strftime('%Y-%m-%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(log_file),
    ],
)
logger = logging.getLogger(__name__)

# ── Throttle detection ────────────────────────────────────────────────────────
_CONSECUTIVE_FAIL_LIMIT = 5
_THROTTLE_PAUSE_SECONDS = 300  # 5 minutes

# ── Signal handling ───────────────────────────────────────────────────────────
_interrupted = False


def _handle_signal(signum, frame):
    global _interrupted
    _interrupted = True
    logger.warning("Signal %d received — will exit cleanly after current ticker.", signum)


signal.signal(signal.SIGINT, _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_null_exchange_tickers(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT ticker
        FROM screener_snapshots s1
        WHERE exchange IS NULL
          AND scraped_at = (
              SELECT MAX(scraped_at)
              FROM screener_snapshots s2
              WHERE s2.ticker = s1.ticker
          )
        ORDER BY ticker
    """)
    return [r[0] for r in cur.fetchall()]


def _update_exchange(conn, ticker, exchange):
    cur = conn.cursor()
    cur.execute(
        """UPDATE screener_snapshots
              SET exchange = ?
            WHERE ticker = ?
              AND scraped_at = (
                  SELECT MAX(scraped_at)
                  FROM screener_snapshots
                  WHERE ticker = ?)""",
        (exchange, ticker, ticker),
    )
    conn.commit()


def _fmt_eta(elapsed_s, done, total):
    if done == 0:
        return "unknown"
    rate = elapsed_s / done
    remaining_s = rate * (total - done)
    eta = datetime.now() + timedelta(seconds=remaining_s)
    return eta.strftime("%H:%M")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    logger.info("=" * 60)
    logger.info("backfill_exchange.py — START")
    logger.info("DB: %s", DATABASE_PATH)

    try:
        conn = get_connection(DATABASE_PATH)
    except Exception as exc:
        logger.critical("Cannot open DB: %s", exc)
        sys.exit(1)

    tickers = _get_null_exchange_tickers(conn)
    total = len(tickers)
    logger.info("Tickers with NULL exchange in latest snapshot: %d", total)

    if total == 0:
        logger.info("Nothing to do — all tickers already have exchange populated.")
        conn.close()
        return

    t_start = time.monotonic()
    n_updated = 0
    n_null_result = 0
    n_errors = 0
    consecutive_fails = 0

    for idx, ticker in enumerate(tickers, start=1):
        if _interrupted:
            break

        status = "?"
        try:
            fv = finvizfinance(ticker)
            exchange = _scrape_exchange(fv.soup)

            if exchange is not None:
                _update_exchange(conn, ticker, exchange)
                n_updated += 1
                consecutive_fails = 0
                status = f"UPDATED → {exchange}"
                logger.info("[%d/%d] %-10s %s", idx, total, ticker, status)
            else:
                n_null_result += 1
                consecutive_fails = 0
                status = "NULL_RESULT"
                logger.info("[%d/%d] %-10s %s", idx, total, ticker, status)

        except Exception as exc:
            n_errors += 1
            consecutive_fails += 1
            status = f"ERROR: {exc}"
            logger.warning("[%d/%d] %-10s %s", idx, total, ticker, status)

            if consecutive_fails >= _CONSECUTIVE_FAIL_LIMIT:
                logger.critical(
                    "%d consecutive failures — possible FinViz throttle. "
                    "Pausing %d seconds before continuing.",
                    consecutive_fails,
                    _THROTTLE_PAUSE_SECONDS,
                )
                # Sleep in short chunks so SIGINT/SIGTERM stays responsive
                for _ in range(_THROTTLE_PAUSE_SECONDS):
                    if _interrupted:
                        break
                    time.sleep(1)
                consecutive_fails = 0

        if idx % 100 == 0:
            elapsed = time.monotonic() - t_start
            pct = idx / total * 100
            eta = _fmt_eta(elapsed, idx, total)
            logger.info(
                "--- Progress: %d/%d (%.1f%% complete, ETA: %s) ---",
                idx, total, pct, eta,
            )

        if not _interrupted:
            time.sleep(REQUEST_DELAY_SECONDS + random.uniform(0, 1))

    elapsed_total = time.monotonic() - t_start
    conn.close()

    summary_lines = [
        "=" * 60,
        f"RUN {'INTERRUPTED' if _interrupted else 'COMPLETE'}",
        f"Total processed : {idx}",
        f"  UPDATED       : {n_updated}",
        f"  NULL_RESULT   : {n_null_result}",
        f"  ERRORS        : {n_errors}",
        f"Runtime         : {timedelta(seconds=int(elapsed_total))}",
        "=" * 60,
    ]
    for line in summary_lines:
        logger.info(line)


if __name__ == "__main__":
    main()
