"""Launch pricing. Single Python source of truth, mirrored from Stripe.

Amounts are integer minor units (USD cents / GBP pence), mirrored EXACTLY
from the Stripe Price unit_amount for lookup_key
<tier>_<currency>_<interval>. Verified against Stripe test mode by
scripts/verify_pricing.py. Must stay in lockstep with Stripe; re-run
verify_pricing.py before any live-charge flip.

PROJECT_CONTEXT.md is documentation only. This module is the source.
Display names live in config/tiers.py (display_name); do not duplicate.
"""

LAUNCH_PRICING = {
    "pro": {
        "usd": {"monthly": 2900,  "annual": 26100},
        "gbp": {"monthly": 2499,  "annual": 22491},
    },
    "elite": {
        "usd": {"monthly": 7900,  "annual": 71100},
        "gbp": {"monthly": 7499,  "annual": 67491},
    },
}

ANNUAL_DISCOUNT_PCT = 25

TIER_FEATURES = {
    "free": [
        "7-day full-access free trial",
        "Browse every listed ticker",
        "Upgrade anytime",
    ],
    "pro": [
        "Full multi-factor signals and ratings",
        "Watchlist signal alerts",
        "Monthly paper-trading tournaments",
        "Up to 5 watchlists",
    ],
    "elite": [
        "Everything in Pro",
        "Penny-stock signals ($1 to $5)",
        "Unlimited watchlists",
        "API access",
    ],
}
