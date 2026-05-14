"""
Yahoo scraper DB helper tests.

Uses an in-memory SQLite database — no live DB writes, no network calls.
Each test runs initialise_schema() on a fresh :memory: connection.

Three concerns:
  1. get_active_tickers respects the recency window.
  2. insert_earnings_history is idempotent (INSERT OR IGNORE, no duplicates).
  3. upsert_external_scrape_log writes correct success/failure state.
"""
import sqlite3
from datetime import datetime, timedelta, timezone
import pytest

from database.db import initialise_schema


@pytest.fixture
def mem_db(tmp_path):
    """In-memory DB path via temp file, schema initialised."""
    db_path = str(tmp_path / "test.db")
    initialise_schema(db_path)
    return db_path


# ── get_active_tickers ────────────────────────────────────────────────────────

def test_get_active_tickers_respects_window(mem_db):
    """
    Tickers with screener_snapshots scraped within the last 7 days are
    returned; older rows are excluded.

    Catches: missing WHERE clause, wrong date arithmetic, off-by-one on window.
    Ignores: ordering of the returned list.
    """
    from database.db import get_active_tickers
    import sqlite3

    now = datetime.now(timezone.utc)
    recent = (now - timedelta(days=3)).isoformat()
    stale  = (now - timedelta(days=10)).isoformat()

    conn = sqlite3.connect(mem_db)
    conn.execute(
        "INSERT INTO screener_snapshots (ticker, scraped_at) VALUES (?, ?)", ("AAPL", recent)
    )
    conn.execute(
        "INSERT INTO screener_snapshots (ticker, scraped_at) VALUES (?, ?)", ("OLD",  stale)
    )
    conn.commit()
    conn.close()

    tickers = get_active_tickers(mem_db, days=7)
    assert "AAPL" in tickers
    assert "OLD"  not in tickers


# ── insert_earnings_history (idempotency) ────────────────────────────────────

def test_insert_earnings_history_idempotent(mem_db):
    """
    Inserting the same (ticker, fiscal_quarter, source) row twice must not
    create duplicates — INSERT OR IGNORE enforces the UNIQUE constraint.

    Catches: accidental INSERT without OR IGNORE, double-insert bug.
    Ignores: value of scraped_at timestamp set by the helper.
    """
    from database.db import insert_earnings_history

    row = {
        "ticker":           "TSLA",
        "fiscal_quarter":   "2024-03-31",
        "eps_actual":       1.23,
        "eps_estimate":     1.10,
        "surprise_pct":     11.8,
        "revenue_actual":   None,
        "revenue_estimate": None,
        "reported_at":      None,
        "source":           "yahoo",
    }

    n1 = insert_earnings_history(mem_db, [row])
    n2 = insert_earnings_history(mem_db, [row])

    assert n1 == 1, "first insert must write 1 row"
    assert n2 == 0, "second insert of same row must be a no-op"

    conn = sqlite3.connect(mem_db)
    count = conn.execute("SELECT COUNT(*) FROM earnings_history").fetchone()[0]
    conn.close()
    assert count == 1


# ── upsert_external_scrape_log ────────────────────────────────────────────────

def test_upsert_external_scrape_log_success_advances_last_success_at(mem_db):
    """
    A successful upsert must set both last_attempted_at and last_success_at.
    A subsequent failure upsert must advance last_attempted_at but NOT change
    last_success_at.

    Catches: CASE WHEN logic inverted (failure overwrites success timestamp),
    or ON CONFLICT branch not executing correctly.
    Ignores: exact timestamp values beyond NULL/non-NULL distinction.
    """
    from database.db import upsert_external_scrape_log

    # First call: success
    upsert_external_scrape_log(mem_db, "MSFT", "EARNINGS", success=True)

    conn = sqlite3.connect(mem_db)
    row = conn.execute(
        "SELECT last_attempted_at, last_success_at, last_error "
        "FROM external_scrape_log WHERE ticker='MSFT' AND data_type='EARNINGS'"
    ).fetchone()
    conn.close()

    assert row[0] is not None, "last_attempted_at must be set on success"
    assert row[1] is not None, "last_success_at must be set on success"
    assert row[2] is None,     "last_error must be NULL on success"

    first_success_at = row[1]

    # Second call: failure — last_success_at must not change
    upsert_external_scrape_log(mem_db, "MSFT", "EARNINGS", success=False, error="timeout")

    conn = sqlite3.connect(mem_db)
    row2 = conn.execute(
        "SELECT last_attempted_at, last_success_at, last_error "
        "FROM external_scrape_log WHERE ticker='MSFT' AND data_type='EARNINGS'"
    ).fetchone()
    conn.close()

    assert row2[0] is not None,            "last_attempted_at must update on failure"
    assert row2[1] == first_success_at,    "last_success_at must NOT change on failure"
    assert row2[2] == "timeout",           "last_error must record the error message"
