# signals/event_study_strata.py
# ─────────────────────────────────────────────────
# Decile stratification of the analyst-PT event-study CAR.
#
# The headline study (signals/event_study.py) showed Raises > Maintains > Lowers
# on mean CAR. This module asks the finer question: does the effect scale with
# the MAGNITUDE of the price-target revision, not just its sign? It cuts the same
# matured OK cohort into deciles of signed PT percent-change and reports mean CAR
# per decile.
#
# STRATIFIER: signed PT percent-change = (current_price_target - prior_price_target)
#   / prior_price_target * 100, pooled across all three actions. Rows with
#   prior_price_target <= 0 are dropped (undefined / ratio-explosive) and tallied.
#
# CAR REUSE: every CAR comes from event_study.compute_event_car against one
#   event_study.prepare_substrate. This module NEVER recomputes a CAR, rebuilds
#   the benchmark, or touches the straddle guard. It only assigns deciles over
#   pct-change and averages the already-computed CARs. All event_study locks
#   (matured-only, grid-clean >=21 depth, source-B benchmark, guarded_forward_return,
#   min-constituent floor 5, LOW_CONFIDENCE vocabulary) carry because the CAR is
#   byte-identical to the headline study's.
#
# TWO CUTS (both reported):
#   1. Headline: NTILE(10) over signed pct-change, pooled. The 697 zero-revision
#      (Maintains) rows are a point mass at 0.0 that NTILE splits across the two
#      deciles straddling zero, fuzzing those cells.
#   2. Zero-bucket robustness: carve the zero-revision rows into a neutral bucket
#      and decile ONLY the non-zero signed revisions. The two cuts are compared;
#      a disagreement on monotonicity is reported, not papered over.
#
# LABEL-VS-SIGN AUDIT: counts rows whose price_target_action label contradicts
#   the sign of its numeric pct-change (a "Lowers" that raised the target, etc.),
#   split by whether prior_price_target was near-zero (ratio-inflation / likely
#   corporate-action artefact) vs a genuine mislabel. Reported, not acted on.
#
# Read-only analytics. Engine stays 0.19.0, no scoring path touched.
# ─────────────────────────────────────────────────
from __future__ import annotations

import logging
import sqlite3

from signals.event_study import (
    PT_ACTIONS,
    OK,
    prepare_substrate,
    compute_event_car,
)

logger = logging.getLogger(__name__)

DECILES = 10
NEAR_ZERO_PRIOR = 1.0  # prior target below this $ is a ratio-inflation suspect


# ── Pure helpers (substrate-free, directly unit-testable) ──

def pct_change(current, prior):
    """Signed percent change of a price-target revision, or None when it is
    undefined: prior is None/<=0 (ratio explosive or meaningless) or current is
    None. Returns a float in PERCENT (120 vs 100 -> +20.0)."""
    if current is None or prior is None or prior <= 0:
        return None
    return (current - prior) / prior * 100.0


def assign_deciles(values, groups=DECILES):
    """NTILE(groups) decile label (1..groups) per input value, matching SQLite's
    NTILE: values sorted ascending, split into `groups` contiguous buckets, the
    first (n mod groups) buckets one larger. Ties are split by sort position
    exactly as SQL NTILE does, so the headline cut reproduces the Phase 1 SQL
    boundaries. Returns a list aligned to the input order."""
    n = len(values)
    if n == 0:
        return []
    order = sorted(range(n), key=lambda i: values[i])
    base, rem = divmod(n, groups)
    labels = [0] * n
    idx = 0
    for g in range(1, groups + 1):
        size = base + 1 if g <= rem else base
        for _ in range(size):
            labels[order[idx]] = g
            idx += 1
    return labels


def _strictly_increasing(seq):
    """True iff every element is strictly greater than its predecessor. None
    elements (empty deciles) make it False, never silently skipped."""
    if any(x is None for x in seq) or len(seq) < 2:
        return False
    return all(b > a for a, b in zip(seq, seq[1:]))


def _inversions(seq):
    """Count adjacent pairs that go DOWN (a partial-monotonicity gauge). None
    elements count as an inversion."""
    if len(seq) < 2:
        return 0
    inv = 0
    for a, b in zip(seq, seq[1:]):
        if a is None or b is None or b <= a:
            inv += 1
    return inv


