"""Structural lock between the canonical component registry and the
TickerSignal dataclass (Part 39 Step 3).

Catches: a `signals/components.py` registry edit that adds or renames a
component `db_column` without a matching field on the `TickerSignal`
dataclass in `signals/scorer.py`. Such a drift would let the registry
expect a persistence column the scorer never emits (or vice versa) and
surface only at runtime; this test fails it at PR time instead.

Ignores (by design, not oversight):
  - TickerSignal fields that are NOT registry db_columns (ticker, company,
    sector, price, legal_penalty, rating, flags, rsi_14, etc.). The lock is
    one-directional: every registry db_column must have a field, but the
    dataclass may carry extra non-component fields (display / raw data).
  - Field types and default values. This is a name-level structural lock,
    not a type or value contract.
  - The two registry entries with empty db_column ('value', 'legal'):
    all_db_columns() filters them out, so they are out of scope here.
"""
import dataclasses

import pytest

from signals.components import all_db_columns
from signals.scorer import TickerSignal


def _columns_missing_fields(columns, field_names):
    """Return the list of `columns` not present in `field_names`.

    Shared by both tests so the negative case (Test 2) exercises the exact
    same membership logic the positive case (Test 1) asserts on.
    """
    field_set = set(field_names)
    return [c for c in columns if c not in field_set]


def _ticker_signal_field_names():
    """Dataclass field names read dynamically, never hardcoded."""
    return [f.name for f in dataclasses.fields(TickerSignal)]


def test_every_db_column_has_ticker_signal_field():
    """Every registry db_column maps to a TickerSignal field name."""
    field_names = _ticker_signal_field_names()
    missing = _columns_missing_fields(all_db_columns(), field_names)
    assert not missing, (
        "Registry db_columns with no matching TickerSignal field: "
        f"{missing}. Add the field(s) to signals/scorer.py:TickerSignal or "
        "correct the db_column in signals/components.py."
    )


def test_registry_consistency_catches_drift():
    """Negative control: the membership check has teeth.

    Inject a synthetic db_column absent from TickerSignal and confirm the
    same check Test 1 relies on flags it. Proves the lock would catch real
    drift, without mutating the dataclass on disk.
    """
    field_names = _ticker_signal_field_names()
    synthetic = [*all_db_columns(), "__synthetic_missing_field__"]
    with pytest.raises(AssertionError):
        missing = _columns_missing_fields(synthetic, field_names)
        assert not missing, f"missing: {missing}"


def test_projection_default_matches_step_2_contract():
    """signal_scores_projection() with no surface emits all 11 db_columns in
    canonical order, extras prefixed first (the Step 2 contract).

    Catches: a regression that drops, reorders, or surface-filters the
    default (write-path) projection. The default feeds insert_signal_scores'
    equivalent column set, so silent shrinkage would lose persisted columns.
    Ignores: prefix/extras formatting beyond order (covered by the explicit
    extras assertion below); SQL validity (this is a string-shape lock).
    """
    from database.db import signal_scores_projection
    from signals.components import all_db_columns

    # Bare call: exactly the 11 db_columns, comma-joined, in registry order.
    assert signal_scores_projection() == ", ".join(all_db_columns())

    # extras come FIRST, then the full component set, order preserved.
    with_extras = signal_scores_projection(extras=("ticker", "composite_score"))
    assert with_extras == ", ".join(("ticker", "composite_score") + all_db_columns())


def test_projection_with_surface_filters_components():
    """signal_scores_projection(surface=<name>) emits exactly the db_columns
    of components_for_surface(<name>), no more, no less, in registry order.

    Catches: a surface projection leaking columns not on that surface (e.g.
    the v0.17.0 sub-scores onto the screener, which the locked Phase 2 Q3
    design hides) or dropping a column the surface should carry.
    Ignores: prefix handling and non-component extras; those are not surface
    filtered.
    """
    from database.db import signal_scores_projection
    from signals.components import (
        components_for_surface, VALID_SURFACES,
    )

    # Every canonical surface, read dynamically (never hardcoded).
    for surface in VALID_SURFACES:
        expected = [c.db_column for c in components_for_surface(surface) if c.db_column]
        assert signal_scores_projection(surface=surface) == ", ".join(expected), surface

    # Explicit screener lock: 5 present, 6 sub-scores absent.
    screener_proj = signal_scores_projection(surface="screener")
    for col in ("momentum_score", "quality_score", "insider_score",
                "reversion_score", "sector_strength_score"):
        assert col in screener_proj, f"screener missing {col}"
    for col in ("volume_score", "earnings_score", "piotroski_score",
                "inst_own_score", "analyst_mom_score", "altman_penalty"):
        assert col not in screener_proj, f"screener leaked {col}"

    # Explicit ticker lock: every component column present (ticker shows all).
    from signals.components import all_db_columns
    ticker_proj = signal_scores_projection(surface="ticker")
    for col in all_db_columns():
        assert col in ticker_proj, f"ticker missing {col}"


def test_projection_invalid_surface_raises():
    """An unknown surface name raises ValueError (no silent fallback),
    matching components_for_surface()'s contract.

    Catches: a regression that swallows a typo'd surface name and returns an
    unfiltered or empty projection instead of failing loud.
    Ignores: the exact message text.
    """
    from database.db import signal_scores_projection

    with pytest.raises(ValueError):
        signal_scores_projection(surface="nonexistent_surface_xyz")
