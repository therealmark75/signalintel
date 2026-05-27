# Stripe Billing — Phase 1 Diagnostic Inventory

**Date:** 2026-05-27
**Status:** Diagnostic complete. **No application code written. No Stripe objects created.**
**Scope:** Inventory existing state, identify gaps, propose Phase 2 build order. Stops at the end for Mark's review and decisions.

**Locked design assumptions (from prompt; not revisited here):**
- Trial model: no-card. The 7-day trial is the `config/entitlements.py` overlay. Stripe does NOT run the trial. Stripe enters only at conversion.
- Pricing locked at: Pro $29/mo · £24.99/mo; Elite $79/mo · £74.99/mo; annual = 25% off both tiers, both currencies. Currency is geo-based with explicit per-currency prices (NOT live FX). 8 price points total (2 tiers × 2 currencies × 2 intervals).

**Surprises surfaced (flag for Mark):**
1. `CLAUDE.md` § Business Model still says "Annual billing at 20% discount" and "Free 7-day trial → Starter / Pro / Elite tiers." The locked Phase 2 spec is **25%** annual and **2** paid tiers (Pro, Elite + free + 7-day overlay). `CLAUDE.md` is stale on both points. Recommend updating `CLAUDE.md` before Phase 2 closes (out of scope here — surfaced, not modified).
2. No `.env` or `.env.example` file exists at the project root. Stripe secrets (publishable key, secret key, webhook signing secret) will need an env strategy decided in Phase 2.

---

## 1. Schema write paths — the four Stripe columns

### EXISTS — live schema dump

Source: `sqlite3 data/trading_system.db ".schema users"`

```
CREATE TABLE users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    NOT NULL UNIQUE,
            email         TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            created_at    TEXT    NOT NULL,
            is_active     INTEGER DEFAULT 1
        , tier TEXT NOT NULL DEFAULT 'free', trial_started_at TEXT, stripe_customer_id TEXT, stripe_subscription_id TEXT, tier_effective_until TEXT);
CREATE INDEX idx_users_stripe_customer
        ON users(stripe_customer_id)
    ;
CREATE INDEX idx_users_stripe_subscription
        ON users(stripe_subscription_id)
    ;
```

All four columns exist in the live DB, all `TEXT`, all default `NULL`. Two webhook-lookup indexes are present.

### EXISTS — schema definition and migration

Source: `grep -rn "trial_started_at\|stripe_customer_id\|stripe_subscription_id\|tier_effective_until" --include="*.py" --include="*.html" --include="*.md" --include="*.sql"`

Schema definition (`database/db.py`):
```
731:            trial_started_at       TEXT,
732:            stripe_customer_id     TEXT,
733:            stripe_subscription_id TEXT,
734:            tier_effective_until   TEXT
```

Idempotent migration (`database/db.py`):
```
792:    if 'trial_started_at' not in user_cols:
793:        cur.execute("ALTER TABLE users ADD COLUMN trial_started_at TEXT")
795:    if 'stripe_customer_id' not in user_cols:
796:        cur.execute("ALTER TABLE users ADD COLUMN stripe_customer_id TEXT")
798:    if 'stripe_subscription_id' not in user_cols:
799:        cur.execute("ALTER TABLE users ADD COLUMN stripe_subscription_id TEXT")
801:    if 'tier_effective_until' not in user_cols:
802:        cur.execute("ALTER TABLE users ADD COLUMN tier_effective_until TEXT")
```

Indexes (`database/db.py`):
```
808:        ON users(stripe_customer_id)
812:        ON users(stripe_subscription_id)
```

### EXISTS — read sites

`trial_started_at` is **read** in `config/entitlements.py` only:
```
43:    """Parse a stored trial_started_at TEXT value into naive UTC datetime.
62:    """True iff user has a valid trial_started_at within the trial window.
66:      - trial_started_at missing / None / empty
67:      - trial_started_at malformed (not parseable as ISO)
68:      - trial_started_at parses but (_now - then) >= TRIAL_DAYS
72:    parsed = _parse_trial_start(user.get('trial_started_at'))
```

