"""
FMP circuit breaker tests.

Tests the consecutive-429 protection in scrapers/fmp_scraper.py.

Uses unittest.mock to stub requests.get and time.sleep — no real HTTP,
no real delays. Each test resets _fmp_429_streak to 0 to prevent
inter-test pollution.
"""
import pytest
from unittest.mock import patch, MagicMock

import scrapers.fmp_scraper as fmp


@pytest.fixture(autouse=True)
def reset_streak():
    """Reset module-level state before every test."""
    with fmp._fmp_429_lock:
        fmp._fmp_429_streak = 0
    yield
    with fmp._fmp_429_lock:
        fmp._fmp_429_streak = 0


def _mock_response(status_code, json_data=None):
    r = MagicMock()
    r.status_code = status_code
    r.json.return_value = json_data or [{"ok": True}]
    return r


def test_streak_below_threshold_resets_on_2xx():
    """
    9 consecutive 429s followed by a 200 must not raise; counter must
    reset to 0 on the 200; the subsequent call must succeed.

    Catches: counter not resetting on 2xx, or premature trip at <10.
    Ignores: warning log messages, sleep durations.
    """
    responses = [_mock_response(429)] * 9 + [_mock_response(200)]

    with patch("scrapers.fmp_scraper.requests.get", side_effect=responses), \
         patch("scrapers.fmp_scraper.time.sleep"), \
         patch("scrapers.fmp_scraper._api_key", return_value="testkey"):

        # 3 calls, each making 3 HTTP attempts (3×3=9 attempts), all 429 → no trip yet
        # Each _get() call consumes up to 3 attempts from the side_effect list
        for _ in range(3):
            result = fmp._get("/test")
            assert result is None  # exhausted retries without 200 or trip

        # Counter is at 9; next call gets a 200
        result = fmp._get("/test")
        assert result == [{"ok": True}]

    with fmp._fmp_429_lock:
        assert fmp._fmp_429_streak == 0


def test_streak_at_threshold_trips_breaker():
    """
    10 consecutive 429 HTTP responses must raise FMPRateLimitError.

    Catches: breaker not tripping after threshold, or tripping early.
    Ignores: which specific call in the sequence trips the breaker.
    """
    always_429 = _mock_response(429)

    with patch("scrapers.fmp_scraper.requests.get", return_value=always_429), \
         patch("scrapers.fmp_scraper.time.sleep"), \
         patch("scrapers.fmp_scraper._api_key", return_value="testkey"):

        with pytest.raises(fmp.FMPRateLimitError):
            # Each _get() increments streak by up to 3 (one per retry attempt);
            # after 10 total 429 responses the breaker fires.
            for _ in range(5):
                fmp._get("/test")


def test_job_refresh_dividends_exits_cleanly_on_trip():
    """
    When FMPRateLimitError is raised mid-loop inside job_refresh_dividends,
    the exception must propagate to the caller (not be swallowed by the
    per-ticker generic except handler).

    Catches: FMPRateLimitError being swallowed, causing an infinite loop.
    Ignores: how many tickers were processed before the trip.
    """
    with patch("scrapers.fmp_scraper.fetch_dividend_profile",
               side_effect=fmp.FMPRateLimitError("breaker test")), \
         patch("scrapers.fmp_scraper.time.sleep"):

        with pytest.raises(fmp.FMPRateLimitError):
            fmp.job_refresh_dividends(":memory:", tickers=["AAA", "BBB", "CCC"])


def test_streak_resets_cross_job_via_2xx():
    """
    Accumulate 8 consecutive 429s, then receive a 200 (simulating a
    concurrent job succeeding). Counter must reset to 0. After reset,
    10 more 429s are required before the breaker trips again.

    Catches: reset not occurring on 2xx, causing premature trip after reset.
    Ignores: which thread triggered the reset.
    """
    with patch("scrapers.fmp_scraper._api_key", return_value="testkey"), \
         patch("scrapers.fmp_scraper.time.sleep"):

        # Manually drive streak to 8
        with fmp._fmp_429_lock:
            fmp._fmp_429_streak = 8

        # One 200 response resets the counter
        with patch("scrapers.fmp_scraper.requests.get",
                   return_value=_mock_response(200)):
            result = fmp._get("/test")
            assert result == [{"ok": True}]

        with fmp._fmp_429_lock:
            assert fmp._fmp_429_streak == 0

        # Now need 10 more consecutive 429s to trip
        with patch("scrapers.fmp_scraper.requests.get",
                   return_value=_mock_response(429)):
            with pytest.raises(fmp.FMPRateLimitError):
                for _ in range(5):
                    fmp._get("/test")


def test_threshold_one_edge_case():
    """
    With threshold=1, the breaker must trip on the very first 429 response.

    Catches: off-by-one errors in the >= comparison.
    Ignores: log messages.
    """
    original = fmp.FMP_CIRCUIT_BREAKER_THRESHOLD
    try:
        fmp.FMP_CIRCUIT_BREAKER_THRESHOLD = 1
        with patch("scrapers.fmp_scraper.requests.get",
                   return_value=_mock_response(429)), \
             patch("scrapers.fmp_scraper.time.sleep"), \
             patch("scrapers.fmp_scraper._api_key", return_value="testkey"):

            with pytest.raises(fmp.FMPRateLimitError):
                fmp._get("/test")
    finally:
        fmp.FMP_CIRCUIT_BREAKER_THRESHOLD = original
