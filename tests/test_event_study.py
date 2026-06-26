"""
Unit tests for the analyst-PT event-study CAR harness (signals/event_study.py).

Seed a throwaway temp SQLite with synthetic screener_snapshots (carrying sector
and price) and analyst_changes (carrying event_date and price_target_action),
then exercise the benchmark construction, the straddle-guard reuse, the
min-constituent floor, the per-event maturity filter, the abnormal-return
arithmetic, the <=0 price filter, and the future-date assertion. Never touches
the live DB or the network.

The benchmark and every step return are produced by the SAME guarded_forward_return
contract the backtester and IC harness use, so these tests also pin that the
event study inherits the corporate-action straddle guard rather than
re-deriving it.
"""
import sqlite3

import pytest

from signals.event_study import (
    build_grid,
    canonical_sectors,
    precompute_step_returns,
    compute_benchmark,
    compute_event_car,
    run_event_study,
    OK,
    IMMATURE,
)


def _db(tmp_path, snapshots, events=None):
    """snapshots: list of (scraped_at, ticker, sector, price).
    events: list of (ticker, event_date, price_target_action) or None.
    Returns (conn, db_path); conn has a committed view of both tables."""
    db_path = str(tmp_path / "es.db")
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE screener_snapshots "
        "(scraped_at TEXT, ticker TEXT, sector TEXT, price REAL)"
    )
    conn.execute(
        "CREATE TABLE analyst_changes "
        "(ticker TEXT, event_date TEXT, price_target_action TEXT)"
    )
    conn.executemany(
        "INSERT INTO screener_snapshots (scraped_at,ticker,sector,price) "
        "VALUES (?,?,?,?)", snapshots,
    )
    if events:
        conn.executemany(
            "INSERT INTO analyst_changes (ticker,event_date,price_target_action) "
            "VALUES (?,?,?)", events,
        )
    conn.commit()
    return conn, db_path


def _snap(date, ticker, sector, price):
    """One screener snapshot at 16:30 on `date` (a 'YYYY-MM-DD' string)."""
    return (f"{date}T16:30:00", ticker, sector, price)


D0, D1, D2, D3 = "2026-05-01", "2026-05-04", "2026-05-05", "2026-05-06"


# ── Guard reuse ───────────────────────────────────

def test_corporate_action_constituent_excluded_from_sector_mean(tmp_path):
    """A constituent whose D0->D1 return is a same-day corporate-action straddle
    (D1 carries both 100 and 300, intraday ratio 3.0 > the 2.0 same-day
    threshold) is dropped by guarded_forward_return, so it must NOT enter the
    sector-day mean: the surviving count is the 5 clean names and the mean is
    their mean (+3.0%), not contaminated by the split print.

    Catches: a guard-skipped constituent leaking into the benchmark (the guard
    being bypassed in the event-study path instead of reused).
    Ignores: the exact benchmark value's downstream use in a CAR (covered by the
    arithmetic test) and the cross-day backstop (only the same-day guard fires
    here).
    """
    snaps = []
    for i, t in enumerate(["T1", "T2", "T3", "T4", "T5"], start=1):
        snaps.append(_snap(D0, t, "Tech", 100.0))
        snaps.append(_snap(D1, t, "Tech", 100.0 + i))   # +1%..+5% -> mean +3%
    # SPLIT: clean D0, but D1 carries a pre- and post-split print (ratio 3.0).
    snaps.append(_snap(D0, "SPLIT", "Tech", 100.0))
    snaps.append((f"{D1}T07:00:00", "SPLIT", "Tech", 300.0))
    snaps.append((f"{D1}T16:30:00", "SPLIT", "Tech", 100.0))
    conn, _ = _db(tmp_path, snaps)

    grid = build_grid(conn)
    sectors = canonical_sectors(conn)
    step_ret = precompute_step_returns(conn, grid)
    benchmark, reliable, counts = compute_benchmark(grid, sectors, step_ret,
                                                    min_constituents=5)

    assert step_ret[("SPLIT", D1)] is None, "straddle constituent must be guard-skipped"
    assert counts[("Tech", D1)] == 5, "split print must not count as a survivor"
    assert benchmark[("Tech", D1)] == pytest.approx(3.0)
    assert ("Tech", D1) in reliable


# ── Min-constituent floor ─────────────────────────