`stripe_customer_id` and `stripe_subscription_id` have **no read sites** in production `.py`. Referenced only in:
- `database/db.py` (schema + indexes)
- `tests/test_user_schema.py` (column-existence assertions)
- `PROJECT_CONTEXT.md` / `HANDOFF.md` (docs)

`tier_effective_until` has **no read sites** in production `.py`. Referenced only in `database/db.py` (schema + migration), tests, and docs.

### GAP — write sites

**Zero application writes to any of the four columns.** The grep above returned no `UPDATE users SET trial_started_at`, no `UPDATE users SET stripe_*`, no `INSERT ... trial_started_at`, no `INSERT ... stripe_*` anywhere in production code or migrations beyond column creation itself. The four columns are entirely unpopulated today.

---

## 2. `register()` and what gets stamped on a fresh user

### EXISTS — `register()` literal code

Source: `web/app.py:199-226`

```python
199 @app.route("/register", methods=["GET","POST"])
200 def register():
201     if "user_id" in session:
202         return redirect(url_for("index"))
203     if request.method == "POST":
204         username = request.form.get("username","").strip()
205         email    = request.form.get("email","").strip()
206         password = request.form.get("password","")
207         confirm  = request.form.get("confirm","")
208         if not username or not email or not password:
209             flash("All fields required")
210         elif password != confirm:
211             flash("Passwords do not match")
212         elif len(password) < 8:
213             flash("Password must be at least 8 characters")
214         elif get_user_by_username(DATABASE_PATH, username):
215             flash("Username already taken")
216         elif get_user_by_email(DATABASE_PATH, email):
217             flash("An account with that email already exists")
218         else:
219             pw_hash = generate_password_hash(password, method='pbkdf2:sha256')
220             user_id = create_user(DATABASE_PATH, username, email, pw_hash)
221             # Every new user gets a default watchlist immediately on signup.
222             create_default_watchlist(DATABASE_PATH, user_id)
223             session["user_id"]  = user_id
224             session["username"] = username
225             return redirect(url_for("index"))
226     return render_template("register.html")
```

### EXISTS — `create_user()` literal code

Source: `database/db.py:883-895`

```python
883 def create_user(db_path: str, username: str, email: str, password_hash: str) -> int:
884     conn = get_connection(db_path)
885     cur  = conn.cursor()
886     cur.execute("""
887         INSERT INTO users (username, email, password_hash, created_at)
888         VALUES (?, ?, ?, ?)
889     """, (username, email, password_hash, datetime.now().isoformat()))
890     conn.commit()
891     user_id = cur.lastrowid
892     conn.close()
893     return user_id
```

### Stored tier of a fresh registrant

`create_user()` writes only `(username, email, password_hash, created_at)`. The schema default `tier TEXT NOT NULL DEFAULT 'free'` (see § 1) applies, so a fresh registrant has `users.tier = 'free'` and `users.trial_started_at = NULL`.

### GAP — trial overlay never gets data

`config/entitlements.py:72` reads `user.get('trial_started_at')` and falls through to "no trial" when the value is `NULL`/missing. Because `create_user()` never stamps `trial_started_at`, **every new user today receives `tier='free'` with no trial overlay grant**. The 7-day elite overlay is wired but unreachable for any user created today.

Nothing in the codebase flips a user OFF trial or to paid tier — confirmed in § 7.

---

## 3. Webhook landing site

### EXISTS — preparation only

`database/db.py:808-812` documents intent: index comment "Indexes for Stripe webhook lookups (webhook itself lands in a later step)."

`tests/test_user_schema.py:127-128` documents intent:
> "The webhook will look up users by stripe_customer_id (on customer.* events) and by stripe_subscription_id (on …)"

### GAP — no webhook code, no Stripe SDK, no env

Source: `grep -rn "webhook\|/stripe\|stripe.api_key\|stripe.Webhook\|STRIPE_WEBHOOK_SECRET" --include="*.py"` — zero production hits.

