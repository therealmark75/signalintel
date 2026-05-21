"""
Unit tests for the 5 Phase 2b-ii enrichment scorer functions.

Coverage matrix (P21): populated-positive, populated-negative, P5-empty,
partial-data, scorer-specific edge — 5 cases × 5 scorers = 25 tests.

All tests call scorer functions directly with synthetic inputs.
No database access; no Flask context needed.

Catches: scorer logic regressions (wrong ladder tiers, wrong neutral returns,
         Lock 1/3 violations, all-or-nothing Altman broken).
Ignores: integration between scorers and score_all_tickers (tested in
         test_scorer_snapshot.py after commit 3 wires them in).
"""
import pytest
from signals.scorer import (
    score_earnings_surprise,
    score_piotroski,
    score_altman_penalty,
    compute_z_raw,
    compute_z_double_prime_raw,
    score_inst_ownership,
    score_analyst_momentum,
    _parse_market_cap_text,
)
from signals.line_item_keys import PIOTROSKI_LOOKUPS, ALTMAN_LOOKUPS


# ── Helpers ──────────────────────────────────────────────────────────────────

def _fin(income=None, balance=None, cashflow=None, year="2025"):
    """Build minimal financials dict for a single fiscal year."""
    result = {}
    if income:
        result["INCOME"] = {year: income}
    if balance:
        result["BALANCE"] = {year: balance}
    if cashflow:
        result["CASHFLOW"] = {year: cashflow}
    return result


def _fin2(income0=None, balance0=None, cashflow0=None,
          income1=None, balance1=None, cashflow1=None,
          y0="2025", y1="2024"):
    """Build financials dict with two fiscal years (Y0 and Y1)."""
    result = {}
    for stmt, d0, d1 in [("INCOME", income0, income1),
                          ("BALANCE", balance0, balance1),
                          ("CASHFLOW", cashflow0, cashflow1)]:
        if d0 or d1:
            result[stmt] = {}
            if d0: result[stmt][y0] = d0
            if d1: result[stmt][y1] = d1
    return result


# ── score_earnings_surprise ───────────────────────────────────────────────────

def test_earnings_surprise_populated_positive():
    """Four quarters all beating > 10% → score near 100.

    Catches: +25 contribution tier not applied correctly for large beats.
    Ignores: quarters beyond 4th (irrelevant by design, decay weight drops to 0).
    """
    quarters = [{"surprise_pct": 15.0}] * 4
    assert score_earnings_surprise("AAPL", quarters) == pytest.approx(100.0)


def test_earnings_surprise_populated_negative():
    """Four quarters all missing by > 10% → score near 0.

    Catches: -25 contribution tier not applied for large misses.
    Ignores: NULL surprise_pct handling (tested in partial-data case).
    """
    quarters = [{"surprise_pct": -15.0}] * 4
    assert score_earnings_surprise("AAPL", quarters) == pytest.approx(0.0)


def test_earnings_surprise_p5_empty():
    """Empty earnings list → neutral 50.0.

    Catches: P5 branch missing (function errors or returns non-neutral on empty input).
    Ignores: populated cases.
    """
    assert score_earnings_surprise("AAPL", []) == pytest.approx(50.0)


def test_earnings_surprise_partial_data_single_quarter():
    """Only 1 quarter available — should work; decay weight = 4 only.

    Catches: index-out-of-range or wrong weight assignment for short lists.
    Ignores: multi-quarter weighting (not applicable with single entry).
    """
    quarters = [{"surprise_pct": 5.0}]  # 3% < 5% <= 10% → +15 contribution
    # weighted_avg = 4*15 / 4 = 15; score = (15+25)*2 = 80
    assert score_earnings_surprise("AAPL", quarters) == pytest.approx(80.0)


def test_earnings_surprise_neutral_zone():
    """Surprise in (-3%, 0%] → contribution = 0 → score 50.0.

    Catches: neutral zone not implemented (e.g. returning -7 for small negative miss).
    Ignores: larger misses (separate tier tests above).
    """
    quarters = [{"surprise_pct": -1.5}]  # -3% < -1.5% <= 0% → contribution 0
    assert score_earnings_surprise("AAPL", quarters) == pytest.approx(50.0)


