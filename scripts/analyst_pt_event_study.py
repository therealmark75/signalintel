#!/usr/bin/env python3
"""
analyst_pt_event_study.py — interim validation for analyst_mom v0.16.0.

Tests the directional thesis baked into the v0.16.0 analyst_mom weighting
(Raises → forward outperformance, Lowers → underperformance) via cumulative
abnormal return vs SPDR sector ETF benchmarks.

This is MEASUREMENT, not engineering. The script does not touch scorer.py,
the composite, the scheduler, or any web route. It reads analyst_changes
and screener_snapshots read-only, fetches external prices from yfinance,
computes CARs, and writes a CSV + stdout summary.

Banked in PROJECT_CONTEXT.md (commit a56afaa, 25 May 2026) as the interim
validation method for the OOS gate. See that block for the acceptance bar
and the substrate rationale.

Design (locked Phase 1):
  • Events: analyst_changes 2019-01-01..2025-12-31, PT actions
    Raises/Maintains/Lowers only.
  • De-clustering: drop events where another event for the same ticker
    sits within ±21 calendar days.
  • Anchor: event_date + 1 trading day (T+1).
  • Daily abnormal return: r_ticker[d] - r_sector_etf[d].
  • CAR per event: arithmetic sum across each window; geometric CAR
    carried as a robustness column.
  • Windows: [T+1,T+5], [T+1,T+21] (headline), [T+1,T+63].
  • Acceptance: monotonicity of mean CAR across R/M/L + positive
    Raises-Lowers spread separable from zero. NO magnitude floor
    (upstream survivorship deflates Lowers, spread is a lower bound).
  • Placebo: same computation on random non-event dates per ticker,
    excluding ±21d of real events. Distinguishes signal from artefact.

Usage:
  python scripts/analyst_pt_event_study.py
  python scripts/analyst_pt_event_study.py --rebuild-cache  # force re-fetch
"""
from __future__ import annotations

import argparse
import logging
import os
import random
import sqlite3
import sys
import time
import warnings
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import yfinance as yf
from scipy import stats

PROJECT_ROOT = Path("/Users/markn/signalintel")
DB_PATH      = PROJECT_ROOT / "data" / "trading_system.db"
CACHE_PATH   = PROJECT_ROOT / "data" / "analyst_pt_event_study_prices.parquet"
OUT_CSV      = PROJECT_ROOT / "data" / "analyst_pt_event_study_events.csv"

WINDOW_START_DATE = "2019-01-01"
WINDOW_END_DATE   = "2025-12-31"
DE_CLUSTER_DAYS   = 21         # calendar days
WINDOWS = {"5d": 5, "21d": 21, "63d": 63}
RANDOM_SEED = 1742

# FinViz sector string → SPDR ETF
SECTOR_TO_ETF = {
    "Basic Materials":       "XLB",
    "Communication Services": "XLC",
    "Consumer Cyclical":     "XLY",
    "Consumer Defensive":    "XLP",
    "Energy":                "XLE",
    "Financial":             "XLF",
    "Healthcare":            "XLV",
    "Industrials":           "XLI",
    "Real Estate":           "XLRE",
    "Technology":            "XLK",
    "Utilities":             "XLU",
}
COHORTS = ("Raises", "Maintains", "Lowers")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("event_study")


# ───────────────────────────────────────────────────────── data assembly ─

def load_events_and_sectors() -> pd.DataFrame:
    """Pull R/M/L events in window, attach latest-known sector per ticker."""
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    events = pd.read_sql_query(
        """
        SELECT ticker, event_date, firm, price_target_action,
               current_price_target, prior_price_target
        FROM analyst_changes
        WHERE event_date BETWEEN ? AND ?
          AND price_target_action IN ('Raises','Maintains','Lowers')
        """,
        con, params=(WINDOW_START_DATE, WINDOW_END_DATE),
    )
    # Latest-known sector per ticker from screener_snapshots
    sectors = pd.read_sql_query(
        """
        WITH latest AS (
          SELECT ticker, MAX(scraped_at) AS m FROM screener_snapshots GROUP BY ticker
        )
        SELECT s.ticker, s.sector, s.market_cap
        FROM screener_snapshots s
        JOIN latest l ON l.ticker = s.ticker AND l.m = s.scraped_at
        """,
        con,
    )
    con.close()
    df = events.merge(sectors, on="ticker", how="left")
    df["etf"] = df["sector"].map(SECTOR_TO_ETF)
    pre = len(df)
    df = df.dropna(subset=["etf"])
    log.info(f"  events loaded: {pre}  | with sector→ETF mapping: {len(df)}")
    df["event_date"] = pd.to_datetime(df["event_date"])
    return df


