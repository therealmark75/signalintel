# SignalIntel Tier Feature Matrix

> **Single source of truth for which features are available on each tier.**
> When adding a new gated feature, update this file first, then implement the gate.
> Numeric limits (watchlist count, etc.) are authoritative in `config/tiers.py` — this document describes *features*, not limits. If they diverge, `config/tiers.py` wins for code; fix this file to match.

---

## Tier Overview

| Tier | Price | Watchlist limit | Target audience |
|---|---|---|---|
| **Free** | $0 (7-day trial) | 2 | Evaluating the product |
| **Starter** | TBD | 5 | Active retail traders, basic signals |
| **Pro** | TBD | 20 | Serious traders, full backtest, API read |
| **Elite** | TBD | Unlimited | Power users, API write, early access |

> Trial length and pricing are set in `config/settings.py` (not yet wired). The table above reflects current design intent.

---

## Feature Matrix

✅ = Full access &nbsp; 🔒 = Locked (upgrade required) &nbsp; ⚠️ = Limited

| Feature | Free | Starter | Pro | Elite |
|---|:---:|:---:|:---:|:---:|
| **Signals & Scores** | | | | |
| Dashboard (top signals) | ✅ | ✅ | ✅ | ✅ |
| Signal Tiers page | ✅ | ✅ | ✅ | ✅ |
| Full signals table (`/screener`) | ✅ | ✅ | ✅ | ✅ |
| Ticker detail page | ✅ | ✅ | ✅ | ✅ |
| 12-month price target | ✅ | ✅ | ✅ | ✅ |
| Score breakdown (component bars) | ✅ | ✅ | ✅ | ✅ |
| Legal risk scoring | ✅ | ✅ | ✅ | ✅ |
| **Watchlists** | | | | |
| Named watchlists | ⚠️ (max 2) | ⚠️ (max 5) | ⚠️ (max 20) | ✅ (unlimited) |
| Add/remove tickers | ✅ | ✅ | ✅ | ✅ |
| % since added tracking | ✅ | ✅ | ✅ | ✅ |
| **Market Data** | | | | |
| Markets overview (`/markets`) | ✅ | ✅ | ✅ | ✅ |
| Earnings calendar (`/earnings`) | ✅ | ✅ | ✅ | ✅ |
| Dividends centre (`/dividends`) | ✅ | ✅ | ✅ | ✅ |
| Events calendar (`/events`) | ✅ | ✅ | ✅ | ✅ |
| **Research Tools** | | | | |
| Insider trades feed | ✅ | ✅ | ✅ | ✅ |
| Rating change history | ✅ | ✅ | ✅ | ✅ |
| Global search | ✅ | ✅ | ✅ | ✅ |
| Theme screener (signal themes) | ✅ | ✅ | ✅ | ✅ |
| **Backtesting** | | | | |
| Basic backtest (`/backtest`) | 🔒 | ✅ | ✅ | ✅ |
| Full backtest (all history) | 🔒 | 🔒 | ✅ | ✅ |
| **Penny & Speculative** | | | | |
| Penny Stock Hub (`/penny`) | 🔒 | 🔒 | 🔒 | ✅ |
| Penny Screener (`/penny/screener`) | 🔒 | 🔒 | 🔒 | ✅ |
| **Alerts** | | | | |
| Email alerts (SendGrid) | 🔒 | ✅ | ✅ | ✅ |
| Custom alert thresholds | 🔒 | 🔒 | ✅ | ✅ |
| **API Access** | | | | |
| API read (signal data) | 🔒 | 🔒 | ✅ | ✅ |
| API write (portfolio sync) | 🔒 | 🔒 | 🔒 | ✅ |
| **Virtual Portfolio** | | | | |
| Paper trading portfolio | 🔒 | ✅ | ✅ | ✅ |
| Leverage up to 5× | 🔒 | 🔒 | ✅ | ✅ |
| Leverage up to 20× | 🔒 | 🔒 | 🔒 | ✅ |
| Monthly tournaments | 🔒 | ✅ | ✅ | ✅ |
| **Early Access** | | | | |
| Beta features | 🔒 | 🔒 | 🔒 | ✅ |

