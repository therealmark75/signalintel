# signals/backtester.py
# ─────────────────────────────────────────────────
# Signal backtester (persisted-price rewire).
#
# Validates historical signal ratings against subsequent price action to
# check whether the ratings have directional predictive value.
#
# PRICE BASIS (read before trusting any number this produces):
#   Forward prices come from the persisted screener_snapshots.price series,
#   NOT from a live market feed. That column is an intraday FinViz SPOT price
#   captured at scrape time. It is NOT dividend or split adjusted, and there
#   may be several snapshots on one calendar day. This basis is acceptable for
#   N=1 and N=5 trading-day DIRECTIONAL validation (does the rating lean the
#   right way over a few days), and must NOT be trusted beyond short horizons:
#   over longer windows the lack of corporate-action adjustment and the
#   spot-vs-close mismatch dominate the signal. N=20 is intentionally NOT
#   supported here.
#
# SEGMENTATION:
#   A backtest run is scoped to ONE scoring_version cohort. Composite scores
#   are never pooled across engine versions, because the scoring methodology
#   (and therefore the meaning of a given composite value) changes between
#   versions. Every read, summary, and persisted row carries scoring_version.
#
# Produces win rate, avg return, and a rough Sharpe-like ratio per
# (scoring_version, rating, hold_days) cohort.
from __future__ import annotations
# ─────────────────────────────────────────────────

import logging
import sqlite3
from collections import namedtuple
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# yfinance is intentionally NOT used by the backtest path anymore. The guard
# is kept only so the module imports cleanly in environments that still expect
# the symbol present; no backtest code path calls into yf.
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    logger.warning("yfinance not available (unused by the backtest path).")


# Corporate-action straddle guard thresholds (tunable, no scoring impact).
# Same-day: a date whose intraday MAX/MIN price ratio exceeds this is a split
# boundary or garbage print; a trade whose entry or exit lands on it is SKIPPED.
SAME_DAY_STRADDLE_RATIO = 2.0
# Cross-day: a surviving trade (no same-day straddle on either side, a date the
# same-day detector cannot flag) whose entry vs exit ratio exceeds this is an
# unadjusted overnight corporate action. Phase 2b: SKIPPED (was log-only); every
# skip is logged for audit. Symmetric bound (collapse < 1/ratio, or jump > ratio).
CROSS_DAY_JUMP_RATIO = 3.0


# ── Data classes ──────────────────────────────────

@dataclass
class TradeResult:
    ticker:         str
    signal_date:    str
    signal_rating:  str
    composite_score:float
    entry_price:    float
    hold_days:      int
    exit_price:     float = None
    return_pct:     float = None
    win:            bool  = None
    error:          str   = None


@dataclass
class BacktestSummary:
    rating:         str
    hold_days:      int
    total_trades:   int
    winning_trades: int
    losing_trades:  int
    win_rate:       float
    avg_return:     float
    median_return:  float
    best_trade:     float
    worst_trade:    float
    avg_win:        float
    avg_loss:       float
    profit_factor:  float   # avg_win / abs(avg_loss)
    sharpe_approx:  float   # avg_return / std_return


# ── Persisted-price lookups (screener_snapshots) ──

def is_straddle_date(conn: sqlite3.Connection, ticker: str, date: str,
                     threshold: float = SAME_DAY_STRADDLE_RATIO) -> bool:
    """True if (ticker, date) shows an intraday MAX(price)/MIN(price) ratio above
    threshold, the signature of a same-day corporate-action split boundary (e.g.
    KLAC 2026-06-12 carrying both ~241 and ~2411) or a garbage data print. Either
    fabricates a return if a trade's entry or exit lands on the date, so both are
    skipped. Rows with NULL or non-positive price are ignored; a date with no
    priced snapshot returns False (nothing to detect)."""
    row = conn.execute(
        """
        SELECT MIN(price) AS mn, MAX(price) AS mx
        FROM screener_snapshots
        WHERE ticker = ? AND DATE(scraped_at) = ?
          AND price IS NOT NULL AND price > 0
        """,
        (ticker, date),
    ).fetchone()
    if not row or row[0] is None or row[0] <= 0:
        return False
    return (row[1] / row[0]) > threshold


