"""
tests/test_volume_component.py
──────────────────────────────
Unit tests for the Volume Confirmation component (signals/scorer.py).

Tests use _compute_volume(rvol, pct) -> (score, band) directly so each
assertion can confirm BOTH which branch fired (band name) AND that
alternative branches did NOT fire (score/band differ from other states).

P15 contract:
  Catches: correct score and band for every rubric state and all
           boundary values; NULL safety; climax cap on extreme RVOL.
  Ignores: composite integration (tested via test_invariants.py on live
           DB data); DB persistence (covered by smoke tests).
"""

import pytest
from signals.scorer import _compute_volume, score_volume


# ── Null-safety (P5) ─────────────────────────────────────────────────

def test_null_rvol_returns_neutral():
    """NULL rvol → score=50, band='null'. Confirmed band (80) did NOT fire."""
    score, band = _compute_volume(None, 1.5)
    assert score == 50.0
    assert band == "null"
    assert score != 80.0   # confirmed bullish did not fire
    assert score != 65.0   # climax did not fire


def test_null_pct_returns_neutral():
    """NULL pct → score=50, band='null'. Confirmed band (80) did NOT fire."""
    score, band = _compute_volume(2.0, None)
    assert score == 50.0
    assert band == "null"
    assert score != 80.0
    assert score != 65.0


def test_both_null_returns_neutral():
    """Both NULL → score=50, band='null'."""
    score, band = _compute_volume(None, None)
    assert score == 50.0
    assert band == "null"


# ── Climax/exhaustion band (rvol >= 4.0) ─────────────────────────────

def test_climax_bullish():
    """rvol=5.0, pct=+2.0 → climax bullish (65). Confirmed band (80) did NOT fire."""
    score, band = _compute_volume(5.0, 2.0)
    assert score == 65.0
    assert band == "climax"
    assert score != 80.0   # confirmed bullish did not execute
    assert score != 50.0   # indecision did not execute


def test_climax_bearish():
    """rvol=5.0, pct=-2.0 → climax bearish (35). Confirmed bearish (20) did NOT fire."""
    score, band = _compute_volume(5.0, -2.0)
    assert score == 35.0
    assert band == "climax"
    assert score != 20.0   # confirmed bearish did not execute


def test_climax_indecision():
    """rvol=5.0, pct=+0.5 → climax indecision (50). Climax band still active."""
    score, band = _compute_volume(5.0, 0.5)
    assert score == 50.0
    assert band == "climax"   # indecision within climax, NOT null band


# ── Confirmed breakout band (1.5 <= rvol < 4.0) ─────────────────────

def test_confirmed_bullish():
    """rvol=2.0, pct=+2.0 → confirmed bullish (80). Climax (65) did NOT fire."""
    score, band = _compute_volume(2.0, 2.0)
    assert score == 80.0
    assert band == "confirmed"
    assert score != 65.0   # climax band did not execute
    assert score != 60.0   # mild band did not execute


def test_confirmed_bearish():
    """rvol=2.0, pct=-2.0 → confirmed bearish (20). Climax bearish (35) did NOT fire."""
    score, band = _compute_volume(2.0, -2.0)
    assert score == 20.0
    assert band == "confirmed"
    assert score != 35.0   # climax bearish did not execute


def test_confirmed_indecision():
    """rvol=2.0, pct=+0.5 → confirmed indecision (50). Confirmed band active."""
    score, band = _compute_volume(2.0, 0.5)
    assert score == 50.0
    assert band == "confirmed"   # NOT null; high vol with no direction


# ── Mild/average volume band (0.8 <= rvol < 1.5) ────────────────────

def test_mild_bullish():
    """rvol=1.0, pct=+1.5 → mild bullish (60). Confirmed (80) did NOT fire."""
    score, band = _compute_volume(1.0, 1.5)
    assert score == 60.0
    assert band == "mild"
    assert score != 80.0   # confirmed bullish did not fire
    assert score != 65.0   # climax did not fire


def test_mild_bearish():
    """rvol=1.0, pct=-1.5 → mild bearish (40). Confirmed bearish (20) did NOT fire."""
    score, band = _compute_volume(1.0, -1.5)
    assert score == 40.0
    assert band == "mild"
    assert score != 20.0   # confirmed bearish did not fire


def test_mild_neutral():
    """rvol=1.0, pct=+0.2 → mild neutral (50). Mild band active, not null."""
    score, band = _compute_volume(1.0, 0.2)
    assert score == 50.0
    assert band == "mild"   # NOT null; average vol with no clear direction