# ── score_piotroski ───────────────────────────────────────────────────────────

def test_piotroski_populated_positive():
    """Healthy company — all 9 signals pass → F=9 → 80.0.

    Catches: any single binary signal computed incorrectly (all 9 must fire).
    Ignores: partial-year data (Lock 1 is a separate test).
    """
    financials = _fin2(
        income0  = {"NetIncome": 100e9, "GrossProfit": 120e9, "TotalRevenue": 400e9},
        income1  = {"NetIncome":  80e9, "GrossProfit": 100e9, "TotalRevenue": 350e9},
        balance0 = {"TotalAssets": 350e9, "LongTermDebt":  90e9,
                    "CurrentAssets": 135e9, "CurrentLiabilities": 125e9,
                    "OrdinarySharesNumber": 14.5e9},
        balance1 = {"TotalAssets": 320e9, "LongTermDebt": 100e9,
                    "CurrentAssets": 120e9, "CurrentLiabilities": 120e9,
                    "OrdinarySharesNumber": 15.0e9},
        cashflow0 = {"OperatingCashFlow": 110e9},
        cashflow1 = {"OperatingCashFlow":  90e9},
    )
    assert score_piotroski("AAPL", financials) == pytest.approx(80.0)


def test_piotroski_populated_negative():
    """Distressed company — all 9 signals fail → F=1 → 20.0.

    Catches: F-Score total not computed correctly for all-fail scenario.
    Ignores: individual signal boundaries (tested via positive case).
    """
    # Note: F9 (asset turnover) passes (rev/ta improved), so F=1 not 0.
    # ≤3 → 20.0 regardless.
    financials = _fin2(
        income0  = {"NetIncome": -50e9, "GrossProfit": 10e9, "TotalRevenue": 200e9},
        income1  = {"NetIncome":  10e9, "GrossProfit": 20e9, "TotalRevenue": 180e9},
        balance0 = {"TotalAssets": 300e9, "LongTermDebt": 200e9,
                    "CurrentAssets": 50e9, "CurrentLiabilities": 100e9,
                    "OrdinarySharesNumber": 20e9},
        balance1 = {"TotalAssets": 350e9, "LongTermDebt": 100e9,
                    "CurrentAssets": 80e9, "CurrentLiabilities": 70e9,
                    "OrdinarySharesNumber": 15e9},
        cashflow0 = {"OperatingCashFlow": -60e9},
        cashflow1 = {"OperatingCashFlow":  30e9},
    )
    assert score_piotroski("AAPL", financials) == pytest.approx(20.0)


def test_piotroski_p5_empty_financials():
    """Empty financials → neutral 50.0 (Lock 1: 0 years < 2).

    Catches: function crashing on empty dict instead of returning neutral.
    Ignores: data with >= 2 years.
    """
    assert score_piotroski("AAPL", {}) == pytest.approx(50.0)


def test_piotroski_partial_one_year_lock1():
    """Only 1 fiscal year available → Lock 1 fires → 50.0.

    Catches: Lock 1 not enforced (function tries change-signals with missing Y1,
             producing wrong score or key error).
    Ignores: two-year scenarios.
    """
    financials = _fin(
        income  = {"NetIncome": 50e9, "TotalRevenue": 200e9, "GrossProfit": 60e9},
        balance = {"TotalAssets": 300e9},
        cashflow= {"OperatingCashFlow": 60e9},
    )
    assert score_piotroski("AAPL", financials) == pytest.approx(50.0)


