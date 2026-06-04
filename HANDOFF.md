# SignalIntel Session Handoff

**Last updated:** end of Part 38 (4 June 2026)
**Engine:** SCORING_ENGINE_VERSION 0.17.0 (unchanged)
**Repo:** all Part 38 commits pushed to origin/main (650cbbd, 8bd0ce3, 06c6e26).

## Where we are
The Stripe production-key flip is now unblocked on every technical axis. All three Part 38 items shipped. `/penny/screener` now shows rows to all tiers with score/rating gated via a single non-elite banner, honouring the gate-the-signal-not-the-ticker invariant. The cancelled-and-elapsed downgrade resolver was eyes-on verified against the live DB and live app via a real browser walk (cancelcheck1 fixture staged, walked, removed). The two long-parked untracked files (AGENTS.md, docs/dash_sweep_plan.md) are now tracked, and the six stale `_parse_trial_start` comment references from the Part 37 rename are cleaned up.

Stripe remains on TEST keys. The production-key flip is now fully unblocked on every internal axis; what remains is a business/product call by Mark, not a technical gate.

## Part 38: penny over-gating fix, downgrade walk, parked-file tidy (commits 650cbbd, 8bd0ce3, 06c6e26, pushed)

### 650cbbd: /penny/screener over-gating fix
Route stopped passing `locked`, now passes `tier = effective_tier(user)`. The template's full-page teaser branch was removed; the table renders unconditionally; a single non-elite upsell banner sits above the table with the branch-exclusive string "Penny scores are an Elite feature." and a CTA to `/pricing`; the bare-hyphen convention is retained for stripped cells via the existing `/api/screener` per-row strip (`strip_scores_for_non_elite` UNTOUCHED). New smoke test `tests/test_penny_screener_gating.py` (2 functions, P15 docstrings): non-elite sees banner + table; elite sees table, no banner. Three browser walks passed: mark2 (effective free) sees banner + hyphens; markn (elite) no banner, real values; marktest1 (mid-trial, so effective elite via overlay) no banner, real values. Gunicorn restarted, new PID 99255.

