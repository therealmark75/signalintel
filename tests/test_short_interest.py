"""
Component 14 (short_interest) scoring tests, v0.19.0.

short_interest is a one-sided additive PENALTY (0, -5, -10, -15) on the
composite, mirroring score_altman_penalty. This file pins the penalty
breakpoints AND the same-commit extraction: score_quality must no longer
apply any short-interest penalty (the signal moved out of quality into the
penalty term, so the composite never double-counts short interest).
"""
import pytest

from signals.scorer import score_short_interest_penalty, score_quality


def test_short_interest_penalty_breakpoints():
    """
    Catches: the penalty ladder drifting off the >10 / >20 / >30 breakpoints,
    or a sign error (a penalty must be <= 0, never a bonus).
    Ignores: values between breakpoints beyond confirming the band they fall
    in; the contract is the four bands, not every intermediate input.
    """
    assert score_short_interest_penalty(35) == -3    # > 30
    assert score_short_interest_penalty(25) == -2    # > 20
    assert score_short_interest_penalty(15) == -1    # > 10
    assert score_short_interest_penalty(10) == 0     # boundary: not > 10
    assert score_short_interest_penalty(5) == 0      # lightly shorted, no drag
    assert score_short_interest_penalty(0) == 0
    # Monotonically non-increasing as short interest rises.
    assert score_short_interest_penalty(35) <= score_short_interest_penalty(25) <= \
        score_short_interest_penalty(15) <= score_short_interest_penalty(5)


def test_short_interest_penalty_missing_and_implausible():
    """
    Catches: missing data being punished (P5 breach) or the >100 implausible
    noise guard being absent (an extreme bad value must apply NO penalty,
    mirroring score_inst_ownership, not the maximum -15).
    Ignores: the exact value of plausible inputs (covered above).
    """
    assert score_short_interest_penalty(None) == 0    # P5 missing -> no penalty
    assert score_short_interest_penalty(150) == 0     # >100 noise -> guarded
    assert score_short_interest_penalty(319.31) == 0  # live universe max observed


def test_score_quality_no_longer_penalises_short_interest():
    """
    Catches: a regression that re-introduces a short-interest term inside
    score_quality (the v0.18.x penalty), which would double-count short
    interest now that the standalone penalty term is live. Quality must be
    invariant to short_interest_pct.
    Ignores: the absolute quality value (driven by roe / eps / analyst);
    only its invariance to short_interest_pct is asserted here.
    """
    base = {
        "roe": 18.0,
        "eps_growth_this_yr": 12.0,
        "eps_growth_next_yr": 8.0,
        "analyst_recom": 2.0,
    }
    q_none = score_quality({**base, "short_interest_pct": None})
    q_low = score_quality({**base, "short_interest_pct": 2.0})
    q_high = score_quality({**base, "short_interest_pct": 45.0})
    q_extreme = score_quality({**base, "short_interest_pct": 90.0})
    assert q_none == q_low == q_high == q_extreme, (
        "score_quality must be invariant to short_interest_pct as of v0.19.0; "
        f"got none={q_none} low={q_low} high={q_high} extreme={q_extreme}"
    )
