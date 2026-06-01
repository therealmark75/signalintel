# SignalIntel Scoring Invariants

These invariants must hold after every scoring run. Any change to scoring logic must preserve them.

---

## 1. Legal Risk Distribution

- The majority of tickers should have `risk_label = 'None'` (~80–95%)
- `Minor` should be a small minority
- `Moderate`, `High`, `Critical`, `Extreme` should be rare
- A healthy distribution confirms the legal classifier is not over-triggering

**Verified 2026-05-05:** 27 None, 3 Minor (BRCC, COIN, SDOT)

---

## 2. Legal Risk Penalty Values

| Label | Penalty | Effect on Score |
|---|---|---|
| None | 0 | no impact |
| Minor | -5 | -5 pts penalty |
| Moderate | -15 | -15 pts penalty |
| High | -25 | -25 pts penalty |
| Critical | -40 | -40 pts penalty |
| Extreme | -60 | -60 pts penalty |

**Note:** `None` carries zero score impact. UI must not display a penalty line for None-classified tickers. Display as "None ✓".

---

## 3. Legal Classifier — Hypothetical Phrase Exclusions

Keywords that trigger `Minor` or above must **not** match when surrounded by hypothetical/standard business language. The `is_hypothetical()` function screens a ±400-char context window for excluding phrases including:

- `"paragraph iv"` — patent IV challenges (normal pharma)
- `"we settled our"` — past completed settlements
- `"joint venture"`, `"supply agreement"`, `"license agreement"` — normal commercial contracts
- `"superfund"`, `"national priorities list"`, `"hazardous material releases"`, `"environmental cleanup"` — EPA Superfund (standard disclosure, not active litigation)

---

## 4. Legal Risk HTML Stripping

Before classification, raw SEC EDGAR HTML must be stripped. The `_classify()` function receives plain text, not HTML. Failure to strip produces false positives from CSS/markup strings matching keyword patterns.

---

## 5. Signal Score Components Must Sum Correctly

Composite score = momentum + quality + insider + reversion + legal_penalty

No component may produce a score outside its declared range. Negative penalties must reduce the composite, not increase it.

---

## 6. Short & Ownership Data Source

`short_interest_pct`, `short_ratio`, `inst_own_pct`, `forward_pe`, `peg_ratio`, `price_to_sales`, `price_to_book` are sourced from **individual FinViz ticker pages** (`finvizfinance(ticker).ticker_fundament()`), NOT from the bulk Custom screener view.

Reason: Custom screener view with `columns=` parameter only returns 20 rows regardless of filter size. Individual pages are the only reliable source for these fields.

---

## 7. Discovery Theme Counts — Legally Clean

The `legally_clean` theme must use **LEFT JOIN** against `legal_risk`, treating `NULL` (no record) as clean. Using `INNER JOIN` restricts results to only the ~30 tickers that have been classified, producing a count of ~26 instead of 8,000+.

```sql
-- CORRECT
LEFT JOIN legal_risk lr ON ss.ticker = lr.ticker
WHERE (lr.risk_label IS NULL OR lr.risk_label IN ('None','Minor'))

-- WRONG — only returns tickers already in legal_risk table
JOIN legal_risk lr ON ss.ticker = lr.ticker
WHERE lr.risk_label IN ('None','Minor')
```

---

## 8. Target Price Data Source

12M Target (`target_price`) and Target Upside (`target_upside`) are stored in `fmp_price_targets` and joined/cached into `signal_scores`. Must be non-null for 10,000+ tickers.

---

## 9. Backtest Data Maturity

Rating changes are logged via `detect_rating_changes()` after every scoring run. The backtest module requires ≥30 days of history for reliable statistics. Do not display meaningless averages on fewer than 30 days of data.

**First rating changes logged:** 2026-04-21  
**Reliable stats available from:** 2026-05-21

---

## 10. Filterable/Sortable Tables — State Preservation

All filterable and sortable tables must preserve filter state when sort changes, and preserve sort state when filters change.

The /screener implementation is the reference: all filter + sort state lives in a `state` object, every action updates `state` then calls `load()` which rebuilds the URL. New filterable tables must replicate this pattern, not invent their own.