### 8bd0ce3: rename stale _parse_trial_start references to _parse_utc_iso
Renamed `_parse_trial_start` to `_parse_utc_iso` in 6 doc-comment/docstring sites (`database/db.py:925`, `web/app.py:267`, `tests/test_registration_trial.py:7, 15, 45, 69`). Comments only, no runtime change. The P23 hook tripped on db.py + app.py path-match (auth-adjacent), cleared via `--no-verify` (Mark's explicit call). Pre-existing em-dashes on two of the touched test lines were deferred to the dash-sweep arc per Mark's call; partial glyph cleanup would muddy the dash inventory.

### 06c6e26: track AGENTS.md and docs/dash_sweep_plan.md
Tracked `AGENTS.md` (Codex agent-bootstrap mirror of CLAUDE.md, seeded 25 May 2026, 343 lines) and `docs/dash_sweep_plan.md` (1,769-line em-dash/en-dash typography inventory, generated 1 June 2026, the design record for a future cleanup arc). Required `--no-verify` (Mark authorized): the dash hook inherently rejects an inventory of dashes; AGENTS.md is the pre-sweep CLAUDE.md mirror. This is the textbook legitimate hook bypass.

## Loose threads / notes banked (Part 38)
- **cancelcheck1 fixture (id 10) was staged, browser-walked, and removed** in the same session. Pattern is reusable if a future cancelled-and-elapsed check is needed: insert via the canonical `create_user` helper, UPDATE tier='pro' + tier_effective_until=past + trial_started_at=NULL, walk, DELETE. About 5 minutes end-to-end. Codified as P32.
- **The dash-sweep arc (docs/dash_sweep_plan.md) is now tracked and ready** to be picked up when prioritised. 827 occurrences across 96 files (global figure); 284 risky rows per the inventory's List 1.
- **P28 fixture gap still active.** marktest1 (id 8) is stored pro but mid-trial, so it resolves effective-elite until approximately 2026-06-05. It will expire naturally around 2026-06-05; until then, Pro-band walks need monkeypatched fixtures.

## Test accounts (use the right fixture, see P28)
- **mark2** (id 6): stored free, no trial, effective free. THE locked-state fixture.
- **beta2** (id 9): stored free, active trial, effective ELITE.
- **markn** (id 2): stored elite, effective elite.
- **marktest1** (id 8): stored pro, mid-trial through approximately 2026-06-05, currently effective elite.

## Infra (Part 38 close)
- Gunicorn last live master PID 99255 (worker 99900 respawn once mid-session, normal). Re-verify on next session open.
- Suite: 397 passed, 2 skipped (the pre-existing FMP price-targets + economic-calendar empty-cache skips).
- Three new tests landed this session (tests/test_penny_screener_gating.py x 2 plus the 5 in test_entitlements.py already counted in Part 37); the +2 is what took 395 to 397.
- Dash-reject pre-commit hook live and working as intended; tripped legitimately twice this session (test docstring during the rename, then the tracking commit), both cleared by Mark.
- Stripe on TEST keys; thesignalvault.io live behind Cloudflare.

## Next session queue (LOCKED ORDER, fresh chat)
1. **Component-rendering refactor (array-driven).** HARD PREREQUISITE before Yahoo components land. Phase 1 will be long: every component's render path, every consumer template, persistence shape. Wants its own session, large surface.
2. **Yahoo Finance pipeline + components 9 to 16.** The substrate expansion.
3. **Backtest validation harness.** Unblocked by v0.17.0 sub-score persistence; should run before too many new components land so the harness shape is set against a smaller component set.
4. **FINRA short-interest composite component.**
5. **Scraper substrate audit** (volume + avg_volume silent-NULL).
6. **Dash-sweep arc.**

Out-of-band: Stripe production-key flip. Every internal gate green; this is a business/product call by Mark.

## Prior arcs (condensed)

### Part 37: paywall enforcement hardening (commits c9d1975 to c3c0111, pushed)
Closed the cancelled-subscription downgrade leak that had blocked the Stripe production-key flip. c21f225 added lazy `tier_effective_until` expiry inside `effective_tier`: a cancelled-and-elapsed user collapses to free, live payers with a future renewal timestamp are never demoted, and the trial overlay still wins; plus five entitlement unit tests. c9d1975 memoised `current_user()` on `flask.g` and routed five stored-tier bypass surfaces (dashboard nav, `/watchlist`, the two `/api/watchlists` routes, and `_nav.html` via a new `nav_tier` context processor) through `effective_tier`, closing the fail-closed trial bug that showed trialists a FREE badge and locked them out of watchlists; added the `tier-read` guard test. c3c0111 gave the `/watchlist` new-watchlist modal the friendly `tier_limit` message via a shared `formatWatchlistLimitError` helper. Renamed `_parse_trial_start` to `_parse_utc_iso` (the six surviving doc-comment references were cleaned up in Part 38, commit 8bd0ce3).

### Part 35: pricing build + dash arc
Built `/pricing` across 3 commits: `web/templates/pricing.html`, `config/pricing.py`, `scripts/verify_pricing.py`, a public `/pricing` route in `web/app.py` (no auth; reads session `user_id` to swap signed-out CTAs for a signed-in banner), and repointed `_locked_teaser.html` default link from `/account` (404) to `/pricing`. All 8 Stripe values verified against EXPECTED: $29/$79 mo, $261/$711 yr USD; GBP 24.99/74.99 mo, GBP 224.91/674.91 yr; `verify_pricing.py` exits 0. Em-dash governance section added to `CLAUDE.md` (prose-targeted, hyphen allowed for numeric ranges and "no data" placeholders). CLAUDE.md pricing text confirmed: two-tier, 25 percent annual, no Starter residue (the only `20%` is the unrelated portfolio margin requirement).

### Part 36: walk verification
All 7 pricing and enforcement walks passed for effective-free: `/pricing` logged-out and logged-in, currency switch (GBP/USD, en-GB default to GBP, all annuals correct at 25 percent), Dashboard Panel 7 lock, `/penny` lock, `/penny/screener` full-page lock, `/watchlist` create gate. Every "Upgrade to Elite" resolved to `/pricing`. Conclusion: enforcement sound for effective-free. Two findings carried into Part 37 and both now resolved: the `tier_limit` raw-code modal defect (item 3, fixed c3c0111) and the deeper enforcement sweep (items 1/2/5, fixed c9d1975 + c21f225). The `/penny/screener` full-page lock that Part 36 recorded as correct was later found to over-gate Pro (item 4, Part 38).
