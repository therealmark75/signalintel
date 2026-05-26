"""
User tier definitions — single source of truth for all feature limits.
All gated features reference this file; never hardcode numeric limits.

Launch model (paywall arc, locked decisions):
  - 'free'  : UNPAID FLOOR. No gateable access. Watchlist limit = 0.
              Post-trial state and the hard-paywall floor. The 7-day
              trial is an *overlay* (see config/entitlements.py), not a
              tier — a trialist's stored users.tier is 'free' while the
              overlay grants elite-equivalent access.
  - 'pro'   : Full signals, alerts, tournaments. Watchlist cap = 5.
  - 'elite' : Pro + API access + unlimited watchlists + penny signals.

Invariant: 'starter' is a dead tier. Any legacy 'starter' value in the
DB column coerces to 'free' via get_tier()'s default branch — no
special-case, the unknown-key fallback handles it.
"""

USER_TIERS = {
    'free': {
        'display_name':    'Free',
        'description':     'Unpaid floor — paywall in effect',
        'watchlist_limit': 0,
        'order':           0,
    },
    'pro': {
        'display_name':    'Pro',
        'description':     'Full signals, alerts, tournaments',
        'watchlist_limit': 5,
        'order':           1,
    },
    'elite': {
        'display_name':    'Elite',
        'description':     'Everything plus API, unlimited watchlists, penny signals',
        'watchlist_limit': None,  # None = unlimited
        'order':           2,
    },
}


def get_tier(tier_key: str) -> dict:
    """Return tier config, defaulting to 'free' if key is invalid or None.

    Legacy 'starter' resolves to 'free' here via the default branch.
    """
    return USER_TIERS.get(tier_key or 'free', USER_TIERS['free'])


def watchlist_limit(tier_key: str):
    """Return watchlist limit for a tier. None = unlimited. 0 = no access."""
    return get_tier(tier_key)['watchlist_limit']


def can_create_watchlist(tier_key: str, current_count: int) -> bool:
    """True if the tier can create another watchlist at the given count.

    'free' returns False at every count (limit=0 = unpaid floor).
    Grandfather rule for over-cap users is handled at the route layer;
    this predicate stays a pure capacity check.
    """
    limit = watchlist_limit(tier_key)
    if limit is None:
        return True
    return current_count < limit


def next_tier(tier_key: str):
    """Return the key of the next tier above this one, or None if at max.

    Walks USER_TIERS by 'order'. After the starter removal:
      next_tier('free')  == 'pro'
      next_tier('pro')   == 'elite'
      next_tier('elite') is None
    """
    current_order = get_tier(tier_key).get('order', 0)
    for key, cfg in USER_TIERS.items():
        if cfg['order'] == current_order + 1:
            return key
    return None