def test_piotroski_f5_boundary():
    """F=5 → 50.0 boundary tier.

    Catches: off-by-one error between F=5 (neutral) and F=6 (65.0) tiers.
    Ignores: extreme F scores (covered by positive/negative tests).
    """
    # Use same base as positive test but flip 4 signals:
    # Keep F1, F2, F3, F4, F9 passing — block F5, F6, F7, F8.
    financials = _fin2(
        income0  = {"NetIncome": 100e9, "GrossProfit": 80e9,  "TotalRevenue": 400e9},
        income1  = {"NetIncome":  80e9, "GrossProfit": 100e9, "TotalRevenue": 350e9},
        balance0 = {"TotalAssets": 350e9, "LongTermDebt": 200e9,   # F5 fail: leverage up
                    "CurrentAssets": 50e9, "CurrentLiabilities": 200e9,  # F6 fail: CR down
                    "OrdinarySharesNumber": 20e9},                 # F7 fail: diluted
        balance1 = {"TotalAssets": 320e9, "LongTermDebt": 100e9,
                    "CurrentAssets": 120e9, "CurrentLiabilities": 120e9,
                    "OrdinarySharesNumber": 15e9},
        cashflow0 = {"OperatingCashFlow": 110e9},
        cashflow1 = {"OperatingCashFlow":  90e9},
    )
    # F1: 100/350 > 0 ✓; F2: 110>0 ✓; F3: ROA improved ✓; F4: OCF>NI ✓
    # F5: LTD/TA 200/350 > 100/320 ✗; F6: 50/200 < 120/120 ✗; F7: 20>15 ✗
    # F8: GM 80/400=0.20 < 100/350=0.286 ✗; F9: AT 400/350 > 350/320 ✓
    # F = 5 → 50.0
    assert score_piotroski("AAPL", financials) == pytest.approx(50.0)


# ── score_altman_penalty ──────────────────────────────────────────────────────

def _altman_fin(wc, ta, re, ebit, tl, rev, year="2025"):
    """Build minimal financials dict for Altman calculation."""
    return {
        "BALANCE": {year: {
            "WorkingCapital":                    wc,
            "TotalAssets":                       ta,
            "RetainedEarnings":                  re,
            "TotalLiabilitiesNetMinorityInterest": tl,
        }},
        "INCOME":  {year: {
            "EBIT":         ebit,
            "TotalRevenue": rev,
        }},
    }


def test_altman_populated_positive_safe():
    """Z'' >> 2.6 (safe zone) → 0 penalty.

    Catches: safe-zone check missing (returns -10 when Z'' is clearly safe).
    Ignores: boundary at exactly 2.6 (edge test below).
    """
    # X4 = 3000e9/80e9 = 37.5 → Z'' >> 2.6 (Z'' ≈ 43.6)
    fin = _altman_fin(wc=90e9, ta=350e9, re=120e9, ebit=75e9, tl=80e9, rev=400e9)
    assert score_altman_penalty("AAPL", fin, "3000B") == 0


def test_altman_populated_negative_distressed():
    """Z'' < 0.0 → maximum penalty -60 (deep distress tier).

    Catches: deep-distress tier not returning -60. Four-tier penalty model
    preserves Z'' < 0 as the most-severe tier (Z'' [0.0, 1.1) yields only -30).
    Ignores: intermediate zones (covered by grey-zone and distress tests).
    """
    # Z'' ≈ -4.24 → Z'' < 0.0 → -60
    fin = _altman_fin(wc=-50e9, ta=200e9, re=-100e9, ebit=-30e9, tl=300e9, rev=150e9)
    assert score_altman_penalty("AAPL", fin, "10B") == -60


def test_altman_p5_empty_financials():
    """Empty financials → 0 (no penalty, P5 rule).

    Catches: function crashing on empty dict or returning non-zero penalty.
    Ignores: populated cases.
    """
    assert score_altman_penalty("AAPL", {}, "100B") == 0


def test_altman_partial_missing_one_key():
    """One required key absent → all-or-nothing → 0 penalty.

    Catches: partial Altman calculation producing incorrect Z (should return 0).
    Ignores: all-keys-present scenarios.
    """
    fin = _altman_fin(wc=90e9, ta=350e9, re=120e9, ebit=75e9, tl=80e9, rev=400e9)
    # Remove WorkingCapital to trigger all-or-nothing
    del fin["BALANCE"]["2025"]["WorkingCapital"]
    assert score_altman_penalty("AAPL", fin, "3000B") == 0


