"""
Tests for config/entitlements.py — capability predicates + trial overlay.

P15 throughout: every test asserts the grant AND the silence (denials).
Time injection uses monkeypatch on entitlements._now() so the
day-6 / day-8 boundary tests don't depend on wall-clock drift.
"""
import sqlite3
import pytest
from datetime import datetime, timedelta
from config import entitlements
from config.constants import DATABASE_PATH
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


# ── tier_effective_until lazy expiry ───────────────────────────────


def _expiry_iso(now_dt, days_offset):
    """Build an ISO tier_effective_until value at `days_offset` from now.

    Positive = future (paying user, not yet expired).
    Negative = past (cancelled-and-elapsed user, should demote).
    """
    return (now_dt + timedelta(days=days_offset)).isoformat()


def test_effective_tier_pro_expiry_past_no_trial(now):
    """Stored 'pro', tier_effective_until in the PAST, no active trial
    -> 'free'. This is the leak close: a cancelled paid user whose
    ride-out period has elapsed must drop to the free floor.

    Catches: lazy expiry regression that would leave cancelled-and-
             elapsed users at their stored paid tier indefinitely.
    Ignores: the exact past-offset magnitude; one day past is enough.
    """
    user = {'tier': 'pro', 'tier_effective_until': _expiry_iso(now, -1)}
    assert effective_tier(user) == 'free'


def test_effective_tier_pro_expiry_future_no_trial(now):
    """Stored 'pro', tier_effective_until in the FUTURE, no active trial
    -> 'pro'. CRITICAL: a live paying user has a future timestamp
    (their next renewal); they must NOT be demoted.

    Catches: an inverted comparison or off-by-one that would demote
             every paying subscriber on every request.
    Ignores: the exact future-offset; one day ahead is enough.
    """
    user = {'tier': 'pro', 'tier_effective_until': _expiry_iso(now, +30)}
    assert effective_tier(user) == 'pro'


def test_effective_tier_pro_expiry_past_active_trial(now):
    """Stored 'pro', tier_effective_until in the PAST, trial 3 days old
    -> 'elite'. The trial overlay wins over the expired-floor demotion.
    Order in the resolver: expiry-to-stored, THEN higher-rank-of
    (stored, trial_grant).

    Catches: the expiry check accidentally running AFTER the overlay,
             which would demote a mid-trial user with a stale paid sub.
    Ignores: whether the overlay reads stored or the demoted floor;
             the overlay's grant is 'elite' regardless.
    """
    user = {
        'tier': 'pro',
        'tier_effective_until': _expiry_iso(now, -1),
        'trial_started_at': _trial_ts(now, 3),
    }
    assert effective_tier(user) == 'elite'


def test_effective_tier_free_no_expiry_unchanged(now):
    """Stored 'free', tier_effective_until None, no trial -> 'free'.
    Null tier_effective_until means 'no cancellation pending'; the
    expiry branch must be a no-op for that case.

    Catches: a None-handling bug that would crash or wrongly demote
             users with no expiry set.
    Ignores: the trial-active branch (covered by overlay tests above).
    """
    user = {'tier': 'free', 'tier_effective_until': None}
    assert effective_tier(user) == 'free'


def test_effective_tier_pro_expiry_unparseable_fail_closed(now):
    """Stored 'pro', tier_effective_until is garbage -> 'pro'. Fail-
    closed: an unparseable timestamp must NOT trigger demotion. The
    user keeps their stored paid floor and the next webhook write
    will overwrite the garbage with a valid ISO value.

    Catches: a parse-failure path that defaults to 'demote on
             uncertainty'. That would lock paying users out of their
             paid surfaces whenever a write produced a malformed value.
    Ignores: the specific malformed input shape; one garbage string
             exercises the except branch in _parse_utc_iso.
    """
    user = {'tier': 'pro', 'tier_effective_until': 'not-an-iso-string'}
    assert effective_tier(user) == 'pro'


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


# ── strip_scores_for_non_elite — bulk row helper ──────────────────


