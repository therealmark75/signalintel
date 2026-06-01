# SignalIntel Session Handoff

**Last updated:** end of Part 37 (2 June 2026)
**Engine:** SCORING_ENGINE_VERSION 0.17.0
**Repo:** all Part 37 commits pushed to origin/main as of this handoff.

## Where we are
The cancelled-subscription downgrade leak is closed. A cancelled user is now demoted to free when their `tier_effective_until` period elapses, at every entitlement surface, via a lazy access-time check inside `effective_tier` (no cron). This was the hard gate blocking the Stripe production-key flip. Items 1, 2, 3, 5 of the Part 37 work order shipped. Item 4 (penny screener over-gating) is diagnosed and a fix is designed but NOT built, it picks up first in Part 38.

Stripe remains on TEST keys. The production flip is now unblocked on the downgrade-leak axis, but should not be flipped until item 4 lands and a real cancelled-and-elapsed user is browser-verified against the live DB (see Part 38 queue).

## Part 37: paywall enforcement hardening (commits c9d1975 to c3c0111, pushed)

Three feature commits plus a doc-update commit. The fail-open revenue leak that blocked the production-key flip is closed, and the fail-closed trial bug that locked trialists out of their own watchlists is closed.

### c9d1975: memoise current_user + route five bypass surfaces through effective_tier + guard test
Closed items 2 and 5 (the fail-closed trial bug: effective-elite trialists were locked out of watchlists and shown a FREE nav badge because five surfaces read stored `tier` instead of `effective_tier`). Five sites routed: `web/app.py` dashboard nav (639), `/watchlist` GET (1046), GET `/api/watchlists` (1062), POST `/api/watchlists` create-gate (1122), and `_nav.html:32` via a new `@app.context_processor` injecting `nav_tier` (covers all 17 nav-rendering routes, not just the hand-edited ones).

`current_user()` memoised on `flask.g` with a `_USER_UNSET` sentinel distinguishing not-loaded / loaded-None / loaded-row, a pre-existing per-call DB query bug, fixed at source (verified 2 to 1 queries per `/watchlist` render).

New guard test `tests/test_tier_read_guard.py` greps `web/app.py` + templates for unmarked stored-tier reads, asserts exactly 2 sentinels (the two webhook audit captures at 356/414), negative-control proven (goes RED on an injected unmarked read, GREEN on revert).

P23 path+content trip (`def current_user`), cleared by Mark via `--no-verify`.

### c21f225: lazy tier_effective_until expiry in effective_tier (THE downgrade-leak close, item 1)
Inside `effective_tier`, after resolving stored tier and BEFORE the trial overlay: if `tier_effective_until` parses to a past datetime, the stored floor collapses to free. Fail-closed: missing/None/unparseable does NOT demote (a null means "no cancellation pending"; only a present past timestamp demotes). Critical edge holds: live paying users have a FUTURE timestamp (next renewal) and are never demoted; only cancelled-and-elapsed users have a past one. Trial overlay still wins (mid-trial user with a stale paid sub sees elite).

Renamed `_parse_trial_start` to `_parse_utc_iso` (the helper was already generic; name now matches role; `trial_active` caller updated).

Five new unit tests in `test_entitlements.py`: past+no-trial to free (leak close), future+no-trial to pro (paying user safe), past+active-trial to elite (overlay wins), None to unchanged, garbage to pro (fail-closed). All use monkeypatched `_now()`.

Live test-client walk: synthesized stored-pro + past `tier_effective_until` + no trial resolved to nav badge FREE and locked state across `/watchlist`, `/screener`, `/penny`.

Clean commit (no P23 content trip). One em-dash caught by the commit hook's dash gate in a test docstring, fixed before commit.

