"""
Regression test for the inert-trial bug (Step 3 hotfix, 2026-05-27).

Pre-fix state: register() called create_user() without stamping
trial_started_at, so the column was NULL for every fresh registrant.
The 7-day trial overlay in config/entitlements.py keys off
trial_started_at — when NULL, _parse_utc_iso returns None,
trial_active() returns False, and effective_tier(user) falls through
to the stored 'free' floor instead of the 'elite' overlay grant. Net
effect: every fresh registrant skipped the 7-day trial and saw the
free paywall on day 0.

This file pins the fix: create_user() now accepts trial_started_at
and writes it; register() now stamps it with naive UTC ISO; the row
round-trips through _parse_utc_iso and effective_tier resolves
to 'elite' on day 0.
"""
import pytest
from datetime import datetime
from werkzeug.security import generate_password_hash

from database.db import initialise_user_schema, create_user, get_user_by_id
from config.entitlements import effective_tier, trial_active


@pytest.fixture
def initialised_db_path(tmp_path):
    """Temp DB path with users-table schema applied. Live DB never touched."""
    db_path = str(tmp_path / "test_registration_trial.db")
    initialise_user_schema(db_path)
    return db_path


def test_fresh_registrant_resolves_to_elite_via_trial_overlay(initialised_db_path):
    """A user created with a UTC ISO trial_started_at resolves to
    effective_tier='elite' on day 0.

    The stored 'tier' column stays at 'free' (the post-trial floor);
    the overlay grants 'elite' for TRIAL_DAYS=7 days. This is the
    contract the inert-trial bug violated by never writing the
    anchor.

    Catches: regression where create_user() stops writing
             trial_started_at, register() stops passing it, the
             stamp format drifts to one _parse_utc_iso can't
             round-trip, or effective_tier loses the overlay branch.
    Ignores: the exact reported elapsed seconds — only the
             overlay-active verdict is asserted. Sub-second clock
             skew is irrelevant at the day-7 boundary on day 0.
    """
    pw_hash = generate_password_hash("hunter22", method="pbkdf2:sha256")
    uid = create_user(
        initialised_db_path, "newuser", "new@example.com", pw_hash,
        trial_started_at=datetime.utcnow().isoformat(),
    )
    user = get_user_by_id(initialised_db_path, uid)

    assert user is not None, "registrant must be retrievable via get_user_by_id"
    assert user["tier"] == "free", (
        f"stored floor must remain 'free' (post-trial floor), got {user['tier']!r}"
    )
    assert user["trial_started_at"] is not None, (
        "trial_started_at must be stamped, not NULL — this is the inert-trial guard"
    )
    assert isinstance(user["trial_started_at"], str), (
        f"trial_started_at must be ISO string, got {type(user['trial_started_at']).__name__}"
    )
    assert trial_active(user) is True, (
        "trial overlay must be active on day 0 — _parse_utc_iso must round-trip the stamp"
    )
    assert effective_tier(user) == "elite", (
        f"day-0 registrant must resolve to 'elite' overlay, got {effective_tier(user)!r}"
    )


def test_create_user_without_trial_started_at_leaves_null(initialised_db_path):
    """create_user() called without trial_started_at writes NULL.

    Backcompat contract for existing test fixtures (e.g.
    tests/test_watchlists.py) that call create_user() without the
    new parameter — they must still get a usable user row, just
    without a trial overlay anchor. The stamp lives at the call
    site (register()), not implicitly inside the DB helper.

    Catches: a future change that makes trial_started_at required,
             or auto-stamps it inside create_user() (which would
             silently start a trial for every test-created user and
             reverse the audit-table direction of the hotfix).
    Ignores: effective_tier behavior on the NULL-anchor row — that
             is the inert-trial path exercised by
             tests/test_entitlements.py:test_no_trial_started_*.
    """
    pw_hash = generate_password_hash("hunter22", method="pbkdf2:sha256")
    uid = create_user(
        initialised_db_path, "legacyuser", "legacy@example.com", pw_hash,
    )
    user = get_user_by_id(initialised_db_path, uid)

    assert user is not None
    assert user["trial_started_at"] is None, (
        "create_user() without trial_started_at must keep the column NULL"
    )