`stripe` is **not** in `requirements.txt` (confirmed by `grep -n "^stripe\|^Stripe" requirements*.txt` → empty).

No `.env` or `.env.example` exists at project root (confirmed by `ls .env*` → "no matches found").

No Flask blueprints exist (confirmed by `grep -rn "Blueprint(\|register_blueprint" --include="*.py"` → empty). The app is single-file Flask in `web/app.py`. A new webhook route attaches to the existing `app` object directly.

### Proposed landing site

- **Route:** `POST /webhooks/stripe` (note plural `/webhooks/`; matches common convention and leaves room for future Sendgrid/Telegram webhooks).
- **File:** `web/app.py`, new route added below the existing `/register` and `/login` group. No blueprint needed at this stage (single-file Flask precedent).
- **Signature verification:** `stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)` — Stripe's reference pattern. No existing signature-verification utility in the codebase to model after (`grep -rn "hmac.compare_digest\|verify_signature"` → empty).

### Proposed Stripe events handled (minimum for no-card conversion flow)

Mark each is at-least-once delivered; idempotency log in § 6 handles duplicates.

| Stripe event | Trigger | Column writes |
|---|---|---|
| `checkout.session.completed` | First successful checkout. Carries `customer`, `subscription`, and the `customer_email` we used to attach our `user_id` via `client_reference_id`. | `stripe_customer_id`, `stripe_subscription_id`, plus the initial `users.tier` flip from "free" to "pro"/"elite" resolved via the subscription's `price.lookup_key`. Sets `tier_effective_until` to the subscription's `current_period_end`. |
| `customer.subscription.updated` | Renewal, plan change (pro↔elite), interval change (monthly↔annual). | Updates `users.tier` if the price changed, refreshes `tier_effective_until` to new `current_period_end`. |
| `customer.subscription.deleted` | Cancellation finalised (subscription actually ended, not just scheduled-to-end). | Cancellation behaviour — **DECISION REQUIRED** (see § 8). |
| `invoice.payment_failed` | Optional in Phase 2. Dunning belongs in a follow-up phase; flagged here so we don't forget. | Out of scope for first build. |

The `customer.subscription.created` event is intentionally **not** in the primary handler list: it fires before payment confirmation. We treat `checkout.session.completed` (which Stripe sends only after successful charge for `mode='subscription'`) as the conversion signal. This keeps the "no-card trial → first paid event" boundary clean.

---

## 4. Stripe Product / Price mapping (paper design only)

**Locked pricing — 8 price points, math verified:**

| Tier | Currency | Monthly | Annual (25% off) |
|---|---|---|---|
| Pro | USD | $29.00 | $261.00 (= 29 × 12 × 0.75) |
| Pro | GBP | £24.99 | £224.91 (= 24.99 × 12 × 0.75) |
| Elite | USD | $79.00 | $711.00 (= 79 × 12 × 0.75) |
| Elite | GBP | £74.99 | £674.91 (= 74.99 × 12 × 0.75) |

**Proposal: 2 Products, 8 Prices.**

- Product `signalintel_pro` ("SignalIntel Pro") — 4 Prices attached.
- Product `signalintel_elite` ("SignalIntel Elite") — 4 Prices attached.

**Lookup key scheme on each Price:**

```
pro_usd_monthly      pro_usd_annual
pro_gbp_monthly      pro_gbp_annual
elite_usd_monthly    elite_usd_annual
elite_gbp_monthly    elite_gbp_annual
```

Format: `<tier>_<currency>_<interval>`. Lowercase, underscore-separated. Deterministically parseable by `lookup_key.split('_')` in the webhook.

**Metadata on each Price (redundant safety):**

```json
{
  "tier": "pro" | "elite",
  "currency": "usd" | "gbp",
  "interval": "month" | "year"
}
```