def _sample_row(ticker, price, with_all_scores=True):
    """Representative response row carrying every proprietary score
    field plus non-score fields that MUST survive every strip path.

    Includes the rating_changes aliases (new_rating, old_rating) even
    though they typically appear only on /api/backtest/stats `recent`
    rows — so matrix tests verify the full PROPRIETARY_SCORE_FIELDS
    set, not just the 'rating' subset.
    """
    row = {
        'ticker':   ticker,
        'company':  'Acme Corp',
        'price':    price,
        'volume':   1_000_000,
    }
    if with_all_scores:
        row.update({
            'composite_score': 67.5,
            'momentum_score':  72.0,
            'quality_score':   55.0,
            'insider_score':   60.0,
            'reversion_score': 40.0,
            'target_price':    8.50,
            'target_upside':   25.0,
            'rating':          'BUY',
            'new_rating':      'BUY',
            'old_rating':      'HOLD',
        })
    return row


def test_strip_free_penny_row_nulls_all_score_fields():
    """Free + penny: every PROPRIETARY_SCORE_FIELDS key on the row →
    None. Non-score keys (ticker/price/volume/company) untouched.

    Catches: a regression where the strip set narrows or stops
             touching one of the eight fields.
    Ignores: dict key order.
    """
    from config.entitlements import (
        strip_scores_for_non_elite, PROPRIETARY_SCORE_FIELDS,
    )
    rows = [_sample_row('ALTO', 4.5)]
    strip_scores_for_non_elite(rows, 'free')
    r = rows[0]
    for f in PROPRIETARY_SCORE_FIELDS:
        assert r[f] is None, f'{f} not nulled: {r[f]!r}'
    assert r['ticker'] == 'ALTO'
    assert r['price'] == 4.5
    assert r['volume'] == 1_000_000
    assert r['company'] == 'Acme Corp'


def test_strip_free_non_penny_row_also_stripped():
    """Free + non-penny ($175 AAPL-shaped): ALSO stripped. Free is
    the unpaid floor — sees no proprietary scores at any price band.

    This is the intended two-tier behaviour: free=blanks-everywhere,
    pro=blanks-on-penny-only, elite=intact-everywhere. Anyone reading
    the free-strips-everything behaviour as a bug should re-read
    this docstring; it is the locked Free=floor invariant from Step 0.

    Catches: a future change that lets free see non-penny scores —
             would silently turn 'free' into a partial-access tier.
    Ignores: which specific non-score keys exist on the row.
    """
    from config.entitlements import (
        strip_scores_for_non_elite, PROPRIETARY_SCORE_FIELDS,
    )
    rows = [_sample_row('AAPL', 175.0)]
    strip_scores_for_non_elite(rows, 'free')
    for f in PROPRIETARY_SCORE_FIELDS:
        assert rows[0][f] is None, f'free should strip {f} at non-penny prices'


def test_strip_pro_penny_row_nulls_scores():
    """Pro + penny: stripped. Penny signals are Elite-only.

    Catches: a parallel $5 boundary creeping into the helper that
             bypasses can_view_score_for_ticker.
    Ignores: which non-score fields survive.
    """
    from config.entitlements import (
        strip_scores_for_non_elite, PROPRIETARY_SCORE_FIELDS,
    )
    rows = [_sample_row('ALTO', 4.5)]
    strip_scores_for_non_elite(rows, 'pro')
    for f in PROPRIETARY_SCORE_FIELDS:
        assert rows[0][f] is None


def test_strip_pro_non_penny_row_preserved():
    """Pro + non-penny ($175): NOT stripped. Pro sees full scores on
    price >= 5 rows — this is what Pro pays for.

    Catches: an over-broad strip that hits all rows regardless of
             price for the pro tier.
    Ignores: exact field values, only that they survive non-None.
    """
    from config.entitlements import (
        strip_scores_for_non_elite, PROPRIETARY_SCORE_FIELDS,
    )
    rows = [_sample_row('AAPL', 175.0)]
    strip_scores_for_non_elite(rows, 'pro')
    for f in PROPRIETARY_SCORE_FIELDS:
        assert rows[0][f] is not None, f'{f} stripped despite pro+non-penny'


