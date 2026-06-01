# SignalIntel Session Handoff

**Last updated:** end of Part 36 (1 June 2026)
**Engine:** SCORING_ENGINE_VERSION 0.17.0
**Repo:** all local commits pushed to origin/main as of this handoff.

## Where we are
The revenue front-door is built and browser-verified. The `/pricing` page ships, Stripe values reconcile, and every tier-gated surface locks correctly for an effective-free user. Paywall enforcement (the deeper sweep) is the Part 37 build.

## Part 35: pricing build + dash arc
- Built `/pricing` across 3 commits: `web/templates/pricing.html`, `config/pricing.py`, `scripts/verify_pricing.py`, a public `/pricing` route in `web/app.py` (no auth; reads session `user_id` to swap signed-out CTAs for a signed-in banner), and repointed `web/templates/_locked_teaser.html` default link from `/account` (404) to `/pricing`.
- All 8 Stripe values verified against EXPECTED: $29/$79 mo, $261/$711 yr USD; £24.99/£74.99 mo, £224.91/£674.91 yr GBP. `verify_pricing.py` exits 0.
- Em-dash arc: swept 5 files clean; added a no-dash governance section to `CLAUDE.md` (~228/230/236), written with Unicode codepoint names, refined to prose-targeted with deliberate equivalents (hyphen allowed for numeric ranges and "no data" placeholders). Mechanical pre-commit dash-reject hook DEFERRED (repo must be fully dash-clean first).
- CLAUDE.md pricing text confirmed correct: two-tier, 25 percent annual, no Starter/three-tier residue. The only `20%` in CLAUDE.md is the unrelated portfolio margin requirement.

## Part 36: walk verification
All 7 pricing and enforcement walks concluded, all pass:
1. `/pricing` logged-out: clean, em-dash fixed, "Most popular" ribbon on Pro, no app-footer bleed.
2. `/pricing` logged-in (markn): "You're signed in" banner, "Back to dashboard", trial CTAs swapped for status pills.
3. Currency switch: `?currency=gbp` and `?currency=usd` both correct; en-GB default resolves to GBP. All four annuals arithmetically correct at 25 percent.
4. Dashboard Panel 7 (mark2, free): locked teaser, padlock, blur, "Upgrade to Elite" to `/pricing`.
5. `/penny` (mark2): both panels locked to `/pricing`.
6. `/penny/screener` (mark2): full-page Elite lock to `/pricing`.
7. `/watchlist` create (mark2): create gate fires correctly (cap 0 blocks). UX defect: modal renders raw error code `tier_limit` instead of a friendly message plus `/pricing` link.

Href gate confirmed: every "Upgrade to Elite" resolves to `http://127.0.0.1:5001/pricing`.

Conclusion: enforcement is sound for effective-free; every proprietary surface locks. Findings below are enforcement polish plus one real leak, all Part 37.

## Test accounts (use the right fixture, see P28)
- **mark2** (id 6): stored free, no trial, effective free. THE fixture for locked-state verification.
- **beta2** (id 9): stored free, active trial, effective ELITE. Sees everything unlocked (correct). Cannot exercise locked-state gates.
- **markn** (id 2): stored elite, effective elite.
- **marktest1**: stored pro (Part 34). Use for Pro-band cells.

## Part 37 scope: paywall enforcement
1. **Watchlist surfaces read stored `tier` not `effective_tier(user)`.** 5 sites: `web/app.py` ~1046 (/watchlist GET), ~1062 (GET /api/watchlists), ~1122 (POST create gate); `watchlist.html` ~135-141 (tier badge); `_watchlist_picker.html` ~200-204 (View-plans condition). Violates the locked invariant at `config/entitlements.py:14-16`. Fail-CLOSED: locks effective-elite trialists out of watchlists. Lead build item.
2. **`/watchlist` new-watchlist modal shows raw `tier_limit`** instead of friendly message plus `/pricing` link. The friendly "View plans" prompt lives only in `_watchlist_picker.html`; the page modal has a separate raw path.
3. **Downgrade sweep.** `customer.subscription.deleted` sets `tier_effective_until` but nothing reads it to drop the tier. Cancelled users keep paid access indefinitely. Fail-OPEN revenue leak. Hard gate before the production-key flip.
4. **Pro-band penny screener untested.** Free correctly sees a full lock; the Pro behaviour (tickers visible, penny scores locked, per gate-the-signal) is the untested matrix cell. Use marktest1.
5. **"FREE" nav badge shows while effective-elite during trial.** UX tell, same root as item 1 (badge reads stored tier).

## Loose ends
- Two untracked files parked: `AGENTS.md`, `docs/dash_sweep_plan.md`. Decide in Part 37 (track, gitignore, or delete).
- Mechanical dash-reject pre-commit hook is LIVE (commit f59422a). Pass 0 scans every added line in the staged diff for U+2014 and U+2013; rejects on any hit. Pre-existing dashes are not policed.