This is belt-and-braces: the webhook resolves price → tier via `lookup_key` *and* validates against `metadata.tier`. If the two disagree, the webhook refuses the tier flip and logs to `subscription_events` with a failure status. Catches the failure mode where someone fat-fingers a Price in the Stripe dashboard.

**Why not store price IDs in the app config?** Stripe price IDs are environment-specific (different in test vs live). `lookup_key` is human-meaningful and stable across environments. The webhook fetches the Price by lookup_key when it needs to confirm, never by hardcoded ID. Checkout creation, conversely, *does* need to pass concrete Price IDs to Stripe — those get resolved at checkout-time via `stripe.Price.list(lookup_keys=[...])`, not stored in app config.

No Stripe objects created in this phase. This is the mapping on paper.

---

## 5. Currency resolution

### EXISTS — nothing usable

`grep -rn "CF-IPCountry\|cf-ipcountry\|geoip\|GeoIP\|X-Forwarded-For\|accept-language" --include="*.py"` → no application hits. The `country` token appears at `web/app.py:1325` but is `request.args.get("country", "")` for the **economic calendar filter** — UI filter input, not user geo.

`grep -rn "currency\|GBP\|USD\|£" --include="*.py"` — currency tokens in `config/markets.py` are **trading pair symbols** (EURUSD, GBPUSD), not user-facing currency. `terms.html` contains the prose "All prices are quoted in GBP unless otherwise stated" — display copy, not logic.

No Cloudflare deployment config in repo (no `wrangler.toml`, no `_headers`, no CF-specific code paths).

### GAP — geo-to-currency bridge does not exist

The webhook side is simple: incoming `price.currency` from the Stripe event tells us GBP vs USD on the way back, so no geo decision is needed at webhook time. The **checkout-creation** side is the gap: when a free/trialing user clicks "Upgrade", the app must decide which of the 8 Prices to hand to `stripe.checkout.Session.create()`, and that decision depends on knowing whether the user is in the UK or not.

Three viable approaches, ranked by cost/effort:

1. **Cloudflare `CF-IPCountry` header at the edge.** Cheapest, no infrastructure. Requires deploying SignalIntel behind Cloudflare (currently is not, per repo state). Pure header read inside the upgrade route. Two-letter ISO country: `GB → GBP, everything else → USD`.
2. **Server-side IP geolocation library or service.** `ip2country` Python library, or a free IP-API call. No deployment change required, but adds a runtime dependency and a lookup per upgrade-click. Cacheable per session.
3. **User profile field.** Add `users.country TEXT` and ask on registration. Most explicit, most accurate, requires schema change and registration-form change.

This is a decision for Mark — flagged below.

---

## 6. `subscription_events` table — webhook idempotency log

### EXISTS — concept only

`tests/test_user_schema.py` (line range cited by upstream inventory) references a "future subscription_events table." No migration, no model, no code creates it.

### Proposed schema

```sql
CREATE TABLE subscription_events (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    stripe_event_id    TEXT    NOT NULL UNIQUE,    -- Stripe's evt_... id; UNIQUE = idempotency lock
    event_type         TEXT    NOT NULL,           -- e.g. 'checkout.session.completed'
    user_id            INTEGER,                    -- FK to users.id (NULL if event can't be resolved to a user)
    stripe_customer_id TEXT,                       -- denormalised for audit-without-join
    received_at        TEXT    NOT NULL,           -- ISO timestamp when webhook received the event
    processed_at       TEXT,                       -- ISO timestamp when handler finished (NULL = in-flight or failed)
    status             TEXT    NOT NULL DEFAULT 'received',
                                                   -- 'received' | 'processed' | 'failed' | 'skipped'
    error_message      TEXT,                       -- populated if status='failed'
    tier_before        TEXT,                       -- snapshot for audit: what users.tier was before this event
    tier_after         TEXT,                       -- snapshot for audit: what users.tier became after this event
    raw_payload        TEXT                        -- full Stripe event JSON (for forensic replay)
);

CREATE INDEX idx_sub_events_user        ON subscription_events(user_id);
CREATE INDEX idx_sub_events_customer    ON subscription_events(stripe_customer_id);
CREATE INDEX idx_sub_events_received_at ON subscription_events(received_at);
```