def de_cluster(events: pd.DataFrame) -> pd.DataFrame:
    """Drop events where another event for the same ticker sits within
    ±21 calendar days. Vectorised per-ticker."""
    keep_mask = []
    grouped = events.sort_values(["ticker", "event_date"]).groupby("ticker", sort=False)
    for _, g in grouped:
        dates = g["event_date"].to_numpy()
        ok = np.ones(len(dates), dtype=bool)
        for i in range(len(dates)):
            for j in range(len(dates)):
                if i == j:
                    continue
                if abs((dates[j] - dates[i]).astype("timedelta64[D]").astype(int)) <= DE_CLUSTER_DAYS:
                    ok[i] = False
                    break
        keep_mask.append(pd.Series(ok, index=g.index))
    mask = pd.concat(keep_mask).sort_index()
    out = events.loc[mask].copy()
    log.info(f"  de-clustering: {len(events)} → {len(out)} events survive ±{DE_CLUSTER_DAYS}d")
    return out


def build_placebo(real_events: pd.DataFrame) -> pd.DataFrame:
    """For each real event, draw a random trading-day placebo date for the
    same ticker, in the same 2019-2025 window, at least ±21 calendar days
    from any real event for that ticker."""
    rng = random.Random(RANDOM_SEED)
    win_start = pd.Timestamp(WINDOW_START_DATE)
    win_end   = pd.Timestamp(WINDOW_END_DATE)
    total_days = (win_end - win_start).days

    ticker_events = defaultdict(list)
    for _, row in real_events.iterrows():
        ticker_events[row["ticker"]].append(row["event_date"])

    placebos = []
    for _, row in real_events.iterrows():
        tk = row["ticker"]
        real_dates = ticker_events[tk]
        # try up to 30 random draws to find a clean placebo date
        chosen = None
        for _ in range(30):
            offset = rng.randint(0, total_days)
            cand = win_start + pd.Timedelta(days=offset)
            # skip weekends (still allow; we'll snap to next trading day later)
            if cand.weekday() >= 5:
                continue
            # ±21d from any real event for this ticker?
            if any(abs((cand - rd).days) <= DE_CLUSTER_DAYS for rd in real_dates):
                continue
            chosen = cand
            break
        if chosen is None:
            continue
        placebos.append({
            "ticker":               tk,
            "event_date":           chosen,
            "firm":                 "_PLACEBO_",
            "price_target_action":  row["price_target_action"],
            "current_price_target": None,
            "prior_price_target":   None,
            "sector":               row["sector"],
            "market_cap":           row["market_cap"],
            "etf":                  row["etf"],
        })
    df = pd.DataFrame(placebos)
    log.info(f"  placebo events drawn: {len(df)} (target {len(real_events)})")
    return df


# ─────────────────────────────────────────────────────── price cache ─

def build_or_load_price_cache(tickers: list[str], rebuild: bool = False) -> pd.DataFrame:
    """Fetch daily auto-adjusted close for every ticker in `tickers`, cache
    to a single parquet. Returns long-form DataFrame: [ticker, date, close]."""
    if CACHE_PATH.exists() and not rebuild:
        t0 = time.time()
        cached = pd.read_parquet(CACHE_PATH)
        log.info(f"  cache HIT: {CACHE_PATH.name}  rows={len(cached):,}  "
                 f"tickers={cached['ticker'].nunique()}  load={time.time()-t0:.2f}s")
        missing = sorted(set(tickers) - set(cached["ticker"].unique()))
        if not missing:
            return cached
        log.info(f"  cache MISS on {len(missing)} tickers — fetching incrementally")
        new_chunk = _fetch_yf_chunk(missing)
        out = pd.concat([cached, new_chunk], ignore_index=True)
        out.to_parquet(CACHE_PATH, index=False)
        return out

    log.info(f"  cache MISS: fetching {len(tickers)} tickers from yfinance")
    df = _fetch_yf_chunk(tickers)
    df.to_parquet(CACHE_PATH, index=False)
    log.info(f"  cache WRITE: {CACHE_PATH} ({len(df):,} rows)")
    return df


