"""
Unit tests for the persisted-price signal backtester (signals/backtester.py).

These tests seed a throwaway temp SQLite file with synthetic signal_scores and
screener_snapshots rows. They never touch the live DB and never hit the
network: the whole point of the rewire is that forward prices come from
screener_snapshots, so a backtest run must complete with yfinance unreachable.

Vocabulary note: ratings here use INTERNAL codes (BUY, STRONG_BUY) because we
are exercising scorer/query logic, never presentation.
"""
import sqlite3
import pytest

from signals import backtester
from signals.backtester import (
    backtest_signals_from_db,
    compute_summary,
    run_full_backtest,
)


# ── Fixture helpers ───────────────────────────────

def _make_db(tmp_path, signals, snapshots):
    """
    Build a temp SQLite with minimal signal_scores + screener_snapshots.

    signals:   list of (scored_at, ticker, rating, composite_score, scoring_version)
    snapshots: list of (scraped_at, ticker, price)
    """
    db_path = str(tmp_path / "bt.db")
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE signal_scores (
            scored_at TEXT, ticker TEXT, rating TEXT,
            composite_score REAL, scoring_version TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE screener_snapshots (
            scraped_at TEXT, ticker TEXT, price REAL
        )
    """)
    conn.executemany(
        "INSERT INTO signal_scores (scored_at,ticker,rating,composite_score,scoring_version) VALUES (?,?,?,?,?)",
        signals,
    )
    conn.executemany(
        "INSERT INTO screener_snapshots (scraped_at,ticker,price) VALUES (?,?,?)",
        snapshots,
    )
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def no_yfinance(monkeypatch):
    """
    Replace the module-level yf symbol with a tripwire that raises on ANY
    attribute access, so the test fails loudly if a backtest path ever calls
    into yfinance.

    Catches: any reachable yf.* call in the backtest path (regression to the
    retired live-fetch design).
    Ignores: the import guard itself (importing yfinance at module load is
    allowed; only *calling* it is forbidden).
    """
    class _Tripwire:
        def __getattr__(self, name):
            raise AssertionError(f"yfinance must not be called in a backtest (got yf.{name})")
    monkeypatch.setattr(backtester, "yf", _Tripwire(), raising=False)
    return _Tripwire


# ── Tests ─────────────────────────────────────────

def test_entry_and_exit_resolved_when_snapshots_exist(tmp_path, no_yfinance):
    """
    Catches: the happy path, that entry resolves to the signal-day spot and
    exit resolves to the price on the Nth forward trading date, and a trade is
    produced with a numeric return.
    Ignores: gap handling, multi-snapshot tie-breaks, and version filtering
    (each has its own dedicated test); here every date is present and unique.
    """
    signals = [("2026-06-01T17:00:00", "AAA", "BUY", 70.0, "0.17.0")]
    snaps = [
        ("2026-06-01T07:00:00", "AAA", 100.0),
        ("2026-06-02T07:00:00", "AAA", 110.0),  # N=1 forward
        ("2026-06-03T07:00:00", "AAA", 120.0),  # N=2 forward
    ]
    db = _make_db(tmp_path, signals, snaps)

    res = backtest_signals_from_db(db, "0.17.0", rating="BUY", hold_days=1, min_score=60.0)
    assert len(res) == 1
    t = res[0]
    assert t.error is None
    assert t.entry_price == 100.0
    assert t.exit_price == 110.0
    assert t.return_pct == 10.0
    assert t.win is True


def test_forward_stepping_skips_gap_date(tmp_path, no_yfinance):
    """
    Catches: that the Nth forward step counts real subsequent observation dates
    and steps OVER an absent date, rather than using calendar signal_date + N.
    With 2026-06-02 missing, N=1 must land on 2026-06-03, not on the empty 06-02.
    Ignores: price-basis quality (spot vs close) and multi-snapshot ties.
    """
    signals = [("2026-06-01T17:00:00", "AAA", "BUY", 70.0, "0.17.0")]
    snaps = [
        ("2026-06-01T07:00:00", "AAA", 100.0),
        # 2026-06-02 deliberately absent (gap / weekend)
        ("2026-06-03T07:00:00", "AAA", 130.0),  # first available forward date
        ("2026-06-04T07:00:00", "AAA", 140.0),
    ]
    db = _make_db(tmp_path, signals, snaps)

    res = backtest_signals_from_db(db, "0.17.0", rating="BUY", hold_days=1, min_score=60.0)
    assert len(res) == 1
    t = res[0]
    assert t.exit_price == 130.0, "N=1 should step to the next AVAILABLE date, not calendar+1"
    assert t.return_pct == 30.0


def test_multiple_snapshots_same_day_picks_max_scraped_at(tmp_path, no_yfinance):
    """
    Catches: same-day tie-break, that both entry and exit take the latest spot
    (MAX(scraped_at)) when a day has several snapshots.
    Ignores: gap stepping and cross-version reads.
    """
    signals = [("2026-06-01T20:00:00", "AAA", "BUY", 70.0, "0.17.0")]
    snaps = [
        ("2026-06-01T07:00:00", "AAA", 100.0),
        ("2026-06-01T15:30:00", "AAA", 105.0),  # latest spot on signal day -> entry
        ("2026-06-02T07:00:00", "AAA", 200.0),
        ("2026-06-02T15:30:00", "AAA", 210.0),  # latest spot on exit day -> exit
    ]
    db = _make_db(tmp_path, signals, snaps)

    res = backtest_signals_from_db(db, "0.17.0", rating="BUY", hold_days=1, min_score=60.0)
    t = res[0]
    assert t.entry_price == 105.0
    assert t.exit_price == 210.0
    assert t.return_pct == 100.0


def test_insufficient_forward_dates_errored_and_excluded(tmp_path, no_yfinance):
    """
    Catches: a signal with fewer than N forward dates is recorded with an error
    and a None return, and compute_summary excludes it (total_trades == 0).
    Ignores: the numeric return path (there is no valid exit to compute).
    """
    signals = [("2026-06-10T17:00:00", "AAA", "BUY", 70.0, "0.17.0")]
    snaps = [
        ("2026-06-10T07:00:00", "AAA", 100.0),  # only the signal day exists, no forward dates
    ]
    db = _make_db(tmp_path, signals, snaps)

    res = backtest_signals_from_db(db, "0.17.0", rating="BUY", hold_days=5, min_score=60.0)
    assert len(res) == 1
    t = res[0]
    assert t.error == "No exit price at N=5"
    assert t.return_pct is None
    assert t.entry_price == 100.0

    summary = compute_summary(res, "BUY", 5)
    assert summary.total_trades == 0


def test_version_segmentation_never_reads_other_version(tmp_path, no_yfinance):
    """
    Catches: cohort isolation, that a run scoped to version A never reads a
    version B signal row, even when both share a ticker namespace and prices.
    Ignores: the price math (both versions are priceable); only WHICH signals
    are selected matters here.
    """
    signals = [
        ("2026-06-01T17:00:00", "AAA", "BUY", 70.0, "0.17.0"),  # version A
        ("2026-06-01T17:00:00", "BBB", "BUY", 70.0, "0.18.0"),  # version B
    ]
    snaps = [
        ("2026-06-01T07:00:00", "AAA", 100.0),
        ("2026-06-02T07:00:00", "AAA", 110.0),
        ("2026-06-01T07:00:00", "BBB", 100.0),
        ("2026-06-02T07:00:00", "BBB", 110.0),
    ]
    db = _make_db(tmp_path, signals, snaps)

    res_a = backtest_signals_from_db(db, "0.17.0", rating="BUY", hold_days=1, min_score=60.0)
    tickers_a = {t.ticker for t in res_a}
    assert tickers_a == {"AAA"}, "version 0.17.0 run must not read the 0.18.0 row"

    res_b = backtest_signals_from_db(db, "0.18.0", rating="BUY", hold_days=1, min_score=60.0)
    assert {t.ticker for t in res_b} == {"BBB"}


def test_return_pct_and_win_known_fixture(tmp_path, no_yfinance):
    """
    Catches: exact return_pct and win computation for one winner and one loser
    on hand-computed prices (winner 100->112 = +12%, loser 50->45 = -10%).
    Ignores: summary aggregation nuances; this asserts per-trade arithmetic.
    """
    signals = [
        ("2026-06-01T17:00:00", "WIN", "BUY", 80.0, "0.17.0"),
        ("2026-06-01T17:00:00", "LOS", "BUY", 80.0, "0.17.0"),
    ]
    snaps = [
        ("2026-06-01T07:00:00", "WIN", 100.0),
        ("2026-06-02T07:00:00", "WIN", 112.0),
        ("2026-06-01T07:00:00", "LOS", 50.0),
        ("2026-06-02T07:00:00", "LOS", 45.0),
    ]
    db = _make_db(tmp_path, signals, snaps)

    res = backtest_signals_from_db(db, "0.17.0", rating="BUY", hold_days=1, min_score=60.0)
    by_ticker = {t.ticker: t for t in res}
    assert by_ticker["WIN"].return_pct == 12.0
    assert by_ticker["WIN"].win is True
    assert by_ticker["LOS"].return_pct == -10.0
    assert by_ticker["LOS"].win is False


def test_run_full_backtest_uses_short_horizons_only(tmp_path, no_yfinance):
    """
    Catches: run_full_backtest defaults to the short-horizon set [1, 5] and
    produces a summary per (rating, horizon) without any N=20 key.
    Ignores: cross-rating behaviour; a single rating is enough to assert the
    horizon set.
    """
    signals = [("2026-06-01T17:00:00", "AAA", "BUY", 70.0, "0.17.0")]
    snaps = [
        ("2026-06-01T07:00:00", "AAA", 100.0),
        ("2026-06-02T07:00:00", "AAA", 110.0),
        ("2026-06-03T07:00:00", "AAA", 120.0),
        ("2026-06-04T07:00:00", "AAA", 130.0),
        ("2026-06-05T07:00:00", "AAA", 140.0),
        ("2026-06-08T07:00:00", "AAA", 150.0),
    ]
    db = _make_db(tmp_path, signals, snaps)

    out = run_full_backtest(db, "0.17.0", ratings=["BUY"], min_score=60.0)
    assert set(out["BUY"].keys()) == {1, 5}
    assert 20 not in out["BUY"]
    assert out["BUY"][1]["summary"].total_trades == 1
