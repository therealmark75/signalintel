"""
Tests for the live-mode guard in scripts/setup_stripe_products.py.

The script creates Stripe Products and Prices. A bug or misconfigured
key that pointed it at live mode would create real, billable Products
and Prices in production Stripe. The guard prevents that.

Tests here exercise only the pure-Python guard function — no Stripe
network calls. The setup script as a whole runs against test mode at
deploy time; that pipeline is observed via script output, not via
pytest.
"""
import importlib.util
import pathlib

import pytest


# Load the script as a module without executing main() (it's guarded by
# `if __name__ == '__main__'`). Avoids needing scripts/__init__.py.
_SCRIPT_PATH = (
    pathlib.Path(__file__).parent.parent / "scripts" / "setup_stripe_products.py"
)


def _load_setup_module():
    spec = importlib.util.spec_from_file_location("setup_stripe_products", _SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_assert_test_mode_rejects_live_key():
    """A sk_live_ key raises SystemExit with the diagnostic prefix.

    Catches: a future edit that loosens the prefix check (e.g. checks
             only for 'sk_' instead of 'sk_test_').
    Ignores: the exact wording of the diagnostic — only the
             SystemExit raise and the offending prefix being surfaced
             are asserted.
    """
    mod = _load_setup_module()
    with pytest.raises(SystemExit) as exc:
        mod.assert_test_mode("sk_live_fakefakefake")
    assert "sk_test_" in str(exc.value), (
        "diagnostic must name the required prefix so the operator "
        "knows what's wrong"
    )


def test_assert_test_mode_rejects_empty_key():
    """An empty string raises SystemExit.

    Catches: a misconfigured local config/settings.py that didn't
             populate STRIPE_SECRET_KEY before the script ran — would
             previously short-circuit the prefix check at the
             `not api_key` clause and silently fail. The SystemExit
             ensures the operator sees the misconfiguration.
    Ignores: None/None-equivalent inputs — caller passes a string
             from settings, never None.
    """
    mod = _load_setup_module()
    with pytest.raises(SystemExit):
        mod.assert_test_mode("")


def test_assert_test_mode_accepts_test_key():
    """A valid sk_test_ prefix does not raise.

    Catches: a regression that broke the happy path (e.g. accidentally
             negated the prefix check).
    Ignores: actual Stripe API connectivity — this asserts only the
             guard's verdict on the input string.
    """
    mod = _load_setup_module()
    # Suffix is intentionally non-alphanumeric (hyphens) so GitHub's
    # Stripe-key secret scanner doesn't match it. The guard checks only
    # the sk_test_ prefix; suffix content is irrelevant to the test.
    mod.assert_test_mode("sk_test_NOT-A-REAL-KEY-unit-test-only")
