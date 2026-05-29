"""
Tests for GET /upgrade — Stripe Checkout creation (Phase 2 Commit 5).

These tests mock stripe.Price.list and stripe.checkout.Session.create
so no Stripe network calls are made. The runtime real-Stripe
verification (creating actual test-mode sessions and reading them
back) happens in the commit gate, not in pytest.

P15 contract for the whole file:
  Catches — regressions in tier/interval/currency validation,
            currency-resolution precedence, lookup_key construction,
            client_reference_id wiring (THE thread the webhook
            uses to identify the user), and the auth gate.
  Ignores — Stripe-side checkout UX, success/cancel page rendering,
            and the post-payment webhook flow (covered in Commit 4).
"""
from unittest import mock

import pytest


VALID_COMBOS = [
    ("pro", "monthly", "usd", "pro_usd_monthly"),
    ("pro", "monthly", "gbp", "pro_gbp_monthly"),
    ("pro", "annual",  "usd", "pro_usd_annual"),
    ("pro", "annual",  "gbp", "pro_gbp_annual"),
    ("elite", "monthly", "usd", "elite_usd_monthly"),
    ("elite", "monthly", "gbp", "elite_gbp_monthly"),
    ("elite", "annual",  "usd", "elite_usd_annual"),
    ("elite", "annual",  "gbp", "elite_gbp_annual"),
]


@pytest.fixture
def isolated_app(tmp_path, monkeypatch):
    """Flask test client backed by a temp DB.

    Same isolation pattern as the webhook tests: monkeypatched
    DATABASE_PATH redirects all DB access to a temp file with
    both schemas applied.
    """
    from database.db import (
        initialise_subscription_events_schema,
        initialise_user_schema,
    )

    db_path = str(tmp_path / "checkout_test.db")
    initialise_user_schema(db_path)
    initialise_subscription_events_schema(db_path)

    import web.app

    monkeypatch.setattr(web.app, "DATABASE_PATH", db_path)
    web.app.app.config["TESTING"] = True
    # The /upgrade route is rate-limited (10/min) in production to
    # prevent abuse, but the test client hits it from a single source
    # IP across many tests in quick succession — disable rate limit
    # in tests so parametrized runs cover all 8 combos without
    # tripping the 429.
    web.app.limiter.enabled = False
    yield {"app": web.app.app, "db_path": db_path}
    web.app.limiter.enabled = True


def _authed_client(isolated_app, *, user_id=42):
    """Flask test client with session['user_id'] pre-seeded."""
    client = isolated_app["app"].test_client()
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
    return client


def _mock_stripe_price(lookup_key, price_id="price_test_xxx"):
    """Build a mock Price object that supports .id attribute access."""
    p = mock.MagicMock()
    p.id = price_id
    p.lookup_key = lookup_key
    return p


def _mock_stripe_session(url="https://checkout.stripe.com/c/pay/cs_test_xxx"):
    """Build a mock Checkout Session object with the .url attribute."""
    s = mock.MagicMock()
    s.url = url
    s.id = "cs_test_session"
    return s


# ── auth gate ──────────────────────────────────────────────────────────


def test_logged_out_user_redirected_to_login(isolated_app):
    """No session['user_id'] → 302 redirect to /login.

    Catches: a regression that drops the @login_required decorator
             or session check, exposing checkout creation to
             anonymous callers (who could spam Stripe with sessions).
    Ignores: the exact redirect target — only the 'reject' verdict
             matters.
    """
    client = isolated_app["app"].test_client()
    resp = client.get("/upgrade?tier=pro&interval=monthly")
    assert resp.status_code == 302
    assert "/login" in resp.headers.get("Location", ""), (
        f"expected redirect to /login, got {resp.headers.get('Location')!r}"
    )


# ── validation ─────────────────────────────────────────────────────────


def test_invalid_tier_returns_400(isolated_app):
    """tier outside {pro, elite} → 400, no Stripe call.

    Catches: a regression where invalid tier falls through to a
             malformed lookup_key (e.g. 'starter_usd_monthly') that
             would 500 on the Stripe.Price.list lookup. The 400
             surface is the cleaner contract.
    Ignores: error message wording.
    """
    client = _authed_client(isolated_app)
    with mock.patch("web.app.stripe.Price.list") as mock_list:
        resp = client.get("/upgrade?tier=starter&interval=monthly")
    assert resp.status_code == 400
    mock_list.assert_not_called()  # no Stripe API call for invalid input


def test_invalid_interval_returns_400(isolated_app):
    """interval outside {monthly, annual} → 400.

    Catches: a regression accepting Stripe's 'month'/'year' interval
             names (Stripe-side names, NOT our lookup_key names).
    Ignores: error message wording.
    """
    client = _authed_client(isolated_app)
    with mock.patch("web.app.stripe.Price.list") as mock_list:
        resp = client.get("/upgrade?tier=pro&interval=month")  # wrong: should be 'monthly'
    assert resp.status_code == 400
    mock_list.assert_not_called()


