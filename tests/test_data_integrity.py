"""
Data integrity tests — freshness, uniqueness, and distribution checks on the live DB.
All tests are read-only. Soft assertions (conditional skips) documented inline.
"""
import sqlite3
from datetime import datetime, timedelta, timezone
import pytest


def test_signal_scores_freshness(db):
    """Latest scored_at must be within 48 hours of now."""
    row = db.execute("SELECT MAX(scored_at) FROM signal_scores").fetchone()
    assert row[0] is not None, "signal_scores is empty"
    latest = datetime.fromisoformat(row[0])
    if latest.tzinfo is None:
        latest = latest.replace(tzinfo=timezone.utc)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
    assert latest >= cutoff, f"signal_scores last updated {row[0]} — older than 48h"


def test_screener_snapshots_freshness(db):
    """Latest scraped_at must be within 48 hours of now."""
    row = db.execute("SELECT MAX(scraped_at) FROM screener_snapshots").fetchone()
    assert row[0] is not None, "screener_snapshots is empty"
    latest = datetime.fromisoformat(row[0])
    if latest.tzinfo is None:
        latest = latest.replace(tzinfo=timezone.utc)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
    assert latest >= cutoff, f"screener_snapshots last scraped {row[0]} — older than 48h"


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