> Features marked 🔒 that are not yet built (alerts, API, virtual portfolio, tournaments) will be gated at the route/API level when implemented. Add the gate before shipping, not after.

---

## Penny Stocks — Elite Only

Penny stocks (`/penny`, `/penny/screener`) are restricted to Elite tier. Rationale:

- Penny stocks carry materially higher risk of loss, low liquidity, and susceptibility to manipulation.
- Surfacing them to trial or entry-tier users without that context is inappropriate for a product positioning itself as a serious trading tool.
- Elite users have self-selected as sophisticated traders who understand speculative risk.

**Gate implementation:** check `user.tier == 'elite'` in the route decorator before rendering. Return a 403 with an upgrade prompt, not a 404.

---

## Restricted Feature Messaging

Messaging at the point of a 🔒 gate must match the nature of the restriction.

### Risk-protective gates (use cautionary language)

For features blocked because of elevated financial risk (penny stocks, high leverage):

> "This feature is available to Elite members. Penny stocks carry higher risk and are suited to experienced traders. [Upgrade to Elite →]"

> "20× leverage is an Elite-only feature. High leverage can result in rapid losses exceeding your initial position. [Upgrade to Elite →]"

Do **not** use purely aspirational upsell language ("unlock powerful tools!") for risk-protective gates. The gate exists partly to protect the user — say so plainly.

### Standard capability gates (neutral/aspirational language)

For features blocked because of tier capability (backtest, API, alerts):

> "Full backtest history is a Pro feature. [Upgrade to Pro →]"

> "Email alerts are available on Starter and above. [Upgrade →]"

Keep these short. No need to justify the restriction beyond tier membership.

### HTTP response conventions

| Situation | Status | Body |
|---|---|---|
| Page route, wrong tier | 403 | Render an upgrade prompt page |
| API route, wrong tier | 403 | `{"error": "...", "upgrade_required": true, "min_tier": "pro"}` |
| Watchlist limit hit | 403 | `{"error": "Watchlist limit reached (5). Upgrade to create more.", "upgrade_required": true}` |

---

## Adding a New Feature

1. **Decide the tier** — add a row to the matrix table above before writing any code.
2. **Update `config/tiers.py`** if the feature requires a numeric limit (like watchlist count). Never hardcode limits in routes.
3. **Gate the route** — use `user.get("tier")` compared against the tier key string. Wrap in a helper if the same gate is needed in multiple places.
4. **Return the right status** — 403 for API routes, upgrade-prompt render for page routes.
5. **Message correctly** — follow the risk-protective vs. standard messaging guidelines above.
6. **Write a test** — at minimum, assert that a Free-tier user is denied and the correct tier can access. Add to `tests/test_user_tiers.py` or the relevant feature test file.

### Tier key strings (match `config/tiers.py` exactly)

```python
'free'     # default for all new registrations
'starter'
'pro'
'elite'    # markn's dev tier; also highest paid tier
```

### Example gate pattern

```python
@app.route("/penny")
@login_required
def penny():
    user = current_user()
    if user.get("tier") not in ("elite",):
        return render_template("upgrade.html", user=user,
                               feature="Penny Stock Hub", min_tier="elite"), 403
    return render_template("penny.html", user=user)
```

---

## Invariants

- **Default tier is `'free'`** — `get_tier(None)` and `get_tier('')` must return the Free config. Enforced in `config/tiers.py`.
- **markn is always `'elite'`** — auto-upgraded on login in `web/app.py:current_user()`.
- **Limits live in `config/tiers.py` only** — no numeric watchlist limits anywhere else in the codebase.
- **Penny stocks are Elite-only** — this is a risk-protective decision, not a commercial one. Do not downgrade this gate without a deliberate product decision logged here.