**Idempotency mechanism.** First line of the webhook handler is `INSERT INTO subscription_events (stripe_event_id, …) VALUES (?, …)`. If Stripe redelivers the same event, the `UNIQUE` constraint on `stripe_event_id` fails, the handler catches `sqlite3.IntegrityError`, logs the duplicate, and returns `200 OK` to Stripe without touching the users table. No double tier flip.

**Audit.** `tier_before` / `tier_after` make it possible to reconstruct exactly what happened to a user's tier after the fact — "show me the Stripe event that flipped this user to elite" is one query.

**`raw_payload` storage.** SQLite TEXT, full JSON. Cheap. Lets us replay an event with the same logic if the handler logic later changes — Phase 3 nice-to-have.

---

## 7. Tier-flip write — single source verification

### EXISTS — `users.tier` reads (all via `effective_tier(user)`)

Source: `grep -rn "users.tier\|UPDATE users SET tier\|set_tier\|user\[.tier.\]\|user.get(.tier.)" --include="*.py"`

Production reads of the stored tier go through `config/entitlements.py`. Strong docstring discipline enforces the indirection (`effective_tier()`):

```
config/tiers.py:9:              tier — a trialist's stored users.tier is 'free' while the
config/entitlements.py:15:user['tier'] raw. The raw column is the post-trial floor only — using
config/entitlements.py:92:      stored      = user['tier'] coerced via get_tier semantics
config/entitlements.py:105:    raw = user.get('tier')
config/entitlements.py:119:# obtain from effective_tier(user). NEVER pass user['tier'] raw — the
config/entitlements.py:126:    `tier` MUST be effective_tier(user), never user['tier'] raw.
config/entitlements.py:140:    `tier` MUST be effective_tier(user), never user['tier'] raw.
config/entitlements.py:156:    `tier` MUST be effective_tier(user), never user['tier'] raw.
config/entitlements.py:164:    `tier` MUST be effective_tier(user), never user['tier'] raw.
config/entitlements.py:173:    `tier` MUST be effective_tier(user), never user['tier'] raw.
config/entitlements.py:181:    `tier` MUST be effective_tier(user), never user['tier'] raw.
```

### EXISTS — `users.tier` writes (test code only, not production)

```
tests/test_watchlists.py:158:    conn.execute("UPDATE users SET tier='pro' WHERE id=?", (uid,))
tests/test_smoke.py:277:    conn.execute("UPDATE users SET tier='pro' WHERE id=2")
tests/test_smoke.py:314:        conn.execute("UPDATE users SET tier='elite' WHERE id=2")
tests/test_smoke.py:340:# that fired UPDATE users SET tier='elite' for username='markn' if tier=='free'
tests/test_smoke.py:352:    conn.execute("UPDATE users SET tier=? WHERE id=?", (tier, user_id))
```

Every production-code write of `users.tier`: **none**. The webhook in Phase 2 will be the **first** production write of `users.tier` after the initial `create_user()` default. (The `tests/test_smoke.py:340` line is the *test guarding against* the BUG-001 regression where production code wrote `tier='elite'` unprompted — confirming the principle that production code does not write tier today.)

### EXISTS — no cached tier source

Source: `grep -rn "session\[.tier.\]\|TIER_CACHE\|tier_cache\|redis.*tier\|cache.*tier\|g\.tier\|g\.user_tier" --include="*.py"` → **zero hits anywhere in the codebase**.

`effective_tier(user)` recomputes from the row each call. Flask `session` stores only `user_id` and `username`, not tier (verified by `register()` at `web/app.py:223-224`).

### Load-bearing assumption — verified

**Flipping `users.tier` is sufficient.** There is no second tier store, no cache, no session copy. Every entitlement gate funnels through `effective_tier(user)` which reads the row at call-time. The webhook only needs to write `users.tier` (plus `tier_effective_until`, `stripe_customer_id`, `stripe_subscription_id`) — no cache invalidation, no event broadcast, no session refresh required.

