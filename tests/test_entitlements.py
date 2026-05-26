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
