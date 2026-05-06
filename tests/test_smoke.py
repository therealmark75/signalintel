"""
Smoke tests — every page and key API endpoint must return HTTP 200.
Auth is pre-injected via the `client` fixture (session['user_id'] = 2, markn).
"""
import json
import pytest


PAGE_ROUTES = [
    "/",
    "/ratings",
    "/screener",
    "/penny/screener",
    "/penny",
    "/earnings",
    "/dividends",
    "/events",
    "/markets",
    "/watchlist",
    "/backtest",
    "/about",
    "/contact",
    "/privacy",
    "/terms",
    "/disclaimer",
    "/ticker/AAPL",
    "/news/AAPL",
    "/industry/Technology",
]

API_ROUTES = [
    "/api/overview",
    "/api/signals",
    "/api/signal_summary",
    "/api/sectors",
    "/api/sector-performance",
    "/api/insider_signals",
    "/api/top_signals",
    "/api/theme-counts",
    "/api/market-sessions",
    "/api/backtest/stats",
    "/api/ticker-tape",
    "/api/screener",
    "/api/watchlist",
    "/api/dividends",
    "/api/earnings",
    "/api/run_log",
    "/api/ticker/AAPL",
    "/api/penny/stock-of-day",
    "/api/penny/hot",
    "/api/signals/STRONG_BUY",
    "/api/signals/sector/Technology",
    "/api/industry/Technology",
    "/api/economic-calendar",
    "/api/economic-calendar/high-impact-banner",
    "/api/markets/SPY",
]


@pytest.mark.parametrize("path", PAGE_ROUTES)
def test_page_returns_200(client, path):
    resp = client.get(path)
    assert resp.status_code == 200, f"{path} returned {resp.status_code}"


@pytest.mark.parametrize("path", API_ROUTES)
def test_api_returns_200_and_json(client, path):
    resp = client.get(path)
    assert resp.status_code == 200, f"{path} returned {resp.status_code}"
    data = json.loads(resp.data)
    assert data is not None


def test_screener_theme_strong_buy_momentum(client):
    resp = client.get("/screener?theme=strong_buy_momentum")
    assert resp.status_code == 200

def test_screener_theme_buy_the_dip(client):
    resp = client.get("/screener?theme=buy_the_dip")
    assert resp.status_code == 200

def test_screener_theme_insider_buying_surge(client):
    resp = client.get("/screener?theme=insider_buying_surge")
    assert resp.status_code == 200

def test_screener_theme_legally_clean(client):
    resp = client.get("/screener?theme=legally_clean")
    assert resp.status_code == 200


def test_login_page_no_auth(flask_app):
    """Login page must be reachable without auth."""
    with flask_app.test_client() as c:
        resp = c.get("/login")
        assert resp.status_code == 200


def test_protected_page_redirects_without_auth(flask_app):
    """Dashboard must redirect unauthenticated users to /login."""
    with flask_app.test_client() as c:
        resp = c.get("/")
        assert resp.status_code in (302, 301)
        assert "/login" in resp.headers.get("Location", "")


def test_api_signals_rating_filter(client):
    resp = client.get("/api/signals/BUY")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert isinstance(data, list)
