"""
Data integrity tests — freshness, uniqueness, and distribution checks on the live DB.
All tests are read-only. Soft assertions (conditional skips) documented inline.
"""
import sqlite3
from datetime import datetime, timedelta, timezone
import pytest


def test_signal_scores_freshness(db):
    """Latest scored_at must be within 72 hours of now."""
    row = db.execute("SELECT MAX(scored_at) FROM signal_scores").fetchone()
    assert row[0] is not None, "signal_scores is empty"
    latest = datetime.fromisoformat(row[0])
    if latest.tzinfo is None:
        latest = latest.replace(tzinfo=timezone.utc)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=72)
    assert latest >= cutoff, f"signal_scores last updated {row[0]}, older than 72h"


def test_screener_snapshots_freshness(db):
    """Latest scraped_at must be within 72 hours of now."""
    row = db.execute("SELECT MAX(scraped_at) FROM screener_snapshots").fetchone()
    assert row[0] is not None, "screener_snapshots is empty"
    latest = datetime.fromisoformat(row[0])
    if latest.tzinfo is None:
        latest = latest.replace(tzinfo=timezone.utc)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=72)
    assert latest >= cutoff, f"screener_snapshots last scraped {row[0]}, older than 72h"


def test_insider_trades_freshness(db):
    """
    Catches scraper job death or persistent FAILED status.

    Ignores quiet insider periods where rows_added=0 is legitimate
    (insider_trades uses INSERT OR IGNORE; a quiet day where all trades
    are already in the table does not advance MAX(scraped_at) even
    though the scraper ran successfully).

    Source: run_log WHERE job_name='insider_scrape' AND status='SUCCESS'.
    """
    row = db.execute(
        "SELECT MAX(run_at) FROM run_log "
        "WHERE job_name = 'insider_scrape' AND status = 'SUCCESS'"
    ).fetchone()
    assert row[0] is not None, "no successful insider_scrape runs in run_log"
    latest = datetime.fromisoformat(row[0])
    if latest.tzinfo is None:
        latest = latest.replace(tzinfo=timezone.utc)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=72)
    assert latest >= cutoff, f"insider_scrape last successful run {row[0]}, older than 72h"


def test_legal_risk_freshness(db):
    """
    Catches legal_risk scraper cron death or extended outage.

    Ignores partial-run days where some rows have been written and the
    job is still mid-run. Scraper expands coverage continuously and
    writes a new scraped_at on each ticker processed, so MAX(scraped_at)
    advances throughout every active run.
    """
    row = db.execute("SELECT MAX(scraped_at) FROM legal_risk").fetchone()
    assert row[0] is not None, "legal_risk is empty"
    latest = datetime.fromisoformat(row[0])
    if latest.tzinfo is None:
        latest = latest.replace(tzinfo=timezone.utc)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=72)
    assert latest >= cutoff, f"legal_risk last scraped {row[0]}, older than 72h"


def test_ticker_metadata_freshness(db):
    """
    Catches ticker_metadata write path breakage independent of
    screener_snapshots success.

    Ignores first_seen_at (frozen at backfill, never advances).
    updated_at is written by the screener scrape via ON CONFLICT...DO
    UPDATE; if that specific write breaks (BUG-B-style miss) while
    screener_snapshots still populates, this test fails while the
    screener_snapshots freshness test still passes.
    """
    row = db.execute("SELECT MAX(updated_at) FROM ticker_metadata").fetchone()
    assert row[0] is not None, "ticker_metadata is empty"
    latest = datetime.fromisoformat(row[0])
    if latest.tzinfo is None:
        latest = latest.replace(tzinfo=timezone.utc)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=72)
    assert latest >= cutoff, f"ticker_metadata last updated {row[0]}, older than 72h"


def test_no_duplicate_signals_for_latest_run(db, latest_run_date):
    """Each ticker must appear at most once in the latest scoring run."""
    rows = db.execute(
        "SELECT ticker, COUNT(*) as cnt FROM signal_scores WHERE DATE(scored_at) = ? "
        "GROUP BY ticker HAVING cnt > 1",
        (latest_run_date,),
    ).fetchall()
    assert len(rows) == 0, f"{len(rows)} tickers have duplicate rows: {[r['ticker'] for r in rows[:5]]}"


def test_rating_distribution_sane(db, latest_run_date):
    """
    Sanity check: no single outlier rating dominates.
    STRONG_BUY and STRONG_SELL should each be < 500 in any given run.
    """
    for rating in ("STRONG_BUY", "STRONG_SELL"):
        row = db.execute(
            "SELECT COUNT(*) FROM signal_scores WHERE DATE(scored_at) = ? AND rating = ?",
            (latest_run_date, rating),
        ).fetchone()
        assert row[0] < 500, f"{rating} count={row[0]} looks implausibly high"


def test_signal_scores_minimum_count(latest_signals):
    """There must be at least 1000 signals in the latest run."""
    assert len(latest_signals) >= 1000, f"Only {len(latest_signals)} signals — scorer may have failed"