def _decile_table(cohort, groups=DECILES):
    """cohort: list of dicts with 'pct' and 'car'. Returns (rows, means) where
    rows is one dict per decile (decile, n, mean_car, lo, hi pct bounds) and
    means is the decile mean_car sequence in decile order."""
    pcts = [r["pct"] for r in cohort]
    labels = assign_deciles(pcts, groups)
    buckets = {g: [] for g in range(1, groups + 1)}
    for r, g in zip(cohort, labels):
        buckets[g].append(r)
    rows, means = [], []
    for g in range(1, groups + 1):
        b = buckets[g]
        mean_car = sum(x["car"] for x in b) / len(b) if b else None
        rows.append({
            "decile": g,
            "n": len(b),
            "mean_car": mean_car,
            "lo": min((x["pct"] for x in b), default=None),
            "hi": max((x["pct"] for x in b), default=None),
        })
        means.append(mean_car)
    return rows, means


def label_sign_audit(rows):
    """rows: list of dicts with 'action', 'pct' (computable, not None), 'prior'.
    For each action, count rows whose numeric pct-change sign contradicts the
    label (Lowers with pct>0, Raises with pct<0, Maintains with pct!=0), split
    into near_zero_prior (prior < NEAR_ZERO_PRIOR, ratio-inflation suspect) vs
    genuine (prior >= NEAR_ZERO_PRIOR). Returns {action: {...}}."""
    out = {a: {"contradictions": 0, "near_zero_prior": 0, "genuine": 0} for a in PT_ACTIONS}
    for r in rows:
        a, p = r["action"], r["pct"]
        if a not in out or p is None:
            continue
        contradicts = (
            (a == "Lowers" and p > 0) or
            (a == "Raises" and p < 0) or
            (a == "Maintains" and p != 0)
        )
        if contradicts:
            out[a]["contradictions"] += 1
            if r["prior"] is not None and r["prior"] < NEAR_ZERO_PRIOR:
                out[a]["near_zero_prior"] += 1
            else:
                out[a]["genuine"] += 1
    return out


def build_cohort(rows, car_lookup):
    """rows: list of dicts (ticker, event_date, action, current, prior).
    car_lookup: {(ticker, event_date): (status, car)}.

    Returns (cohort, dropped_prior, nonok). The cohort is OK events with a
    computable pct-change, each carrying pct, car, action, prior. An OK event
    with prior<=0 is dropped_prior; a non-OK event is nonok (no CAR to stratify).
    """
    cohort, dropped_prior, nonok = [], 0, 0
    for r in rows:
        status, car = car_lookup.get((r["ticker"], r["event_date"]), (None, None))
        if status != OK:
            nonok += 1
            continue
        pct = pct_change(r["current"], r["prior"])
        if pct is None:
            dropped_prior += 1
            continue
        cohort.append({
            "ticker": r["ticker"], "event_date": r["event_date"],
            "action": r["action"], "pct": pct, "car": car, "prior": r["prior"],
        })
    return cohort, dropped_prior, nonok


# ── Orchestrator ──────────────────────────────────

def run_strata(db_path: str, window: int = None, min_constituents: int = None,
               groups: int = DECILES) -> dict:
    """Build the substrate once, resolve every matured PT event's CAR through the
    headline study's compute_event_car, then cut the OK cohort into deciles of
    signed pct-change (headline) and into a zero-bucket + non-zero deciles
    (robustness). Read-only."""
    from signals.event_study import CAR_WINDOW, MIN_CONSTITUENTS
    window = CAR_WINDOW if window is None else window
    min_constituents = MIN_CONSTITUENTS if min_constituents is None else min_constituents

    sub = prepare_substrate(db_path, window, min_constituents)

    conn = sqlite3.connect(db_path)
    try:
        raw = conn.execute(
            """
            SELECT ticker, event_date, price_target_action,
                   current_price_target, prior_price_target
            FROM analyst_changes
            WHERE price_target_action IN ({})
            """.format(",".join("?" * len(PT_ACTIONS))),
            PT_ACTIONS,
        ).fetchall()
    finally:
        conn.close()

    # Resolve CARs through the headline contract; future events never priced.
    car_lookup, future_dropped = {}, 0
    rows = []
    for ticker, event_date, action, current, prior in raw:
        if event_date > sub.substrate_max:
            future_dropped += 1
            continue
        key = (ticker, event_date)
        if key not in car_lookup:
            car_lookup[key] = compute_event_car(
                ticker, event_date, sub.sectors, sub.grid, sub.step_ret,
                sub.benchmark, sub.reliable, sub.substrate_max, window)
        rows.append({"ticker": ticker, "event_date": event_date, "action": action,
                     "current": current, "prior": prior})

    cohort, dropped_prior, nonok = build_cohort(rows, car_lookup)

    # Headline pooled deciles.
    head_rows, head_means = _decile_table(cohort, groups)

    # Zero-bucket robustness variant.
    zero = [r for r in cohort if r["pct"] == 0.0]
    nonzero = [r for r in cohort if r["pct"] != 0.0]
    nz_rows, nz_means = _decile_table(nonzero, groups)
    zero_mean = sum(r["car"] for r in zero) / len(zero) if zero else None

    head_mono = _strictly_increasing(head_means)
    nz_mono = _strictly_increasing(nz_means)

    audit = label_sign_audit(cohort)

    return {
        "window": window, "min_constituents": min_constituents, "groups": groups,
        "cohort_n": len(cohort), "dropped_prior": dropped_prior,
        "nonok_excluded": nonok, "future_dropped": future_dropped,
        "headline": {"deciles": head_rows, "means": head_means,
                     "monotone": head_mono, "inversions": _inversions(head_means)},
        "zero_variant": {"zero_bucket": {"n": len(zero), "mean_car": zero_mean},
                         "deciles": nz_rows, "means": nz_means,
                         "monotone": nz_mono, "inversions": _inversions(nz_means)},
        "agreement": head_mono == nz_mono,
        "label_sign": audit,
    }


