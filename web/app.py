import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrapers.legal_risk_scraper import get_legal_risk, fetch_legal_risk, save_legal_risk
# web/app.py - Phase 5 full web dashboard
import sys, json, sqlite3, requests as http_requests
from pathlib import Path
from datetime import datetime
from functools import wraps
import stripe
from flask import (Flask, jsonify, render_template, request,
                   redirect, url_for, session, flash, g)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.constants import DATABASE_PATH, MIN_PRICE_FOR_SIGNAL, SCORING_ENGINE_VERSION
from database.db import (
    get_connection, get_latest_screener, get_recent_insiders,
    get_cluster_signals, get_top_signals, get_signal_summary,
    get_ticker_sentiment, initialise_user_schema,
    initialise_subscription_events_schema,
    create_user, get_user_by_username, get_user_by_email, get_user_by_id,
    get_watchlist, get_watchlists_meta, get_or_create_default_watchlist,
    create_watchlist, rename_watchlist, delete_watchlist,
    add_to_watchlist, remove_from_watchlist,
    toggle_watchlist_alerts,
    create_default_watchlist, is_default_watchlist,
    get_top_signals_of_day, generate_top_signals_of_day,
    signal_scores_projection,
)
from config.tiers import can_create_watchlist, watchlist_limit, get_tier, next_tier
from config.pricing import LAUNCH_PRICING, ANNUAL_DISCOUNT_PCT, TIER_FEATURES
from config.entitlements import (
    effective_tier, can_view_penny_signals, can_view_score_for_ticker,
    strip_scores_for_non_elite, filter_proprietary_flags_for_non_elite,
    strip_subscores_for_non_elite,
)
from config.settings import FLASK_SECRET_KEY, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
from signals.signal_labels import tier_short
from signals.components import COMPONENTS, to_json_dict, sortable_columns

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = FLASK_SECRET_KEY
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.config["SESSION_COOKIE_SECURE"]   = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[],
    storage_uri="memory://",
)

# Ensure user tables exist
initialise_user_schema(DATABASE_PATH)
initialise_subscription_events_schema(DATABASE_PATH)

# Wire Stripe SDK with the secret key (empty in dev until populated locally).
if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

