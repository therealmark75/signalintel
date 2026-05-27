"""
Tests for the subscription_events table (Stripe webhook idempotency log).

P15 throughout: pins both the column set AND the constraint contract
the webhook depends on. Specifically:
  - stripe_event_id is the idempotency lock (UNIQUE + NOT NULL).
    Losing either turns "duplicate Stripe delivery" from a no-op into
    a double tier flip — the load-bearing reason this table exists.
  - status defaults to 'received' so the webhook handler doesn't have
    to pass it on initial insert; the handler transitions to
    'processed' / 'failed' as it works.

DB is built per-test in pytest's tmp_path. data/trading_system.db is
NEVER touched.
"""
import sqlite3

import pytest

from database.db import (
    get_connection,
    initialise_subscription_events_schema,
    initialise_user_schema,
)


SUBSCRIPTION_EVENTS_COLUMNS = (
    'id',
    'stripe_event_id',
    'event_type',
    'user_id',
    'stripe_customer_id',
    'received_at',
    'processed_at',
    'status',
    'error_message',
    'tier_before',
    'tier_after',
    'raw_payload',
)

SUBSCRIPTION_EVENTS_INDEXES = (
    'idx_sub_events_user',
    'idx_sub_events_customer',
    'idx_sub_events_received_at',
)


@pytest.fixture
def initialised_db_path(tmp_path):
    """Temp DB with users + subscription_events schemas applied.

    users must come first because subscription_events.user_id has
    REFERENCES users(id). Even though SQLite's FK enforcement is
    off by default in this codebase, the schema declaration still
    parses against the parent table.
    """
    db_path = str(tmp_path / "test_subscription_events_schema.db")
    initialise_user_schema(db_path)
    initialise_subscription_events_schema(db_path)
    return db_path


def _table_columns(db_path, table):
    """Return {name: (type, notnull, dflt_value)} for every column on `table`."""
    conn = get_connection(db_path)
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    conn.close()
    return {r[1]: (r[2], r[3], r[4]) for r in rows}


def _table_indexes(db_path, table):
    """Return the set of index names on `table` from sqlite_master."""
    conn = get_connection(db_path)
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name=?",
        (table,),
    ).fetchall()
    conn.close()
    return {r[0] for r in rows}


def test_subscription_events_table_exists(initialised_db_path):
    """initialise_subscription_events_schema creates the table.

    Catches: someone deleting the CREATE TABLE statement, or
             renaming the table.
    Ignores: column order, defaults, indexes — covered by
             dedicated tests below.
    """
    conn = get_connection(initialised_db_path)
    row = conn.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name='subscription_events'"
    ).fetchone()
    conn.close()
    assert row is not None, "subscription_events table not created"


def test_subscription_events_columns_present(initialised_db_path):
    """All 12 columns the webhook handler reads/writes exist.

    Catches: someone deleting a column from the CREATE TABLE block.
    Ignores: column order (cid) — future migrations may shift it.
    """
    cols = _table_columns(initialised_db_path, 'subscription_events')
    for name in SUBSCRIPTION_EVENTS_COLUMNS:
        assert name in cols, f"missing column: {name}"


def test_stripe_event_id_is_unique_and_not_null(initialised_db_path):
    """stripe_event_id has UNIQUE + NOT NULL — the idempotency lock.

    Both constraints are load-bearing for the webhook:
      - NOT NULL ensures the handler can never write a row without
        the idempotency key (would silently break duplicate-detection).
      - UNIQUE is the actual lock — duplicate INSERT raises
        IntegrityError; the handler catches and short-circuits.

    Catches: a future migration relaxing either constraint, which
             would let the same Stripe event trigger two tier flips
             on delivery retry.
    Ignores: the index name SQLite auto-creates for UNIQUE
             (sqlite_autoindex_*) — implementation detail.
    """
    cols = _table_columns(initialised_db_path, 'subscription_events')
    col_type, notnull, _ = cols['stripe_event_id']
    assert col_type == 'TEXT', f"stripe_event_id: expected TEXT, got {col_type!r}"
    assert notnull == 1, f"stripe_event_id: notnull={notnull}, expected 1"

    # Verify UNIQUE empirically by attempting a duplicate insert.
    conn = get_connection(initialised_db_path)
    conn.execute(
        "INSERT INTO subscription_events "
        "(stripe_event_id, event_type, received_at) VALUES (?, ?, ?)",
        ('evt_test_1', 'checkout.session.completed', '2026-05-27T00:00:00'),
    )
    conn.commit()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO subscription_events "
            "(stripe_event_id, event_type, received_at) VALUES (?, ?, ?)",
            ('evt_test_1', 'checkout.session.completed', '2026-05-27T00:00:01'),
        )
    conn.close()