For client-side sorted tables (dashboard ALL SIGNALS), reading the active filter button's raw rating value from its `onclick` attribute (not textContent) is the correct pattern.

**Applies to:** Dashboard ALL SIGNALS, /screener, /penny/screener, /watchlist

---

## 11. UI Consistency — Tooltip Icons

Hover `data-tip` or `title` attributes on heading labels are sufficient for tooltips. Do **not** add `(?)` icons next to headings that already have hover tooltips. `(?)` icons add visual clutter without adding information value.

**Acceptable:** `(?) more` used as an inline read-more affordance within prose text (e.g. backtest.html:71).  
**Not acceptable:** `(?)` adjacent to a heading that already has a hover tooltip on the heading itself.

---

## Final Verification — 2026-05-05

| Check | Expected | Actual | Status |
|---|---|---|---|
| legal_risk distribution | Mostly None | 28 None / 3 Minor | ✅ |
| NONE penalty | 0 | 0 | ✅ |
| signal_scores count (latest) | 11,000+ | 11,118 | ✅ |
| target_price coverage | 10,000+ | 11,092 | ✅ |
| legally_clean theme count | 7,000+ | 7,961 | ✅ |
| Dashboard sort preserves filter | Yes | Fixed (Item 14) | ✅ |
| Penny screener Top Rated preset | STRONG_BUY/BUY, score≥60 | Fixed (Item 10) | ✅ |
| Legal None display | "None ✓" no penalty | Fixed (Item 12) | ✅ |

---

# PROCESS INVARIANTS — Rules for Future Development Sessions

These rules govern HOW we build SignalIntel. They apply to every Claude Code session, every feature prompt, and every commit going forward. Derived from real issues encountered during the 2026-05-05 stabilisation session.

---

## P1 — Audit All Surfaces When Adding or Modifying Data

When a new score component, field, rating, or data type is added (or an existing one is modified), it must be reflected on EVERY surface where related data appears. Adding to one surface and forgetting others creates silent inconsistencies that erode product credibility.

Surfaces to check whenever scoring/data changes:
- `/ticker/<symbol>` — header row, scorecard radar, score breakdown card, fundamentals card, stat cards row
- `/screener` — column visibility, sort options, filter options
- `/penny/screener` — column visibility, sort options, filters
- `/watchlist` — column visibility
- `/backtest` — relevant rating analysis
- `/` dashboard — Discovery Themes, ALL SIGNALS table
- `/api/*` endpoints — data shape returned to frontend
- Telegram alerts — if the new data should trigger or appear in notifications
- Database schema — column exists, populated, indexed if used for sorting/filtering

Every feature prompt must end with: *"Audit all relevant surfaces (ticker page, screener, watchlist, dashboard, backtest, API, alerts, DB) for consistency. Report which surfaces were updated and which were checked-but-already-correct."*

---

## P2 — Diagnose Before Fixing

For any bug or unexpected behaviour, the first action is ALWAYS diagnosis, not modification. Diagnose by:
- Running SQL queries to check data state
- Curling API endpoints to see actual responses
- Reading `git log` for recent changes in the affected area
- Checking Flask logs for errors

Report the diagnosis findings BEFORE applying a fix. Identify the actual root cause, not the surface symptom.

This prevents "fixing" a code path that was never broken whilst missing the actual bug elsewhere.

---

## P3 — Verify in Browser, Not in Code

A fix is not complete until it has been verified in the actual running application. Code review of the change is insufficient. Required verification:
- Hard refresh the page (Cmd+Shift+R)
- Click through the user journey that exercises the fix
- Confirm the data/UI matches expected state
- For backend changes, curl the relevant endpoint and inspect the response

If a fix is reported as complete, the report must include explicit confirmation of browser/endpoint verification. "Code change applied" is not "fix complete."

---

## P4 — Commits Are Checkpoints, Not Summaries

Commits are made per logical fix or feature, not in batches at the end of a session. The commit message must describe the specific change, not the broader theme. Granular commits enable selective rollback when something regresses.

- **Bad:** `"Stabilisation session complete"`
- **Good:** `"Fix Item 5: populate Short Interest from FinViz Ownership view"`
- **Good:** `"Fix Item 14: read rating from data attribute not button text"`