# ── Low conviction band (rvol < 0.8) ────────────────────────────────

def test_low_conviction_ignores_direction():
    """rvol=0.5, pct=+2.0 → low conviction (50). Even strong price move ignored."""
    score, band = _compute_volume(0.5, 2.0)
    assert score == 50.0
    assert band == "low"
    assert score != 80.0   # confirmed bullish did not fire
    assert score != 60.0   # mild bullish did not fire


# ── Boundary values ──────────────────────────────────────────────────

def test_boundary_rvol_exactly_4_is_climax():
    """rvol=4.0 (boundary) with bullish pct → climax band (65), NOT confirmed (80)."""
    score, band = _compute_volume(4.0, 1.5)
    assert score == 65.0
    assert band == "climax"
    assert score != 80.0


def test_boundary_rvol_3_99_is_confirmed():
    """rvol=3.99 (just below climax threshold) → confirmed band (80)."""
    score, band = _compute_volume(3.99, 1.5)
    assert score == 80.0
    assert band == "confirmed"
    assert score != 65.0


def test_boundary_rvol_exactly_1_5_is_confirmed():
    """rvol=1.5 (boundary) with bullish pct → confirmed band (80), NOT mild (60)."""
    score, band = _compute_volume(1.5, 1.5)
    assert score == 80.0
    assert band == "confirmed"
    assert score != 60.0


def test_boundary_rvol_1_49_is_mild():
    """rvol=1.49 (just below confirmed threshold) → mild band (60)."""
    score, band = _compute_volume(1.49, 1.5)
    assert score == 60.0
    assert band == "mild"
    assert score != 80.0


def test_boundary_rvol_exactly_0_8_is_mild():
    """rvol=0.8 (boundary) with bullish pct → mild band (60), NOT low (50)."""
    score, band = _compute_volume(0.8, 1.5)
    assert score == 60.0
    assert band == "mild"
    assert score != 50.0 or band != "low"   # at least one must differ from low


def test_boundary_rvol_0_79_is_low():
    """rvol=0.79 (just below mild threshold) → low band (50)."""
    score, band = _compute_volume(0.79, 1.5)
    assert score == 50.0
    assert band == "low"
    assert band != "mild"


def test_boundary_pct_exactly_1_0_is_bullish():
    """pct=1.0 (boundary) in confirmed band → bullish (80), NOT indecision (50)."""
    score, band = _compute_volume(2.0, 1.0)
    assert score == 80.0
    assert band == "confirmed"


def test_boundary_pct_0_99_is_indecision():
    """pct=0.99 (just below bullish threshold) → indecision (50)."""
    score, band = _compute_volume(2.0, 0.99)
    assert score == 50.0
    assert band == "confirmed"


def test_boundary_pct_exactly_neg_1_0_is_bearish():
    """pct=-1.0 (boundary) in confirmed band → bearish (20), NOT indecision."""
    score, band = _compute_volume(2.0, -1.0)
    assert score == 20.0
    assert band == "confirmed"


def test_boundary_pct_neg_0_99_is_indecision():
    """pct=-0.99 (just above bearish threshold) → indecision (50)."""
    score, band = _compute_volume(2.0, -0.99)
    assert score == 50.0
    assert band == "confirmed"


# ── Edge cases ───────────────────────────────────────────────────────

def test_edge_rvol_zero_is_low():
    """rvol=0 → low band (50). Treated same as rvol < 0.8."""
    score, band = _compute_volume(0, 2.0)
    assert score == 50.0
    assert band == "low"
    assert score != 80.0


def test_edge_extreme_rvol_capped_at_climax():
    """rvol=10.0 with strong bullish pct → climax (65), NOT confirmed (80).
    This is the critical climax cap: extreme RVOL does not unlock the
    confirmed-band maximum."""
    score, band = _compute_volume(10.0, 2.0)
    assert score == 65.0
    assert band == "climax"
    assert score != 80.0   # confirmed band MUST NOT have fired


# ── Public API wrapper ───────────────────────────────────────────────

def test_score_volume_matches_compute_volume():
    """score_volume() is a thin wrapper — result must match _compute_volume()[0]."""
    cases = [
        (None, 1.0), (2.0, None), (5.0, 2.0), (2.0, 2.0),
        (1.0, 1.5), (0.5, 2.0), (4.0, 1.5),
    ]
    for rvol, pct in cases:
        expected, _ = _compute_volume(rvol, pct)
        assert score_volume(rvol, pct) == expected, f"Mismatch for rvol={rvol}, pct={pct}"
