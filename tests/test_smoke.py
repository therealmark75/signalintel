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


# ── New watchlist picker + penny polish tests ─────────────────────

def test_api_watchlists_all_tickers_returns_list(client):
    """
    /api/watchlists/all-tickers must return {tickers:[...]} for the screener.

    Catches: endpoint missing or returning wrong shape.
    Ignores: whether tickers is empty (no watchlist data in test DB).
    """
    resp = client.get("/api/watchlists/all-tickers")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert "tickers" in data
    assert isinstance(data["tickers"], list)


def test_api_watchlists_with_ticker_param_has_contains_flag(client):
    """
    GET /api/watchlists?ticker=AAPL must annotate each watchlist with
    contains_ticker boolean so the picker can render checkmarks.

    Catches: missing contains_ticker field on watchlist objects.
    Ignores: whether the user actually has AAPL in a watchlist.
    """
    resp = client.get("/api/watchlists?ticker=AAPL")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert "watchlists" in data
    # If user has watchlists, each must have contains_ticker
    for wl in data["watchlists"]:
        assert "contains_ticker" in wl, f"watchlist {wl.get('id')} missing contains_ticker"


def test_penny_screener_has_wl_column_header(client):
    """
    /penny/screener must contain a WL column header so each row has a
    watchlist button (Issue 2 parity with main screener).

    Catches: missing WL header — indicates the column was not added.
    Ignores: button styling, picker JS behaviour (not testable in smoke).
    """
    resp = client.get("/penny/screener")
    assert resp.status_code == 200
    body = resp.data.decode()
    assert 'wl-picker-btn' in body or 'wl-btn' in body, \
        "penny_screener.html missing watchlist button markup"


def test_screener_has_wl_picker_btn_class(client):
    """
    /screener must use wl-picker-btn class so the shared picker attaches.

    Catches: reverting to old toggleWatchlist() call without picker class.
    Ignores: exact button text (+ vs ✓ depends on user's watchlist state).
    """
    resp = client.get("/screener")
    assert resp.status_code == 200
    assert b'wl-picker-btn' in resp.data


def test_ticker_page_has_wl_picker_btn(client):
    """
    /ticker/AAPL must expose the shared picker button, not the old
    wlBtnClick() custom function.

    Catches: using wlBtnClick() (old custom picker) instead of WlPicker.open().
    Ignores: WlPicker.open internals — those are JS unit-level concerns.
    """
    resp = client.get("/ticker/AAPL")
    assert resp.status_code == 200
    body = resp.data.decode()
    assert 'WlPicker.open' in body, "ticker page not using shared WlPicker"
    assert 'wlBtnClick' not in body, "old custom wlBtnClick() still present"


def test_penny_page_market_cap_no_raw_float(client):
    """
    /penny must not render a raw float in the Mkt Cap field.
    The fmtMktCap helper should format as $1.22B etc.

    Catches: s.market_cap rendered without formatting (e.g. 1220000000.0).
    Ignores: legitimate short numbers like '$900K', formatted '$1.22B', and
    JavaScript source code that contains the number as part of an expression.

    P15: absence test — verifies the bad pattern is gone, not the good one.
    """
    resp = client.get("/penny")
    assert resp.status_code == 200
    body = resp.data.decode()
    # The raw float pattern would appear as e.g. >1220000000.0< in the HTML
    import re
    # Match a bare 10+-digit number followed by .0 inside an HTML context
    raw_float_in_html = re.search(r'>\s*\d{10,}\.0\s*<', body)
    assert raw_float_in_html is None, \
        f"Raw market cap float found in /penny HTML: {raw_float_in_html.group()}"


def test_wl_picker_partial_included_on_screener(client):
    """
    The shared _watchlist_picker.html partial (via _nav.html) must be present
    on every page. Spot-check: /screener must contain the picker dropdown div.

    Catches: partial not included, picker DOM element missing.
    Ignores: picker CSS specifics, JS function body details.
    """
    resp = client.get("/screener")
    assert b'wl-picker-drop' in resp.data
