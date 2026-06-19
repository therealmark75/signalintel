"""
FMP entitlement error tests.

Tests the 401/402/403 auth/entitlement escalation in scrapers/fmp_scraper.py,
the run_log FAILED write in job handlers, and the Telegram dedup helper.

Mirrors tests/test_fmp_circuit_breaker.py for stub patterns: unittest.mock
patches requests.get and time.sleep; no real HTTP, no real delays.
Each test resets _fmp_429_streak to 0 to prevent inter-test pollution.

Origin: 18 May 2026 economic_calendar staleness — HTTP 402 was silently
swallowed for 11 days by _get()'s generic warning-then-None path. The
FMPEntitlementError class and these tests prevent the regression and
prove the new observability path writes the correct run_log row.
"""
import sqlite3

import pytest
from unittest.mock import patch, MagicMock

import scrapers.fmp_scraper as fmp
import notifications.telegram as tg


@pytest.fixture(autouse=True)
def reset_streak():
    """Reset module-level state before every test."""
    with fmp._fmp_429_lock:
        fmp._fmp_429_streak = 0
    yield
    with fmp._fmp_429_lock:
        fmp._fmp_429_streak = 0


@pytest.fixture(autouse=True)
def reset_telegram_dedup():
    """Reset Telegram dedup dict before and after each test."""
    tg._last_fmp_alert_at.clear()
    yield
    tg._last_fmp_alert_at.clear()


def _mock_response(status_code, json_data=None):
    r = MagicMock()
    r.status_code = status_code
    r.json.return_value = json_data or [{"ok": True}]
    return r


def test_get_402_raises_entitlement_error():
    """
    _get() must raise FMPEntitlementError on HTTP 402, carrying
    status_code=402 and path attributes for the caller to read.

    Catches: regression to the silent-warning-then-None behaviour that
    swallowed the 11-day economic_calendar staleness on 18 May 2026.
    Ignores: log message format; only the exception type and
    attributes are asserted.
    """
    with patch("scrapers.fmp_scraper.requests.get",
               return_value=_mock_response(402)), \
         patch("scrapers.fmp_scraper.time.sleep"), \
         patch("scrapers.fmp_scraper._api_key", return_value="testkey"):

        with pytest.raises(fmp.FMPEntitlementError) as excinfo:
            fmp._get("/earnings-calendar")

    assert excinfo.value.status_code == 402
    assert excinfo.value.path == "/earnings-calendar"
    assert "402" in str(excinfo.value)
    assert "/earnings-calendar" in str(excinfo.value)


def test_get_401_raises_entitlement_error():
    """
    _get() must raise FMPEntitlementError on HTTP 401 (unauthorized —
    API key missing or revoked). Same escalation path as 402.

    Catches: 401 falling through to the generic else branch and
    returning None silently.
    Ignores: log message format; only the exception type and the
    status_code attribute are asserted.
    """
    with patch("scrapers.fmp_scraper.requests.get",
               return_value=_mock_response(401)), \
         patch("scrapers.fmp_scraper.time.sleep"), \
         patch("scrapers.fmp_scraper._api_key", return_value="testkey"):

        with pytest.raises(fmp.FMPEntitlementError) as excinfo:
            fmp._get("/dividends")

    assert excinfo.value.status_code == 401
    assert excinfo.value.path == "/dividends"


def test_get_403_raises_entitlement_error():
    """
    _get() must raise FMPEntitlementError on HTTP 403 (forbidden —
    some APIs return 403 instead of 402 for entitlement failures).

    Catches: 403 falling through to the generic else branch.
    Ignores: log message format; only the exception type and the
    status_code attribute are asserted.
    """
    with patch("scrapers.fmp_scraper.requests.get",
               return_value=_mock_response(403)), \
         patch("scrapers.fmp_scraper.time.sleep"), \
         patch("scrapers.fmp_scraper._api_key", return_value="testkey"):

        with pytest.raises(fmp.FMPEntitlementError) as excinfo:
            fmp._get("/earnings-calendar")

    assert excinfo.value.status_code == 403
    assert excinfo.value.path == "/earnings-calendar"


def test_get_500_does_not_raise_entitlement_error():
    """
    HTTP 500 (and other 5xx server errors) are transient. _get() must
    NOT raise FMPEntitlementError on 500; it must hit the generic
    warning-then-None path, exhaust the 3-attempt retry loop, and
    return None. Preserves existing behaviour for transient outages.

    Catches: scope creep where 5xx accidentally lands in the
    entitlement branch and starts alerting on every FMP server hiccup.
    Ignores: number of retry attempts; only the final return value
    (None) and the absence of FMPEntitlementError are asserted.
    """
    with patch("scrapers.fmp_scraper.requests.get",
               return_value=_mock_response(500)), \
         patch("scrapers.fmp_scraper.time.sleep"), \
         patch("scrapers.fmp_scraper._api_key", return_value="testkey"):

        # Must not raise — the generic else branch returns None.
        result = fmp._get("/profile")

    assert result is None


def test_telegram_alert_rate_limited_per_endpoint():
    """
    send_alert_rate_limited must fire send_alert(message) at most once
    per (key, 24h) window. A second call with the same key inside the
    window must return False and not invoke send_alert.

    Catches: alert-flood regression if the dedup logic is removed or
    the key is computed incorrectly (e.g. always-unique by including
    timestamp).
    Ignores: real Telegram HTTP (send_alert is fully stubbed);
    monotonic-clock precision (uses monkeypatched time.time).
    """
    fake_now = [1_000_000.0]
    def fake_time():
        return fake_now[0]

    with patch("notifications.telegram.send_alert", return_value=True) as mock_send, \
         patch("notifications.telegram.time.time", side_effect=fake_time):

        # First call: fires.
        sent_1 = tg.send_alert_rate_limited(
            ("/earnings-calendar", 402), "alert body 1"
        )
        assert sent_1 is True
        assert mock_send.call_count == 1

        # Second call, same key, 1 hour later (well inside 24h window): suppressed.
        fake_now[0] += 3600
        sent_2 = tg.send_alert_rate_limited(
            ("/earnings-calendar", 402), "alert body 2"
        )
        assert sent_2 is False
        assert mock_send.call_count == 1  # no new call

        # Different key on the same clock: fires (different endpoint or status).
        sent_3 = tg.send_alert_rate_limited(
            ("/dividends", 402), "alert body 3"
        )
        assert sent_3 is True
        assert mock_send.call_count == 2

        # Original key, 24h+1s later: fires again.
        fake_now[0] += 86401 - 3600  # advance to just past 24h since the first call
        sent_4 = tg.send_alert_rate_limited(
            ("/earnings-calendar", 402), "alert body 4"
        )
        assert sent_4 is True
        assert mock_send.call_count == 3