def fetch_entry_price(conn: sqlite3.Connection, ticker: str, signal_date: str) -> float | None:
    """
    Entry price for (ticker, signal_date): the latest priced screener snapshot
    ON that calendar day. If several snapshots exist that day we take the one
    with MAX(scraped_at) (latest spot of the day). Returns None if the ticker
    has no priced snapshot on signal_date (unpriceable entry).
    """
    if is_straddle_date(conn, ticker, signal_date):
        logger.warning(
            "Straddle skip (entry): %s %s intraday ratio > %.1f",
            ticker, signal_date, SAME_DAY_STRADDLE_RATIO,
        )
        return None
    row = conn.execute(
        """
        SELECT price
        FROM screener_snapshots
        WHERE ticker = ?
          AND DATE(scraped_at) = ?
          AND price IS NOT NULL
        ORDER BY scraped_at DESC
        LIMIT 1
        """,
        (ticker, signal_date),
    ).fetchone()
    return row[0] if row else None


def fetch_exit_price(conn: sqlite3.Connection, ticker: str, signal_date: str, hold_days: int) -> float | None:
    """
    Exit price at horizon N (= hold_days) TRADING days forward. We enumerate
    the distinct priced snapshot dates strictly after signal_date for this
    ticker, in ascending order, and step to the Nth one. This steps OVER gap
    and weekend dates (absent dates are simply not in the list), so the horizon
    is measured in real subsequent observations, never calendar signal_date+N.
    On that Nth forward date we take the MAX(scraped_at) price. Returns None if
    fewer than N forward priced dates exist (no exit yet).
    """
    forward_dates = conn.execute(
        """
        SELECT DISTINCT DATE(scraped_at) AS d
        FROM screener_snapshots
        WHERE ticker = ?
          AND DATE(scraped_at) > ?
          AND price IS NOT NULL
        ORDER BY d ASC
        LIMIT ?
        """,
        (ticker, signal_date, hold_days),
    ).fetchall()

    if len(forward_dates) < hold_days:
        return None

    nth_date = forward_dates[hold_days - 1][0]
    if is_straddle_date(conn, ticker, nth_date):
        logger.warning(
            "Straddle skip (exit): %s %s N=%d intraday ratio > %.1f",
            ticker, nth_date, hold_days, SAME_DAY_STRADDLE_RATIO,
        )
        return None
    row = conn.execute(
        """
        SELECT price
        FROM screener_snapshots
        WHERE ticker = ?
          AND DATE(scraped_at) = ?
          AND price IS NOT NULL
        ORDER BY scraped_at DESC
        LIMIT 1
        """,
        (ticker, nth_date),
    ).fetchone()
    return row[0] if row else None


ForwardResult = namedtuple("ForwardResult", "ok entry_price exit_price return_pct error")


def guarded_forward_return(conn, ticker, signal_date, hold_days):
    """The single guarded forward-return contract. Prices a trade's entry and
    exit through the same-day-straddle-guarded fetch path, then applies the
    cross-day overnight-split guard, so EVERY consumer (the backtest loop, the
    validation harness) inherits both guards from one place. No consumer
    reimplements the cross-day logic.

    Returns a ForwardResult. ok=True carries entry_price/exit_price (rounded) and
    a raw return_pct. ok=False is a skip with error set to "No entry price",
    "No exit price at N=...", or a cross-day collapse tag; entry/exit are filled
    where known so callers can still record them.

    Cross-day rule: a trade that priced through fetch_* has no same-day straddle
    on either date (else the fetch returned None), so an entry-vs-exit ratio
    breaching CROSS_DAY_JUMP_RATIO here is an unadjusted overnight corporate
    action the same-day detector cannot see. Logged on every skip for audit.
    """
    entry_price = fetch_entry_price(conn, ticker, signal_date)
    if not entry_price:
        return ForwardResult(False, None, None, None, "No entry price")
    exit_price = fetch_exit_price(conn, ticker, signal_date, hold_days)
    if not exit_price:
        return ForwardResult(False, round(entry_price, 2), None, None,
                             f"No exit price at N={hold_days}")
    _xr = exit_price / entry_price if entry_price else 0
    if _xr > CROSS_DAY_JUMP_RATIO or (0 < _xr < 1 / CROSS_DAY_JUMP_RATIO):
        logger.warning(
            "Cross-day skip (overnight split): %s entry %.2f exit %.2f "
            "N=%d ratio %.2f, no same-day straddle on either date",
            ticker, entry_price, exit_price, hold_days, _xr,
        )
        return ForwardResult(False, round(entry_price, 2), round(exit_price, 2), None,
                             f"Cross-day corporate-action collapse (ratio {_xr:.2f})")
    return ForwardResult(True, round(entry_price, 2), round(exit_price, 2),
                         ((exit_price - entry_price) / entry_price) * 100.0, None)


