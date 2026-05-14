"""
Yahoo Finance fetch benchmark.

Fetches all 4 data types for a small set of well-known tickers and reports
row counts, timing, and any rate-limit signals. Run once before the first
live scrape to confirm yfinance is responsive and the DB helpers write correctly.

Usage:
    source venv/bin/activate
    python scripts/benchmark_yahoo.py

Exit codes:
    0 — all fetches completed (some may be empty; that's acceptable)
    1 — YahooRateLimitedError tripped during benchmark
"""
import sys
import time
import logging

sys.path.insert(0, ".")

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BENCHMARK_TICKERS = ["AAPL", "MSFT", "AMZN", "GOOGL", "TSLA"]

from config.constants import DATABASE_PATH, YAHOO_REQUEST_DELAY_SECONDS
from scrapers.yahoo_scraper import (
    YahooRateLimitedError,
    fetch_earnings_history,
    fetch_financial_statements,
    fetch_institutional_holders,
    fetch_analyst_changes,
)
from database.db import (
    insert_earnings_history,
    insert_financial_statements,
    insert_institutional_holders,
    insert_analyst_changes,
    upsert_external_scrape_log,
    initialise_schema,
)

DATA_TYPES = [
    ("EARNINGS",   fetch_earnings_history,      insert_earnings_history),
    ("FINANCIALS", fetch_financial_statements,   insert_financial_statements),
    ("HOLDERS",    fetch_institutional_holders,  insert_institutional_holders),
    ("ANALYST",    fetch_analyst_changes,        insert_analyst_changes),
]


def main():
    import yfinance as yf

    initialise_schema(DATABASE_PATH)
    totals = {dt: 0 for dt, _, _ in DATA_TYPES}
    overall_start = time.time()

    for ticker in BENCHMARK_TICKERS:
        logger.info(f"── {ticker} ────────────────────────────")
        try:
            t = yf.Ticker(ticker)
            for data_type, fetch_fn, insert_fn in DATA_TYPES:
                t0 = time.time()
                try:
                    rows = fetch_fn(t, ticker)
                    elapsed = time.time() - t0
                    if rows:
                        n = insert_fn(DATABASE_PATH, rows)
                        totals[data_type] += n
                        logger.info(f"  {data_type:12s} {len(rows):4d} fetched  {n:4d} inserted  {elapsed:.2f}s")
                    else:
                        logger.info(f"  {data_type:12s}    0 fetched (no data)  {elapsed:.2f}s")
                    upsert_external_scrape_log(DATABASE_PATH, ticker, data_type, success=True)
                except YahooRateLimitedError:
                    raise
                except Exception as e:
                    logger.warning(f"  {data_type:12s} FAILED: {e}")
                    upsert_external_scrape_log(DATABASE_PATH, ticker, data_type, success=False, error=str(e))
        except YahooRateLimitedError as e:
            logger.error(f"Circuit breaker tripped on {ticker}: {e}")
            sys.exit(1)

        time.sleep(YAHOO_REQUEST_DELAY_SECONDS)

    elapsed_total = time.time() - overall_start
    logger.info("────────────────────────────────────────")
    logger.info(f"Benchmark complete in {elapsed_total:.1f}s")
    for data_type, rows_inserted in totals.items():
        logger.info(f"  {data_type:12s} {rows_inserted:5d} total rows inserted")


if __name__ == "__main__":
    main()
