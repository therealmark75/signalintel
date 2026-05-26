"""
Tests for config/entitlements.py — capability predicates + trial overlay.

P15 throughout: every test asserts the grant AND the silence (denials).
Time injection uses monkeypatch on entitlements._now() so the
day-6 / day-8 boundary tests don't depend on wall-clock drift.
"""
import pytest
from datetime import datetime, timedelta
from config import entitlements
from config.entitlements import (
    effective_tier,
    trial_active,
    can_view_penny_signals,
    can_view_score_for_ticker,
    can_create_watchlist,
    can_use_alerts,
    can_enter_tournament,
    can_call_api,
    TRIAL_DAYS,
)


# Fixed "now" pinned across time-sensitive tests. Date chosen to avoid
# DST edges and to keep ISO formatting clean.
FIXED_NOW = datetime(2026, 5, 26, 12, 0, 0)


@pytest.fixture
def now(monkeypatch):
    """Pin entitlements._now() to FIXED_NOW for deterministic trial math.

    Catches: wall-clock drift causing the day-6 / day-8 boundary tests
             to flap.
    Ignores: timezone offsets — FIXED_NOW is naive UTC same as _now().
    """
    monkeypatch.setattr(entitlements, '_now', lambda: FIXED_NOW)
    return FIXED_NOW


def _trial_ts(now_dt, days_ago):
    """Build an ISO trial_started_at value as `days_ago` days before now_dt."""
    return (now_dt - timedelta(days=days_ago)).isoformat()


# ── effective_tier resolver ────────────────────────────────────────


def test_effective_tier_free_no_trial(now):
    """Stored 'free', no trial → 'free' (the unpaid floor)."""
    user = {'tier': 'free'}
    assert effective_tier(user) == 'free'


def test_effective_tier_free_trial_day_6(now):
    """Stored 'free', trial 6 days old → 'elite' (within 7-day window).

    Catches: overlay accidentally lifting before day 7.
    """
    user = {'tier': 'free', 'trial_started_at': _trial_ts(now, 6)}
    assert effective_tier(user) == 'elite'


def test_effective_tier_free_trial_day_8(now):
    """Stored 'free', trial 8 days old → 'free' (overlay lifted at access time).

    Catches: trial silently extending past the 7-day window — the
             hard-paywall floor must close automatically with no
             cron dependency.
    """
    user = {'tier': 'free', 'trial_started_at': _trial_ts(now, 8)}
    assert effective_tier(user) == 'free'


def test_effective_tier_pro_trial_day_3_higher_rank(now):
    """Stored 'pro', trial 3 days old → 'elite'.

    Catches: higher-rank rule regressing — a paid Pro user mid-trial
             must see elite during the window, not their paid floor.
    """
    user = {'tier': 'pro', 'trial_started_at': _trial_ts(now, 3)}
    assert effective_tier(user) == 'elite'


def test_effective_tier_pro_trial_expired(now):
    """Stored 'pro', trial expired → 'pro'. Post-trial falls to PAID
    floor, not 'free' — a paying user keeps what they paid for.

    Catches: expiry path accidentally dropping a paid user to 'free'.
    """
    user = {'tier': 'pro', 'trial_started_at': _trial_ts(now, 10)}
    assert effective_tier(user) == 'pro'


def test_effective_tier_elite_no_trial(now):
    """Stored 'elite', no trial → 'elite'."""
    user = {'tier': 'elite'}
    assert effective_tier(user) == 'elite'


def test_effective_tier_elite_trial_day_3(now):
    """Stored 'elite', trial 3 days old → 'elite'.

    Exercises the equality branch in the rank compare (line 110:
    `_tier_rank(trial_grant) >= _tier_rank(stored)` with both ranks = 2).

    Honesty caveat: in THIS specific case the >= vs > distinction is
    invisible — trial_grant is hardcoded to 'elite' and stored is
    also 'elite', so BOTH branches of the if/else return 'elite'.
    A naive >=→> rewrite would not flip this test.

    Catches: an elite user mid-trial regressing below elite (e.g. if
             a future change made the trial-grant branch return
             trial_grant only when STRICTLY higher than stored, an
             elite+trial user would unexpectedly fall to stored — but
             stored here is also elite, so the outcome is the same).
             More usefully it catches a future bug where the resolver
             accidentally downgrades an elite user during a trial
             (e.g. overlay logic flipped).
    Ignores: the >= vs > distinction — that would only be observable
             with a non-elite trial_grant, which doesn't exist today.
    """
    user = {'tier': 'elite', 'trial_started_at': _trial_ts(now, 3)}
    assert effective_tier(user) == 'elite'


def test_effective_tier_user_none_fails_closed(now):
    """user=None → 'free'. Fail-closed against anonymous calls."""
    assert effective_tier(None) == 'free'


def test_effective_tier_non_dict_fails_closed(now):
    """user='not-a-dict' → 'free'. Defensive against caller bugs."""
    assert effective_tier('not-a-dict') == 'free'


def test_effective_tier_unknown_stored_tier_coerces_to_free(now):
    """Legacy 'starter' or any unknown stored tier → 'free'
    (matches config/tiers.get_tier semantics)."""
    user = {'tier': 'starter'}
    assert effective_tier(user) == 'free'


# ── trial_active ──────────────────────────────────────────────────


