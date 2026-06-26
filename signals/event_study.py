# signals/event_study.py
# ─────────────────────────────────────────────────
# Analyst price-target event-study CAR harness (in-sourced).
#
# In-sources the external analyst-PT event study (25 May 2026): group analyst
# price-target actions into Raises / Maintains / Lowers, measure each group's
# cumulative abnormal return (CAR) over a forward window, and check whether the
# group means are monotonically ordered (Raises > Maintains > Lowers).
#
# EVENT SOURCE: analyst_changes (event_date, price_target_action). NOT
# rating_changes (which carries SignalIntel tier transitions, no PT-action
# labels). One analyst action row = one event; the same (ticker, event_date)
# price path is shared across firm rows and cached.
#
# PRICE / BENCHMARK BASIS (read before trusting any number):
#   Returns come ONLY from the persisted screener_snapshots.price series, priced
#   through guarded_forward_return (signals/backtester.py) at hold_days=1 per
#   step. That column is an intraday FinViz SPOT price, not split/dividend
#   adjusted, several snapshots per day (canonicalised to MAX(scraped_at)). The
#   benchmark (locked source B) is the per-sector per-day mean of constituent
#   daily returns; sector_performance is NOT used (it has no daily-return
#   column). Every event-ticker AND every benchmark-constituent return inherits
#   the one straddle guard contract; a guard-skipped return is excluded from the
#   sector mean and makes a dependent event ragged.
#
# GRID ALIGNMENT (design decision, load-bearing):
#   CAR = sum of daily abnormal returns. To make that sum well defined under
#   ragged per-ticker coverage, returns are computed on the UNIVERSE trading-date
#   grid (distinct DATE(scraped_at)). An event anchors to the first grid date >=
#   its event_date; the window is the next WINDOW grid steps. An event is mature
#   only if the event ticker has a guard-clean return on ALL WINDOW grid steps
#   (this realises the per-ticker >=WINDOW-depth filter on the grid so event and
#   benchmark align exactly). Ragged or guard-skipped within the window => the
#   event is IMMATURE and dropped, never zero-padded.
#
# SUBSTRATE BOUNDS:
#   - Upper (future guard, belt-and-braces): an event with event_date later than
#     the substrate's max trading date can never be priced. compute_event_car
#     asserts it; run_event_study filters it into a future_dropped tally first.
#   - Lower: an event before the substrate's first trading date has no
#     contemporaneous prices and is OUT_OF_SUBSTRATE (dropped), never anchored
#     forward onto unrelated later prices.
#
# Read-only analytics. No scoring math, no scoring path touched, engine stays
# 0.19.0. The LOW_CONFIDENCE flag vocabulary mirrors signals/validation.py.
# ─────────────────────────────────────────────────
from __future__ import annotations

import logging
import sqlite3
import statistics
from bisect import bisect_left

from signals.backtester import guarded_forward_return

logger = logging.getLogger(__name__)

# Forward CAR window in TRADING days (grid steps). 21 matches the external study.
CAR_WINDOW = 21

# Minimum guard-surviving constituents for a sector-day benchmark to be trusted.
# A sector-day below this floor is unreliable; any event whose window touches it
# is dropped to LOW_CONFIDENCE (mirrors the validation.py LOW_CONFIDENCE flag).
MIN_CONSTITUENTS = 5

# The only PT-action classes in scope, exact-case. The 6 case-variant rows
# (lowers/raises/LOwers) and Announces/Removes/Adjusts/NULL are out of scope.
PT_ACTIONS = ("Raises", "Maintains", "Lowers")

# Event outcome statuses.
OK = "OK"
IMMATURE = "IMMATURE"               # ticker ragged/guard-skipped within window
LOW_CONFIDENCE = "LOW_CONFIDENCE"   # window touches an unreliable sector-day
NO_SECTOR = "NO_SECTOR"             # event ticker has no screener sector
OUT_OF_SUBSTRATE = "OUT_OF_SUBSTRATE"  # event_date before the price substrate


# ── Substrate readers ─────────────────────────────

def build_grid(conn: sqlite3.Connection) -> list[str]:
    """Sorted distinct trading dates (DATE(scraped_at)) carrying a positive
    price in screener_snapshots. This is the universe grid every return is
    measured on. Ascending; ISO 'YYYY-MM-DD' strings sort chronologically."""
    rows = conn.execute(
        """
        SELECT DISTINCT DATE(scraped_at) AS d
        FROM screener_snapshots
        WHERE price IS NOT NULL AND price > 0
        ORDER BY d ASC
        """
    ).fetchall()
    return [r[0] for r in rows]


