"""
Unit tests for the per-component IC validation harness (signals/validation.py).

Seed a throwaway temp SQLite with synthetic signal_scores (carrying component
columns) and screener_snapshots, then exercise the Spearman IC math, the NULL /
coverage honesty, the LOW_CONFIDENCE flag, and the reuse of the Item-1 straddle
guard in the forward-return join. Never touches the live DB or the network.
"""
import sqlite3
import pytest

from signals.validation import (
    _spearman_ic,
    component_ic,
    _forward_returns_for_cohort,
)

# signal_scores columns the harness reads; everything not in a row dict is NULL.
_TEXT = {"scored_at", "ticker", "rating", "scoring_version"}
_SIG_COLS = [
    "scored_at", "ticker", "rating", "scoring_version", "composite_score",
    "momentum_score", "quality_score", "insider_score", "reversion_score",
    "sector_strength_score", "volume_score", "earnings_score",
    "piotroski_score", "inst_own_score", "analyst_mom_score",
    "altman_penalty", "short_interest_penalty",
]


def _make_db(tmp_path, signal_rows, snapshots):
    """signal_rows: list of dicts (only the columns to set); snapshots:
    list of (scraped_at, ticker, price). Returns a Row-factory connection."""
    db_path = str(tmp_path / "val.db")
    conn = sqlite3.connect(db_path)
    coldefs = ", ".join(f"{c} {'TEXT' if c in _TEXT else 'REAL'}" for c in _SIG_COLS)
    conn.execute(f"CREATE TABLE signal_scores ({coldefs})")
    conn.execute("CREATE TABLE screener_snapshots (scraped_at TEXT, ticker TEXT, price REAL)")
    for row in signal_rows:
        cols = list(row.keys())
        conn.execute(
            f"INSERT INTO signal_scores ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
            [row[c] for c in cols],
        )
    conn.executemany(
        "INSERT INTO screener_snapshots (scraped_at,ticker,price) VALUES (?,?,?)", snapshots
    )
    conn.commit()
    conn.row_factory = sqlite3.Row
    return conn


def _sig(ticker, momentum=None, composite=70.0, **extra):
    row = {"scored_at": "2026-06-01T17:00:00", "ticker": ticker, "rating": "BUY",
           "scoring_version": "0.17.0", "composite_score": composite}
    if momentum is not None:
        row["momentum_score"] = momentum
    row.update(extra)
    return row


# ── IC math ───────────────────────────────────────

def test_spearman_ic_perfect_and_zero():
    """
    Catches: the Spearman IC math, that a perfectly rank-monotone pair is +1.0,
    a perfectly inverse pair is -1.0, and an independent pair constructed to have
    exactly zero rank covariance is 0.0.
    Ignores: the DB/join layer; this asserts the primitive on hand-built arrays.
    """
    ic_pos, n = _spearman_ic([1, 2, 3, 4, 5], [10, 20, 30, 40, 50])
    assert n == 5 and ic_pos == pytest.approx(1.0)
    ic_neg, _ = _spearman_ic([1, 2, 3, 4, 5], [50, 40, 30, 20, 10])
    assert ic_neg == pytest.approx(-1.0)
    # ranks x=[1,2,3,4], y ranks=[2,4,1,3] -> sum d^2 = 10 -> Spearman exactly 0
    ic_zero, _ = _spearman_ic([10, 20, 30, 40], [20, 40, 10, 30])
    assert ic_zero == pytest.approx(0.0, abs=1e-9)


def test_zero_variance_score_returns_none():
    """
    Catches: a constant score (zero variance) yielding None rather than a divide
    by zero, a flat component cannot rank anything.
    Ignores: the non-degenerate IC value (covered elsewhere).
    """
    ic, n = _spearman_ic([5, 5, 5, 5], [1, 2, 3, 4])
    assert ic is None and n == 4


# ── Coverage honesty + flags ──────────────────────

def test_all_null_component_is_n_zero_not_crash(tmp_path):
    """
    Catches: a component that is NULL across the whole cohort (e.g.
    short_interest_penalty for a v0.17.0 cohort) returning N=0 and a None IC,
    flagged LOW_CONFIDENCE, rather than raising.
    Ignores: the IC value of well-covered components in the same run.
    """
    signals = [_sig("AAA", momentum=70), _sig("BBB", momentum=60), _sig("CCC", momentum=80)]
    snaps = [
        ("2026-06-01T07:00:00", "AAA", 100.0), ("2026-06-02T07:00:00", "AAA", 110.0),
        ("2026-06-01T07:00:00", "BBB", 50.0), ("2026-06-02T07:00:00", "BBB", 55.0),
        ("2026-06-01T07:00:00", "CCC", 20.0), ("2026-06-02T07:00:00", "CCC", 24.0),
    ]
    conn = _make_db(tmp_path, signals, snaps)
    res = component_ic(conn, "0.17.0", "BUY", hold_days=1, min_score=60.0)
    by = {r["component"]: r for r in res}
    assert by["short_interest_penalty"]["n"] == 0
    assert by["short_interest_penalty"]["ic"] is None
    assert by["short_interest_penalty"]["confidence"] == "LOW_CONFIDENCE"
    assert by["momentum_score"]["n"] == 3  # the covered component paired all 3
    conn.close()