def _fetch_one_with_retry(tk: str, attempts: int = 3) -> "pd.DataFrame | None":
    """Single yfinance fetch with backoff on rate-limit errors."""
    for attempt in range(attempts):
        try:
            h = yf.Ticker(tk).history(
                start=WINDOW_START_DATE, end="2026-05-26", auto_adjust=True
            )
            if h is None or len(h) == 0:
                return None
            return pd.DataFrame({
                "ticker": tk,
                "date":   h.index.tz_localize(None).normalize(),
                "close":  h["Close"].astype(float).values,
            })
        except Exception as e:
            msg = str(e)
            if ("Too Many" in msg or "rate" in msg.lower() or "429" in msg) and attempt < attempts - 1:
                wait = 5 * (2 ** attempt)  # 5s, 10s, 20s
                log.warning(f"    {tk}: rate-limited, sleeping {wait}s before retry {attempt+2}/{attempts}")
                time.sleep(wait)
                continue
            if attempt == attempts - 1:
                raise
    return None


def _fetch_yf_chunk(tickers: list[str]) -> pd.DataFrame:
    """Sequential yfinance pull. Returns long-form: [ticker, date, close].

    Priority order: SPDR sector ETFs FIRST (must-have for CAR), then event
    tickers alphabetically. Small inter-call sleep + retry-with-backoff
    on rate-limit errors. Re-run uses incremental cache to only fetch
    missing tickers, so a partial failure auto-resumes on the next run.
    """
    etfs = [t for t in tickers if t in set(SECTOR_TO_ETF.values())]
    others = sorted([t for t in tickers if t not in set(SECTOR_TO_ETF.values())])
    ordered = etfs + others

    rows = []
    t0 = time.time()
    fail = empty = 0
    for i, tk in enumerate(ordered, 1):
        try:
            sub = _fetch_one_with_retry(tk)
            if sub is None:
                empty += 1
            else:
                rows.append(sub)
        except Exception as e:
            fail += 1
            if fail <= 5:
                log.warning(f"    fetch err {tk}: {str(e)[:80]}")
        time.sleep(0.05)  # gentle pacing to stay below yfinance throttle ceiling
        if i % 500 == 0 or i == len(ordered):
            log.info(f"    [{i}/{len(ordered)}] elapsed={time.time()-t0:.0f}s "
                     f"empty={empty} fail={fail}")
    df = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=["ticker","date","close"])
    log.info(f"  yfinance pull DONE: {len(df):,} rows, {fail} errors, {empty} empty "
             f"in {time.time()-t0:.0f}s")
    return df


# ─────────────────────────────────────────────────────── CAR engine ─

