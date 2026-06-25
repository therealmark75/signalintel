"""
Screener API filter tests, exchange filter and values-screen (exclude_ethical) correctness.

Uses the live data/trading_system.db via the `client` fixture (session['user_id']=2).
All tests request per_page=200 so row-level assertions cover a meaningful sample.
"""
import json
import sqlite3
import pytest

from config.constants import DATABASE_PATH, ETHICAL_EXCLUDED_INDUSTRIES

# Mirror of api_screener's base population (latest snapshot per ticker within the
# 2-day window). Kept byte-identical to the route's latest_ss subquery so the
# values-screen tests can assert exact removal counts against the same universe.
_LATEST_SS = """
    SELECT s.ticker, s.industry
    FROM screener_snapshots s
    INNER JOIN (
        SELECT ticker, MAX(scraped_at) AS max_ts
        FROM screener_snapshots
        WHERE scraped_at >= datetime('now', '-2 days')
        GROUP BY ticker
    ) lts ON s.ticker = lts.ticker AND s.scraped_at = lts.max_ts
"""


def _db_universe_counts():
    """Return (total_rows, excluded_rows, nonalcoholic_rows) from the live DB
    using the same base population the screener route uses."""
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        rows = conn.execute(_LATEST_SS).fetchall()
    finally:
        conn.close()
    excluded_set = set(ETHICAL_EXCLUDED_INDUSTRIES)
    total = len(rows)
    excluded = sum(1 for _, ind in rows if ind in excluded_set)
    nonalc = sum(1 for _, ind in rows if ind == "Beverages - Non-Alcoholic")
    return total, excluded, nonalc


def _get(client, params=""):
    resp = client.get(f"/api/screener?per_page=200{('&' + params) if params else ''}")
    assert resp.status_code == 200
    return json.loads(resp.data)


def test_api_screener_exchange_filter_single_nasdaq(client):
    """
    ?exchange=NASDAQ must return only rows with exchange == 'NASDAQ'.

    Catches: WHERE clause missing or using wrong column, so NYSE/AMEX/Other
             rows leak into a NASDAQ-only result set.
    Ignores: total count, whether the result set is empty (data-dependent),
             pagination beyond per_page=200.
    """
    data = _get(client, "exchange=NASDAQ")
    assert data["total"] >= 0
    for row in data["rows"]:
        assert row["exchange"] == "NASDAQ", (
            f"Ticker {row['ticker']} has exchange={row['exchange']!r}, "
            "expected 'NASDAQ'"
        )


def test_api_screener_exchange_filter_multiple(client):
    """
    ?exchange=NASDAQ,NYSE must return only rows with exchange in {NASDAQ, NYSE}.
    No AMEX or Other rows may appear.

    Catches: IN clause not being multi-value, or exchange values being
             incorrectly split on the backend (e.g. 'NASDAQ,NYSE' treated
             as a single string literal).
    Ignores: relative counts between NASDAQ and NYSE, total, pagination.
    """
    data = _get(client, "exchange=NASDAQ,NYSE")
    assert data["total"] >= 0
    for row in data["rows"]:
        assert row["exchange"] in ("NASDAQ", "NYSE"), (
            f"Ticker {row['ticker']} has exchange={row['exchange']!r}, "
            "expected one of NASDAQ or NYSE"
        )


def test_api_screener_exchange_filter_other_includes_null(client):
    """
    ?exchange=Other must return rows with exchange='Other' OR exchange=None
    (COALESCE maps NULL ticker_metadata join results into the 'Other' bucket).

    Catches: COALESCE omitted so tickers with no ticker_metadata row are
             silently excluded when filtering for Other.
    Ignores: whether any NULL-exchange rows actually exist in the live DB
             (COALESCE correctness is structural, not count-dependent).
    """
    data = _get(client, "exchange=Other")
    assert data["total"] >= 0
    for row in data["rows"]:
        assert row["exchange"] in ("Other", None), (
            f"Ticker {row['ticker']} has exchange={row['exchange']!r}, "
            "expected 'Other' or None"
        )


def test_api_screener_exchange_filter_absent(client):
    """
    Omitting the exchange param must return the same total as passing all
    four known values explicitly (no rows are excluded by default).

    Catches: a WHERE condition being applied unconditionally even when the
             param is absent, silently shrinking the result set.
    Ignores: row order, pagination details, any difference caused by tickers
             whose exchange resolves to a value outside the four known values
             (COALESCE covers NULLs into 'Other', so totals should be equal).
    """
    unfiltered = _get(client)
    all_exchanges = _get(client, "exchange=NYSE,NASDAQ,AMEX,Other")
    assert unfiltered["total"] == all_exchanges["total"], (
        f"Unfiltered total={unfiltered['total']} differs from "
        f"all-exchanges total={all_exchanges['total']} — exchange filter "
        "is being applied when param is absent"
    )


def test_api_screener_exchange_filter_unknown_value(client):
    """
    ?exchange=BOGUS must return an empty result set (total=0, rows=[]),
    not a 500 error or a full unfiltered response.

    Catches: backend erroring on an unrecognised exchange value, or
             silently ignoring the param and returning all rows.
    Ignores: which exchange values are considered 'valid' — no server-side
             allowlist exists, so any value simply matches nothing.
    """
    data = _get(client, "exchange=BOGUS")
    assert data["total"] == 0, (
        f"Expected total=0 for exchange=BOGUS, got {data['total']}"
    )
    assert data["rows"] == [], (
        f"Expected empty rows for exchange=BOGUS, got {len(data['rows'])} rows"
    )


