"""
Unit tests for the persisted-price signal backtester (signals/backtester.py).

These tests seed a throwaway temp SQLite file with synthetic signal_scores and
screener_snapshots rows. They never touch the live DB and never hit the
network: the whole point of the rewire is that forward prices come from
screener_snapshots, so a backtest run must complete with yfinance unreachable.

Vocabulary note: ratings here use INTERNAL codes (BUY, STRONG_BUY) because we
are exercising scorer/query logic, never presentation.
"""
import logging
import sqlite3
import pytest

from signals import backtester
from signals.backtester import (
    backtest_signals_from_db,
    compute_summary,
    is_straddle_date,
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


# ── Corporate-action straddle guard (Part 49 Item 1) ──

def test_same_day_straddle_exit_is_skipped_not_fabricated(tmp_path, no_yfinance):
    """
    KLAC-shape: the N=1 exit date carries both a pre-split (~2411) and post-split
    (~241) snapshot (intraday ratio ~10). The guard must return None for the exit
    so the trade carries an error and is EXCLUDED from aggregates, never a
    fabricated -89% return.

    Catches: a straddle exit date producing a fabricated return_pct instead of
    being dropped (the original KLAC bug).
    Ignores: the entry side (single price here) and the cross-day backstop; the
    exit-side same-day skip is the one behaviour under test.
    """
    signals = [("2026-06-11T17:00:00", "KLAC", "BUY", 70.0, "0.17.0")]
    snaps = [
        ("2026-06-11T07:00:00", "KLAC", 2305.86),   # clean entry day (ratio 1.0)
        ("2026-06-12T07:00:00", "KLAC", 2411.64),   # exit day, pre-split print
        ("2026-06-12T16:30:00", "KLAC", 241.16),    # exit day, post-split -> STRADDLE
    ]
    db = _make_db(tmp_path, signals, snaps)

    res = backtest_signals_from_db(db, "0.17.0", rating="BUY", hold_days=1, min_score=60.0)
    assert len(res) == 1
    t = res[0]
    assert t.return_pct is None, "straddle exit must not fabricate a return"
    assert t.error is not None
    assert compute_summary(res, "BUY", 1).total_trades == 0, "must be excluded from aggregates"


def test_real_penny_doubling_is_kept(tmp_path, no_yfinance):
    """
    FATN-shape: 3.78 on the entry day, 8.30 on the N=1 exit day, neither a
    same-day straddle. This is a real micro-cap move and must be KEPT with its
    +119.58% return, the guard must not over-fire on genuine volatility.

    Catches: the guard wrongly skipping a legitimate large move (over-firing).
    Ignores: the cross-day warning (ratio 2.20 is below the 3.0 backstop, and the
    backstop never skips anyway).
    """
    signals = [("2026-05-25T17:00:00", "FATN", "BUY", 70.0, "0.17.0")]
    snaps = [
        ("2026-05-25T07:00:00", "FATN", 3.78),   # entry day, single price
        ("2026-05-26T07:00:00", "FATN", 8.30),   # N=1 exit day, single price
    ]
    db = _make_db(tmp_path, signals, snaps)

    res = backtest_signals_from_db(db, "0.17.0", rating="BUY", hold_days=1, min_score=60.0)
    t = res[0]
    assert t.error is None
    assert t.return_pct == 119.58
    assert compute_summary(res, "BUY", 1).total_trades == 1


def test_is_straddle_date_predicate(tmp_path, no_yfinance):
    """
    is_straddle_date returns True when a date's intraday MAX/MIN ratio exceeds the
    threshold (split boundary) and False for a normal volatile day (ratio 1.4).

    Catches: the predicate mis-thresholding (firing on normal volatility or
    missing a true split), and that the threshold argument is tunable.
    Ignores: which downstream function consumes it; this asserts the detector in
    isolation.
    """
    snaps = [
        ("2026-06-12T07:00:00", "SPLIT", 2411.64),
        ("2026-06-12T16:30:00", "SPLIT", 241.16),   # ratio ~10.0
        ("2026-06-13T07:00:00", "VOL", 100.0),
        ("2026-06-13T16:30:00", "VOL", 140.0),      # ratio 1.4
    ]
    db = _make_db(tmp_path, [], snaps)
    conn = sqlite3.connect(db)
    assert is_straddle_date(conn, "SPLIT", "2026-06-12") is True
    assert is_straddle_date(conn, "VOL", "2026-06-13") is False
    # tunable: a lower threshold flags the 1.4 day too
    assert is_straddle_date(conn, "VOL", "2026-06-13", threshold=1.3) is True
    conn.close()


def test_cross_day_collapse_logs_and_skips(tmp_path, no_yfinance, caplog):
    """
    KLAC-overnight-shape: entry on a clean pre-split day (2305.86), exit on a
    clean post-split day (254.84), neither date a same-day straddle, ratio 0.11.
    Phase 2b escalates the cross-day check from log-only to SKIP, so this trade
    must be EXCLUDED from aggregates AND emit a WARNING for audit.

    Catches: a regression to log-only (the fabricated -89% surviving), or the skip
    not routing through the error-tag exclusion path (return_pct must be None).
    Ignores: same-day straddles (handled by the same-day guard) and the exact
    return magnitude; this asserts the overnight collapse is dropped.
    """
    signals = [("2026-06-11T17:00:00", "KLAC", "BUY", 70.0, "0.17.0")]
    snaps = [
        ("2026-06-11T07:00:00", "KLAC", 2305.86),   # clean pre-split entry day
        ("2026-06-18T07:00:00", "KLAC", 254.84),    # clean post-split exit day, ratio 0.11
    ]
    db = _make_db(tmp_path, signals, snaps)

    with caplog.at_level(logging.WARNING, logger="signals.backtester"):
        res = backtest_signals_from_db(db, "0.17.0", rating="BUY", hold_days=1, min_score=60.0)

    assert len(res) == 1
    assert res[0].return_pct is None, "overnight collapse must not fabricate a return"
    assert res[0].error is not None
    assert compute_summary(res, "BUY", 1).total_trades == 0, "must be excluded from aggregates"
    assert "Cross-day skip" in caplog.text


def test_normal_cross_day_move_is_kept(tmp_path, no_yfinance):
    """
    A real cross-day move inside the keep band [1/3, 3] (here +40%, ratio 1.4)
    must NOT be skipped by the cross-day guard; only extreme collapses/jumps
    outside the band are corporate-action suspects.

    Catches: the cross-day skip over-firing on legitimate volatility (a genuine
    winner wrongly excluded), which would bias the aggregates.
    Ignores: the same-day path and the warning log; only kept-vs-skipped matters.
    """
    signals = [("2026-06-01T17:00:00", "REAL", "BUY", 70.0, "0.17.0")]
    snaps = [
        ("2026-06-01T07:00:00", "REAL", 10.0),   # entry
        ("2026-06-02T07:00:00", "REAL", 14.0),   # N=1 exit, ratio 1.4 (inside keep band)
    ]
    db = _make_db(tmp_path, signals, snaps)

    res = backtest_signals_from_db(db, "0.17.0", rating="BUY", hold_days=1, min_score=60.0)
    t = res[0]
    assert t.error is None
    assert t.return_pct == 40.0
    assert compute_summary(res, "BUY", 1).total_trades == 1