def compute_car_for_events(events: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    """For each event, compute CAR over each window vs sector ETF.

    Returns events DF with added columns:
      car_arith_5d, car_arith_21d, car_arith_63d,
      car_geom_5d,  car_geom_21d,  car_geom_63d.
    Drops events with insufficient forward price coverage (T+1 to T+window).
    """
    # Pivot prices to wide: index=date, columns=ticker, value=close
    pivot = prices.pivot_table(index="date", columns="ticker", values="close", aggfunc="last")
    pivot = pivot.sort_index()
    daily_ret = pivot.pct_change()

    out_rows = []
    skipped_no_t1 = 0
    skipped_short_window = 0
    for _, ev in events.iterrows():
        tk  = ev["ticker"]
        etf = ev["etf"]
        ed  = pd.Timestamp(ev["event_date"]).normalize()

        if tk not in daily_ret.columns or etf not in daily_ret.columns:
            skipped_no_t1 += 1
            continue

        future_idx = daily_ret.index[daily_ret.index > ed]
        if len(future_idx) < 1:
            skipped_no_t1 += 1
            continue

        t1 = future_idx[0]
        t1_pos = daily_ret.index.get_loc(t1)

        result = dict(ev)
        for label, n in WINDOWS.items():
            end_pos = t1_pos + n - 1
            if end_pos >= len(daily_ret.index):
                result[f"car_arith_{label}"] = np.nan
                result[f"car_geom_{label}"]  = np.nan
                continue
            window_slice = slice(t1_pos, end_pos + 1)
            r_tk  = daily_ret[tk].iloc[window_slice].to_numpy()
            r_etf = daily_ret[etf].iloc[window_slice].to_numpy()
            mask = ~(np.isnan(r_tk) | np.isnan(r_etf))
            if mask.sum() < n * 0.7:  # require ≥70% non-NaN coverage
                result[f"car_arith_{label}"] = np.nan
                result[f"car_geom_{label}"]  = np.nan
                continue
            abnormal = r_tk[mask] - r_etf[mask]
            result[f"car_arith_{label}"] = float(abnormal.sum())
            # Geometric: prod(1+ar) - 1
            result[f"car_geom_{label}"]  = float(np.prod(1 + abnormal) - 1)
        out_rows.append(result)

    log.info(f"  CAR computed for {len(out_rows)} events "
             f"(skipped: no T+1 price = {skipped_no_t1})")
    return pd.DataFrame(out_rows)


# ─────────────────────────────────────────────────────── reporting ─

def cohort_summary(df: pd.DataFrame, label: str) -> None:
    print(f"\n  ─── {label} ───")
    print(f"  {'cohort':<10} {'n':>7} | "
          f"{'mean_5d':>9}  {'med_5d':>9} | "
          f"{'mean_21d':>9}  {'med_21d':>9} | "
          f"{'mean_63d':>9}  {'med_63d':>9}")
    for coh in COHORTS:
        sub = df[df["price_target_action"] == coh].dropna(subset=["car_arith_21d"])
        if len(sub) == 0:
            continue
        m5  = sub["car_arith_5d"].mean()
        md5 = sub["car_arith_5d"].median()
        m21 = sub["car_arith_21d"].mean()
        md21= sub["car_arith_21d"].median()
        m63 = sub["car_arith_63d"].mean()
        md63= sub["car_arith_63d"].median()
        print(f"  {coh:<10} {len(sub):>7,} | "
              f"{m5*100:>+8.3f}%  {md5*100:>+8.3f}% | "
              f"{m21*100:>+8.3f}%  {md21*100:>+8.3f}% | "
              f"{m63*100:>+8.3f}%  {md63*100:>+8.3f}%")


def spread_test(df: pd.DataFrame, label: str) -> dict:
    print(f"\n  ─── {label}: Raises − Lowers spread (Welch t-test, two-sided) ───")
    results = {}
    for win in WINDOWS.keys():
        raises = df[df["price_target_action"]=="Raises"][f"car_arith_{win}"].dropna()
        lowers = df[df["price_target_action"]=="Lowers"][f"car_arith_{win}"].dropna()
        if len(raises) < 30 or len(lowers) < 30:
            print(f"  {win:<5}  insufficient n (raises={len(raises)}, lowers={len(lowers)})")
            continue
        t, p = stats.ttest_ind(raises, lowers, equal_var=False)
        spread = raises.mean() - lowers.mean()
        results[win] = {"spread": spread, "t": float(t), "p": float(p),
                        "n_R": len(raises), "n_L": len(lowers)}
        print(f"  {win:<5}  spread={spread*100:>+8.3f}%   "
              f"t={t:>+7.2f}   p={p:.3e}   "
              f"n_R={len(raises):,}  n_L={len(lowers):,}")
    return results


def monotonicity_check(df: pd.DataFrame, label: str, win: str = "21d") -> bool:
    mean_R = df[df["price_target_action"]=="Raises"][f"car_arith_{win}"].mean()
    mean_M = df[df["price_target_action"]=="Maintains"][f"car_arith_{win}"].mean()
    mean_L = df[df["price_target_action"]=="Lowers"][f"car_arith_{win}"].mean()
    mono = mean_R > mean_M > mean_L
    print(f"\n  monotonicity at {win} ({label}): "
          f"R({mean_R*100:+.3f}%) > M({mean_M*100:+.3f}%) > L({mean_L*100:+.3f}%) "
          f"→ {'PASS' if mono else 'FAIL'}")
    return mono


def robustness_slices(df: pd.DataFrame) -> None:
    print(f"\n  ─── Robustness slices on Raises−Lowers spread, 21d ───")

    # By year
    df["year"] = df["event_date"].dt.year
    by_year = df.groupby("year").apply(
        lambda g: (g[g["price_target_action"]=="Raises"]["car_arith_21d"].mean()
                   - g[g["price_target_action"]=="Lowers"]["car_arith_21d"].mean()) * 100
    )
    print(f"\n  by year:")
    for y, s in by_year.items():
        n_r = len(df[(df["year"]==y) & (df["price_target_action"]=="Raises")])
        n_l = len(df[(df["year"]==y) & (df["price_target_action"]=="Lowers")])
        print(f"    {y}  spread={s:+7.3f}%   n_R={n_r:,}  n_L={n_l:,}")

    # By sector
    by_sector = df.groupby("sector").apply(
        lambda g: (g[g["price_target_action"]=="Raises"]["car_arith_21d"].mean()
                   - g[g["price_target_action"]=="Lowers"]["car_arith_21d"].mean()) * 100
    )
    print(f"\n  by sector:")
    for s, v in by_sector.sort_values(ascending=False).items():
        n_r = len(df[(df["sector"]==s) & (df["price_target_action"]=="Raises")])
        n_l = len(df[(df["sector"]==s) & (df["price_target_action"]=="Lowers")])
        print(f"    {s:<22} spread={v:+7.3f}%  n_R={n_r:,}  n_L={n_l:,}")

    # By market cap bucket (FinViz string: "$1.2B", "$500M", etc.)
    def _mc_bucket(s):
        if not isinstance(s, str): return "unknown"
        s = s.strip()
        if "B" in s:
            try: v = float(s.replace("$","").replace("B",""))
            except: return "unknown"
            if v >= 200: return "mega"
            if v >= 10:  return "large"
            return "mid"
        if "M" in s:
            try: v = float(s.replace("$","").replace("M",""))
            except: return "unknown"
            if v >= 2000: return "mid"
            if v >= 300:  return "small"
            return "micro"
        return "unknown"
    df["mc_bucket"] = df["market_cap"].map(_mc_bucket)
    bucket_order = ["mega","large","mid","small","micro","unknown"]
    print(f"\n  by market-cap bucket:")
    for b in bucket_order:
        sub = df[df["mc_bucket"]==b]
        if len(sub) == 0: continue
        n_r = len(sub[sub["price_target_action"]=="Raises"])
        n_l = len(sub[sub["price_target_action"]=="Lowers"])
        if n_r == 0 or n_l == 0: continue
        sp = (sub[sub["price_target_action"]=="Raises"]["car_arith_21d"].mean()
              - sub[sub["price_target_action"]=="Lowers"]["car_arith_21d"].mean()) * 100
        print(f"    {b:<8} spread={sp:+7.3f}%  n_R={n_r:,}  n_L={n_l:,}")

    # By top-10 most-active firms (real only — placebo has firm='_PLACEBO_')
    real = df[df["firm"] != "_PLACEBO_"]
    top10 = real["firm"].value_counts().head(10).index.tolist()
    print(f"\n  by top-10 firms:")
    for f in top10:
        sub = real[real["firm"] == f]
        n_r = len(sub[sub["price_target_action"]=="Raises"])
        n_l = len(sub[sub["price_target_action"]=="Lowers"])
        if n_r == 0 or n_l == 0: continue
        sp = (sub[sub["price_target_action"]=="Raises"]["car_arith_21d"].mean()
              - sub[sub["price_target_action"]=="Lowers"]["car_arith_21d"].mean()) * 100
        print(f"    {f:<28} spread={sp:+7.3f}%  n_R={n_r:,}  n_L={n_l:,}")


def survivorship_disclosure() -> None:
    print("\n  ─── SURVIVORSHIP DISCLOSURE ───")
    print("  Event population built from yfinance get_upgrades_downgrades(), which")
    print("  excludes ticker pages for delistings. Failed companies that received")
    print("  Lowers ratings before delisting are systematically absent — the")
    print("  Lowers cohort's mean CAR is biased upward (less negative than reality).")
    print("  Net effect on Raises−Lowers spread: spread is biased toward UNDER-")
    print("  estimation. A measured positive spread is a LOWER BOUND on the true")
    print("  effect. Sign and ordering survive the bias; magnitude does not.")
    print("  Magnitudes reported here are DESCRIPTIVE, never a pass condition.")


def verdict(real_results: dict, real_mono: bool, placebo_results: dict, placebo_mono: bool) -> None:
    print("\n" + "=" * 78)
    print("VERDICT")
    print("=" * 78)

    real_21 = real_results.get("21d", {})
    plac_21 = placebo_results.get("21d", {})

    if not real_21 or not plac_21:
        print("  INCONCLUSIVE: missing 21d test results.")
        return

    real_sig = real_21["p"] < 0.05
    real_pos = real_21["spread"] > 0
    plac_sig = plac_21["p"] < 0.05
    plac_spread_abs = abs(plac_21["spread"])
    real_dominates_placebo = abs(real_21["spread"]) > 3 * plac_spread_abs

    print(f"  Real    21d: spread {real_21['spread']*100:+.3f}%  "
          f"t={real_21['t']:+.2f}  p={real_21['p']:.2e}  "
          f"mono={'PASS' if real_mono else 'FAIL'}")
    print(f"  Placebo 21d: spread {plac_21['spread']*100:+.3f}%  "
          f"t={plac_21['t']:+.2f}  p={plac_21['p']:.2e}  "
          f"mono={'PASS' if placebo_mono else 'FAIL'}")
    print()
    if not (real_pos and real_sig and real_mono):
        print("  → FAIL: real cohort does not satisfy sign + monotonicity + separability.")
        print("    The w=0.25 analyst PT weight is NOT forward-justified by this test.")
        return
    if plac_sig and plac_spread_abs > 0.5 * abs(real_21["spread"]):
        print("  → INCONCLUSIVE: placebo cohort shows a comparable spread; the real")
        print("    spread cannot be cleanly attributed to analyst events. Likely a")
        print("    method artefact (sector matching, calendar drift, etc.).")
        return
    if real_dominates_placebo:
        print("  → PASS: real spread is positive, monotonic, separable from zero,")
        print("    and at least 3× the placebo spread — the analyst events drive a")
        print("    real signal distinct from the null. Magnitude is a LOWER BOUND")
        print("    per the survivorship disclosure.")
    else:
        print("  → PASS (weak): real spread satisfies acceptance bar but is not 3×")
        print("    the placebo spread. Signal is present but the placebo contrast")
        print("    is softer than ideal — interpret magnitude cautiously.")


# ──────────────────────────────────────────────────────────────────── main ─

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--rebuild-cache", action="store_true",
                   help="Force re-fetch all yfinance history")
    args = p.parse_args()

    t_main = time.time()

    log.info("loading events + sector mapping...")
    events_raw = load_events_and_sectors()

    log.info("de-clustering events...")
    events = de_cluster(events_raw)

    by_cohort = events["price_target_action"].value_counts()
    log.info(f"  de-clustered counts: {dict(by_cohort)}")

    # Tickers needed: event tickers + 11 sector ETFs
    needed = sorted(set(events["ticker"].unique()) | set(SECTOR_TO_ETF.values()))
    log.info(f"  total tickers needed for price pull: {len(needed)}")

    prices = build_or_load_price_cache(needed, rebuild=args.rebuild_cache)

    log.info("building placebo events...")
    placebos = build_placebo(events)

    log.info("computing CAR (real cohort)...")
    real_cars = compute_car_for_events(events, prices)
    log.info("computing CAR (placebo cohort)...")
    plac_cars = compute_car_for_events(placebos, prices)

    real_cars.to_csv(OUT_CSV, index=False)
    log.info(f"  per-event CSV written: {OUT_CSV} ({len(real_cars):,} rows)")

    # ─── stdout summary ───
    print("\n" + "=" * 78)
    print("ANALYST PRICE-TARGET EVENT STUDY — RESULTS")
    print(f"window: {WINDOW_START_DATE} → {WINDOW_END_DATE} | "
          f"de-cluster: ±{DE_CLUSTER_DAYS} cal days | anchor: T+1")
    print("=" * 78)

    cohort_summary(real_cars, "REAL events")
    cohort_summary(plac_cars, "PLACEBO events")

    real_results = spread_test(real_cars, "REAL")
    plac_results = spread_test(plac_cars, "PLACEBO")

    real_mono = monotonicity_check(real_cars, "REAL", "21d")
    plac_mono = monotonicity_check(plac_cars, "PLACEBO", "21d")

    robustness_slices(real_cars)
    survivorship_disclosure()
    verdict(real_results, real_mono, plac_results, plac_mono)

    print(f"\n  total runtime: {time.time()-t_main:.1f}s")


if __name__ == "__main__":
    main()
