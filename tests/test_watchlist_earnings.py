"""
Tests for job_watchlist_earnings_alerts (Path A: global-chat delivery,
per-subscriber-shaped dedup).

P15, what these tests pin:
  * The once-per-(user_id, ticker, earnings_date) guarantee: a triple
    fires exactly once and the dedup row blocks every re-fire for the
    same triple, surviving across runs.
  * The MIN(earnings_date)-per-ticker collapse of multiple future rows.
  * The send-then-record ordering: a falsy send_alert writes NO dedup
    rows, so the next run retries rather than silently swallowing.

P15, what these tests intentionally ignore:
  * Message wording/formatting beyond the ticker appearing in the body.
  * The real system clock: every test injects an explicit target_date
    and seeds earnings dates relative to date.today(), so the only
    clock dependency is the CTE's `earnings_date >= DATE('now')` floor,
    which is satisfied by seeding dates in the future.
  * Real Telegram delivery: send_alert is monkeypatched in every test.

DB is built per-test in pytest's tmp_path. data/trading_system.db is
NEVER touched.
"""
from datetime import date, timedelta

import pytest

import main
from database.db import (
    initialise_schema,
    initialise_user_schema,
    get_connection,
)
from scrapers.fmp_scraper import _ensure_tables


# ── Date fixtures relative to the real clock ──────────────────────────
# Seeded earnings dates must be >= today so the query's
# `WHERE earnings_date >= DATE('now')` CTE floor keeps them.
TODAY = date.today()
TOMORROW = (TODAY + timedelta(days=1)).isoformat()
DAY_AFTER = (TODAY + timedelta(days=2)).isoformat()
NEXT_WEEK = (TODAY + timedelta(days=7)).isoformat()


class _Recorder:
    """Stand-in for send_alert: records calls and returns a fixed result."""

    def __init__(self, result=True):
        self.result = result
        self.calls = []  # list of message strings

    def __call__(self, message):
        self.calls.append(message)
        return self.result

    @property
    def count(self):
        return len(self.calls)


@pytest.fixture
def db_path(tmp_path):
    """Temp DB with the scheduler schema (incl. earnings_notifications_sent),
    the user schema (watchlists / watchlists_meta), and the FMP
    earnings_calendar table. No shared state."""
    p = str(tmp_path / "test_watchlist_earnings.db")
    initialise_schema(p)        # earnings_notifications_sent lives here
    initialise_user_schema(p)   # users, watchlists_meta, watchlists
    _ensure_tables(p)           # earnings_calendar (owned by fmp_scraper)
    return p


# ── Seed helpers ──────────────────────────────────────────────────────

def _add_watchlist(db_path, user_id, meta_id, ticker, alerts_enabled=1):
    """Create a watchlist_meta row (if new) and add a ticker to it.

    Seeds a users row first: foreign keys are enforced on get_connection
    (watchlists_meta.user_id REFERENCES users(id))."""
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO users (id, username, email, password_hash, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, f"user{user_id}", f"user{user_id}@test.local", "x", "2026-01-01T00:00:00"),
        )
        cur.execute(
            "INSERT OR IGNORE INTO watchlists_meta (id, user_id, name, alerts_enabled, is_default) "
            "VALUES (?, ?, ?, ?, ?)",
            (meta_id, user_id, "Test WL", alerts_enabled, 1),
        )
        cur.execute(
            "INSERT INTO watchlists (user_id, watchlist_id, ticker, added_at) "
            "VALUES (?, ?, ?, ?)",
            (user_id, meta_id, ticker, "2026-01-01T00:00:00"),
        )
        conn.commit()
    finally:
        conn.close()


def _add_earnings(db_path, ticker, earnings_date):
    """Insert a forward earnings_calendar row."""
    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT OR REPLACE INTO earnings_calendar (ticker, earnings_date, timing, last_updated) "
            "VALUES (?, ?, 'TBA', ?)",
            (ticker, earnings_date, "2026-01-01T06:05:00"),
        )
        conn.commit()
    finally:
        conn.close()


def _clear_earnings(db_path, ticker):
    conn = get_connection(db_path)
    try:
        conn.execute("DELETE FROM earnings_calendar WHERE ticker = ?", (ticker,))
        conn.commit()
    finally:
        conn.close()


def _dedup_rows(db_path):
    conn = get_connection(db_path)
    try:
        return [
            tuple(r)
            for r in conn.execute(
                "SELECT user_id, ticker, earnings_date FROM earnings_notifications_sent "
                "ORDER BY user_id, ticker, earnings_date"
            ).fetchall()
        ]
    finally:
        conn.close()


# ── Tests ─────────────────────────────────────────────────────────────

def test_first_fire_sends(db_path, monkeypatch):
    """Case 1: a watchlist ticker reporting tomorrow fires once and records
    exactly one dedup row. Catches the happy-path wiring end to end."""
    rec = _Recorder(result=True)
    monkeypatch.setattr(main, "send_alert", rec)

    _add_watchlist(db_path, user_id=1, meta_id=100, ticker="AAPL")
    _add_earnings(db_path, "AAPL", TOMORROW)

    main.job_watchlist_earnings_alerts(db_path, target_date=TOMORROW)

    assert rec.count == 1
    assert "AAPL" in rec.calls[0]
    rows = _dedup_rows(db_path)
    assert rows == [(1, "AAPL", TOMORROW)]