def test_strip_elite_penny_row_preserved():
    """Elite + penny: NOT stripped. Elite sees everything at any band.

    Catches: a regression in the elite short-circuit that mutated
             rows anyway.
    Ignores: exact field values.
    """
    from config.entitlements import (
        strip_scores_for_non_elite, PROPRIETARY_SCORE_FIELDS,
    )
    rows = [_sample_row('ALTO', 4.5)]
    strip_scores_for_non_elite(rows, 'elite')
    for f in PROPRIETARY_SCORE_FIELDS:
        assert rows[0][f] is not None


def test_strip_missing_price_fails_closed_for_non_elite():
    """Row missing price_key (or price=None) for non-elite → stripped.
    Mirrors can_view_score_for_ticker's price=None branch (elite-only).

    Catches: a fail-open path where a NULL price silently let scores
             through to a non-elite caller.
    Ignores: the exact reason price was missing (no key vs None value).
    """
    from config.entitlements import (
        strip_scores_for_non_elite, PROPRIETARY_SCORE_FIELDS,
    )
    # price=None
    rows = [_sample_row('ALTO', None)]
    strip_scores_for_non_elite(rows, 'pro')
    for f in PROPRIETARY_SCORE_FIELDS:
        assert rows[0][f] is None

    # price key entirely absent
    r = {'ticker': 'ALTO', 'volume': 100_000,
         'composite_score': 67.0, 'rating': 'BUY'}
    strip_scores_for_non_elite([r], 'pro')
    assert r['composite_score'] is None
    assert r['rating'] is None


def test_strip_only_nulls_existing_fields_no_new_keys():
    """A row missing some score fields keeps its shape. The helper
    does NOT add keys that were absent on input — that would expand
    response payloads with spurious nulls and could break clients
    expecting a specific shape.

    Catches: an implementation that templates all 8 fields onto every
             row.
    Ignores: order of remaining keys.
    """
    from config.entitlements import strip_scores_for_non_elite
    r = {'ticker': 'ALTO', 'price': 4.5,
         'composite_score': 67.0, 'rating': 'BUY'}
    before_keys = set(r.keys())
    strip_scores_for_non_elite([r], 'free')
    after_keys = set(r.keys())
    assert before_keys == after_keys, \
        f'helper added keys: {after_keys - before_keys}'
    assert r['composite_score'] is None
    assert r['rating'] is None
    # Fields never on the row stay absent
    assert 'momentum_score' not in r
    assert 'target_upside' not in r


def test_strip_alternate_price_key_for_backtest_recent():
    """The backtest 'recent' array uses 'price_at_change' as the
    price field. Helper must honour the alternate key — the predicate
    decision must be driven by the value under price_key, not by
    looking for 'price' which isn't on these rows.

    Tested both branches (penny + non-penny) to prove the alternate
    key actually drives the gate, not just that strip happens for
    other reasons (NULL-price fail-closed branch would also strip,
    masking a buggy price_key lookup).

    Catches: a hardcoded 'price' lookup that would miss the backtest
             surface entirely.
    Ignores: which other fields exist on the backtest row.
    """
    from config.entitlements import strip_scores_for_non_elite
    # Non-penny price under the alternate key → pro gate OPEN → preserved
    rows = [{
        'ticker':          'AAPL',
        'price_at_change': 175.0,
        'composite_score': 85.0,
        'new_rating':      'STRONG_BUY',
    }]
    strip_scores_for_non_elite(rows, 'pro', price_key='price_at_change')
    assert rows[0]['composite_score'] == 85.0, \
        'non-penny price_at_change should NOT trigger strip for pro'
    assert rows[0]['new_rating'] == 'STRONG_BUY'

    # Penny price under the alternate key → pro gate CLOSES → stripped
    rows = [{
        'ticker':          'MTEX',
        'price_at_change': 4.62,
        'composite_score': 33.1,
        'new_rating':      'SELL',
    }]
    strip_scores_for_non_elite(rows, 'pro', price_key='price_at_change')
    assert rows[0]['composite_score'] is None
    # new_rating is now in PROPRIETARY_SCORE_FIELDS (rating alias) — stripped
    assert rows[0]['new_rating'] is None


