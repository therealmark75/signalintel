"""
Unit tests for the yfinance price-target writer path (Phase 2, v0.18.1).

Covers fetch_price_target (yahoo_scraper) pulling targetMeanPrice +
numberOfAnalystOpinions out of Ticker.info, and upsert_price_target
(fmp_scraper) persisting only positive targets into fmp_price_targets
with a fresh last_updated. No network: Ticker.info is stubbed.
"""
import sqlite3

import pytest

from scrapers.yahoo_scraper import fetch_price_target
from scrapers.fmp_scraper import upsert_price_target, get_price_targets_map


class _FakeTicker:
    """Stand-in for yf.Ticker exposing a static .info dict (no network)."""

    def __init__(self, info):
        self._info = info

    @property
    def info(self):
        return self._info


def test_fetch_price_target_extracts_target_and_count():
    """
    Catches: fetch_price_target failing to pull targetMeanPrice /
    numberOfAnalystOpinions out of Ticker.info, or mis-pairing the two.
    Ignores: live yfinance behaviour and the rate-limit circuit breaker (a
    static dict never trips _safe_fetch's 429 branch); those belong to the
    live job, not this unit.
    """
    t = _FakeTicker({"targetMeanPrice": 312.71, "numberOfAnalystOpinions": 43})
    assert fetch_price_target(t, "AAPL") == (312.71, 43)


def test_fetch_price_target_absent_returns_none_pair():
    """
    Catches: fetch_price_target emitting a partial or non-positive tuple for a
    no-coverage ticker (empty info, missing key, zero or negative target),
    which would let null/garbage targets reach the writer.
    Ignores: the count value when the target is absent (the contract is the
    (None, None) sentinel regardless of any stray analyst count).
    """
    assert fetch_price_target(_FakeTicker({}), "NOCOV") == (None, None)
    assert fetch_price_target(_FakeTicker({"targetMeanPrice": 0}), "ZERO") == (None, None)
    assert fetch_price_target(
        _FakeTicker({"targetMeanPrice": -5, "numberOfAnalystOpinions": 2}), "NEG"
    ) == (None, None)


def test_upsert_price_target_writes_positive_row_with_fresh_timestamp(tmp_path):
    """
    Catches: the writer not persisting a positive target, dropping the
    analyst_count, or stamping a stale/missing last_updated (which the
    reader's 7-day window would then silently exclude).
    Ignores: the exact last_updated string format; freshness is asserted via
    the same datetime('now') basis the reader uses, not by parsing the text.
    """
    db = str(tmp_path / "t.db")
    assert upsert_price_target(db, "AAPL", 312.71, 43) == 1

    conn = sqlite3.connect(db)
    row = conn.execute(
        "SELECT price_target, analyst_count FROM fmp_price_targets WHERE ticker='AAPL'"
    ).fetchone()
    fresh = conn.execute(
        "SELECT COUNT(*) FROM fmp_price_targets "
        "WHERE ticker='AAPL' AND last_updated >= datetime('now','-120 seconds')"
    ).fetchone()[0]
    conn.close()

    assert row is not None
    assert abs(row[0] - 312.71) < 1e-6
    assert row[1] == 43
    assert fresh == 1
    # Reader returns it, proving the row clears the 7-day freshness window.
    assert get_price_targets_map(db).get("AAPL") == pytest.approx(312.71)


def test_upsert_price_target_skips_none_target(tmp_path):
    """
    Catches: the writer inserting a row for a None (no-coverage) target, which
    would pollute the cache with null price_target values and distort the
    target-price coverage metric.
    Ignores: positive-target writes (covered above); this isolates the skip
    path so a regression there cannot hide behind a passing happy path.
    """
    db = str(tmp_path / "t.db")
    assert upsert_price_target(db, "NOCOV", None, None) == 0
    # get_price_targets_map bootstraps the table, so this also proves no row landed.
    assert "NOCOV" not in get_price_targets_map(db)