### c3c0111: friendly tier_limit message in /watchlist new-watchlist modal (item 3)
The page modal's `submitNew()` rendered the raw enum literal `tier_limit` via `.textContent` because it never consumed the friendly handler the picker uses. Fix: extracted a shared `window.formatWatchlistLimitError(err)` helper into `_watchlist_picker.html` (included on every authed page via `_nav.html`, so always present); both the picker pill and the modal call it. The modal's `tier_limit` branch switched to `.innerHTML` (scoped to that branch only; generic errors still use `.textContent`, so no arbitrary-HTML injection).

mark2 now sees "Watchlist limit reached (1/0 . Free). Upgrade to Pro for more. View plans" with a `/pricing` link (200), instead of the bare string. Pure template change, no P23 trip.

## Part 38 queue (in order)

1. **Item 4: /penny/screener over-gating, fix DESIGNED not built.** Phase 1 complete this session. The dedicated `/penny/screener` page full-page-locks both Free AND Pro at the route (`locked = not can_view_penny_signals(tier)`, where `can_view_penny_signals` returns `tier == 'elite'` only), hiding the row table entirely. Violates the locked penny-gating invariant: gate the SIGNAL, not the ticker. **Answer 1 LOCKED by Mark:** the page must show the row table to all tiers with the score/rating gated, mirroring the main `/screener` contract. NOTE: the `/api/screener` per-row strip (`strip_scores_for_non_elite`) is already correct and must NOT be touched; only the `/penny/screener` PAGE route + template over-gate.
   - **Proposed fix (CC, AWAITING MARK'S LOCK, not decided):**
     - (A) Drop `locked` as the page gate, pass effective `tier` to the template, collapse `{% if locked %}`, make `boot()` unconditional.
     - (B) Replace the full-page teaser with a single non-elite upsell BANNER above the table. CC recommends banner over per-cell padlocks, to avoid a one-off cell-lock UI that diverges from the product-wide bare-hyphen convention for stripped cells. Athena concurs as a lean, not a lock; decide at Part 38 open.
     - (C) Reuse the bare hyphen for stripped cells.
     - (D) Free and Pro render identically on this page (both non-elite, whole table is penny-band by construction).
     - (E) Add a smoke test: non-elite sees banner, elite does not.
   - Phase 2 will touch `web/app.py` (P23 path-match, not content-match; expect hook trip, Mark clears). DECIDE banner-vs-per-cell at Part 38 open, then run Phase 2.

2. **Pre-production-flip browser check.** Before flipping Stripe to live keys: verify a real cancelled-and-elapsed user (stored paid, past `tier_effective_until`, no trial) renders as free in a real browser against the live DB, not just the test client. The logic is proven; this is the eyes-on confirmation for the irreversible-money moment.

3. **Parked untracked files, decide.** `AGENTS.md` (origin unknown since Part 33; run `git log --oneline -- AGENTS.md`, likely nothing since it is untracked) and `docs/dash_sweep_plan.md` (a real em-dash/en-dash typography-sweep inventory, 827 occurrences across 96 files, generated 1 June; NOT related to the downgrade sweep despite the name). Athena's call: track `dash_sweep_plan.md` as the design record for a future em-dash cleanup arc; resolve `AGENTS.md` after the git-log check. Neither blocks anything.

4. **Stale comment references to _parse_trial_start.** The rename to `_parse_utc_iso` left stale doc-comment references at `database/db.py:925` and `web/app.py:267` (comments only, no runtime impact). Two-line cosmetic fix; fold into the parked-files tidy.

## Loose threads / notes banked (Part 37)

- **THM score lineage (resolved, no action).** A walk header this session cited THM at composite 77.1 STRONG_BUY; the live `/api/screener` render returns 61.5 STRONG_HOLD (scoring_version 0.17.0, verified against `signal_scores` latest by `scored_at`). The 77.1 was a stale historical row surfaced by an exploratory LEFT JOIN that fanned across multiple scoring entries. Current truth is 61.5 STRONG_HOLD. The walk DATA was correct (None for non-elite, 61.5 for elite); only the typed header note was stale. No bug.

- **P28 fixture gap, no stable post-trial Pro fixture.** marktest1 (id 8) is stored 'pro' but inside its 7-day trial (started 2026-05-29), so it resolves to effective-elite until approximately 2026-06-05 and is UNUSABLE as a Pro-band fixture during that window. Every stored-Pro account drifts to effective-elite for its first 7 days. Pro-band walks must currently synthesize a stored-pro-no-trial fixture via test-client monkeypatch (the pattern used for the expired-pro walk this session and the item-4 Walk B). Fix options (defer the choice): (a) a dedicated post-trial stored-pro fixture with `trial_started_at` backdated past `TRIAL_DAYS`, or (b) a documented synth-fixture helper in `tests/conftest.py`. Bank for fixture tidy.

- **Process note, gate-detection signal.** The item-4 walk burned two false lock-detection signals (a CSS class present regardless of state) before landing on a branch-exclusive string ("Available on the Elite tier", emitted only inside `{% if locked %}`). Lesson: when the test for "did a template branch render" is needed, grep the template for a branch-EXCLUSIVE string and confirm exclusivity FIRST, before walking. CC self-corrected (the P16 instinct held) but third, not first.

## Test accounts (use the right fixture, see P28)
- **mark2** (id 6): stored free, no trial, effective free. THE fixture for locked-state verification.
- **beta2** (id 9): stored free, active trial, effective ELITE. Sees everything unlocked (correct). Cannot exercise locked-state gates.
- **markn** (id 2): stored elite, effective elite.
- **marktest1** (id 8): stored pro, but CURRENTLY mid-trial so resolves effective-elite until approximately 2026-06-05. See the P28 fixture gap above before using it as a Pro-band fixture.

## Infra (Part 37 session)
- Gunicorn restarted after each `web/app.py` and `entitlements.py` commit per drift discipline. Last live PID 70957; re-verify on Part 38 open. `/pricing` returned 200 after each restart.
- Suite at session close: 395 passed, 2 skipped (pre-existing FMP price-targets + economic-calendar empty-cache skips).
- Commit-1 tier-read guard green throughout.
- Mechanical dash-reject pre-commit hook LIVE (commit f59422a, Part 35). Pass 0 scans every added line in the staged diff for U+2014 and U+2013; rejects on any hit. Pre-existing dashes are not policed. It caught one em-dash in a test docstring this session (c21f225), working as intended.
- Stripe on TEST keys. thesignalvault.io live behind Cloudflare.

## Prior arcs (condensed)

### Part 35: pricing build + dash arc
Built `/pricing` across 3 commits: `web/templates/pricing.html`, `config/pricing.py`, `scripts/verify_pricing.py`, a public `/pricing` route in `web/app.py` (no auth; reads session `user_id` to swap signed-out CTAs for a signed-in banner), and repointed `_locked_teaser.html` default link from `/account` (404) to `/pricing`. All 8 Stripe values verified against EXPECTED: $29/$79 mo, $261/$711 yr USD; GBP 24.99/74.99 mo, GBP 224.91/674.91 yr; `verify_pricing.py` exits 0. Em-dash governance section added to `CLAUDE.md` (prose-targeted, hyphen allowed for numeric ranges and "no data" placeholders). CLAUDE.md pricing text confirmed: two-tier, 25 percent annual, no Starter residue (the only `20%` is the unrelated portfolio margin requirement).

### Part 36: walk verification
All 7 pricing and enforcement walks passed for effective-free: `/pricing` logged-out and logged-in, currency switch (GBP/USD, en-GB default to GBP, all annuals correct at 25 percent), Dashboard Panel 7 lock, `/penny` lock, `/penny/screener` full-page lock, `/watchlist` create gate. Every "Upgrade to Elite" resolved to `/pricing`. Conclusion: enforcement sound for effective-free. Two findings carried into Part 37 and both now resolved: the `tier_limit` raw-code modal defect (item 3, fixed c3c0111) and the deeper enforcement sweep (items 1/2/5, fixed c9d1975 + c21f225). The `/penny/screener` full-page lock that Part 36 recorded as correct was later found to over-gate Pro (item 4, Part 38).