def test_altman_grey_zone_minus10():
    """1.1 <= Z'' < 2.6 → -10 penalty (grey zone).

    Catches: grey-zone tier missing or returning wrong penalty.
    Ignores: safe and distress zones.

    Note: under classic Z these inputs yielded Z=2.66 (grey); under Z'' the
    same inputs yield Z''=3.917 (safe). Inputs updated for SCORING_ENGINE_VERSION
    0.14.0 to keep grey-zone coverage: tl=200e9 + mc="50B" reduces X4 to 0.25
    and lands Z''=2.0795 squarely inside [1.1, 2.6). rev=160e9 retained as a
    no-op (Z'' does not consume revenue) for fixture-shape stability.
    """
    # X1=0.10, X2=0.15, X3=0.10, X4=0.25 → Z'' ≈ 2.0795
    fin = _altman_fin(wc=20e9, ta=200e9, re=30e9, ebit=20e9, tl=200e9, rev=160e9)
    result = score_altman_penalty("AAPL", fin, "50B")
    assert result == -10


# ── compute_z_raw helper ──────────────────────────────────────────────────────

def test_compute_z_raw_grey_zone_known_value():
    """Synthetic grey-zone inputs produce Z = 2.6600 exactly.

    Same numerical set used by test_altman_grey_zone_minus10 — verifies the
    pure-math helper produces the value the penalty tier relies on. 4-decimal
    tolerance because IEEE 754 sum-of-products may drift in the LSB.

    Catches: formula drift (coefficient typo, ratio inversion).
    Ignores: penalty-tier mapping (tested by score_altman_penalty tests).
    """
    z = compute_z_raw(
        working_capital   = 20e9,
        total_assets      = 200e9,
        retained_earnings = 30e9,
        ebit              = 20e9,
        total_liabilities = 100e9,
        total_revenue     = 160e9,
        market_cap        = 200e9,
    )
    assert z == pytest.approx(2.6600, abs=1e-4)


def test_compute_z_raw_safe_zone_healthy():
    """Healthy inputs produce Z = 18.91 (deep safe zone, well above 3.0).

    Computed by hand: x1=0.5 x2=0.8 x3=0.3 x4=25.0 x5=1.2 →
    Z = 1.2*0.5 + 1.4*0.8 + 3.3*0.3 + 0.6*25.0 + 1.0*1.2 = 18.91.

    Catches: helper returning None or a clipped value for healthy inputs.
    Ignores: where in the safe zone — only that Z >= 3.0.
    """
    z = compute_z_raw(
        working_capital   = 50e9,
        total_assets      = 100e9,
        retained_earnings = 80e9,
        ebit              = 30e9,
        total_liabilities = 20e9,
        total_revenue     = 120e9,
        market_cap        = 500e9,
    )
    assert z == pytest.approx(18.91, abs=1e-4)


def test_compute_z_raw_distress_zone():
    """Distress inputs (0 < Z < 1.8). Expected Z = 0.51017 to 5 d.p.

    Computed: x1=0.025 x2=0.010 x3=0.015 x4=50/180 x5=0.25 →
    Z = 0.03 + 0.014 + 0.0495 + 0.166666... + 0.25 = 0.510166...

    Catches: negative-x4 reflection bug (some Altman impls treat MC/TL with
    abs()); a sign-flipped x4 here would push Z out of [0, 1.8).
    Ignores: penalty magnitude (-30); only the raw Z is asserted.
    """
    z = compute_z_raw(
        working_capital   = 5e9,
        total_assets      = 200e9,
        retained_earnings = 2e9,
        ebit              = 3e9,
        total_liabilities = 180e9,
        total_revenue     = 50e9,
        market_cap        = 50e9,
    )
    assert z == pytest.approx(0.51017, abs=1e-4)
    assert 0.0 <= z < 1.8