# ── currency resolution ────────────────────────────────────────────────


def test_default_currency_is_usd_when_no_geo_signal(isolated_app):
    """Bare request (no CF, no Accept-Language) → USD.

    Catches: a regression that flips the default to GBP — most of
             our addressable market is US-based, GBP-default would
             surprise.
    Ignores: how the resolver behaves with conflicting signals (own
             tests below).
    """
    client = _authed_client(isolated_app)
    with mock.patch("web.app.stripe.Price.list") as mock_list, \
         mock.patch("web.app.stripe.checkout.Session.create") as mock_create:
        mock_list.return_value = mock.MagicMock(data=[_mock_stripe_price("pro_usd_monthly")])
        mock_create.return_value = _mock_stripe_session()
        client.get("/upgrade?tier=pro&interval=monthly")
    mock_list.assert_called_once_with(lookup_keys=["pro_usd_monthly"], limit=1)


def test_cf_ipcountry_gb_resolves_to_gbp(isolated_app):
    """CF-IPCountry: GB → GBP lookup_key.

    Catches: regression in the CF header read path — this is the
             production geo source once the app sits behind Cloudflare.
    Ignores: other ISO countries — they all resolve to USD by policy.
    """
    client = _authed_client(isolated_app)
    with mock.patch("web.app.stripe.Price.list") as mock_list, \
         mock.patch("web.app.stripe.checkout.Session.create") as mock_create:
        mock_list.return_value = mock.MagicMock(data=[_mock_stripe_price("pro_gbp_monthly")])
        mock_create.return_value = _mock_stripe_session()
        client.get(
            "/upgrade?tier=pro&interval=monthly",
            headers={"CF-IPCountry": "GB"},
        )
    mock_list.assert_called_once_with(lookup_keys=["pro_gbp_monthly"], limit=1)


def test_cf_ipcountry_non_uk_resolves_to_usd(isolated_app):
    """CF-IPCountry: US (or any non-GB) → USD lookup_key.

    Catches: a regression where a non-GB CF country falls through to
             the Accept-Language fallback instead of locking to USD.
             That would mis-route some US users to GBP if they had
             en-GB in their browser locale (rare but real).
    Ignores: the specific non-GB country code used.
    """
    client = _authed_client(isolated_app)
    with mock.patch("web.app.stripe.Price.list") as mock_list, \
         mock.patch("web.app.stripe.checkout.Session.create") as mock_create:
        mock_list.return_value = mock.MagicMock(data=[_mock_stripe_price("elite_usd_annual")])
        mock_create.return_value = _mock_stripe_session()
        # CF says US even though Accept-Language tries to claim GB.
        client.get(
            "/upgrade?tier=elite&interval=annual",
            headers={"CF-IPCountry": "US", "Accept-Language": "en-GB,en;q=0.9"},
        )
    mock_list.assert_called_once_with(lookup_keys=["elite_usd_annual"], limit=1)


def test_explicit_currency_query_overrides_geo(isolated_app):
    """?currency=gbp wins over CF-IPCountry=US.

    Catches: precedence regression. Explicit overrides exist for
             marketing experiments and for tests; if CF wins, neither
             use case works.
    Ignores: the gbp/usd-symmetric inverse (covered next test).
    """
    client = _authed_client(isolated_app)
    with mock.patch("web.app.stripe.Price.list") as mock_list, \
         mock.patch("web.app.stripe.checkout.Session.create") as mock_create:
        mock_list.return_value = mock.MagicMock(data=[_mock_stripe_price("pro_gbp_annual")])
        mock_create.return_value = _mock_stripe_session()
        client.get(
            "/upgrade?tier=pro&interval=annual&currency=gbp",
            headers={"CF-IPCountry": "US"},
        )
    mock_list.assert_called_once_with(lookup_keys=["pro_gbp_annual"], limit=1)


def test_accept_language_en_gb_fallback(isolated_app):
    """No CF header, Accept-Language: en-GB → GBP.

    Catches: a regression dropping the Accept-Language fallback.
             Without CF in dev and without ?currency override,
             this is the only signal that a UK user gets GBP.
    Ignores: other Accept-Language values (covered by default case).
    """
    client = _authed_client(isolated_app)
    with mock.patch("web.app.stripe.Price.list") as mock_list, \
         mock.patch("web.app.stripe.checkout.Session.create") as mock_create:
        mock_list.return_value = mock.MagicMock(data=[_mock_stripe_price("elite_gbp_monthly")])
        mock_create.return_value = _mock_stripe_session()
        client.get(
            "/upgrade?tier=elite&interval=monthly",
            headers={"Accept-Language": "en-GB,en-US;q=0.9"},
        )
    mock_list.assert_called_once_with(lookup_keys=["elite_gbp_monthly"], limit=1)


# ── load-bearing: client_reference_id ──────────────────────────────────


