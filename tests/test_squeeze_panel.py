"""
Dashboard short-squeeze setups tile — confluence detector tests.

Covers _get_squeeze_candidates(db_path) from web/app.py. The tile is
DISPLAY-ONLY (it does NOT feed the composite score); these tests prove
the filter logic, not any scoring math.

Catches:
- Confluence regression (rating filter wrong → wrong-tier tickers leak in).
- Threshold drift on the qualifying floor (10) or the elevated band (20).
- Implausibility guard regression (SI > 100 leaking back in).
- Staleness suppression breaking (stale rows surfacing in the tile).
- elevated_flag boolean miscut.
- Empty population mishandling.

Ignores:
- Render-layer concerns (Jinja markup, CSS classes, tier_short() mapping —
  those live in test_signal_labels.py and the browser walk).
- ORDER BY tie-break behaviour beyond DESC on short_interest_pct.
- The ~49.5% FinViz NULL coverage (accepted by design per Phase 1).
"""
import sqlite3
import pytest

from web.app import _get_squeeze_candidates


@pytest.fixture()
def tmp_db(tmp_path):
    """Isolated SQLite with minimal schema: screener_snapshots + signal_scores."""
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE screener_snapshots (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            scraped_at          TEXT    NOT NULL,
            ticker              TEXT    NOT NULL,
            short_interest_pct  REAL
        );
        CREATE TABLE signal_scores (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            scored_at       TEXT    NOT NULL,
            ticker          TEXT    NOT NULL,
            rating          TEXT,
            composite_score REAL
        );
    """)
    conn.commit()
    conn.close()
    return db_path


def _seed_pair(db_path, ticker, *, rating, composite, si_pct, ss_age_days=0):
    """Seed one signal_scores row at today and one screener_snapshots row
    `ss_age_days` ago for `ticker`. Helper to keep test rows obvious."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO signal_scores (scored_at, ticker, rating, composite_score) "
        "VALUES (datetime('now'), ?, ?, ?)",
        (ticker, rating, composite),
    )
    conn.execute(
        "INSERT INTO screener_snapshots (scraped_at, ticker, short_interest_pct) "
        "VALUES (datetime('now', ?), ?, ?)",
        (f"-{ss_age_days} days", ticker, si_pct),
    )
    conn.commit()
    conn.close()


def test_strong_buy_with_si_floor_appears(tmp_db):
    """STRONG_BUY (Very Strong) + SI >= 10 lands on the tile.

    Catches: STRONG_BUY missing from the rating filter (a half-built
             confluence that only fires on BUY would silently exclude
             the top-tier match).
    Ignores: BUY-tier behaviour (covered separately).
    """
    _seed_pair(tmp_db, "VS1", rating="STRONG_BUY", composite=80.0, si_pct=15.0)
    out = _get_squeeze_candidates(tmp_db)
    assert len(out) == 1
    assert out[0]["ticker"] == "VS1"
    assert out[0]["rating"] == "STRONG_BUY"
    assert out[0]["elevated_flag"] is False  # 15 is below the 20 band


def test_buy_with_si_floor_appears(tmp_db):
    """BUY (Strong) + SI >= 10 lands on the tile.

    Catches: BUY missing from the rating filter (would mean the tile
             only ever fires when STRONG_BUY is non-empty, which today
             is population 1).
    Ignores: STRONG_BUY case (covered separately).
    """
    _seed_pair(tmp_db, "S1", rating="BUY", composite=68.0, si_pct=12.5)
    out = _get_squeeze_candidates(tmp_db)
    assert len(out) == 1
    assert out[0]["ticker"] == "S1"
    assert out[0]["rating"] == "BUY"


def test_hold_excluded_even_with_high_si(tmp_db):
    """HOLD tier with SI >= 10 is NOT on the tile — confluence requires
    Very Strong or Strong.

    Catches: rating filter overly permissive (e.g. dropping the IN clause
             entirely would surface every heavily-shorted ticker
             regardless of conviction — the whole point of the tile is
             the confluence).
    Ignores: WEAK_HOLD / SELL / STRONG_SELL cases — same exclusion path.
    """
    _seed_pair(tmp_db, "H1", rating="HOLD", composite=50.0, si_pct=42.0)
    assert _get_squeeze_candidates(tmp_db) == []


