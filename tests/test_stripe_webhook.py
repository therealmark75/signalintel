"""
Tests for POST /webhooks/stripe (Phase 2 Commit 4).

Test path: synthetic Stripe-signed payloads constructed in-process with
HMAC-SHA256 over `{timestamp}.{payload}` keyed by a test webhook secret.
No Stripe network calls, no `stripe listen`. The runtime end-to-end
(stripe listen → Flask) is a deploy-time concern, not a unit gate.

Isolation: each test uses a tmp_path SQLite DB; web/app.py reads
DATABASE_PATH per-request, so monkeypatching the module-level binding
redirects every webhook call into the temp DB. The live
data/trading_system.db is never touched.

P15 contract for the whole file:
  Catches — every change to the signature-verification, idempotency,
            tier-flip, or cancellation-handling logic that would alter
            the documented behaviour of the endpoint.
  Ignores — Stripe-side delivery semantics (retry timing, signature
            tolerance windows), the upstream checkout-creation flow
            (Commit 5), and entitlement evaluation downstream of the
            users.tier flip (covered by tests/test_entitlements.py).
"""
import hashlib
import hmac
import json
import sqlite3
import time
from unittest import mock

import pytest


TEST_WEBHOOK_SECRET = "whsec_test_signalintel_unit_tests_only_aaaaaa"


# ── helpers ────────────────────────────────────────────────────────────


def sign_payload(event_dict, secret=TEST_WEBHOOK_SECRET):
    """Mimic Stripe's webhook signature header.

    Stripe signs `{timestamp}.{payload}` with HMAC-SHA256 keyed by the
    endpoint's signing secret. The header format is `t=<ts>,v1=<sig>`.
    """
    payload = json.dumps(event_dict, separators=(",", ":"))
    timestamp = int(time.time())
    signed = f"{timestamp}.{payload}".encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    header = f"t={timestamp},v1={sig}"
    return payload.encode("utf-8"), header


def make_checkout_completed_event(
    *, event_id, user_id, customer_id, subscription_id
):
    # The top-level "object": "event" is required — stripe.Webhook.construct_event
    # reads it via attribute access to discriminate v1 vs v2 event payloads.
    return {
        "id": event_id,
        "object": "event",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_aaaaaa",
                "object": "checkout.session",
                "client_reference_id": str(user_id),
                "customer": customer_id,
                "subscription": subscription_id,
                "mode": "subscription",
            }
        },
    }


def make_subscription_deleted_event(*, event_id, subscription_id, period_end_unix):
    return {
        "id": event_id,
        "object": "event",
        "type": "customer.subscription.deleted",
        "data": {
            "object": {
                "id": subscription_id,
                "object": "subscription",
                "status": "canceled",
                "ended_at": period_end_unix,
                "current_period_end": period_end_unix,
            }
        },
    }


def make_stripe_subscription_for_lookup(lookup_key, period_end_unix):
    """Construct a stripe.Subscription StripeObject for Subscription.retrieve mocks."""
    import stripe

    tier = lookup_key.split("_")[0]
    currency = lookup_key.split("_")[1]
    interval = lookup_key.split("_")[2].rstrip("ly")  # "monthly" → "month", "annual" → "annua" (don't use this)
    # Map literally to avoid rstrip pitfalls:
    interval_map = {"monthly": "month", "annual": "year"}
    interval = interval_map[lookup_key.split("_")[2]]

    return stripe.Subscription.construct_from(
        {
            "id": "sub_test_xxx",
            "object": "subscription",
            "items": {
                "object": "list",
                "data": [
                    {
                        "id": "si_test_xxx",
                        "object": "subscription_item",
                        # Per the 2025-03-31 API shape, current_period_end
                        # lives on the item, not the subscription.
                        "current_period_end": period_end_unix,
                        "price": {
                            "id": "price_test_xxx",
                            "object": "price",
                            "lookup_key": lookup_key,
                            "currency": currency,
                            "recurring": {"interval": interval},
                            "metadata": {
                                "tier": tier,
                                "currency": currency,
                                "interval": interval,
                            },
                        },
                    }
                ],
            },
        },
        "sk_test_unused",
    )


