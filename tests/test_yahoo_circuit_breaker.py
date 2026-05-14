"""
Yahoo Finance circuit breaker tests.

Tests the consecutive-rate-limit protection in scrapers/yahoo_scraper.py.

Uses unittest.mock to stub the fetch callable and time.sleep — no real HTTP,
no real delays. Each test resets _yahoo_429_streak to 0 via the lock to
prevent inter-test pollution.

Mirrors the structural pattern of tests/test_fmp_circuit_breaker.py.
"""
import pytest
from unittest.mock import patch, MagicMock

import pandas as pd
import scrapers.yahoo_scraper as yahoo


@pytest.fixture(autouse=True)
def reset_streak():
    """Reset module-level state before and after every test."""
    with yahoo._yahoo_429_lock:
        yahoo._yahoo_429_streak = 0
    yield
    with yahoo._yahoo_429_lock:
        yahoo._yahoo_429_streak = 0


def _rate_limit_exc(msg="Too many requests, try again later"):
    return Exception(msg)


def _other_exc(msg="Connection refused"):
    return Exception(msg)


def test_rate_limit_exception_increments_streak_below_threshold():
    """
    9 consecutive rate-limit exceptions must NOT raise YahooRateLimitedError;
    streak must be 9 after the 9th call.

    Catches: breaker tripping too early (< threshold).
    Ignores: sleep duration, log messages.
    """
    def failing_fetch():
        raise _rate_limit_exc()

    with patch("scrapers.yahoo_scraper.time.sleep"):
        for i in range(9):
            result = yahoo._safe_fetch(failing_fetch, "AAPL", "TEST")
            assert result is None

    with yahoo._yahoo_429_lock:
        assert yahoo._yahoo_429_streak == 9


def test_rate_limit_exception_trips_at_threshold():
    """
    A 10th consecutive rate-limit exception must raise YahooRateLimitedError.

    Catches: breaker not tripping at threshold, or off-by-one in >= comparison.
    Ignores: which specific message variant triggers the exception detection.
    """
    def failing_fetch():
        raise _rate_limit_exc()

    with patch("scrapers.yahoo_scraper.time.sleep"):
        # Drive streak to threshold-1 manually
        with yahoo._yahoo_429_lock:
            yahoo._yahoo_429_streak = yahoo.YAHOO_CIRCUIT_BREAKER_THRESHOLD - 1

        with pytest.raises(yahoo.YahooRateLimitedError):
            yahoo._safe_fetch(failing_fetch, "AAPL", "TEST")


def test_success_resets_streak():
    """
    A successful fetch (non-empty DataFrame) must reset _yahoo_429_streak to 0.

    Catches: streak not resetting on success, causing eventual premature trip.
    Ignores: the contents of the returned DataFrame.
    """
    df = pd.DataFrame({"col": [1, 2, 3]})

    with yahoo._yahoo_429_lock:
        yahoo._yahoo_429_streak = 7

    result = yahoo._safe_fetch(lambda: df, "AAPL", "TEST")
    assert result is not None

    with yahoo._yahoo_429_lock:
        assert yahoo._yahoo_429_streak == 0


def test_non_rate_limit_exception_does_not_increment_streak():
    """
    Exceptions that are NOT rate-limit-related must not increment the streak
    or raise YahooRateLimitedError.

    Catches: streak over-incrementing on benign errors (connection refused,
    JSON parse error, etc.), causing premature circuit trip.
    Ignores: the specific warning log message emitted.
    """
    def failing_fetch():
        raise _other_exc()

    with patch("scrapers.yahoo_scraper.time.sleep"):
        for _ in range(20):
            result = yahoo._safe_fetch(failing_fetch, "AAPL", "TEST")
            assert result is None

    with yahoo._yahoo_429_lock:
        assert yahoo._yahoo_429_streak == 0


def test_threshold_one_edge_case():
    """
    With YAHOO_CIRCUIT_BREAKER_THRESHOLD=1, the very first rate-limit
    exception must raise YahooRateLimitedError immediately.

    Catches: off-by-one in >= comparison at the lowest possible threshold.
    Ignores: log messages.
    """
    original = yahoo.YAHOO_CIRCUIT_BREAKER_THRESHOLD
    try:
        yahoo.YAHOO_CIRCUIT_BREAKER_THRESHOLD = 1

        def failing_fetch():
            raise _rate_limit_exc()

        with patch("scrapers.yahoo_scraper.time.sleep"):
            with pytest.raises(yahoo.YahooRateLimitedError):
                yahoo._safe_fetch(failing_fetch, "AAPL", "TEST")
    finally:
        yahoo.YAHOO_CIRCUIT_BREAKER_THRESHOLD = original