def canonical_sectors(conn: sqlite3.Connection) -> dict[str, str]:
    """{ticker: sector} using each ticker's LATEST non-empty sector. One source
    for both the event ticker's sector and the benchmark constituents, so the
    vocabulary is exact-match by construction (no mapping)."""
    rows = conn.execute(
        """
        SELECT s.ticker, s.sector
        FROM screener_snapshots s
        WHERE s.sector IS NOT NULL AND s.sector <> ''
          AND s.scraped_at = (
              SELECT MAX(s2.scraped_at) FROM screener_snapshots s2
              WHERE s2.ticker = s.ticker
                AND s2.sector IS NOT NULL AND s2.sector <> ''
          )
        GROUP BY s.ticker
        """
    ).fetchall()
    return {r[0]: r[1] for r in rows}


def _ticker_priced_dates(conn: sqlite3.Connection) -> dict[str, set]:
    """{ticker: {priced grid dates}} where the ticker has at least one positive
    price that day. Used only to decide which grid steps a ticker can possibly
    contribute to; the RETURN itself is always computed by guarded_forward_return
    so the straddle guard stays single-sourced."""
    rows = conn.execute(
        """
        SELECT ticker, DATE(scraped_at) AS d
        FROM screener_snapshots
        WHERE price IS NOT NULL AND price > 0
        GROUP BY ticker, DATE(scraped_at)
        """
    ).fetchall()
    out: dict[str, set] = {}
    for ticker, d in rows:
        out.setdefault(ticker, set()).add(d)
    return out


# ── Step returns (the single guarded contract per grid step) ──

def precompute_step_returns(conn: sqlite3.Connection, grid: list[str]) -> dict:
    """step_ret[(ticker, d_cur)] = the guard-checked 1-trading-day return for the
    grid step ending at d_cur (from its immediate grid predecessor), expressed in
    PERCENT, for every ticker that is priced on both grid endpoints.

    The value is guarded_forward_return(conn, ticker, d_prev, 1).return_pct when
    that contract returns ok=True. A guard SKIP (same-day straddle or cross-day
    overnight split) stores None, so the constituent is excluded from that
    sector-day mean and a dependent event is ragged. No guard logic lives here:
    this function only decides which (ticker, step) pairs exist and delegates the
    return (and both guards) to guarded_forward_return.
    """
    date_index = {d: i for i, d in enumerate(grid)}
    ticker_dates = _ticker_priced_dates(conn)
    step_ret: dict = {}
    total = len(ticker_dates)
    for n, (ticker, dates) in enumerate(ticker_dates.items()):
        if n and n % 2000 == 0:
            logger.info("precompute_step_returns: %d/%d tickers", n, total)
        for d_cur in dates:
            i = date_index[d_cur]
            if i == 0:
                continue  # no predecessor grid date
            d_prev = grid[i - 1]
            if d_prev not in dates:
                continue  # ticker not priced on the predecessor grid date
            fr = guarded_forward_return(conn, ticker, d_prev, 1)
            step_ret[(ticker, d_cur)] = fr.return_pct if fr.ok else None
    return step_ret


# ── Benchmark (per-sector per-day mean of constituent returns) ──

def compute_benchmark(grid: list[str], sectors: dict[str, str], step_ret: dict,
                      min_constituents: int = MIN_CONSTITUENTS):
    """Build the per-sector per-day benchmark from already-guarded step returns.

    Returns (benchmark, reliable, counts):
      benchmark[(sector, d_cur)] = mean constituent return (PERCENT) for every
          cell with >=1 surviving constituent.
      reliable = set of (sector, d_cur) cells with >= min_constituents survivors.
      counts[(sector, d_cur)] = surviving-constituent count for the cell.

    A constituent survives a cell iff step_ret[(ticker, d_cur)] is a number (not
    None and not absent); a guard-skipped or non-trading constituent is excluded,
    so the mean is over guard-clean constituents only.
    """
    members_by_sector: dict[str, list[str]] = {}
    for ticker, sector in sectors.items():
        members_by_sector.setdefault(sector, []).append(ticker)

    benchmark: dict = {}
    reliable: set = set()
    counts: dict = {}
    for i in range(1, len(grid)):
        d_cur = grid[i]
        for sector, members in members_by_sector.items():
            survivors = [step_ret[(t, d_cur)] for t in members
                         if step_ret.get((t, d_cur)) is not None]
            n = len(survivors)
            counts[(sector, d_cur)] = n
            if n >= 1:
                benchmark[(sector, d_cur)] = sum(survivors) / n
            if n >= min_constituents:
                reliable.add((sector, d_cur))
    return benchmark, reliable, counts