# ── fixtures ───────────────────────────────────────────────────────────


@pytest.fixture
def isolated_app(tmp_path, monkeypatch):
    """Flask test client backed by a temp DB with both schemas applied.

    The webhook reads DATABASE_PATH per-request, so a monkeypatched
    module-level binding redirects every webhook call into the temp DB.
    STRIPE_WEBHOOK_SECRET is patched to a known test value so signed
    payloads in this file can be constructed deterministically.
    """
    from database.db import (
        get_connection,
        initialise_subscription_events_schema,
        initialise_user_schema,
    )

    db_path = str(tmp_path / "webhook_test.db")
    initialise_user_schema(db_path)
    initialise_subscription_events_schema(db_path)

    import web.app

    monkeypatch.setattr(web.app, "DATABASE_PATH", db_path)
    monkeypatch.setattr(web.app, "STRIPE_WEBHOOK_SECRET", TEST_WEBHOOK_SECRET)

    web.app.app.config["TESTING"] = True
    with web.app.app.test_client() as c:
        yield {"client": c, "db_path": db_path, "get_connection": get_connection}


def _insert_user(db_path, *, user_id=None, tier="free", subscription_id=None):
    """Insert a test user. Returns user_id."""
    from werkzeug.security import generate_password_hash
    from database.db import create_user, get_connection

    pw = generate_password_hash("pw", method="pbkdf2:sha256")
    uid = create_user(db_path, f"user{user_id or ''}", f"user{user_id or ''}@x", pw)
    conn = get_connection(db_path)
    if tier != "free":
        conn.execute("UPDATE users SET tier=? WHERE id=?", (tier, uid))
    if subscription_id:
        conn.execute(
            "UPDATE users SET stripe_subscription_id=? WHERE id=?",
            (subscription_id, uid),
        )
    conn.commit()
    conn.close()
    return uid


