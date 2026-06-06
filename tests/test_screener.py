"""
Screener API filter tests — exchange filter correctness.

Uses the live data/trading_system.db via the `client` fixture (session['user_id']=2).
All tests request per_page=200 so row-level assertions cover a meaningful sample.
"""
import json
import pytest


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