def test_strip_elite_short_circuits_mixed_list():
    """Mixed list (penny + non-penny) for elite caller comes back
    fully intact. Elite predicate is True at all bands; the short-
    circuit skips per-row work entirely.

    Catches: the elite branch accidentally iterating and mutating
             (would surface if someone removed the if-tier=='elite'
             guard).
    Ignores: timing — this is correctness, not perf.
    """
    from config.entitlements import strip_scores_for_non_elite
    rows = [_sample_row('ALTO', 4.5), _sample_row('AAPL', 175.0)]
    before = [dict(r) for r in rows]
    strip_scores_for_non_elite(rows, 'elite')
    assert rows == before, 'elite caller saw mutation'


def test_strip_returns_the_same_list_object():
    """Helper returns the list passed in (not a copy). Callers can
    rely on either the return value or the in-place mutation.

    Catches: an accidental list comprehension that returns a copy
             and leaves the original list unchanged.
    Ignores: row-element identity (the dicts inside can still be
             the same instances either way).
    """
    from config.entitlements import strip_scores_for_non_elite
    rows = [_sample_row('ALTO', 4.5)]
    returned = strip_scores_for_non_elite(rows, 'free')
    assert returned is rows


def test_strip_new_rating_old_rating_aliases_nulled():
    """A backtest-shaped row carrying new_rating/old_rating (the
    rating_changes aliases) → both nulled for non-elite alongside
    composite_score. Non-score fields (ticker, price_at_change,
    change_date) preserved.

    Catches: a regression where the rating-alias additions to
             PROPRIETARY_SCORE_FIELDS get reverted, leaving the
             backtest 'recent' array partially gated (composite null
             but rating values still leaking).
    Ignores: which other backtest-side fields exist on the row.
    """
    from config.entitlements import strip_scores_for_non_elite
    rows = [{
        'ticker':          'MTEX',
        'price_at_change': 4.62,
        'change_date':     '2026-05-07',
        'old_rating':      'HOLD',
        'new_rating':      'SELL',
        'composite_score': 33.1,
    }]
    strip_scores_for_non_elite(rows, 'free', price_key='price_at_change')
    assert rows[0]['composite_score'] is None
    assert rows[0]['old_rating'] is None
    assert rows[0]['new_rating'] is None
    # Non-score fields preserved
    assert rows[0]['ticker'] == 'MTEX'
    assert rows[0]['price_at_change'] == 4.62
    assert rows[0]['change_date'] == '2026-05-07'


def test_filter_proprietary_flags_free_penny_drops_proprietary_keeps_descriptive():
    """Free + penny row: proprietary flags dropped from flag_list,
    descriptive flags retained. Catches: the filter dropping too
    much (descriptive lost — over-broad gate) or too little
    (proprietary leaked — under-broad gate).

    Uses the actual proprietary strings from signals/scorer's named
    constants — sourced via the PROPRIETARY_FLAGS frozenset, so this
    test follows the same single-source-of-truth as production.

    Ignores: order of remaining descriptive flags.
    """
    from config.entitlements import filter_proprietary_flags_for_non_elite
    from signals.scorer import PROPRIETARY_FLAGS
    descriptive = "⚠ Overbought RSI"
    other_descriptive = "↑ Above 50d SMA"
    proprietary_a = "★ Strong insider buying"
    proprietary_b = "↩ Mean reversion candidate"
    # Sanity: confirm our test fixtures match the production set
    assert proprietary_a in PROPRIETARY_FLAGS
    assert proprietary_b in PROPRIETARY_FLAGS
    assert descriptive not in PROPRIETARY_FLAGS

    rows = [{
        'ticker': 'ALTO', 'price': 2.50,
        'flag_list': [descriptive, other_descriptive, proprietary_a,
                      "⚠ High short interest 25.0%", proprietary_b]
    }]
    filter_proprietary_flags_for_non_elite(rows, 'free')
    remaining = rows[0]['flag_list']
    assert proprietary_a not in remaining
    assert proprietary_b not in remaining
    assert descriptive in remaining
    assert other_descriptive in remaining
    assert "⚠ High short interest 25.0%" in remaining


def test_filter_proprietary_flags_pro_non_penny_keeps_all():
    """Pro + non-penny: gate doesn't fire → all flags kept INCLUDING
    proprietary. Pro pays for scores on non-penny tickers.

    Catches: filter over-broadly dropping flags for pro on any price.
    Ignores: descriptive flag presence (only the proprietary survival
             matters here).
    """
    from config.entitlements import filter_proprietary_flags_for_non_elite
    rows = [{
        'ticker': 'AAPL', 'price': 175.0,
        'flag_list': ["⚠ Overbought RSI", "★ Strong insider buying"]
    }]
    filter_proprietary_flags_for_non_elite(rows, 'pro')
    assert "★ Strong insider buying" in rows[0]['flag_list']


