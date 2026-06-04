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
