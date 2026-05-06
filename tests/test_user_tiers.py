"""
Tests for config/tiers.py tier system.

P15 notes (where applicable):
  These tests exercise pure functions — no template pattern matching involved.
"""
import pytest
from config.tiers import (
    USER_TIERS, get_tier, watchlist_limit, can_create_watchlist
)


def test_all_four_tiers_present():
    assert set(USER_TIERS.keys()) == {'free', 'starter', 'pro', 'elite'}


def test_tier_order_is_ascending():
    orders = [USER_TIERS[k]['order'] for k in ('free', 'starter', 'pro', 'elite')]
    assert orders == sorted(orders)
    assert len(set(orders)) == len(orders), "tier orders must be unique"


def test_watchlist_limits():
    assert watchlist_limit('free') == 2
    assert watchlist_limit('starter') == 5
    assert watchlist_limit('pro') == 20
    assert watchlist_limit('elite') is None


def test_get_tier_defaults_to_free_on_invalid_key():
    assert get_tier('nonsense')['watchlist_limit'] == 2
    assert get_tier(None)['watchlist_limit'] == 2
    assert get_tier('')['watchlist_limit'] == 2


def test_can_create_watchlist_free():
    assert can_create_watchlist('free', 0) is True
    assert can_create_watchlist('free', 1) is True
    assert can_create_watchlist('free', 2) is False


def test_can_create_watchlist_starter():
    assert can_create_watchlist('starter', 4) is True
    assert can_create_watchlist('starter', 5) is False


def test_can_create_watchlist_pro():
    assert can_create_watchlist('pro', 19) is True
    assert can_create_watchlist('pro', 20) is False


def test_can_create_watchlist_elite_unlimited():
    for n in (0, 20, 100, 1000):
        assert can_create_watchlist('elite', n) is True


def test_display_names_non_empty():
    for key, tier in USER_TIERS.items():
        assert tier['display_name'], f"'{key}' has empty display_name"
