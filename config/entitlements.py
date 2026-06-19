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


def _parse_utc_iso(ts_str):
    """Parse a stored ISO TEXT timestamp into a naive UTC datetime.

    Generic helper shared by trial_active (reads trial_started_at) and
    effective_tier (reads tier_effective_until). Both columns are
    written as naive UTC ISO strings by their respective producers;
    parsing is uniform.

    Fail-closed: returns None on missing / non-string / empty /
    malformed input. An unparseable timestamp MUST NOT silently grant
    access; callers treat None as the absent-or-invalid case (no
    trial active, no expiry pending).
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
    parsed = _parse_utc_iso(user.get('trial_started_at'))
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
    """Resolve the user's *effective* tier accounting for trial overlay
    and lazy tier_effective_until expiry.

    Logic, in order:
      stored      = user['tier'] coerced via USER_TIERS membership
                    (unknown / missing / non-dict -> 'free')
      EXPIRY      if user['tier_effective_until'] parses to a past
                  datetime, demote stored to 'free' (lazy expiry).
                  Missing / None / unparseable: no demotion.
      trial_grant = 'elite' if trial_active(user) else None
      return        the HIGHER-RANK of (stored, trial_grant) by USER_TIERS order

    During an active trial window the user always sees 'elite' (top
    rank) regardless of expiry. Post-trial, falls back to stored, with
    expired paid subs collapsed to 'free' by the lazy check above.

    user=None or non-dict -> 'free' (fail closed).
    """
    if not isinstance(user, dict):
        return 'free'
    raw = user.get('tier')
    stored = raw if raw in USER_TIERS else 'free'

    # Lazy tier_effective_until expiry: if the stored paid floor has a
    # PRESENT, PARSEABLE timestamp in the PAST, the floor collapses to
    # 'free'. Applied to the stored floor BEFORE the trial overlay, so
    # a trialist whose paid sub has elapsed still sees elite via the
    # overlay; the same user post-trial falls to free.
    #
    # Fail-closed: missing / None / unparseable tier_effective_until
    # does NOT expire. A null value means "no cancellation pending";
    # only an explicit past timestamp demotes. A live paying user has
    # a FUTURE timestamp (their next renewal) and must not be demoted.
    expiry_iso = user.get('tier_effective_until')
    if expiry_iso:
        expiry = _parse_utc_iso(expiry_iso)
        if expiry is not None and expiry < _now():
            stored = 'free'

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


# ── Bulk row-strip for list endpoints ──────────────────────────────
#
# Every proprietary score field a list/JSON endpoint can emit. The
# strip helper below NULLs each of these on rows that the caller's
# tier cannot view. Single source of truth for the field set so the
# 10+ leak surfaces stay synchronised — adding a new score column to
# signal_scores in the future means adding it here and the gate
# catches every route automatically.
# short_interest_penalty is intentionally NOT listed here. It is an all-tiers
# risk flag, not a proprietary score, and is served to Free, Pro, and Elite
# alike. Do not add it to this set or to ELITE_ONLY_SUBSCORE_FIELDS.
PROPRIETARY_SCORE_FIELDS = (
    'composite_score',
    'momentum_score',
    'quality_score',
    'insider_score',
    'reversion_score',
    'target_price',
    'target_upside',
    'rating',
    # Rating-change aliases pulled from rating_changes (currently only
    # /api/backtest/stats `recent` array). Same proprietary semantic as
    # 'rating', different column names. The `if f in r` guard in
    # strip_scores_for_non_elite makes these no-op on routes that don't
    # carry them — safe to extend the global set.
    'new_rating',
    'old_rating',
)


def strip_scores_for_non_elite(rows, tier, price_key='price'):
    """Mutate each row in `rows` IN PLACE: for any row whose price band
    is gated for `tier`, NULL every PROPRIETARY_SCORE_FIELDS key that
    EXISTS on the row. Non-score keys (ticker, price, volume, etc.)
    are untouched. Keys absent from the row are NOT added.

    Per-row gate calls can_view_score_for_ticker(tier, row[price_key])
    so the $5 boundary stays single-sourced in that predicate. Rows
    where price_key is absent or None fall through to the predicate's
    fail-closed branch (treated as gated for non-elite).

    Tier semantics (consistent with the entitlement contract):
      - elite : SHORT-CIRCUITS. No iteration, no mutation. Returns rows
                immediately because the predicate is True at every band.
      - pro   : iterates per row. Penny rows (price<5) stripped;
                non-penny rows preserved.
      - free  : iterates per row. Every row stripped at every price band.
                This is the locked Free=floor invariant — a free user
                sees NO proprietary scores anywhere, penny or not.

    `rows` must be a list of dicts (mutable mappings). The web/app.py
    db_query helper returns list[dict] via `[dict(r) for r in
    cur.fetchall()]`, so this is the shape every score-emitting route
    already passes downstream. Raw sqlite3.Row instances are immutable
    and would raise TypeError on assignment — that is an explicit
    failure mode, not a silent leak.

    `price_key` defaults to 'price' but accepts alternatives — e.g.
    'price_at_change' for the backtest `recent` array, 'current_price'
    for portfolio holdings. The predicate decision is identical; only
    the lookup name changes.

    Returns the same `rows` list. Callers can rely on either the
    in-place mutation or the return value, both are equivalent.
    """
    if tier == 'elite':
        return rows
    for r in rows:
        price = r.get(price_key)
        if not can_view_score_for_ticker(tier, price):
            for f in PROPRIETARY_SCORE_FIELDS:
                if f in r:
                    r[f] = None
    return rows


# ── Elite-strict sub-score gate (ticker detail Advanced section) ───
#
# The four positive sub-scores plus the Altman distress penalty are an
# Elite-only surface on the ticker detail page, regardless of price.
# This is STRICTER than strip_scores_for_non_elite, which gates the base
# scores by price band and would let a pro user see them on >=$5 tickers.
# Reusing that helper here would leak the sub-scores to pro. Hence a
# dedicated Elite-strict strip with its own field tuple (single source of
# truth for the set).
ELITE_ONLY_SUBSCORE_FIELDS = (
    'earnings_score',
    'piotroski_score',
    'inst_own_score',
    'analyst_mom_score',
    'altman_penalty',
)


def strip_subscores_for_non_elite(signal_dict, tier):
    """Pop every ELITE_ONLY_SUBSCORE_FIELDS key from `signal_dict` unless
    `tier` is 'elite'. Price-INDEPENDENT: a pro user loses the sub-scores
    at every price band (unlike strip_scores_for_non_elite, which only
    strips pro at the penny band).

    Tier semantics:
      - elite : returns signal_dict untouched (all five fields preserved).
      - pro / free / anything else : the five keys are popped if present;
        keys absent from the dict are a no-op (pop with default).

    Mutates `signal_dict` in place and returns it. The caller passes the
    per-ticker signal dict (web/app.py api_ticker), not a list of rows, so
    this takes a single dict rather than mirroring the list-based
    strip_scores_for_non_elite signature.
    """
    if tier == 'elite':
        return signal_dict
    for f in ELITE_ONLY_SUBSCORE_FIELDS:
        signal_dict.pop(f, None)
    return signal_dict


def filter_proprietary_flags_for_non_elite(rows, tier, price_key='price', flag_key='flag_list'):
    """For rows where `tier` can't see scores at the row's price band,
    DROP proprietary flag strings from row[flag_key]. Descriptive
    flags (RSI/SMA/short/analyst/52w bands) survive — they're
    market-data pass-through, not proprietary score output.

    PROPRIETARY_FLAGS is sourced from signals/scorer.py — the same
    named-constant tuples that `build_flags` appends from. Single
    source of truth for proprietary classification; no parallel
    hand-maintained list. Adding a new proprietary flag in scorer.py
    means appending to those tuples and the gate-set inherits it
    automatically.

    Tier semantics mirror strip_scores_for_non_elite:
      - elite : SHORT-CIRCUITS. No iteration, no mutation.
      - pro   : iterates per row; penny rows lose proprietary flags;
                non-penny rows untouched.
      - free  : iterates per row; every row loses proprietary flags
                (Free=floor — no proprietary signal output anywhere).

    Mutates in place; returns the same `rows` list.

    Import is lazy to avoid circular imports between signals/scorer
    and config/entitlements (scorer doesn't import entitlements
    today, but the lazy import keeps that property robust to
    refactors).
    """
    from signals.scorer import PROPRIETARY_FLAGS
    if tier == 'elite':
        return rows
    for r in rows:
        flags = r.get(flag_key)
        if not flags:
            continue
        if not can_view_score_for_ticker(tier, r.get(price_key)):
            r[flag_key] = [f for f in flags if f not in PROPRIETARY_FLAGS]
    return rows