def test_filter_proprietary_flags_pro_penny_drops_proprietary():
    """Pro + penny: gate fires (penny is Elite-only) → proprietary
    flags dropped. Descriptive flags kept.

    Catches: filter not firing for the pro+penny case.
    """
    from config.entitlements import filter_proprietary_flags_for_non_elite
    rows = [{
        'ticker': 'ALTO', 'price': 2.50,
        'flag_list': ["⚠ Overbought RSI", "★ Strong insider buying"]
    }]
    filter_proprietary_flags_for_non_elite(rows, 'pro')
    assert "★ Strong insider buying" not in rows[0]['flag_list']
    assert "⚠ Overbought RSI" in rows[0]['flag_list']


def test_filter_proprietary_flags_elite_short_circuits():
    """Elite caller: helper short-circuits — proprietary flags
    survive unchanged on any row.

    Catches: the elite branch accidentally iterating and mutating.
    """
    from config.entitlements import filter_proprietary_flags_for_non_elite
    rows = [{
        'ticker': 'ALTO', 'price': 2.50,
        'flag_list': ["★ Strong insider buying", "↩ Mean reversion candidate"]
    }]
    before = list(rows[0]['flag_list'])
    filter_proprietary_flags_for_non_elite(rows, 'elite')
    assert rows[0]['flag_list'] == before


def test_filter_proprietary_flags_missing_price_fails_closed():
    """price=None for non-elite → gated → proprietary flags dropped.
    Mirrors can_view_score_for_ticker's None-fails-closed branch.

    Catches: a fail-open path on missing price.
    """
    from config.entitlements import filter_proprietary_flags_for_non_elite
    rows = [{
        'ticker': 'ALTO', 'price': None,
        'flag_list': ["⚠ Overbought RSI", "★ Strong insider buying"]
    }]
    filter_proprietary_flags_for_non_elite(rows, 'pro')
    assert "★ Strong insider buying" not in rows[0]['flag_list']
    assert "⚠ Overbought RSI" in rows[0]['flag_list']


def test_filter_proprietary_flags_empty_flag_list_noop():
    """Row with empty flag_list (or missing key) → no-op, no error.

    Catches: helper crashing on rows that don't have flag_list yet
             (would break any route where flags aren't always present).
    """
    from config.entitlements import filter_proprietary_flags_for_non_elite
    rows = [
        {'ticker': 'ALTO', 'price': 2.50, 'flag_list': []},
        {'ticker': 'AACG', 'price': 1.79},  # no flag_list key at all
    ]
    filter_proprietary_flags_for_non_elite(rows, 'free')
    assert rows[0]['flag_list'] == []
    assert 'flag_list' not in rows[1]


def test_strip_two_tier_intended_behaviour():
    """P15 documentary test: spells out the THREE-tier strip pattern
    on a single mixed list with one penny and one non-penny row.

      free  → both rows stripped (Free=floor, no scores anywhere)
      pro   → penny stripped, non-penny preserved
      elite → both intact (no stripping at any band)

    Catches: a future relaxation of the floor that lets free see
             non-penny scores; or pro becoming over-broad.
    Ignores: which non-score keys exist on each row.
    """
    from config.entitlements import strip_scores_for_non_elite

    def fresh():
        return [_sample_row('ALTO', 4.5), _sample_row('AAPL', 175.0)]

    free_rows = strip_scores_for_non_elite(fresh(), 'free')
    assert free_rows[0]['composite_score'] is None  # penny stripped
    assert free_rows[1]['composite_score'] is None  # non-penny ALSO (floor)

    pro_rows = strip_scores_for_non_elite(fresh(), 'pro')
    assert pro_rows[0]['composite_score'] is None      # penny stripped
    assert pro_rows[1]['composite_score'] is not None  # non-penny preserved

    elite_rows = strip_scores_for_non_elite(fresh(), 'elite')
    assert elite_rows[0]['composite_score'] is not None  # penny intact
    assert elite_rows[1]['composite_score'] is not None  # non-penny intact


