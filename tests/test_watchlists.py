"""
Tests for multi-watchlist CRUD — db layer and API endpoints.
"""
import pytest
import sqlite3
import tempfile
import os
from database.db import (
    initialise_user_schema, create_user, get_watchlists_meta,
    get_or_create_default_watchlist, create_watchlist, rename_watchlist,
    delete_watchlist, add_to_watchlist, remove_from_watchlist, get_watchlist,
)
def _hash(pw):
    from werkzeug.security import generate_password_hash
    return generate_password_hash(pw, method="pbkdf2:sha256")


# ── In-memory DB fixture ─────────────────────────────────────────────

@pytest.fixture
def tmp_db(tmp_path):
    db_path = str(tmp_path / "test.db")
    initialise_user_schema(db_path)
    # Also need the main schema tables referenced by get_watchlist
    from database.db import initialise_schema
    initialise_schema(db_path)
    return db_path


@pytest.fixture
def user_id(tmp_db):
    uid = create_user(tmp_db, "testuser", "test@example.com", _hash("pw"))
    return uid


# ── DB layer tests ────────────────────────────────────────────────────

def test_get_or_create_default_watchlist_creates_on_first_call(tmp_db, user_id):
    wid = get_or_create_default_watchlist(tmp_db, user_id)
    assert isinstance(wid, int)
    wls = get_watchlists_meta(tmp_db, user_id)
    assert len(wls) == 1
    assert wls[0]['name'] == 'My Watchlist'


def test_get_or_create_default_watchlist_idempotent(tmp_db, user_id):
    wid1 = get_or_create_default_watchlist(tmp_db, user_id)
    wid2 = get_or_create_default_watchlist(tmp_db, user_id)
    assert wid1 == wid2
    assert len(get_watchlists_meta(tmp_db, user_id)) == 1


def test_create_watchlist_returns_id_and_name(tmp_db, user_id):
    result = create_watchlist(tmp_db, user_id, "Tech Picks")
    assert result["name"] == "Tech Picks"
    assert isinstance(result["id"], int)


def test_create_watchlist_duplicate_raises_value_error(tmp_db, user_id):
    create_watchlist(tmp_db, user_id, "Dupes")
    with pytest.raises(ValueError, match="already exists"):
        create_watchlist(tmp_db, user_id, "Dupes")


def test_rename_watchlist(tmp_db, user_id):
    wid = create_watchlist(tmp_db, user_id, "Old Name")["id"]
    ok = rename_watchlist(tmp_db, user_id, wid, "New Name")
    assert ok is True
    wls = get_watchlists_meta(tmp_db, user_id)
    names = [w["name"] for w in wls]
    assert "New Name" in names
    assert "Old Name" not in names


def test_rename_watchlist_wrong_user_returns_false(tmp_db, user_id):
    wid = create_watchlist(tmp_db, user_id, "Mine")["id"]
    ok = rename_watchlist(tmp_db, user_id + 99, wid, "Stolen")
    assert ok is False


def test_rename_to_existing_name_raises(tmp_db, user_id):
    create_watchlist(tmp_db, user_id, "A")
    wid_b = create_watchlist(tmp_db, user_id, "B")["id"]
    with pytest.raises(ValueError):
        rename_watchlist(tmp_db, user_id, wid_b, "A")


def test_delete_watchlist(tmp_db, user_id):
    wid = create_watchlist(tmp_db, user_id, "To Delete")["id"]
    ok = delete_watchlist(tmp_db, user_id, wid)
    assert ok is True
    wls = get_watchlists_meta(tmp_db, user_id)
    assert all(w["id"] != wid for w in wls)


def test_delete_watchlist_wrong_user_returns_false(tmp_db, user_id):
    wid = create_watchlist(tmp_db, user_id, "Mine")["id"]
    ok = delete_watchlist(tmp_db, user_id + 99, wid)
    assert ok is False


def test_add_and_remove_ticker(tmp_db, user_id):
    wid = get_or_create_default_watchlist(tmp_db, user_id)
    add_to_watchlist(tmp_db, user_id, "AAPL", watchlist_id=wid)
    items = get_watchlist(tmp_db, user_id, wid)
    assert any(r["ticker"] == "AAPL" for r in items)
    remove_from_watchlist(tmp_db, user_id, "AAPL", watchlist_id=wid)
    items = get_watchlist(tmp_db, user_id, wid)
    assert not any(r["ticker"] == "AAPL" for r in items)


def test_same_ticker_in_multiple_watchlists(tmp_db, user_id):
    """Ticker can appear in more than one watchlist for the same user."""
    wid1 = create_watchlist(tmp_db, user_id, "WL1")["id"]
    wid2 = create_watchlist(tmp_db, user_id, "WL2")["id"]
    add_to_watchlist(tmp_db, user_id, "TSLA", watchlist_id=wid1)
    add_to_watchlist(tmp_db, user_id, "TSLA", watchlist_id=wid2)
    items1 = get_watchlist(tmp_db, user_id, wid1)
    items2 = get_watchlist(tmp_db, user_id, wid2)
    assert any(r["ticker"] == "TSLA" for r in items1)
    assert any(r["ticker"] == "TSLA" for r in items2)