If a session has 13 items, expect ≥13 commits.

---

## P5 — Treat Absence of Data as Neutral, Not Negative

Queries that depend on sparsely-populated tables (`legal_risk`, `insider_trades`, `dividend_history`, `earnings_calendar`, `analyst_recom`) must handle NULL/missing data correctly:
- Tickers without data should be treated as "not flagged"
- Use LEFT JOIN, not INNER JOIN
- Default scoring impact for missing data: 0 (neutral), not a penalty

This prevents systematically excluding tickers from themes and scoring views simply because their underlying data hasn't been gathered yet.

---

## P6 — Numeric Values Stored Numeric, Displayed Formatted

All numeric data (market cap, volume, price, percentages, scores) must be stored in DB as NUMERIC types. Sort operations must use the numeric value. Display formatting (B/M/K suffixes, $ prefixes, comma separators, percentage signs) is applied ONLY at render time, never to the underlying value.

The display string and the sort key must always be separate.

---

## P7 — UI Tooltips on Labels, Not (?) Icons

When a UI element has a hover tooltip on its text label, do NOT add a `(?)` icon next to it. The `(?)` icon is visual clutter that adds no information value. Hover tooltips are sufficient.

**Exception:** when no hover tooltip is present and a tooltip is specifically needed, a `(?)` icon may be used. Once added, the hover behaviour should attach to both the label and the icon, not just the icon.

---

## P8 — Theme Definitions Are Single Source of Truth

Discovery Theme definitions live in `config/themes.py` and are referenced by both the homepage Discovery Themes card and the screener `?theme=<id>` route.

If the homepage count and the screener row count for a theme differ, that is a bug.

Adding a new theme requires updating `config/themes.py` only — the homepage and screener consume the canonical definition.

---

## P9 — Filter and Sort State Preserves Across Actions

In any filterable/sortable table:
- Clicking a filter must preserve the active sort
- Clicking a sort header must preserve all active filters
- State lives in URL query parameters (bookmarkable)
- Browser back button must work (`history.pushState`)

The `/screener` implementation is the reference. New filterable tables must replicate this pattern.

---

## P10 — Defensive Empty-State Handling

API endpoints and frontend components must NEVER hang on "Loading..." indefinitely. If a query returns empty:
- The response must include a clear status message (e.g. "Insufficient data — backtest stats accumulating")
- The frontend must render the message
- Empty state must be distinguishable from broken state

Loading states should resolve in <5 seconds. Anything longer needs explicit user-facing communication.

---

## P11 — Document Scoring Invariants as You Discover Them

When you discover or codify a "should always be true" rule about SignalIntel's scoring or data, append it to `docs/scoring_invariants.md`. Examples:
- "Composite score must be in range 0–100"
- "Sector strength score must be in range 0–100"
- "Legal classification 'None' must result in 0 score impact"
- "Sector modifier must never exceed ±7.5 points"

This file becomes the source of truth for the test suite.

---

## P12 — Preserve Raw Values When Applying Modifiers

When a calculated value modifies another (e.g. `sector_modifier` applied to `composite_score`), preserve the original as a separate column (`composite_score_raw`) alongside the modified value. This enables:
- A/B comparison of modifier effectiveness
- Backtest validation of whether modifier adds value
- Rollback if the modifier introduces problems
- User-facing transparency about what's being adjusted

---

## P13 — User-Facing Signal Language Is Descriptive, Not Directive

All user-facing tier labels must describe signal strength, not prescribe trading actions.

| Internal constant | User-facing label |
|---|---|
| `STRONG_BUY` | Very Strong Signal |
| `BUY` | Strong Signal |
| `STRONG_HOLD` | Stable Signal |
| `HOLD` | Neutral Signal |
| `WEAK_HOLD` | Soft Signal |
| `SELL` | Bearish Signal |
| `STRONG_SELL` | Strong Bearish Signal |

The canonical mapping lives in `signals/signal_labels.py`. Internal DB columns, Python constants, and API keys (`STRONG_BUY`, `BUY`, etc.) are **never** renamed. Only display labels change.

**Why:** SignalIntel is not a licensed financial adviser. Directive language ("Buy", "Sell") implies a trading recommendation. Descriptive language ("Very Strong Signal") describes what the data shows.

