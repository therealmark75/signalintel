"""Verify config/pricing.py is in lockstep with Stripe.

Reads the Stripe Price for each of the 8 lookup_keys
<tier>_<currency>_<interval> and asserts integer equality against
config/pricing.LAUNCH_PRICING. Exits non-zero on any mismatch.

Run before any live-charge flip and after any Stripe Price edit.
"""

from __future__ import annotations

import os
import sys

# Repo root on sys.path so `config.*` imports resolve regardless of CWD.
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import stripe  # noqa: E402

from config.pricing import LAUNCH_PRICING  # noqa: E402
from config.settings import STRIPE_SECRET_KEY  # noqa: E402

stripe.api_key = STRIPE_SECRET_KEY


def main() -> int:
    mismatches: list[str] = []
    rows: list[tuple[str, int | str, str, int, str]] = []

    for tier, by_currency in LAUNCH_PRICING.items():
        for currency, by_interval in by_currency.items():
            for interval, expected_amount in by_interval.items():
                lookup_key = f"{tier}_{currency}_{interval}"
                res = stripe.Price.list(lookup_keys=[lookup_key], limit=1)
                if not res.data:
                    rows.append((lookup_key, "MISSING", "-", expected_amount, "NO"))
                    mismatches.append(f"{lookup_key}: no Stripe Price")
                    continue
                price = res.data[0]
                actual = int(price.unit_amount)
                ok = (actual == int(expected_amount)) and (price.currency == currency)
                rows.append((lookup_key, actual, price.currency, expected_amount, "YES" if ok else "NO"))
                if not ok:
                    mismatches.append(
                        f"{lookup_key}: Stripe={actual} {price.currency} "
                        f"vs config={expected_amount} {currency}"
                    )

    print(f"{'lookup_key':<22} {'Stripe unit_amount':>20} {'Stripe currency':>17} {'config':>10} {'MATCH':>7}")
    print("-" * 80)
    for lookup_key, stripe_amount, stripe_currency, cfg_amount, match in rows:
        print(f"{lookup_key:<22} {str(stripe_amount):>20} {stripe_currency:>17} {cfg_amount:>10} {match:>7}")
    print("-" * 80)

    if mismatches:
        print(f"FAIL: {len(mismatches)} mismatch(es)")
        for m in mismatches:
            print(f"  - {m}")
        return 1

    print(f"OK: {len(rows)}/8 lookup_keys match Stripe")
    return 0


if __name__ == "__main__":
    sys.exit(main())