### GAP — none for this item

Hypothesis confirmed empirically. Marks the architectural cleanest leverage point in the whole arc.

---

## 8. Cancellation path

### EXISTS — `is_active` filter on every user lookup

Source: `database/db.py`

```python
896 def get_user_by_email(db_path: str, email: str):
899     cur.execute("SELECT * FROM users WHERE email = ? AND is_active = 1", (email,))

905 def get_user_by_username(db_path: str, username: str):
908     cur.execute("SELECT * FROM users WHERE username = ? AND is_active = 1", (username,))

914 def get_user_by_id(db_path: str, user_id: int):
917     cur.execute("SELECT * FROM users WHERE id = ? AND is_active = 1", (user_id,))
```

A user with `is_active = 0` is invisible to every login flow and every session-based authentication path. They cannot log in; if they were already logged in, the next `get_user_by_id()` returns `None` and the session is effectively dead.

`HANDOFF.md:25` and surrounding notes state: "cancellation = deactivation path."

### EXISTS — soft-delete precedent

Portfolio deletion uses soft-delete (`is_active = 0`), confirmed via prior inventory at `web/app.py:2306`. The codebase pattern is established.

### GAP — no cancellation handler today

No code currently sets `users.is_active = 0` or changes `users.tier` away from a paid value. Neither user-facing ("delete my account") nor webhook-driven. Greps `is_active = 0`, `deactivate`, `cancel`, `/cancel`, `delete_account` against production `.py` return no matching handlers in `web/app.py`.

### DECISION REQUIRED — surfaced for Mark, not decided here

On `customer.subscription.deleted`, three plausible behaviours:

| Option | Behaviour | Implication |
|---|---|---|
| **A. Deactivate** | `users.is_active = 0` (leave `tier` as-is) | User cannot log in. Aligned with HANDOFF.md wording. Loses any "re-subscribe" reactivation flow without a sysadmin step. |
| **B. Drop to free** | `users.tier = 'free'` (leave `is_active = 1`) | User can still log in to watchlists, dashboard, basic features. Cleanest UX for win-back. Stripe IDs (`stripe_customer_id`) remain so re-subscribe reuses the same customer. |
| **C. Both** | `tier='free'` AND `is_active=0` | Defensive. Loses login *and* drops tier. Reactivation requires both flips. |

My read: **Option B** is the cleanest for SaaS reality (canceled users come back; making them re-register loses the existing Stripe customer linkage). Option A is what `HANDOFF.md` says today, but that wording predates this Stripe inventory and may not be load-bearing. **This is Mark's call — not mine.**

Note that `tier_effective_until` provides a middle ground regardless of which option is chosen: a user who cancels mid-period keeps elite/pro access until `tier_effective_until` passes, at which point a scheduled job (or just the entitlement layer reading `tier_effective_until` alongside `tier`) downgrades them. That logic is also unbuilt today — flagged here as a downstream design question for Phase 2.

---

## Proposed build order — Phase 2

Each step is sized for one atomic commit. The hook P23 rules apply throughout: `register()` and webhook code are auth-adjacent and require Mark's terminal for commit confirmation.

