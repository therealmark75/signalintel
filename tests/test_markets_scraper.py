"""
Writer-guard tests for scrapers/markets_scraper.scrape_markets.

These verify the NULL-close skip guard: a forming/partial daily bar (Close is
NaN, which _safe_float turns into None) must NOT be persisted as a NULL-close
row in market_history, because the dashboard Market State panel reads the latest
row by date and a NULL close blanks the tile.

No network: yfinance is monkeypatched with a fake Ticker that returns
hand-built DataFrames, so scrape_markets never reaches the real feed.
"""
import sqlite3
import pandas as pd

from scrapers import markets_scraper


def _frame(rows):
    """rows = list of (date_str, open, high, low, close, volume) -> DataFrame
    shaped like yfinance .history() output (DatetimeIndex + OHLCV columns)."""
    idx = pd.to_datetime([r[0] for r in rows])
    return pd.DataFrame(
        {
            "Open":   [r[1] for r in rows],
            "High":   [r[2] for r in rows],
            "Low":    [r[3] for r in rows],
            "Close":  [r[4] for r in rows],
            "Volume": [r[5] for r in rows],
        },
        index=idx,
    )


def _install_fake_yf(monkeypatch, frames):
    """Point markets_scraper at a fake yfinance returning `frames[symbol]`,
    restrict ALL_SYMBOLS to the seeded symbols, and silence the sleep."""
    class _FakeTicker:
        def __init__(self, symbol):
            self._symbol = symbol
        def history(self, period=None, interval=None):
            return frames[self._symbol]

    class _FakeYF:
        @staticmethod
        def Ticker(symbol):
            return _FakeTicker(symbol)

    import types
    monkeypatch.setattr(markets_scraper, "yf", _FakeYF)
    monkeypatch.setattr(markets_scraper, "ALL_SYMBOLS", list(frames.keys()))
    monkeypatch.setattr(markets_scraper, "time", types.SimpleNamespace(sleep=lambda *a, **k: None))


def test_nan_close_row_is_not_persisted(tmp_path, monkeypatch):
    """
    Catches: a forming bar whose Close is NaN being written as a NULL-close row
    (the dashboard-blanking bug). The symbol with a NaN-close 'today' row must
    keep its real prior row and must NOT gain a NULL-close row.
    Ignores: the real feed (yfinance is faked), and other OHLC fields being None
    (only a None close gates the skip; open/high/low/volume may still be None).
    """
    frames = {
        "GOOD":     _frame([("2026-06-16", 98.0, 99.0, 97.0, 99.0, 1000.0),
                            ("2026-06-17", 99.0, 101.0, 98.0, 100.0, 1100.0)]),
        "BADCLOSE": _frame([("2026-06-16", 49.0, 51.0, 48.0, 50.0, 500.0),
                            ("2026-06-17", 50.0, 52.0, 49.0, float("nan"), 0.0)]),
    }
    _install_fake_yf(monkeypatch, frames)

    db_path = str(tmp_path / "mkt.db")
    markets_scraper.scrape_markets(db_path)

    conn = sqlite3.connect(db_path)
    # Zero NULL-close rows anywhere.
    null_rows = conn.execute(
        "SELECT COUNT(*) FROM market_history WHERE close IS NULL"
    ).fetchone()[0]
    assert null_rows == 0, "a NULL-close row was persisted despite the skip guard"

    # GOOD keeps both real rows.
    good = conn.execute(
        "SELECT date, close FROM market_history WHERE symbol='GOOD' ORDER BY date"
    ).fetchall()
    assert good == [("2026-06-16", 99.0), ("2026-06-17", 100.0)]

    # BADCLOSE keeps only its non-NaN row; the NaN-close 2026-06-17 row is absent.
    bad = conn.execute(
        "SELECT date, close FROM market_history WHERE symbol='BADCLOSE' ORDER BY date"
    ).fetchall()
    conn.close()
    assert bad == [("2026-06-16", 50.0)], f"NaN-close row leaked: {bad}"


def test_all_real_closes_all_persisted(tmp_path, monkeypatch):
    """
    Catches: an over-eager guard that drops valid rows. A symbol whose closes are
    all real numbers must have every row written.
    Ignores: the real feed (faked); price-value correctness beyond persistence.
    """
    frames = {
        "REAL": _frame([("2026-06-16", 10.0, 11.0, 9.0, 10.5, 5.0),
                        ("2026-06-17", 10.5, 12.0, 10.0, 11.5, 6.0)]),
    }
    _install_fake_yf(monkeypatch, frames)

    db_path = str(tmp_path / "mkt.db")
    markets_scraper.scrape_markets(db_path)

    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT date, close FROM market_history WHERE symbol='REAL' ORDER BY date"
    ).fetchall()
    conn.close()
    assert rows == [("2026-06-16", 10.5), ("2026-06-17", 11.5)]