---

## P14 — Discovery Theme IDs Are Stable; Labels May Change

Theme IDs (e.g. `strong_buy_momentum`, `buy_the_dip`) are used as URL parameters, JS variables, and API keys. They must never be renamed once shipped.

Theme labels (e.g. "Top Signal Momentum", "Oversold Signals") are user-facing and may be updated in `config/themes.py`. The homepage and screener consume the canonical `THEMES` list — updating the label in one place is sufficient.

**Applies to:** `config/themes.py`, `web/templates/index.html` theme card names, `web/templates/screener.html` preset button labels.

---

## P1.1 — Inventory Before Edit (The Migration Rule)

Migration sessions, refactors, and any change touching more than one surface MUST begin with an inventory pass. Before any code change, produce and report the full list of files that render, reference, or depend on the affected data. The migration is then executed against that explicit list.

The inventory is built by:
- `grep` across `web/templates/`, `web/static/`, `scrapers/`, `notifications/`, `signals/`, `database/`, `docs/`
- Listing every template, JS file, Python module, and doc that touches the affected concept
- Flagging surfaces where the affected concept is referenced indirectly (e.g. CSS class names, URL parameters, column headers)

The inventory is reported BEFORE making changes. The user reviews the inventory and confirms scope. Only then does the migration proceed.

This prevents "reported complete but partial" migrations where Claude Code lists what was changed without auditing what should have been changed.

---

## P1.2 — Migration Completeness Is Verified by Absence, Not Presence

A migration is complete when:
- (a) All inventoried surfaces have been updated, AND
- (b) A grep for the OLD pattern across user-facing files returns zero matches

Reporting "all listed surfaces updated" is insufficient. The final step of any migration is the absence grep — confirming the old pattern has been eliminated, not just confirming the new pattern was added in the places we thought to look.

For Signal Strength: the final grep was:
```
grep -rn "STRONG_BUY\|STRONG BUY\|Strong Buy" web/templates/ --include="*.html" | grep -v "value=\|== \|FinViz"
```
returning zero matches.

For future migrations: define the equivalent grep in the migration prompt itself. The migration is not done until that grep is clean.

---

## P1.3 — Reports Must Be Audit Tables, Not Narrative Summaries

When Claude Code completes a migration or multi-surface change, the final report MUST be structured as an audit table, not a narrative paragraph. Required columns:

| Surface | Old state | New state | Verified by |
|---|---|---|---|

"Verified by" is the specific check performed (grep returned zero, browser hard-refresh confirmed, curl response inspected).

Narrative summaries like "the templates were updated and the file was added" obscure what wasn't checked. Audit tables make gaps visible because empty rows are obvious.

---

## P15 — Test Design Must Articulate Both Signal and Silence

Every test must be designed and described so the author can answer two questions:

1. **What specific regression would trip this test?** (One concrete example.)
2. **What legitimate code or content would NOT trip it?** (One concrete example, especially for grep-based or pattern-matching tests.)

A test that fires on everything creates noise, gets disabled, and protects nothing. A test that fires on nothing provides false confidence and protects nothing. The space between those failure modes is where useful tests live.

**Examples drawn from this codebase:**

Good — `test_no_directive_language_in_templates`:
- **Catches:** `<span>Strong Buy</span>` rendered as display text
- **Ignores:** `value="STRONG_BUY"`, `rating-STRONG_BUY` CSS class, `{'STRONG_BUY': 'Very Strong'}` JS map keys, `{% if rating == 'STRONG_BUY' %}` template logic
- **Mechanism:** `allowed_substrings` list defines identifier contexts; anything not matching those contexts is treated as display text by elimination

Bad pattern (avoid): `assert "STRONG_BUY" not in template`
- Would fire on every form value, every CSS class, every map key, every comparison. False positive factory.

Bad pattern (avoid): `assert "Strong Buy" not in template.lower()`
- Lowercasing means "stronger buyout" or unrelated prose containing those words would also fire. Pattern is too broad.

When writing or reviewing a test, the test docstring must include both a *Catches* example and an *Ignores* example for any pattern-matching or grep-based check. If the author cannot produce both, the test is not ready to commit.

## P17 — Full enumeration of effects in audits

