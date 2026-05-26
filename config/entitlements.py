"""
Capability predicates and the trial-overlay resolver — the single
authoritative entitlements surface every gate downstream reads from.

LOCKED DECISIONS (paywall arc):
  - 'free'  : unpaid floor, no gated access
  - 'pro'   : full signals, alerts, tournaments, watchlists cap=5
  - 'elite' : pro + API + unlimited watchlists + penny signals
  - 7-day trial is an *overlay*. During the window, effective_tier
    returns 'elite' regardless of stored tier. Stored 'tier' column
    holds the post-trial floor — 'free' for an unpaid trialist; 'pro'
    or 'elite' for a paying user.

INVARIANT: every predicate consumes effective_tier(user) output, never
user['tier'] raw. The raw column is the post-trial floor only — using
it would skip the overlay and lock trial users out of paid features.

NO Flask coupling here. Pure functions. The route decorator that wraps
these lands in Step 3, not here.
"""
from datetime import datetime, timedelta, timezone
from config.tiers import (
    USER_TIERS,
    can_create_watchlist as _tiers_can_create_watchlist,
)


# Trial length is single-owned here so the gate, the Stripe webhook
# (Step 2+), and the day-8 expiry detection all read the same constant.
TRIAL_DAYS = 7


def _now():
    """Indirection point for time injection in tests. Returns naive UTC.

    Tests monkeypatch this to a fixed datetime for deterministic
    day-6 / day-8 boundary checks. Production callers never replace it.
    """
    return datetime.utcnow()


def _parse_trial_start(ts_str):
    """Parse a stored trial_started_at TEXT value into naive UTC datetime.

    Fail-closed: returns None on missing / non-string / empty /
    malformed input. An unparseable timestamp MUST NOT silently grant
    access; the caller (trial_active) treats None as 'no trial'.
    """
    if not ts_str or not isinstance(ts_str, str):
        return None
    try:
        s = ts_str.replace('Z', '+00:00') if ts_str.endswith('Z') else ts_str
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except (ValueError, TypeError):
        return None


def trial_active(user):
    """True iff user has a valid trial_started_at within the trial window.

    Fail-closed semantics — every one of these returns False:
      - user is None / falsy / not a dict
      - trial_started_at missing / None / empty
      - trial_started_at malformed (not parseable as ISO)
      - trial_started_at parses but (_now - then) >= TRIAL_DAYS
    """
    if not isinstance(user, dict):
        return False
    parsed = _parse_trial_start(user.get('trial_started_at'))
    if parsed is None:
        return False
    return (_now() - parsed) < timedelta(days=TRIAL_DAYS)


def _tier_rank(tier_key):
    """Read rank from config/tiers.py USER_TIERS[...]['order'] — single source.

    Unknown / invalid keys resolve to free's rank. DO NOT add a
    parallel rank table to this module; that would let entitlements
    and tiers drift.
    """
    return USER_TIERS.get(tier_key, USER_TIERS['free'])['order']


def effective_tier(user):
    """Resolve the user's *effective* tier accounting for the trial overlay.

    Logic:
      stored      = user['tier'] coerced via get_tier semantics
                    (unknown / missing / non-dict → 'free')
      trial_grant = 'elite' if trial_active(user) else None
      return        the HIGHER-RANK of (stored, trial_grant) by USER_TIERS order

    During an active trial window the user always sees 'elite' (top rank).
    Post-trial, falls back to stored — a paid Pro user falls to 'pro',
    not 'free'; an unpaid trialist falls to 'free' (the hard paywall floor).

    user=None or non-dict → 'free' (fail closed).
    """
    if not isinstance(user, dict):
        return 'free'
    raw = user.get('tier')
    stored = raw if raw in USER_TIERS else 'free'

    trial_grant = 'elite' if trial_active(user) else None
    if trial_grant is None:
        return stored
    if _tier_rank(trial_grant) >= _tier_rank(stored):
        return trial_grant
    return stored


# ── Capability predicates ──────────────────────────────────────────
#
# Every predicate below takes a `tier` argument that the caller MUST
# obtain from effective_tier(user). NEVER pass user['tier'] raw — the
# raw column is the post-trial floor only and skips the overlay.


def can_view_penny_signals(tier):
    """Elite only — the $1-5 score/rating panel is the Elite hook.

    `tier` MUST be effective_tier(user), never user['tier'] raw.
    """
    return tier == 'elite'


def can_view_score_for_ticker(tier, price):
    """Score/rating panel visibility, price-aware.

    The $5 boundary lives HERE and nowhere else.
      - price < 5  (penny band, $1-5)  → elite only
      - price >= 5                      → pro or elite
      - price is None                   → fail closed (elite only)
    Free is always denied (it's the unpaid floor).

    `tier` MUST be effective_tier(user), never user['tier'] raw.
    """
    if price is None:
        return tier == 'elite'
    if price < 5:
        return tier == 'elite'
    return tier in ('pro', 'elite')


def can_create_watchlist(tier, current_count):
    """Watchlist creation cap.

    Delegates to config/tiers.py so the cap numbers (free=0, pro=5,
    elite=None) stay single-owned there. This function exists so
    callers see one entitlements surface, not because the math lives here.

    `tier` MUST be effective_tier(user), never user['tier'] raw.
    """
    return _tiers_can_create_watchlist(tier, current_count)


def can_use_alerts(tier):
    """Telegram / email alert dispatch. Pro or elite.

    `tier` MUST be effective_tier(user), never user['tier'] raw.
    """
    return tier in ('pro', 'elite')


def can_enter_tournament(tier):
    """Monthly tournament entry. Pro or elite — deliberately NOT
    Elite-exclusive (acquisition hook, per locked decisions).

    `tier` MUST be effective_tier(user), never user['tier'] raw.
    """
    return tier in ('pro', 'elite')


def can_call_api(tier):
    """API endpoints (read + write). Elite only.

    `tier` MUST be effective_tier(user), never user['tier'] raw.
    """
    return tier == 'elite'