def test_compute_z_raw_deep_distress_negative():
    """Deep-distress inputs produce Z = -0.903 (Z < 0 zone).

    Computed: x1=-0.10 x2=-0.25 x3=-0.15 x4=0.02 x5=0.05 →
    Z = -0.12 + -0.35 + -0.495 + 0.012 + 0.05 = -0.903.

    Catches: helper clamping to 0 (it must not — pure math, no clamp).
    Ignores: penalty magnitude (-60).
    """
    z = compute_z_raw(
        working_capital   = -20e9,
        total_assets      = 200e9,
        retained_earnings = -50e9,
        ebit              = -30e9,
        total_liabilities = 250e9,
        total_revenue     = 10e9,
        market_cap        = 5e9,
    )
    assert z == pytest.approx(-0.903, abs=1e-4)
    assert z < 0.0


_ALTMAN_VALID_INPUTS = {
    "working_capital":   20e9,
    "total_assets":      200e9,
    "retained_earnings": 30e9,
    "ebit":              20e9,
    "total_liabilities": 100e9,
    "total_revenue":     160e9,
    "market_cap":        200e9,
}


@pytest.mark.parametrize("missing_key", list(_ALTMAN_VALID_INPUTS.keys()))
def test_compute_z_raw_none_when_input_missing(missing_key):
    """Any single None input → return None (all-or-nothing semantic).

    Catches: helper silently substituting 0 for None on any input. Substituted
    zero would yield a wrong Z (e.g. None for market_cap → x4=0 → Z low and
    wrongly distress-coded).
    Ignores: which input is missing — the contract is binary, not per-input.
    """
    inputs = dict(_ALTMAN_VALID_INPUTS)
    inputs[missing_key] = None
    assert compute_z_raw(**inputs) is None


def test_compute_z_raw_none_when_total_assets_zero():
    """total_assets = 0 → return None (zero denominator would explode).

    Catches: division-by-zero raised instead of None returned.
    Ignores: other inputs being None (covered by parametrized test above).
    """
    inputs = dict(_ALTMAN_VALID_INPUTS)
    inputs["total_assets"] = 0
    assert compute_z_raw(**inputs) is None


def test_compute_z_raw_none_when_total_liabilities_zero():
    """total_liabilities = 0 → return None (x4 denominator is zero).

    Catches: division-by-zero raised instead of None returned.
    Ignores: other inputs being None (covered by parametrized test above).
    """
    inputs = dict(_ALTMAN_VALID_INPUTS)
    inputs["total_liabilities"] = 0
    assert compute_z_raw(**inputs) is None


def test_compute_z_raw_kwargs_only_enforced():
    """compute_z_raw() rejects positional args via the `*,` separator.

    Catches: drift to positional signature, which would silently accept
    argument-swap (e.g. swap working_capital and total_assets) and produce
    plausible-but-wrong Z values at scale.
    Ignores: keyword-arg behaviour (covered by every other test in this set).
    """
    with pytest.raises(TypeError):
        compute_z_raw(20e9, 200e9, 30e9, 20e9, 100e9, 160e9, 200e9)


# ── compute_z_double_prime_raw helper ─────────────────────────────────────────

def test_compute_z_double_prime_grey_zone_known_value():
    """Same inputs as classic-Z grey-zone test → Z'' = 3.917 (safe under Z'').

    Hand-computed: x1=0.10 x2=0.15 x3=0.10 x4=2.00 →
    Z'' = 6.56*0.10 + 3.26*0.15 + 6.72*0.10 + 1.05*2.00
        = 0.656 + 0.489 + 0.672 + 2.10
        = 3.917.

    Note: the SAME numerical input set that yields classic Z = 2.66 (grey)
    yields Z'' = 3.917 (safe). This illustrates that Z'' is more forgiving
    than classic Z for the same firm — the empirical justification for the
    Phase 2c calibration switch.

    Catches: coefficient typo, ratio inversion, X5 accidentally included.
    Ignores: bin mapping (no penalty logic in this helper).
    """
    z = compute_z_double_prime_raw(
        working_capital   = 20e9,
        total_assets      = 200e9,
        retained_earnings = 30e9,
        ebit              = 20e9,
        total_liabilities = 100e9,
        market_cap        = 200e9,
    )
    assert z == pytest.approx(3.917, abs=1e-4)