# ── strip_subscores_for_non_elite, Elite-strict sub-score gate ────


def _signal_with_subscores():
    """A ticker-detail signal dict carrying the four positive sub-scores
    plus the Altman penalty AND base scores that must survive every strip
    path. Mirrors the payload['signal'] shape api_ticker builds."""
    return {
        'ticker':            'AAPL',
        'composite_score':   67.5,
        'momentum_score':    72.0,
        'rating':            'BUY',
        'earnings_score':    60.0,
        'piotroski_score':   65.0,
        'inst_own_score':    75.0,
        'analyst_mom_score': 70.0,
        'altman_penalty':    -30,
    }


def test_strip_subscores_elite_preserves_all():
    """Elite: all five ELITE_ONLY_SUBSCORE_FIELDS preserved; base scores
    untouched.

    Catches: an elite short-circuit regression that mutated the dict.
    Ignores: base-field values beyond presence.
    """
    from config.entitlements import (
        strip_subscores_for_non_elite, ELITE_ONLY_SUBSCORE_FIELDS,
    )
    sig = _signal_with_subscores()
    strip_subscores_for_non_elite(sig, 'elite')
    for f in ELITE_ONLY_SUBSCORE_FIELDS:
        assert sig[f] is not None, f'elite lost {f}'
    assert sig['composite_score'] == 67.5
    assert sig['momentum_score'] == 72.0


def test_strip_subscores_pro_pops_all_fields():
    """Pro: every sub-score key POPPED (absent, not nulled). Base scores
    (composite, momentum, rating) survive untouched.

    Catches: the revenue leak, pro retaining any of the five sub-score
             fields. Popping (not nulling) means the keys cannot reach
             the client at all.
    Ignores: which base fields exist beyond the three asserted.
    """
    from config.entitlements import (
        strip_subscores_for_non_elite, ELITE_ONLY_SUBSCORE_FIELDS,
    )
    sig = _signal_with_subscores()
    strip_subscores_for_non_elite(sig, 'pro')
    for f in ELITE_ONLY_SUBSCORE_FIELDS:
        assert f not in sig, f'pro retained {f}'
    assert sig['composite_score'] == 67.5
    assert sig['momentum_score'] == 72.0
    assert sig['rating'] == 'BUY'


def test_strip_subscores_free_pops_all_fields():
    """Free: identical to pro for this gate, all five popped.

    Catches: a tier check that only handled 'pro' and let 'free' through.
    """
    from config.entitlements import (
        strip_subscores_for_non_elite, ELITE_ONLY_SUBSCORE_FIELDS,
    )
    sig = _signal_with_subscores()
    strip_subscores_for_non_elite(sig, 'free')
    for f in ELITE_ONLY_SUBSCORE_FIELDS:
        assert f not in sig, f'free retained {f}'


def test_strip_subscores_price_independent_for_pro():
    """Elite-strict and price-INDEPENDENT: the helper takes no price, so
    there is no band that can open the gate for pro. This is the explicit
    contrast with strip_scores_for_non_elite, which preserves base scores
    for pro on price >= 5. The sub-scores are Elite-only at EVERY price.

    Catches: a future refactor that reintroduces a price-band exception
             and lets pro see sub-scores on non-penny tickers (the exact
             leak the dedicated helper exists to prevent).
    Ignores: any price value, there is no price parameter by design.
    """
    from config.entitlements import (
        strip_subscores_for_non_elite, ELITE_ONLY_SUBSCORE_FIELDS,
    )
    # A notionally high-priced name still loses the sub-scores for pro.
    sig = _signal_with_subscores()
    sig['price'] = 175.0
    strip_subscores_for_non_elite(sig, 'pro')
    for f in ELITE_ONLY_SUBSCORE_FIELDS:
        assert f not in sig, f'pro retained {f} on a high-priced ticker'


