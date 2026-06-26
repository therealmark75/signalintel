# signals/validation.py
# ─────────────────────────────────────────────────
# Per-component Information Coefficient (IC) validation harness.
#
# Read-only analytics over persisted signal_scores, priced forward through the
# Item-1 straddle-guarded fetch path in signals/backtester.py. Answers the
# harness's core question: does each component score actually rank-predict the
# forward return?
#
# IC here is the Spearman rank correlation between a component's score and the
# signal's forward return at horizon N. Forward returns come ONLY through
# guarded_forward_return (the single Item-1 guard contract: same-day straddle
# plus cross-day overnight-split), so a guarded-out signal never leaks into a
# pairing: it is dropped from EVERY component's sample, and each result's N
# reflects that. This module adds no guard logic of its own.
#
# NOT scoring code: no scoring math, no version bump (engine stays 0.19.0).
# ─────────────────────────────────────────────────
from __future__ import annotations

import logging
import math
import sqlite3

from signals.backtester import guarded_forward_return

logger = logging.getLogger(__name__)

# The 12 component columns plus composite_score, every score we can rank against
# forward returns. Order is display-only; results are returned sorted by IC.
COMPONENT_COLUMNS = [
    "momentum_score", "quality_score", "insider_score", "reversion_score",
    "sector_strength_score", "volume_score", "earnings_score",
    "piotroski_score", "inst_own_score", "analyst_mom_score",
    "altman_penalty", "short_interest_penalty", "composite_score",
]

# Below this paired-sample size an IC is flagged LOW_CONFIDENCE (never suppressed,
# just flagged). 30 is the conventional small-sample floor for a correlation to
# carry any signal; documented and tunable, not load-bearing on scoring.
LOW_CONFIDENCE_N = 30


# ── Rank-correlation primitives ───────────────────

def _rank(vals: list[float]) -> list[float]:
    """Average (fractional) ranks, 1-based; tied values share the mean of their
    rank positions so equal scores do not get an arbitrary order."""
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    ranks = [0.0] * len(vals)
    i = 0
    while i < len(vals):
        j = i
        while j + 1 < len(vals) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0  # mean of 0-based positions i..j, made 1-based
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _spearman_ic(xs: list[float], ys: list[float]):
    """Spearman rank IC between paired xs and ys. Returns (ic, n). ic is None
    when n < 2 or either series has zero variance (a constant score cannot rank
    anything)."""
    n = len(xs)
    if n < 2:
        return None, n
    rx, ry = _rank(xs), _rank(ys)
    mx, my = sum(rx) / n, sum(ry) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    vx = sum((a - mx) ** 2 for a in rx)
    vy = sum((b - my) ** 2 for b in ry)
    if vx == 0 or vy == 0:
        return None, n
    return cov / math.sqrt(vx * vy), n


def _t_stat(ic, n):
    """Significance proxy: t = IC * sqrt(N-2) / sqrt(1 - IC^2). None if undefined;
    inf at |IC| = 1 (perfect rank correlation, zero residual)."""
    if ic is None or n is None or n < 3:
        return None
    denom = 1.0 - ic * ic
    if denom <= 0:
        return float("inf")
    return ic * math.sqrt(n - 2) / math.sqrt(denom)


# ── Cohort forward returns (via the Item-1 guarded fetch path) ──