def test_compute_z_double_prime_safe_zone():
    """Healthy inputs produce Z'' = 34.154 (deep safe zone).

    Hand-computed: x1=0.5 x2=0.8 x3=0.3 x4=25.0 →
    Z'' = 6.56*0.5 + 3.26*0.8 + 6.72*0.3 + 1.05*25.0
        = 3.28 + 2.608 + 2.016 + 26.25
        = 34.154.

    Catches: helper returning None or clipped value for healthy inputs.
    Ignores: where in the safe zone — only that Z'' >= 2.6.
    """
    z = compute_z_double_prime_raw(
        working_capital   = 50e9,
        total_assets      = 100e9,
        retained_earnings = 80e9,
        ebit              = 30e9,
        total_liabilities = 20e9,
        market_cap        = 500e9,
    )
    assert z == pytest.approx(34.154, abs=1e-4)
    assert z >= 2.6


def test_compute_z_double_prime_distress_zone():
    """Distress inputs produce Z'' < 1.1 (Z'' distress zone).

    Hand-computed: x1=0.025 x2=0.010 x3=0.015 x4=50/180≈0.2778 →
    Z'' = 6.56*0.025 + 3.26*0.010 + 6.72*0.015 + 1.05*0.27777...
        = 0.164 + 0.0326 + 0.1008 + 0.291666...
        ≈ 0.589066.

    Catches: negative-x4 reflection bug; coefficient swap with classic Z.
    Ignores: penalty magnitude (Phase 2d scope).
    """
    z = compute_z_double_prime_raw(
        working_capital   = 5e9,
        total_assets      = 200e9,
        retained_earnings = 2e9,
        ebit              = 3e9,
        total_liabilities = 180e9,
        market_cap        = 50e9,
    )
    assert z == pytest.approx(0.58907, abs=1e-4)
    assert z < 1.1


_ALTMAN_DOUBLE_PRIME_VALID_INPUTS = {
    "working_capital":   20e9,
    "total_assets":      200e9,
    "retained_earnings": 30e9,
    "ebit":              20e9,
    "total_liabilities": 100e9,
    "market_cap":        200e9,
}


@pytest.mark.parametrize("missing_key", list(_ALTMAN_DOUBLE_PRIME_VALID_INPUTS.keys()))
def test_compute_z_double_prime_none_when_input_missing(missing_key):
    """Any single None input → return None (all-or-nothing semantic).

    Catches: helper silently substituting 0 for None on any of the 6 inputs.
    Ignores: which input is missing — the contract is binary.
    """
    inputs = dict(_ALTMAN_DOUBLE_PRIME_VALID_INPUTS)
    inputs[missing_key] = None
    assert compute_z_double_prime_raw(**inputs) is None


@pytest.mark.parametrize("zero_key", ["total_assets", "total_liabilities"])
def test_compute_z_double_prime_none_when_zero_denominator(zero_key):
    """total_assets=0 or total_liabilities=0 → return None (would divide by zero).

    Catches: ZeroDivisionError raised instead of None returned.
    Ignores: other inputs (covered by missing-input parametrization).
    """
    inputs = dict(_ALTMAN_DOUBLE_PRIME_VALID_INPUTS)
    inputs[zero_key] = 0
    assert compute_z_double_prime_raw(**inputs) is None


def test_compute_z_double_prime_kwargs_only_enforced():
    """compute_z_double_prime_raw() rejects positional args via `*,` separator.

    Catches: drift to positional signature, which would silently accept
    argument-swap (e.g. wc↔ta) and produce plausible-but-wrong Z'' values.
    Ignores: keyword-arg behaviour (covered by every other test in this set).
    """
    with pytest.raises(TypeError):
        compute_z_double_prime_raw(20e9, 200e9, 30e9, 20e9, 100e9, 200e9)


# ── score_inst_ownership ──────────────────────────────────────────────────────

