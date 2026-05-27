#!/usr/bin/env python3
"""
scripts/setup_stripe_products.py

Idempotent setup of the SignalIntel paywall arc in Stripe:
  - 2 Products: "SignalIntel Pro", "SignalIntel Elite"
  - 8 Prices:   pro/elite × usd/gbp × monthly/annual
    Lookup keys: <tier>_<currency>_<interval>

LIVE-MODE GUARD: refuses to run unless STRIPE_SECRET_KEY starts with
'sk_test_'. The webhook (Commit 4) resolves price_id → tier via
lookup_key, with metadata.tier as a belt-and-braces validator.

Idempotency:
  - Products are matched by metadata.signalintel_tier
  - Prices are matched by lookup_key (Stripe enforces uniqueness)
Re-running creates nothing new.

Usage:
  source venv/bin/activate
  python scripts/setup_stripe_products.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import stripe
from config.settings import STRIPE_SECRET_KEY


# ── Pricing matrix (locked) ────────────────────────────────────────
# Amounts are in minor units (cents/pence). Annual = round(monthly * 12 * 0.75).
#   Pro USD:   $29.00/mo  →  $261.00/yr
#   Pro GBP:   £24.99/mo  →  £224.91/yr
#   Elite USD: $79.00/mo  →  $711.00/yr
#   Elite GBP: £74.99/mo  →  £674.91/yr
PRICE_MATRIX = [
    ("pro",   "usd", "month",  2900,  "pro_usd_monthly"),
    ("pro",   "usd", "year",  26100,  "pro_usd_annual"),
    ("pro",   "gbp", "month",  2499,  "pro_gbp_monthly"),
    ("pro",   "gbp", "year",  22491,  "pro_gbp_annual"),
    ("elite", "usd", "month",  7900,  "elite_usd_monthly"),
    ("elite", "usd", "year",  71100,  "elite_usd_annual"),
    ("elite", "gbp", "month",  7499,  "elite_gbp_monthly"),
    ("elite", "gbp", "year",  67491,  "elite_gbp_annual"),
]

PRODUCTS = {
    "pro":   {"name": "SignalIntel Pro",   "metadata": {"signalintel_tier": "pro"}},
    "elite": {"name": "SignalIntel Elite", "metadata": {"signalintel_tier": "elite"}},
}


def assert_test_mode(api_key: str) -> None:
    """Refuse unless api_key is a Stripe test-mode key.

    Guarding here means a misconfigured live key can never silently
    create live Products/Prices via this script. Live setup is an
    explicit, separate operation.
    """
    if not api_key or not api_key.startswith("sk_test_"):
        raise SystemExit(
            "REFUSED: STRIPE_SECRET_KEY must start with 'sk_test_'. "
            "This script is gated to Stripe test mode. "
            f"Got prefix: {api_key[:10]!r}"
        )


def find_product_by_tier(tier_key):
    """Linear scan of products in the account, filtered by metadata.

    Avoids stripe.Product.search (which requires the Search API to be
    enabled on the account) — with at most 2 products to manage, a
    list+filter is trivially cheap.

    StripeObject is dict-like via __getitem__ but does NOT expose
    .get() as an instance method — `product.get(...)` triggers
    __getattr__ which raises AttributeError. Use bracket access with
    try/except for missing-metadata products in the same account.
    """
    for product in stripe.Product.list(limit=100, active=True).auto_paging_iter():
        try:
            if product["metadata"]["signalintel_tier"] == tier_key:
                return product
        except (KeyError, TypeError):
            continue
    return None


def find_price_by_lookup_key(lookup_key):
    result = stripe.Price.list(lookup_keys=[lookup_key], limit=1)
    return result.data[0] if result.data else None


def upsert_product(tier_key):
    existing = find_product_by_tier(tier_key)
    if existing is not None:
        return existing, False
    spec = PRODUCTS[tier_key]
    product = stripe.Product.create(name=spec["name"], metadata=spec["metadata"])
    return product, True


def upsert_price(product_id, tier_key, currency, interval, unit_amount, lookup_key):
    existing = find_price_by_lookup_key(lookup_key)
    if existing is not None:
        return existing, False
    price = stripe.Price.create(
        product=product_id,
        unit_amount=unit_amount,
        currency=currency,
        recurring={"interval": interval},
        lookup_key=lookup_key,
        metadata={"tier": tier_key, "currency": currency, "interval": interval},
    )
    return price, True


def main():
    assert_test_mode(STRIPE_SECRET_KEY)
    stripe.api_key = STRIPE_SECRET_KEY

    print(f"Stripe SDK: {stripe.VERSION}")
    print(f"API key prefix: {STRIPE_SECRET_KEY[:8]}... (test mode confirmed)\n")

    created_products = 0
    reused_products = 0
    created_prices = 0
    reused_prices = 0

    products_by_tier = {}
    for tier_key in ("pro", "elite"):
        product, created = upsert_product(tier_key)
        products_by_tier[tier_key] = product.id
        marker = "CREATED" if created else "REUSED "
        print(f"  [{marker}] product  id={product.id}  tier={tier_key}  name={product.name!r}")
        if created:
            created_products += 1
        else:
            reused_products += 1

    print()

    for tier, currency, interval, amount, lookup_key in PRICE_MATRIX:
        product_id = products_by_tier[tier]
        price, created = upsert_price(product_id, tier, currency, interval, amount, lookup_key)
        marker = "CREATED" if created else "REUSED "
        display = amount / 100
        symbol = "$" if currency == "usd" else "£"
        print(
            f"  [{marker}] price    id={price.id}  "
            f"lookup_key={lookup_key:<22}  "
            f"{symbol}{display:>8.2f} {currency.upper()}/{interval}"
        )
        if created:
            created_prices += 1
        else:
            reused_prices += 1

    print()
    print(
        f"Summary: products created={created_products} reused={reused_products}  "
        f"prices created={created_prices} reused={reused_prices}"
    )


if __name__ == "__main__":
    main()
