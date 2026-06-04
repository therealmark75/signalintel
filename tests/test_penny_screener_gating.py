"""Smoke test for the /penny/screener page-level tier gate (Part 38, Item 4).

Background: the page previously hid the entire results table behind a
full-page locked teaser for any non-elite caller (over-gating). The fix
drops `locked` as the page gate, renders the table for all tiers, and
shows a single non-elite upsell banner above the table. Per-row score
cells are stripped server-side by strip_scores_for_non_elite in
/api/screener (unchanged), so the data layer stays gated regardless.

Fixtures (real DB, effective_tier verified at authoring time):
  - mark2  (id 6): stored 'free', no trial -> effective 'free' (non-elite).
  - markn  (id 2): stored 'elite'          -> effective 'elite'.
Both are stable: free has no trial window that can expire mid-suite, and
elite is the stored value. This satisfies P28 (fixture effective_tier
must match the asserted band).

Catches (P15):
  - Re-introduction of a page-level gate that hides the results table
    from non-elite users (the original over-gating bug): both tiers must
    render the table shell.
  - The Elite upsell banner leaking to elite users, or failing to render
    for non-elite users. The assertion keys on a branch-exclusive string
    ("Penny scores are an Elite feature.") that exists ONLY inside the
    `{% if tier != 'elite' %}` banner branch, so a true presence/absence
    flip is required to pass (P28 lesson from Part 37: a shared string
    would pass for both tiers and prove nothing).

Ignores (P15), by design not oversight:
  - Per-row score stripping (strip_scores_for_non_elite in /api/screener):
    that is the data layer, tested via the API surface elsewhere. This
    test asserts only the page shell, not cell contents.
  - Actual data rows: the table body is populated by client-side JS
    (boot() -> /api/screener), which the Flask test client does not run.
    "Table present" means the server-rendered table shell, not populated
    rows.
  - Banner copy wording, styling, and the CTA href beyond confirming the
    branch-exclusive marker string is present/absent.
"""

# Branch-exclusive marker: appears ONLY in the non-elite banner branch.
BANNER_STRING = "Penny scores are an Elite feature."
# Server-rendered table shell present for all tiers (no page-level gate).
TABLE_MARKER = 'id="results-table"'


def _client_for(flask_app, user_id):
    """Flask test client with session['user_id'] pre-seeded to user_id."""
    c = flask_app.test_client()
    with c.session_transaction() as sess:
        sess["user_id"] = user_id
    return c


def test_non_elite_sees_banner_and_table(flask_app):
    """mark2 (id 6, effective 'free'): upsell banner present AND the
    results table shell renders (no page-level over-gating)."""
    client = _client_for(flask_app, 6)
    resp = client.get("/penny/screener")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert BANNER_STRING in html, "non-elite must see the Elite upsell banner"
    assert TABLE_MARKER in html, "non-elite must see the results table shell"


def test_elite_sees_table_without_banner(flask_app):
    """markn (id 2, effective 'elite'): results table shell renders AND
    the non-elite upsell banner is absent."""
    client = _client_for(flask_app, 2)
    resp = client.get("/penny/screener")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert BANNER_STRING not in html, "elite must NOT see the upsell banner"
    assert TABLE_MARKER in html, "elite must see the results table shell"
