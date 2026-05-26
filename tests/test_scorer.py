"""
Tests for signals/scorer.py — paywall-arc proprietary-flag discipline.

The 4d invariant: every flag emitted from a proprietary code path
(insider_score / reversion_score threshold) is a member of
PROPRIETARY_FLAGS. These tests catch a future regression where
someone adds a proprietary flag as an inline literal instead of
sourcing it from the _PROPRIETARY_* tuples — that would leave the
entitlements gate blind to the new leak surface.

This is the flag-world equivalent of the type:'rating' discipline
on the /api/ticker/<ticker>/events route. Structural-at-source means
the proprietary classification is set at the append site, not
matched later by string detection.
"""
import pytest
from signals.scorer import build_flags, PROPRIETARY_FLAGS


# ── Each proprietary code path emits a flag in the gate's set ─────


def test_insider_score_high_emits_proprietary_flag():
    """insider_score >= 70 → emits "★ Strong insider buying" AND that
    string is in PROPRIETARY_FLAGS.

    Catches: a future change appending an inline-literal flag on this
             code path that the gate-set wouldn't recognize, leaving
             the proprietary verdict visible to non-elite callers.
    Ignores: which descriptive flags also happen to fire on the same
             row — the row is intentionally bare to isolate the
             proprietary path.
    """
    flags = build_flags(row={}, insider_score=85.0, reversion_score=50.0)
    expected = "★ Strong insider buying"
    assert expected in flags, f"expected {expected!r} in {flags}"
    assert expected in PROPRIETARY_FLAGS, \
        (f"build_flags emitted {expected!r} from a proprietary code path "
         f"but it is NOT in PROPRIETARY_FLAGS — the entitlements gate "
         f"would miss this leak. Source the literal from "
         f"_PROPRIETARY_INSIDER_FLAGS, do not inline.")


def test_insider_score_low_emits_proprietary_flag():
    """insider_score <= 30 → emits "⚠ Insider selling pressure" AND
    that string is in PROPRIETARY_FLAGS.

    Catches: same inline-literal regression on the low-insider branch.
    Ignores: other descriptive flags on the row.
    """
    flags = build_flags(row={}, insider_score=15.0, reversion_score=50.0)
    expected = "⚠ Insider selling pressure"
    assert expected in flags
    assert expected in PROPRIETARY_FLAGS, \
        f"{expected!r} not in PROPRIETARY_FLAGS — gate would leak"


def test_reversion_score_high_emits_proprietary_flag():
    """reversion_score >= 75 → emits "↩ Mean reversion candidate" AND
    that string is in PROPRIETARY_FLAGS.

    Catches: same regression on the reversion path.
    Ignores: descriptive flags from row.
    """
    flags = build_flags(row={}, insider_score=50.0, reversion_score=85.0)
    expected = "↩ Mean reversion candidate"
    assert expected in flags
    assert expected in PROPRIETARY_FLAGS


def test_neutral_scores_emit_no_proprietary_flags():
    """Mid-range scores (insider 31-69, reversion <75) → ZERO
    proprietary flags emitted.

    P15 silence assertion. Catches: a threshold-logic bug where the
    proprietary branches fire on mid-range scores.
    Ignores: descriptive flags (none on a bare row).
    """
    flags = build_flags(row={}, insider_score=50.0, reversion_score=50.0)
    proprietary_seen = [f for f in flags if f in PROPRIETARY_FLAGS]
    assert proprietary_seen == [], \
        f"unexpected proprietary flags on neutral scores: {proprietary_seen}"


def test_descriptive_flags_not_in_proprietary_set():
    """Every descriptive flag the function can emit is NOT in
    PROPRIETARY_FLAGS. Catches: someone accidentally adding a
    descriptive flag string to the _PROPRIETARY_* tuples — that
    would over-broadly strip descriptive market signals from
    non-elite responses.

    Constructs a row that fires every descriptive code path; asserts
    each emitted descriptive flag is OUTSIDE the proprietary set.

    Ignores: the proprietary flags (they're tested above).
    """
    row = {
        'rsi_14':            80.0,    # → "⚠ Overbought RSI"
        'sma_50_pct':        5.0,     # → "↑ Above 50d SMA"
        'sma_200_pct':       3.0,     # → "↑ Above 200d SMA"
        'short_interest_pct': 25.0,   # → "⚠ High short interest 25.0%"
        'analyst_recom':     1.5,     # → "✓ Strong analyst consensus"
        'low_52w_pct':       5.0,     # → "📍 Near 52-week low"
        'high_52w_pct':     -3.0,     # → "🔝 Near 52-week high"
    }
    flags = build_flags(row, insider_score=50.0, reversion_score=50.0)
    descriptive_seen = [f for f in flags if f not in PROPRIETARY_FLAGS]
    # At minimum: RSI overbought + SMA50 + SMA200 + short + analyst + 52w-low + 52w-high
    assert len(descriptive_seen) >= 7, \
        f"expected >= 7 descriptive flags, got {len(descriptive_seen)}: {descriptive_seen}"
    proprietary_leak = [f for f in flags if f in PROPRIETARY_FLAGS]
    assert proprietary_leak == [], \
        f"descriptive-only row should not fire proprietary flags: {proprietary_leak}"


def test_proprietary_flags_set_is_a_frozenset():
    """PROPRIETARY_FLAGS must be a frozenset (immutable). Catches: a
    refactor that turned it into a list/set that could be mutated at
    runtime, opening a privilege-escalation path.
    """
    assert isinstance(PROPRIETARY_FLAGS, frozenset)


def test_proprietary_flags_set_non_empty():
    """The proprietary set must be non-empty (otherwise the gate is a
    no-op). Catches: an accidental empty-tuple regression on the
    _PROPRIETARY_* constants.
    """
    assert len(PROPRIETARY_FLAGS) > 0