def test_api_screener_excludes_hidden_subscores(client):
    """An elite caller's /api/screener rows carry the 5 screener components
    but NONE of the 6 v0.17.0 sub-scores (the locked Phase 2 Q3 surface rule).

    The `client` fixture is user_id=2 (markn, elite), so scores are not
    stripped and every present key is real. This is the response-shape lock
    the Step 5 projection switch introduced: a regression that widened the
    screener projection to all 11 components (or reverted the surface filter)
    would leak the sub-scores here.

    Catches: sub-score leakage onto the screener surface, or a screener
             component silently dropped from the projection.
    Ignores: row values (only key presence/absence), tier-stripping behaviour
             for non-elite (a separate concern), pagination.
    """
    data = _get(client, "per_page=5")
    rows = data["rows"]
    if not rows:
        pytest.skip("screener returned no rows on the live DB this run")
    forbidden = ("volume_score", "earnings_score", "piotroski_score",
                 "inst_own_score", "analyst_mom_score", "altman_penalty")
    required = ("momentum_score", "quality_score", "insider_score",
                "reversion_score", "sector_strength_score")
    for row in rows:
        leaked = [k for k in forbidden if k in row]
        assert not leaked, f"{row.get('ticker')} leaked hidden sub-scores: {leaked}"
        missing = [k for k in required if k not in row]
        assert not missing, f"{row.get('ticker')} missing screener components: {missing}"


def test_api_screener_exclude_ethical_removes_excluded_industries(client):
    """
    ?exclude_ethical=1 must remove rows whose industry is in the values-screen
    set, and must shrink the universe total relative to the unfiltered baseline.

    Catches: the NOT IN clause matching the wrong column, an excluded industry
             (e.g. Tobacco) leaking through, or the filter being a no-op that
             leaves the total unchanged.
    Ignores: which specific tickers appear on the first page, the absolute
             total (data-dependent), pagination beyond per_page=200, and any
             industry outside the locked 10-string set.
    """
    excluded_set = set(ETHICAL_EXCLUDED_INDUSTRIES)
    baseline = _get(client)
    filtered = _get(client, "exclude_ethical=1")
    assert filtered["total"] < baseline["total"], (
        f"exclude_ethical=1 total={filtered['total']} not less than "
        f"baseline total={baseline['total']}, filter removed no rows"
    )
    for row in filtered["rows"]:
        assert row.get("industry") not in excluded_set, (
            f"Ticker {row['ticker']} has industry={row.get('industry')!r}, "
            "which is in the values-screen exclusion set but leaked through"
        )


def test_api_screener_exclude_ethical_off_matches_baseline(client):
    """
    Omitting exclude_ethical, and passing exclude_ethical=0, must both return
    the same total as the unfiltered baseline (no silent always-on filtering).

    Catches: the values-screen WHERE block being applied unconditionally, or a
             falsy param value ('0') being treated as truthy.
    Ignores: row order, pagination, and the absolute total (only equality of
             the three totals matters).
    """
    baseline = _get(client)
    off = _get(client, "exclude_ethical=0")
    assert baseline["total"] == off["total"], (
        f"baseline total={baseline['total']} differs from exclude_ethical=0 "
        f"total={off['total']}, a falsy value is being treated as on"
    )


def test_api_screener_ethical_exclusion_set_is_exactly_the_locked_ten(client):
    """
    config.constants.ETHICAL_EXCLUDED_INDUSTRIES must be exactly the 10 locked
    strings, in the locked order. This is a drift guard, not a route test.

    Catches: an accidental edit to the tuple (addition, removal, reordering,
             typo, or the deliberately-deferred v1 categories such as
             'Aerospace & Defense' being slipped in).
    Ignores: the screener route entirely, the DB, and whether any of these
             industries currently has rows in the live data.
    """
    expected = (
        "Tobacco",
        "Gambling",
        "Resorts & Casinos",
        "Beverages - Brewers",
        "Beverages - Wineries & Distilleries",
        "Oil & Gas E&P",
        "Oil & Gas Drilling",
        "Oil & Gas Integrated",
        "Thermal Coal",
        "Coking Coal",
    )
    assert ETHICAL_EXCLUDED_INDUSTRIES == expected, (
        "ETHICAL_EXCLUDED_INDUSTRIES drifted from the locked v1 set: "
        f"got {ETHICAL_EXCLUDED_INDUSTRIES!r}"
    )
    assert len(ETHICAL_EXCLUDED_INDUSTRIES) == 10


def test_api_screener_exclude_ethical_does_not_overreach_to_adjacent(client):
    """
    The alcohol exclusion must use exact-string match: 'Beverages - Non-Alcoholic'
    is NOT in the set, and exclude_ethical=1 removes EXACTLY the excluded-industry
    rows from the universe (baseline total minus filtered total equals the DB
    count of excluded-industry tickers), proving no adjacent industry is swept up.

    Catches: a fuzzy/prefix match (e.g. 'Beverages -%') that would over-exclude
             non-alcoholic beverages, or any removal count larger than the exact
             excluded population.
    Ignores: which non-alcoholic tickers appear on the result page (the proof is
             the exact arithmetic, not page membership) and the absolute totals.
    """
    assert "Beverages - Non-Alcoholic" not in ETHICAL_EXCLUDED_INDUSTRIES
    total, excluded_count, nonalc_count = _db_universe_counts()
    if nonalc_count == 0:
        pytest.skip("no Beverages - Non-Alcoholic rows in the live universe this run")
    baseline = _get(client)
    filtered = _get(client, "exclude_ethical=1")
    assert baseline["total"] - filtered["total"] == excluded_count, (
        f"removed={baseline['total'] - filtered['total']} rows but the DB shows "
        f"exactly {excluded_count} excluded-industry tickers, filter over- or "
        "under-reaches"
    )