def test_status_defaults_to_received(initialised_db_path):
    """status column defaults to 'received'.

    Catches: a default-clobber migration. The webhook handler relies
             on this default — initial insert omits status, transitions
             happen via UPDATE.
    Ignores: the schema's NOT NULL annotation enforcement order —
             only the default literal is asserted.
    """
    cols = _table_columns(initialised_db_path, 'subscription_events')
    col_type, notnull, dflt = cols['status']
    assert col_type == 'TEXT'
    assert notnull == 1, f"status notnull={notnull}, expected 1"
    # PRAGMA returns the SQL literal: 'received' with embedded quotes.
    assert dflt == "'received'", f"status default={dflt!r}, expected \"'received'\""


def test_required_columns_not_null(initialised_db_path):
    """event_type and received_at are NOT NULL.

    Both are mandatory for forensics: a row without event_type can't
    be filtered by type; a row without received_at can't be ordered
    on the audit timeline.

    Catches: a migration making either nullable.
    Ignores: optional columns (processed_at, error_message,
             tier_before, tier_after, raw_payload) — those are
             populated as the handler progresses.
    """
    cols = _table_columns(initialised_db_path, 'subscription_events')
    assert cols['event_type'][1] == 1, "event_type must be NOT NULL"
    assert cols['received_at'][1] == 1, "received_at must be NOT NULL"


def test_subscription_events_indexes_present(initialised_db_path):
    """All 3 explicit forensic indexes exist.

    Catches: silent removal of any of the forensic indexes. SQLite
             would still answer the queries without them, just
             slowly — and slow webhook lookups compound into
             Stripe retry → duplicate-write risk.
    Ignores: the implicit sqlite_autoindex_subscription_events_*
             that SQLite auto-creates for the UNIQUE constraint —
             that's not under our control.
    """
    idx = _table_indexes(initialised_db_path, 'subscription_events')
    for name in SUBSCRIPTION_EVENTS_INDEXES:
        assert name in idx, f"missing index: {name}"


def test_initialise_subscription_events_schema_is_idempotent(tmp_path):
    """Running the migration twice leaves columns and indexes unchanged.

    Critical for production: this runs at every Flask boot via
    web/app.py. The second run must be a true no-op.

    Catches: a future ALTER added without an IF-NOT-EXISTS / column
             guard, which would either fail on second run or
             duplicate state.
    Ignores: the schema in absolute terms — only the second-run
             delta is asserted to be empty.
    """
    db_path = str(tmp_path / "idempotency.db")
    initialise_user_schema(db_path)  # parent table for FK
    initialise_subscription_events_schema(db_path)
    cols_first = _table_columns(db_path, 'subscription_events')
    idx_first = _table_indexes(db_path, 'subscription_events')

    initialise_subscription_events_schema(db_path)
    cols_second = _table_columns(db_path, 'subscription_events')
    idx_second = _table_indexes(db_path, 'subscription_events')

    assert cols_first == cols_second, (
        f"column shape changed on re-run: before={cols_first} after={cols_second}"
    )
    assert idx_first == idx_second, (
        f"index set changed on re-run: before={idx_first} after={idx_second}"
    )