# ── Reporting ─────────────────────────────────────

def _fmt_decile_rows(rows):
    out = []
    for r in rows:
        mc = "n/a" if r["mean_car"] is None else f"{r['mean_car']:+.4f}"
        lo = "n/a" if r["lo"] is None else f"{r['lo']:+.2f}"
        hi = "n/a" if r["hi"] is None else f"{r['hi']:+.2f}"
        out.append(f"  D{r['decile']:<2} {r['n']:>6}  {mc:>10}   [{lo:>8} , {hi:>8}]")
    return out


def format_strata_report(res: dict) -> str:
    lines = []
    lines.append("=== Analyst-PT CAR decile stratification ===")
    lines.append(
        f"cohort N={res['cohort_n']} (window={res['window']}, "
        f"min_constituents={res['min_constituents']}) | dropped prior<=0: "
        f"{res['dropped_prior']} | non-OK excluded: {res['nonok_excluded']} | "
        f"future dropped: {res['future_dropped']}"
    )

    lines.append("")
    lines.append("HEADLINE  pooled NTILE(10) over signed PT pct-change")
    lines.append(f"  {'dec':<3} {'N':>6}  {'mean_CAR%':>10}   pct-change bounds")
    lines.extend(_fmt_decile_rows(res["headline"]["deciles"]))
    h = res["headline"]
    lines.append(f"  monotone increasing D1->D{res['groups']}: "
                 f"{'YES' if h['monotone'] else 'NO'}  ({h['inversions']} adjacent inversions)")

    lines.append("")
    z = res["zero_variant"]
    zb = z["zero_bucket"]
    zmc = "n/a" if zb["mean_car"] is None else f"{zb['mean_car']:+.4f}"
    lines.append("ZERO-BUCKET ROBUSTNESS  zero-revision rows held out, deciles over non-zero")
    lines.append(f"  zero bucket: N={zb['n']}  mean_CAR%={zmc}  (neutral midpoint reference)")
    lines.append(f"  {'dec':<3} {'N':>6}  {'mean_CAR%':>10}   pct-change bounds")
    lines.extend(_fmt_decile_rows(z["deciles"]))
    lines.append(f"  monotone increasing D1->D{res['groups']}: "
                 f"{'YES' if z['monotone'] else 'NO'}  ({z['inversions']} adjacent inversions)")

    lines.append("")
    agree = res["agreement"]
    lines.append(
        f"MONOTONICITY AGREEMENT: the two cuts {'AGREE' if agree else 'DISAGREE'} "
        f"(headline={'YES' if h['monotone'] else 'NO'}, "
        f"zero-variant={'YES' if z['monotone'] else 'NO'})."
    )
    if not agree:
        lines.append("  -> headline is SOFT: the zero-mass split changes the verdict.")

    lines.append("")
    lines.append("LABEL-VS-SIGN AUDIT  (rows whose action label contradicts pct sign)")
    lines.append(f"  {'action':<10} {'contradict':>11} {'near0_prior':>12} {'genuine':>8}")
    for a in PT_ACTIONS:
        x = res["label_sign"][a]
        lines.append(f"  {a:<10} {x['contradictions']:>11} "
                     f"{x['near_zero_prior']:>12} {x['genuine']:>8}")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    from config.constants import DATABASE_PATH
    print(format_strata_report(run_strata(DATABASE_PATH)))