def test_delete_watchlist_cascades_tickers(tmp_db, user_id):
    wid = create_watchlist(tmp_db, user_id, "Ephemeral")["id"]
    add_to_watchlist(tmp_db, user_id, "GOOG", watchlist_id=wid)
    delete_watchlist(tmp_db, user_id, wid)
    from database.db import get_connection
    conn = get_connection(tmp_db)
    rows = conn.execute("SELECT * FROM watchlists WHERE watchlist_id=?", (wid,)).fetchall()
    conn.close()
    assert rows == []


def test_ticker_count_in_meta(tmp_db, user_id):
    wid = create_watchlist(tmp_db, user_id, "Counted")["id"]
    add_to_watchlist(tmp_db, user_id, "MSFT", watchlist_id=wid)
    add_to_watchlist(tmp_db, user_id, "NVDA", watchlist_id=wid)
    meta = get_watchlists_meta(tmp_db, user_id)
    counted = next(w for w in meta if w["id"] == wid)
    assert counted["ticker_count"] == 2


# ── API endpoint tests ────────────────────────────────────────────────

@pytest.fixture
def api_user(tmp_db):
    """Create a user in the tmp_db and return (db_path, user_id)."""
    uid = create_user(tmp_db, "apiuser", "api@example.com", _hash("pw"))
    return tmp_db, uid


@pytest.fixture
def wl_client(api_user):
    """Flask test client with auth session pointed at tmp_db."""
    db_path, uid = api_user
    import web.app as app_module
    # Temporarily redirect DATABASE_PATH
    original = app_module.DATABASE_PATH
    app_module.DATABASE_PATH = db_path
    app_module.app.config['TESTING'] = True
    with app_module.app.test_client() as c:
        with c.session_transaction() as sess:
            sess["user_id"] = uid
        yield c
    app_module.DATABASE_PATH = original


def test_api_watchlists_list_empty(wl_client):
    r = wl_client.get('/api/watchlists')
    assert r.status_code == 200
    data = r.get_json()
    assert "watchlists" in data
    assert isinstance(data["watchlists"], list)


def test_api_watchlists_create(wl_client):
    r = wl_client.post('/api/watchlists',
                       json={"name": "My Picks"},
                       content_type='application/json')
    assert r.status_code == 200
    data = r.get_json()
    assert data["ok"] is True
    assert "id" in data


def test_api_watchlists_create_duplicate_returns_409(wl_client):
    wl_client.post('/api/watchlists', json={"name": "Dupe"},
                   content_type='application/json')
    r = wl_client.post('/api/watchlists', json={"name": "Dupe"},
                       content_type='application/json')
    assert r.status_code == 409


def test_api_watchlists_rename(wl_client):
    r = wl_client.post('/api/watchlists', json={"name": "Original"},
                       content_type='application/json')
    wid = r.get_json()["id"]
    r2 = wl_client.patch(f'/api/watchlists/{wid}',
                         json={"name": "Renamed"},
                         content_type='application/json')
    assert r2.status_code == 200
    assert r2.get_json()["ok"] is True


def test_api_watchlists_delete_only_watchlist_blocked(wl_client):
    r = wl_client.post('/api/watchlists', json={"name": "Solo"},
                       content_type='application/json')
    wid = r.get_json()["id"]
    r2 = wl_client.delete(f'/api/watchlists/{wid}?confirm=true')
    assert r2.status_code == 400
    assert "only watchlist" in r2.get_json()["error"].lower()


def test_api_watchlists_delete_with_two_succeeds(wl_client):
    r1 = wl_client.post('/api/watchlists', json={"name": "First"},
                        content_type='application/json')
    wl_client.post('/api/watchlists', json={"name": "Second"},
                   content_type='application/json')
    wid = r1.get_json()["id"]
    r2 = wl_client.delete(f'/api/watchlists/{wid}?confirm=true')
    assert r2.status_code == 200
    assert r2.get_json()["ok"] is True


def test_api_watchlists_delete_without_confirm_rejected(wl_client):
    r = wl_client.post('/api/watchlists', json={"name": "Safe"},
                       content_type='application/json')
    wid = r.get_json()["id"]
    r2 = wl_client.delete(f'/api/watchlists/{wid}')
    assert r2.status_code == 400


def test_api_add_and_remove_ticker(wl_client):
    r = wl_client.post('/api/watchlists', json={"name": "Picks"},
                       content_type='application/json')
    wid = r.get_json()["id"]
    # Add
    r2 = wl_client.post(f'/api/watchlists/{wid}/tickers',
                         json={"ticker": "AAPL"}, content_type='application/json')
    assert r2.get_json()["ok"] is True
    # Remove
    r3 = wl_client.delete(f'/api/watchlists/{wid}/tickers/AAPL')
    assert r3.get_json()["ok"] is True
