"""Row-shape contract lock for the registry-driven /api/signals* endpoints
(Phase 3 Step 6).

The three signal-list handlers (api_signals, api_signals_by_sector,
api_signals_by_rating in web/app.py) were migrated from hand-listed score
columns to a single signal_scores_projection(surface='signals') call. These
tests freeze the JSON row shape those endpoints emit so a future registry
change that drops or renames a signals component fails loudly at PR time
instead of silently changing the API payload.

Catches:
  - A signals component being dropped or renamed in signals/components.py
    (the registry-coupling test reads the expected db_column set straight
    from components_for_surface('signals'), so the endpoint shape is bound
    to the registry, not to a static list).
  - sector_strength_score leaking back onto the signals surface after its
    Step 5.5 removal.
  - The post-query transform regressing: raw 'flags' leaking into the
    payload, or the derived 'flag_list' / non-component carries
    (composite_score, rating, scored_at) going missing.

Ignores (by design, not oversight):
  - Component VALUES. This is a key-presence/name contract, not a value or
    range check; scorer correctness is covered by test_scorer / test_invariants.
  - Tier-based score stripping. The `client` fixture authenticates as
    user_id=2 (markn); penny-row stripping for non-elite tiers is exercised
    by test_penny_screener_gating / test_entitlements, not here.
  - Extra non-component keys (ticker, price, sector, industry). Assertions
    1-3 lock the four-component set explicitly; assertion 4 asserts the live
    keys are a SUPERSET of the registry set, so adding components 9-16 to the
    signals surface later keeps this contract valid without an edit here.
"""
import json

import pytest

from signals.components import components_for_surface


# Literal parity anchor for assertions 1-3 (the registry-coupling assertion 4
# derives its expected set dynamically instead).
SIGNAL_COMPONENT_KEYS = {
    "momentum_score",
    "quality_score",
    "insider_score",
    "reversion_score",
}

# Non-component carries that must survive the projection + post-query transform.
NON_COMPONENT_CARRIES = {"composite_score", "rating", "scored_at", "flag_list"}


def _get_rows(client, url):
    """GET `url`, assert 200 + a non-empty JSON list, return the rows."""
    resp = client.get(url)
    assert resp.status_code == 200, f"{url} returned {resp.status_code}"
    data = json.loads(resp.data)
    assert isinstance(data, list), f"{url} did not return a list: {type(data)}"
    assert data, f"{url} returned an empty list; cannot lock row shape"
    return data


def _assert_component_shape(rows, url):
    """Every row carries the four signals components, and none carries the
    Step-5.5-removed sector_strength_score."""
    for row in rows:
        keys = set(row.keys())
        missing = SIGNAL_COMPONENT_KEYS - keys
        assert not missing, f"{url} row missing components {missing}"
        assert "sector_strength_score" not in keys, (
            f"{url} row carries sector_strength_score; it was removed from the "
            "signals surface at Step 5.5"
        )


def test_api_signals_component_shape(client):
    """Assertion 1: /api/signals locks the four-component set."""
    rows = _get_rows(client, "/api/signals")
    _assert_component_shape(rows, "/api/signals")


def test_api_signals_by_sector_component_shape(client):
    """Assertion 2: /api/signals/sector/<sector> locks the four-component set
    (Technology is a sector known to carry rows)."""
    url = "/api/signals/sector/Technology"
    rows = _get_rows(client, url)
    _assert_component_shape(rows, url)


def test_api_signals_by_rating_component_shape(client):
    """Assertion 3: /api/signals/<rating> locks the four-component set, using a
    valid internal rating code that returns rows (HOLD is reliably populated;
    STRONG_BUY can be thin)."""
    for rating in ("HOLD", "STRONG_BUY"):
        resp = client.get(f"/api/signals/{rating}")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        if data:
            _assert_component_shape(data, f"/api/signals/{rating}")
            return
    pytest.fail("Neither /api/signals/HOLD nor /api/signals/STRONG_BUY returned rows")


def test_api_signals_keys_are_registry_superset(client):
    """Assertion 4 (the key test): couple the endpoint shape to the registry.

    Derive the expected component db_columns from
    components_for_surface('signals') and assert the live row keys are a
    superset. Adding components 9-16 to the signals surface later will require
    this contract to still hold (the projection must emit them and the endpoint
    must carry them through)."""
    expected = {c.db_column for c in components_for_surface("signals")}
    assert expected, "components_for_surface('signals') returned no db_columns"
    rows = _get_rows(client, "/api/signals")
    for row in rows:
        keys = set(row.keys())
        assert keys >= expected, (
            f"/api/signals row keys are not a superset of the registry signals "
            f"components; missing {expected - keys}"
        )


def test_api_signals_non_component_carries_and_no_raw_flags(client):
    """Assertion 5: non-component carries survive (composite_score, rating,
    scored_at, flag_list) and raw 'flags' is never exposed (the post-query
    block converts it to flag_list)."""
    rows = _get_rows(client, "/api/signals")
    for row in rows:
        keys = set(row.keys())
        missing = NON_COMPONENT_CARRIES - keys
        assert not missing, f"/api/signals row missing non-component carries {missing}"
        assert "flags" not in keys, (
            "/api/signals row exposes raw 'flags'; it should be converted to "
            "'flag_list' by the post-query transform"
        )
