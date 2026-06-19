"""
Reader-guard test for the dashboard Market State panel (Panel 4 in web/app.py).

The panel query reads the latest close per index symbol. The fix adds
`AND close IS NOT NULL` so a forming/partial 'today' row with a NULL close is
skipped and the tile shows the last real close instead of going blank.

This test pins the QUERY SEMANTICS against a seeded temp SQLite (no Flask app,
no network, no live DB). PANEL_QUERY below mirrors the literal query in
web/app.py Panel 4; if that query changes, this test must change with it.
"""
import sqlite3
import pytest

# Mirror of the Panel 4 per-symbol query in web/app.py (Market State tiles).
PANEL_QUERY = (
    "SELECT close FROM market_history "
    "WHERE symbol = ? AND close IS NOT NULL "
    "ORDER BY date DESC LIMIT 2"
)


def _seed(tmp_path, rows):
    """rows = list of (symbol, date, close). Returns a temp DB path."""
    db_path = str(tmp_path / "panel.db")
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE market_history (symbol TEXT, date TEXT, close REAL, "
        "PRIMARY KEY (symbol, date))"
    )
    conn.executemany(
        "INSERT INTO market_history (symbol, date, close) VALUES (?,?,?)", rows
    )
    conn.commit()
    conn.close()
    return db_path


def _tile(db_path, sym):
    """Replicate app.py Panel 4 latest/prev/chg_pct computation for one symbol."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(PANEL_QUERY, (sym,)).fetchall()
    conn.close()
    latest = rows[0]["close"] if rows else None
    prev = rows[1]["close"] if len(rows) > 1 else None
    chg_pct = ((latest - prev) / prev * 100.0) if (latest and prev) else None
    return latest, prev, chg_pct


def test_null_latest_row_falls_back_to_last_real_close(tmp_path):
    """
    Catches: the dashboard-blanking bug, a NULL-close 'today' row (latest by
    date) making the tile render None. With the guard, the tile shows
    yesterday's real close.
    Ignores: template rendering and freshness windows; this asserts only the
    query's null-skip and latest-by-date selection.
    """
    db = _seed(tmp_path, [
        ("^GSPC", "2026-06-17", 7420.10),   # yesterday, real
        ("^GSPC", "2026-06-18", None),       # today, forming bar -> NULL close
    ])
    latest, prev, chg_pct = _tile(db, "^GSPC")
    assert latest == 7420.10, "latest should skip the NULL today-row, not return None"
    assert prev is None       # only one non-null row exists, so no prev
    assert chg_pct is None


def test_all_non_null_returns_true_latest_and_change(tmp_path):
    """
    Catches: regression where the guard drops a valid latest row. With all real
    closes, the tile returns the true latest and computes change vs the prior
    real close.
    Ignores: rounding/formatting of the percentage (asserted approximately).
    """
    db = _seed(tmp_path, [
        ("^IXIC", "2026-06-16", 25500.0),
        ("^IXIC", "2026-06-17", 26021.66),
    ])
    latest, prev, chg_pct = _tile(db, "^IXIC")
    assert latest == 26021.66
    assert prev == 25500.0
    assert chg_pct == pytest.approx((26021.66 - 25500.0) / 25500.0 * 100.0)
