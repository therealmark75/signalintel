"""
Shared pytest fixtures for SignalIntel test suite.

Auth: all routes require session['user_id']. The `client` fixture injects
user_id=2 (markn) into the Flask test session before each test.

DB: connects to data/trading_system.db — the live SQLite file. All queries
are read-only. Tests never write to the database.
"""
import sys
import os
import sqlite3
from datetime import datetime, timedelta, timezone
import pytest

# Ensure project root is on path so web.app and config.settings are importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.constants import DATABASE_PATH


@pytest.fixture(scope="session")
def db():
    """Read-only SQLite connection to the live trading_system.db."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture(scope="session")
def flask_app():
    """Flask app instance with TESTING=True."""
    from web.app import app
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(flask_app):
    """
    Flask test client with auth session pre-seeded.
    Creates a fresh client per test; injects session['user_id'] = 2 (markn).
    """
    with flask_app.test_client() as c:
        with c.session_transaction() as sess:
            sess["user_id"] = 2
        yield c


@pytest.fixture(scope="session")
def latest_run_date(db):
    """The most recent DATE(scored_at) in signal_scores."""
    row = db.execute(
        "SELECT MAX(DATE(scored_at)) FROM signal_scores"
    ).fetchone()
    date = row[0]
    assert date is not None, "signal_scores is empty — run the scorer first"
    return date


@pytest.fixture(scope="session")
def latest_signals(db, latest_run_date):
    """All signal_scores rows for the most recent scoring run."""
    rows = db.execute(
        "SELECT * FROM signal_scores WHERE DATE(scored_at) = ?",
        (latest_run_date,),
    ).fetchall()
    assert len(rows) > 0, f"No signals found for {latest_run_date}"
    return rows


@pytest.fixture(scope="session")
def scoring_run_complete(db):
    """Skip scoring-content tests when the latest scoring run is still mid-write.

    A scoring-content test reads scheduler_meta because the watermark is the only
    end-of-run sentinel in the schema: detect_rating_changes advances
    rating_changes_watermark to MAX(scored_at) ONLY after a run finishes
    (database/db.py:1437). The *_freshness gates stay unguarded as the liveness
    backstop. Skip ONLY when MAX(scored_at) differs from the watermark AND is
    within the last 90 minutes (a plausible transient mid-cycle write); a
    mismatch older than 90 minutes is a real stale-watermark condition that must
    surface, not hide.
    """
    max_ts = db.execute("SELECT MAX(scored_at) FROM signal_scores").fetchone()[0]
    if max_ts is None:
        return  # no scoring run yet; let the dependent tests assert emptiness
    wm_row = db.execute(
        "SELECT value FROM scheduler_meta WHERE key = 'rating_changes_watermark'"
    ).fetchone()
    watermark = wm_row[0] if wm_row else None
    if watermark == max_ts:
        return  # run complete; guard stays out of the way
    # Incomplete (mismatch or missing watermark): skip only if plausibly transient.
    latest = datetime.fromisoformat(max_ts)
    if latest.tzinfo is None:
        latest = latest.replace(tzinfo=timezone.utc)
    if latest >= datetime.now(timezone.utc) - timedelta(minutes=90):
        pytest.skip(
            f"scoring run for {max_ts} incomplete: MAX(scored_at) != "
            f"rating_changes_watermark ({watermark}); within 90min, treating as "
            "transient mid-cycle write"
        )
    # Stale watermark older than 90 minutes: real condition, let the tests run.