def test_strip_subscores_absent_keys_noop():
    """A signal dict missing the sub-score keys → no-op (pop with default),
    no KeyError, no spurious keys added.

    Catches: a pop without default that would crash on a data-poor signal,
             or an implementation that templates the five keys onto every
             dict.
    """
    from config.entitlements import strip_subscores_for_non_elite
    sig = {'ticker': 'AAPL', 'composite_score': 50.0}
    before = set(sig.keys())
    strip_subscores_for_non_elite(sig, 'pro')
    assert set(sig.keys()) == before


def test_strip_subscores_returns_same_dict():
    """Helper returns the dict passed in (in-place mutation contract)."""
    from config.entitlements import strip_subscores_for_non_elite
    sig = _signal_with_subscores()
    assert strip_subscores_for_non_elite(sig, 'elite') is sig


# ── api_ticker server-side leak guard (integration) ───────────────


def _ticker_above_five_with_subscores():
    """Pick a ticker whose LATEST screener price is >= $5 and whose latest
    signal row carries at least one non-null sub-score. Mirrors the route's
    latest-snapshot price read so the chosen ticker is genuinely non-penny
    for api_ticker. Returns the ticker or None (test skips on a thin DB)."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("""
            SELECT s.ticker
            FROM signal_scores s
            WHERE EXISTS (
                SELECT 1 FROM screener_snapshots ss
                WHERE ss.ticker = s.ticker
                  AND ss.scraped_at = (
                      SELECT MAX(scraped_at) FROM screener_snapshots
                      WHERE ticker = s.ticker
                  )
                  AND ss.price >= 5
            )
            AND (s.earnings_score IS NOT NULL OR s.piotroski_score IS NOT NULL
                 OR s.inst_own_score IS NOT NULL OR s.analyst_mom_score IS NOT NULL)
            ORDER BY s.scored_at DESC
            LIMIT 1
        """).fetchone()
        return row['ticker'] if row else None
    finally:
        conn.close()


def test_api_ticker_elite_includes_subscores(client, monkeypatch):
    """Elite caller on a >= $5 ticker: payload['signal'] carries all five
    sub-score fields and subscores_locked is False.

    Catches: the server gate over-stripping for elite (the four sub-scores
             vanishing for the tier that paid for them).
    Ignores: the sub-score VALUES (some may be legitimately NULL on a
             data-poor ticker); this asserts key PRESENCE and the flag.
    """
    import web.app as webapp
    ticker = _ticker_above_five_with_subscores()
    if not ticker:
        pytest.skip("no >=$5 ticker with sub-scores in DB")
    monkeypatch.setattr(webapp, 'effective_tier', lambda u: 'elite')
    resp = client.get(f"/api/ticker/{ticker}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['subscores_locked'] is False
    sig = data['signal']
    for f in ('earnings_score', 'piotroski_score', 'inst_own_score',
              'analyst_mom_score', 'altman_penalty'):
        assert f in sig, f'elite missing {f} from /api/ticker payload'


def test_api_ticker_pro_strips_subscores_leak_guard(client, monkeypatch):
    """MANDATORY LEAK GUARD. Pro caller on a >= $5 ticker: the base signal
    is visible (composite present, proving the row is non-penny and NOT
    empty for the wrong reason), but the five sub-score fields are ABSENT
    from the JSON, and subscores_locked is True.

    Catches: the revenue leak where pro receives the Elite-only sub-scores
             in the API response (leakable via view-source / devtools even
             if the template hides them). This is the regression guard the
             whole server-side-gate design exists for.
    Ignores: the base-score values; only their presence (visibility proof)
             and the sub-score absence matter.
    """
    import web.app as webapp
    ticker = _ticker_above_five_with_subscores()
    if not ticker:
        pytest.skip("no >=$5 ticker with sub-scores in DB")
    monkeypatch.setattr(webapp, 'effective_tier', lambda u: 'pro')
    resp = client.get(f"/api/ticker/{ticker}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['subscores_locked'] is True
    sig = data['signal']
    # Base signal visible for pro on a non-penny ticker (not empty for the
    # wrong reason): proves the absence below is the strip, not a penny lock.
    assert sig.get('composite_score') is not None, \
        'expected a visible base signal for pro on a >=$5 ticker'
    for f in ('earnings_score', 'piotroski_score', 'inst_own_score',
              'analyst_mom_score', 'altman_penalty'):
        assert f not in sig, f'LEAK: pro received {f} in /api/ticker payload'
