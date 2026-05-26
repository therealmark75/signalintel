"""
Tests for config/tiers.py tier system (paywall-arc launch model).

P15 notes (where applicable):
  These tests exercise pure functions — no template pattern matching involved.
  Catches: drift from the locked 2-tier+floor model (free / pro / elite).
  Ignores: tier display copy and tier description wording.
"""
import pytest
from config.tiers import (
    USER_TIERS, get_tier, watchlist_limit, can_create_watchlist, next_tier
)


def test_only_three_tier_keys_present():
    """
    Launch model = two paid tiers plus an unpaid floor.

    Catches: silent reintroduction of 'starter' or any other tier key.
    Ignores: order field renumbering as long as it stays ascending.
    """
    assert set(USER_TIERS.keys()) == {'free', 'pro', 'elite'}


def test_tier_order_is_ascending():
    """
    Catches: order collision between tiers (would break next_tier()).
    Ignores: absolute order values, only the ascending invariant matters.
    """
    orders = [USER_TIERS[k]['order'] for k in ('free', 'pro', 'elite')]
    assert orders == sorted(orders)
    assert len(set(orders)) == len(orders), "tier orders must be unique"


def test_watchlist_limits_locked():
    """
    Catches: cap drift on any tier — free=0 (no access), pro=5, elite=unlimited.
    Ignores: changes to other limit fields if added later.
    """
    assert watchlist_limit('free') == 0
    assert watchlist_limit('pro') == 5
    assert watchlist_limit('elite') is None


def test_get_tier_defaults_to_free_on_invalid_key():
    """
    Catches: invalid tier key silently granting paid-tier limits.
    Ignores: the exact display_name returned for the default.
    """
    assert get_tier('nonsense')['watchlist_limit'] == 0
    assert get_tier(None)['watchlist_limit'] == 0
    assert get_tier('')['watchlist_limit'] == 0


def test_free_grants_no_watchlists():
    """
    P15 silence assertion: 'free' is the unpaid floor — no gateable access.
    A free user CANNOT create a watchlist at any count, ever.

    Catches: regression where free tier accidentally gains a non-zero cap.
    Ignores: how the rejection is surfaced upstream (403/redirect/etc.).
    """
    for n in (0, 1, 5, 100):
        assert can_create_watchlist('free', n) is False


def test_can_create_watchlist_pro():
    """
    Catches: Pro cap drift away from 5 (locked at launch).
    Ignores: how the route surfaces the over-cap rejection.
    """
    assert can_create_watchlist('pro', 0) is True
    assert can_create_watchlist('pro', 4) is True
    assert can_create_watchlist('pro', 5) is False


def test_can_create_watchlist_elite_unlimited():
    """
    Catches: elite tier ever picking up a finite cap.
    Ignores: practical limits enforced elsewhere (DB row-count, etc.).
    """
    for n in (0, 5, 100, 1000):
        assert can_create_watchlist('elite', n) is True


def test_starter_is_dead():
    """
    P15 silence assertion: 'starter' is no longer a usable tier. A stored
    column carrying 'starter' (legacy data) must coerce to the unpaid
    floor via get_tier()'s default branch — same as any other unknown key.

    Catches: someone reintroducing 'starter' to USER_TIERS, or get_tier
             special-casing the legacy string into a paid tier.
    Ignores: how legacy starter rows are migrated (DB cleanup is separate).
    """
    assert 'starter' not in USER_TIERS
    assert get_tier('starter')['watchlist_limit'] == 0
    assert can_create_watchlist('starter', 0) is False


def test_next_tier_walks_free_pro_elite():
    """
    Catches: starter accidentally reinserted as an intermediate order step.
    Ignores: the absolute order values, only the walk sequence matters.
    """
    assert next_tier('free') == 'pro'
    assert next_tier('pro') == 'elite'
    assert next_tier('elite') is None


def test_display_names_non_empty():
    """
    Catches: tier definition stub forgotten before ship.
    Ignores: the actual copy of the display_name string.
    """
    for key, tier in USER_TIERS.items():
        assert tier['display_name'], f"'{key}' has empty display_name"