def _forward_returns_for_cohort(conn, scoring_version, rating, hold_days, min_score):
    """One row per (ticker, signal day) for the cohort, carrying every component
    score plus the forward return at hold_days.

    Forward return is computed ONLY through guarded_forward_return (the single
    straddle + cross-day guard contract in signals/backtester.py). A signal whose
    entry or exit is unpriceable, lands on a same-day corporate-action straddle,
    OR crosses an overnight split is skipped there (ok=False) and dropped here, so
    it cannot enter any component's IC sample. No guard logic lives in this module.
    """
    cols = ", ".join(COMPONENT_COLUMNS)
    rows = conn.execute(
        f"""
        SELECT ticker, DATE(scored_at) AS signal_date, {cols}
        FROM signal_scores s
        WHERE rating = ? AND scoring_version = ? AND composite_score >= ?
          AND scored_at = (
              SELECT MAX(scored_at) FROM signal_scores s2
              WHERE s2.ticker = s.ticker
                AND DATE(s2.scored_at) = DATE(s.scored_at)
                AND s2.scoring_version = s.scoring_version
          )
        GROUP BY ticker, DATE(scored_at)
        """,
        (rating, scoring_version, min_score),
    ).fetchall()

    cohort = []
    for r in rows:
        d = dict(r)
        fr = guarded_forward_return(conn, d["ticker"], d["signal_date"], hold_days)
        if not fr.ok:
            continue
        d["forward_return"] = fr.return_pct
        cohort.append(d)
    return cohort


def component_ic(conn, scoring_version, rating, hold_days,
                 min_score=60.0, low_confidence_n=LOW_CONFIDENCE_N):
    """Per-component Spearman IC for one (scoring_version, rating, horizon)
    cohort. Returns a list of dicts sorted by IC desc, each carrying:
    component, ic, n, t_stat, confidence, coverage_first, coverage_last.

    NULL handling (NOT scoring, so P5 deliberately does NOT apply): a signal with
    a NULL component score is excluded from THAT component's pairing only. We do
    NOT coerce a missing input to neutral 50 the way the scorer does, because
    coercion would invent a rank and bias the IC. Each result's n is the
    post-exclusion paired count, and coverage_first/last bound the signal dates
    actually used, so a thin or absent component is visible, not hidden.
    """
    cohort = _forward_returns_for_cohort(conn, scoring_version, rating, hold_days, min_score)

    results = []
    for comp in COMPONENT_COLUMNS:
        present = [row for row in cohort if row[comp] is not None]
        xs = [row[comp] for row in present]
        ys = [row["forward_return"] for row in present]
        ic, n = _spearman_ic(xs, ys)
        dates = [row["signal_date"] for row in present]
        results.append({
            "component": comp,
            "ic": ic,
            "n": n,
            "t_stat": _t_stat(ic, n),
            "confidence": "LOW_CONFIDENCE" if (n is None or n < low_confidence_n) else "OK",
            "coverage_first": min(dates) if dates else None,
            "coverage_last": max(dates) if dates else None,
        })
    results.sort(key=lambda r: (r["ic"] if r["ic"] is not None else -2.0), reverse=True)
    return results


def ic_report(db_path, scoring_version="0.17.0", rating="BUY",
              horizons=(1, 5), min_score=60.0):
    """Run component_ic across horizons for a cohort. Returns {horizon: [rows]}.
    Read-only; opens and closes its own connection."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return {h: component_ic(conn, scoring_version, rating, h, min_score)
                for h in horizons}
    finally:
        conn.close()


def format_ic_report(report, scoring_version="0.17.0", rating="BUY") -> str:
    """Human-readable table of an ic_report() result."""
    lines = []
    for horizon in sorted(report):
        lines.append(f"\n=== IC report  v{scoring_version} {rating}  N={horizon} ===")
        lines.append(f"{'component':<24} {'IC':>8} {'N':>6} {'t_stat':>8}  {'flag':<14} coverage")
        for r in report[horizon]:
            ic = "n/a" if r["ic"] is None else f"{r['ic']:+.4f}"
            t = "n/a" if r["t_stat"] is None else (
                "inf" if r["t_stat"] == float("inf") else f"{r['t_stat']:+.2f}")
            cov = "-" if r["coverage_first"] is None else f"{r['coverage_first']} to {r['coverage_last']}"
            lines.append(f"{r['component']:<24} {ic:>8} {r['n']:>6} {t:>8}  {r['confidence']:<14} {cov}")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config.constants import DATABASE_PATH
    rep = ic_report(DATABASE_PATH, scoring_version="0.17.0", rating="BUY", horizons=(1, 5))
    print(format_ic_report(rep))