def test_session_carries_client_reference_id_as_string(isolated_app):
    """client_reference_id MUST be str(session['user_id']).

    THE thread the webhook (Commit 4) uses to identify the user.
    Was verified live this session — webhook fails with "missing
    client_reference_id" when not set.

    Catches: a regression where client_reference_id is omitted or
             passes int instead of str. Stripe stores it as a string
             either way, but pinning the call-site contract here
             matches what the webhook reads.
    Ignores: other session-creation params except those required
             for the test (price + mode are required by Stripe).
    """
    client = _authed_client(isolated_app, user_id=12345)
    with mock.patch("web.app.stripe.Price.list") as mock_list, \
         mock.patch("web.app.stripe.checkout.Session.create") as mock_create:
        mock_list.return_value = mock.MagicMock(data=[_mock_stripe_price("pro_usd_monthly")])
        mock_create.return_value = _mock_stripe_session()
        resp = client.get("/upgrade?tier=pro&interval=monthly")

    assert resp.status_code == 303
    call_kwargs = mock_create.call_args.kwargs
    assert call_kwargs["client_reference_id"] == "12345", (
        f"client_reference_id must be the user id as a string; "
        f"got {call_kwargs['client_reference_id']!r}"
    )
    assert call_kwargs["mode"] == "subscription"
    assert call_kwargs["line_items"][0]["price"] == "price_test_xxx"
    # success/cancel URLs must be absolute (Stripe requires this).
    assert call_kwargs["success_url"].startswith("http"), (
        f"success_url must be absolute, got {call_kwargs['success_url']!r}"
    )
    assert "upgrade=success" in call_kwargs["success_url"]
    assert call_kwargs["cancel_url"].startswith("http")
    assert "upgrade=cancel" in call_kwargs["cancel_url"]


def test_redirect_targets_stripe_hosted_url(isolated_app):
    """Endpoint 303-redirects to the Stripe-hosted checkout URL.

    Catches: a regression that returns JSON instead of redirecting,
             or uses 200 instead of 303. 303 is the correct status
             for "see other" after a side-effecting GET that
             produces a resource elsewhere.
    Ignores: the exact URL format Stripe returns (it varies by
             session id).
    """
    client = _authed_client(isolated_app)
    with mock.patch("web.app.stripe.Price.list") as mock_list, \
         mock.patch("web.app.stripe.checkout.Session.create") as mock_create:
        mock_list.return_value = mock.MagicMock(data=[_mock_stripe_price("pro_usd_monthly")])
        mock_create.return_value = _mock_stripe_session(
            url="https://checkout.stripe.com/c/pay/cs_test_redirect_target"
        )
        resp = client.get("/upgrade?tier=pro&interval=monthly")
    assert resp.status_code == 303
    assert resp.headers["Location"] == (
        "https://checkout.stripe.com/c/pay/cs_test_redirect_target"
    )


# ── all 8 combos resolve to the right lookup_key ───────────────────────


@pytest.mark.parametrize(
    "tier,interval,currency,expected_lookup_key", VALID_COMBOS
)
def test_all_combos_resolve_correct_lookup_key(
    isolated_app, tier, interval, currency, expected_lookup_key
):
    """All 8 (tier × interval × currency) combinations resolve their
    documented lookup_key.

    Catches: any drift between the lookup_key scheme (Phase 1 § 4
             and the Commit 3 setup script) and the
             checkout-resolution code in this route. If the setup
             script wrote 'pro_usd_monthly' but the route requests
             'pro-usd-monthly', no price is found and checkout 500s.
    Ignores: the actual price amount or Stripe-side recurring
             interval — those are pinned by the setup script.
    """
    client = _authed_client(isolated_app)
    with mock.patch("web.app.stripe.Price.list") as mock_list, \
         mock.patch("web.app.stripe.checkout.Session.create") as mock_create:
        mock_list.return_value = mock.MagicMock(
            data=[_mock_stripe_price(expected_lookup_key)]
        )
        mock_create.return_value = _mock_stripe_session()
        resp = client.get(
            f"/upgrade?tier={tier}&interval={interval}&currency={currency}"
        )

    assert resp.status_code == 303, f"failed for {expected_lookup_key}: {resp.data}"
    mock_list.assert_called_once_with(lookup_keys=[expected_lookup_key], limit=1)


def test_missing_price_returns_500(isolated_app):
    """If Stripe.Price.list returns empty (the lookup_key isn't
    populated), the route 500s loudly so the operator notices the
    drift.

    Catches: a regression that silently falls back to a different
             price, or 200s with no checkout URL.
    Ignores: the error message wording.
    """
    client = _authed_client(isolated_app)
    with mock.patch("web.app.stripe.Price.list") as mock_list, \
         mock.patch("web.app.stripe.checkout.Session.create") as mock_create:
        mock_list.return_value = mock.MagicMock(data=[])
        resp = client.get("/upgrade?tier=pro&interval=monthly")
    assert resp.status_code == 500
    mock_create.assert_not_called()