Audit entries describing a function's behaviour must enumerate the function's complete set of effects: reads, writes, mutations, side effects, and external calls. A description that is technically true while concealing material behaviour is an audit failure.

Specifically: a function being audited for "does it read X correctly" must also disclose "does it write to anything, mutate state, call external services, or have side effects."

Origin: BUG-001-REOPENED (7 May 2026). The previous CC audit reported "current_user() always reads DB" — technically true, but the function also issued an UPDATE on every call, hardcoding tier='elite' for a specific username. The audit didn't lie; it under-described. The bug remained for hours because the audit answered the narrow question ("does it read?") rather than the full question ("what does it do?").

Enforcement: When CC produces an audit table entry for any function, that entry must list every effect the function has, not only the effect being audited for. Reviewers (Mark or Athena) flag entries that describe one effect without addressing whether others exist.

---

## P20 — Analyst completeness gate

**P20 — Analyst completeness gate.** When two paths diverge on what an analyst making a buy/sell/hold decision actually receives, the path serving the more complete analyst experience wins, regardless of implementation cost. Engineering cost is a tiebreaker between analytically-equivalent paths, not a vetoing factor over analytically-stronger ones.

---

## P26 — Freshness tests fire red on first run by design

**P26 — Freshness tests fire red on first run by design.** When a freshness test catches real production staleness on its first execution, the red is the audit's empirical value, not a problem to mask. Resist the impulse to loosen thresholds, add conditional skips for "known stuck" windows, or otherwise dilute the signal. The threshold is what surfaced the bug; weakening it suppresses the next bug too.

The 17 May 2026 economic_calendar finding is the canonical example. `test_fmp_economic_calendar_freshness` landed in commit a25e39d with a 72h threshold (matching the daily mon-fri cadence). On first run it caught that economic_calendar had not received a new row since 2026-05-07 — 9 days of silent staleness on a daily job. The job's wrapper in main.py swallowed the failure with `try/except logger.error` and wrote no run_log entry, so the 8-day window had no observability anywhere. The test surfaced what the runtime hid.

Action when this happens:
1. Commit the test as-is. Do not loosen the threshold to make CI green.
2. File the underlying scraper / job failure as a separate FOLLOWUP entry in PROJECT_CONTEXT.md (not as a TODO comment, not as a test skip).
3. Let CI run red until the underlying issue is fixed. The red is doing its job: every CI run is a fresh reminder that the upstream system has not recovered.
4. Once the underlying job produces fresh data, the test goes green automatically — no test change needed.

Origin: 17 May 2026 economic_calendar staleness, surfaced by Phase 2C / Item 4 freshness test on its first commit.

---

## P27 — Altman Z'' (1995 non-manufacturing) replaces classic Z (1968) for bankruptcy-risk penalty

**P27 — Altman Z'' (1995 non-manufacturing) used for bankruptcy-risk penalty as of SCORING_ENGINE_VERSION 0.14.0 (18 May 2026).** Empirical justification: classic Altman Z (1968 manufacturing) penalised 62.9% of the SignalIntel ticker universe (2,285 of 3,631 computable tickers), a calibration failure for a tech-heavy non-manufacturing universe. Z'' reduces this to 47.8% (1,735 tickers) with thresholds calibrated for non-manufacturing companies. Healthcare sector concentration in distress bin dropped from 47% to 34.4%. Analysis: scripts/altman_distribution_analysis.py, run dated 2026-05-18, results in data/altman_distribution_2026-05-18.csv. Penalty magnitudes (-10 grey, -30 distress, -60 deep distress) preserved for backward-compatible composite-score scale. Four-tier penalty model preserved by splitting Z'' < 1.1 into Z'' [0.0, 1.1) = -30 and Z'' < 0.0 = -60.

---

## P28 - Verify tier-gating on a fixture whose effective_tier equals the tier under test

A trialing account is `effective_tier`=elite for the trial window and shows every gated surface unlocked, so it cannot exercise locked-state gates. Use a stored-free, no-trial account (mark2) for free/locked verification, and a stored-pro account (marktest1) for Pro-band cells. Sibling to P3 (verify in browser): browser truth is only truth when the fixture's effective tier matches the cell under test.
