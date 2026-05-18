"""Altman Z-Score distribution analysis across the production ticker universe.

Read-only script. Computes Z-scores for every ticker with complete Altman
inputs (6 from financial_statements + market_cap from screener_snapshots),
bins them into the four penalty zones, and writes per-bin summary stats to
stdout plus a per-ticker CSV side-output for further analysis.

Purpose: empirical evidence for the Phase 2c calibration decision. Altman's
1968 manufacturing thresholds may suppress composites systematically across
the tech-heavy SignalIntel universe. The distribution shape determines
whether to recalibrate.

Usage: python scripts/altman_distribution_analysis.py
Output: stdout summary + data/altman_distribution_<YYYY-MM-DD>.csv
"""

import csv
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.constants import DATABASE_PATH, SCORING_ENGINE_VERSION
from signals.scorer import compute_z_raw, compute_z_double_prime_raw, _parse_market_cap_text
from signals.line_item_keys import ALTMAN_LOOKUPS
from database.db import get_financials_enrichment_map, get_latest_screener


BINS = [
    ("Z < 0.0",         lambda z: z < 0.0,                "negative"),
    ("0.0 <= Z < 1.8",  lambda z: 0.0 <= z < 1.8,         "distress"),
    ("1.8 <= Z < 3.0",  lambda z: 1.8 <= z < 3.0,         "grey"),
    ("Z >= 3.0",        lambda z: z >= 3.0,               "safe"),
]

BIN_MIDPOINTS = {
    "negative": None,
    "distress": 0.9,
    "grey":     2.4,
    "safe":     None,
}

# Altman Z'' (1995 non-manufacturing) — three bins, not four
ZPP_BINS = [
    ("Z'' < 1.1",        lambda z: z < 1.1,         "distress"),
    ("1.1 <= Z'' < 2.6", lambda z: 1.1 <= z < 2.6,  "grey"),
    ("Z'' >= 2.6",       lambda z: z >= 2.6,        "safe"),
]


def _classify_zpp_bin(z: float) -> str:
    for _, predicate, label in ZPP_BINS:
        if predicate(z):
            return label
    return "unknown"


def _latest_composite_map(db_path: str) -> dict:
    """{ticker: composite_score} for the most recent scored_at per ticker."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT s.ticker, s.composite_score
        FROM signal_scores s
        JOIN (
            SELECT ticker, MAX(scored_at) AS ts
            FROM signal_scores
            GROUP BY ticker
        ) latest
          ON latest.ticker = s.ticker AND latest.ts = s.scored_at
    """)
    out = {r["ticker"]: r["composite_score"] for r in cur.fetchall()}
    conn.close()
    return out


def _resolve_latest_fy(stmt_map: dict) -> "str | None":
    """Max fiscal_year across all statement_types for one ticker.

    stmt_map shape: {stmt_type: {fiscal_year: {line_item_key: value}}}
    """
    years: set = set()
    for years_map in stmt_map.values():
        years.update(years_map.keys())
    return max(years) if years else None


def _get_input(stmt_map: dict, fy: str, canonical_key: str):
    stmt_type, raw_key = ALTMAN_LOOKUPS[canonical_key]
    return stmt_map.get(stmt_type, {}).get(fy, {}).get(raw_key)


def _classify_bin(z: float) -> str:
    for _, predicate, label in BINS:
        if predicate(z):
            return label
    return "unknown"


def _select_exemplars(rows: list[dict], bin_label: str, n: int = 5) -> list[dict]:
    """Top-N selection rule per bin:
      negative bin → most-negative Z
      safe bin     → most-positive Z
      middle bins  → closest to midpoint
    """
    midpoint = BIN_MIDPOINTS[bin_label]
    if bin_label == "negative":
        return sorted(rows, key=lambda r: r["z_score"])[:n]
    if bin_label == "safe":
        return sorted(rows, key=lambda r: r["z_score"], reverse=True)[:n]
    return sorted(rows, key=lambda r: abs(r["z_score"] - midpoint))[:n]