# ── Per-event CAR ─────────────────────────────────

def compute_event_car(ticker: str, event_date: str, sectors: dict[str, str],
                      grid: list[str], step_ret: dict, benchmark: dict,
                      reliable: set, substrate_max: str, window: int = CAR_WINDOW):
    """CAR for one event. Returns (status, car). car is a number only when
    status == OK (PERCENT, the summed daily abnormal return); otherwise None.

    Future guard (belt-and-braces): asserts event_date <= substrate_max. The
    orchestrator filters future events out first, so this assert documents the
    invariant and fires only if a future event ever reaches pricing.

    Statuses: OK; NO_SECTOR (ticker has no screener sector); OUT_OF_SUBSTRATE
    (event_date before the substrate's first grid date); IMMATURE (fewer than
    `window` grid dates ahead, OR the ticker is ragged / guard-skipped on any of
    the window's grid steps, never zero-padded); LOW_CONFIDENCE (the window
    touches a sector-day with fewer than MIN_CONSTITUENTS survivors).
    """
    assert event_date <= substrate_max, (
        f"future-dated event {ticker} {event_date} must never be priced "
        f"(substrate max {substrate_max})"
    )

    sector = sectors.get(ticker)
    if sector is None:
        return NO_SECTOR, None
    if event_date < grid[0]:
        return OUT_OF_SUBSTRATE, None

    anchor = bisect_left(grid, event_date)  # first grid index with grid[i] >= event_date
    if anchor + window >= len(grid):
        return IMMATURE, None  # not enough forward grid dates yet (trailing by design)

    car = 0.0
    for t in range(1, window + 1):
        d_cur = grid[anchor + t]
        ev = step_ret.get((ticker, d_cur))
        if ev is None:
            return IMMATURE, None  # ragged / guard-skipped: not zero-padded
        if (sector, d_cur) not in reliable:
            return LOW_CONFIDENCE, None
        car += ev - benchmark[(sector, d_cur)]
    return OK, car


# ── Orchestrator ──────────────────────────────────

def run_event_study(db_path: str, window: int = CAR_WINDOW,
                    min_constituents: int = MIN_CONSTITUENTS,
                    actions: tuple = PT_ACTIONS) -> dict:
    """Run the full analyst-PT CAR study. Read-only; opens and closes its own
    connection. Returns a structured result dict consumed by format_report."""
    conn = sqlite3.connect(db_path)
    try:
        grid = build_grid(conn)
        if len(grid) < window + 1:
            raise ValueError(
                f"price substrate has {len(grid)} grid dates, need >= {window + 1} "
                f"for a {window}-step CAR"
            )
        substrate_max = grid[-1]
        sectors = canonical_sectors(conn)
        logger.info("event study: %d grid dates, %d tickers with a sector",
                    len(grid), len(sectors))
        step_ret = precompute_step_returns(conn, grid)
        benchmark, reliable, counts = compute_benchmark(
            grid, sectors, step_ret, min_constituents)

        event_rows = conn.execute(
            """
            SELECT ticker, event_date, price_target_action
            FROM analyst_changes
            WHERE price_target_action IN ({})
            """.format(",".join("?" * len(actions))),
            actions,
        ).fetchall()
    finally:
        conn.close()

    # Per-group tallies.
    groups = {a: {"cars": [], "immature": 0, "low_confidence": 0,
                  "no_sector": 0, "out_of_substrate": 0, "future_dropped": 0}
              for a in actions}
    car_cache: dict = {}  # (ticker, event_date) -> (status, car)

    for ticker, event_date, action in event_rows:
        g = groups[action]
        if event_date > substrate_max:
            g["future_dropped"] += 1  # never priced (future guard)
            continue
        key = (ticker, event_date)
        if key not in car_cache:
            car_cache[key] = compute_event_car(
                ticker, event_date, sectors, grid, step_ret,
                benchmark, reliable, substrate_max, window)
        status, car = car_cache[key]
        if status == OK:
            g["cars"].append(car)
        elif status == IMMATURE:
            g["immature"] += 1
        elif status == LOW_CONFIDENCE:
            g["low_confidence"] += 1
        elif status == NO_SECTOR:
            g["no_sector"] += 1
        elif status == OUT_OF_SUBSTRATE:
            g["out_of_substrate"] += 1

    group_out = {}
    for a in actions:
        cars = groups[a]["cars"]
        group_out[a] = {
            "n_ok": len(cars),
            "mean_car": (sum(cars) / len(cars)) if cars else None,
            "immature": groups[a]["immature"],
            "low_confidence": groups[a]["low_confidence"],
            "no_sector": groups[a]["no_sector"],
            "out_of_substrate": groups[a]["out_of_substrate"],
            "future_dropped": groups[a]["future_dropped"],
        }

    cell_counts = list(counts.values())
    distribution = {
        "cells": len(cell_counts),
        "min": min(cell_counts) if cell_counts else None,
        "median": statistics.median(cell_counts) if cell_counts else None,
        "max": max(cell_counts) if cell_counts else None,
        "unreliable_cells": sum(1 for c in cell_counts if c < min_constituents),
    }

    monotonic = _monotonic_check(group_out, actions)

    return {
        "window": window,
        "min_constituents": min_constituents,
        "grid_dates": len(grid),
        "substrate_first": grid[0],
        "substrate_max": substrate_max,
        "n_tickers_with_sector": len(sectors),
        "groups": group_out,
        "constituent_distribution": distribution,
        "monotonic": monotonic,
    }