1. **Stamp `trial_started_at` at registration.** Modify `create_user()` (and `register()` if necessary) to write `trial_started_at = datetime.now().isoformat()` on user creation. Tests: new user receives elite overlay for 7 days then falls to free. (Auth-adjacent: hook will trip — surface diff to Mark, await approval, commit `--no-verify`.)
2. **Add `subscription_events` table.** Idempotent migration in `database/db.py:init_schema()`. Schema as specified in § 6. Test: `tests/test_subscription_events_schema.py` (column-existence parity, same pattern as `test_user_schema.py`).
3. **Pin `stripe` Python SDK.** Add `stripe==<latest>` to `requirements.txt`. No code import yet.
4. **Add Stripe config keys.** Decide env strategy (`.env`, OS env, Flask config file). Define `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`. **Update `docs/config_variable_classification.md`** to mark all three as `SECRET` (per CLAUDE.md guidance that this file is the authoritative secrets enumeration).
5. **Webhook route skeleton.** Add `POST /webhooks/stripe` in `web/app.py`. Signature verification only. Returns 200 on valid signature with a `subscription_events` row written at `status='received'`; returns 400 on invalid signature with no row written. No tier writes yet. Tests: signature-valid fixture passes, signature-invalid fixture 400s, duplicate `stripe_event_id` returns 200 without re-inserting.
6. **Webhook handler: `checkout.session.completed`.** Resolve `price.lookup_key` → `(tier, currency, interval)`. Write `stripe_customer_id`, `stripe_subscription_id`, `tier`, `tier_effective_until`. Update the `subscription_events` row with `tier_before`/`tier_after` and `status='processed'`. Auth-adjacent — same hook process as step 1.
7. **Webhook handler: `customer.subscription.updated`.** Refresh tier and `tier_effective_until`. Auth-adjacent.
8. **Webhook handler: `customer.subscription.deleted`.** Apply Mark's cancellation decision from § 8. Auth-adjacent.
9. **Currency / geo decision.** Implement chosen approach from § 5. May be small (CF-IPCountry header read) or larger (schema change for user country). Sized after Mark's decision.
10. **Checkout-creation route.** `GET /upgrade?tier=pro&interval=month` → resolve currency from § 9 → `stripe.checkout.Session.create()` with `client_reference_id=user_id`, `customer_email=user.email`, the matching Price by `lookup_key`, success/cancel URLs. Auth-adjacent.
11. **Create Stripe Products and Prices.** Run a one-shot script (or use Mark via dashboard, per his preference) to create the 2 Products and 8 Prices with the lookup_key scheme from § 4. Verify with `stripe.Price.list(lookup_keys=[...])`.
12. **End-to-end: Stripe test mode.** Real card-test flow: free user → upgrade → Stripe checkout → webhook fires → tier flips → user sees elite gates. Cancellation flow: same path, deletion event → § 8 behaviour applied.

Steps 1, 5, 6, 7, 8, 10 trip the P23 hook. Steps 2, 3, 4, 9, 11, 12 do not (assuming step 4 adds env handling without touching `web/app.py` auth surfaces — likely a separate `config/stripe.py` module).

---

## Decisions required from Mark before Phase 2 starts

1. **Cancellation behaviour (§ 8).** Pick A (deactivate), B (drop to free), or C (both). Default if no decision: B, with `HANDOFF.md` updated to match.
2. **Currency / geo source (§ 5).** Pick (a) Cloudflare header (requires deploying behind CF), (b) server-side IP lookup (which library/service?), or (c) `users.country` field on registration.
3. **Env strategy for Stripe secrets (§ 3 GAP).** `.env` file? OS env via shell? Flask config file? CLAUDE.md flags `docs/config_variable_classification.md` as the authoritative secrets enumeration — whatever you pick, the three Stripe keys go in that file.
4. **Who creates Stripe Products/Prices (§ 4, step 11).** Mark via dashboard then provides IDs/lookup_keys, or automated script that Mark runs against the live account?
5. **`tier_effective_until` enforcement (§ 8 note).** When a user cancels mid-period and keeps access until `current_period_end`, is the entitlement layer responsible for reading `tier_effective_until` (so a canceled user automatically drops on day-N), or does a scheduled job sweep expired subscriptions? Both work — the former is stateless and cleaner; the latter is explicit. Defer to Mark.
6. **`CLAUDE.md` updates (Surprises §).** Annual discount is 25% (not 20%). Paid tiers are Pro + Elite (not Starter + Pro + Elite). Update `CLAUDE.md` § Business Model at the start of Phase 2, or wait?

**STOP. Awaiting Mark's review of this inventory and decisions above before Phase 2.**