def test_buy_below_floor_excluded(tmp_db):
    """BUY-rated ticker with SI < 10 is NOT on the tile — floor not cleared.

    Catches: floor threshold drift down (e.g. accidentally lowered to 5),
             which would flood the tile with mildly-shorted top-tier names.
    Ignores: SI = exactly 10 boundary case (covered by inclusion at
             threshold via the `>= 10` comparator).
    """
    _seed_pair(tmp_db, "B1", rating="BUY", composite=66.0, si_pct=8.9)
    assert _get_squeeze_candidates(tmp_db) == []


def test_implausible_si_excluded(tmp_db):
    """SI > 100 (float < shares-short artefact) excluded by guard.

    Catches: guard regression — without it, the tile's worst case is a
             data artefact ranking #1 (Phase 1 probe saw max 379.28%).
    Ignores: SI between 10 and 100 (covered by other tests).
    """
    _seed_pair(tmp_db, "X1", rating="BUY", composite=70.0, si_pct=120.0)
    assert _get_squeeze_candidates(tmp_db) == []


def test_stale_row_suppressed(tmp_db):
    """Screener row older than 14 days suppresses the ticker (display-only,
    not a neutral score — the ticker simply doesn't appear).

    Catches: staleness rule missing or inverted; would surface a squeeze
             setup off month-old SI data if the scraper broke.
    Ignores: rows within the 14-day trust window (covered elsewhere).
    """
    _seed_pair(tmp_db, "STALE", rating="BUY", composite=65.0, si_pct=22.0, ss_age_days=15)
    assert _get_squeeze_candidates(tmp_db) == []


def test_elevated_flag_at_boundary_and_below(tmp_db):
    """elevated_flag is true at SI >= 20 and false between 10 and 20.

    Catches: boundary error on the elevated band (e.g. > 20 instead of
             >= 20, dropping every ticker exactly at the line; or wrongly
             rounding 19.99 up).
    Ignores: visual rendering of the chip (template concern).
    """
    _seed_pair(tmp_db, "LOW",  rating="BUY", composite=66.0, si_pct=12.0)
    _seed_pair(tmp_db, "EDGE", rating="BUY", composite=66.0, si_pct=20.0)
    _seed_pair(tmp_db, "HIGH", rating="BUY", composite=66.0, si_pct=45.0)
    out = {r["ticker"]: r["elevated_flag"] for r in _get_squeeze_candidates(tmp_db)}
    assert out == {"LOW": False, "EDGE": True, "HIGH": True}


def test_empty_population_returns_empty_list(tmp_db):
    """Empty DB → empty list (the template renders the empty-state line).

    Catches: helper raising on an empty result set; or returning None
             which the template would coerce to a no-iter branch and
             miss the empty-state copy.
    Ignores: the actual empty-state string (template concern).
    """
    assert _get_squeeze_candidates(tmp_db) == []


def test_top_10_row_cap(tmp_db):
    """Tile caps at top 10 by short_interest_pct DESC.

    Catches: missing LIMIT (full result set hits the panel); or wrong
             ORDER BY direction (would put the least-shorted at the top).
    Ignores: tie-break behaviour at exactly equal SI values.
    """
    for i in range(15):
        # SI values 11..25 — all above floor; expect the 10 highest (16..25)
        _seed_pair(tmp_db, f"T{i:02d}", rating="BUY", composite=60.0 + i, si_pct=11.0 + i)
    out = _get_squeeze_candidates(tmp_db)
    assert len(out) == 10
    # Highest first
    sis = [r["short_interest_pct"] for r in out]
    assert sis == sorted(sis, reverse=True)
    assert sis[0] == pytest.approx(25.0)
    assert sis[-1] == pytest.approx(16.0)