def test_min_constituent_floor_marks_four_unreliable_five_reliable(tmp_path):
    """A sector-day with 4 surviving constituents is below the floor of 5 and
    must be marked unreliable (absent from `reliable`); a sibling sector-day with
    exactly 5 survivors clears the floor and is reliable.

    Catches: an off-by-one in the floor (4 wrongly kept, or 5 wrongly dropped).
    Ignores: the benchmark mean values themselves (reliability is independent of
    the mean) and any event-level consequence (covered by the maturity test).
    """
    snaps = []
    for i, t in enumerate(["F1", "F2", "F3", "F4"], start=1):   # 4 in Fin
        snaps.append(_snap(D0, t, "Fin", 100.0))
        snaps.append(_snap(D1, t, "Fin", 100.0 + i))
    for i, t in enumerate(["E1", "E2", "E3", "E4", "E5"], start=1):  # 5 in Egy
        snaps.append(_snap(D0, t, "Egy", 100.0))
        snaps.append(_snap(D1, t, "Egy", 100.0 + i))
    conn, _ = _db(tmp_path, snaps)

    grid = build_grid(conn)
    sectors = canonical_sectors(conn)
    step_ret = precompute_step_returns(conn, grid)
    _, reliable, counts = compute_benchmark(grid, sectors, step_ret, min_constituents=5)

    assert counts[("Fin", D1)] == 4 and ("Fin", D1) not in reliable
    assert counts[("Egy", D1)] == 5 and ("Egy", D1) in reliable


# ── Per-event maturity ────────────────────────────

def test_immature_event_excluded_not_zero_padded(tmp_path):
    """An event whose ticker is ragged inside the window (priced D0,D1,D2 but
    NOT D3, so the final grid step has no return) must return IMMATURE with a
    None CAR, never a zero-padded OK with a fabricated CAR of 0.

    Catches: zero-padding a missing forward step into a spurious OK observation.
    Ignores: the LOW_CONFIDENCE path (the benchmark is reliable here) and the
    universe-truncation flavour of immaturity (too-recent events); this isolates
    the ragged-ticker flavour.
    """
    snaps = []
    # 5 filler constituents keep "Tech" reliable on every step D1..D3.
    for i, t in enumerate(["C1", "C2", "C3", "C4", "C5"], start=1):
        for d in (D0, D1, D2, D3):
            snaps.append(_snap(d, t, "Tech", 100.0 + i))
    # EVT trades D0,D1,D2 but is missing D3 -> ragged in a window of 3.
    snaps.append(_snap(D0, "EVT", "Tech", 100.0))
    snaps.append(_snap(D1, "EVT", "Tech", 110.0))
    snaps.append(_snap(D2, "EVT", "Tech", 121.0))
    conn, _ = _db(tmp_path, snaps)

    grid = build_grid(conn)                      # [D0, D1, D2, D3]
    sectors = canonical_sectors(conn)
    step_ret = precompute_step_returns(conn, grid)
    benchmark, reliable, _ = compute_benchmark(grid, sectors, step_ret, min_constituents=5)

    status, car = compute_event_car(
        "EVT", D0, sectors, grid, step_ret, benchmark, reliable,
        substrate_max=grid[-1], window=3,
    )
    assert status == IMMATURE
    assert car is None


# ── Abnormal-return arithmetic ────────────────────

def test_abnormal_return_arithmetic_known_fixture(tmp_path):
    """A hand-constructed event over a 2-step window. EVT returns +10% each step;
    five sector peers return +4% each step. With EVT itself a constituent of its
    own sector, the benchmark is mean(+10, +4x5) = +5.0% each step, so the daily
    abnormal return is +5.0% each step and CAR = +10.0%.

    Catches: a sign or summation error in CAR = sum(event_ret - benchmark_ret),
    and silently dropping the event ticker from its own sector benchmark.
    Ignores: guard/floor/maturity edge cases (each has its own test); all inputs
    here are clean and reliable.
    """
    snaps = []
    snaps.append(_snap(D0, "EVT", "Tech", 100.0))
    snaps.append(_snap(D1, "EVT", "Tech", 110.0))    # +10%
    snaps.append(_snap(D2, "EVT", "Tech", 121.0))    # +10%
    for t in ["P1", "P2", "P3", "P4", "P5"]:
        snaps.append(_snap(D0, t, "Tech", 100.0))
        snaps.append(_snap(D1, t, "Tech", 104.0))    # +4%
        snaps.append(_snap(D2, t, "Tech", 108.16))   # +4%
    conn, _ = _db(tmp_path, snaps)

    grid = build_grid(conn)                      # [D0, D1, D2]
    sectors = canonical_sectors(conn)
    step_ret = precompute_step_returns(conn, grid)
    benchmark, reliable, _ = compute_benchmark(grid, sectors, step_ret, min_constituents=5)

    # Benchmark each step = mean(+10, +4, +4, +4, +4, +4) = +5.0
    assert benchmark[("Tech", D1)] == pytest.approx(5.0)
    assert benchmark[("Tech", D2)] == pytest.approx(5.0)

    status, car = compute_event_car(
        "EVT", D0, sectors, grid, step_ret, benchmark, reliable,
        substrate_max=grid[-1], window=2,
    )
    assert status == OK
    assert car == pytest.approx(10.0)            # (10-5) + (10-5)