# ── Core backtest functions ───────────────────────

def backtest_signals_from_db(
    db_path:         str,
    scoring_version: str,
    rating:          str = "BUY",
    hold_days:       int = 1,
    min_score:       float = 60.0,
    limit:           int = 100,
) -> list[TradeResult]:
    """
    Backtest one (scoring_version, rating, hold_days) cohort against the
    persisted screener_snapshots price series.

    Args:
        db_path:         Path to SQLite database
        scoring_version: REQUIRED. Cohort to scope to. Scores are never pooled
                         across versions.
        rating:          Signal rating to test (BUY, REVERSION, STRONG_BUY, ...)
        hold_days:       Forward horizon in TRADING days (1 or 5)
        min_score:       Minimum composite score to include
        limit:           Max signals to test

    Returns:
        List of TradeResult objects. Unpriceable / no-exit-yet signals are
        returned with .error set and .return_pct None so compute_summary
        excludes them from the stats.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur  = conn.cursor()

    cur.execute("""
        SELECT DISTINCT ticker, DATE(scored_at) as signal_date,
               rating, composite_score
        FROM signal_scores
        WHERE rating = ?
          AND composite_score >= ?
          AND scoring_version = ?
        GROUP BY ticker, DATE(scored_at)
        ORDER BY scored_at DESC
        LIMIT ?
    """, (rating, min_score, scoring_version, limit))

    signals = [dict(r) for r in cur.fetchall()]

    logger.info(
        f"Backtesting {len(signals)} {rating} signals (v{scoring_version}) "
        f"over {hold_days}-trading-day hold..."
    )

    results = []
    for i, sig in enumerate(signals):
        ticker      = sig["ticker"]
        signal_date = sig["signal_date"]

        # Single guarded contract: same-day straddle guard (in fetch_*) plus the
        # cross-day overnight-split guard, all inside guarded_forward_return so
        # the backtester and the validation harness share one guard path.
        fr = guarded_forward_return(conn, ticker, signal_date, hold_days)
        if not fr.ok:
            results.append(TradeResult(
                ticker=ticker, signal_date=signal_date,
                signal_rating=rating, composite_score=sig["composite_score"],
                entry_price=(fr.entry_price if fr.entry_price is not None else 0),
                hold_days=hold_days, exit_price=fr.exit_price, error=fr.error,
            ))
            continue

        results.append(TradeResult(
            ticker=ticker, signal_date=signal_date,
            signal_rating=rating, composite_score=sig["composite_score"],
            entry_price=fr.entry_price,
            hold_days=hold_days,
            exit_price=fr.exit_price,
            return_pct=round(fr.return_pct, 2),
            win=fr.return_pct > 0,
        ))

    conn.close()
    return results


def compute_summary(results: list[TradeResult], rating: str, hold_days: int) -> BacktestSummary:
    """Compute aggregate statistics from a list of TradeResults."""
    valid = [r for r in results if r.return_pct is not None]

    if not valid:
        return BacktestSummary(
            rating=rating, hold_days=hold_days, total_trades=0,
            winning_trades=0, losing_trades=0, win_rate=0,
            avg_return=0, median_return=0, best_trade=0, worst_trade=0,
            avg_win=0, avg_loss=0, profit_factor=0, sharpe_approx=0,
        )

    returns  = [r.return_pct for r in valid]
    wins     = [r for r in valid if r.win]
    losses   = [r for r in valid if not r.win]

    avg_return = sum(returns) / len(returns)
    sorted_r   = sorted(returns)
    median_r   = sorted_r[len(sorted_r) // 2]

    avg_win  = sum(r.return_pct for r in wins)  / len(wins)  if wins   else 0
    avg_loss = sum(r.return_pct for r in losses) / len(losses) if losses else 0

    profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float("inf")

    # Approximate Sharpe (return / std, annualised roughly)
    if len(returns) > 1:
        import statistics
        std = statistics.stdev(returns)
        sharpe = (avg_return / std) * (252 / hold_days) ** 0.5 if std > 0 else 0
    else:
        sharpe = 0

    return BacktestSummary(
        rating=rating,
        hold_days=hold_days,
        total_trades=len(valid),
        winning_trades=len(wins),
        losing_trades=len(losses),
        win_rate=round(len(wins) / len(valid) * 100, 1),
        avg_return=round(avg_return, 2),
        median_return=round(median_r, 2),
        best_trade=round(max(returns), 2),
        worst_trade=round(min(returns), 2),
        avg_win=round(avg_win, 2),
        avg_loss=round(avg_loss, 2),
        profit_factor=round(profit_factor, 2),
        sharpe_approx=round(sharpe, 2),
    )


def run_full_backtest(
    db_path:         str,
    scoring_version: str,
    ratings:         list[str] = None,
    hold_days:       list[int] = None,
    min_score:       float = 60.0,
    limit:           int = 50,
) -> dict:
    """
    Run backtests across multiple ratings and SHORT holding periods, scoped to
    a single scoring_version.

    Returns nested dict: {rating: {hold_days: {summary, trades}}}
    """
    ratings   = ratings   or ["BUY", "REVERSION", "STRONG_BUY"]
    hold_days = hold_days or [1, 5]

    all_results = {}

    for rating in ratings:
        all_results[rating] = {}
        for days in hold_days:
            logger.info(f"\nBacktesting {rating} | v{scoring_version} | {days}-trading-day hold...")
            results = backtest_signals_from_db(
                db_path=db_path, scoring_version=scoring_version, rating=rating,
                hold_days=days, min_score=min_score, limit=limit,
            )
            summary = compute_summary(results, rating, days)
            all_results[rating][days] = {
                "summary": summary,
                "trades":  results,
            }
            logger.info(
                f"  {rating} {days}d: Win rate {summary.win_rate}% | "
                f"Avg return {summary.avg_return:+.2f}% | "
                f"Profit factor {summary.profit_factor}"
            )

    return all_results


def _ensure_scoring_version_column(conn: sqlite3.Connection, table: str) -> None:
    """Idempotently add a scoring_version TEXT column to an existing table."""
    cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    if "scoring_version" not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN scoring_version TEXT")


def save_backtest_results(db_path: str, results: dict, scoring_version: str) -> None:
    """Persist backtest summaries to the database, stamped with scoring_version."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS backtest_results (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            run_at          TEXT,
            rating          TEXT,
            hold_days       INTEGER,
            total_trades    INTEGER,
            win_rate        REAL,
            avg_return      REAL,
            median_return   REAL,
            best_trade      REAL,
            worst_trade     REAL,
            profit_factor   REAL,
            sharpe_approx   REAL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS backtest_trades (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            run_at          TEXT,
            ticker          TEXT,
            signal_date     TEXT,
            signal_rating   TEXT,
            composite_score REAL,
            entry_price     REAL,
            exit_price      REAL,
            hold_days       INTEGER,
            return_pct      REAL,
            win             INTEGER,
            error           TEXT
        )
    """)
    # Idempotent column add for pre-existing tables (no drop/recreate).
    _ensure_scoring_version_column(conn, "backtest_results")
    _ensure_scoring_version_column(conn, "backtest_trades")

    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    for rating, days_data in results.items():
        for days, data in days_data.items():
            s = data["summary"]
            conn.execute("""
                INSERT INTO backtest_results
                    (run_at, rating, hold_days, total_trades, win_rate,
                     avg_return, median_return, best_trade, worst_trade,
                     profit_factor, sharpe_approx, scoring_version)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, (now, s.rating, s.hold_days, s.total_trades, s.win_rate,
                  s.avg_return, s.median_return, s.best_trade, s.worst_trade,
                  s.profit_factor, s.sharpe_approx, scoring_version))

            for t in data["trades"]:
                if t.return_pct is not None:
                    conn.execute("""
                        INSERT INTO backtest_trades
                            (run_at, ticker, signal_date, signal_rating,
                             composite_score, entry_price, exit_price,
                             hold_days, return_pct, win, error, scoring_version)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                    """, (now, t.ticker, t.signal_date, t.signal_rating,
                          t.composite_score, t.entry_price, t.exit_price,
                          t.hold_days, t.return_pct, int(t.win) if t.win is not None else None,
                          t.error, scoring_version))

    conn.commit()
    conn.close()
    logger.info("Backtest results saved to database.")
