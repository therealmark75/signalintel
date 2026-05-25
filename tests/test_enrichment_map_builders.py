"""
Shape and basic-correctness tests for the 4 Yahoo enrichment map builder helpers.

Each test creates an isolated in-memory SQLite database seeded with minimal rows,
calls the helper, and asserts the returned structure matches the expected shape.

Catches: regression in SQL (wrong column names, wrong JOIN logic, wrong aggregation).
Ignores: data-quality issues (NULL values, zero counts) — those are DB-level constraints
         tested in test_data_integrity.py. Also ignores the live DB state entirely;
         these tests are fully isolated via tmp_path + schema init.
"""
import sqlite3
import pytest
from database.db import (
    get_earnings_enrichment_map,
    get_financials_enrichment_map,
    get_inst_ownership_map,
    get_analyst_momentum_map,
)


@pytest.fixture()
def tmp_db(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE earnings_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            fiscal_quarter TEXT NOT NULL,
            eps_actual REAL,
            eps_estimate REAL,
            surprise_pct REAL,
            revenue_actual REAL,
            revenue_estimate REAL,
            reported_at TEXT,
            source TEXT NOT NULL DEFAULT 'yahoo',
            scraped_at TEXT NOT NULL,
            UNIQUE (ticker, fiscal_quarter, source)
        );
        CREATE TABLE financial_statements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            fiscal_year TEXT NOT NULL,
            statement_type TEXT NOT NULL,
            line_item_key TEXT NOT NULL,
            value REAL,
            source TEXT NOT NULL DEFAULT 'yahoo',
            scraped_at TEXT NOT NULL,
            UNIQUE (ticker, fiscal_year, statement_type, line_item_key, source)
        );
        CREATE TABLE institutional_holders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            filing_date TEXT NOT NULL,
            holder_name TEXT NOT NULL,
            shares INTEGER,
            pct_out REAL,
            value REAL,
            source TEXT NOT NULL DEFAULT 'yahoo',
            scraped_at TEXT NOT NULL,
            UNIQUE (ticker, filing_date, holder_name, source)
        );
        CREATE TABLE analyst_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            event_date TEXT NOT NULL,
            firm TEXT NOT NULL,
            from_grade TEXT,
            to_grade TEXT,
            action TEXT,
            price_target_action TEXT,
            current_price_target REAL,
            prior_price_target REAL,
            source TEXT NOT NULL DEFAULT 'yahoo',
            scraped_at TEXT NOT NULL,
            UNIQUE (ticker, event_date, firm, action, source)
        );
    """)
    conn.commit()
    conn.close()
    return db_path


def test_earnings_enrichment_map_shape(tmp_db):
    """Map returns list-of-dicts per ticker, ordered most-recent first.

    Catches: wrong column names in SELECT or reversed sort order.
    Ignores: tickers with no earnings (absent key is correct — caller treats as empty list).
    """
    conn = sqlite3.connect(tmp_db)
    conn.executemany(
        "INSERT INTO earnings_history (ticker, fiscal_quarter, eps_actual, eps_estimate, surprise_pct, reported_at, scraped_at) "
        "VALUES (?, ?, ?, ?, ?, ?, '2026-05-14T00:00:00')",
        [
            ("AAPL", "2026-Q1", 2.18, 2.10, 3.8,  "2026-01-28"),
            ("AAPL", "2025-Q4", 2.11, 2.35, -10.2, "2025-10-30"),
            ("TSLA", "2026-Q1", 0.72, 0.64, 12.5, "2026-04-22"),
        ],
    )
    conn.commit()
    conn.close()

    result = get_earnings_enrichment_map(tmp_db)

    assert set(result.keys()) == {"AAPL", "TSLA"}
    assert len(result["AAPL"]) == 2
    assert result["AAPL"][0]["fiscal_quarter"] == "2026-Q1"  # most recent first
    assert result["AAPL"][0]["surprise_pct"] == pytest.approx(3.8)
    assert result["TSLA"][0]["eps_actual"] == pytest.approx(0.72)
    assert "fiscal_quarter" in result["AAPL"][0]
    assert "eps_estimate" in result["AAPL"][0]
    assert "reported_at" in result["AAPL"][0]


def test_financials_enrichment_map_shape(tmp_db):
    """Map returns 3-level nesting: {ticker: {stmt_type: {fiscal_year: {line_item_key: value}}}}.

    Catches: wrong nesting order (e.g. year before stmt_type) or missing line items.
    Ignores: tickers not yet scraped (absent from map is correct behaviour).
    """
    conn = sqlite3.connect(tmp_db)
    conn.executemany(
        "INSERT INTO financial_statements (ticker, fiscal_year, statement_type, line_item_key, value, scraped_at) "
        "VALUES (?, ?, ?, ?, ?, '2026-05-14T00:00:00')",
        [
            ("AAPL", "2025", "INCOME",  "NetIncome",   94000000000.0),
            ("AAPL", "2025", "INCOME",  "TotalRevenue", 391000000000.0),
            ("AAPL", "2025", "BALANCE", "TotalAssets",  352800000000.0),
            ("AAPL", "2024", "INCOME",  "NetIncome",    97000000000.0),
            ("TSLA", "2025", "CASHFLOW","OperatingCashFlow", 14500000000.0),
        ],
    )
    conn.commit()
    conn.close()

    result = get_financials_enrichment_map(tmp_db)

    assert "AAPL" in result
    assert "TSLA" in result
    assert "INCOME"  in result["AAPL"]
    assert "BALANCE" in result["AAPL"]
    assert "2025"    in result["AAPL"]["INCOME"]
    assert "2024"    in result["AAPL"]["INCOME"]
    assert result["AAPL"]["INCOME"]["2025"]["NetIncome"] == pytest.approx(94000000000.0)
    assert result["AAPL"]["INCOME"]["2025"]["TotalRevenue"] == pytest.approx(391000000000.0)
    assert result["AAPL"]["BALANCE"]["2025"]["TotalAssets"] == pytest.approx(352800000000.0)
    assert result["TSLA"]["CASHFLOW"]["2025"]["OperatingCashFlow"] == pytest.approx(14500000000.0)


def test_inst_ownership_map_shape(tmp_db):
    """Map returns latest-filing aggregation: total_pct_held, holder_count, filing_date.

    Catches: JOIN not filtering to latest filing date (would over-count across dates).
    Ignores: holders with NULL pct_out (SUM returns NULL or partial — DB-level constraint test).
    """
    conn = sqlite3.connect(tmp_db)
    conn.executemany(
        "INSERT INTO institutional_holders (ticker, filing_date, holder_name, pct_out, scraped_at) "
        "VALUES (?, ?, ?, ?, '2026-05-14T00:00:00')",
        [
            # AAPL — two filing dates; only 2026-03-31 should be used
            ("AAPL", "2026-03-31", "Vanguard",   7.2),
            ("AAPL", "2026-03-31", "BlackRock",  6.1),
            ("AAPL", "2025-12-31", "Vanguard",   7.0),  # stale — must be ignored
            # TSLA — single filing date
            ("TSLA", "2026-03-31", "ARK Invest", 4.5),
        ],
    )
    conn.commit()
    conn.close()

    result = get_inst_ownership_map(tmp_db)

    assert set(result.keys()) == {"AAPL", "TSLA"}
    assert result["AAPL"]["holder_count"]   == 2
    assert result["AAPL"]["total_pct_held"] == pytest.approx(13.3)
    assert result["AAPL"]["filing_date"]    == "2026-03-31"
    assert result["TSLA"]["holder_count"]   == 1
    assert result["TSLA"]["total_pct_held"] == pytest.approx(4.5)


def test_analyst_momentum_map_shape(tmp_db):
    """Map returns upgrades, downgrades, net_momentum for the 90-day window.

    Catches: CASE WHEN action logic wrong (e.g. 'init' not counted as upgrade) or
             events outside the window being included.
    Ignores: tickers with zero activity in window (absent from map is correct — caller
             treats absent key as None → neutral 50.0).
    """
    conn = sqlite3.connect(tmp_db)
    # Use date('now', ...) relative dates so the test stays valid over time
    conn.executemany(
        "INSERT INTO analyst_changes (ticker, event_date, firm, action, scraped_at) "
        "VALUES (?, date('now', ?), ?, ?, '2026-05-14T00:00:00')",
        [
            ("AAPL", "-10 days", "Goldman",  "up",   ),
            ("AAPL", "-20 days", "MS",       "init", ),
            ("AAPL", "-30 days", "JPM",      "down", ),
            ("TSLA", "-5 days",  "BofA",     "down", ),
            ("TSLA", "-200 days","Citi",     "up",   ),  # outside 90-day window
        ],
    )
    conn.commit()
    conn.close()

    result = get_analyst_momentum_map(tmp_db)

    assert "AAPL" in result
    assert "TSLA" in result
    assert result["AAPL"]["upgrades_90d"]   == 2  # 'up' + 'init'
    assert result["AAPL"]["downgrades_90d"] == 1
    assert result["AAPL"]["net_momentum"]   == 1
    assert result["TSLA"]["upgrades_90d"]   == 0  # outside-window event excluded
    assert result["TSLA"]["downgrades_90d"] == 1
    assert result["TSLA"]["net_momentum"]   == -1


def test_analyst_momentum_map_pt_contributions_v016(tmp_db):
    """v0.16.0: soft action rows (main/reit) with priceTargetAction Raises/Lowers
    contribute ±0.25 to net_momentum; hard rows ignore PT (no double-count).

    Synthetic fixture covers the four contribution branches at once:
      AAPL: 2 hard up + 3 main+Raises + 1 main+Lowers → net = 2 + 0.5 = +2.5
      TSLA: 1 hard down + 1 up+Lowers (hard wins, PT ignored) → net = -1 + 1 = 0
            (hard down=-1, hard up=+1; PT 'Lowers' on the up row IGNORED → net 0)
      NVDA: 0 hard + 1 main+Maintains + 1 reit+Raises → net = +0.25
            (Maintains contributes 0; only the reit Raises counts)

    Catches:
      - PT contribution branch missing entirely (NVDA would be absent from map).
      - Double-counting: TSLA would land at -0.75 (=-1 -0.25 from up+Lowers PT)
        instead of 0 if the SQL CASE allowed hard rows to fall through to PT.
      - Maintains/Announces being mis-weighted: NVDA would drift off +0.25.
    Ignores: ladder-tier behaviour (that's the scorer's job, covered by
             test_phase2b_scorers float-ladder cases).
    """
    conn = sqlite3.connect(tmp_db)
    conn.executemany(
        "INSERT INTO analyst_changes "
        "  (ticker, event_date, firm, action, price_target_action, scraped_at) "
        "VALUES (?, date('now', ?), ?, ?, ?, '2026-05-25T00:00:00')",
        [
            # AAPL: 2 hard up + 3 main+Raises + 1 main+Lowers
            ("AAPL", "-1 days", "F1", "up",   None,       ),
            ("AAPL", "-2 days", "F2", "up",   None,       ),
            ("AAPL", "-3 days", "F3", "main", "Raises",   ),
            ("AAPL", "-4 days", "F4", "main", "Raises",   ),
            ("AAPL", "-5 days", "F5", "main", "Raises",   ),
            ("AAPL", "-6 days", "F6", "main", "Lowers",   ),
            # TSLA: 1 hard down + 1 hard up with a 'Lowers' PT (PT must be IGNORED)
            ("TSLA", "-1 days", "G1", "down", None,       ),
            ("TSLA", "-2 days", "G2", "up",   "Lowers",   ),  # hard wins → +1, not +0.75
            # NVDA: Maintains (=0) + reit+Raises (=+0.25)
            ("NVDA", "-1 days", "H1", "main", "Maintains",),
            ("NVDA", "-2 days", "H2", "reit", "Raises",   ),
        ],
    )
    conn.commit()
    conn.close()

    result = get_analyst_momentum_map(tmp_db)

    assert result["AAPL"]["upgrades_90d"]   == 2
    assert result["AAPL"]["downgrades_90d"] == 0
    assert result["AAPL"]["net_momentum"]   == pytest.approx(2.5)

    assert result["TSLA"]["upgrades_90d"]   == 1
    assert result["TSLA"]["downgrades_90d"] == 1
    assert result["TSLA"]["net_momentum"]   == pytest.approx(0.0)  # PT on hard row ignored

    assert result["NVDA"]["upgrades_90d"]   == 0
    assert result["NVDA"]["downgrades_90d"] == 0
    assert result["NVDA"]["net_momentum"]   == pytest.approx(0.25)