# ── <=0 price filter ──────────────────────────────

def test_non_positive_price_is_filtered(tmp_path):
    """A constituent priced 0.0 on D0 has no usable entry, so its D0->D1 step is
    not formed and it is excluded from the sector-day survivors: the count is the
    5 clean names, and the zero-priced ticker has no step return.

    Catches: a <=0 screener price being treated as a real price and either
    fabricating a return or inflating the constituent count.
    Ignores: NULL prices (filtered identically upstream) and negative prices
    (absent from the production substrate, verified at build time).
    """
    snaps = []
    for i, t in enumerate(["Z1", "Z2", "Z3", "Z4", "Z5"], start=1):
        snaps.append(_snap(D0, t, "Zed", 100.0))
        snaps.append(_snap(D1, t, "Zed", 100.0 + i))
    snaps.append(_snap(D0, "ZERO", "Zed", 0.0))     # non-positive entry
    snaps.append(_snap(D1, "ZERO", "Zed", 100.0))
    conn, _ = _db(tmp_path, snaps)

    grid = build_grid(conn)
    sectors = canonical_sectors(conn)
    step_ret = precompute_step_returns(conn, grid)
    _, _, counts = compute_benchmark(grid, sectors, step_ret, min_constituents=5)

    assert step_ret.get(("ZERO", D1)) is None, "zero-priced entry must not form a step"
    assert counts[("Zed", D1)] == 5, "zero-priced ticker must not count as a survivor"


# ── Future-date guard ─────────────────────────────

def test_future_dated_event_asserted_out_and_never_priced(tmp_path):
    """A future-dated event (event_date after the substrate's max trading date)
    must never reach return computation: compute_event_car asserts on it, and
    run_event_study tallies it under future_dropped without producing an OK
    observation, while a same-ticker in-window event still prices to OK.

    Catches: a post-dated analyst row (the substrate holds event_date up to
    2026-10-05) leaking a CAR computed off prices that do not exist yet.
    Ignores: the magnitude of the in-window CAR (covered by the arithmetic test);
    this only pins the future row's exclusion and the live row's survival.
    """
    snaps = []
    snaps.append(_snap(D0, "EVT", "Tech", 100.0))
    snaps.append(_snap(D1, "EVT", "Tech", 110.0))
    snaps.append(_snap(D2, "EVT", "Tech", 121.0))
    snaps.append(_snap(D0, "FILL", "Tech", 100.0))
    snaps.append(_snap(D1, "FILL", "Tech", 105.0))
    snaps.append(_snap(D2, "FILL", "Tech", 110.0))
    events = [
        ("EVT", D0, "Raises"),             # in-window -> OK
        ("EVT", "2099-01-01", "Lowers"),   # future -> future_dropped
    ]
    conn, db_path = _db(tmp_path, snaps, events)

    grid = build_grid(conn)
    sectors = canonical_sectors(conn)
    step_ret = precompute_step_returns(conn, grid)
    benchmark, reliable, _ = compute_benchmark(grid, sectors, step_ret, min_constituents=1)

    # Belt-and-braces: pricing a future event directly is an assertion failure.
    with pytest.raises(AssertionError):
        compute_event_car(
            "EVT", "2099-01-01", sectors, grid, step_ret, benchmark, reliable,
            substrate_max=grid[-1], window=2,
        )

    # Orchestrator: future row tallied out, in-window row survives to OK.
    res = run_event_study(db_path, window=2, min_constituents=1)
    assert res["groups"]["Lowers"]["future_dropped"] == 1
    assert res["groups"]["Lowers"]["n_ok"] == 0
    assert res["groups"]["Raises"]["n_ok"] == 1