def main():
    run_ts = datetime.utcnow().isoformat() + "Z"
    today  = datetime.utcnow().strftime("%Y-%m-%d")

    print("Altman Z distribution analysis")
    print(f"SCORING_ENGINE_VERSION: {SCORING_ENGINE_VERSION}")
    print(f"DB: {DATABASE_PATH}")
    print(f"Run timestamp: {run_ts}")
    print()

    financials_map      = get_financials_enrichment_map(DATABASE_PATH)
    screener_rows       = get_latest_screener(DATABASE_PATH)
    market_cap_text_by_ticker = {r["ticker"]: r.get("market_cap") for r in screener_rows}
    sector_by_ticker          = {r["ticker"]: r.get("sector") for r in screener_rows}
    composite_by_ticker       = _latest_composite_map(DATABASE_PATH)

    total_fin_tickers = len(financials_map)

    # Per-input missingness counters (over tickers that *have* a latest fy)
    missing_counts = Counter()
    no_latest_fy   = 0
    missing_marketcap = 0
    missing_financials_only = 0
    complete_rows = []

    for ticker, stmt_map in financials_map.items():
        fy = _resolve_latest_fy(stmt_map)
        if fy is None:
            no_latest_fy += 1
            continue

        wc   = _get_input(stmt_map, fy, "working_capital")
        ta   = _get_input(stmt_map, fy, "total_assets")
        re_  = _get_input(stmt_map, fy, "retained_earnings")
        eb   = _get_input(stmt_map, fy, "ebit")
        tl   = _get_input(stmt_map, fy, "total_liabilities")
        rev  = _get_input(stmt_map, fy, "total_revenue")

        present = {
            "WorkingCapital":                       wc  is not None,
            "TotalAssets":                          ta  is not None,
            "RetainedEarnings":                     re_ is not None,
            "EBIT":                                 eb  is not None,
            "TotalLiabilitiesNetMinorityInterest":  tl  is not None,
            "TotalRevenue":                         rev is not None,
        }
        for key, ok in present.items():
            if not ok:
                missing_counts[key] += 1

        all_six_present = all(present.values())
        mc_text = market_cap_text_by_ticker.get(ticker)
        mc_num  = _parse_market_cap_text(mc_text)

        if not all_six_present and mc_num is None:
            missing_financials_only += 1  # both missing — count under financials bucket
            continue
        if not all_six_present:
            missing_financials_only += 1
            continue
        if mc_num is None:
            missing_marketcap += 1
            continue

        z = compute_z_raw(
            working_capital   = wc,
            total_assets      = ta,
            retained_earnings = re_,
            ebit              = eb,
            total_liabilities = tl,
            total_revenue     = rev,
            market_cap        = mc_num,
        )
        if z is None:
            # Division-by-zero guard inside compute_z_raw — treat as financials problem
            missing_financials_only += 1
            continue

        z_pp = compute_z_double_prime_raw(
            working_capital   = wc,
            total_assets      = ta,
            retained_earnings = re_,
            ebit              = eb,
            total_liabilities = tl,
            market_cap        = mc_num,
        )

        complete_rows.append({
            "ticker":              ticker,
            "sector":              sector_by_ticker.get(ticker),
            "fiscal_year":         fy,
            "working_capital":     wc,
            "total_assets":        ta,
            "retained_earnings":   re_,
            "ebit":                eb,
            "total_liabilities":   tl,
            "total_revenue":       rev,
            "market_cap_text":     mc_text,
            "market_cap_numeric":  mc_num,
            "z_score":             z,
            "bin":                 _classify_bin(z),
            "composite_score":     composite_by_ticker.get(ticker),
            "z_double_prime":      z_pp,
            "bin_z_double_prime":  _classify_zpp_bin(z_pp) if z_pp is not None else None,
        })

    complete_n = len(complete_rows)
    excluded_fin = missing_financials_only + no_latest_fy
    excluded_mc  = missing_marketcap

    # ── Stdout summary ───────────────────────────────────────────────────────
    print("─── POPULATION ─────────────────────────────────────────────────────")
    print(f"Tickers in financial_statements:              {total_fin_tickers}")
    print(f"Tickers with complete Altman inputs + mcap:   {complete_n}")
    print(f"Excluded (missing financial inputs):          {excluded_fin}")
    print(f"Excluded (missing market_cap):                {excluded_mc}")
    print()
    print(f"Excluded: {excluded_fin} tickers missing financial inputs "
          f"(top reasons: {', '.join(f'{k}={v}' for k, v in missing_counts.most_common(3))}), "
          f"{excluded_mc} tickers missing market_cap.")
    print()

    # Per-input missing breakdown
    print("─── PER-INPUT MISSING (over latest-fy tickers) ────────────────────")
    for key in ["WorkingCapital", "TotalAssets", "RetainedEarnings",
                "EBIT", "TotalLiabilitiesNetMinorityInterest", "TotalRevenue"]:
        print(f"  {key:40s} missing: {missing_counts[key]}")
    print()

    # Bin counts
    by_bin = defaultdict(list)
    for r in complete_rows:
        by_bin[r["bin"]].append(r)

    print("─── BIN DISTRIBUTION ───────────────────────────────────────────────")
    print(f"{'Bin':20s} {'Label':12s} {'Count':>8s} {'Pct':>8s}")
    for bin_name, _, label in BINS:
        n = len(by_bin[label])
        pct = (n / complete_n * 100.0) if complete_n else 0.0
        print(f"{bin_name:20s} {label:12s} {n:8d} {pct:7.2f}%")
    print()

    # Sector breakdown per bin (top 6)
    print("─── TOP SECTORS PER BIN ────────────────────────────────────────────")
    for bin_name, _, label in BINS:
        rows = by_bin[label]
        if not rows:
            print(f"  {bin_name} ({label}): (empty)")
            continue
        sector_counts = Counter(r["sector"] or "(unknown)" for r in rows)
        top = sector_counts.most_common(6)
        print(f"  {bin_name} ({label}): n={len(rows)}")
        for sec, n in top:
            pct = n / len(rows) * 100.0
            print(f"    {sec:30s} {n:5d}  {pct:5.1f}%")
    print()

    # Per-bin top-5 exemplars
    print("─── TOP-5 EXEMPLARS PER BIN ────────────────────────────────────────")
    for bin_name, _, label in BINS:
        rows = by_bin[label]
        if not rows:
            print(f"  {bin_name} ({label}): (empty)")
            continue
        rule = ("most-negative" if label == "negative"
                else "most-positive" if label == "safe"
                else f"closest to midpoint {BIN_MIDPOINTS[label]}")
        print(f"  {bin_name} ({label}) — selection: {rule}")
        ex = _select_exemplars(rows, label, n=5)
        for r in ex:
            comp = r["composite_score"]
            comp_str = f"{comp:6.2f}" if comp is not None else "  n/a "
            print(f"    {r['ticker']:8s}  Z={r['z_score']:8.3f}  composite={comp_str}  "
                  f"sector={r['sector'] or '(unknown)'}")
    print()

    # ── Altman Z'' (1995 non-manufacturing) ─────────────────────────────────
    zpp_by_bin = defaultdict(list)
    for r in complete_rows:
        if r["z_double_prime"] is not None:
            zpp_by_bin[r["bin_z_double_prime"]].append(r)
    zpp_total = sum(len(v) for v in zpp_by_bin.values())

    print("=== ALTMAN Z'' (1995) DISTRIBUTION ===")
    print()
    for bin_name, _, label in ZPP_BINS:
        n = len(zpp_by_bin[label])
        pct = (n / zpp_total * 100.0) if zpp_total else 0.0
        suffix = {"distress": "[distress]", "grey": "[grey zone]", "safe": "[safe]"}[label]
        print(f"  {bin_name:18s} : {n:5d} tickers ({pct:5.2f}%)   {suffix}")
    print()
    print(f"Total computable: {zpp_total} (same as classic Z, same input set)")
    print()

    # Sector breakdown for Z'' distress bin (mirroring classic-Z negative-bin)
    print("─── Z'' DISTRESS BIN — TOP SECTORS ────────────────────────────────")
    distress_rows = zpp_by_bin["distress"]
    if distress_rows:
        sector_counts = Counter(r["sector"] or "(unknown)" for r in distress_rows)
        for sec, n in sector_counts.most_common(6):
            pct = n / len(distress_rows) * 100.0
            print(f"  {sec:30s} {n:5d}  {pct:5.1f}%")
    else:
        print("  (empty)")
    print()

    # ── Side-by-side comparison ──────────────────────────────────────────────
    print("=== SIDE-BY-SIDE COMPARISON ===")
    print()
    classic_neg      = len(by_bin["negative"])
    classic_distress = len(by_bin["distress"])
    classic_grey     = len(by_bin["grey"])
    classic_safe     = len(by_bin["safe"])
    classic_penalised = classic_neg + classic_distress  # Z < 1.8 (the -10/-30/-60 region in 2c)
    zpp_distress = len(zpp_by_bin["distress"])
    zpp_grey     = len(zpp_by_bin["grey"])
    zpp_safe     = len(zpp_by_bin["safe"])

    def _pct(n: int) -> float:
        return (n / complete_n * 100.0) if complete_n else 0.0

    print(f"Classic Z penalised:  {classic_penalised:5d} tickers ({_pct(classic_penalised):5.2f}%)  [Z < 1.8]")
    print(f"Altman Z'' distress:  {zpp_distress:5d} tickers ({_pct(zpp_distress):5.2f}%)  [Z'' < 1.1]")
    delta = zpp_distress - classic_penalised
    delta_pp = _pct(zpp_distress) - _pct(classic_penalised)
    sign = "+" if delta >= 0 else ""
    print(f"Delta:                {sign}{delta:5d} tickers ({sign}{delta_pp:5.2f} pct points)")
    print()

    zpp_label = "Altman Z''"
    def _fmt(n: int) -> str:
        return f"{n} ({_pct(n):.1f}%)"

    row_label_z0   = "  Z<0 (no Z'' equiv)"
    row_label_dist = "  Z[0,1.8) / Z'' < 1.1"

    print(f"{'Tier':32s} {'Classic Z':>16s} {zpp_label:>16s}")
    print("-" * 66)
    print(f"{'distress (most-penalised)':32s} {_fmt(classic_neg+classic_distress):>16s} {_fmt(zpp_distress):>16s}")
    print(f"{row_label_z0:32s} {_fmt(classic_neg):>16s} {'—':>16s}")
    print(f"{row_label_dist:32s} {_fmt(classic_distress):>16s} {_fmt(zpp_distress):>16s}")
    print(f"{'grey':32s} {_fmt(classic_grey):>16s} {_fmt(zpp_grey):>16s}")
    print(f"{'safe':32s} {_fmt(classic_safe):>16s} {_fmt(zpp_safe):>16s}")
    print()

    # ── CSV side-output ──────────────────────────────────────────────────────
    csv_path = Path(DATABASE_PATH).parent / f"altman_distribution_{today}.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "ticker", "sector", "fiscal_year",
        "working_capital", "total_assets", "retained_earnings",
        "ebit", "total_liabilities", "total_revenue",
        "market_cap_text", "market_cap_numeric",
        "z_score", "bin", "composite_score",
        "z_double_prime", "bin_z_double_prime",
    ]
    sorted_rows = sorted(complete_rows, key=lambda r: r["z_score"])
    with csv_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(sorted_rows)

    print(f"CSV written: {csv_path}  ({len(sorted_rows)} rows)")


if __name__ == "__main__":
    main()