def test_inst_own_populated_positive():
    """pct >= 48 → v0.15.0 top quartile → 75.0.

    v0.15.0 (175bbf7): quartile-anchored cuts on the real top-10-SUM
    distribution (p25=12.4, p50=34.4, p75=48.3) replace the original
    60/40/20 ladder. pct=65 lands in the top tier (>= 48).

    Catches: top-tier threshold drifting off the 48 cut (e.g. reverting
    to >= 60 or >= 80).
    Ignores: lower pct tiers.
    """
    assert score_inst_ownership("AAPL", {"total_pct_held": 65.0}) == pytest.approx(75.0)


def test_inst_own_populated_negative():
    """pct < 12 → v0.15.0 bottom quartile → 30.0.

    v0.15.0 (175bbf7): bottom-quartile floor lowered from the previous
    35.0 to 30.0 to widen separation between bottom (< p25=12.4) and
    the next-up tier. pct=10 lands in the bottom bucket.

    Catches: bottom tier reverting to the old 35.0 floor, or the
    p25=12 threshold drifting.
    Ignores: mid-range tiers.
    """
    assert score_inst_ownership("AAPL", {"total_pct_held": 10.0}) == pytest.approx(30.0)


def test_inst_own_p5_none():
    """inst_data is None → neutral 50.0.

    Catches: P5 branch missing (crashes or returns non-neutral).
    Ignores: populated cases.
    """
    assert score_inst_ownership("AAPL", None) == pytest.approx(50.0)


def test_inst_own_partial_pct_null():
    """total_pct_held is None (dict present but key missing) → neutral 50.0.

    Catches: KeyError or wrong default when pct key is absent.
    Ignores: None inst_data (separate P5 test).
    """
    assert score_inst_ownership("AAPL", {"holder_count": 5}) == pytest.approx(50.0)


def test_inst_own_implausible_sum_neutral():
    """pct > 100 → v0.15.0 data-quality guard → neutral 50.0.

    Renamed from test_inst_own_pct_capped_at_100. v0.15.0 (175bbf7)
    replaced the pre-recalibration cap-at-100 behaviour with an explicit
    data-quality guard: yfinance's pctHeld is not consistently normalised
    to total-shares-outstanding for ~0.85% of the universe (~51 tickers
    as of the 21 May 2026 re-scrape, max observed SUM=522.51 for DUOT).
    Per-ticker SUM exceeding 100% is source-data noise, not a real signal
    — route to neutral 50.0 rather than tier-scoring a phantom top tier.

    Catches: the >100 → 50.0 guard being removed, which would re-introduce
    phantom top-tier scoring for tickers with broken yfinance pctHeld
    normalisation.
    Ignores: normal pct values (covered by other tier tests).
    """
    assert score_inst_ownership("AAPL", {"total_pct_held": 115.0}) == pytest.approx(50.0)


# ── score_analyst_momentum ────────────────────────────────────────────────────

def test_analyst_mom_populated_positive():
    """net >= 3 → 80.0.

    Catches: top-tier threshold wrong (e.g. requires >= 4).
    Ignores: lower net values.
    """
    assert score_analyst_momentum("AAPL", {"net_momentum": 4}) == pytest.approx(80.0)


def test_analyst_mom_populated_negative():
    """net <= -3 → 20.0.

    Catches: bottom-tier threshold wrong.
    Ignores: mid-range net values.
    """
    assert score_analyst_momentum("AAPL", {"net_momentum": -5}) == pytest.approx(20.0)


def test_analyst_mom_p5_none():
    """mom_data is None → neutral 50.0.

    Catches: P5 branch missing.
    Ignores: populated cases.
    """
    assert score_analyst_momentum("AAPL", None) == pytest.approx(50.0)


def test_analyst_mom_neutral_zero():
    """net = 0 → exactly neutral 50.0.

    Catches: net=0 routed to wrong tier (off-by-one in ladder).
    Ignores: non-zero net values.
    """
    assert score_analyst_momentum("AAPL", {"net_momentum": 0}) == pytest.approx(50.0)


def test_analyst_mom_net_positive_1():
    """net = 1 → 60.0 (one-upgrade net positive).

    Catches: single-upgrade net not distinguishing from neutral.
    Ignores: stronger positive signals.
    """
    assert score_analyst_momentum("AAPL", {"net_momentum": 1}) == pytest.approx(60.0)
