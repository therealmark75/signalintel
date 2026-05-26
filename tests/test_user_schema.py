"""
Tests for the users-table schema invariants (paywall arc).

P15 throughout: pins both the presence of paywall columns AND their
nullable/default contract — the Stripe webhook is about to write to
these columns and a silent default change (e.g. NOT NULL added by a
future migration, or DEFAULT shifting away from 'free' on tier) would
either break inserts or grant unintended access.

DB is built per-test in pytest's tmp_path. data/trading_system.db is
NEVER touched.
"""
import pytest
from database.db import initialise_user_schema, get_connection


# The 4 paywall columns added in Step 2 of the paywall arc.
PAYWALL_COLUMNS = (
    'trial_started_at',
    'stripe_customer_id',
    'stripe_subscription_id',
    'tier_effective_until',
)

# The 2 webhook-lookup indexes added in Step 2.
PAYWALL_INDEXES = (
    'idx_users_stripe_customer',
    'idx_users_stripe_subscription',
)


@pytest.fixture
def initialised_db_path(tmp_path):
    """A temp DB path with initialise_user_schema already applied.

    Each test gets its own tmp_path → no shared state, no risk of
    touching data/trading_system.db.
    """
    db_path = str(tmp_path / "test_user_schema.db")
    initialise_user_schema(db_path)
    return db_path


def _users_columns(db_path):
    """Return {name: (type, notnull, dflt_value)} for every column on
    the users table. Source: PRAGMA table_info — returns rows of
    (cid, name, type, notnull, dflt_value, pk).
    """
    conn = get_connection(db_path)
    rows = conn.execute("PRAGMA table_info(users)").fetchall()
    conn.close()
    return {r[1]: (r[2], r[3], r[4]) for r in rows}


def _users_indexes(db_path):
    """Return the set of index names on the users table.
    Source: sqlite_master.
    """
    conn = get_connection(db_path)
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='users'"
    ).fetchall()
    conn.close()
    return {r[0] for r in rows}


def test_paywall_columns_present(initialised_db_path):
    """All 4 paywall columns exist after initialise_user_schema.

    Catches: someone deleting a column from the CREATE TABLE block
             or from the ALTER migration block.
    Ignores: column order — only presence is asserted (cid is not
             checked because future migrations may shift it).
    """
    cols = _users_columns(initialised_db_path)
    for name in PAYWALL_COLUMNS:
        assert name in cols, f"missing column: {name}"


def test_paywall_columns_nullable_no_default(initialised_db_path):
    """Each paywall column is TEXT, nullable (notnull=0), no default.

    A NOT NULL constraint or a non-NULL default on any of these would
    either break create_user() (which omits them — they'd need a value
    supplied) or silently inject state into every new user (e.g. a
    DEFAULT on trial_started_at would auto-start a trial for every
    signup, regardless of intent).

    Catches: a future migration adding NOT NULL or a DEFAULT to any of
             the four columns.
    Ignores: the cid (column index) — column-order shifts are fine.
    """
    cols = _users_columns(initialised_db_path)
    for name in PAYWALL_COLUMNS:
        col_type, notnull, dflt = cols[name]
        assert col_type == 'TEXT', f"{name}: expected TEXT, got {col_type!r}"
        assert notnull == 0, f"{name}: notnull={notnull}, expected 0 (nullable)"
        assert dflt is None, f"{name}: default={dflt!r}, expected None"


def test_tier_default_still_free_post_migration(initialised_db_path):
    """The tier column still defaults to 'free' after the Step 2 migration.

    The Step 0 contract (free = unpaid floor; new signups land at the
    floor unless overridden) MUST survive every future migration on
    this table. A wandering ALTER that drops or shifts this default
    would silently grant new signups whatever the next default becomes
    (or break inserts entirely if NOT NULL is added without a default).

    Catches: a future migration clobbering the tier default away from
             'free'.
    Ignores: USER_TIERS dict shape in config/tiers.py — that's tested
             separately in tests/test_user_tiers.py.
    """
    cols = _users_columns(initialised_db_path)
    col_type, notnull, dflt = cols['tier']
    assert col_type == 'TEXT', f"tier: expected TEXT, got {col_type!r}"
    # PRAGMA table_info returns the default as the raw SQL literal —
    # for a string default 'free' that comes back as the 6-char string
    # "'free'" (with embedded single quotes).
    assert dflt == "'free'", f"tier default={dflt!r}, expected \"'free'\""


def test_stripe_indexes_present(initialised_db_path):
    """Both Stripe webhook-lookup indexes exist on the users table.

    The webhook will look up users by stripe_customer_id (on
    customer.* events) and by stripe_subscription_id (on
    subscription.* events). Fast lookup matters because Stripe retries
    on timeout — a slow lookup compounds into duplicate-write risk
    against the future subscription_events table.

    Catches: silent removal of either index.
    Ignores: the auto-indexes SQLite creates for UNIQUE constraints
             on username/email (sqlite_autoindex_users_*) — they're
             not under our control.
    """
    idx = _users_indexes(initialised_db_path)
    for name in PAYWALL_INDEXES:
        assert name in idx, f"missing index: {name}"


def test_initialise_user_schema_is_idempotent(tmp_path):
    """Running initialise_user_schema twice leaves columns and indexes
    unchanged.

    Critical for production: this function runs at every gunicorn boot
    via web/app.py:49, and the N-th run must be a no-op. An ALTER
    without an `if 'col' not in user_cols` guard would either fail on
    the second run (SQLite errors on duplicate column add) or
    duplicate state (extra indexes, etc.).

    Catches: a future migration lacking an IF-NOT-EXISTS / column-set
             guard.
    Ignores: the schema in absolute terms — this test only asserts the
             second-run delta is empty.
    """
    db_path = str(tmp_path / "idempotency.db")
    initialise_user_schema(db_path)
    cols_first = _users_columns(db_path)
    idx_first = _users_indexes(db_path)

    initialise_user_schema(db_path)
    cols_second = _users_columns(db_path)
    idx_second = _users_indexes(db_path)

    assert cols_first == cols_second, \
        f"column shape changed on re-run: before={cols_first} after={cols_second}"
    assert idx_first == idx_second, \
        f"index set changed on re-run: before={idx_first} after={idx_second}"