def _monotonic_check(group_out: dict, actions: tuple) -> dict:
    """Raises > Maintains > Lowers on mean CAR. Pass is False (not None) when any
    group has no OK events, so an undefined ordering never reads as a pass."""
    r = group_out.get("Raises", {}).get("mean_car")
    m = group_out.get("Maintains", {}).get("mean_car")
    l = group_out.get("Lowers", {}).get("mean_car")
    if r is None or m is None or l is None:
        return {"pass": False, "raises": r, "maintains": m, "lowers": l,
                "note": "ordering undefined (a group has no OK events)"}
    return {"pass": bool(r > m > l), "raises": r, "maintains": m, "lowers": l,
            "note": None}


# ── Reporting ─────────────────────────────────────

def format_report(result: dict) -> str:
    """Human-readable summary of a run_event_study result."""
    lines = []
    lines.append("=== Analyst-PT event-study CAR ===")
    lines.append(
        f"window={result['window']} trading days | min_constituents="
        f"{result['min_constituents']} | grid {result['substrate_first']} to "
        f"{result['substrate_max']} ({result['grid_dates']} dates) | "
        f"{result['n_tickers_with_sector']} tickers with a sector"
    )
    d = result["constituent_distribution"]
    lines.append(
        f"constituents/sector-day: min={d['min']} median={d['median']} "
        f"max={d['max']}  ({d['unreliable_cells']}/{d['cells']} cells below floor)"
    )
    lines.append("")
    lines.append(f"{'action':<10} {'mean_CAR%':>10} {'N_ok':>7} {'immature':>9} "
                 f"{'lowconf':>8} {'out_sub':>8} {'no_sec':>7} {'future':>7}")
    for a in ("Raises", "Maintains", "Lowers"):
        g = result["groups"][a]
        mc = "n/a" if g["mean_car"] is None else f"{g['mean_car']:+.4f}"
        lines.append(
            f"{a:<10} {mc:>10} {g['n_ok']:>7} {g['immature']:>9} "
            f"{g['low_confidence']:>8} {g['out_of_substrate']:>8} "
            f"{g['no_sector']:>7} {g['future_dropped']:>7}"
        )
    mo = result["monotonic"]
    lines.append("")
    if mo["raises"] is None or mo["maintains"] is None or mo["lowers"] is None:
        lines.append(f"monotonic (Raises>Maintains>Lowers): FAIL  ({mo['note']})")
    else:
        verdict = "PASS" if mo["pass"] else "FAIL"
        lines.append(
            f"monotonic (Raises>Maintains>Lowers): {verdict}  "
            f"Raises {mo['raises']:+.4f} | Maintains {mo['maintains']:+.4f} | "
            f"Lowers {mo['lowers']:+.4f}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    from config.constants import DATABASE_PATH
    res = run_event_study(DATABASE_PATH)
    print(format_report(res))