def test_second_fire_same_day_suppressed(db_path, monkeypatch):
    """Case 2: running again the same day for the same triple sends nothing
    (the NOT EXISTS gate matches the row written by the first run)."""
    rec = _Recorder(result=True)
    monkeypatch.setattr(main, "send_alert", rec)

    _add_watchlist(db_path, user_id=1, meta_id=100, ticker="AAPL")
    _add_earnings(db_path, "AAPL", TOMORROW)

    main.job_watchlist_earnings_alerts(db_path, target_date=TOMORROW)
    main.job_watchlist_earnings_alerts(db_path, target_date=TOMORROW)

    assert rec.count == 1                       # only the first run sent
    assert len(_dedup_rows(db_path)) == 1       # still one row, not two


def test_new_earnings_date_same_ticker_fires_again(db_path, monkeypatch):
    """Case 3: when the ticker's next earnings date moves to a new value,
    the new triple is not in the dedup table and fires again. Catches that
    dedup is keyed on the triple INCLUDING earnings_date."""
    rec = _Recorder(result=True)
    monkeypatch.setattr(main, "send_alert", rec)

    _add_watchlist(db_path, user_id=1, meta_id=100, ticker="AAPL")

    # Run 1: reports on TOMORROW.
    _add_earnings(db_path, "AAPL", TOMORROW)
    main.job_watchlist_earnings_alerts(db_path, target_date=TOMORROW)

    # Calendar rolls forward: the old date is gone, a new quarter appears.
    _clear_earnings(db_path, "AAPL")
    _add_earnings(db_path, "AAPL", DAY_AFTER)
    main.job_watchlist_earnings_alerts(db_path, target_date=DAY_AFTER)

    assert rec.count == 2
    assert _dedup_rows(db_path) == [
        (1, "AAPL", TOMORROW),    # _dedup_rows sorts by earnings_date asc
        (1, "AAPL", DAY_AFTER),
    ]


def test_min_date_collapses_duplicate_future_rows(db_path, monkeypatch):
    """Case 4: two future rows for one ticker (NKE 06-25/06-30 shape) collapse
    to MIN(earnings_date); a run on the MIN date fires exactly once."""
    rec = _Recorder(result=True)
    monkeypatch.setattr(main, "send_alert", rec)

    _add_watchlist(db_path, user_id=1, meta_id=100, ticker="NKE")
    _add_earnings(db_path, "NKE", TOMORROW)     # the MIN
    _add_earnings(db_path, "NKE", NEXT_WEEK)    # stale-later row

    main.job_watchlist_earnings_alerts(db_path, target_date=TOMORROW)

    assert rec.count == 1
    assert _dedup_rows(db_path) == [(1, "NKE", TOMORROW)]

    # A run targeted at the later date must NOT fire (MIN is not NEXT_WEEK).
    main.job_watchlist_earnings_alerts(db_path, target_date=NEXT_WEEK)
    assert rec.count == 1
    assert len(_dedup_rows(db_path)) == 1


def test_empty_set_sends_nothing(db_path, monkeypatch):
    """Case 5: no watchlist ticker reports on target_date -> no send, no rows,
    no empty digest."""
    rec = _Recorder(result=True)
    monkeypatch.setattr(main, "send_alert", rec)

    _add_watchlist(db_path, user_id=1, meta_id=100, ticker="AAPL")
    _add_earnings(db_path, "AAPL", NEXT_WEEK)   # reports later, not tomorrow

    main.job_watchlist_earnings_alerts(db_path, target_date=TOMORROW)

    assert rec.count == 0
    assert _dedup_rows(db_path) == []


def test_alerts_disabled_excluded(db_path, monkeypatch):
    """Case 6: a muted watchlist (alerts_enabled=0) holding a tomorrow-reporting
    ticker yields no triple. Catches the only gate the design relies on."""
    rec = _Recorder(result=True)
    monkeypatch.setattr(main, "send_alert", rec)

    _add_watchlist(db_path, user_id=1, meta_id=100, ticker="AAPL", alerts_enabled=0)
    _add_earnings(db_path, "AAPL", TOMORROW)

    main.job_watchlist_earnings_alerts(db_path, target_date=TOMORROW)

    assert rec.count == 0
    assert _dedup_rows(db_path) == []


def test_send_failure_records_nothing(db_path, monkeypatch):
    """Case 7: a falsy send_alert result writes NO dedup rows, so the next run
    retries. Catches the send-then-record ordering contract."""
    rec = _Recorder(result=False)   # send fails
    monkeypatch.setattr(main, "send_alert", rec)

    _add_watchlist(db_path, user_id=1, meta_id=100, ticker="AAPL")
    _add_earnings(db_path, "AAPL", TOMORROW)

    main.job_watchlist_earnings_alerts(db_path, target_date=TOMORROW)

    assert rec.count == 1               # it tried to send
    assert _dedup_rows(db_path) == []   # but recorded nothing

    # Next run retries (now with a working send) and records.
    rec.result = True
    main.job_watchlist_earnings_alerts(db_path, target_date=TOMORROW)
    assert rec.count == 2
    assert _dedup_rows(db_path) == [(1, "AAPL", TOMORROW)]