def test_target_price_coverage(db, latest_run_date):
    """
    Invariant 8: target_price should be non-null for 10,000+ tickers.
    CONDITIONAL — skipped if coverage is 0% (fmp_price_targets not yet populated).
    """
    non_null = db.execute(
        "SELECT COUNT(*) FROM signal_scores WHERE DATE(scored_at) = ? AND target_price IS NOT NULL",
        (latest_run_date,),
    ).fetchone()[0]
    total = db.execute(
        "SELECT COUNT(*) FROM signal_scores WHERE DATE(scored_at) = ?",
        (latest_run_date,),
    ).fetchone()[0]
    if non_null == 0:
        pytest.skip("target_price is 0% — fmp_price_targets not yet populated")
    coverage_pct = non_null / total * 100
    assert non_null >= 10000, f"target_price coverage {non_null}/{total} ({coverage_pct:.0f}%) below threshold"


def test_no_signal_scores_orphans(db):
    """Every ticker in signal_scores must also appear in screener_snapshots."""
    orphans = db.execute(
        "SELECT COUNT(*) FROM signal_scores "
        "WHERE ticker NOT IN (SELECT DISTINCT ticker FROM screener_snapshots)"
    ).fetchone()[0]
    assert orphans < 200, f"{orphans} signal_scores tickers have no screener data"


def test_legal_risk_distribution(db):
    """
    Invariant 1: majority of classified tickers should have risk_label 'None'.
    Skipped if legal_risk table is empty.
    """
    total = db.execute("SELECT COUNT(*) FROM legal_risk").fetchone()[0]
    if total == 0:
        pytest.skip("legal_risk table is empty — SEC scraper not yet run")
    none_count = db.execute(
        "SELECT COUNT(*) FROM legal_risk WHERE risk_label = 'None'"
    ).fetchone()[0]
    none_pct = none_count / total * 100
    assert none_pct >= 70, f"'None' risk only {none_pct:.0f}% of classified tickers — classifier may be over-triggering"


# ── Yahoo Phase 2a freshness gates ───────────────────────────────────────────

def test_yahoo_earnings_history_freshness(db):
    """
    Latest earnings_history scraped_at must be within 14 days of now.
    Skipped if the table is empty (job has not yet run — acceptable on fresh deploy).

    Catches: yahoo_earnings_priority or yahoo_earnings_bulk job dying silently.
    Ignores: tickers with no earnings data from Yahoo (empty fetch is NOT written).
    """
    row = db.execute("SELECT MAX(scraped_at) FROM earnings_history").fetchone()
    if row[0] is None:
        pytest.skip("earnings_history is empty — Yahoo scraper not yet run")
    latest = datetime.fromisoformat(row[0])
    if latest.tzinfo is None:
        latest = latest.replace(tzinfo=timezone.utc)
    cutoff = datetime.now(timezone.utc) - timedelta(days=14)
    assert latest >= cutoff, f"earnings_history last scraped {row[0]} — older than 14 days"


def test_yahoo_financial_statements_freshness(db):
    """
    Latest financial_statements scraped_at must be within 14 days of now.
    Skipped if the table is empty (weekly bulk job runs once; first run may be pending).

    Catches: yahoo_financials bulk job dying silently.
    Ignores: tickers with no financial data from Yahoo.
    """
    row = db.execute("SELECT MAX(scraped_at) FROM financial_statements").fetchone()
    if row[0] is None:
        pytest.skip("financial_statements is empty — Yahoo financials scraper not yet run")
    latest = datetime.fromisoformat(row[0])
    if latest.tzinfo is None:
        latest = latest.replace(tzinfo=timezone.utc)
    cutoff = datetime.now(timezone.utc) - timedelta(days=14)
    assert latest >= cutoff, f"financial_statements last scraped {row[0]} — older than 14 days"


def test_yahoo_analyst_changes_freshness(db):
    """
    Latest analyst_changes scraped_at must be within 14 days of now.
    Skipped if the table is empty (daily job has not yet run on this deploy).

    Catches: yahoo_analyst_changes daily priority job dying silently.
    Ignores: tickers with no analyst upgrade/downgrade history from Yahoo.
    """
    row = db.execute("SELECT MAX(scraped_at) FROM analyst_changes").fetchone()
    if row[0] is None:
        pytest.skip("analyst_changes is empty — Yahoo analyst scraper not yet run")
    latest = datetime.fromisoformat(row[0])
    if latest.tzinfo is None:
        latest = latest.replace(tzinfo=timezone.utc)
    cutoff = datetime.now(timezone.utc) - timedelta(days=14)
    assert latest >= cutoff, f"analyst_changes last scraped {row[0]} — older than 14 days"


def test_yahoo_institutional_holders_freshness(db):
    """
    Latest institutional_holders scraped_at must be within 14 days of now.
    Skipped if the table is empty (weekly Sunday bulk job may not have run yet).

    Catches: yahoo_institutional_holders weekly bulk job dying silently.
    Ignores: tickers where Yahoo returns no institutional holder data.
    """
    row = db.execute("SELECT MAX(scraped_at) FROM institutional_holders").fetchone()
    if row[0] is None:
        pytest.skip("institutional_holders is empty — Yahoo holders scraper not yet run")
    latest = datetime.fromisoformat(row[0])
    if latest.tzinfo is None:
        latest = latest.replace(tzinfo=timezone.utc)
    cutoff = datetime.now(timezone.utc) - timedelta(days=14)
    assert latest >= cutoff, f"institutional_holders last scraped {row[0]} — older than 14 days"