def test_low_confidence_flag_threshold(tmp_path):
    """
    Catches: the LOW_CONFIDENCE flag firing strictly on the N floor, a 5-pair
    component is LOW_CONFIDENCE under the default floor (30) and OK under a floor
    of 2, with the same underlying N.
    Ignores: the IC magnitude; only the flag and N matter.
    """
    moms = [70, 60, 80, 55, 90]
    signals = [_sig(f"T{i}", momentum=m) for i, m in enumerate(moms)]
    snaps = []
    for i in range(5):
        snaps += [(f"2026-06-01T07:00:00", f"T{i}", 100.0 + i),
                  (f"2026-06-02T07:00:00", f"T{i}", 110.0 + i)]
    conn = _make_db(tmp_path, signals, snaps)
    strict = {r["component"]: r for r in component_ic(conn, "0.17.0", "BUY", 1, 60.0)}
    loose = {r["component"]: r for r in component_ic(conn, "0.17.0", "BUY", 1, 60.0, low_confidence_n=2)}
    assert strict["momentum_score"]["n"] == 5
    assert strict["momentum_score"]["confidence"] == "LOW_CONFIDENCE"
    assert loose["momentum_score"]["confidence"] == "OK"
    conn.close()


def test_straddle_skipped_signal_excluded_from_pairing(tmp_path):
    """
    Catches: a corporate-action straddle leaking into an IC sample, the forward
    join must go through the Item-1 guarded fetch, so a signal whose exit date is
    a same-day straddle (ratio > 2.0) is dropped and the component N reflects the
    exclusion (3 signals in, 2 paired).
    Ignores: the IC value; this asserts the pairing COUNT and the guard reuse.
    """
    signals = [_sig("AAA", momentum=70), _sig("BBB", momentum=60), _sig("KLAC", momentum=90)]
    snaps = [
        ("2026-06-01T07:00:00", "AAA", 100.0), ("2026-06-02T07:00:00", "AAA", 110.0),
        ("2026-06-01T07:00:00", "BBB", 50.0), ("2026-06-02T07:00:00", "BBB", 55.0),
        ("2026-06-01T07:00:00", "KLAC", 2000.0),
        ("2026-06-02T07:00:00", "KLAC", 2400.0),   # exit day pre-split print
        ("2026-06-02T16:30:00", "KLAC", 240.0),    # exit day post-split -> STRADDLE
    ]
    conn = _make_db(tmp_path, signals, snaps)
    cohort = _forward_returns_for_cohort(conn, "0.17.0", "BUY", 1, 60.0)
    tickers = {row["ticker"] for row in cohort}
    assert tickers == {"AAA", "BBB"}, "straddle-exit signal must be excluded"
    by = {r["component"]: r for r in component_ic(conn, "0.17.0", "BUY", 1, 60.0)}
    assert by["momentum_score"]["n"] == 2, "IC sample must exclude the straddle-skipped signal"
    conn.close()


def test_cross_day_artefact_excluded_inherits_guard(tmp_path):
    """
    The cross-day overnight-split guard now lives in the shared
    guarded_forward_return contract, so the validation forward join inherits it
    with no cross-day code of its own. A KLAC-shape trade (pre-split entry
    2305.86, clean post-split exit 254.84 at N=5, ratio 0.11, NO same-day
    straddle on either date) must be EXCLUDED from the pairing.

    Catches: the cross-day artefact leaking into an IC sample (the exact gap this
    unification closes), proving validation reaches the shared guard.
    Ignores: the same-day straddle case (its own test) and the IC value.
    """
    signals = [_sig("AAA", momentum=70), _sig("KLAC", momentum=90)]
    snaps = [
        ("2026-06-01T07:00:00", "AAA", 100.0),
        ("2026-06-02T07:00:00", "AAA", 110.0), ("2026-06-03T07:00:00", "AAA", 111.0),
        ("2026-06-04T07:00:00", "AAA", 112.0), ("2026-06-05T07:00:00", "AAA", 113.0),
        ("2026-06-08T07:00:00", "AAA", 114.0),
        ("2026-06-01T07:00:00", "KLAC", 2305.86),   # pre-split entry day
        ("2026-06-02T07:00:00", "KLAC", 2300.0), ("2026-06-03T07:00:00", "KLAC", 2310.0),
        ("2026-06-04T07:00:00", "KLAC", 2295.0), ("2026-06-05T07:00:00", "KLAC", 2305.0),
        ("2026-06-08T07:00:00", "KLAC", 254.84),    # clean post-split N=5 exit, ratio 0.11
    ]
    conn = _make_db(tmp_path, signals, snaps)
    cohort = _forward_returns_for_cohort(conn, "0.17.0", "BUY", 5, 60.0)
    assert {row["ticker"] for row in cohort} == {"AAA"}, \
        "cross-day overnight-split artefact must be excluded via the shared guard"
    conn.close()
