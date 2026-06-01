"""Guard against stored-tier bypass reads creeping back into routes
and templates.

Catches: any unmarked stored-tier read in `web/app.py` or
`web/templates/*.html` that should route through
`config/entitlements.py:effective_tier(user)`. Patterns checked:

  - `user.get("tier"...` and `user.get('tier'...)` (Python attribute
    access via dict.get).
  - `user["tier"]` / `user['tier']` (Python item access).
  - `SELECT ... tier ... FROM users` (raw SQL in route context).
  - `user.tier` as a Jinja attribute in templates.

Ignores (by design, not by oversight):

  - `config/entitlements.py:105` -- the resolver's OWN stored-tier
    read inside `effective_tier()`. The resolver IS the canonical
    stored-tier reader; it cannot route through itself. Out of the
    grep scope of this test by file path.
  - `database/db.py` `get_user_by_*` helpers that issue
    `SELECT * FROM users` and return the full row. Callers decide
    what to read off the row; the SELECT itself is not an
    entitlement read.
  - `tests/*` and `scripts/*` -- not entitlement-context. Tests may
    legitimately assert on stored tier values (P28 fixture
    discipline); scripts are maintenance utilities.

Marked sites (sentinel: `# noqa: tier-read (<reason>)`):

  - `web/app.py:_handle_checkout_session_completed` -- captures
    `tier_before` pre-flip for the `subscription_events` audit row.
    The webhook handler is the writer of the canonical tier
    transition; it must observe stored state directly to log the
    transition. Not entitlement-context.
  - `web/app.py:_handle_subscription_deleted` -- same role,
    `tier_before` capture for the ride-out audit row.

Total expected marked sentinels: **2**. The assertion is exact, not
a lower bound. Deleting one of the audit captures (which would
silently lose the `tier_before` log) or adding a new unmarked read
(which would bypass `effective_tier`) both trip this test.

Per P15: this test catches new unmarked stored-tier reads in
routes and templates. It does NOT catch the resolver's own read,
`SELECT *` helpers in `database/db.py`, test files, or scripts.
"""
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent

# Patterns that flag a stored-tier read in route context (Python).
PY_TIER_READ_PATTERNS = [
    r'user\.get\(\s*["\']tier["\']',          # user.get("tier", ...)
    r'user\[\s*["\']tier["\']\s*\]',           # user["tier"] / user['tier']
    r'SELECT\b[^\n]*\btier\b[^\n]*\bFROM\s+users\b',  # SELECT ... tier ... FROM users
]
PY_TIER_RE = re.compile("|".join(PY_TIER_READ_PATTERNS), re.IGNORECASE)

# Pattern that flags a stored-tier read in templates (Jinja attribute).
TEMPLATE_TIER_RE = re.compile(r'\buser\.tier\b')

# Sentinel patterns that mark a read as deliberate.
NOQA_PY_RE = re.compile(r'#\s*noqa:\s*tier-read\s*\(')
NOQA_TEMPLATE_RE = re.compile(r'\{#\s*noqa:\s*tier-read\s*\(')

EXPECTED_MARKED_TOTAL = 2  # web/app.py:_handle_checkout_session_completed + _handle_subscription_deleted


def _scan(path: Path, content_re: re.Pattern, noqa_re: re.Pattern):
    """Return (unmarked_hits, marked_count) for one file."""
    unmarked = []
    marked = 0
    with path.open(encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            if content_re.search(line):
                if noqa_re.search(line):
                    marked += 1
                else:
                    unmarked.append((lineno, line.rstrip("\n")))
    return unmarked, marked


def test_no_unmarked_stored_tier_reads_in_routes_or_templates():
    """Every stored-tier read in web/app.py or web/templates/*.html
    must either route through effective_tier() or carry a
    `# noqa: tier-read (<reason>)` sentinel (template form
    `{# noqa: tier-read (<reason>) #}`). Total sentinel count across
    the scope must be exactly EXPECTED_MARKED_TOTAL.
    """
    app_py = REPO_ROOT / "web" / "app.py"
    unmarked_py, marked_py = _scan(app_py, PY_TIER_RE, NOQA_PY_RE)

    template_dir = REPO_ROOT / "web" / "templates"
    unmarked_tpl_all = []
    marked_tpl = 0
    for tpl in sorted(template_dir.glob("*.html")):
        u, m = _scan(tpl, TEMPLATE_TIER_RE, NOQA_TEMPLATE_RE)
        unmarked_tpl_all.extend((tpl.name, ln, text) for ln, text in u)
        marked_tpl += m

    failures = []
    if unmarked_py:
        failures.append(
            "Unmarked stored-tier reads in web/app.py "
            "(should route through effective_tier() or carry "
            "`# noqa: tier-read (<reason>)`):\n"
            + "\n".join(f"  L{ln}: {text}" for ln, text in unmarked_py)
        )
    if unmarked_tpl_all:
        failures.append(
            "Unmarked `user.tier` reads in templates "
            "(should use a context variable derived from "
            "effective_tier(), e.g. `nav_tier`):\n"
            + "\n".join(
                f"  {name}:L{ln}: {text}"
                for name, ln, text in unmarked_tpl_all
            )
        )
    assert not failures, "\n\n".join(failures)

    total_marked = marked_py + marked_tpl
    assert total_marked == EXPECTED_MARKED_TOTAL, (
        f"Expected exactly {EXPECTED_MARKED_TOTAL} `# noqa: tier-read (...)` "
        f"sentinels across web/app.py + web/templates/*.html, found "
        f"{total_marked} ({marked_py} in app.py, {marked_tpl} in templates). "
        f"If a deliberate read was added or removed, update EXPECTED_MARKED_TOTAL "
        f"in this file and document the new site in the module docstring."
    )