def test_trial_active_none_fails_closed(now):
    """trial_started_at=None → False. Fail-closed: no value, no grant."""
    user = {'tier': 'free', 'trial_started_at': None}
    assert trial_active(user) is False


def test_trial_active_missing_field_fails_closed(now):
    """trial_started_at field absent → False."""
    user = {'tier': 'free'}
    assert trial_active(user) is False


def test_trial_active_malformed_timestamp_fails_closed(now):
    """trial_started_at='not-a-date' → False. Fail-closed: unparseable
    must not silently grant access."""
    user = {'tier': 'free', 'trial_started_at': 'not-a-date'}
    assert trial_active(user) is False


def test_trial_active_empty_string_fails_closed(now):
    """trial_started_at='' → False."""
    user = {'tier': 'free', 'trial_started_at': ''}
    assert trial_active(user) is False


def test_trial_active_non_string_timestamp_fails_closed(now):
    """trial_started_at=12345 (wrong type) → False."""
    user = {'tier': 'free', 'trial_started_at': 12345}
    assert trial_active(user) is False


def test_trial_active_day_6_true(now):
    """Trial 6 days old → True (within 7-day window)."""
    user = {'tier': 'free', 'trial_started_at': _trial_ts(now, 6)}
    assert trial_active(user) is True


def test_trial_active_day_8_false(now):
    """Trial 8 days old → False. The boundary closed at day 7."""
    user = {'tier': 'free', 'trial_started_at': _trial_ts(now, 8)}
    assert trial_active(user) is False


def test_trial_active_iso_with_z_suffix(now):
    """ISO timestamp ending with 'Z' (UTC) parses correctly."""
    ts_utc = (now - timedelta(days=3)).isoformat() + 'Z'
    user = {'tier': 'free', 'trial_started_at': ts_utc}
    assert trial_active(user) is True


# ── Predicate matrix: free / pro / elite × each capability ────────


def test_can_view_penny_signals_matrix():
    """Penny signals: elite only.

    P15 silence: free AND pro denied — exactly one tier passes.
    """
    assert can_view_penny_signals('free') is False
    assert can_view_penny_signals('pro') is False
    assert can_view_penny_signals('elite') is True


def test_can_use_alerts_matrix():
    """Alerts: pro or elite.

    P15 silence: free denied — paid floor only.
    """
    assert can_use_alerts('free') is False
    assert can_use_alerts('pro') is True
    assert can_use_alerts('elite') is True


def test_can_enter_tournament_matrix():
    """Tournaments: pro or elite (acquisition hook).

    P15 silence: free denied; deliberately NOT elite-exclusive.
    """
    assert can_enter_tournament('free') is False
    assert can_enter_tournament('pro') is True
    assert can_enter_tournament('elite') is True


def test_can_call_api_matrix():
    """API: elite only.

    P15 silence: free AND pro denied — Elite hook.
    """
    assert can_call_api('free') is False
    assert can_call_api('pro') is False
    assert can_call_api('elite') is True


# ── $5 boundary: can_view_score_for_ticker — both sides × every tier


def test_can_view_score_for_ticker_penny_band():
    """price=2 (penny band, $1-5): elite only.

    Catches: free or pro accidentally seeing penny scores.
    """
    assert can_view_score_for_ticker('free', 2.0) is False
    assert can_view_score_for_ticker('pro', 2.0) is False
    assert can_view_score_for_ticker('elite', 2.0) is True


def test_can_view_score_for_ticker_above_five():
    """price=10 (above $5): pro or elite.

    Catches: free seeing non-penny scores.
    """
    assert can_view_score_for_ticker('free', 10.0) is False
    assert can_view_score_for_ticker('pro', 10.0) is True
    assert can_view_score_for_ticker('elite', 10.0) is True


def test_can_view_score_for_ticker_boundary_at_five():
    """price=5 exactly: pro or elite (boundary is strict < 5).

    Catches: off-by-one — $5 is NOT in the penny band.
    """
    assert can_view_score_for_ticker('free', 5.0) is False
    assert can_view_score_for_ticker('pro', 5.0) is True
    assert can_view_score_for_ticker('elite', 5.0) is True


def test_can_view_score_for_ticker_none_price_fails_closed():
    """price=None → fail closed to penny-band rule (elite only).

    Catches: an unknown price silently defaulting to the more
             permissive gate.
    """
    assert can_view_score_for_ticker('free', None) is False
    assert can_view_score_for_ticker('pro', None) is False
    assert can_view_score_for_ticker('elite', None) is True


# ── can_create_watchlist — delegation contract ────────────────────


def test_can_create_watchlist_delegates_to_tiers():
    """entitlements.can_create_watchlist must produce the same answer
    as config/tiers.py for the same inputs across the full matrix.

    Catches: a parallel cap table sneaking into entitlements.py.
    """
    from config.tiers import can_create_watchlist as _tiers_cap
    for tier in ('free', 'pro', 'elite'):
        for n in (0, 1, 4, 5, 100):
            assert can_create_watchlist(tier, n) == _tiers_cap(tier, n), \
                f"divergence at tier={tier} count={n}"


# ── Trial-length constant: catch silent drift ─────────────────────


def test_trial_days_locked_at_seven():
    """TRIAL_DAYS must be 7 — locked decision.

    Catches: silent bump of the trial window length without
             a deliberate decision.
    """
    assert TRIAL_DAYS == 7
