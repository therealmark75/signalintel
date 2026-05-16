"""
Route-level P13 regression tests for rating display in JSON API responses.

Catches: regressions where /api/ticker/<>/events (or any rating-bearing JSON
response we extend this file to cover) reverts to rendering internal scorer
codes — STRONG_BUY, STRONG_HOLD, SELL, etc. — instead of the descriptive
display labels from signals.signal_labels.tier_short(). Also catches the
"?" arrow artifact that the prior `(old_rating or '?')` ternary produced
when old_rating was NULL on a ticker's first-ever rating row.

Ignores: rating codes that appear in JSON fields acting as machine
identifiers (e.g. `new_rating`, `direction`) — those are data plumbing
consumed by client-side renderers, not user-visible prose. The check
targets `title` fields only, which are the actual human-facing strings.
Ignores: CSS class names, form values, URL query parameters, and any
other surface where internal codes are intentionally used.
"""
import sqlite3

import pytest

from config.constants import DATABASE_PATH
from signals.signal_labels import SIGNAL_TIERS


RAW_CODES = list(SIGNAL_TIERS.keys())  # STRONG_BUY, BUY, STRONG_HOLD, ...
DISPLAY_LABELS = {v["short"] for v in SIGNAL_TIERS.values()}  # Very Strong, Strong, Stable, ...


def _ticker_with_rating_history():
    """Pick a ticker that has at least one rating_changes row, preferring one
    whose history includes a NULL old_rating (so we exercise both branches —
    "Rating set:" and "Rating changed:"). Returns None if rating_changes is
    empty so the test can skip on a fresh deploy."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        # Prefer a ticker with a NULL old_rating row (covers both branches).
        row = conn.execute(
            "SELECT ticker FROM rating_changes WHERE old_rating IS NULL "
            "ORDER BY change_date DESC LIMIT 1"
        ).fetchone()
        if row:
            return row["ticker"]
        # Fallback: any ticker with rating history (covers only the changed-from branch).
        row = conn.execute(
            "SELECT ticker FROM rating_changes ORDER BY change_date DESC LIMIT 1"
        ).fetchone()
        return row["ticker"] if row else None
    finally:
        conn.close()


def test_ticker_events_uses_display_labels(client):
    """
    /api/ticker/<>/events title field must render descriptive labels via
    tier_short(), never raw internal codes or the legacy '?' artifact.

    Catches: regression to the pre-fix `(old or '?').replace('_',' ')` shape
    or any other path that re-introduces STRONG_HOLD/SELL/etc. into title prose.
    Ignores: the `new_rating` JSON field (machine identifier, not prose) and
    any non-title field. CSS classes and URL params are out of scope.
    """
    ticker = _ticker_with_rating_history()
    if ticker is None:
        pytest.skip("rating_changes is empty — no fixture data on this deploy")

    resp = client.get(f"/api/ticker/{ticker}/events")
    assert resp.status_code == 200, f"/api/ticker/{ticker}/events returned {resp.status_code}"
    payload = resp.get_json()
    assert payload is not None, "events endpoint returned non-JSON"

    rating_events = [e for e in payload.get("events", payload if isinstance(payload, list) else [])
                     if e.get("type") == "rating"]
    assert rating_events, f"no rating events returned for {ticker} — fixture assumption broken"

    for ev in rating_events:
        title = ev.get("title", "")
        # No '?' artifact anywhere in the title.
        assert "?" not in title, f"'?' artifact in title for {ticker}: {title!r}"
        # No raw internal codes — exact-word matches only, to avoid false
        # positives if a label ever legitimately contains a substring like 'sell'.
        for code in RAW_CODES:
            spaced = code.replace("_", " ")
            assert code not in title, f"raw code {code!r} in title for {ticker}: {title!r}"
            assert spaced not in title, f"raw code {spaced!r} (space-separated) in title for {ticker}: {title!r}"
        # At least one canonical display label must appear — proves the
        # translation actually fired (rather than producing empty strings).
        assert any(lbl in title for lbl in DISPLAY_LABELS), (
            f"title for {ticker} contains no canonical display label: {title!r}"
        )


def test_ticker_events_initial_rating_uses_rating_set_phrasing(client):
    """
    First-ever rating row (old_rating IS NULL) must render as 'Rating set: <label>'
    instead of 'Rating changed: ? → <label>'.

    Catches: regression where the NULL old_rating branch is dropped or the
    '?' fallback is reintroduced.
    Ignores: tickers whose first rating row is not present in the latest
    /api/ticker/<>/events response (the endpoint limits to LIMIT 15).
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT ticker FROM rating_changes WHERE old_rating IS NULL "
            "ORDER BY change_date DESC LIMIT 1"
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        pytest.skip("no rating_changes row with NULL old_rating — can't exercise initial-rating branch")
    ticker = row["ticker"]

    resp = client.get(f"/api/ticker/{ticker}/events")
    assert resp.status_code == 200
    payload = resp.get_json()
    rating_events = [e for e in payload.get("events", payload if isinstance(payload, list) else [])
                     if e.get("type") == "rating"]

    initial_rows = [e for e in rating_events if e["title"].startswith("Rating set:")]
    assert initial_rows, (
        f"expected at least one 'Rating set: <label>' title for {ticker} "
        f"(NULL old_rating row exists in DB) — got titles: "
        f"{[e['title'] for e in rating_events]}"
    )
    # And no 'Rating changed: ? →' anywhere.
    for ev in rating_events:
        assert " ? " not in ev["title"], f"'?' arrow survived for {ticker}: {ev['title']!r}"