def _fetch_user(db_path, user_id):
    from database.db import get_connection

    conn = get_connection(db_path)
    row = conn.execute(
        "SELECT id, tier, is_active, stripe_customer_id, "
        "stripe_subscription_id, tier_effective_until "
        "FROM users WHERE id=?",
        (user_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def _fetch_subscription_event(db_path, event_id):
    from database.db import get_connection

    conn = get_connection(db_path)
    row = conn.execute(
        "SELECT * FROM subscription_events WHERE stripe_event_id=?",
        (event_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ── tests ──────────────────────────────────────────────────────────────


def test_rejects_invalid_signature(isolated_app):
    """Bad signature → 400, no DB writes.

    Catches: any future relaxation of construct_event() — e.g.
             swallowing SignatureVerificationError and accepting
             unsigned payloads, which would let anyone with the
             webhook URL flip arbitrary tiers.
    Ignores: the exact 4xx code Stripe's own libraries return on
             malformed payloads — only the 'reject' verdict matters.
    """
    client = isolated_app["client"]
    db_path = isolated_app["db_path"]

    event = make_checkout_completed_event(
        event_id="evt_bad_sig",
        user_id=1,
        customer_id="cus_x",
        subscription_id="sub_x",
    )
    payload = json.dumps(event).encode("utf-8")

    resp = client.post(
        "/webhooks/stripe",
        data=payload,
        headers={
            "Stripe-Signature": "t=12345,v1=deadbeefdeadbeefdeadbeefdeadbeef",
            "Content-Type": "application/json",
        },
    )
    assert resp.status_code == 400, f"expected 400 on bad sig, got {resp.status_code}"
    # Nothing should have been written to subscription_events
    assert _fetch_subscription_event(db_path, "evt_bad_sig") is None


def test_rejects_missing_signature_header(isolated_app):
    """No Stripe-Signature header → 400.

    Catches: a regression where the route reads the header with a
             permissive default and falls through to construct_event
             with empty string, which the SDK still rejects but the
             explicit 400 path is the documented contract.
    Ignores: whether construct_event raises ValueError or
             SignatureVerificationError on the empty header — both are
             caught.
    """
    client = isolated_app["client"]

    event = make_checkout_completed_event(
        event_id="evt_no_sig", user_id=1, customer_id="cus_x", subscription_id="sub_x"
    )
    payload = json.dumps(event).encode("utf-8")

    resp = client.post(
        "/webhooks/stripe",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 400


def test_conversion_event_flips_tier_and_writes_columns(isolated_app):
    """checkout.session.completed flips users.tier and writes the 3 Stripe columns.

    Catches: regression in tier resolution (lookup_key parsing,
             metadata validation), or in the column-write set
             (forgetting any of stripe_customer_id /
             stripe_subscription_id / tier_effective_until).
    Ignores: the exact tier_effective_until timestamp seconds — the
             test fixes a known Unix timestamp and checks the ISO
             starts with the matching date.
    """
    client = isolated_app["client"]
    db_path = isolated_app["db_path"]

    uid = _insert_user(db_path, tier="free")
    before = _fetch_user(db_path, uid)
    assert before["tier"] == "free"
    assert before["stripe_customer_id"] is None
    assert before["stripe_subscription_id"] is None
    assert before["tier_effective_until"] is None

    event = make_checkout_completed_event(
        event_id="evt_convert_1",
        user_id=uid,
        customer_id="cus_test_aaa",
        subscription_id="sub_test_bbb",
    )
    payload, sig = sign_payload(event)

    period_end_unix = 1748736000  # 2025-06-01 00:00:00 UTC, fixed
    mocked_sub = make_stripe_subscription_for_lookup("pro_usd_monthly", period_end_unix)

    with mock.patch("web.app.stripe.Subscription.retrieve", return_value=mocked_sub):
        resp = client.post(
            "/webhooks/stripe",
            data=payload,
            headers={"Stripe-Signature": sig, "Content-Type": "application/json"},
        )

    assert resp.status_code == 200, resp.data
    body = resp.get_json()
    assert body["status"] == "ok"

    after = _fetch_user(db_path, uid)
    assert after["tier"] == "pro", f"tier did not flip: {after}"
    assert after["stripe_customer_id"] == "cus_test_aaa"
    assert after["stripe_subscription_id"] == "sub_test_bbb"
    assert after["tier_effective_until"] is not None
    assert after["tier_effective_until"].startswith("2025-06-01"), (
        f"unexpected tier_effective_until: {after['tier_effective_until']}"
    )
    # is_active untouched by conversion
    assert after["is_active"] == 1

    # Audit row recorded
    audit = _fetch_subscription_event(db_path, "evt_convert_1")
    assert audit["status"] == "processed"
    assert audit["tier_before"] == "free"
    assert audit["tier_after"] == "pro"


def test_duplicate_event_is_no_op(isolated_app):
    """Delivering the same stripe_event_id twice flips tier once.

    Catches: a regression where the IntegrityError branch silently
             continues into the handler, which would double-write
             columns and (more importantly in future commits) charge
             a re-flip with stale data.
    Ignores: the exact response body shape on duplicate — only the
             single tier flip is asserted.
    """
    client = isolated_app["client"]
    db_path = isolated_app["db_path"]

    uid = _insert_user(db_path, tier="free")

    event = make_checkout_completed_event(
        event_id="evt_dup_xyz",
        user_id=uid,
        customer_id="cus_dup",
        subscription_id="sub_dup",
    )
    payload, sig = sign_payload(event)

    period_end_unix = 1748736000
    mocked_sub = make_stripe_subscription_for_lookup(
        "elite_gbp_annual", period_end_unix
    )

    call_count = {"n": 0}

    def _counting_retrieve(*args, **kwargs):
        call_count["n"] += 1
        return mocked_sub

    with mock.patch("web.app.stripe.Subscription.retrieve", side_effect=_counting_retrieve):
        r1 = client.post(
            "/webhooks/stripe",
            data=payload,
            headers={"Stripe-Signature": sig, "Content-Type": "application/json"},
        )
        # Identical second delivery (same event id, freshly signed
        # because timestamp differs — Stripe redelivers with the same
        # event id but possibly different signature timestamps).
        payload2, sig2 = sign_payload(event)
        r2 = client.post(
            "/webhooks/stripe",
            data=payload2,
            headers={"Stripe-Signature": sig2, "Content-Type": "application/json"},
        )

    assert r1.status_code == 200
    assert r2.status_code == 200
    body2 = r2.get_json()
    assert body2["status"] == "duplicate", f"second delivery should report duplicate, got {body2}"

    # Subscription.retrieve called exactly once — second delivery
    # short-circuited at the idempotency lock before the handler ran.
    assert call_count["n"] == 1, (
        f"duplicate event must not invoke Stripe.Subscription.retrieve "
        f"(called {call_count['n']} times — handler ran twice)"
    )

    # Only one row in subscription_events for this event id
    after = _fetch_user(db_path, uid)
    assert after["tier"] == "elite"  # flipped once, by the first delivery


def test_cancellation_sets_tier_effective_until_only(isolated_app):
    """customer.subscription.deleted sets tier_effective_until.

    Locked: do NOT change users.tier, do NOT change users.is_active.
    Just refresh tier_effective_until to the subscription's end date.

    Catches: any change that drops tier to 'free' or deactivates the
             user on cancellation — the documented "ride out the
             period" contract.
    Ignores: the downgrade-to-free sweep that runs when the period
             actually expires — that is a separate concern.
    """
    client = isolated_app["client"]
    db_path = isolated_app["db_path"]

    uid = _insert_user(
        db_path, tier="elite", subscription_id="sub_cancel_zzz"
    )
    # Set initial tier_effective_until to a known prior value so we can
    # see the refresh.
    from database.db import get_connection as _gc

    conn = _gc(db_path)
    conn.execute(
        "UPDATE users SET tier_effective_until=?, stripe_customer_id=? WHERE id=?",
        ("2025-05-01T00:00:00", "cus_cancel_zzz", uid),
    )
    conn.commit()
    conn.close()

    period_end_unix = 1748736000  # 2025-06-01 00:00:00 UTC
    event = make_subscription_deleted_event(
        event_id="evt_cancel_1",
        subscription_id="sub_cancel_zzz",
        period_end_unix=period_end_unix,
    )
    payload, sig = sign_payload(event)

    resp = client.post(
        "/webhooks/stripe",
        data=payload,
        headers={"Stripe-Signature": sig, "Content-Type": "application/json"},
    )
    assert resp.status_code == 200, resp.data
    body = resp.get_json()
    assert body["status"] == "ok"

    after = _fetch_user(db_path, uid)
    # Locked: tier unchanged, is_active unchanged.
    assert after["tier"] == "elite", (
        f"cancellation must NOT drop tier — locked decision. Got tier={after['tier']!r}"
    )
    assert after["is_active"] == 1, (
        f"cancellation must NOT deactivate — locked decision. "
        f"Got is_active={after['is_active']!r}"
    )
    # tier_effective_until refreshed to the new period end.
    assert after["tier_effective_until"].startswith("2025-06-01"), (
        f"tier_effective_until not refreshed: {after['tier_effective_until']}"
    )
    # Stripe id preserved.
    assert after["stripe_subscription_id"] == "sub_cancel_zzz"

    audit = _fetch_subscription_event(db_path, "evt_cancel_1")
    assert audit["status"] == "processed"
    assert audit["tier_before"] == "elite"
    assert audit["tier_after"] == "elite", (
        "tier_after must equal tier_before on cancellation — tier deliberately unchanged"
    )


def test_unhandled_event_type_logged_and_skipped(isolated_app):
    """Events we don't handle yet land in subscription_events with status='skipped'.

    Catches: a regression where unhandled events silently 200 without
             being logged, losing the audit trail. The webhook arc
             will grow to handle more events over time; status='skipped'
             rows are how operators discover what's coming through that
             we haven't wired yet.
    Ignores: the specific event type used here (invoice.paid is a
             plausible future event, but the test isn't asserting
             anything about invoice handling).
    """
    client = isolated_app["client"]
    db_path = isolated_app["db_path"]

    event = {
        "id": "evt_unhandled_qqq",
        "object": "event",
        "type": "invoice.paid",
        "data": {"object": {"id": "in_test_xxx"}},
    }
    payload, sig = sign_payload(event)

    resp = client.post(
        "/webhooks/stripe",
        data=payload,
        headers={"Stripe-Signature": sig, "Content-Type": "application/json"},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "skipped"

    audit = _fetch_subscription_event(db_path, "evt_unhandled_qqq")
    assert audit["status"] == "skipped"
    # No tier touched, no error.
    assert audit["tier_before"] is None
    assert audit["tier_after"] is None
    assert audit["error_message"] is None


def test_handler_failure_marks_row_failed_and_returns_200(isolated_app):
    """Handler exception → row marked status='failed', response still 200.

    Stripe retries on non-2xx. If a handler bug keeps throwing, retries
    just cause more failed rows for the same deterministic error. 200
    + audit log is the right tradeoff.

    Catches: a regression where the exception escapes the route
             handler (500 to Stripe → retry storm) or where the
             failed status isn't written.
    Ignores: the exact error message format — only that it's
             non-empty and bounded.
    """
    client = isolated_app["client"]
    db_path = isolated_app["db_path"]

    # No user with this user_id → handler raises ValueError.
    event = make_checkout_completed_event(
        event_id="evt_handler_fail",
        user_id=99999,
        customer_id="cus_xxx",
        subscription_id="sub_xxx",
    )
    payload, sig = sign_payload(event)
    period_end_unix = 1748736000
    mocked_sub = make_stripe_subscription_for_lookup(
        "pro_usd_monthly", period_end_unix
    )

    with mock.patch(
        "web.app.stripe.Subscription.retrieve", return_value=mocked_sub
    ):
        resp = client.post(
            "/webhooks/stripe",
            data=payload,
            headers={"Stripe-Signature": sig, "Content-Type": "application/json"},
        )

    assert resp.status_code == 200, (
        "handler failures must still return 200 to prevent Stripe retry storms; "
        f"got {resp.status_code}"
    )
    body = resp.get_json()
    assert body["status"] == "failed"

    audit = _fetch_subscription_event(db_path, "evt_handler_fail")
    assert audit["status"] == "failed"
    assert audit["error_message"] is not None
    assert "user_id=99999" in audit["error_message"]


def test_missing_webhook_secret_returns_500(isolated_app, monkeypatch):
    """If STRIPE_WEBHOOK_SECRET is empty, the route returns 500.

    Catches: a misconfigured production deploy where the secret env
             wasn't set — the endpoint would silently accept unsigned
             payloads if construct_event was called with an empty
             string. The 500 short-circuit ensures the misconfiguration
             is visible.
    Ignores: the rest of the request path — no signature verification
             attempted, no DB writes.
    """
    import web.app

    monkeypatch.setattr(web.app, "STRIPE_WEBHOOK_SECRET", "")

    client = isolated_app["client"]
    event = make_checkout_completed_event(
        event_id="evt_no_secret",
        user_id=1,
        customer_id="cus_x",
        subscription_id="sub_x",
    )
    payload, sig = sign_payload(event)

    resp = client.post(
        "/webhooks/stripe",
        data=payload,
        headers={"Stripe-Signature": sig, "Content-Type": "application/json"},
    )
    assert resp.status_code == 500