# Ensure contact_submissions table exists
def _init_contact_table():
    conn = get_connection(DATABASE_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS contact_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()
_init_contact_table()

def _init_penny_tables():
    conn = get_connection(DATABASE_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS penny_stock_of_day (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            ticker TEXT NOT NULL,
            composite_score REAL,
            rating TEXT,
            selected_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()
_init_penny_tables()


def _init_market_tables():
    conn = get_connection(DATABASE_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS market_history (
            symbol  TEXT NOT NULL,
            date    TEXT NOT NULL,
            open    REAL,
            high    REAL,
            low     REAL,
            close   REAL,
            volume  REAL,
            PRIMARY KEY (symbol, date)
        )
    """)
    conn.commit()
    conn.close()
_init_market_tables()

from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def _send_telegram(msg):
    try:
        http_requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg},
            timeout=5,
        )
    except Exception:
        pass


# ── Auth helpers ──────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            # Return JSON 401 for API routes, redirect for page routes
            if request.path.startswith('/api/'):
                return jsonify({"error": "session_expired",
                                "message": "Your session has expired. Please log in again.",
                                "login_url": "/login"}), 401
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

_USER_UNSET = object()  # sentinel: distinguishes "not loaded" from "loaded as None"


def current_user():
    """Return the current user row (dict) or None, memoised on flask.g.

    Per-request cache: every call within one request hits the DB at most
    once. A logged-out request loads None once and stays None for the
    request (no re-query on every call). A logged-in request loads the
    row once even if multiple call sites (route handler, context
    processor, helpers) need it. Flask gives a fresh `g` per request so
    the memo is naturally scoped and needs no teardown.

    Return contract unchanged: dict row for authenticated, None for
    unauthenticated. No caller change required.
    """
    cached = getattr(g, "user", _USER_UNSET)
    if cached is not _USER_UNSET:
        return cached
    if "user_id" in session:
        loaded = get_user_by_id(DATABASE_PATH, session["user_id"])
    else:
        loaded = None
    g.user = loaded
    return loaded


@app.context_processor
def _inject_nav_tier():
    """Inject the resolver-computed effective tier as `nav_tier` into
    every template render context.

    Rides on the g-memoised current_user(), so on an authenticated
    request that already loaded the user, this is a cache read, not a
    fresh DB query. Fail-closes to 'free' on logged-out requests via
    effective_tier(None) -> 'free'; _nav.html only renders the badge
    inside {% if user %}, so the 'free' default never leaks to
    unauthenticated visitors. Runs on every render by design so every
    nav-rendering template gets the same effective value with zero
    per-route plumbing.
    """
    return {"nav_tier": effective_tier(current_user())}


@app.context_processor
def inject_component_registry():
    """Inject the canonical component registry into every template render.

    `components` is the registry tuple (Steps 11-15 templates iterate it);
    `components_json` is the same data pre-serialised as a JSON string for
    the Step 10 ticker.html JS shim (assigned to window.COMPONENTS_DATA).
    Single source: signals.components. No try/except: a registry that
    fails to serialise should fail loud at render, not silently.
    """
    return {
        "components": COMPONENTS,
        "components_json": json.dumps(to_json_dict()),
    }

def db_query(sql, params=()):
    conn = get_connection(DATABASE_PATH)
    cur  = conn.cursor()
    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# ── Page routes ───────────────────────────────────

@app.route("/")
@login_required
def index():
    # Phase 2A: logged-in users go straight to the new /dashboard. The historical
    # index() body below is preserved per the Phase 2A spec ("add the redirect
    # branch only. Do not remove or rewrite the existing / route logic") and is
    # unreachable while this redirect is in place.
    return redirect(url_for("dashboard"))

    user = current_user()
    # Generate today's top signals if not done yet
    today = datetime.now().strftime("%Y-%m-%d")
    top = get_top_signals_of_day(DATABASE_PATH, today)
    if not top:
        top = generate_top_signals_of_day(DATABASE_PATH)
    conn = get_connection(DATABASE_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(DISTINCT ticker) as total_tickers,
               MAX(scored_at) as last_scored
        FROM signal_scores
    """)
    stats = dict(cur.fetchone())
    conn.close()
    wl_rows = db_query("SELECT DISTINCT ticker FROM watchlists WHERE user_id=?", (user["id"],)) if user else []
    watchlist_tickers = {r["ticker"] for r in wl_rows}
    return render_template("index.html", user=user, top_signals=top,
                           total_tickers=stats["total_tickers"],
                           last_scored=stats["last_scored"],
                           watchlist_tickers=watchlist_tickers)


@app.route("/login", methods=["GET","POST"])
@limiter.limit("10 per minute", methods=["POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","")
        user = get_user_by_username(DATABASE_PATH, username)
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"]  = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("index"))
        flash("Invalid username or password")
    return render_template("login.html")


@app.route("/register", methods=["GET","POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username","").strip()
        email    = request.form.get("email","").strip()
        password = request.form.get("password","")
        confirm  = request.form.get("confirm","")
        if not username or not email or not password:
            flash("All fields required")
        elif password != confirm:
            flash("Passwords do not match")
        elif len(password) < 8:
            flash("Password must be at least 8 characters")
        elif get_user_by_username(DATABASE_PATH, username):
            flash("Username already taken")
        elif get_user_by_email(DATABASE_PATH, email):
            flash("An account with that email already exists")
        else:
            pw_hash = generate_password_hash(password, method='pbkdf2:sha256')
            # Naive UTC ISO matches _now() in config/entitlements.py so
            # _parse_utc_iso round-trips and the 7-day overlay starts here.
            trial_started_at = datetime.utcnow().isoformat()
            user_id = create_user(DATABASE_PATH, username, email, pw_hash,
                                  trial_started_at=trial_started_at)
            # Every new user gets a default watchlist immediately on signup.
            create_default_watchlist(DATABASE_PATH, user_id)
            session["user_id"]  = user_id
            session["username"] = username
            return redirect(url_for("index"))
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ──────────────────────────────────────────────────────────────────────
# Stripe webhook (Phase 2 Commit 4)
# ──────────────────────────────────────────────────────────────────────
#
# Authenticated by Stripe-Signature header (HMAC-SHA256 over
# `{timestamp}.{payload}` keyed by STRIPE_WEBHOOK_SECRET). NOT by Flask
# session. The webhook is called by Stripe's servers, not by a browser.
#
# Idempotency: subscription_events.stripe_event_id has a UNIQUE
# constraint. The first action of every webhook is to INSERT that row
# inside a try/except sqlite3.IntegrityError. Duplicate Stripe deliveries
# fail the INSERT and short-circuit to a 200 no-op without touching the
# users table.
#
# Cancellation contract (locked): RIDE OUT THE PERIOD. On
# customer.subscription.deleted we set tier_effective_until to the
# subscription's end date and do NOT change users.tier or users.is_active.
# The downgrade-to-free sweep when the period actually expires is its own
# concern (deferred, see docs/stripe_billing_phase1.md § 8).

def _resolve_tier_from_subscription(subscription):
    """Resolve (tier, tier_effective_until_iso) from a Stripe Subscription.

    Reads lookup_key from the subscription's first item's price.
    lookup_key format is '<tier>_<currency>_<interval>' so tier is
    lookup_key.split('_')[0]. Validates against price.metadata.tier
    as belt-and-braces, catches Stripe-side fat-fingers where a price
    was created with the wrong lookup_key.
    """
    item = subscription["items"]["data"][0]
    price = item["price"]
    try:
        lookup_key = price["lookup_key"]
    except (KeyError, TypeError):
        lookup_key = None
    if not lookup_key:
        raise ValueError(
            f"subscription {subscription['id']} price has no lookup_key: "
            f"webhook cannot resolve tier without it"
        )
    tier_from_lookup = lookup_key.split("_")[0]

    try:
        metadata_tier = price["metadata"]["tier"]
    except (KeyError, TypeError):
        metadata_tier = None
    if metadata_tier and metadata_tier != tier_from_lookup:
        raise ValueError(
            f"price {price['id']} has inconsistent tier: "
            f"lookup_key={lookup_key} → {tier_from_lookup}, "
            f"metadata.tier={metadata_tier}"
        )

    if tier_from_lookup not in ("pro", "elite"):
        raise ValueError(
            f"price {price['id']} lookup_key {lookup_key!r} "
            f"resolves to unknown tier {tier_from_lookup!r}"
        )

    # As of API version 2025-03-31, current_period_end lives on each
    # subscription item, not on the top-level Subscription. We have a
    # single item per subscription so reading items.data[0] is correct.
    period_end_iso = datetime.utcfromtimestamp(
        item["current_period_end"]
    ).isoformat()
    return tier_from_lookup, period_end_iso


def _handle_checkout_completed(conn, event):
    """First successful payment: flip user tier + write Stripe IDs.

    The checkout session carries client_reference_id (our user_id),
    customer (stripe_customer_id), and subscription (stripe_subscription_id).
    We fetch the full subscription to read lookup_key, then resolve tier.

    Returns (tier_before, tier_after).
    """
    sess = event["data"]["object"]
    user_id_raw = sess.get("client_reference_id") if hasattr(sess, "get") else None
    if user_id_raw is None:
        try:
            user_id_raw = sess["client_reference_id"]
        except (KeyError, TypeError):
            user_id_raw = None
    if not user_id_raw:
        raise ValueError(
            f"checkout.session.completed missing client_reference_id "
            f"(session_id={sess.get('id') if hasattr(sess, 'get') else sess['id']})"
        )
    user_id = int(user_id_raw)

    try:
        sub_id = sess["subscription"]
    except (KeyError, TypeError):
        sub_id = None
    if not sub_id:
        raise ValueError("checkout.session.completed missing subscription id")
    try:
        customer_id = sess["customer"]
    except (KeyError, TypeError):
        customer_id = None

    subscription = stripe.Subscription.retrieve(
        sub_id, expand=["items.data.price"]
    )
    new_tier, period_end_iso = _resolve_tier_from_subscription(subscription)

    cur = conn.cursor()
    row = cur.execute(
        "SELECT tier FROM users WHERE id = ?", (user_id,)  # noqa: tier-read (webhook audit: capture tier_before pre-flip for subscription_events)
    ).fetchone()
    if row is None:
        raise ValueError(
            f"checkout.session.completed user_id={user_id} not found in users table"
        )
    tier_before = row["tier"]

    cur.execute(
        """
        UPDATE users
        SET tier = ?,
            stripe_customer_id = ?,
            stripe_subscription_id = ?,
            tier_effective_until = ?
        WHERE id = ?
        """,
        (new_tier, customer_id, sub_id, period_end_iso, user_id),
    )
    conn.commit()
    return tier_before, new_tier


def _handle_subscription_deleted(conn, event):
    """Subscription ended/canceled. RIDE OUT semantics.

    Set tier_effective_until to the actual subscription end (ended_at
    if present, else current_period_end). Do NOT change users.tier.
    Do NOT change users.is_active. The downgrade-to-free sweep is a
    separate concern.

    Returns (tier_before, tier_after). tier_after == tier_before
    because tier is deliberately unchanged.
    """
    sub = event["data"]["object"]
    sub_id = sub["id"]

    end_unix = None
    try:
        end_unix = sub["ended_at"]
    except (KeyError, TypeError):
        pass
    if not end_unix:
        # Fallback to the per-item current_period_end (new API shape:
        # current_period_* moved off Subscription onto each item).
        try:
            end_unix = sub["items"]["data"][0]["current_period_end"]
        except (KeyError, TypeError):
            pass
    if not end_unix:
        raise ValueError(
            f"customer.subscription.deleted {sub_id} missing both "
            f"ended_at and current_period_end"
        )
    end_iso = datetime.utcfromtimestamp(end_unix).isoformat()

    cur = conn.cursor()
    row = cur.execute(
        "SELECT id, tier FROM users WHERE stripe_subscription_id = ?",  # noqa: tier-read (webhook audit: capture tier_before pre-flip for subscription_events)
        (sub_id,),
    ).fetchone()
    if row is None:
        raise ValueError(
            f"customer.subscription.deleted sub_id={sub_id} "
            f"not matched to any user"
        )
    tier_before = row["tier"]

    cur.execute(
        """
        UPDATE users
        SET tier_effective_until = ?
        WHERE stripe_subscription_id = ?
        """,
        (end_iso, sub_id),
    )
    conn.commit()
    return tier_before, tier_before


@app.route("/webhooks/stripe", methods=["POST"])
def stripe_webhook():
    """Stripe webhook endpoint. Signature-verified, idempotent.

    Returns:
      400 if signature is missing/invalid.
      500 if STRIPE_WEBHOOK_SECRET is empty (misconfiguration).
      200 in every other case, including handler failures (logged
          to subscription_events.status='failed' for forensics).
          Returning 200 on handler failure prevents Stripe from
          retrying a deterministic bug; the failed row in our audit
          log surfaces it for operator review.
    """
    if not STRIPE_WEBHOOK_SECRET:
        return jsonify({"error": "webhook secret not configured"}), 500

    sig_header = request.headers.get("Stripe-Signature", "")
    payload = request.get_data()

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return jsonify({"error": "invalid signature"}), 400

    event_id = event["id"]
    event_type = event["type"]

    conn = get_connection(DATABASE_PATH)
    try:
        cur = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO subscription_events
                  (stripe_event_id, event_type, received_at, raw_payload)
                VALUES (?, ?, ?, ?)
                """,
                (
                    event_id,
                    event_type,
                    datetime.utcnow().isoformat(),
                    payload.decode("utf-8"),
                ),
            )
            event_row_id = cur.lastrowid
            conn.commit()
        except sqlite3.IntegrityError:
            return jsonify({"status": "duplicate", "event_id": event_id}), 200

        try:
            if event_type == "checkout.session.completed":
                tier_before, tier_after = _handle_checkout_completed(conn, event)
            elif event_type == "customer.subscription.deleted":
                tier_before, tier_after = _handle_subscription_deleted(conn, event)
            else:
                cur.execute(
                    "UPDATE subscription_events "
                    "SET status=?, processed_at=? WHERE id=?",
                    ("skipped", datetime.utcnow().isoformat(), event_row_id),
                )
                conn.commit()
                return (
                    jsonify({"status": "skipped", "event_type": event_type}),
                    200,
                )

            cur.execute(
                """
                UPDATE subscription_events
                SET status=?, processed_at=?, tier_before=?, tier_after=?
                WHERE id=?
                """,
                (
                    "processed",
                    datetime.utcnow().isoformat(),
                    tier_before,
                    tier_after,
                    event_row_id,
                ),
            )
            conn.commit()
            return jsonify({"status": "ok", "event_type": event_type}), 200

        except Exception as e:
            cur.execute(
                """
                UPDATE subscription_events
                SET status=?, processed_at=?, error_message=?
                WHERE id=?
                """,
                (
                    "failed",
                    datetime.utcnow().isoformat(),
                    str(e)[:500],
                    event_row_id,
                ),
            )
            conn.commit()
            return jsonify({"status": "failed", "error": str(e)}), 200
    finally:
        conn.close()


# ──────────────────────────────────────────────────────────────────────
# Stripe Checkout creation (Phase 2 Commit 5)
# ──────────────────────────────────────────────────────────────────────
#
# GET /upgrade?tier=<pro|elite>&interval=<monthly|annual> creates a
# Stripe Checkout Session for the logged-in user and 303-redirects to
# Stripe's hosted page. The conversion event lands on the webhook
# (Commit 4); the thread tying it back is client_reference_id, which
# is set to str(session["user_id"]) here.
#
# Currency resolution precedence (highest first):
#   1. Explicit ?currency=gbp|usd query override (lets us force GBP
#      for marketing experiments and lets tests cover both branches
#      without infrastructure).
#   2. Cloudflare CF-IPCountry header (free + accurate when the app
#      sits behind Cloudflare; absent in dev).
#   3. Accept-Language containing 'en-GB' (rough dev fallback when
#      Cloudflare isn't terminating).
#   4. Default 'usd'.
# UK → GBP, everything else → USD per locked policy.

_VALID_TIERS = ("pro", "elite")
_VALID_INTERVALS = ("monthly", "annual")


def _resolve_currency_from_request(req):
    """Two-letter currency code 'gbp' or 'usd'. See precedence above."""
    explicit = req.args.get("currency", "").lower()
    if explicit in ("gbp", "usd"):
        return explicit
    cf_country = req.headers.get("CF-IPCountry", "").upper()
    if cf_country == "GB":
        return "gbp"
    if cf_country:
        return "usd"
    accept_lang = req.headers.get("Accept-Language", "").lower()
    if "en-gb" in accept_lang:
        return "gbp"
    return "usd"


@app.route("/upgrade", methods=["GET"])
@login_required
@limiter.limit("10 per minute")
def upgrade():
    """Create a Stripe Checkout Session for the logged-in user.

    Validates tier + interval, resolves currency, looks up the
    matching Stripe Price by lookup_key, creates the session with
    client_reference_id = session['user_id'] (the load-bearing
    thread the webhook uses to identify the user), then redirects
    303 to the Stripe-hosted checkout URL. Stripe handles all card
    data; we never see it.
    """
    tier = request.args.get("tier", "").lower()
    interval = request.args.get("interval", "").lower()

    if tier not in _VALID_TIERS:
        return jsonify({"error": f"invalid tier: {tier!r}"}), 400
    if interval not in _VALID_INTERVALS:
        return jsonify({"error": f"invalid interval: {interval!r}"}), 400

    currency = _resolve_currency_from_request(request)
    lookup_key = f"{tier}_{currency}_{interval}"

    prices = stripe.Price.list(lookup_keys=[lookup_key], limit=1)
    if not prices.data:
        # The setup script (Commit 3) is meant to keep all 8 lookup_keys
        # populated; a missing one means a config drift or that someone
        # disabled the Price in Stripe Dashboard. Loud 500 so the
        # operator notices.
        return jsonify({"error": f"no Stripe price for lookup_key={lookup_key}"}), 500
    price = prices.data[0]

    user_id = session["user_id"]
    dashboard_url = url_for("dashboard", _external=True)

    checkout_session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price.id, "quantity": 1}],
        client_reference_id=str(user_id),
        success_url=dashboard_url + "?upgrade=success",
        cancel_url=dashboard_url + "?upgrade=cancel",
    )

    return redirect(checkout_session.url, code=303)


# ── /dashboard ───────────────────────────────────────────────────────────────
# Phase 2A (greenfield): 13-panel grid per docs/mockups/dashboard_restructure_v1.html.
# 2A delivers the 6 above-the-fold panels (Daily Summary, Top 5 Strong,
# Top 5 Bearish, Market State, Watchlist Preview, Discovery Themes) + the
# Elite tier-gating plumbing. 2B adds the Penny-Stock spotlight + 6 below-fold
# panels (Earnings, Dividends, Sector Performance, Rating Changes, Insider, News).
@app.route("/dashboard")
@login_required
def dashboard():
    user        = current_user()
    tier_key    = effective_tier(user)
    # Both tier_key (dashboard badge) and is_elite (Panel 7 gate) now
    # route through the resolver so trial overlay and (future) lazy
    # tier_effective_until expiry apply uniformly. BUG-001's "badge
    # reflects DB state" contract is satisfied because effective_tier
    # falls back to stored when no overlay applies.
    is_elite    = (effective_tier(user) == 'elite')

    # ── Live header context (dash-head subline) ──────────────────────────────
    meta_row = db_query("""
        SELECT MAX(scored_at)         AS last_scored,
               COUNT(DISTINCT ticker) AS ticker_count
        FROM signal_scores
        WHERE DATE(scored_at) = DATE((SELECT MAX(scored_at) FROM signal_scores))
    """)
    last_scored  = meta_row[0]["last_scored"]  if meta_row else None
    ticker_count = meta_row[0]["ticker_count"] if meta_row else 0

    # ── Panel 1: Daily Summary ──────────────────────────────────────────────
    UP_SET   = {"STRONG_BUY", "BUY", "STRONG_HOLD"}
    DOWN_SET = {"SELL", "STRONG_SELL", "WEAK_HOLD"}
    rc_rows = db_query("""
        SELECT old_rating, new_rating
        FROM rating_changes
        WHERE change_date >= datetime('now','-1 day')
    """)
    upgrades   = sum(1 for r in rc_rows
                     if r["new_rating"] in UP_SET and r["old_rating"] not in UP_SET)
    downgrades = sum(1 for r in rc_rows
                     if r["new_rating"] in DOWN_SET and r["old_rating"] not in DOWN_SET)

    mover = db_query("""
        SELECT ticker, change_pct FROM screener_snapshots
        WHERE scraped_at = (SELECT MAX(scraped_at) FROM screener_snapshots)
          AND change_pct IS NOT NULL
        ORDER BY ABS(change_pct) DESC LIMIT 1
    """)
    top_mover = mover[0] if mover else None

    earnings_today_row = db_query(
        "SELECT COUNT(*) AS n FROM earnings_calendar WHERE earnings_date = DATE('now')"
    )
    earnings_today = earnings_today_row[0]["n"] if earnings_today_row else 0

    vix_row = db_query(
        "SELECT close FROM market_history WHERE symbol = '^VIX' ORDER BY date DESC LIMIT 1"
    )
    vix_val = vix_row[0]["close"] if vix_row else None
    if vix_val is None:
        vix_label = None
    elif vix_val < 15:
        vix_label = "calm"
    elif vix_val <= 22:
        vix_label = "choppy"
    else:
        vix_label = "elevated"

    summary = {
        "upgrades":       upgrades,
        "downgrades":     downgrades,
        "top_mover":      top_mover,
        "earnings_today": earnings_today,
        "vix_val":        vix_val,
        "vix_label":      vix_label,
    }

    # ── Panels 2 / 3: Top 5 Strong + Top 5 Bearish ──────────────────────────
    TIER_CLASS = {
        "STRONG_BUY":  "tb-vs",
        "BUY":         "tb-s",
        "SELL":        "tb-b",
        "STRONG_SELL": "tb-vb",
    }

    def _thesis(row, direction):
        comps = {
            "momentum":  row.get("momentum_score"),
            "quality":   row.get("quality_score"),
            "insider":   row.get("insider_score"),
            "reversion": row.get("reversion_score"),
        }
        # Phase 2B: for bearish, treat 0-valued components as missing (same
        # rationale as the composite>0 guard on the panel query. A 0 here is
        # typically a penalty-floored / unscored value, not a real bearish
        # driver; surfacing it produced "weak X 0" artefacts in 2A).
        if direction == "strong":
            comps = {k: v for k, v in comps.items() if v is not None}
        else:
            comps = {k: v for k, v in comps.items() if v is not None and v > 0}
        if not comps:
            return "-"
        if direction == "strong":
            k = max(comps, key=lambda x: comps[x])
            return f"{k} {comps[k]:.0f}"
        k = min(comps, key=lambda x: comps[x])
        return f"weak {k} {comps[k]:.0f}"

    def _annotate(rows, direction):
        out = []
        for r in rows:
            d = dict(r)
            d["tier_short"] = tier_short(d.get("rating", ""))
            d["tier_class"] = TIER_CLASS.get(d.get("rating", ""), "")
            d["thesis"]     = _thesis(d, direction)
            out.append(d)
        return out

    top_strong = _annotate(db_query(f"""
        SELECT ticker, rating, composite_score, {signal_scores_projection(surface='dashboard')}
        FROM signal_scores
        WHERE DATE(scored_at) = DATE((SELECT MAX(scored_at) FROM signal_scores))
          AND rating IN ('STRONG_BUY','BUY')
        ORDER BY composite_score DESC LIMIT 5
    """), "strong")

    # Panel 3 fix (Phase 2B): exclude composite_score = 0. Those rows are the
    # penalty-floored set (761 SELL/STRONG_SELL rows pinned at 0 by _clamp on
    # the latest run); they're not genuine bearish conviction, they're tickers
    # whose composite went negative and got floored. Real bearish names start
    # at composite ~0.1 (LVO) under the current methodology.
    top_bearish = _annotate(db_query(f"""
        SELECT ticker, rating, composite_score, {signal_scores_projection(surface='dashboard')}
        FROM signal_scores
        WHERE DATE(scored_at) = DATE((SELECT MAX(scored_at) FROM signal_scores))
          AND rating IN ('SELL','STRONG_SELL')
          AND composite_score > 0
        ORDER BY composite_score ASC LIMIT 5
    """), "bearish")

    # ── Panel 4: Market State (Hang Seng dropped, Phase 1 flagged ^HSI empty) ─
    INDICES = [
        ("^GSPC", "S&P 500"),
        ("^IXIC", "NASDAQ"),
        ("^DJI",  "DOW"),
        ("^VIX",  "VIX"),
        ("^FTSE", "FTSE 100"),
    ]
    market_tiles = []
    for sym, name in INDICES:
        rows = db_query(
            "SELECT close FROM market_history WHERE symbol = ? ORDER BY date DESC LIMIT 2",
            (sym,),
        )
        latest = rows[0]["close"] if rows else None
        prev   = rows[1]["close"] if len(rows) > 1 else None
        chg_pct = ((latest - prev) / prev * 100.0) if (latest and prev) else None
        market_tiles.append({
            "symbol":  sym,
            "name":    name,
            "level":   latest,
            "chg_pct": chg_pct,
        })

    # ── Panel 5: Watchlist Preview ──────────────────────────────────────────
    default_wl_id = get_or_create_default_watchlist(DATABASE_PATH, user["id"])
    wl_full   = get_watchlist(DATABASE_PATH, user["id"], default_wl_id)
    wl_preview = []
    for w in wl_full[:5]:
        d = dict(w)
        d["tier_short"] = tier_short(d.get("rating", "") or "")
        d["tier_class"] = TIER_CLASS.get(d.get("rating", ""), "")
        wl_preview.append(d)
    metas = get_watchlists_meta(DATABASE_PATH, user["id"])
    wl_meta = next((m for m in metas if m.get("id") == default_wl_id), None)
    wl_name = (wl_meta or {}).get("name", "Watchlist")

    # ── Panel 6: Discovery Themes (live counts via shared helper) ───────────
    counts = _compute_theme_counts(DATABASE_PATH)
    from config.themes import THEMES
    themes_panel = []
    for th in THEMES[:6]:
        themes_panel.append({
            "id":    th["id"],
            "label": th.get("label", th["id"]),
            "emoji": th.get("emoji", ""),
            "count": counts.get(th["id"], 0),
        })

    # ── Panel 7: Penny Stock Spotlight (ELITE-GATED, server-side only) ──────
    # Phase 1 lesson: free clients must never receive real pick data. Non-Elite
    # users get spotlight=None, the template renders the locked teaser with
    # placeholder copy only, no ticker/price/breakdown leaks into the HTML.
    spotlight = _get_penny_pick_full(DATABASE_PATH) if is_elite else None

    # ── Relative-time helper (used by panels 11/12/13) ───────────────────────
    from datetime import datetime as _dt, timezone as _tz
    _now = _dt.utcnow()
    def _ago(ts):
        if not ts:
            return "-"
        try:
            s = ts.replace("Z", "").replace("T", " ")
            t = _dt.fromisoformat(s.split(".")[0])
        except Exception:
            return ts
        delta = _now - t
        secs = int(delta.total_seconds())
        if secs < 60:
            return f"{secs}s ago"
        if secs < 3600:
            return f"{secs // 60}m ago"
        if secs < 86400:
            return f"{secs // 3600}h ago"
        return f"{secs // 86400}d ago"

    # ── Panel 8: Earnings Next 7 Days ───────────────────────────────────────
    # Sparse-state: 4 rows live in 7-day window per Phase 1.
    earnings_upcoming = db_query("""
        SELECT ec.ticker, ec.earnings_date, ec.eps_estimate,
               sig.rating, sig.composite_score
        FROM earnings_calendar ec
        LEFT JOIN signal_scores sig
          ON sig.ticker = ec.ticker
         AND DATE(sig.scored_at) = DATE((SELECT MAX(scored_at) FROM signal_scores))
        WHERE ec.earnings_date BETWEEN DATE('now') AND DATE('now','+7 days')
        ORDER BY ec.earnings_date ASC,
                 COALESCE(sig.composite_score, 0) DESC
        LIMIT 7
    """)
    earnings_upcoming = [
        {**dict(r),
         "tier_short": tier_short(r.get("rating") or ""),
         "tier_class": TIER_CLASS.get(r.get("rating") or "", "")}
        for r in earnings_upcoming
    ]

    # ── Panel 9: Dividends This Week ────────────────────────────────────────
    # Sparse-state: 2 rows live this week per Phase 1.
    divs_week = db_query("""
        SELECT dv.ticker, dv.ex_dividend_date, dv.dividend_yield,
               dv.annual_dividend,
               sig.rating
        FROM dividends dv
        LEFT JOIN signal_scores sig
          ON sig.ticker = dv.ticker
         AND DATE(sig.scored_at) = DATE((SELECT MAX(scored_at) FROM signal_scores))
        WHERE dv.ex_dividend_date BETWEEN DATE('now') AND DATE('now','+7 days')
        ORDER BY dv.ex_dividend_date ASC, dv.dividend_yield DESC
        LIMIT 7
    """)
    divs_week = [
        {**dict(r),
         "tier_short": tier_short(r.get("rating") or ""),
         "tier_class": TIER_CLASS.get(r.get("rating") or "", "")}
        for r in divs_week
    ]

    # ── Panel 10: Sector Performance (7d ranking via shared helper) ─────────
    sectors_panel = _get_sector_performance(DATABASE_PATH)

    # ── Panel 11: Recent Rating Changes ─────────────────────────────────────
    rating_change_rows = db_query("""
        SELECT ticker, old_rating, new_rating, composite_score, change_date
        FROM rating_changes
        WHERE change_date >= datetime('now','-1 day')
        ORDER BY change_date DESC
        LIMIT 8
    """)
    rating_changes_panel = []
    for r in rating_change_rows:
        d = dict(r)
        d["old_short"] = tier_short(d.get("old_rating") or "") or "-"
        d["new_short"] = tier_short(d.get("new_rating") or "") or "-"
        d["new_class"] = TIER_CLASS.get(d.get("new_rating") or "", "")
        d["ago"]       = _ago(d.get("change_date"))
        rating_changes_panel.append(d)

    # ── Panel 12: Insider Activity (cluster signals, 14d) ───────────────────
    insider_panel = db_query("""
        SELECT ticker, signal_type,
               MAX(insider_count) AS insider_count,
               MAX(total_value)   AS total_value,
               MAX(detected_at)   AS detected_at
        FROM insider_signals
        WHERE detected_at >= datetime('now','-14 days')
        GROUP BY ticker, signal_type
        ORDER BY total_value DESC
        LIMIT 7
    """)
    insider_panel = [
        {**dict(r), "ago": _ago(r.get("detected_at"))} for r in insider_panel
    ]

    # ── Panel 13: News Headlines (latest 24h) ───────────────────────────────
    news_panel = db_query("""
        SELECT ticker, headline, source, published, scraped_at, url
        FROM news_sentiment
        WHERE scraped_at >= datetime('now','-1 day')
        ORDER BY COALESCE(published, scraped_at) DESC
        LIMIT 7
    """)
    news_panel = [
        {**dict(r), "ago": _ago(r.get("published") or r.get("scraped_at"))}
        for r in news_panel
    ]

    # ── Panel 14: Short-Squeeze Setups (confluence: heavy SI + Very Strong/Strong) ─
    squeeze_panel = [
        {**r, "tier_short": tier_short(r["rating"])}
        for r in _get_squeeze_candidates(DATABASE_PATH)
    ]

    return render_template(
        "dashboard.html",
        user=user,
        tier_key=tier_key,
        is_elite=is_elite,
        last_scored=last_scored,
        ticker_count=ticker_count,
        engine_version=SCORING_ENGINE_VERSION,
        summary=summary,
        top_strong=top_strong,
        top_bearish=top_bearish,
        market_tiles=market_tiles,
        wl_preview=wl_preview,
        wl_name=wl_name,
        themes_panel=themes_panel,
        spotlight=spotlight,                # Phase 2B: None for non-Elite (gated)
        earnings_upcoming=earnings_upcoming,
        divs_week=divs_week,
        sectors_panel=sectors_panel,
        rating_changes_panel=rating_changes_panel,
        insider_panel=insider_panel,
        news_panel=news_panel,
        squeeze_panel=squeeze_panel,
    )


@app.route("/ticker/<ticker>")
@login_required
def ticker_page(ticker):
    legal_risk_data = get_legal_risk(ticker.upper())
    if legal_risk_data is None:
        try:
            result = fetch_legal_risk(ticker.upper())
            save_legal_risk(ticker.upper(), result)
            legal_risk_data = result
        except:
            legal_risk_data = {
                'risk_level': 'NONE', 'risk_label': 'Unavailable',
                'risk_color': '#6b7280', 'penalty': 0, 'findings': [],
                'scraped_at': None,
            }
    from_page = request.args.get('from', '')
    user = current_user()
    page_user_watchlists = []
    page_ticker_wl_ids = []
    if user:
        page_user_watchlists = get_watchlists_meta(DATABASE_PATH, user["id"])
        wl_rows = db_query(
            "SELECT watchlist_id FROM watchlists WHERE user_id=? AND ticker=?",
            (user["id"], ticker.upper())
        )
        page_ticker_wl_ids = [r["watchlist_id"] for r in wl_rows]
    return render_template('ticker.html', ticker=ticker.upper(),
                           legal_risk=legal_risk_data, from_page=from_page,
                           user=user,
                           user_watchlists=page_user_watchlists,
                           ticker_watchlist_ids=page_ticker_wl_ids)



@app.route("/industry/<path:industry_name>")
@login_required
def industry_page(industry_name):
    return render_template("industry.html", industry=industry_name)

@app.route("/api/industry/<path:industry_name>")
@login_required  
def api_industry(industry_name):
    rows = db_query(f"""
        SELECT ss.ticker, ss.company, ss.price, ss.change_pct,
               ss.market_cap, ss.sector, ss.industry,
               sc.rating, sc.composite_score,
               {signal_scores_projection(prefix='sc.', surface='industry')},
               ss.analyst_recom
        FROM screener_snapshots ss
        LEFT JOIN signal_scores sc ON ss.ticker = sc.ticker
            AND DATE(sc.scored_at) = DATE((SELECT MAX(scored_at) FROM signal_scores))
        WHERE ss.industry = ?
        AND ss.scraped_at >= datetime('now', '-2 days')
        GROUP BY ss.ticker
        ORDER BY sc.composite_score DESC NULLS LAST
        LIMIT 200
    """, (industry_name,))
    # Price-aware score gate (penny rows stripped for non-elite).
    tier = effective_tier(current_user())
    rows = strip_scores_for_non_elite(rows, tier, price_key='price')
    return jsonify(rows)

@app.route("/signals")
def signals_redirect():
    """Redirect /signals?rating=X to /?rating=X for nav links from ratings page."""
    rating = request.args.get("rating", "")
    return redirect(f"/?rating={rating}" if rating else "/")

@app.route("/watchlist")
@login_required
def watchlist():
    user  = current_user()
    wls   = get_watchlists_meta(DATABASE_PATH, user["id"])
    active_id = request.args.get("wl", type=int)
    if not active_id and wls:
        active_id = wls[0]["id"]
    items = get_watchlist(DATABASE_PATH, user["id"], active_id) if active_id else []
    tier  = get_tier(effective_tier(user))
    limit = tier["watchlist_limit"]
    return render_template("watchlist.html", user=user, items=items,
                           watchlists=wls, active_watchlist_id=active_id,
                           tier=tier, watchlist_limit=limit,
                           min_price_for_signal=MIN_PRICE_FOR_SIGNAL)


# ── Watchlist API ─────────────────────────────────

@app.route("/api/watchlists", methods=["GET"])
@login_required
def api_watchlists_list():
    user   = current_user()
    ticker = request.args.get("ticker", "").upper() or None
    wls    = get_watchlists_meta(DATABASE_PATH, user["id"])
    tier   = get_tier(effective_tier(user))
    if ticker:
        # Annotate each watchlist with contains_ticker flag
        wl_ids_with_ticker = {
            r["watchlist_id"]
            for r in db_query(
                "SELECT DISTINCT watchlist_id FROM watchlists WHERE user_id=? AND ticker=?",
                (user["id"], ticker)
            )
        }
        for wl in wls:
            wl["contains_ticker"] = wl["id"] in wl_ids_with_ticker
    return jsonify({"watchlists": wls, "limit": tier["watchlist_limit"],
                    "count": len(wls), "tier_name": tier["display_name"]})


@app.route("/api/watchlists/membership")
@login_required
def api_watchlists_membership():
    """Return per-watchlist membership for a specific ticker. Used by the watchlist picker on open."""
    user   = current_user()
    ticker = request.args.get("ticker", "").upper()
    if not ticker:
        return jsonify({"error": "ticker param required"}), 400
    wls = get_watchlists_meta(DATABASE_PATH, user["id"])
    member_ids = {
        r["watchlist_id"]
        for r in db_query(
            "SELECT DISTINCT watchlist_id FROM watchlists WHERE user_id=? AND ticker=?",
            (user["id"], ticker)
        )
    }
    return jsonify({
        "ticker": ticker,
        "watchlists": [{"id": wl["id"], "name": wl["name"], "contains_ticker": wl["id"] in member_ids}
                       for wl in wls],
    })


@app.route("/api/watchlists/all-tickers")
@login_required
def api_watchlists_all_tickers():
    """Return flat list of all ticker symbols across all user watchlists."""
    user = current_user()
    rows = db_query(
        "SELECT DISTINCT ticker FROM watchlists WHERE user_id=?", (user["id"],)
    )
    return jsonify({"tickers": [r["ticker"] for r in rows]})


@app.route("/api/watchlists", methods=["POST"])
@login_required
def api_watchlists_create():
    user       = current_user()
    body       = request.json or {}
    name       = body.get("name", "").strip()
    add_ticker = body.get("add_ticker", "").strip().upper()
    if not name:
        return jsonify({"ok": False, "error": "Name required"}), 400
    wls = get_watchlists_meta(DATABASE_PATH, user["id"])
    tier_key = effective_tier(user)
    if not can_create_watchlist(tier_key, len(wls)):
        limit    = watchlist_limit(tier_key)
        tier_cfg = get_tier(tier_key)
        return jsonify({
            "ok":         False,
            "error":      "tier_limit",
            "feature":    "watchlists",
            "tier":       tier_key,
            "tier_name":  tier_cfg["display_name"],
            "limit":      limit,
            "current":    len(wls),
            "upgrade_to": next_tier(tier_key),
        }), 403
    try:
        result = create_watchlist(DATABASE_PATH, user["id"], name)
        if add_ticker:
            add_to_watchlist(DATABASE_PATH, user["id"], add_ticker, "", watchlist_id=result["id"])
        return jsonify({"ok": True, **result})
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 409


@app.route("/api/watchlists/<int:wl_id>", methods=["PATCH"])
@login_required
def api_watchlists_rename(wl_id):
    user     = current_user()
    new_name = (request.json or {}).get("name", "").strip()
    if not new_name:
        return jsonify({"ok": False, "error": "Name required"}), 400
    try:
        ok = rename_watchlist(DATABASE_PATH, user["id"], wl_id, new_name)
        if not ok:
            return jsonify({"ok": False, "error": "Not found"}), 404
        return jsonify({"ok": True})
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 409


@app.route("/api/watchlists/<int:wl_id>", methods=["DELETE"])
@login_required
def api_watchlists_delete(wl_id):
    user = current_user()
    confirm = request.args.get("confirm") == "true"
    if not confirm:
        return jsonify({"ok": False, "error": "Pass ?confirm=true to delete"}), 400
    if is_default_watchlist(DATABASE_PATH, user["id"], wl_id):
        return jsonify({
            "ok": False,
            "error": "The default watchlist cannot be deleted. You can rename it instead.",
        }), 400
    wls = get_watchlists_meta(DATABASE_PATH, user["id"])
    if len(wls) <= 1:
        return jsonify({"ok": False, "error": "Cannot delete your only watchlist"}), 400
    ok = delete_watchlist(DATABASE_PATH, user["id"], wl_id)
    if not ok:
        return jsonify({"ok": False, "error": "Not found"}), 404
    return jsonify({"ok": True})


@app.route("/api/watchlists/<int:wl_id>/toggle_alerts", methods=["POST"])
@login_required
def api_watchlists_toggle_alerts(wl_id):
    user   = current_user()
    result = toggle_watchlist_alerts(DATABASE_PATH, user["id"], wl_id)
    if result is None:
        return jsonify({"ok": False, "error": "Not found"}), 404
    return jsonify({"ok": True, **result})


@app.route("/api/watchlists/<int:wl_id>/tickers", methods=["POST"])
@login_required
def api_watchlists_add_ticker(wl_id):
    user   = current_user()
    ticker = (request.json or {}).get("ticker", "").upper()
    notes  = (request.json or {}).get("notes", "")
    if not ticker:
        return jsonify({"ok": False, "error": "No ticker"}), 400
    ok = add_to_watchlist(DATABASE_PATH, user["id"], ticker, notes, watchlist_id=wl_id)
    return jsonify({"ok": ok, "ticker": ticker})


@app.route("/api/watchlists/<int:wl_id>/tickers/<ticker>", methods=["DELETE"])
@login_required
def api_watchlists_remove_ticker(wl_id, ticker):
    user = current_user()
    remove_from_watchlist(DATABASE_PATH, user["id"], ticker.upper(), watchlist_id=wl_id)
    return jsonify({"ok": True, "ticker": ticker.upper()})


@app.route("/api/watchlist/add", methods=["POST"])
@login_required
def api_watchlist_add():
    user        = current_user()
    ticker      = (request.json or {}).get("ticker", "").upper()
    notes       = (request.json or {}).get("notes", "")
    watchlist_id = (request.json or {}).get("watchlist_id")
    if not ticker:
        return jsonify({"ok": False, "error": "No ticker"})
    ok = add_to_watchlist(DATABASE_PATH, user["id"], ticker, notes,
                          watchlist_id=watchlist_id)
    return jsonify({"ok": ok, "ticker": ticker})


@app.route("/api/watchlist/remove", methods=["POST"])
@login_required
def api_watchlist_remove():
    user        = current_user()
    ticker      = (request.json or {}).get("ticker", "").upper()
    watchlist_id = (request.json or {}).get("watchlist_id")
    remove_from_watchlist(DATABASE_PATH, user["id"], ticker, watchlist_id=watchlist_id)
    return jsonify({"ok": True, "ticker": ticker})


@app.route("/api/watchlist")
@login_required
def api_watchlist():
    user        = current_user()
    watchlist_id = request.args.get("wl", type=int)
    items = get_watchlist(DATABASE_PATH, user["id"], watchlist_id)
    return jsonify(items)


# ── Data API ──────────────────────────────────────

@app.route("/api/overview")
@login_required
def api_overview():
    rows = db_query("""
        SELECT
            (SELECT COUNT(*) FROM screener_snapshots) as screener_rows,
            (SELECT COUNT(DISTINCT ticker) FROM screener_snapshots) as unique_tickers,
            (SELECT MAX(scraped_at) FROM screener_snapshots) as last_screener,
            (SELECT COUNT(*) FROM insider_trades) as insider_trades,
            (SELECT MAX(scraped_at) FROM insider_trades) as last_insider,
            (SELECT COUNT(*) FROM signal_scores) as signal_scores,
            (SELECT MAX(scored_at) FROM signal_scores) as last_scored
    """)
    return jsonify(rows[0] if rows else {})


@app.route("/api/signals")
@login_required
def api_signals():
    rows = db_query(f"""
        SELECT ss.ticker, ss.rating, MAX(ss.composite_score) as composite_score,
        {signal_scores_projection(prefix='ss.', surface='signals')}, ss.flags, MAX(ss.scored_at) as scored_at,
        sc.sector, sc.industry, sc.price
FROM signal_scores ss
LEFT JOIN (
    SELECT s.ticker, s.sector, s.industry, s.price
    FROM screener_snapshots s
    INNER JOIN (
        SELECT ticker, MAX(scraped_at) AS max_ts
        FROM screener_snapshots
        GROUP BY ticker
    ) lts ON s.ticker = lts.ticker AND s.scraped_at = lts.max_ts
) sc ON ss.ticker = sc.ticker
        WHERE DATE(ss.scored_at) = DATE((SELECT MAX(scored_at) FROM signal_scores))
        GROUP BY ss.ticker
        ORDER BY ss.composite_score DESC
    """)
    for r in rows:
        raw = (r.get("flags") or "").split("|")
        r["flag_list"] = [f.strip() for f in raw if f.strip()]
        r.pop("flags", None)
    # Price-aware score gate (penny rows stripped for non-elite).
    tier = effective_tier(current_user())
    rows = strip_scores_for_non_elite(rows, tier, price_key='price')
    filter_proprietary_flags_for_non_elite(rows, tier, price_key='price')
    return jsonify(rows)
@app.route("/api/signals/sector/<sector>")
@login_required
def api_signals_by_sector(sector):
    rows = db_query(f"""
        SELECT ss.ticker, ss.rating, MAX(ss.composite_score) as composite_score,
               {signal_scores_projection(prefix='ss.', surface='signals')}, ss.flags, MAX(ss.scored_at) as scored_at,
               sc.sector, sc.industry, sc.price
        FROM signal_scores ss
        LEFT JOIN (
            SELECT s.ticker, s.sector, s.industry, s.price
            FROM screener_snapshots s
            INNER JOIN (
                SELECT ticker, MAX(scraped_at) AS max_ts
                FROM screener_snapshots
                GROUP BY ticker
            ) lts ON s.ticker = lts.ticker AND s.scraped_at = lts.max_ts
        ) sc ON ss.ticker = sc.ticker
        WHERE DATE(ss.scored_at) = DATE((SELECT MAX(scored_at) FROM signal_scores))
        AND sc.sector = ?
        GROUP BY ss.ticker
        ORDER BY ss.composite_score DESC
    """, (sector,))
    for r in rows:
        raw = (r.get("flags") or "").split("|")
        r["flag_list"] = [f.strip() for f in raw if f.strip()]
        r.pop("flags", None)
    # Price-aware score gate (penny rows stripped for non-elite).
    tier = effective_tier(current_user())
    rows = strip_scores_for_non_elite(rows, tier, price_key='price')
    filter_proprietary_flags_for_non_elite(rows, tier, price_key='price')
    return jsonify(rows)

@app.route("/api/signals/<rating>")
@login_required
def api_signals_by_rating(rating):
    rows = db_query(f"""
        SELECT sig.ticker, sig.rating, MAX(sig.composite_score) as composite_score,
               {signal_scores_projection(prefix='sig.', surface='signals')}, sig.flags, MAX(sig.scored_at) as scored_at,
               sc.price
        FROM signal_scores sig
        LEFT JOIN (
            SELECT s.ticker, s.price
            FROM screener_snapshots s
            INNER JOIN (
                SELECT ticker, MAX(scraped_at) AS max_ts
                FROM screener_snapshots
                GROUP BY ticker
            ) lts ON s.ticker = lts.ticker AND s.scraped_at = lts.max_ts
        ) sc ON sig.ticker = sc.ticker
        WHERE DATE(sig.scored_at) = DATE((SELECT MAX(scored_at) FROM signal_scores))
          AND sig.rating = ?
        GROUP BY sig.ticker
        ORDER BY composite_score DESC
        LIMIT 100
    """, (rating.upper(),))
    for r in rows:
        raw = (r.get("flags") or "").split("|")
        r["flag_list"] = [f.strip() for f in raw if f.strip()]
        r.pop("flags", None)
    # Price-aware score gate (penny rows stripped for non-elite).
    tier = effective_tier(current_user())
    rows = strip_scores_for_non_elite(rows, tier, price_key='price')
    filter_proprietary_flags_for_non_elite(rows, tier, price_key='price')
    return jsonify(rows)


@app.route("/api/signal_summary")
@login_required
def api_signal_summary():
    return jsonify(get_signal_summary(DATABASE_PATH))


@app.route("/api/sectors")
@login_required
def api_sectors():
    rows = db_query("""
        SELECT
            sector,
            COUNT(DISTINCT ticker) as tickers,
            ROUND(AVG(rsi_14), 1) as avg_rsi,
            ROUND(AVG(change_pct), 2) as avg_change,
            ROUND(AVG(sma_50_pct), 2) as avg_50sma,
            ROUND(AVG(analyst_recom), 2) as avg_analyst,
            SUM(CASE WHEN change_pct > 0 THEN 1 ELSE 0 END) as gainers,
            SUM(CASE WHEN change_pct < 0 THEN 1 ELSE 0 END) as losers
        FROM screener_snapshots
        WHERE scraped_at >= datetime('now', '-2 days')
          AND sector IS NOT NULL
        GROUP BY sector
        ORDER BY sector ASC
    """)
    return jsonify(rows)


def _get_sector_performance(db_path: str) -> list:
    """Latest sector relative strength ranking (all 11 sectors).

    Canonical query, extracted from api_sector_performance so the dashboard
    route can reuse the same data without duplicating SQL.
    """
    conn = get_connection(db_path)
    cur  = conn.cursor()
    cur.execute("""
        SELECT sector, etf_symbol, return_7d, return_30d,
               rank_7d, sector_strength_score, date
        FROM sector_performance
        WHERE date = (SELECT MAX(date) FROM sector_performance)
        ORDER BY rank_7d ASC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def _get_squeeze_candidates(db_path: str) -> list:
    """Short-squeeze detector tile: confluence of heavy short interest and
    a Very Strong / Strong composite rating.

    Display-only (not a scoring component). FinViz `short_interest_pct` is
    the only data source. ~49.5% universe coverage is accepted (the tile
    is inherently selective and fires on the heavily-shorted tail where
    FinViz coverage is strongest).

    Fire conditions:
      - rating IN ('STRONG_BUY','BUY')            (Very Strong or Strong)
      - short_interest_pct >= 10                  (qualifying floor)
      - short_interest_pct <= 100                 (implausibility guard,
                                                   mirrors inst_own >100)
      - julianday('now') - julianday(scraped_at) <= 14
                                                  (staleness suppression,
                                                   half a bi-monthly cycle)

    Elevated band: short_interest_pct >= 20 → caller renders a gold chip.
    Ordering: short_interest_pct DESC, top 10.

    Returns list[dict] with keys: ticker, short_interest_pct, elevated_flag,
    composite_score, rating, scraped_at. Empty list when nothing qualifies.
    """
    conn = get_connection(db_path)
    cur  = conn.cursor()
    cur.execute("""
        WITH latest_per_ticker AS (
            SELECT ticker, MAX(scraped_at) AS max_ts
            FROM screener_snapshots
            GROUP BY ticker
        ),
        latest_batch AS (
            SELECT ticker, rating, composite_score
            FROM signal_scores
            WHERE DATE(scored_at) = DATE((SELECT MAX(scored_at) FROM signal_scores))
              AND rating IN ('STRONG_BUY','BUY')
        )
        SELECT lb.ticker,
               sn.short_interest_pct,
               sn.scraped_at,
               lb.rating,
               lb.composite_score
        FROM latest_batch lb
        JOIN latest_per_ticker l  ON l.ticker = lb.ticker
        JOIN screener_snapshots sn ON sn.ticker = lb.ticker AND sn.scraped_at = l.max_ts
        WHERE sn.short_interest_pct IS NOT NULL
          AND sn.short_interest_pct >= 10
          AND sn.short_interest_pct <= 100
          AND (julianday('now') - julianday(sn.scraped_at)) <= 14
        ORDER BY sn.short_interest_pct DESC
        LIMIT 10
    """)
    rows = []
    for r in cur.fetchall():
        d = dict(r)
        d["elevated_flag"] = d["short_interest_pct"] >= 20
        rows.append(d)
    conn.close()
    return rows


@app.route("/api/sector-performance")
@login_required
def api_sector_performance():
    """Latest sector relative strength ranking (all 11 sectors)."""
    return jsonify(_get_sector_performance(DATABASE_PATH))


@app.route("/api/insider_signals")
@login_required
def api_insider_signals():
    rows = db_query("""
        SELECT ticker, signal_type, MAX(insider_count) as insider_count,
               MAX(total_value) as total_value, MAX(detected_at) as detected_at, notes
        FROM insider_signals
        WHERE detected_at >= datetime('now', '-14 days')
        GROUP BY ticker, signal_type
        ORDER BY total_value DESC
    """)
    return jsonify(rows)


@app.route("/api/news")
@login_required
def api_news():
    return jsonify(get_ticker_sentiment(DATABASE_PATH))


@app.route("/api/top_signals")
@login_required
def api_top_signals():
    today = datetime.now().strftime("%Y-%m-%d")
    top   = get_top_signals_of_day(DATABASE_PATH, today)
    if not top:
        top = generate_top_signals_of_day(DATABASE_PATH)
    return jsonify(top)


@app.route("/api/search")
@login_required
def api_search():
    q = request.args.get("q", "").strip().upper()
    if not q:
        return jsonify({"results": []})
    prefix = q + "%"
    substr = "%" + q + "%"
    rows = db_query("""
        SELECT ss.ticker, ss.company, ss.price,
               sig.rating, sig.composite_score, sig.target_price, sig.target_upside
        FROM (
            SELECT s.ticker, s.company, s.price
            FROM screener_snapshots s
            INNER JOIN (
                SELECT ticker, MAX(scraped_at) AS max_ts
                FROM screener_snapshots
                WHERE ticker LIKE ? OR UPPER(company) LIKE ?
                GROUP BY ticker
            ) lts ON s.ticker = lts.ticker AND s.scraped_at = lts.max_ts
        ) ss
        LEFT JOIN (
            SELECT ticker, rating, composite_score, target_price, target_upside,
                   MAX(scored_at) as max_ts
            FROM signal_scores
            GROUP BY ticker
        ) sig ON ss.ticker = sig.ticker
        ORDER BY
            CASE WHEN ss.ticker LIKE ? THEN 0 ELSE 1 END,
            sig.composite_score DESC
        LIMIT 10
    """, (prefix, substr, prefix))
    results = [dict(r) for r in rows]
    # Price-aware score gate (penny matches stripped for non-elite).
    tier = effective_tier(current_user())
    strip_scores_for_non_elite(results, tier, price_key='price')
    return jsonify({"results": results})


@app.route("/dividends")
@login_required
def dividends():
    user = current_user()
    try:
        from config.settings import FMP_API_KEY
        has_key = bool(FMP_API_KEY)
    except Exception:
        has_key = False
    sectors = db_query("""
        SELECT DISTINCT sector FROM screener_snapshots WHERE sector IS NOT NULL ORDER BY sector
    """)
    return render_template("dividends.html", user=user, has_fmp_key=has_key,
                           sectors=[r["sector"] for r in sectors])


@app.route("/api/dividends")
@login_required
def api_dividends():
    from scrapers.fmp_scraper import get_dividends, _ensure_tables
    _ensure_tables(DATABASE_PATH)
    user       = current_user()
    min_yield  = request.args.get("min_yield", type=float, default=0)
    sector     = request.args.get("sector", "")
    rating_f   = request.args.get("rating", "")
    aristocrat = request.args.get("aristocrat", "0") == "1"
    sort_col   = request.args.get("sort", "dividend_yield")
    sort_dir   = request.args.get("dir", "desc")

    allowed_sorts = {"dividend_yield", "annual_dividend", "payout_ratio",
                     "ex_dividend_date", "payment_date", "dividend_growth_5yr",
                     "consecutive_years", "composite_score", "ticker"}
    if sort_col not in allowed_sorts:
        sort_col = "dividend_yield"
    if sort_dir not in ("asc", "desc"):
        sort_dir = "desc"

    rows = get_dividends(DATABASE_PATH,
                         min_yield=min_yield,
                         sector=sector or None,
                         rating=rating_f or None,
                         aristocrat=aristocrat)

    # Sort in Python for flexibility
    def sort_key(r):
        v = r.get(sort_col)
        return (v is None, v if v is not None else 0)
    rows.sort(key=sort_key, reverse=(sort_dir == "desc"))

    # Mark watchlist
    wl = set()
    if user:
        wl_rows = db_query("SELECT ticker FROM watchlists WHERE user_id = ?", (user["id"],))
        wl = {r["ticker"] for r in wl_rows}
    for r in rows:
        r["in_watchlist"] = r.get("ticker") in wl

    # Price-aware score gate. get_dividends() now JOINs latest
    # screener_snapshots and exposes 'price' on each row (4c SQL change
    # in scrapers/fmp_scraper.py).
    tier = effective_tier(user)
    strip_scores_for_non_elite(rows, tier, price_key='price')

    return jsonify({"rows": rows, "total": len(rows)})


@app.route("/api/dividends/refresh", methods=["POST"])
@login_required
def api_dividends_refresh():
    data   = request.get_json() or {}
    tickers = data.get("tickers")   # optional list
    try:
        from scrapers.fmp_scraper import job_refresh_dividends
        n = job_refresh_dividends(DATABASE_PATH, tickers=tickers)
        return jsonify({"ok": True, "saved": n})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/earnings")
@login_required
def earnings():
    user = current_user()
    try:
        from config.settings import FMP_API_KEY
        has_key = bool(FMP_API_KEY)
    except Exception:
        has_key = False
    return render_template("earnings.html", user=user, has_fmp_key=has_key)


@app.route("/api/earnings")
@login_required
def api_earnings():
    from scrapers.fmp_scraper import get_earnings_calendar, _ensure_tables
    from datetime import datetime, timedelta
    _ensure_tables(DATABASE_PATH)
    view     = request.args.get("view", "week")   # week / next_week / month
    rating_f = request.args.get("rating", "")
    user     = current_user()

    today = datetime.now().date()
    if view == "week":
        from_d = today.strftime("%Y-%m-%d")
        to_d   = (today + timedelta(days=7)).strftime("%Y-%m-%d")
    elif view == "next_week":
        from_d = (today + timedelta(days=7)).strftime("%Y-%m-%d")
        to_d   = (today + timedelta(days=14)).strftime("%Y-%m-%d")
    else:
        from_d = today.strftime("%Y-%m-%d")
        to_d   = (today + timedelta(days=30)).strftime("%Y-%m-%d")

    rows = get_earnings_calendar(DATABASE_PATH, from_d, to_d)

    # Filter by rating
    if rating_f:
        rows = [r for r in rows if r.get("rating") == rating_f]

    # Mark watchlist tickers
    wl = set()
    if user:
        wl_rows = db_query("SELECT ticker FROM watchlists WHERE user_id = ?", (user["id"],))
        wl = {r["ticker"] for r in wl_rows}
    for r in rows:
        r["in_watchlist"] = r["ticker"] in wl

    return jsonify({"rows": rows, "total": len(rows)})


@app.route("/api/earnings/refresh", methods=["POST"])
@login_required
def api_earnings_refresh():
    try:
        from scrapers.fmp_scraper import job_refresh_earnings
        n = job_refresh_earnings(DATABASE_PATH, days_ahead=30)
        return jsonify({"ok": True, "saved": n})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/ratings")
@login_required
def ratings():
    user = current_user()
    distribution = db_query("""
        SELECT rating, COUNT(DISTINCT ticker) as count,
               ROUND(AVG(composite_score), 1) as avg_score,
               ROUND(MIN(composite_score), 1) as min_score,
               ROUND(MAX(composite_score), 1) as max_score
        FROM signal_scores
        WHERE DATE(scored_at) = DATE((SELECT MAX(scored_at) FROM signal_scores))
        GROUP BY rating
        ORDER BY avg_score DESC
    """)
    last_run = db_query("SELECT MAX(scored_at) as ts FROM signal_scores")
    return render_template("ratings.html", user=user,
                           distribution=distribution,
                           last_run=last_run[0]["ts"] if last_run else None)


@app.route("/events")
@login_required
def events_page():
    user = current_user()
    return render_template("events.html", user=user)


@app.route("/api/economic-calendar")
@login_required
def api_economic_calendar():
    impact = request.args.get("impact", "")
    country = request.args.get("country", "")
    from_date = request.args.get("from", "")
    to_date = request.args.get("to", "")

    conditions = []
    params = []
    if impact:
        conditions.append("impact = ?")
        params.append(impact)
    if country:
        conditions.append("country = ?")
        params.append(country.upper())
    if from_date:
        conditions.append("event_date >= ?")
        params.append(from_date)
    if to_date:
        conditions.append("event_date <= ?")
        params.append(to_date)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    rows = db_query(f"""
        SELECT event_date, event_name, impact, country, currency,
               estimate, actual, previous, unit
        FROM economic_calendar
        {where}
        ORDER BY event_date ASC, impact DESC
        LIMIT 500
    """, params)
    return jsonify(rows)


@app.route("/api/economic-calendar/high-impact-banner")
@login_required
def api_high_impact_banner():
    """Return high-impact US events within next 7 days for events page banner."""
    rows = db_query("""
        SELECT event_date, event_name
        FROM economic_calendar
        WHERE impact = 'High'
          AND event_date >= DATE('now')
          AND event_date <= DATE('now', '+7 days')
          AND country = 'US'
        ORDER BY event_date ASC
        LIMIT 20
    """)
    return jsonify(rows)


def _compute_theme_counts(db_path: str) -> dict:
    """Return stock counts for all 7 discovery theme cards.

    Canonical query logic, identical to /api/screener?theme=<id>.
    Extracted from api_theme_counts so the dashboard route can call the same
    underlying computation without duplicating SQL.
    """
    from datetime import date as _date, timedelta as _td
    latest_ss_cte = """
        SELECT s.*
        FROM screener_snapshots s
        INNER JOIN (
            SELECT ticker, MAX(scraped_at) AS max_ts
            FROM screener_snapshots
            WHERE scraped_at >= datetime('now', '-2 days')
            GROUP BY ticker
        ) lts ON s.ticker = lts.ticker AND s.scraped_at = lts.max_ts
    """
    latest_sig_cte = """
        SELECT ticker, rating, composite_score, momentum_score, insider_score
        FROM signal_scores
        WHERE DATE(scored_at) = DATE((SELECT MAX(scored_at) FROM signal_scores))
    """

    conn = get_connection(db_path)
    cur  = conn.cursor()

    def q(sql, params=()):
        cur.execute(sql, params)
        row = cur.fetchone()
        return (row[0] or 0) if row else 0

    # strong_buy_momentum: STRONG_BUY, score≥70, momentum≥70, price≥5
    strong_buy_momentum = q(f"""
        SELECT COUNT(*) FROM ({latest_ss_cte}) ss
        JOIN ({latest_sig_cte}) sig ON ss.ticker = sig.ticker
        WHERE sig.rating = 'STRONG_BUY'
          AND sig.composite_score >= 70
          AND sig.momentum_score >= 70
          AND ss.price >= 5
    """)

    # dividend_powerhouses: yield≥3, good rating, joined with screener data
    dividend_powerhouses = q(f"""
        SELECT COUNT(DISTINCT ss.ticker) FROM ({latest_ss_cte}) ss
        JOIN ({latest_sig_cte}) sig ON ss.ticker = sig.ticker
        JOIN dividends dv ON ss.ticker = dv.ticker
        WHERE dv.dividend_yield >= 3
          AND sig.rating IN ('STRONG_BUY','BUY','STRONG_HOLD')
    """)

    # buy_the_dip: rsi≤35, STRONG_BUY/BUY/STRONG_HOLD
    buy_the_dip = q(f"""
        SELECT COUNT(*) FROM ({latest_ss_cte}) ss
        JOIN ({latest_sig_cte}) sig ON ss.ticker = sig.ticker
        WHERE ss.rsi_14 <= 35
          AND sig.rating IN ('STRONG_BUY','BUY','STRONG_HOLD')
    """)

    # earnings_this_week: upcoming earnings, must also be in screener data
    future_date = (_date.today() + _td(days=7)).isoformat()
    earnings_this_week = q(f"""
        SELECT COUNT(DISTINCT ec.ticker)
        FROM earnings_calendar ec
        JOIN ({latest_ss_cte}) ss ON ec.ticker = ss.ticker
        WHERE ec.earnings_date BETWEEN DATE('now') AND ?
    """, (future_date,))

    # legally_clean: risk_label None/Minor, good rating
    # LEFT JOIN so tickers with no legal_risk record are treated as clean
    legally_clean = q(f"""
        SELECT COUNT(DISTINCT ss.ticker) FROM ({latest_ss_cte}) ss
        JOIN ({latest_sig_cte}) sig ON ss.ticker = sig.ticker
        LEFT JOIN legal_risk lr ON ss.ticker = lr.ticker
        WHERE (lr.risk_label IS NULL OR lr.risk_label IN ('None','Minor'))
          AND sig.rating IN ('STRONG_BUY','BUY','STRONG_HOLD')
    """)

    # insider_buying_surge: insider_score≥70, good rating
    insider_buying_surge = q(f"""
        SELECT COUNT(*) FROM ({latest_sig_cte}) sig
        WHERE sig.insider_score >= 70
          AND sig.rating IN ('STRONG_BUY','BUY','STRONG_HOLD')
    """)

    # undervalued: 20%+ below 52w high, good rating
    undervalued = q(f"""
        SELECT COUNT(*) FROM ({latest_ss_cte}) ss
        JOIN ({latest_sig_cte}) sig ON ss.ticker = sig.ticker
        WHERE ss.high_52w_pct <= -20
          AND sig.rating IN ('STRONG_BUY','BUY','STRONG_HOLD')
    """)

    conn.close()
    return {
        "strong_buy_momentum":  strong_buy_momentum,
        "dividend_powerhouses": dividend_powerhouses,
        "buy_the_dip":          buy_the_dip,
        "earnings_this_week":   earnings_this_week,
        "legally_clean":        legally_clean,
        "insider_buying_surge": insider_buying_surge,
        "undervalued":          undervalued,
    }


@app.route("/api/theme-counts")
@login_required
def api_theme_counts():
    """Return stock counts for all 7 discovery theme cards as JSON."""
    return jsonify(_compute_theme_counts(DATABASE_PATH))


@app.route("/api/economic-calendar/refresh", methods=["POST"])
@login_required
def api_economic_calendar_refresh():
    try:
        from scrapers.fmp_scraper import refresh_economic_calendar
        n = refresh_economic_calendar(DATABASE_PATH)
        return jsonify({"ok": True, "saved": n})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ── Markets ─────────────────────────────────────────────────────────────────

@app.route("/markets")
@login_required
def markets_page():
    from config.markets import MAJOR_INDICES, SP_SECTORS, CURRENCIES, CRYPTO_TOP_10
    return render_template(
        "markets.html",
        user=current_user(),
        indices=MAJOR_INDICES,
        sectors=SP_SECTORS,
        currencies=CURRENCIES,
        crypto=CRYPTO_TOP_10,
    )


@app.route("/markets/<path:symbol>")
@login_required
def market_chart_page(symbol):
    from config.markets import MAJOR_INDICES, SP_SECTORS, CURRENCIES, CRYPTO_TOP_10
    all_items = MAJOR_INDICES + SP_SECTORS + CURRENCIES + CRYPTO_TOP_10
    label = next((i["label"] for i in all_items if i.get("tv") == symbol or i.get("symbol") == symbol), symbol)
    return render_template("market_chart.html", user=current_user(), tv_symbol=symbol, label=label)


@app.route("/api/market-sessions")
@login_required
def api_market_sessions():
    from utils.market_sessions import get_all_sessions
    return jsonify(get_all_sessions())


@app.route("/api/markets/<path:symbol>")
@login_required
def api_market_symbol(symbol):
    rows = db_query(
        "SELECT date, close FROM market_history WHERE symbol = ? ORDER BY date ASC",
        (symbol,),
    )
    if not rows:
        return jsonify({"symbol": symbol, "data": [], "latest": None,
                        "prev_close": None, "change_pct": 0}), 200

    data = [{"time": r["date"], "value": r["close"]}
            for r in rows if r["close"] is not None]
    if not data:
        return jsonify({"symbol": symbol, "data": [], "latest": None,
                        "prev_close": None, "change_pct": 0}), 200

    latest    = data[-1]["value"]
    prev_close = data[-2]["value"] if len(data) >= 2 else latest
    change_pct = ((latest - prev_close) / prev_close * 100) if prev_close else 0

    return jsonify({
        "symbol":     symbol,
        "data":       data,
        "latest":     latest,
        "prev_close": prev_close,
        "change_pct": round(change_pct, 2),
    })


@app.route("/screener")
@login_required
def screener():
    user = current_user()
    sectors = db_query("""
        SELECT DISTINCT sector FROM screener_snapshots
        WHERE sector IS NOT NULL ORDER BY sector
    """)
    return render_template("screener.html", user=user,
                           sectors=[r["sector"] for r in sectors])


@app.route("/api/screener")
@login_required
def api_screener():
    """
    Filterable screener endpoint. All params are optional query strings:
    sector, rating (comma-sep), score_min, score_max,
    mcap (any/micro/small/mid/large), pe_min, pe_max,
    rsi_min, rsi_max, upside_min,
    exchange (comma-sep: NYSE, NASDAQ, AMEX, Other),
    momentum_score_min, insider_score_min, volume_min,
    high_52w_pct_max, dividend_yield_min, earnings_days, legally_clean,
    sort (column), dir (asc/desc), page, per_page
    """
    sector    = request.args.get("sector", "")
    ratings   = [r for r in request.args.get("rating", "").split(",") if r]
    score_min = request.args.get("score_min", type=float, default=0)
    score_max = request.args.get("score_max", type=float, default=100)
    mcap      = request.args.get("mcap", "any")
    pe_min    = request.args.get("pe_min", type=float)
    pe_max    = request.args.get("pe_max", type=float)
    rsi_min   = request.args.get("rsi_min", type=float)
    rsi_max   = request.args.get("rsi_max", type=float)
    upside_min = request.args.get("upside_min", type=float)
    short_min  = request.args.get("short_min", type=float)
    price_max  = request.args.get("price_max", type=float)
    price_min  = request.args.get("price_min", type=float)
    relvol_min = request.args.get("relvol_min", type=float)
    # Theme-specific params
    momentum_score_min  = request.args.get("momentum_score_min", type=float)
    insider_score_min   = request.args.get("insider_score_min", type=float)
    volume_min          = request.args.get("volume_min", type=float)
    high_52w_pct_max    = request.args.get("high_52w_pct_max", type=float)
    dividend_yield_min  = request.args.get("dividend_yield_min", type=float)
    earnings_days       = request.args.get("earnings_days", type=int)
    legally_clean_param = request.args.get("legally_clean", "").lower() in ("1", "true", "yes")
    exchanges  = [e for e in request.args.get("exchange", "").split(",") if e]
    sort_col  = request.args.get("sort", "composite_score")
    sort_dir  = request.args.get("dir", "desc").lower()
    page      = max(1, request.args.get("page", type=int, default=1))
    per_page  = min(200, request.args.get("per_page", type=int, default=50))

    # Registry-derived: component sort columns come from sortable_columns();
    # screener_extras holds only the non-component screener columns. The two
    # unioned reproduce the prior 25-element set exactly (screener is already
    # a superset of the sortable component columns).
    screener_extras = {
        "ticker", "company", "sector", "market_cap", "composite_score",
        "target_price", "target_upside", "price", "change_pct", "volume",
        "pe_ratio", "rsi_14", "rating", "high_52w_pct", "low_52w_pct",
        "short_interest_pct", "insider_transactions", "beta",
        "rel_volume", "avg_volume", "exchange",
    }
    allowed_sorts = set(sortable_columns()) | screener_extras
    if sort_col not in allowed_sorts:
        sort_col = "composite_score"
    if sort_dir not in ("asc", "desc"):
        sort_dir = "desc"

    # Base FROM: one row per ticker (latest scraped_at in last 2 days).
    # This prevents market_cap ambiguity when a ticker has multiple scraped rows
    # with different (or NULL) market_cap values within the window.
    latest_ss = """
        SELECT s.*
        FROM screener_snapshots s
        INNER JOIN (
            SELECT ticker, MAX(scraped_at) AS max_ts
            FROM screener_snapshots
            WHERE scraped_at >= datetime('now', '-2 days')
            GROUP BY ticker
        ) lts ON s.ticker = lts.ticker AND s.scraped_at = lts.max_ts
    """

    where = ["1=1"]
    params = []

    if sector:
        where.append("ss.sector = ?")
        params.append(sector)
    if ratings:
        placeholders = ",".join("?" * len(ratings))
        where.append(f"sig.rating IN ({placeholders})")
        params.extend(ratings)
    if score_min > 0:
        where.append("sig.composite_score >= ?")
        params.append(score_min)
    if score_max < 100:
        where.append("sig.composite_score <= ?")
        params.append(score_max)
    if mcap == "micro":
        where.append("(ss.market_cap IS NULL OR ss.market_cap = '' OR CAST(ss.market_cap AS REAL) < 300000000)")
    elif mcap == "small":
        where.append("CAST(ss.market_cap AS REAL) >= 300000000 AND CAST(ss.market_cap AS REAL) < 2000000000")
    elif mcap == "mid":
        where.append("CAST(ss.market_cap AS REAL) >= 2000000000 AND CAST(ss.market_cap AS REAL) < 10000000000")
    elif mcap == "large":
        where.append("CAST(ss.market_cap AS REAL) >= 10000000000")
    if pe_min is not None:
        where.append("ss.pe_ratio >= ?")
        params.append(pe_min)
    if pe_max is not None:
        where.append("ss.pe_ratio <= ?")
        params.append(pe_max)
    if rsi_min is not None:
        where.append("ss.rsi_14 >= ?")
        params.append(rsi_min)
    if rsi_max is not None:
        where.append("ss.rsi_14 <= ?")
        params.append(rsi_max)
    if upside_min is not None:
        where.append("sig.target_upside >= ?")
        params.append(upside_min)
    if short_min is not None:
        where.append("ss.short_interest_pct >= ?")
        params.append(short_min)
    if price_max is not None:
        where.append("ss.price <= ?")
        params.append(price_max)
    if price_min is not None:
        where.append("ss.price >= ?")
        params.append(price_min)
    if relvol_min is not None:
        where.append("ss.rel_volume >= ?")
        params.append(relvol_min)
    if exchanges:
        placeholders = ",".join("?" * len(exchanges))
        where.append(f"COALESCE(tm.exchange, 'Other') IN ({placeholders})")
        params.extend(exchanges)
    # Theme-specific conditions
    if momentum_score_min is not None:
        where.append("sig.momentum_score >= ?")
        params.append(momentum_score_min)
    if insider_score_min is not None:
        where.append("sig.insider_score >= ?")
        params.append(insider_score_min)
    if volume_min is not None:
        where.append("ss.volume >= ?")
        params.append(volume_min)
    if high_52w_pct_max is not None:
        where.append("ss.high_52w_pct <= ?")
        params.append(high_52w_pct_max)

    # Optional JOINs (dividend, earnings, legal)
    extra_joins = []
    if dividend_yield_min is not None:
        extra_joins.append("JOIN dividends dv ON ss.ticker = dv.ticker")
        where.append("dv.dividend_yield >= ?")
        params.append(dividend_yield_min)
    if earnings_days is not None:
        from datetime import date as _date, timedelta as _td
        future = (_date.today() + _td(days=earnings_days)).isoformat()
        extra_joins.append("JOIN earnings_calendar ec ON ss.ticker = ec.ticker")
        where.append("ec.earnings_date BETWEEN DATE('now') AND ?")
        params.append(future)
    if legally_clean_param:
        extra_joins.append("LEFT JOIN legal_risk lr ON ss.ticker = lr.ticker")
        where.append("(lr.risk_label IS NULL OR lr.risk_label IN ('None','Minor'))")

    extra_joins_sql = "\n        ".join(extra_joins)
    where_sql = " AND ".join(where)

    # Map sort column to correct table prefix
    _ss_cols = {"ticker","company","sector","market_cap","price","change_pct","volume",
                "pe_ratio","rsi_14","high_52w_pct","low_52w_pct",
                "short_interest_pct","insider_transactions","beta",
                "eps_growth_this_yr","eps_growth_next_yr",
                "rel_volume","avg_volume"}
    _sig_cols = {"rating","composite_score","target_price","target_upside",
                 "momentum_score","quality_score","insider_score","reversion_score",
                 "sector_strength_score"}
    # Columns stored as TEXT but containing numeric values, must cast for correct sort order
    _numeric_text_cols = {"market_cap"}
    if sort_col in _ss_cols:
        if sort_col in _numeric_text_cols:
            order_sql = f"CAST(ss.{sort_col} AS REAL) {sort_dir.upper()} NULLS LAST"
        else:
            order_sql = f"ss.{sort_col} {sort_dir.upper()} NULLS LAST"
    elif sort_col in _sig_cols:
        order_sql = f"sig.{sort_col} {sort_dir.upper()} NULLS LAST"
    elif sort_col == "exchange":
        order_sql = f"tm.exchange {sort_dir.upper()} NULLS LAST"
    else:
        order_sql = f"sig.composite_score DESC NULLS LAST"
    offset    = (page - 1) * per_page

    _subq_proj = signal_scores_projection(
        surface='screener',
        extras=('ticker', 'rating', 'composite_score', 'target_price', 'target_upside'),
    )
    sig_subq = f"""
        SELECT {_subq_proj},
               MAX(scored_at) as scored_at
        FROM signal_scores
        WHERE DATE(scored_at) = DATE((SELECT MAX(scored_at) FROM signal_scores))
        GROUP BY ticker
    """

    count_rows = db_query(f"""
        SELECT COUNT(*) as total
        FROM ({latest_ss}) ss
        LEFT JOIN ({sig_subq}) sig ON ss.ticker = sig.ticker
        LEFT JOIN ticker_metadata tm ON ss.ticker = tm.ticker
        {extra_joins_sql}
        WHERE {where_sql}
    """, params)
    total = count_rows[0]["total"] if count_rows else 0

    _sig_proj = signal_scores_projection(
        prefix='sig.',
        surface='screener',
        extras=('rating', 'composite_score', 'target_price', 'target_upside'),
    )
    rows = db_query(f"""
        SELECT ss.ticker, ss.company, ss.sector,
               ss.market_cap, ss.price, ss.change_pct, ss.volume,
               ss.pe_ratio, ss.rsi_14,
               ss.high_52w_pct, ss.low_52w_pct,
               ss.eps_growth_this_yr, ss.eps_growth_next_yr,
               ss.short_interest_pct, ss.insider_transactions, ss.beta,
               ss.rel_volume, ss.avg_volume, tm.exchange,
               {_sig_proj}
        FROM ({latest_ss}) ss
        LEFT JOIN ({sig_subq}) sig ON ss.ticker = sig.ticker
        LEFT JOIN ticker_metadata tm ON ss.ticker = tm.ticker
        {extra_joins_sql}
        WHERE {where_sql}
        ORDER BY {order_sql}
        LIMIT ? OFFSET ?
    """, params + [per_page, offset])

    target_count = sum(1 for r in rows if r.get("target_price") is not None)
    target_banner = None
    if rows and target_count < len(rows) * 0.5:
        target_banner = "Target prices are being recalculated. Check back shortly."

    # Price-aware score gate. Per-row strip via the shared helper.
    # Penny rows ($1-5) lose composite + sub-scores + rating + targets
    # for non-elite. The $5 boundary lives in can_view_score_for_ticker;
    # no parallel price logic here. target_banner is computed BEFORE the
    # strip on purpose, it reflects backend data freshness, not the
    # caller's tier view.
    tier = effective_tier(current_user())
    rows = strip_scores_for_non_elite(rows, tier, price_key='price')

    return jsonify({
        "rows":          rows,
        "total":         total,
        "page":          page,
        "per_page":      per_page,
        "pages":         max(1, (total + per_page - 1) // per_page),
        "target_banner": target_banner,
    })


@app.route("/api/ticker/<ticker>")
@login_required
def api_ticker(ticker):
    ticker = ticker.upper()
    user   = current_user()

    screener = db_query("""
        SELECT * FROM screener_snapshots WHERE ticker = ?
        ORDER BY scraped_at DESC LIMIT 1
    """, (ticker,))

    metadata_row = db_query(
        "SELECT * FROM ticker_metadata WHERE ticker = ?", (ticker,)
    )

    _signal_proj = signal_scores_projection(
        surface='ticker',
        extras=('rating', 'composite_score', 'target_price',
                'target_upside', 'sector_modifier_applied'),
    )
    signal = db_query(f"""
        SELECT {_signal_proj} FROM signal_scores WHERE ticker = ?
        ORDER BY scored_at DESC LIMIT 1
    """, (ticker,))

    insiders = db_query("""
        SELECT * FROM insider_trades WHERE ticker = ?
        ORDER BY transaction_date DESC LIMIT 20
    """, (ticker,))

    news = db_query("""
        SELECT * FROM news_sentiment WHERE ticker = ?
        ORDER BY scraped_at DESC LIMIT 20
    """, (ticker,))

    history = db_query("""
        SELECT DATE(scored_at) as date,
               MAX(composite_score) as composite_score, rating
        FROM signal_scores WHERE ticker = ?
        GROUP BY DATE(scored_at)
        ORDER BY date ASC
    """, (ticker,))

    # Fair Value calculation (P/E vs sector average)
    sc = screener[0] if screener else None
    sc = dict(sc) if sc else {}
    tm = dict(metadata_row[0]) if metadata_row else {}
    fair_value = None
    fv_discount = None
    fv_label = None
    if sc.get('pe_ratio') and sc.get('sector') and sc.get('price'):
        sector_pe = db_query("""
            SELECT ROUND(AVG(pe_ratio),1) as avg_pe, ROUND(AVG(roe),1) as avg_roe
            FROM screener_snapshots
            WHERE sector = ? AND pe_ratio > 0 AND pe_ratio < 200
        """, (sc['sector'],))
        if sector_pe and sector_pe[0]['avg_pe']:
            avg_pe = sector_pe[0]['avg_pe']
            avg_roe = sector_pe[0]['avg_roe'] or 15
            stock_pe = sc['pe_ratio']
            price = sc['price']
            # Simple fair value: if P/E below sector avg, stock is undervalued
            fair_value = round(price * (avg_pe / stock_pe), 2)
            fv_discount = round(((fair_value - price) / price) * 100, 1)
            if fv_discount > 15:
                fv_label = 'UNDERVALUED'
            elif fv_discount < -15:
                fv_label = 'OVERVALUED'
            else:
                fv_label = 'FAIR VALUE'

    # Technical summary
    tech = {'buy': 0, 'neutral': 0, 'sell': 0, 'signals': []}
    if sc:
        rsi = sc.get('rsi_14')
        sma50 = sc.get('sma_50_pct')
        sma200 = sc.get('sma_200_pct')
        high52 = sc.get('high_52w_pct')
        low52 = sc.get('low_52w_pct')

        if rsi:
            if rsi < 35:
                tech['buy'] += 1; tech['signals'].append({'name':'RSI(14)','value':round(rsi,1),'signal':'BUY'})
            elif rsi > 65:
                tech['sell'] += 1; tech['signals'].append({'name':'RSI(14)','value':round(rsi,1),'signal':'SELL'})
            else:
                tech['neutral'] += 1; tech['signals'].append({'name':'RSI(14)','value':round(rsi,1),'signal':'NEUTRAL'})

        if sma50 is not None:
            if sma50 > 0:
                tech['buy'] += 1; tech['signals'].append({'name':'SMA 50','value':round(sma50,1),'signal':'BUY'})
            else:
                tech['sell'] += 1; tech['signals'].append({'name':'SMA 50','value':round(sma50,1),'signal':'SELL'})

        if sma200 is not None:
            if sma200 > 0:
                tech['buy'] += 1; tech['signals'].append({'name':'SMA 200','value':round(sma200,1),'signal':'BUY'})
            else:
                tech['sell'] += 1; tech['signals'].append({'name':'SMA 200','value':round(sma200,1),'signal':'SELL'})

        if high52 is not None:
            if high52 > -10:
                tech['buy'] += 1; tech['signals'].append({'name':'52W High','value':round(high52,1),'signal':'BUY'})
            elif high52 < -30:
                tech['sell'] += 1; tech['signals'].append({'name':'52W High','value':round(high52,1),'signal':'SELL'})
            else:
                tech['neutral'] += 1; tech['signals'].append({'name':'52W High','value':round(high52,1),'signal':'NEUTRAL'})

        if low52 is not None:
            if low52 > 50:
                tech['buy'] += 1; tech['signals'].append({'name':'52W Low','value':round(low52,1),'signal':'BUY'})
            else:
                tech['neutral'] += 1; tech['signals'].append({'name':'52W Low','value':round(low52,1),'signal':'NEUTRAL'})

        total = tech['buy'] + tech['neutral'] + tech['sell']
        if total > 0:
            if tech['buy'] > tech['sell'] + tech['neutral']:
                tech['overall'] = 'BUY'
            elif tech['sell'] > tech['buy'] + tech['neutral']:
                tech['overall'] = 'SELL'
            else:
                tech['overall'] = 'NEUTRAL'
        else:
            tech['overall'] = 'NEUTRAL'

    # Check watchlist membership
    in_watchlist = False
    user_watchlists = []
    ticker_watchlist_ids = set()
    if user:
        wl_rows = db_query(
            "SELECT watchlist_id FROM watchlists WHERE user_id=? AND ticker=?",
            (user["id"], ticker)
        )
        ticker_watchlist_ids = {r["watchlist_id"] for r in wl_rows}
        in_watchlist = bool(ticker_watchlist_ids)
        user_watchlists = get_watchlists_meta(DATABASE_PATH, user["id"])

    legal = get_legal_risk(ticker)
    if legal is None:
        legal = {"risk_level": "NONE", "risk_label": "No data", "risk_color": "#6b7280", "penalty": 0}

    analyst_ts = db_query(
        "SELECT MAX(scraped_at) as ts FROM screener_snapshots WHERE ticker = ? AND analyst_recom IS NOT NULL",
        (ticker,)
    )
    analyst_updated_at = analyst_ts[0]['ts'] if analyst_ts and analyst_ts[0]['ts'] else None

    next_earnings_date = None
    try:
        from scrapers.fmp_scraper import _ensure_tables
        _ensure_tables(DATABASE_PATH)
        ec = db_query(
            "SELECT earnings_date FROM earnings_calendar WHERE ticker = ? AND earnings_date >= DATE('now') ORDER BY earnings_date ASC LIMIT 1",
            (ticker,)
        )
        if ec:
            next_earnings_date = ec[0]['earnings_date']
    except Exception:
        pass

    # Sector performance ranking for bar chart on ticker page
    sector_perf = db_query("""
        SELECT sector, etf_symbol, return_7d, return_30d, rank_7d, sector_strength_score
        FROM sector_performance
        WHERE date = (SELECT MAX(date) FROM sector_performance)
        ORDER BY rank_7d ASC
    """)
    sector_perf_list = [dict(r) for r in sector_perf] if sector_perf else []

    # Score-panel gate (price-aware). For non-elite + penny band ($1-5),
    # strip signal/history/technical/fair_value to teaser values; surface
    # "locked": True. The $5 boundary lives in can_view_score_for_ticker.
    # Do NOT reimplement it inline. price=None fails closed (elite-only).
    tier = effective_tier(user)
    price = sc.get('price')
    score_visible = can_view_score_for_ticker(tier, price)

    payload = {
        "ticker":               ticker,
        "screener":             sc,
        "metadata":             tm,
        "signal":               dict(signal[0]) if (signal and score_visible) else {},
        "insiders":             insiders,
        "news":                 news,
        "history":              history if score_visible else [],
        "in_watchlist":         in_watchlist,
        "user_watchlists":      user_watchlists,
        "ticker_watchlist_ids": list(ticker_watchlist_ids),
        "fair_value":           ({"estimated": fair_value, "discount_pct": fv_discount, "label": fv_label} if fair_value else None) if score_visible else None,
        "technical":            tech if score_visible else None,
        "legal_risk":           legal,
        "analyst_updated_at":   analyst_updated_at,
        "next_earnings_date":   next_earnings_date,
        "sector_performance":   sector_perf_list,
    }
    if not score_visible:
        payload["locked"] = True

    # Elite-strict sub-score gate (additive, layered on top of the
    # price-band score-visible gate above). The four positive sub-scores
    # plus the Altman distress penalty are Elite-only on this surface
    # regardless of price; pro/free never receive them in the JSON. The
    # base eight components and composite stay visible to pro as today.
    # subscores_locked is the explicit teaser-vs-section flag for the
    # template: do NOT infer lock state from key absence, since an elite
    # user on a data-poor ticker can have legitimately NULL sub-scores.
    if payload["signal"]:
        strip_subscores_for_non_elite(payload["signal"], tier)
    payload["subscores_locked"] = (tier != 'elite')
    return jsonify(payload)


@app.route("/api/ticker/<ticker>/events")
@login_required
def api_ticker_events(ticker):
    ticker = ticker.upper()
    events = []

    # Score-panel gate: rating events embed composite_score in their detail
    # string. For non-elite + penny band, skip the rating_changes query
    # entirely (gate-before-fetch). Insider/legal/earnings still emit,
    # factual record, not proprietary score output.
    tier = effective_tier(current_user())
    price_row = db_query(
        "SELECT price FROM screener_snapshots WHERE ticker = ? ORDER BY scraped_at DESC LIMIT 1",
        (ticker,)
    )
    price = price_row[0]['price'] if price_row else None
    score_visible = can_view_score_for_ticker(tier, price)

    if score_visible:
        # Rating changes (last 15)
        rc = db_query("""
            SELECT change_date as date, old_rating, new_rating, price_at_change, composite_score
            FROM rating_changes WHERE ticker = ?
            ORDER BY change_date DESC LIMIT 15
        """, (ticker,))
        for r in rc:
            up_tiers = {'STRONG_BUY','BUY','STRONG_HOLD'}
            down_tiers = {'SELL','STRONG_SELL','WEAK_HOLD'}
            direction = 'up' if r['new_rating'] in up_tiers else 'down' if r['new_rating'] in down_tiers else 'neutral'
            new_label = tier_short(r['new_rating'])
            if r['old_rating']:
                title = f"Rating changed: {tier_short(r['old_rating'])} → {new_label}"
            else:
                title = f"Rating set: {new_label}"
            events.append({
                'type': 'rating',
                'date': r['date'],
                'title': title,
                'detail': f"Score {r['composite_score']:.1f} · Price ${r['price_at_change']:.2f}" if r['composite_score'] and r['price_at_change'] else None,
                'direction': direction,
                'new_rating': r['new_rating'],
            })

    # Insider trades (last 10)
    it = db_query("""
        SELECT transaction_date as date, insider_name, insider_title, transaction_type, shares, price, value
        FROM insider_trades WHERE ticker = ?
        ORDER BY transaction_date DESC LIMIT 10
    """, (ticker,))
    for r in it:
        is_buy = (r['transaction_type'] or '').upper() in ('BUY','P - PURCHASE','PURCHASE')
        val_str = f"${r['value']:,.0f}" if r['value'] else ''
        sh_str  = f"{int(r['shares']):,} shares" if r['shares'] else ''
        events.append({
            'type': 'insider',
            'date': r['date'],
            'title': f"Insider {'Buy' if is_buy else 'Sell'}: {r['insider_name'] or 'Unknown'} ({r['insider_title'] or ''})",
            'detail': ' · '.join(filter(None, [sh_str, val_str])),
            'direction': 'up' if is_buy else 'down',
            'new_rating': None,
        })

    # Legal risk entry
    lr = db_query("""
        SELECT scraped_at as date, risk_level, risk_label, filing_type
        FROM legal_risk WHERE ticker = ?
        ORDER BY scraped_at DESC LIMIT 1
    """, (ticker,))
    if lr:
        r = lr[0]
        direction = 'down' if r['risk_level'] not in ('NONE','MINOR') else 'neutral'
        events.append({
            'type': 'legal',
            'date': (r['date'] or '')[:10],
            'title': f"Legal risk assessed: {r['risk_label'] or r['risk_level']}",
            'detail': f"Filing: {r['filing_type']}" if r['filing_type'] else None,
            'direction': direction,
            'new_rating': None,
        })

    # Upcoming earnings
    ec = db_query("""
        SELECT earnings_date as date, timing, eps_estimate, eps_last_year
        FROM earnings_calendar WHERE ticker = ? AND earnings_date >= DATE('now')
        ORDER BY earnings_date ASC LIMIT 1
    """, (ticker,))
    for r in ec:
        est = f"EPS est. ${r['eps_estimate']:.2f}" if r['eps_estimate'] else None
        events.append({
            'type': 'earnings',
            'date': r['date'],
            'title': f"Earnings report ({r['timing'] or 'TBD'})",
            'detail': est,
            'direction': 'neutral',
            'new_rating': None,
        })

    # Sort all events by date desc, take last 10
    events.sort(key=lambda e: e['date'] or '', reverse=True)
    payload = {'events': events[:10]}
    if not score_visible:
        payload['locked'] = True
    return jsonify(payload)


@app.route("/api/run_log")
@login_required
def api_run_log():
    return jsonify(db_query(
        "SELECT * FROM run_log ORDER BY run_at DESC LIMIT 50"
    ))



@app.route("/api/portfolios")
@login_required
def api_portfolios():
    user = current_user()
    rows = db_query("SELECT * FROM portfolios WHERE user_id = ? AND is_active = 1 ORDER BY created_at DESC", (user["id"],))
    return jsonify(rows)

@app.route("/api/portfolios/create", methods=["POST"])
@login_required
def api_create_portfolio():
    user = current_user()
    data = request.get_json()
    count = db_query("SELECT COUNT(*) as c FROM portfolios WHERE user_id = ? AND is_active = 1", (user["id"],))
    if count[0]["c"] >= 5:
        return jsonify({"error": "Maximum 5 portfolios allowed"}), 400
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Portfolio name required"}), 400
    balance = float(data.get("starting_balance", 10000))
    conn = get_connection(DATABASE_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO portfolios (user_id, name, description, starting_balance, cash_balance, created_at) VALUES (?,?,?,?,?,?)",
        (user["id"], name, data.get("description",""), balance, balance, datetime.now().isoformat()))
    conn.commit()
    return jsonify({"id": cur.lastrowid, "message": "Portfolio created"})

@app.route("/api/portfolios/<int:portfolio_id>")
@login_required
def api_portfolio_detail(portfolio_id):
    user = current_user()
    port = db_query("SELECT * FROM portfolios WHERE id = ? AND user_id = ?", (portfolio_id, user["id"]))
    if not port:
        return jsonify({"error": "Not found"}), 404
    port = port[0]
    holdings = db_query("""
        SELECT h.*, s.price as current_price, sig.rating, sig.composite_score
        FROM portfolio_holdings h
        LEFT JOIN (SELECT ticker, price FROM screener_snapshots GROUP BY ticker) s ON h.ticker = s.ticker
        LEFT JOIN (SELECT ticker, rating, composite_score FROM signal_scores 
                   WHERE DATE(scored_at) = DATE((SELECT MAX(scored_at) FROM signal_scores))
                   GROUP BY ticker) sig ON h.ticker = sig.ticker
        WHERE h.portfolio_id = ?
    """, (portfolio_id,))
    transactions = db_query("SELECT * FROM portfolio_transactions WHERE portfolio_id = ? ORDER BY executed_at DESC LIMIT 50", (portfolio_id,))
    
    # Calculate P&L for each holding
    total_value = port["cash_balance"]
    for h in holdings:
        cp = h.get("current_price") or h["avg_buy_price"]
        if h["direction"] == "LONG":
            pnl = (cp - h["avg_buy_price"]) * h["shares"] * h["leverage"]
        else:
            pnl = (h["avg_buy_price"] - cp) * h["shares"] * h["leverage"]
        h["pnl"] = round(pnl, 2)
        h["pnl_pct"] = round((pnl / (h["avg_buy_price"] * h["shares"])) * 100, 2)
        h["current_price"] = cp
        position_value = cp * h["shares"]
        total_value += position_value
    
    port["total_value"] = round(total_value, 2)
    port["total_return"] = round(total_value - port["starting_balance"], 2)
    port["total_return_pct"] = round(((total_value - port["starting_balance"]) / port["starting_balance"]) * 100, 2)

    # Price-aware score gate on holdings. A free user holding penny
    # tickers loses rating/composite for those positions; their pnl,
    # shares, avg_buy_price, current_price all remain visible.
    tier = effective_tier(user)
    strip_scores_for_non_elite(holdings, tier, price_key='current_price')

    return jsonify({"portfolio": port, "holdings": holdings, "transactions": transactions})

@app.route("/api/portfolios/<int:portfolio_id>/trade", methods=["POST"])
@login_required
def api_trade(portfolio_id):
    user = current_user()
    port = db_query("SELECT * FROM portfolios WHERE id = ? AND user_id = ?", (portfolio_id, user["id"]))
    if not port:
        return jsonify({"error": "Not found"}), 404
    port = port[0]
    data = request.get_json()
    
    ticker   = data.get("ticker","").upper()
    action   = data.get("action","").upper()  # BUY, SELL, SHORT, COVER
    shares   = float(data.get("shares", 0))
    leverage = int(data.get("leverage", 1))
    direction = "SHORT" if action in ["SHORT","COVER"] else "LONG"
    
    # Get current price
    price_row = db_query("SELECT price FROM screener_snapshots WHERE ticker = ? ORDER BY scraped_at DESC LIMIT 1", (ticker,))
    if not price_row:
        return jsonify({"error": "Ticker not found"}), 404
    price = float(price_row[0]["price"])
    total = price * shares
    margin_required = total / leverage

    conn = get_connection(DATABASE_PATH)
    cur = conn.cursor()

    if action in ["BUY", "SHORT"]:
        if port["cash_balance"] < margin_required:
            return jsonify({"error": "Insufficient funds"}), 400
        # Check existing holding
        existing = db_query("SELECT * FROM portfolio_holdings WHERE portfolio_id = ? AND ticker = ? AND direction = ?",
            (portfolio_id, ticker, direction))
        if existing:
            e = existing[0]
            new_shares = e["shares"] + shares
            new_avg = ((e["avg_buy_price"] * e["shares"]) + (price * shares)) / new_shares
            cur.execute("UPDATE portfolio_holdings SET shares=?, avg_buy_price=?, current_price=?, margin_used=margin_used+? WHERE id=?",
                (new_shares, new_avg, price, margin_required, e["id"]))
        else:
            cur.execute("INSERT INTO portfolio_holdings (portfolio_id, ticker, shares, avg_buy_price, current_price, direction, leverage, margin_used, opened_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (portfolio_id, ticker, shares, price, price, direction, leverage, margin_required, datetime.now().isoformat()))
        cur.execute("UPDATE portfolios SET cash_balance=cash_balance-? WHERE id=?", (margin_required, portfolio_id))

    elif action in ["SELL", "COVER"]:
        existing = db_query("SELECT * FROM portfolio_holdings WHERE portfolio_id = ? AND ticker = ? AND direction = ?",
            (portfolio_id, ticker, direction))
        if not existing:
            return jsonify({"error": "No position to close"}), 400
        e = existing[0]
        if shares > e["shares"]:
            return jsonify({"error": "Cannot sell more than you hold"}), 400
        if direction == "LONG":
            pnl = (price - e["avg_buy_price"]) * shares * e["leverage"]
        else:
            pnl = (e["avg_buy_price"] - price) * shares * e["leverage"]
        proceeds = (e["margin_used"] / e["shares"]) * shares + pnl
        if e["shares"] - shares < 0.0001:
            cur.execute("DELETE FROM portfolio_holdings WHERE id=?", (e["id"],))
        else:
            cur.execute("UPDATE portfolio_holdings SET shares=shares-?, margin_used=margin_used-? WHERE id=?",
                (shares, (e["margin_used"]/e["shares"])*shares, e["id"]))
        cur.execute("UPDATE portfolios SET cash_balance=cash_balance+? WHERE id=?", (proceeds, portfolio_id))

    # Log transaction
    cur.execute("INSERT INTO portfolio_transactions (portfolio_id, ticker, type, shares, price, total_value, leverage, direction, executed_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (portfolio_id, ticker, action, shares, price, total, leverage, direction, datetime.now().isoformat()))
    
    conn.commit()
    return jsonify({"message": f"{action} executed", "price": price, "total": total})

@app.route("/api/portfolios/<int:portfolio_id>/check_margins", methods=["POST"])
@login_required  
def api_check_margins(portfolio_id):
    holdings = db_query("""
        SELECT h.*, s.price as current_price
        FROM portfolio_holdings h
        LEFT JOIN (SELECT ticker, price FROM screener_snapshots GROUP BY ticker) s ON h.ticker = s.ticker
        WHERE h.portfolio_id = ?
    """, (portfolio_id,))
    
    margin_calls = []
    conn = get_connection(DATABASE_PATH)
    cur = conn.cursor()
    
    for h in holdings:
        cp = h.get("current_price") or h["avg_buy_price"]
        if h["direction"] == "LONG":
            pnl = (cp - h["avg_buy_price"]) * h["shares"] * h["leverage"]
        else:
            pnl = (h["avg_buy_price"] - cp) * h["shares"] * h["leverage"]
        margin_loss_pct = abs(pnl) / h["margin_used"] * 100 if h["margin_used"] > 0 else 0
        
        if pnl < 0 and margin_loss_pct >= 100:
            # BUST - auto liquidate
            cur.execute("DELETE FROM portfolio_holdings WHERE id=?", (h["id"],))
            cur.execute("UPDATE portfolios SET cash_balance=cash_balance+? WHERE id=?", 
                (max(0, h["margin_used"] + pnl), portfolio_id))
            cur.execute("INSERT INTO margin_calls (portfolio_id, holding_id, ticker, margin_level, status, issued_at, resolved_at) VALUES (?,?,?,?,?,?,?)",
                (portfolio_id, h["id"], h["ticker"], margin_loss_pct, "BUSTED", datetime.now().isoformat(), datetime.now().isoformat()))
            margin_calls.append({"ticker": h["ticker"], "status": "BUSTED"})
        elif pnl < 0 and margin_loss_pct >= 75:
            cur.execute("INSERT OR IGNORE INTO margin_calls (portfolio_id, holding_id, ticker, margin_level, status, issued_at) VALUES (?,?,?,?,?,?)",
                (portfolio_id, h["id"], h["ticker"], margin_loss_pct, "WARNING", datetime.now().isoformat()))
            margin_calls.append({"ticker": h["ticker"], "status": "WARNING", "margin_level": margin_loss_pct})
    
    conn.commit()
    # Check if portfolio is fully bust
    port = db_query("SELECT * FROM portfolios WHERE id=?", (portfolio_id,))
    if port and port[0]["cash_balance"] <= 0 and not holdings:
        cur.execute("UPDATE portfolios SET is_active=0 WHERE id=?", (portfolio_id,))
        conn.commit()
        return jsonify({"bust": True, "margin_calls": margin_calls})
    
    return jsonify({"bust": False, "margin_calls": margin_calls})


@app.route("/backtest")
@login_required
def backtest():
    user = current_user()
    try:
        conn = get_connection(DATABASE_PATH)
        cur = conn.cursor()
        cur.execute(
            "SELECT DISTINCT scoring_version FROM rating_changes "
            "WHERE scoring_version IS NOT NULL ORDER BY scoring_version"
        )
        available_versions = [r[0] for r in cur.fetchall()]
        conn.close()
    except Exception:
        available_versions = []
    if not available_versions:
        available_versions = [SCORING_ENGINE_VERSION]
    return render_template(
        "backtest.html", user=user,
        scoring_version=SCORING_ENGINE_VERSION,
        available_versions=available_versions,
    )

@app.route("/api/backtest/stats")
@login_required
def api_backtest_stats():
    from collections import defaultdict
    try:
        return _api_backtest_stats_inner()
    except Exception as e:
        logger.error(f"[Backtest] stats endpoint error: {e}", exc_info=True)
        return jsonify({"stats": [], "recent": [], "sector_comparison": {"note": f"Data temporarily unavailable: {e}"},
                        "message": "Backtest data temporarily unavailable. Check server logs."})

def _api_backtest_stats_inner():
    from collections import defaultdict
    version = request.args.get("version", SCORING_ENGINE_VERSION)
    conn = get_connection(DATABASE_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT
            rc1.new_rating,
            rc1.ticker,
            rc1.price_at_change as entry_price,
            rc1.change_date as entry_date,
            rc2.price_at_change as exit_price,
            rc2.change_date as exit_date,
            ROUND(((rc2.price_at_change - rc1.price_at_change) / rc1.price_at_change) * 100, 2) as return_pct,
            CAST(julianday(rc2.change_date) - julianday(rc1.change_date) AS INTEGER) as days_held
        FROM rating_changes rc1
        JOIN rating_changes rc2
            ON rc1.ticker = rc2.ticker
            AND rc2.change_date > rc1.change_date
            AND NOT EXISTS (
                SELECT 1 FROM rating_changes rc3
                WHERE rc3.ticker = rc1.ticker
                AND rc3.change_date > rc1.change_date
                AND rc3.change_date < rc2.change_date
            )
        WHERE rc1.price_at_change IS NOT NULL
        AND rc2.price_at_change IS NOT NULL
        AND rc1.price_at_change > 0
        AND COALESCE(rc1.scoring_version, '0.9.0') = ?
    """, (version,))
    periods = cur.fetchall()

    stats = defaultdict(lambda: {'returns':[], 'wins':0, 'total':0, 'days':[], 'trades':[]})
    for p in periods:
        r, rating = p['return_pct'], p['new_rating']
        if r is None: continue
        stats[rating]['returns'].append(r)
        stats[rating]['days'].append(p['days_held'] or 0)
        stats[rating]['total'] += 1
        is_win = (r < 0) if rating in ('STRONG_SELL', 'SELL', 'WEAK_HOLD') else (r > 0)
        if is_win: stats[rating]['wins'] += 1
        stats[rating]['trades'].append({
            'ticker':      p['ticker'],
            'entry_date':  p['entry_date'],
            'entry_price': p['entry_price'],
            'exit_price':  p['exit_price'],
            'return_pct':  r,
            'days_held':   p['days_held'] or 0,
        })

    # Recent changes feed
    cur.execute("""
        SELECT ticker, old_rating, new_rating, price_at_change, change_date, composite_score
        FROM rating_changes
        WHERE old_rating IS NOT NULL
          AND COALESCE(scoring_version, '0.9.0') = ?
        ORDER BY change_date DESC, id DESC
        LIMIT 50
    """, (version,))
    recent = [dict(r) for r in cur.fetchall()]
    conn.close()

    result = []
    for rating in ['STRONG_BUY','BUY','STRONG_HOLD','HOLD','WEAK_HOLD','SELL','STRONG_SELL']:
        s = stats.get(rating)
        if not s or not s['returns']: continue
        avg = sum(s['returns']) / len(s['returns'])
        win_rate = (s['wins'] / s['total'] * 100) if s['total'] > 0 else 0
        avg_days = sum(s['days']) / len(s['days']) if s['days'] else 0
        all_trades = sorted(s['trades'], key=lambda x: x['return_pct'], reverse=True)
        result.append({
            'rating':       rating,
            'avg_return':   round(avg, 2),
            'win_rate':     round(win_rate, 1),
            'samples':      s['total'],
            'avg_days_held': round(avg_days, 1),
            'trades':       all_trades[:20],
        })

    # Sector comparison: top-3 vs bottom-3 sector Strong Buys
    # Uses current sector rankings as proxy (historical sector data accumulates over time)
    sector_comparison = {"top_avg": None, "bottom_avg": None, "spread": None,
                         "top_n": 0, "bottom_n": 0, "note": ""}
    try:
        # Get current sector rankings
        sp_rows = db_query("""
            SELECT sector, rank_7d FROM sector_performance
            WHERE date = (SELECT MAX(date) FROM sector_performance)
        """)
        top_sectors    = {r["sector"] for r in sp_rows if r["rank_7d"] and r["rank_7d"] <= 3}
        bottom_sectors = {r["sector"] for r in sp_rows if r["rank_7d"] and r["rank_7d"] >= 9}

        # Strong Buy periods with sector info
        sb_periods = db_query("""
            SELECT rc1.ticker,
                   ROUND(((rc2.price_at_change - rc1.price_at_change) / rc1.price_at_change) * 100, 2) as return_pct,
                   CAST(julianday(rc2.change_date) - julianday(rc1.change_date) AS INTEGER) as days_held,
                   (SELECT sector FROM screener_snapshots WHERE ticker = rc1.ticker ORDER BY scraped_at DESC LIMIT 1) as sector
            FROM rating_changes rc1
            JOIN rating_changes rc2
                ON rc1.ticker = rc2.ticker
                AND rc2.change_date > rc1.change_date
                AND NOT EXISTS (
                    SELECT 1 FROM rating_changes rc3
                    WHERE rc3.ticker = rc1.ticker
                    AND rc3.change_date > rc1.change_date
                    AND rc3.change_date < rc2.change_date
                )
            WHERE rc1.new_rating = 'STRONG_BUY'
              AND rc1.price_at_change IS NOT NULL AND rc1.price_at_change > 0
              AND rc2.price_at_change IS NOT NULL
              AND CAST(julianday(rc2.change_date) - julianday(rc1.change_date) AS INTEGER) >= 30
        """)

        top_returns    = [r["return_pct"] for r in sb_periods if r["sector"] in top_sectors and r["return_pct"] is not None]
        bottom_returns = [r["return_pct"] for r in sb_periods if r["sector"] in bottom_sectors and r["return_pct"] is not None]
        top_avg    = round(sum(top_returns) / len(top_returns), 2) if top_returns else None
        bottom_avg = round(sum(bottom_returns) / len(bottom_returns), 2) if bottom_returns else None
        spread     = round(top_avg - bottom_avg, 2) if top_avg is not None and bottom_avg is not None else None

        sector_comparison = {
            "top_avg": top_avg, "bottom_avg": bottom_avg, "spread": spread,
            "top_n": len(top_returns), "bottom_n": len(bottom_returns),
            "top_sectors": sorted(top_sectors), "bottom_sectors": sorted(bottom_sectors),
            "note": "Uses current sector rankings as proxy. Historical accuracy improves as daily sector data accumulates." if sp_rows else "No sector data yet.",
        }
    except Exception as e:
        sector_comparison["note"] = f"Sector comparison unavailable: {e}"

    # Price-aware score gate on the two leak surfaces of this endpoint:
    #   (1) `recent` carries per-trade composite + new_rating + old_rating,
    #       direct strip via the helper, price_key='price_at_change'.
    #   (2) `stats[].trades` carries no rating field per-trade, but the
    #       parent dict's 'rating' tier name + the trade's ticker would
    #       let a non-elite caller infer rating-by-penny-ticker. Helper
    #       can't null fields that don't exist; structural filter drops
    #       penny-band trades from each tier's list. Aggregate stats
    #       (avg_return, win_rate, samples) computed BEFORE this filter
    #       those are cohort-level, not per-ticker, so they stay.
    tier = effective_tier(current_user())
    strip_scores_for_non_elite(recent, tier, price_key='price_at_change')
    if tier != 'elite':
        for entry in result:
            entry['trades'] = [
                t for t in entry['trades']
                if can_view_score_for_ticker(tier, t.get('entry_price'))
            ]

    return jsonify({
        'stats': result,
        'recent': recent,
        'sector_comparison': sector_comparison,
        'version': version,
        'current_version': SCORING_ENGINE_VERSION,
    })



@app.route('/news/<ticker>')
@login_required
def ticker_news(ticker):
    conn = get_connection(DATABASE_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT headline, url, source, published, sentiment
        FROM news_sentiment
        WHERE ticker = ?
        ORDER BY scraped_at DESC
        LIMIT 50
    """, (ticker,))
    articles = [dict(r) for r in cur.fetchall()]
    conn.close()
    return render_template('ticker_news.html', ticker=ticker, articles=articles)

# ── Penny & Small Cap ─────────────────────────────────

def _penny_why(stock):
    reasons = []
    ms  = stock.get("momentum_score") or 0
    qs  = stock.get("quality_score")  or 0
    ins = stock.get("insider_score")  or 0
    rev = stock.get("reversion_score") or 0
    rsi = stock.get("rsi_14")
    upside = stock.get("target_upside")
    cs  = stock.get("composite_score") or 0

    if ms >= 75:
        reasons.append(f"Strong price momentum (score {ms:.0f}/100). Trending above key moving averages with sustained upward pressure.")
    elif ms >= 55:
        reasons.append(f"Building momentum (score {ms:.0f}/100). Early signs of upward trend emerging.")
    if ins >= 70:
        reasons.append(f"Significant insider buying activity (score {ins:.0f}/100). Company insiders actively increasing their stake, the strongest conviction signal available.")
    if qs >= 65:
        reasons.append(f"Solid fundamentals for a penny stock (quality score {qs:.0f}/100). Above-average business metrics relative to its peer group.")
    if rsi and rsi < 33:
        reasons.append(f"Oversold RSI at {rsi:.0f}. Potential mean reversion bounce back toward the mean.")
    if upside and upside > 25:
        reasons.append(f"Model target price implies {upside:.0f}% potential upside from current levels.")
    if not reasons:
        reasons.append(f"Highest composite signal score ({cs:.0f}/100) among penny stocks in today's scan. No single dominant driver but the strongest overall reading in this universe.")
    return reasons


def _select_penny_stock_of_day():
    today = datetime.utcnow().date().isoformat()
    conn = get_connection(DATABASE_PATH)
    cur  = conn.cursor()

    # Return today's pick if already computed
    cur.execute("SELECT ticker FROM penny_stock_of_day WHERE date = ?", (today,))
    row = cur.fetchone()
    if row:
        conn.close()
        return row[0]

    # Select best penny stock. Prefer STRONG_BUY/BUY, then highest composite
    cur.execute("""
        SELECT ss.ticker, sig.composite_score, sig.rating
        FROM screener_snapshots ss
        JOIN signal_scores sig ON ss.ticker = sig.ticker
        WHERE ss.scraped_at = (SELECT MAX(scraped_at) FROM screener_snapshots)
          AND sig.scored_at = (SELECT MAX(scored_at) FROM signal_scores)
          AND ss.price > 0 AND ss.price < 5
          AND sig.composite_score IS NOT NULL
        ORDER BY
            CASE sig.rating
                WHEN 'STRONG_BUY' THEN 1
                WHEN 'BUY'        THEN 2
                WHEN 'STRONG_HOLD'THEN 3
                ELSE 4
            END ASC,
            sig.composite_score DESC
        LIMIT 1
    """)
    pick = cur.fetchone()
    if pick:
        cur.execute(
            "INSERT OR REPLACE INTO penny_stock_of_day (date, ticker, composite_score, rating) VALUES (?,?,?,?)",
            (today, pick[0], pick[1], pick[2])
        )
        conn.commit()
        ticker = pick[0]
    else:
        ticker = None
    conn.close()
    return ticker


@app.route("/penny")
@login_required
def penny():
    user = current_user()
    # Server-driven locked decision (4d). Template renders the
    # locked-teaser when locked=True and does NOT fire the /api/penny/*
    # XHRs, avoids the empty-loading flash on a known-gated state.
    tier = effective_tier(user)
    locked = not can_view_penny_signals(tier)
    return render_template("penny.html", user=user, locked=locked)


@app.route("/penny/screener")
@login_required
def penny_screener():
    user = current_user()
    tier = effective_tier(user)
    # Page renders for all tiers. Per-row score cells are gated server-side by
    # strip_scores_for_non_elite in /api/screener; non-elite callers see a
    # single upsell banner above the table (rendered when tier != 'elite').
    return render_template("penny_screener.html", user=user, tier=tier)


def _get_penny_pick_full(db_path: str) -> "dict | None":
    """Resolve today's penny pick and return the full enriched record.

    Returns None if no pick exists yet. Used by /api/penny/stock-of-day
    (JSON endpoint) and by the Elite branch of the /dashboard route.
    Real penny-pick data must NEVER reach a non-Elite client. Callers gate.
    """
    ticker = _select_penny_stock_of_day()
    if not ticker:
        return None

    rows = db_query(f"""
        SELECT ss.ticker, ss.company, ss.sector, ss.industry,
               ss.price, ss.change_pct, ss.volume, ss.rsi_14,
               ss.high_52w_pct, ss.low_52w_pct, ss.rel_volume, ss.avg_volume,
               ss.market_cap, ss.beta,
               sig.rating, sig.composite_score,
               {signal_scores_projection(prefix='sig.', surface='signals')},
               sig.target_price, sig.target_upside,
               lr.risk_label, lr.risk_color, lr.penalty
        FROM screener_snapshots ss
        JOIN signal_scores sig ON ss.ticker = sig.ticker
        LEFT JOIN legal_risk lr ON ss.ticker = lr.ticker
        WHERE ss.ticker = ?
          AND ss.scraped_at = (SELECT MAX(scraped_at) FROM screener_snapshots)
          AND sig.scored_at = (SELECT MAX(scored_at) FROM signal_scores)
        LIMIT 1
    """, (ticker,))

    if not rows:
        return None

    stock = rows[0]
    stock["why"] = _penny_why(stock)
    return stock


@app.route("/api/penny/stock-of-day")
@login_required
def api_penny_stock_of_day():
    # Penny signals are Elite-only. Gate BEFORE the fetch. _get_penny_pick_full
    # must not run for a non-elite caller. "locked": True distinguishes this
    # response from the existing no-pick-today branch below ({"stock": None}).
    tier = effective_tier(current_user())
    if not can_view_penny_signals(tier):
        return jsonify({"stock": None, "locked": True})
    stock = _get_penny_pick_full(DATABASE_PATH)
    if not stock:
        return jsonify({"stock": None})
    return jsonify({"stock": stock, "date": datetime.utcnow().date().isoformat()})


@app.route("/api/penny/hot")
@login_required
def api_penny_hot():
    # Penny signals are Elite-only. Gate BEFORE the exchange loop. No
    # query fires for a non-elite caller. Empty per-exchange arrays plus
    # "locked": True so the client can distinguish a gated response from
    # a genuinely empty result.
    tier = effective_tier(current_user())
    if not can_view_penny_signals(tier):
        return jsonify({"NASDAQ": [], "NYSE": [], "OTC": [], "locked": True})

    # One row per ticker (latest snapshot + latest signal score)
    lts_sq = """
        SELECT ticker, MAX(scraped_at) AS max_ts
        FROM screener_snapshots
        WHERE scraped_at >= datetime('now', '-2 days')
        GROUP BY ticker
    """
    sig_sq = """
        SELECT ticker, rating, composite_score, MAX(scored_at) AS scored_at
        FROM signal_scores
        WHERE DATE(scored_at) = DATE((SELECT MAX(scored_at) FROM signal_scores))
        GROUP BY ticker
    """

    exchanges = ["NASDAQ", "NYSE", "OTC"]
    result = {}
    for exch in exchanges:
        rows = db_query(f"""
            SELECT ss.ticker, ss.company, ss.price, ss.change_pct, ss.volume,
                   sig.rating, sig.composite_score
            FROM screener_snapshots ss
            INNER JOIN ({lts_sq}) lts ON ss.ticker = lts.ticker AND ss.scraped_at = lts.max_ts
            LEFT JOIN ({sig_sq}) sig ON ss.ticker = sig.ticker
            INNER JOIN ticker_metadata tm ON ss.ticker = tm.ticker
            WHERE ss.price > 0 AND ss.price < 5
              AND tm.exchange = ?
              AND ss.change_pct IS NOT NULL
            ORDER BY ABS(ss.change_pct) DESC
            LIMIT 5
        """, (exch,))
        result[exch] = rows

    # Fallback: if no exchange data, return top movers regardless of exchange
    has_data = any(result[e] for e in exchanges)
    if not has_data:
        top = db_query(f"""
            SELECT ss.ticker, ss.company, ss.price, ss.change_pct, ss.volume,
                   sig.rating, sig.composite_score
            FROM screener_snapshots ss
            INNER JOIN ({lts_sq}) lts ON ss.ticker = lts.ticker AND ss.scraped_at = lts.max_ts
            LEFT JOIN ({sig_sq}) sig ON ss.ticker = sig.ticker
            WHERE ss.price > 0 AND ss.price < 5
              AND ss.change_pct IS NOT NULL
            ORDER BY ABS(ss.change_pct) DESC
            LIMIT 15
        """)
        return jsonify({"no_exchange": True, "movers": top})

    return jsonify(result)


# ── Ticker tape ───────────────────────────────────────

@app.route("/api/ticker-tape")
@login_required
def api_ticker_tape():
    """Top ~40 movers from today's screener for the scrolling tape."""
    conn = get_connection(DATABASE_PATH)
    cur  = conn.cursor()
    cur.execute("""
        SELECT ss.ticker, ss.price, ss.change_pct, sig.rating
        FROM screener_snapshots ss
        INNER JOIN (
            SELECT ticker, MAX(scraped_at) AS max_ts
            FROM screener_snapshots
            WHERE scraped_at >= datetime('now', '-2 days')
            GROUP BY ticker
        ) lts ON ss.ticker = lts.ticker AND ss.scraped_at = lts.max_ts
        LEFT JOIN (
            SELECT ticker, rating, MAX(scored_at) AS scored_at
            FROM signal_scores
            WHERE DATE(scored_at) = DATE((SELECT MAX(scored_at) FROM signal_scores))
            GROUP BY ticker
        ) sig ON ss.ticker = sig.ticker
        WHERE ss.price IS NOT NULL AND ss.change_pct IS NOT NULL
          AND ABS(ss.change_pct) > 0
        ORDER BY ABS(ss.change_pct) DESC
        LIMIT 40
    """)
    rows = cur.fetchall()
    conn.close()
    tape = [
        {"ticker": r[0], "price": r[1], "change_pct": r[2], "rating": r[3]}
        for r in rows
    ]
    # Price-aware score gate. Tape carries 'rating' on every row;
    # penny rows lose rating for non-elite (the only proprietary field
    # on this endpoint, composite/sub-scores are not exposed here).
    tier = effective_tier(current_user())
    strip_scores_for_non_elite(tape, tier, price_key='price')
    return jsonify(tape)


# ── Static / public pages ─────────────────────────────

@app.route("/pricing")
def pricing():
    """Public pricing discovery surface.

    Posture A (beta-free) is locked: the page shows the real launch
    numbers but every CTA routes to /register (trial signup), NOT to
    Stripe checkout. Logged-in visitors see a single neutral beta
    banner instead of per-column CTAs. No DB lookup, no tier check,
    only "user_id" in session is read. Currency resolved via the
    existing precedence helper.
    """
    currency = _resolve_currency_from_request(request)
    symbol = "£" if currency == "gbp" else "$"

    def _fmt(minor_units):
        whole, frac = divmod(int(minor_units), 100)
        if frac == 0:
            return f"{symbol}{whole}"
        return f"{symbol}{whole}.{frac:02d}"

    paid_tiers = ("pro", "elite")
    prices = {
        tier: {
            "monthly": _fmt(LAUNCH_PRICING[tier][currency]["monthly"]),
            "annual":  _fmt(LAUNCH_PRICING[tier][currency]["annual"]),
        }
        for tier in paid_tiers
    }

    display_names = {key: get_tier(key)["display_name"] for key in ("free", "pro", "elite")}

    logged_in = "user_id" in session

    return render_template(
        "pricing.html",
        currency=currency,
        prices=prices,
        annual_discount_pct=ANNUAL_DISCOUNT_PCT,
        features=TIER_FEATURES,
        display_names=display_names,
        logged_in=logged_in,
    )


@app.route("/about")
def about():
    return render_template("about.html", user=current_user())

@app.route("/contact", methods=["GET", "POST"])
def contact():
    success = False
    if request.method == "POST":
        name    = request.form.get("name", "").strip()
        email   = request.form.get("email", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()
        if name and email and subject and message:
            conn = get_connection(DATABASE_PATH)
            conn.execute(
                "INSERT INTO contact_submissions (name, email, subject, message) VALUES (?,?,?,?)",
                (name, email, subject, message)
            )
            conn.commit()
            conn.close()
            _send_telegram(f"📧 New contact form submission from {name}: {subject}")
            success = True
    return render_template("contact.html", user=current_user(), success=success)

@app.route("/privacy")
def privacy():
    return render_template("privacy.html", user=current_user())

@app.route("/terms")
def terms():
    return render_template("terms.html", user=current_user())

@app.route("/disclaimer")
def disclaimer():
    return render_template("disclaimer.html", user=current_user())


if __name__ == '__main__':
    print("=" * 50)
    print("  SignalIntel Web Dashboard")
    print("  Open: http://localhost:5001")
    print("=" * 50)
    app.run(debug=False, host="0.0.0.0", port=5001)
