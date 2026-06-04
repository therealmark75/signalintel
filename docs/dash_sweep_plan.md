# Dash sweep plan (Phase 1, inventory only)

Generated 2026-06-01T09:07:39Z by a read-only Python analysis pass.
Phase 1: inventory only. Phase 2 will mechanically apply the replacements per spec below.
This plan is the only file created in Phase 1. The plan itself is excluded from the scan to avoid self-reference.

## Replacement spec (Phase 2 will apply this)

- **Prose em-dash or en-dash**: comma, period, semicolon, colon, or brackets, per sentence fit.
- **Title-separator em-dash** (for example `Dashboard <em-dash> SignalIntel`): hyphen with spaces, ` - `.
- **Placeholder em-dash** (glyph is the whole cell value): single hyphen, `-`.
- **Numeric-range en-dash** (for example `0<en-dash>100`, `$1<en-dash>$5`): the word `to` (spaced) or hyphen `-` (compact).

## List 1: P23-flagged and STRING-LITERAL occurrences (read first)

These rows need extra care in Phase 2: P23 commits require explicit clearance; STRING-LITERAL changes need a coherent test-expectation review since `assert msg == "..."` style tests embed the literal glyph.

Total risky rows: **284**

| file:line | glyph | category | flags | excerpt |
|---|---|---|---|---|
| `config/entitlements.py:2` | em | prose | P23 | `Capability predicates and the trial-overlay resolver — the single` |
| `config/entitlements.py:11` | em | prose | P23 | `holds the post-trial floor — 'free' for an unpaid trialist; 'pro'` |
| `config/entitlements.py:15` | em | prose | P23 | `user['tier'] raw. The raw column is the post-trial floor only — using` |
| `config/entitlements.py:64` | em | prose | P23 | `Fail-closed semantics — every one of these returns False:` |
| `config/entitlements.py:79` | em | prose | P23,STRING-LITERAL | `"""Read rank from config/tiers.py USER_TIERS[...]['order'] — single source.` |
| `config/entitlements.py:98` | em | prose | P23 | `Post-trial, falls back to stored — a paid Pro user falls to 'pro',` |
| `config/entitlements.py:119` | em | prose | P23 | `# obtain from effective_tier(user). NEVER pass user['tier'] raw — the` |
| `config/entitlements.py:124` | em | prose | P23,STRING-LITERAL | `"""Elite only — the $1-5 score/rating panel is the Elite hook.` |
| `config/entitlements.py:170` | em | prose | P23,STRING-LITERAL | `"""Monthly tournament entry. Pro or elite — deliberately NOT` |
| `config/entitlements.py:191` | em | prose | P23 | `# 10+ leak surfaces stay synchronised — adding a new score column to` |
| `config/entitlements.py:207` | em | prose | P23 | `# carry them — safe to extend the global set.` |
| `config/entitlements.py:230` | em | prose | P23 | `This is the locked Free=floor invariant — a free user` |
| `config/entitlements.py:237` | em | prose | P23 | `and would raise TypeError on assignment — that is an explicit` |
| `config/entitlements.py:240` | em | prose | P23 | `\`price_key\` defaults to 'price' but accepts alternatives — e.g.` |
| `config/entitlements.py:262` | em | prose | P23 | `flags (RSI/SMA/short/analyst/52w bands) survive — they're` |
| `config/entitlements.py:265` | em | prose | P23 | `PROPRIETARY_FLAGS is sourced from signals/scorer.py — the same` |
| `config/entitlements.py:277` | em | prose | P23 | `(Free=floor — no proprietary signal output anywhere).` |
| `config/tiers.py:2` | em | prose | P23 | `User tier definitions — single source of truth for all feature limits.` |
| `config/tiers.py:9` | em | prose | P23 | `tier — a trialist's stored users.tier is 'free' while the` |
| `config/tiers.py:15` | em | prose | P23,STRING-LITERAL | `DB column coerces to 'free' via get_tier()'s default branch — no` |
| `config/tiers.py:22` | em | prose | P23,STRING-LITERAL | `'description':     'Unpaid floor — paywall in effect',` |
| `dashboard/dashboard.py:68` | em | prose | STRING-LITERAL | `title = f"Top Signals" + (f" — {rating}" if rating else " — All Ratings")` |
| `dashboard/dashboard.py:68` | em | prose | STRING-LITERAL | `title = f"Top Signals" + (f" — {rating}" if rating else " — All Ratings")` |
| `database/db.py:924` | em | prose | STRING-LITERAL | `# trial_started_at is the caller's responsibility — register() stamps a` |
| `docs/data_source_map.md:5` | em | prose | STRING-LITERAL | `- Drop **congressional trading** and **ESG** from the composite score and keep them as dashboard surfaces o...` |
| `docs/data_source_map.md:5` | en | numeric-range | STRING-LITERAL | `- Drop **congressional trading** and **ESG** from the composite score and keep them as dashboard surfaces o...` |
| `docs/data_source_map.md:5` | en | numeric-range | STRING-LITERAL | `- Drop **congressional trading** and **ESG** from the composite score and keep them as dashboard surfaces o...` |
| `docs/data_source_map.md:42` | em | prose | STRING-LITERAL | `\| **Yahoo Finance / yfinance** \| Free unofficial scraping \| n/a \| None \| JSON (private) \| The pipelin...` |
| `docs/data_source_map.md:114` | en | numeric-range | STRING-LITERAL | `\| **Congressional Trading** \| Ziobrowski 2004, *JFQA* 39(4) vs Eggers & Hainmueller 2013, *Journal of Pol...` |
| `docs/data_source_map.md:114` | en | numeric-range | STRING-LITERAL | `\| **Congressional Trading** \| Ziobrowski 2004, *JFQA* 39(4) vs Eggers & Hainmueller 2013, *Journal of Pol...` |
| `docs/data_source_map.md:114` | en | numeric-range | STRING-LITERAL | `\| **Congressional Trading** \| Ziobrowski 2004, *JFQA* 39(4) vs Eggers & Hainmueller 2013, *Journal of Pol...` |
| `docs/data_source_map.md:115` | en | prose | STRING-LITERAL | `\| **ESG** \| Friede/Busch/Bassen 2015 *JSF&I* vs Pedersen/Fitzgibbons/Pomorski 2021, *JFE* 142(2) \| Fried...` |
| `docs/data_source_map.md:185` | em | prose | STRING-LITERAL | `- **Reddit and Twitter/X API terms shifted hard in 2023 and again in early 2026.** Reddit's paid tier is ex...` |
| `docs/data_source_map.md:187` | en | numeric-range | STRING-LITERAL | `- **Congressional trading alpha is sample-dependent and contested.** The famous ~12%/yr Ziobrowski 2004 Sen...` |
| `docs/data_source_map.md:187` | en | numeric-range | STRING-LITERAL | `- **Congressional trading alpha is sample-dependent and contested.** The famous ~12%/yr Ziobrowski 2004 Sen...` |
| `docs/data_source_map.md:187` | en | numeric-range | STRING-LITERAL | `- **Congressional trading alpha is sample-dependent and contested.** The famous ~12%/yr Ziobrowski 2004 Sen...` |
| `docs/scoring_invariants.md:248` | em | prose | STRING-LITERAL | `- The response must include a clear status message (e.g. "Insufficient data — backtest stats accumulating")` |
| `docs/scoring_invariants.md:259` | en | numeric-range | STRING-LITERAL | `- "Composite score must be in range 0–100"` |
| `docs/scoring_invariants.md:260` | en | numeric-range | STRING-LITERAL | `- "Sector strength score must be in range 0–100"` |
| `docs/stripe_billing_phase1.md:305` | em | prose | STRING-LITERAL | `**Audit.** \`tier_before\` / \`tier_after\` make it possible to reconstruct exactly what happened to a user...` |
| `docs/stripe_billing_phase1.md:400` | em | prose | STRING-LITERAL | `My read: **Option B** is the cleanest for SaaS reality (canceled users come back; making them re-register l...` |
| `main.py:317` | em | prose | STRING-LITERAL | `f"📊 <b>SignalIntel — {len(relevant)} watchlist changes</b>\n"` |
| `main.py:321` | em | prose | STRING-LITERAL | `logger.info("_send_rating_alerts: throttled — %d changes exceeded max %d", len(relevant), TELEGRAM_ALERT_MA...` |
| `main.py:351` | em | prose | STRING-LITERAL | `send_alert(f"📋 <b>SignalIntel — watchlist changes</b>\n\n{body}")` |
| `main.py:373` | em | prose | STRING-LITERAL | `f"🚨 SignalIntel — FMP entitlement failure\n\n"` |
| `main.py:404` | em | prose | STRING-LITERAL | `f"🚨 SignalIntel — FMP entitlement failure\n\n"` |
| `main.py:426` | em | prose | STRING-LITERAL | `lines = [f"📊 <b>SIGNALINTEL — DAILY SUMMARY</b>  {date.today()}", ""]` |
| `main.py:925` | em | prose | STRING-LITERAL | `f"🚨 SignalIntel — FMP entitlement failure\n\n"` |
| `scrapers/fmp_scraper.py:50` | em | prose | STRING-LITERAL | `f"FMP HTTP {status_code} on {path} — endpoint not included "` |
| `scrapers/fmp_scraper.py:77` | em | prose | STRING-LITERAL | `"Aborting job — re-enable once FMP rate limit clears."` |
| `scrapers/fmp_scraper.py:80` | en | prose | STRING-LITERAL | `logger.warning(f"[FMP] Rate limited ({streak}/{FMP_CIRCUIT_BREAKER_THRESHOLD}) – sleeping 10s")` |
| `scrapers/markets_scraper.py:93` | em | prose | STRING-LITERAL | `logger.info(f"[markets] Scrape complete — {total} rows total")` |
| `scrapers/sector_scraper.py:90` | em | prose | STRING-LITERAL | `logger.error(f"[Sector] {etf}: fetch failed — {e}")` |
| `scrapers/sector_scraper.py:151` | em | prose | STRING-LITERAL | `logger.warning(f"[Sector] {sector}: no data — assigned neutral score 50")` |
| `scrapers/sector_scraper.py:165` | em | prose | STRING-LITERAL | `logger.info(f"[Sector] Done — {len(results)} sectors written for {today}")` |
| `scrapers/yahoo_scraper.py:73` | em | prose | STRING-LITERAL | `"Aborting job — re-enable once Yahoo rate limit clears."` |
| `scrapers/yahoo_scraper.py:78` | en | prose | STRING-LITERAL | `f"for {ticker} {data_type} – sleeping 10s"` |
| `scripts/altman_distribution_analysis.py:285` | em | prose | STRING-LITERAL | `print(f"  {bin_name} ({label}) — selection: {rule}")` |
| `scripts/altman_distribution_analysis.py:313` | em | prose | STRING-LITERAL | `print("─── Z'' DISTRESS BIN — TOP SECTORS ────────────────────────────────")` |
| `scripts/altman_distribution_analysis.py:357` | em | placeholder | STRING-LITERAL | `print(f"{row_label_z0:32s} {_fmt(classic_neg):>16s} {'—':>16s}")` |
| `scripts/analyst_pt_event_study.py:215` | em | prose | STRING-LITERAL | `log.info(f"  cache MISS on {len(missing)} tickers — fetching incrementally")` |
| `scripts/analyst_pt_event_study.py:479` | em | prose | STRING-LITERAL | `print("  Lowers ratings before delisting are systematically absent — the")` |
| `scripts/analyst_pt_event_study.py:523` | em | prose | STRING-LITERAL | `print("    and at least 3× the placebo spread — the analyst events drive a")` |
| `scripts/analyst_pt_event_study.py:529` | em | prose | STRING-LITERAL | `print("    is softer than ideal — interpret magnitude cautiously.")` |
| `scripts/analyst_pt_event_study.py:570` | em | prose | STRING-LITERAL | `print("ANALYST PRICE-TARGET EVENT STUDY — RESULTS")` |
| `scripts/backfill_exchange.py:60` | em | prose | STRING-LITERAL | `logger.warning("Signal %d received — will exit cleanly after current ticker.", signum)` |
| `scripts/backfill_exchange.py:110` | em | prose | STRING-LITERAL | `logger.info("backfill_exchange.py — START")` |
| `scripts/backfill_exchange.py:124` | em | prose | STRING-LITERAL | `logger.info("Nothing to do — all tickers already have exchange populated.")` |
| `scripts/backfill_exchange.py:163` | em | prose | STRING-LITERAL | `"%d consecutive failures — possible FinViz throttle. "` |
| `scripts/drop_screener_snapshots_exchange.py:22` | em | prose | STRING-LITERAL | `print("exchange column not present — nothing to do.")` |
| `scripts/drop_screener_snapshots_exchange.py:25` | em | prose | STRING-LITERAL | `print(f"exchange column found — {cols.index('exchange')+1}/{len(cols)} columns")` |
| `scripts/install-hooks.sh:30` | em | prose | STRING-LITERAL | `echo "WARNING: existing symlink points to '$current_link' — replacing"` |
| `scripts/install-hooks.sh:34` | em | prose | STRING-LITERAL | `echo "WARNING: existing non-symlink file at $TARGET — backing up to $backup"` |
| `scripts/purge_sub_threshold_rating_changes.py:122` | em | prose | STRING-LITERAL | `logger.error("Purge FAILED — rolled back: %s", e)` |
| `scripts/rebuild_rating_changes.py:171` | em | prose | STRING-LITERAL | `logger.error("Rebuild FAILED — rolled back: %s", e)` |
| `scripts/reclassify_legal_risk.py:91` | em | prose | STRING-LITERAL | `print("(Dry run — no DB changes written)")` |
| `scripts/setup_stripe_products.py:74` | em | prose | P23 | `enabled on the account) — with at most 2 products to manage, a` |
| `scripts/setup_stripe_products.py:78` | em | prose | P23 | `.get() as an instance method — \`product.get(...)\` triggers` |
| `signals/scorer.py:878` | em | prose | STRING-LITERAL | `logger.debug("Skipped %s — price $%.4f below MIN_PRICE_FOR_SIGNAL", ticker, price)` |
| `signals/scorer.py:964` | em | prose | STRING-LITERAL | `f"({', '.join(sample)}{'...' if len(missing_legal) > 5 else ''}) — flagged for scraping"` |
| `tests/conftest.py:7` | em | prose | P23 | `DB: connects to data/trading_system.db — the live SQLite file. All queries` |
| `tests/conftest.py:57` | em | prose | P23,STRING-LITERAL | `assert date is not None, "signal_scores is empty — run the scorer first"` |
| `tests/test_api_rating_display.py:66` | em | prose | STRING-LITERAL | `pytest.skip("rating_changes is empty — no fixture data on this deploy")` |
| `tests/test_api_rating_display.py:75` | em | prose | STRING-LITERAL | `assert rating_events, f"no rating events returned for {ticker} — fixture assumption broken"` |
| `tests/test_api_rating_display.py:114` | em | prose | STRING-LITERAL | `pytest.skip("no rating_changes row with NULL old_rating — can't exercise initial-rating branch")` |
| `tests/test_api_rating_display.py:126` | em | prose | STRING-LITERAL | `f"(NULL old_rating row exists in DB) — got titles: "` |
| `tests/test_data_integrity.py:120` | em | prose | STRING-LITERAL | `assert len(latest_signals) >= 1000, f"Only {len(latest_signals)} signals — scorer may have failed"` |
| `tests/test_data_integrity.py:137` | em | prose | STRING-LITERAL | `pytest.skip("target_price is 0% — fmp_price_targets not yet populated")` |
| `tests/test_data_integrity.py:158` | em | prose | STRING-LITERAL | `pytest.skip("legal_risk table is empty — SEC scraper not yet run")` |
| `tests/test_data_integrity.py:163` | em | prose | STRING-LITERAL | `assert none_pct >= 70, f"'None' risk only {none_pct:.0f}% of classified tickers — classifier may be over-tr...` |
| `tests/test_data_integrity.py:178` | em | prose | STRING-LITERAL | `pytest.skip("earnings_history is empty — Yahoo scraper not yet run")` |
| `tests/test_data_integrity.py:183` | em | prose | STRING-LITERAL | `assert latest >= cutoff, f"earnings_history last scraped {row[0]} — older than 14 days"` |
| `tests/test_data_integrity.py:196` | em | prose | STRING-LITERAL | `pytest.skip("financial_statements is empty — Yahoo financials scraper not yet run")` |
| `tests/test_data_integrity.py:201` | em | prose | STRING-LITERAL | `assert latest >= cutoff, f"financial_statements last scraped {row[0]} — older than 14 days"` |
| `tests/test_data_integrity.py:214` | em | prose | STRING-LITERAL | `pytest.skip("analyst_changes is empty — Yahoo analyst scraper not yet run")` |
| `tests/test_data_integrity.py:219` | em | prose | STRING-LITERAL | `assert latest >= cutoff, f"analyst_changes last scraped {row[0]} — older than 14 days"` |
| `tests/test_data_integrity.py:232` | em | prose | STRING-LITERAL | `pytest.skip("institutional_holders is empty — Yahoo holders scraper not yet run")` |
| `tests/test_data_integrity.py:237` | em | prose | STRING-LITERAL | `assert latest >= cutoff, f"institutional_holders last scraped {row[0]} — older than 14 days"` |
| `tests/test_data_integrity.py:294` | em | prose | STRING-LITERAL | `pytest.skip("earnings_calendar is empty — FMP earnings scraper not yet run")` |
| `tests/test_data_integrity.py:299` | em | prose | STRING-LITERAL | `assert latest >= cutoff, f"earnings_calendar last updated {row[0]} — older than 72h"` |
| `tests/test_data_integrity.py:313` | em | prose | STRING-LITERAL | `pytest.skip("dividends is empty — FMP dividend scraper not yet run")` |
| `tests/test_data_integrity.py:318` | em | prose | STRING-LITERAL | `assert latest >= cutoff, f"dividends last updated {row[0]} — older than 14 days"` |
| `tests/test_data_integrity.py:336` | em | prose | STRING-LITERAL | `pytest.skip("fmp_price_targets is empty — scoring job has not yet populated cache")` |
| `tests/test_data_integrity.py:341` | em | prose | STRING-LITERAL | `assert latest >= cutoff, f"fmp_price_targets last updated {row[0]} — older than 14 days"` |
| `tests/test_data_integrity.py:360` | em | prose | STRING-LITERAL | `pytest.skip("economic_calendar is empty — FMP economic scraper not yet run")` |
| `tests/test_data_integrity.py:365` | em | prose | STRING-LITERAL | `assert latest >= cutoff, f"economic_calendar last scraped {row[0]} — older than 72h"` |
| `tests/test_entitlements.py:2` | em | prose | P23 | `Tests for config/entitlements.py — capability predicates + trial overlay.` |
| `tests/test_entitlements.py:35` | em | prose | P23 | `Ignores: timezone offsets — FIXED_NOW is naive UTC same as _now().` |
| `tests/test_entitlements.py:67` | em | prose | P23 | `Catches: trial silently extending past the 7-day window — the` |
| `tests/test_entitlements.py:78` | em | prose | P23 | `Catches: higher-rank rule regressing — a paid Pro user mid-trial` |
| `tests/test_entitlements.py:87` | em | prose | P23 | `floor, not 'free' — a paying user keeps what they paid for.` |
| `tests/test_entitlements.py:108` | em | prose | P23 | `invisible — trial_grant is hardcoded to 'elite' and stored is` |
| `tests/test_entitlements.py:115` | em | prose | P23 | `elite+trial user would unexpectedly fall to stored — but` |
| `tests/test_entitlements.py:120` | em | prose | P23 | `Ignores: the >= vs > distinction — that would only be observable` |
| `tests/test_entitlements.py:203` | em | prose | P23 | `P15 silence: free AND pro denied — exactly one tier passes.` |
| `tests/test_entitlements.py:213` | em | prose | P23 | `P15 silence: free denied — paid floor only.` |
| `tests/test_entitlements.py:233` | em | prose | P23 | `P15 silence: free AND pro denied — Elite hook.` |
| `tests/test_entitlements.py:240` | em | prose | P23 | `# ── $5 boundary: can_view_score_for_ticker — both sides × every tier` |
| `tests/test_entitlements.py:266` | em | prose | P23 | `Catches: off-by-one — $5 is NOT in the penny band.` |
| `tests/test_entitlements.py:284` | em | prose | P23 | `# ── can_create_watchlist — delegation contract ────────────────────` |
| `tests/test_entitlements.py:304` | em | prose | P23,STRING-LITERAL | `"""TRIAL_DAYS must be 7 — locked decision.` |
| `tests/test_entitlements.py:312` | em | prose | P23 | `# ── strip_scores_for_non_elite — bulk row helper ──────────────────` |
| `tests/test_entitlements.py:321` | em | prose | P23 | `rows — so matrix tests verify the full PROPRIETARY_SCORE_FIELDS` |
| `tests/test_entitlements.py:370` | em | prose | P23 | `the unpaid floor — sees no proprietary scores at any price band.` |
| `tests/test_entitlements.py:377` | em | prose | P23 | `Catches: a future change that lets free see non-penny scores —` |
| `tests/test_entitlements.py:408` | em | prose | P23 | `price >= 5 rows — this is what Pro pays for.` |
| `tests/test_entitlements.py:466` | em | prose | P23 | `does NOT add keys that were absent on input — that would expand` |
| `tests/test_entitlements.py:491` | em | prose | P23 | `price field. Helper must honour the alternate key — the predicate` |
| `tests/test_entitlements.py:526` | em | prose | P23 | `# new_rating is now in PROPRIETARY_SCORE_FIELDS (rating alias) — stripped` |
| `tests/test_entitlements.py:538` | em | prose | P23 | `Ignores: timing — this is correctness, not perf.` |
| `tests/test_entitlements.py:596` | em | prose | P23 | `much (descriptive lost — over-broad gate) or too little` |
| `tests/test_entitlements.py:597` | em | prose | P23 | `(proprietary leaked — under-broad gate).` |
| `tests/test_entitlements.py:600` | em | prose | P23 | `constants — sourced via the PROPRIETARY_FLAGS frozenset, so this` |
| `tests/test_entitlements.py:664` | em | prose | P23,STRING-LITERAL | `"""Elite caller: helper short-circuits — proprietary flags` |
| `tests/test_fmp_entitlement_error.py:11` | em | prose | P23 | `Origin: 18 May 2026 economic_calendar staleness — HTTP 402 was silently` |
| `tests/test_fmp_entitlement_error.py:76` | em | prose | P23 | `_get() must raise FMPEntitlementError on HTTP 401 (unauthorized —` |
| `tests/test_fmp_entitlement_error.py:98` | em | prose | P23 | `_get() must raise FMPEntitlementError on HTTP 403 (forbidden —` |
| `tests/test_fmp_entitlement_error.py:134` | em | prose | P23 | `# Must not raise — the generic else branch returns None.` |
| `tests/test_fmp_entitlement_error.py:147` | em | prose | P23 | `forgets the log_run call — the 18 May root cause where the cron` |
| `tests/test_invariants.py:75` | em | prose | STRING-LITERAL | `f"across {len(latest_signals)} rows — the in-memory scores are being "` |
| `tests/test_invariants.py:145` | em | prose | STRING-LITERAL | `pytest.skip("sector_modifier_applied is all NULL — sector modifier not yet active")` |
| `tests/test_phase2b_scorers.py:90` | em | prose | STRING-LITERAL | `"""Only 1 quarter available — should work; decay weight = 4 only.` |
| `tests/test_phase2b_scorers.py:113` | em | prose | STRING-LITERAL | `"""Healthy company — all 9 signals pass → F=9 → 80.0.` |
| `tests/test_phase2b_scorers.py:134` | em | prose | STRING-LITERAL | `"""Distressed company — all 9 signals fail → F=1 → 20.0.` |
| `tests/test_registration_trial.py:7` | em | prose | P23 | `trial_started_at — when NULL, _parse_trial_start returns None,` |
| `tests/test_registration_trial.py:47` | em | prose | P23 | `Ignores: the exact reported elapsed seconds — only the` |
| `tests/test_registration_trial.py:63` | em | prose | P23,STRING-LITERAL | `"trial_started_at must be stamped, not NULL — this is the inert-trial guard"` |
| `tests/test_registration_trial.py:69` | em | prose | P23,STRING-LITERAL | `"trial overlay must be active on day 0 — _parse_trial_start must round-trip the stamp"` |
| `tests/test_registration_trial.py:81` | em | prose | P23 | `new parameter — they must still get a usable user row, just` |
| `tests/test_registration_trial.py:89` | em | prose | P23 | `Ignores: effective_tier behavior on the NULL-anchor row — that` |
| `tests/test_scorer.py:39` | em | prose | STRING-LITERAL | `f"but it is NOT in PROPRIETARY_FLAGS — the entitlements gate "` |
| `tests/test_scorer.py:55` | em | prose | STRING-LITERAL | `f"{expected!r} not in PROPRIETARY_FLAGS — gate would leak"` |
| `tests/test_scorer_snapshot.py:361` | em | prose | STRING-LITERAL | `f"{len(mismatches)} snapshot mismatches — refactor is not behaviour-preserving:\n"` |
| `tests/test_screener.py:88` | em | prose | STRING-LITERAL | `f"all-exchanges total={all_exchanges['total']} — exchange filter "` |
| `tests/test_setup_stripe_guard.py:8` | em | prose | P23 | `Tests here exercise only the pure-Python guard function — no Stripe` |
| `tests/test_setup_stripe_guard.py:38` | em | prose | P23 | `Ignores: the exact wording of the diagnostic — only the` |
| `tests/test_setup_stripe_guard.py:55` | em | prose | P23 | `populate STRIPE_SECRET_KEY before the script ran — would` |
| `tests/test_setup_stripe_guard.py:59` | em | prose | P23 | `Ignores: None/None-equivalent inputs — caller passes a string` |
| `tests/test_setup_stripe_guard.py:72` | em | prose | P23 | `Ignores: actual Stripe API connectivity — this asserts only the` |
| `tests/test_signal_labels.py:54` | em | prose | STRING-LITERAL | `f"tier_label('{rating}') = '{tier_label(rating)}' — expected '{expected}'"` |
| `tests/test_signal_labels.py:61` | em | prose | STRING-LITERAL | `f"tier_short('{rating}') = '{tier_short(rating)}' — expected '{expected}'"` |
| `tests/test_smoke.py:2` | em | prose | P23 | `Smoke tests — every page and key API endpoint must return HTTP 200.` |
| `tests/test_smoke.py:151` | em | prose | P23 | `Catches: missing WL header — indicates the column was not added.` |
| `tests/test_smoke.py:179` | em | prose | P23 | `Ignores: WlPicker.open internals — those are JS unit-level concerns.` |
| `tests/test_smoke.py:197` | em | prose | P23 | `P15: absence test — verifies the bad pattern is gone, not the good one.` |
| `tests/test_smoke.py:239` | em | prose | P23 | `/watchlist must include the tier badge — catches regressions where the` |
| `tests/test_smoke.py:254` | em | prose | P23 | `numeric limit/current fields — not a plain string.` |
| `tests/test_smoke.py:321` | em | prose | P23 | `The string 'unauthorized' must never appear in any rendered page body —` |
| `tests/test_smoke.py:371` | em | prose | P23 | `'FREE' — not 'ELITE' — and the DB row MUST still read 'free' after the` |
| `tests/test_smoke.py:371` | em | prose | P23 | `'FREE' — not 'ELITE' — and the DB row MUST still read 'free' after the` |
| `tests/test_smoke.py:386` | em | prose | P23,STRING-LITERAL | `"Nav rendered 'ELITE' despite DB tier='free' — current_user() or "` |
| `tests/test_smoke.py:392` | em | prose | P23,STRING-LITERAL | `"DB tier was silently overwritten during the request — a hook is "` |
| `tests/test_smoke.py:405` | em | prose | P23 | `user. This asserts the SILENCE — the badge should never fabricate a` |
| `tests/test_smoke.py:425` | em | prose | P23,STRING-LITERAL | `f"{path} rendered 'ELITE' badge despite DB tier='free' — "` |
| `tests/test_smoke.py:430` | em | prose | P23,STRING-LITERAL | `"After rendering all PAGE_ROUTES, DB tier was silently mutated — "` |
| `tests/test_squeeze_panel.py:103` | em | prose | STRING-LITERAL | `"""HOLD tier with SI >= 10 is NOT on the tile — confluence requires` |
| `tests/test_squeeze_panel.py:117` | em | prose | STRING-LITERAL | `"""BUY-rated ticker with SI < 10 is NOT on the tile — floor not cleared.` |
| `tests/test_stripe_checkout.py:2` | em | prose | P23 | `Tests for GET /upgrade — Stripe Checkout creation (Phase 2 Commit 5).` |
| `tests/test_stripe_checkout.py:10` | em | prose | P23 | `Catches — regressions in tier/interval/currency validation,` |
| `tests/test_stripe_checkout.py:14` | em | prose | P23 | `Ignores — Stripe-side checkout UX, success/cancel page rendering,` |
| `tests/test_stripe_checkout.py:57` | em | prose | P23 | `# IP across many tests in quick succession — disable rate limit` |
| `tests/test_stripe_checkout.py:98` | em | prose | P23 | `Ignores: the exact redirect target — only the 'reject' verdict` |
| `tests/test_stripe_checkout.py:148` | em | prose | P23 | `Catches: a regression that flips the default to GBP — most of` |
| `tests/test_stripe_checkout.py:166` | em | prose | P23 | `Catches: regression in the CF header read path — this is the` |
| `tests/test_stripe_checkout.py:168` | em | prose | P23 | `Ignores: other ISO countries — they all resolve to USD by policy.` |
| `tests/test_stripe_checkout.py:251` | em | prose | P23 | `Was verified live this session — webhook fails with "missing` |
| `tests/test_stripe_checkout.py:327` | em | prose | P23 | `interval — those are pinned by the setup script.` |
| `tests/test_stripe_webhook.py:15` | em | prose | P23 | `Catches — every change to the signature-verification, idempotency,` |
| `tests/test_stripe_webhook.py:18` | em | prose | P23 | `Ignores — Stripe-side delivery semantics (retry timing, signature` |
| `tests/test_stripe_webhook.py:56` | em | prose | P23 | `# The top-level "object": "event" is required — stripe.Webhook.construct_event` |
| `tests/test_stripe_webhook.py:220` | em | prose | P23 | `Catches: any future relaxation of construct_event() — e.g.` |
| `tests/test_stripe_webhook.py:225` | em | prose | P23 | `malformed payloads — only the 'reject' verdict matters.` |
| `tests/test_stripe_webhook.py:259` | em | prose | P23 | `SignatureVerificationError on the empty header — both are` |
| `tests/test_stripe_webhook.py:284` | em | prose | P23 | `Ignores: the exact tier_effective_until timestamp seconds — the` |
| `tests/test_stripe_webhook.py:345` | em | prose | P23 | `Ignores: the exact response body shape on duplicate — only the` |
| `tests/test_stripe_webhook.py:379` | em | prose | P23 | `# because timestamp differs — Stripe redelivers with the same` |
| `tests/test_stripe_webhook.py:393` | em | prose | P23 | `# Subscription.retrieve called exactly once — second delivery` |
| `tests/test_stripe_webhook.py:397` | em | prose | P23,STRING-LITERAL | `f"(called {call_count['n']} times — handler ran twice)"` |
| `tests/test_stripe_webhook.py:412` | em | prose | P23 | `user on cancellation — the documented "ride out the` |
| `tests/test_stripe_webhook.py:415` | em | prose | P23 | `actually expires — that is a separate concern.` |
| `tests/test_stripe_webhook.py:455` | em | prose | P23,STRING-LITERAL | `f"cancellation must NOT drop tier — locked decision. Got tier={after['tier']!r}"` |
| `tests/test_stripe_webhook.py:458` | em | prose | P23,STRING-LITERAL | `f"cancellation must NOT deactivate — locked decision. "` |
| `tests/test_stripe_webhook.py:472` | em | prose | P23,STRING-LITERAL | `"tier_after must equal tier_before on cancellation — tier deliberately unchanged"` |
| `tests/test_stripe_webhook.py:526` | em | prose | P23 | `Ignores: the exact error message format — only that it's` |
| `tests/test_stripe_webhook.py:571` | em | prose | P23,STRING-LITERAL | `wasn't set — the endpoint would silently accept unsigned` |
| `tests/test_stripe_webhook.py:575` | em | prose | P23 | `Ignores: the rest of the request path — no signature verification` |
| `tests/test_subscription_events_schema.py:8` | em | prose | P23 | `a double tier flip — the load-bearing reason this table exists.` |
| `tests/test_subscription_events_schema.py:88` | em | prose | P23 | `Ignores: column order, defaults, indexes — covered by` |
| `tests/test_subscription_events_schema.py:104` | em | prose | P23 | `Ignores: column order (cid) — future migrations may shift it.` |
| `tests/test_subscription_events_schema.py:112` | em | prose | P23,STRING-LITERAL | `"""stripe_event_id has UNIQUE + NOT NULL — the idempotency lock.` |
| `tests/test_subscription_events_schema.py:117` | em | prose | P23 | `- UNIQUE is the actual lock — duplicate INSERT raises` |
| `tests/test_subscription_events_schema.py:124` | em | prose | P23 | `(sqlite_autoindex_*) — implementation detail.` |
| `tests/test_subscription_events_schema.py:152` | em | prose | P23 | `on this default — initial insert omits status, transitions` |
| `tests/test_subscription_events_schema.py:154` | em | prose | P23,STRING-LITERAL | `Ignores: the schema's NOT NULL annotation enforcement order —` |
| `tests/test_subscription_events_schema.py:174` | em | prose | P23 | `tier_before, tier_after, raw_payload) — those are` |
| `tests/test_subscription_events_schema.py:187` | em | prose | P23 | `slowly — and slow webhook lookups compound into` |
| `tests/test_subscription_events_schema.py:190` | em | prose | P23 | `that SQLite auto-creates for the UNIQUE constraint —` |
| `tests/test_subscription_events_schema.py:207` | em | prose | P23 | `Ignores: the schema in absolute terms — only the second-run` |
| `tests/test_themes.py:23` | em | prose | STRING-LITERAL | `"""Theme IDs must be lowercase snake_case (P14 — IDs are stable once shipped)."""` |
| `tests/test_themes.py:45` | em | prose | STRING-LITERAL | `f"legally_clean count={count} — suspiciously low, "` |
| `tests/test_user_schema.py:5` | em | prose | P23 | `nullable/default contract — the Stripe webhook is about to write to` |
| `tests/test_user_schema.py:46` | em | prose | P23 | `the users table. Source: PRAGMA table_info — returns rows of` |
| `tests/test_user_schema.py:72` | em | prose | P23 | `Ignores: column order — only presence is asserted (cid is not` |
| `tests/test_user_schema.py:84` | em | prose | P23 | `either break create_user() (which omits them — they'd need a value` |
| `tests/test_user_schema.py:91` | em | prose | P23 | `Ignores: the cid (column index) — column-order shifts are fine.` |
| `tests/test_user_schema.py:112` | em | prose | P23 | `Ignores: USER_TIERS dict shape in config/tiers.py — that's tested` |
| `tests/test_user_schema.py:118` | em | prose | P23 | `# PRAGMA table_info returns the default as the raw SQL literal —` |
| `tests/test_user_schema.py:130` | em | prose | P23 | `on timeout — a slow lookup compounds into duplicate-write risk` |
| `tests/test_user_schema.py:135` | em | prose | P23 | `on username/email (sqlite_autoindex_users_*) — they're` |
| `tests/test_user_schema.py:155` | em | prose | P23 | `Ignores: the schema in absolute terms — this test only asserts the` |
| `tests/test_user_tiers.py:5` | em | prose | P23 | `These tests exercise pure functions — no template pattern matching involved.` |
| `tests/test_user_tiers.py:37` | em | prose | P23 | `Catches: cap drift on any tier — free=0 (no access), pro=5, elite=unlimited.` |
| `tests/test_user_tiers.py:57` | em | prose | P23 | `P15 silence assertion: 'free' is the unpaid floor — no gateable access.` |
| `tests/test_user_tiers.py:90` | em | prose | P23,STRING-LITERAL | `floor via get_tier()'s default branch — same as any other unknown key.` |
| `tests/test_volume_component.py:238` | em | prose | STRING-LITERAL | `"""score_volume() is a thin wrapper — result must match _compute_volume()[0]."""` |
| `web/templates/_locked_teaser_css.html:4` | em | prose | STRING-LITERAL | `so CSS placed in _nav.html doesn't reach it — hence this dedicated` |
| `web/templates/backtest.html:89` | em | prose | STRING-LITERAL | `<div class="note" title="SignalIntel targets a 12-month price horizon matching industry standard (Bloomberg...` |
| `web/templates/backtest.html:160` | em | prose | STRING-LITERAL | `<tbody>${tradesHtml \|\| (data.locked ? '<tr><td colspan="5"><div class="lt-inline"><span class="lt-inline-...` |
| `web/templates/backtest.html:190` | em | prose | STRING-LITERAL | `<div style="font-size:10px;color:${Math.abs(sc.spread\|\|0)>=5?'var(--accent2)':'var(--muted)'};margin-top:...` |
| `web/templates/contact.html:50` | en | numeric-range | STRING-LITERAL | `<p>✅ Your message has been sent. We'll get back to you within 1–2 business days.</p>` |
| `web/templates/dashboard.html:573` | em | placeholder | STRING-LITERAL | `<div class="spot-company">{{ spotlight.company or '—' }}{% if spotlight.sector %} · {{ spotlight.sector }}{...` |
| `web/templates/dashboard.html:695` | em | placeholder | STRING-LITERAL | `<span class="sec-rank">{{ s.rank_7d or '—' }}</span>` |
| `web/templates/dashboard.html:765` | em | placeholder | STRING-LITERAL | `<div class="news-head">{{ n.headline or '—' }}</div>` |
| `web/templates/dividends.html:127` | em | prose | STRING-LITERAL | `<th data-tip="Dividend payout ratio — percentage of earnings paid as dividends. Above 80% may be unsustaina...` |
| `web/templates/dividends.html:128` | em | prose | STRING-LITERAL | `<th data-tip="Ex-dividend date — you must own shares BEFORE this date to receive the next dividend payment"...` |
| `web/templates/earnings.html:119` | em | prose | STRING-LITERAL | `<th data-tip="Price to Earnings ratio — current share price divided by annual earnings per share">P/E</th>` |
| `web/templates/index.html:287` | em | prose | STRING-LITERAL | `<div class="section-title">Today's Top 10 Signals —</div>` |
| `web/templates/index.html:809` | em | prose | STRING-LITERAL | `document.getElementById('sector-drilldown-title').textContent = sector + ' — Signals';` |
| `web/templates/markets.html:134` | em | placeholder | STRING-LITERAL | `if (v == null) return '—';` |
| `web/templates/markets.html:210` | em | placeholder | STRING-LITERAL | `priceRow.innerHTML = '<span class="card-price-val" style="color:var(--muted)">—</span>';` |
| `web/templates/penny.html:243` | em | placeholder | STRING-LITERAL | `if (v == null) return '<span class="neu">—</span>';` |
| `web/templates/penny_screener.html:186` | em | prose | STRING-LITERAL | `route, so the data wouldn't leak even if JS fired — but the locked` |
| `web/templates/penny_screener.html:571` | em | placeholder | STRING-LITERAL | `if (v == null \|\| v === '') return '<span class="neu">—</span>';` |
| `web/templates/penny_screener.html:573` | em | placeholder | STRING-LITERAL | `if (isNaN(n)) return '<span class="neu">—</span>';` |
| `web/templates/penny_screener.html:587` | em | placeholder | STRING-LITERAL | `if (v == null) return '<span class="neu">—</span>';` |
| `web/templates/penny_screener.html:596` | em | placeholder | STRING-LITERAL | `if (v == null) return '<span class="neu">—</span>';` |
| `web/templates/penny_screener.html:606` | em | placeholder | STRING-LITERAL | `if (v == null) return '<span class="neu">—</span>';` |
| `web/templates/penny_screener.html:614` | em | placeholder | STRING-LITERAL | `if (v == null) return '<span class="neu">—</span>';` |
| `web/templates/penny_screener.html:616` | em | placeholder | STRING-LITERAL | `if (isNaN(n)) return '<span class="neu">—</span>';` |
| `web/templates/penny_screener.html:623` | em | placeholder | STRING-LITERAL | `if (v == null) return '<span class="neu">—</span>';` |
| `web/templates/penny_screener.html:629` | em | placeholder | STRING-LITERAL | `if (v == null) return '<span class="neu">—</span>';` |
| `web/templates/penny_screener.html:646` | em | placeholder | STRING-LITERAL | `<td class="tc-sector">${r.exchange \|\| '—'}</td>` |
| `web/templates/penny_screener.html:647` | em | placeholder | STRING-LITERAL | `<td class="tc-company">${r.company \|\| '—'}</td>` |
| `web/templates/penny_screener.html:648` | em | placeholder | STRING-LITERAL | `<td class="tc-sector">${r.sector \|\| '—'}</td>` |
| `web/templates/ratings.html:82` | em | prose | STRING-LITERAL | `<p class="subtitle">SignalIntel's 7-tier signal classification — definitions, scoring logic, and current di...` |
| `web/templates/screener.html:223` | em | prose | STRING-LITERAL | `data-tip="Insider score ≥70 with Strong Signal or better. Directors and officers are net buyers — follow th...` |
| `web/templates/screener.html:245` | en | numeric-range | STRING-LITERAL | `<th data-tip="Composite score 0–100 combining Momentum, Quality, Insider, Reversion and Legal signals" oncl...` |
| `web/templates/ticker.html:393` | em | placeholder | STRING-LITERAL | `getValue(s, lr) { const v = s.momentum_score; const w = v == null; return { num: w?0:v, display: w?'—':v.to...` |
| `web/templates/ticker.html:400` | em | placeholder | STRING-LITERAL | `getValue(s, lr) { const v = s.quality_score; const w = v == null; return { num: w?0:v, display: w?'—':v.toF...` |
| `web/templates/ticker.html:407` | em | placeholder | STRING-LITERAL | `getValue(s, lr) { const v = s.insider_score; const w = v == null; return { num: w?0:v, display: w?'—':v.toF...` |
| `web/templates/ticker.html:414` | em | placeholder | STRING-LITERAL | `getValue(s, lr) { const v = s.reversion_score; const w = v == null; return { num: w?0:v, display: w?'—':v.t...` |
| `web/templates/ticker.html:421` | em | placeholder | STRING-LITERAL | `getValue(s, lr) { const v = s.volume_score; const w = v == null; return { num: w?0:v, display: w?'—':v.toFi...` |
| `web/templates/ticker.html:570` | em | placeholder | STRING-LITERAL | `<span class="badge">${tm.exchange \|\| '—'}</span>` |
| `web/templates/ticker.html:760` | em | prose | STRING-LITERAL | `<div class="stat-row" data-tip="P/E Ratio — price divided by annual EPS. Lower = cheaper relative to earnin...` |
| `web/templates/ticker.html:773` | em | prose | STRING-LITERAL | `<div class="stat-row" data-tip="Relative Strength Index — below 30 = oversold (buy signal), above 70 = over...` |
| `web/templates/ticker.html:798` | em | prose | STRING-LITERAL | `<div class="stat-row" data-tip="Days to Cover — how many days of average volume needed to cover all short p...` |
| `web/templates/ticker.html:887` | em | placeholder | STRING-LITERAL | `gauge.textContent = '—';` |
| `web/templates/ticker.html:889` | em | prose | STRING-LITERAL | `alabel.textContent = 'Fund/ETF — no analyst consensus';` |
| `web/templates/ticker.html:1030` | em | placeholder | STRING-LITERAL | `el.textContent = r.wasNull ? '—' : fmtS(r.num);` |
| `web/templates/watchlist.html:118` | em | prose | STRING-LITERAL | `{{ wl.name }}{% if wl.is_default %} <span class="wl-default-lock" data-tip="Default watchlist — cannot be d...` |
| `web/templates/watchlist.html:157` | en | numeric-range | STRING-LITERAL | `<th data-tip="Composite score 0–100 combining Momentum, Quality, Insider, Reversion and Legal signals">Scor...` |
| `web/templates/watchlist.html:159` | em | prose | STRING-LITERAL | `<th data-tip="Momentum score — measures price trend strength and direction">Mom</th>` |
| `web/templates/watchlist.html:160` | em | prose | STRING-LITERAL | `<th data-tip="Quality score — fundamentals including P/E, EPS growth and return on equity">Qual</th>` |
| `web/templates/watchlist.html:161` | em | prose | STRING-LITERAL | `<th data-tip="Insider score — based on recent insider buying and selling activity">Insider</th>` |

## List 2: Protected-doc occurrence counts (per-file sign-off required)

Counted only, NOT enumerated. Phase 2 must NOT sweep these without explicit per-file authorisation.

| file | em-dash (U+2014) | en-dash (U+2013) |
|---|---:|---:|
| `CLAUDE.md` | 29 | 2 |
| `HANDOFF.md` | 70 | 1 |
| `PROJECT_CONTEXT.md` | 131 | 1 |
| **Subtotal** | **230** | **4** |

## List 3: Stale artefacts (DELETE, do not sweep)

Phase 2 will `git rm` these in a dedicated commit instead of sweeping their content.

- `fix_scraper_final.py` (exists)
- `logs/backfill_exchange_2026-05-07.log` (exists)
- `rewrite_legal_scraper.py` (exists)
- `scrapers/legal_risk_scraper.py.bak` (exists)

## Bucket A: User-facing templates

Files in scope: **26** | em-dash: **155** | en-dash: **18**

### `web/templates/_locked_teaser_css.html`
em-dash: 2 | en-dash: 0 | total: 2

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 4 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `so CSS placed in _nav.html doesn't reach it — hence this dedicated` |
| 33 | em | prose | comma (default), period if clause-break, colon for label |  | `/* Inline variant — compact, used in table cells / small surfaces` |

### `web/templates/_nav.html`
em-dash: 1 | en-dash: 0 | total: 1

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 48 | em | prose | comma (default), period if clause-break, colon for label |  | `/* Toast — must live outside header to avoid backdrop-filter fixed-positioning bug */` |

### `web/templates/_watchlist_picker.html`
em-dash: 1 | en-dash: 0 | total: 1

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 1 | em | prose | comma (default), period if clause-break, colon for label |  | `<!-- Shared watchlist picker — included once via _nav.html, used on every page -->` |

### `web/templates/about.html`
em-dash: 9 | en-dash: 0 | total: 9

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 6 | em | title-separator | " - " (hyphen with spaces) |  | `<title>About — The Signal Vault</title>` |
| 50 | em | prose | comma (default), period if clause-break, colon for label |  | `<div class="diff-item"><span class="diff-check">✅</span><span class="diff-text"><strong>Verified ...` |
| 51 | em | prose | comma (default), period if clause-break, colon for label |  | `<div class="diff-item"><span class="diff-check">✅</span><span class="diff-text"><strong>SEC EDGAR...` |
| 52 | em | prose | comma (default), period if clause-break, colon for label |  | `<div class="diff-item"><span class="diff-check">✅</span><span class="diff-text"><strong>Proprieta...` |
| 53 | em | prose | comma (default), period if clause-break, colon for label |  | `<div class="diff-item"><span class="diff-check">✅</span><span class="diff-text"><strong>Insider a...` |
| 54 | em | prose | comma (default), period if clause-break, colon for label |  | `<div class="diff-item"><span class="diff-check">✅</span><span class="diff-text"><strong>Multi-mar...` |
| 55 | em | prose | comma (default), period if clause-break, colon for label |  | `<div class="diff-item"><span class="diff-check">✅</span><span class="diff-text"><strong>Real-time...` |
| 63 | em | prose | comma (default), period if clause-break, colon for label |  | `<p>SignalIntel is the core product of The Signal Vault. It aggregates data from multiple sources ...` |
| 63 | em | prose | comma (default), period if clause-break, colon for label |  | `<p>SignalIntel is the core product of The Signal Vault. It aggregates data from multiple sources ...` |

### `web/templates/backtest.html`
em-dash: 5 | en-dash: 1 | total: 6

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 6 | en | title-separator | " - " (hyphen with spaces) |  | `<title>SignalIntel – Backtesting</title>` |
| 70 | em | prose | comma (default), period if clause-break, colon for label |  | `<p class="subtitle">Historical accuracy of each signal strength tier — measured over the <strong>...` |
| 89 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `<div class="note" title="SignalIntel targets a 12-month price horizon matching industry standard ...` |
| 121 | em | prose | comma (default), period if clause-break, colon for label |  | `grid.innerHTML = \`${dataMsg}<div style="color:var(--muted);font-family:var(--mono);font-size:13p...` |
| 160 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `<tbody>${tradesHtml \|\| (data.locked ? '<tr><td colspan="5"><div class="lt-inline"><span class="...` |
| 190 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `<div style="font-size:10px;color:${Math.abs(sc.spread\|\|0)>=5?'var(--accent2)':'var(--muted)'};m...` |

### `web/templates/contact.html`
em-dash: 1 | en-dash: 2 | total: 3

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 6 | em | title-separator | " - " (hyphen with spaces) |  | `<title>Contact — The Signal Vault</title>` |
| 45 | en | numeric-range | 'to' (spaced) or '-' (compact) |  | `<p style="color:var(--muted);font-size:12px;">We aim to respond to all enquiries within 1–2 busin...` |
| 50 | en | numeric-range | 'to' (spaced) or '-' (compact) | STRING-LITERAL | `<p>✅ Your message has been sent. We'll get back to you within 1–2 business days.</p>` |

### `web/templates/dashboard.html`
em-dash: 43 | en-dash: 0 | total: 43

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 1 | em | prose | comma (default), period if clause-break, colon for label |  | `{# Phase 2A — 6 above-fold panels (1-6). Phase 2B adds Elite Spotlight + panels 7-13. #}` |
| 8 | em | title-separator | " - " (hyphen with spaces) |  | `<title>Dashboard — SignalIntel</title>` |
| 285 | em | prose | comma (default), period if clause-break, colon for label |  | `/* Locked teaser (non-Elite) — full overlay, blurred placeholder */` |
| 416 | em | prose | comma (default), period if clause-break, colon for label |  | `{# ─── ABOVE THE FOLD — 3×2 ────────────────────────────────────── #}` |
| 419 | em | prose | comma (default), period if clause-break, colon for label |  | `{# PANEL 1 — DAILY SUMMARY #}` |
| 437 | em | prose | comma (default), period if clause-break, colon for label |  | `<span class="stat-value">{% if summary.top_mover %}{{ summary.top_mover.ticker }} {{ '%+.1f'\|for...` |
| 445 | em | prose | comma (default), period if clause-break, colon for label |  | `<span class="stat-value">{% if summary.vix_val is not none %}{{ '%.1f'\|format(summary.vix_val) }...` |
| 452 | em | prose | comma (default), period if clause-break, colon for label |  | `{# PANEL 2 — TOP 5 STRONG #}` |
| 474 | em | prose | comma (default), period if clause-break, colon for label |  | `{# PANEL 3 — TOP 5 BEARISH #}` |
| 496 | em | prose | comma (default), period if clause-break, colon for label |  | `{# PANEL 4 — MARKET STATE #}` |
| 507 | em | prose | comma (default), period if clause-break, colon for label |  | `<div class="mkt-level">{% if t.level is not none %}{{ '{:,.0f}'.format(t.level) if t.level >= 100...` |
| 509 | em | prose | comma (default), period if clause-break, colon for label |  | `{% if t.chg_pct is not none %}{{ '%+.2f'\|format(t.chg_pct) }}%{% else %}—{% endif %}` |
| 518 | em | prose | comma (default), period if clause-break, colon for label |  | `{# PANEL 5 — WATCHLIST PREVIEW #}` |
| 529 | em | placeholder | '-' (single hyphen) |  | `{% if w.rating %}<span class="tier-badge {{ w.tier_class }}">{{ w.tier_short }}</span>{% else %}<...` |
| 530 | em | prose | comma (default), period if clause-break, colon for label |  | `<span class="score">{% if w.composite_score is not none %}{{ '%.0f'\|format(w.composite_score) }}...` |
| 532 | em | prose | comma (default), period if clause-break, colon for label |  | `{% if w.change_pct is not none %}{{ '%+.1f'\|format(w.change_pct) }}%{% else %}—{% endif %}` |
| 543 | em | prose | comma (default), period if clause-break, colon for label |  | `{# PANEL 6 — DISCOVERY THEMES #}` |
| 565 | em | prose | comma (default), period if clause-break, colon for label |  | `{# ─── PANEL 7 — PENNY STOCK SPOTLIGHT (Elite-gated, full-width) ───── #}` |
| 567 | em | prose | comma (default), period if clause-break, colon for label |  | `{# Elite-tier branch — real pick data flows to the client #}` |
| 573 | em | placeholder | '-' (single hyphen) | STRING-LITERAL | `<div class="spot-company">{{ spotlight.company or '—' }}{% if spotlight.sector %} · {{ spotlight....` |
| 575 | em | prose | comma (default), period if clause-break, colon for label |  | `{% if spotlight.price is not none %}${{ '%.2f'\|format(spotlight.price) }}{% else %}—{% endif %}` |
| 586 | em | prose | comma (default), period if clause-break, colon for label |  | `<div class="comp-bar-label"><span>{{ lbl }}</span><span class="v">{% if v is not none %}{{ '%.0f'...` |
| 603 | em | prose | comma (default), period if clause-break, colon for label |  | `{# Non-elite branch — migrated to shared locked_teaser macro (4d).` |
| 613 | em | prose | comma (default), period if clause-break, colon for label |  | `<div class="spot-ticker">— — — —</div>` |
| 613 | em | prose | comma (default), period if clause-break, colon for label |  | `<div class="spot-ticker">— — — —</div>` |
| 613 | em | prose | comma (default), period if clause-break, colon for label |  | `<div class="spot-ticker">— — — —</div>` |
| 613 | em | prose | comma (default), period if clause-break, colon for label |  | `<div class="spot-ticker">— — — —</div>` |
| 615 | em | prose | comma (default), period if clause-break, colon for label |  | `<div class="spot-price">$—.—— <span class="chg up">+—.—%</span></div>` |
| 615 | em | prose | comma (default), period if clause-break, colon for label |  | `<div class="spot-price">$—.—— <span class="chg up">+—.—%</span></div>` |
| 615 | em | prose | comma (default), period if clause-break, colon for label |  | `<div class="spot-price">$—.—— <span class="chg up">+—.—%</span></div>` |
| 615 | em | prose | comma (default), period if clause-break, colon for label |  | `<div class="spot-price">$—.—— <span class="chg up">+—.—%</span></div>` |
| 615 | em | prose | comma (default), period if clause-break, colon for label |  | `<div class="spot-price">$—.—— <span class="chg up">+—.—%</span></div>` |
| 621 | em | placeholder | '-' (single hyphen) |  | `<div class="comp-bar-label"><span>{{ lbl }}</span><span class="v">—</span></div>` |
| 638 | em | prose | comma (default), period if clause-break, colon for label |  | `{# ─── BELOW THE FOLD — 3×2 ──────────────────────────────────────── #}` |
| 641 | em | prose | comma (default), period if clause-break, colon for label |  | `{# PANEL 8 — EARNINGS NEXT 7 DAYS #}` |
| 662 | em | prose | comma (default), period if clause-break, colon for label |  | `{# PANEL 9 — DIVIDENDS THIS WEEK #}` |
| 683 | em | prose | comma (default), period if clause-break, colon for label |  | `{# PANEL 10 — SECTOR PERFORMANCE #}` |
| 695 | em | placeholder | '-' (single hyphen) | STRING-LITERAL | `<span class="sec-rank">{{ s.rank_7d or '—' }}</span>` |
| 707 | em | prose | comma (default), period if clause-break, colon for label |  | `{# PANEL 11 — RECENT RATING CHANGES #}` |
| 729 | em | prose | comma (default), period if clause-break, colon for label |  | `{# PANEL 12 — INSIDER ACTIVITY #}` |
| 751 | em | prose | comma (default), period if clause-break, colon for label |  | `{# PANEL 13 — NEWS HEADLINES #}` |
| 765 | em | placeholder | '-' (single hyphen) | STRING-LITERAL | `<div class="news-head">{{ n.headline or '—' }}</div>` |
| 775 | em | prose | comma (default), period if clause-break, colon for label |  | `{# PANEL 14 — SHORT-SQUEEZE SETUPS (confluence: heavy SI + Very Strong/Strong) #}` |

### `web/templates/disclaimer.html`
em-dash: 2 | en-dash: 0 | total: 2

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 6 | em | title-separator | " - " (hyphen with spaces) |  | `<title>Risk Disclaimer — The Signal Vault</title>` |
| 67 | em | prose | comma (default), period if clause-break, colon for label |  | `<li>Low liquidity — difficulty buying or selling at desired prices</li>` |

### `web/templates/dividends.html`
em-dash: 3 | en-dash: 0 | total: 3

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 6 | em | title-separator | " - " (hyphen with spaces) |  | `<title>SignalIntel — Dividend Centre</title>` |
| 127 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `<th data-tip="Dividend payout ratio — percentage of earnings paid as dividends. Above 80% may be ...` |
| 128 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `<th data-tip="Ex-dividend date — you must own shares BEFORE this date to receive the next dividen...` |

### `web/templates/earnings.html`
em-dash: 2 | en-dash: 0 | total: 2

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 6 | em | title-separator | " - " (hyphen with spaces) |  | `<title>SignalIntel — Earnings Calendar</title>` |
| 119 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `<th data-tip="Price to Earnings ratio — current share price divided by annual earnings per share"...` |

### `web/templates/events.html`
em-dash: 3 | en-dash: 0 | total: 3

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 6 | em | title-separator | " - " (hyphen with spaces) |  | `<title>SignalIntel — Economic Events</title>` |
| 195 | em | prose | comma (default), period if clause-break, colon for label |  | `if (date === today)    label = \`Today — ${date}\`;` |
| 196 | em | prose | comma (default), period if clause-break, colon for label |  | `if (date === tomorrow) label = \`Tomorrow — ${date}\`;` |

### `web/templates/index.html`
em-dash: 6 | en-dash: 1 | total: 7

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 160 | em | prose | comma (default), period if clause-break, colon for label |  | `<!-- Scrolling Ticker Tape — sticky immediately below nav -->` |
| 274 | em | prose | comma (default), period if clause-break, colon for label |  | `<div class="theme-desc">High insider score — directors and officers are buying</div>` |
| 287 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `<div class="section-title">Today's Top 10 Signals —</div>` |
| 363 | em | prose | comma (default), period if clause-break, colon for label |  | `<span style="font-size:9px;font-weight:400;color:var(--muted)"> — score 0-100 used as composite m...` |
| 418 | em | prose | comma (default), period if clause-break, colon for label |  | `// Watchlist set — seeded from server on page load, updated in-place by WlPicker` |
| 727 | en | prose | comma (default), period if clause-break, colon for label |  | `<span>Showing ${start+1}–${Math.min(end,total)} of ${total.toLocaleString()} results</span>` |
| 809 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `document.getElementById('sector-drilldown-title').textContent = sector + ' — Signals';` |

### `web/templates/industry.html`
em-dash: 1 | en-dash: 0 | total: 1

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 6 | em | title-separator | " - " (hyphen with spaces) |  | `<title>SignalIntel — {{ industry }}</title>` |

### `web/templates/login.html`
em-dash: 1 | en-dash: 0 | total: 1

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 6 | em | title-separator | " - " (hyphen with spaces) |  | `<title>SignalIntel — Login</title>` |

### `web/templates/market_chart.html`
em-dash: 1 | en-dash: 0 | total: 1

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 6 | em | title-separator | " - " (hyphen with spaces) |  | `<title>{{ label }} — SignalIntel Markets</title>` |

### `web/templates/markets.html`
em-dash: 3 | en-dash: 0 | total: 3

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 6 | em | title-separator | " - " (hyphen with spaces) |  | `<title>SignalIntel — Markets</title>` |
| 134 | em | placeholder | '-' (single hyphen) | STRING-LITERAL | `if (v == null) return '—';` |
| 210 | em | placeholder | '-' (single hyphen) | STRING-LITERAL | `priceRow.innerHTML = '<span class="card-price-val" style="color:var(--muted)">—</span>';` |

### `web/templates/penny.html`
em-dash: 4 | en-dash: 1 | total: 5

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 7 | em | title-separator | " - " (hyphen with spaces) |  | `<title>SignalIntel — Penny &amp; Small Cap</title>` |
| 138 | en | numeric-range | 'to' (spaced) or '-' (compact) |  | `<strong>High Risk Asset Class.</strong> Penny and small-cap stocks are significantly more volatil...` |
| 138 | em | prose | comma (default), period if clause-break, colon for label |  | `<strong>High Risk Asset Class.</strong> Penny and small-cap stocks are significantly more volatil...` |
| 243 | em | placeholder | '-' (single hyphen) | STRING-LITERAL | `if (v == null) return '<span class="neu">—</span>';` |
| 280 | em | prose | comma (default), period if clause-break, colon for label |  | `<div class="sotd-label">★ Penny Stock of the Day — ${d.date}</div>` |

### `web/templates/penny_screener.html`
em-dash: 14 | en-dash: 3 | total: 17

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 7 | em | title-separator | " - " (hyphen with spaces) |  | `<title>SignalIntel — Penny Screener</title>` |
| 171 | en | numeric-range | 'to' (spaced) or '-' (compact) |  | `<strong>High Risk.</strong> Penny stocks are highly volatile and speculative. Prices can move 50–...` |
| 186 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `route, so the data wouldn't leak even if JS fired — but the locked` |
| 198 | en | numeric-range | 'to' (spaced) or '-' (compact) |  | `<button class="tier-tab" data-tier="1to5" onclick="setTier(this,'1to5')">$1 – $5</button>` |
| 252 | en | numeric-range | '-' (literal range separator inside HTML) |  | `<span class="range-sep">–</span>` |
| 571 | em | placeholder | '-' (single hyphen) | STRING-LITERAL | `if (v == null \|\| v === '') return '<span class="neu">—</span>';` |
| 573 | em | placeholder | '-' (single hyphen) | STRING-LITERAL | `if (isNaN(n)) return '<span class="neu">—</span>';` |
| 587 | em | placeholder | '-' (single hyphen) | STRING-LITERAL | `if (v == null) return '<span class="neu">—</span>';` |
| 596 | em | placeholder | '-' (single hyphen) | STRING-LITERAL | `if (v == null) return '<span class="neu">—</span>';` |
| 606 | em | placeholder | '-' (single hyphen) | STRING-LITERAL | `if (v == null) return '<span class="neu">—</span>';` |
| 614 | em | placeholder | '-' (single hyphen) | STRING-LITERAL | `if (v == null) return '<span class="neu">—</span>';` |
| 616 | em | placeholder | '-' (single hyphen) | STRING-LITERAL | `if (isNaN(n)) return '<span class="neu">—</span>';` |
| 623 | em | placeholder | '-' (single hyphen) | STRING-LITERAL | `if (v == null) return '<span class="neu">—</span>';` |
| 629 | em | placeholder | '-' (single hyphen) | STRING-LITERAL | `if (v == null) return '<span class="neu">—</span>';` |
| 646 | em | placeholder | '-' (single hyphen) | STRING-LITERAL | `<td class="tc-sector">${r.exchange \|\| '—'}</td>` |
| 647 | em | placeholder | '-' (single hyphen) | STRING-LITERAL | `<td class="tc-company">${r.company \|\| '—'}</td>` |
| 648 | em | placeholder | '-' (single hyphen) | STRING-LITERAL | `<td class="tc-sector">${r.sector \|\| '—'}</td>` |

### `web/templates/privacy.html`
em-dash: 2 | en-dash: 0 | total: 2

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 6 | em | title-separator | " - " (hyphen with spaces) |  | `<title>Privacy Policy — The Signal Vault</title>` |
| 78 | em | prose | comma (default), period if clause-break, colon for label |  | `<p>We use session cookies for authentication only. We do not use tracking cookies or third-party ...` |

### `web/templates/ratings.html`
em-dash: 17 | en-dash: 5 | total: 22

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 6 | en | title-separator | " - " (hyphen with spaces) |  | `<title>SignalIntel – Signal Strength Tiers</title>` |
| 82 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `<p class="subtitle">SignalIntel's 7-tier signal classification — definitions, scoring logic, and ...` |
| 96 | em | prose | comma (default), period if clause-break, colon for label |  | `<span class="tier-action action-strong-buy">Highest conviction — all factors aligned</span>` |
| 97 | em | prose | comma (default), period if clause-break, colon for label |  | `<div class="tier-condition">Composite ≥ 72 AND Insider Score ≥ 65. Insider activity is required —...` |
| 107 | em | prose | comma (default), period if clause-break, colon for label |  | `<span class="tier-action action-buy">Strong signal — momentum and quality aligned</span>` |
| 118 | em | prose | comma (default), period if clause-break, colon for label |  | `<span class="tier-action action-strong-hold">Stable — no clear directional signal</span>` |
| 119 | en | numeric-range | 'to' (spaced) or '-' (compact) |  | `<div class="tier-condition">Composite 45–62 (default tier — no strong signal in either direction)...` |
| 119 | em | prose | comma (default), period if clause-break, colon for label |  | `<div class="tier-condition">Composite 45–62 (default tier — no strong signal in either direction)...` |
| 121 | en | numeric-range | 'to' (spaced) or '-' (compact) |  | `<div class="tier-score">Composite 45–62</div>` |
| 128 | em | prose | comma (default), period if clause-break, colon for label |  | `<div class="tier-desc">Neutral signal triggered by mean-reversion opportunity — the stock has dev...` |
| 129 | em | prose | comma (default), period if clause-break, colon for label |  | `<span class="tier-action action-hold">Neutral — possible mean-reversion candidate</span>` |
| 139 | em | prose | comma (default), period if clause-break, colon for label |  | `<div class="tier-desc">Weakening signal — momentum fading, fundamentals softening, insider confid...` |
| 140 | em | prose | comma (default), period if clause-break, colon for label |  | `<span class="tier-action action-weak-hold">Soft — signal strength declining</span>` |
| 150 | em | prose | comma (default), period if clause-break, colon for label |  | `<div class="tier-desc">Bearish signal. Multiple negative signals across momentum, quality, and in...` |
| 151 | em | prose | comma (default), period if clause-break, colon for label |  | `<span class="tier-action action-sell">Bearish — multiple negative factors</span>` |
| 161 | em | prose | comma (default), period if clause-break, colon for label |  | `<div class="tier-desc">Strongest bearish signal. Severe deterioration across all factors — legal ...` |
| 162 | em | prose | comma (default), period if clause-break, colon for label |  | `<span class="tier-action action-strong-sell">Strongly bearish — all factors negative</span>` |
| 170 | en | numeric-range | 'to' (spaced) or '-' (compact) |  | `<div class="section-title">Score Components (0–100)</div>` |
| 178 | em | prose | comma (default), period if clause-break, colon for label |  | `<div class="score-desc">Fundamental strength — P/E ratio, profit margins, ROE, EPS growth, and de...` |
| 182 | em | prose | comma (default), period if clause-break, colon for label |  | `<div class="score-desc">Recent insider buying activity. 100 = significant cluster buying by compa...` |
| 212 | en | prose | comma (default), period if clause-break, colon for label |  | `Range: {{ row.min_score }} – {{ row.max_score }}` |
| 222 | em | prose | comma (default), period if clause-break, colon for label |  | `<p class="no-data">No signal data yet — run the signal generator first.</p>` |

### `web/templates/register.html`
em-dash: 1 | en-dash: 0 | total: 1

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 6 | em | title-separator | " - " (hyphen with spaces) |  | `<title>SignalIntel — Register</title>` |

### `web/templates/screener.html`
em-dash: 5 | en-dash: 4 | total: 9

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 6 | em | title-separator | " - " (hyphen with spaces) |  | `<title>SignalIntel — Screener</title>` |
| 164 | en | numeric-range | '-' (literal range separator inside HTML) |  | `<span class="range-sep">–</span>` |
| 184 | en | numeric-range | '-' (literal range separator inside HTML) |  | `<span class="range-sep">–</span>` |
| 193 | en | numeric-range | '-' (literal range separator inside HTML) |  | `<span class="range-sep">–</span>` |
| 223 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `data-tip="Insider score ≥70 with Strong Signal or better. Directors and officers are net buyers —...` |
| 245 | en | numeric-range | 'to' (spaced) or '-' (compact) | STRING-LITERAL | `<th data-tip="Composite score 0–100 combining Momentum, Quality, Insider, Reversion and Legal sig...` |
| 523 | em | prose | comma (default), period if clause-break, colon for label |  | `// Canonical theme definitions — must match config/themes.py` |
| 603 | em | prose | comma (default), period if clause-break, colon for label |  | `// Legacy preset alias — redirects old ?preset= params to the matching theme` |
| 676 | em | prose | comma (default), period if clause-break, colon for label |  | `// Preset button tooltips — pinned below the button` |

### `web/templates/terms.html`
em-dash: 1 | en-dash: 0 | total: 1

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 6 | em | title-separator | " - " (hyphen with spaces) |  | `<title>Terms of Service — The Signal Vault</title>` |

### `web/templates/ticker.html`
em-dash: 20 | en-dash: 0 | total: 20

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 6 | em | title-separator | " - " (hyphen with spaces) |  | `<title>SignalIntel — {{ ticker }}</title>` |
| 393 | em | placeholder | '-' (single hyphen) | STRING-LITERAL | `getValue(s, lr) { const v = s.momentum_score; const w = v == null; return { num: w?0:v, display: ...` |
| 400 | em | placeholder | '-' (single hyphen) | STRING-LITERAL | `getValue(s, lr) { const v = s.quality_score; const w = v == null; return { num: w?0:v, display: w...` |
| 407 | em | placeholder | '-' (single hyphen) | STRING-LITERAL | `getValue(s, lr) { const v = s.insider_score; const w = v == null; return { num: w?0:v, display: w...` |
| 414 | em | placeholder | '-' (single hyphen) | STRING-LITERAL | `getValue(s, lr) { const v = s.reversion_score; const w = v == null; return { num: w?0:v, display:...` |
| 421 | em | placeholder | '-' (single hyphen) | STRING-LITERAL | `getValue(s, lr) { const v = s.volume_score; const w = v == null; return { num: w?0:v, display: w?...` |
| 570 | em | placeholder | '-' (single hyphen) | STRING-LITERAL | `<span class="badge">${tm.exchange \|\| '—'}</span>` |
| 586 | em | prose | comma (default), period if clause-break, colon for label |  | `<!-- Locked teaser (4d) — replaces the signal-banner when API returns data.locked=true (penny + n...` |
| 587 | em | prose | comma (default), period if clause-break, colon for label |  | `${data.locked ? \`<div class="signal-banner" style="justify-content:center;padding:24px"><div cla...` |
| 739 | em | prose | comma (default), period if clause-break, colon for label |  | `<div class="chart-title">Price Chart — ${TICKER}</div>` |
| 760 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `<div class="stat-row" data-tip="P/E Ratio — price divided by annual EPS. Lower = cheaper relative...` |
| 769 | em | prose | comma (default), period if clause-break, colon for label |  | `<!-- Technicals + 52W + Short + Target — 2×2 grid -->` |
| 773 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `<div class="stat-row" data-tip="Relative Strength Index — below 30 = oversold (buy signal), above...` |
| 798 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `<div class="stat-row" data-tip="Days to Cover — how many days of average volume needed to cover a...` |
| 845 | em | prose | comma (default), period if clause-break, colon for label |  | `// Detect fund/ETF/REIT — these don't have P/E-based fair value or analyst consensus` |
| 887 | em | placeholder | '-' (single hyphen) | STRING-LITERAL | `gauge.textContent = '—';` |
| 889 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `alabel.textContent = 'Fund/ETF — no analyst consensus';` |
| 1030 | em | placeholder | '-' (single hyphen) | STRING-LITERAL | `el.textContent = r.wasNull ? '—' : fmtS(r.num);` |
| 1121 | em | prose | comma (default), period if clause-break, colon for label |  | `// Price chart card — manual collapse (separate structure from .card)` |
| 1210 | em | prose | comma (default), period if clause-break, colon for label |  | `// Floating tooltip — #tip-box must exist before this IIFE runs,` |

### `web/templates/ticker_news.html`
em-dash: 2 | en-dash: 0 | total: 2

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 6 | em | title-separator | " - " (hyphen with spaces) |  | `<title>{{ ticker }} News — SignalIntel</title>` |
| 86 | em | prose | comma (default), period if clause-break, colon for label |  | `{{ ticker }} — NEWS ARTICLES` |

### `web/templates/watchlist.html`
em-dash: 5 | en-dash: 1 | total: 6

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 6 | em | title-separator | " - " (hyphen with spaces) |  | `<title>SignalIntel — Watchlist</title>` |
| 118 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `{{ wl.name }}{% if wl.is_default %} <span class="wl-default-lock" data-tip="Default watchlist — c...` |
| 157 | en | numeric-range | 'to' (spaced) or '-' (compact) | STRING-LITERAL | `<th data-tip="Composite score 0–100 combining Momentum, Quality, Insider, Reversion and Legal sig...` |
| 159 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `<th data-tip="Momentum score — measures price trend strength and direction">Mom</th>` |
| 160 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `<th data-tip="Quality score — fundamentals including P/E, EPS growth and return on equity">Qual</th>` |
| 161 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `<th data-tip="Insider score — based on recent insider buying and selling activity">Insider</th>` |


## Bucket B: Source and tests (.py, .js, .css, .sh)

Files in scope: **58** | em-dash: **391** | en-dash: **4**

### `.gitignore`
em-dash: 1 | en-dash: 0 | total: 1

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 15 | em | prose | comma (default), period if clause-break, colon for label |  | `# parquet snapshots) — regeneratable, never seed/fixture/config. Globs are` |

### `config/constants.py`
em-dash: 1 | en-dash: 0 | total: 1

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 86 | em | prose | comma (default), period if clause-break, colon for label |  | `# Raises-Lowers 21d CAR spread of -0.79% (t=-3.64, p=2.7e-04) — wrong` |

### `config/entitlements.py` **[P23]**
em-dash: 17 | en-dash: 0 | total: 17

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 2 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Capability predicates and the trial-overlay resolver — the single` |
| 11 | em | prose | comma (default), period if clause-break, colon for label | P23 | `holds the post-trial floor — 'free' for an unpaid trialist; 'pro'` |
| 15 | em | prose | comma (default), period if clause-break, colon for label | P23 | `user['tier'] raw. The raw column is the post-trial floor only — using` |
| 64 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Fail-closed semantics — every one of these returns False:` |
| 79 | em | prose | comma (default), period if clause-break, colon for label | P23,STRING-LITERAL | `"""Read rank from config/tiers.py USER_TIERS[...]['order'] — single source.` |
| 98 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Post-trial, falls back to stored — a paid Pro user falls to 'pro',` |
| 119 | em | prose | comma (default), period if clause-break, colon for label | P23 | `# obtain from effective_tier(user). NEVER pass user['tier'] raw — the` |
| 124 | em | prose | comma (default), period if clause-break, colon for label | P23,STRING-LITERAL | `"""Elite only — the $1-5 score/rating panel is the Elite hook.` |
| 170 | em | prose | comma (default), period if clause-break, colon for label | P23,STRING-LITERAL | `"""Monthly tournament entry. Pro or elite — deliberately NOT` |
| 191 | em | prose | comma (default), period if clause-break, colon for label | P23 | `# 10+ leak surfaces stay synchronised — adding a new score column to` |
| 207 | em | prose | comma (default), period if clause-break, colon for label | P23 | `# carry them — safe to extend the global set.` |
| 230 | em | prose | comma (default), period if clause-break, colon for label | P23 | `This is the locked Free=floor invariant — a free user` |
| 237 | em | prose | comma (default), period if clause-break, colon for label | P23 | `and would raise TypeError on assignment — that is an explicit` |
| 240 | em | prose | comma (default), period if clause-break, colon for label | P23 | `\`price_key\` defaults to 'price' but accepts alternatives — e.g.` |
| 262 | em | prose | comma (default), period if clause-break, colon for label | P23 | `flags (RSI/SMA/short/analyst/52w bands) survive — they're` |
| 265 | em | prose | comma (default), period if clause-break, colon for label | P23 | `PROPRIETARY_FLAGS is sourced from signals/scorer.py — the same` |
| 277 | em | prose | comma (default), period if clause-break, colon for label | P23 | `(Free=floor — no proprietary signal output anywhere).` |

### `config/markets.py`
em-dash: 2 | en-dash: 0 | total: 2

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 4 | em | prose | comma (default), period if clause-break, colon for label |  | `Tabs 1-3 (indices, sectors, currencies) use yfinance — 'yf' key.` |
| 5 | em | prose | comma (default), period if clause-break, colon for label |  | `Tab 4 (crypto) uses TradingView widgets — 'symbol' key.` |

### `config/settings.py`
em-dash: 1 | en-dash: 0 | total: 1

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 3 | em | prose | comma (default), period if clause-break, colon for label |  | `# SECRETS ONLY — this file is gitignored.` |

### `config/tiers.py` **[P23]**
em-dash: 4 | en-dash: 0 | total: 4

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 2 | em | prose | comma (default), period if clause-break, colon for label | P23 | `User tier definitions — single source of truth for all feature limits.` |
| 9 | em | prose | comma (default), period if clause-break, colon for label | P23 | `tier — a trialist's stored users.tier is 'free' while the` |
| 15 | em | prose | comma (default), period if clause-break, colon for label | P23,STRING-LITERAL | `DB column coerces to 'free' via get_tier()'s default branch — no` |
| 22 | em | prose | comma (default), period if clause-break, colon for label | P23,STRING-LITERAL | `'description':     'Unpaid floor — paywall in effect',` |

### `dashboard/dashboard.py`
em-dash: 2 | en-dash: 0 | total: 2

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 68 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `title = f"Top Signals" + (f" — {rating}" if rating else " — All Ratings")` |
| 68 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `title = f"Top Signals" + (f" — {rating}" if rating else " — All Ratings")` |

### `database/db.py`
em-dash: 6 | en-dash: 0 | total: 6

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 199 | em | prose | comma (default), period if clause-break, colon for label |  | `# be isolated from stored history without persistence — see PROJECT_CONTEXT` |
| 452 | em | prose | comma (default), period if clause-break, colon for label |  | `Schema migration is owned by \`initialise_schema\` — the PRAGMA-gated` |
| 787 | em | prose | comma (default), period if clause-break, colon for label |  | `# Migration: paywall arc — trial overlay + Stripe billing identity columns.` |
| 848 | em | prose | comma (default), period if clause-break, colon for label |  | `IntegrityError — the handler catches it, returns 200, and skips` |
| 924 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `# trial_started_at is the caller's responsibility — register() stamps a` |
| 1628 | em | prose | comma (default), period if clause-break, colon for label |  | `works correctly on integer values — the ±0.5 neutral band is the` |

### `main.py`
em-dash: 11 | en-dash: 0 | total: 11

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 317 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `f"📊 <b>SignalIntel — {len(relevant)} watchlist changes</b>\n"` |
| 321 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `logger.info("_send_rating_alerts: throttled — %d changes exceeded max %d", len(relevant), TELEGRA...` |
| 351 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `send_alert(f"📋 <b>SignalIntel — watchlist changes</b>\n\n{body}")` |
| 373 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `f"🚨 SignalIntel — FMP entitlement failure\n\n"` |
| 404 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `f"🚨 SignalIntel — FMP entitlement failure\n\n"` |
| 426 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `lines = [f"📊 <b>SIGNALINTEL — DAILY SUMMARY</b>  {date.today()}", ""]` |
| 664 | em | prose | comma (default), period if clause-break, colon for label |  | `Originating incident: 21 May 2026 analyst bulk crash on ticker FLEU — a` |
| 690 | em | prose | comma (default), period if clause-break, colon for label |  | `constraint — re-scrapes add new events and skip already-known ones.` |
| 901 | em | prose | comma (default), period if clause-break, colon for label |  | `# FMP dividend refresh (weekly, Sunday 03:00) — circuit breaker in _get() protects against stuck ...` |
| 925 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `f"🚨 SignalIntel — FMP entitlement failure\n\n"` |
| 943 | em | prose | comma (default), period if clause-break, colon for label |  | `# Market history (indices, sectors, currencies) — daily 07:00` |

### `notifications/telegram.py`
em-dash: 1 | en-dash: 0 | total: 1

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 41 | em | prose | comma (default), period if clause-break, colon for label |  | `acceptable for the entitlement-failure case — restart-fresh` |

### `scrapers/fmp_scraper.py`
em-dash: 3 | en-dash: 1 | total: 4

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 43 | em | prose | comma (default), period if clause-break, colon for label |  | `recoverable by retry — callers should fail the job and surface the` |
| 50 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `f"FMP HTTP {status_code} on {path} — endpoint not included "` |
| 77 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `"Aborting job — re-enable once FMP rate limit clears."` |
| 80 | en | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `logger.warning(f"[FMP] Rate limited ({streak}/{FMP_CIRCUIT_BREAKER_THRESHOLD}) – sleeping 10s")` |

### `scrapers/legal_risk_scraper.py`
em-dash: 13 | en-dash: 0 | total: 13

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 98 | em | prose | comma (default), period if clause-break, colon for label |  | `# penalty language in an educational/prescriptive context — not enforcement.` |
| 139 | em | prose | comma (default), period if clause-break, colon for label |  | `# Explicit negation — company states absence of litigation` |
| 144 | em | prose | comma (default), period if clause-break, colon for label |  | `# Accounting/accrual context — "settled for" in reserve/estimate language` |
| 147 | em | prose | comma (default), period if clause-break, colon for label |  | `# Routine/ordinary-course language — not indicative of misconduct` |
| 152 | em | prose | comma (default), period if clause-break, colon for label |  | `# Pharma/biotech Paragraph IV — routine generic drug challenge process` |
| 164 | em | prose | comma (default), period if clause-break, colon for label |  | `# Risk-factor list language — "litigation, settlement costs" as category listing` |
| 168 | em | prose | comma (default), period if clause-break, colon for label |  | `# Past/completed settlements — risk is resolved, not ongoing` |
| 174 | em | prose | comma (default), period if clause-break, colon for label |  | `# EPA environmental cleanup — not SEC/fraud type legal risk` |
| 196 | em | prose | comma (default), period if clause-break, colon for label |  | `# Tier 1: single match sufficient — language that only appears in actual enforcement orders` |
| 197 | em | prose | comma (default), period if clause-break, colon for label |  | `# Tier 2: moderate signals — require 2+ non-hypothetical hits to reduce false positives` |
| 199 | em | prose | comma (default), period if clause-break, colon for label |  | `# Tier 1 — extremely specific to actual enforcement; one match is conclusive` |
| 233 | em | prose | comma (default), period if clause-break, colon for label |  | `# Tier 2 — weaker signals; only classify if 2+ non-hypothetical hits co-occur` |
| 288 | em | prose | comma (default), period if clause-break, colon for label |  | `# Require present-tense active language — skip if context is forward-looking/hypothetical.` |

### `scrapers/markets_scraper.py`
em-dash: 1 | en-dash: 0 | total: 1

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 93 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `logger.info(f"[markets] Scrape complete — {total} rows total")` |

### `scrapers/screener_scraper.py`
em-dash: 1 | en-dash: 0 | total: 1

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 280 | em | prose | comma (default), period if clause-break, colon for label |  | `# Exchange is metadata — write to ticker_metadata, not screener_snapshots.` |

### `scrapers/sector_scraper.py`
em-dash: 3 | en-dash: 0 | total: 3

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 90 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `logger.error(f"[Sector] {etf}: fetch failed — {e}")` |
| 151 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `logger.warning(f"[Sector] {sector}: no data — assigned neutral score 50")` |
| 165 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `logger.info(f"[Sector] Done — {len(results)} sectors written for {today}")` |

### `scrapers/yahoo_scraper.py`
em-dash: 3 | en-dash: 1 | total: 4

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 73 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `"Aborting job — re-enable once Yahoo rate limit clears."` |
| 78 | en | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `f"for {ticker} {data_type} – sleeping 10s"` |
| 122 | em | prose | comma (default), period if clause-break, colon for label |  | `Fetch income statement, balance sheet, and cash flow — three separate HTTP calls.` |
| 183 | em | prose | comma (default), period if clause-break, colon for label |  | `# (pct > 60 / > 40 / > 20). None stays None — never coerce to 0.` |

### `scripts/altman_distribution_analysis.py`
em-dash: 6 | en-dash: 0 | total: 6

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 46 | em | prose | comma (default), period if clause-break, colon for label |  | `# Altman Z'' (1995 non-manufacturing) — three bins, not four` |
| 173 | em | prose | comma (default), period if clause-break, colon for label |  | `missing_financials_only += 1  # both missing — count under financials bucket` |
| 192 | em | prose | comma (default), period if clause-break, colon for label |  | `# Division-by-zero guard inside compute_z_raw — treat as financials problem` |
| 285 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `print(f"  {bin_name} ({label}) — selection: {rule}")` |
| 313 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `print("─── Z'' DISTRESS BIN — TOP SECTORS ────────────────────────────────")` |
| 357 | em | placeholder | '-' (single hyphen) | STRING-LITERAL | `print(f"{row_label_z0:32s} {_fmt(classic_neg):>16s} {'—':>16s}")` |

### `scripts/analyst_pt_event_study.py`
em-dash: 7 | en-dash: 0 | total: 7

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 3 | em | prose | comma (default), period if clause-break, colon for label |  | `analyst_pt_event_study.py — interim validation for analyst_mom v0.16.0.` |
| 215 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `log.info(f"  cache MISS on {len(missing)} tickers — fetching incrementally")` |
| 461 | em | prose | comma (default), period if clause-break, colon for label |  | `# By top-10 most-active firms (real only — placebo has firm='_PLACEBO_')` |
| 479 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `print("  Lowers ratings before delisting are systematically absent — the")` |
| 523 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `print("    and at least 3× the placebo spread — the analyst events drive a")` |
| 529 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `print("    is softer than ideal — interpret magnitude cautiously.")` |
| 570 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `print("ANALYST PRICE-TARGET EVENT STUDY — RESULTS")` |

### `scripts/backfill_exchange.py`
em-dash: 4 | en-dash: 0 | total: 4

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 60 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `logger.warning("Signal %d received — will exit cleanly after current ticker.", signum)` |
| 110 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `logger.info("backfill_exchange.py — START")` |
| 124 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `logger.info("Nothing to do — all tickers already have exchange populated.")` |
| 163 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `"%d consecutive failures — possible FinViz throttle. "` |

### `scripts/backup_database.sh`
em-dash: 7 | en-dash: 0 | total: 7

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 2 | em | prose | comma (default), period if clause-break, colon for label |  | `# SignalIntel — nightly DB backup.` |
| 67 | em | prose | comma (default), period if clause-break, colon for label |  | `# ── 4) Rotation — explicit keep-set; everything else gets pruned ─────────────` |
| 74 | em | prose | comma (default), period if clause-break, colon for label |  | `# bash 3.2 has no associative arrays — we track the keep-set as a delimited` |
| 88 | em | prose | comma (default), period if clause-break, colon for label |  | `# DAILY set — top N most recent (strict pattern check on each, defensive)` |
| 100 | em | prose | comma (default), period if clause-break, colon for label |  | `# WEEKLY set — top N most recent Sunday backups` |
| 118 | em | prose | comma (default), period if clause-break, colon for label |  | `# Prune — only files matching the strict pattern that are NOT in the keep-set` |
| 126 | em | prose | comma (default), period if clause-break, colon for label |  | `# filename did not match strict pattern — skip (defensive: never touch` |

### `scripts/benchmark_yahoo.py`
em-dash: 2 | en-dash: 0 | total: 2

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 13 | em | prose | comma (default), period if clause-break, colon for label |  | `0 — all fetches completed (some may be empty; that's acceptable)` |
| 14 | em | prose | comma (default), period if clause-break, colon for label |  | `1 — YahooRateLimitedError tripped during benchmark` |

### `scripts/drop_screener_snapshots_exchange.py`
em-dash: 2 | en-dash: 0 | total: 2

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 22 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `print("exchange column not present — nothing to do.")` |
| 25 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `print(f"exchange column found — {cols.index('exchange')+1}/{len(cols)} columns")` |

### `scripts/git-hooks/pre-commit`
em-dash: 1 | en-dash: 0 | total: 1

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 2 | em | prose | comma (default), period if clause-break, colon for label |  | `# Auth-adjacent pre-commit hook — P23 mechanical enforcement.` |

### `scripts/install-hooks.sh`
em-dash: 2 | en-dash: 0 | total: 2

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 30 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `echo "WARNING: existing symlink points to '$current_link' — replacing"` |
| 34 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `echo "WARNING: existing non-symlink file at $TARGET — backing up to $backup"` |

### `scripts/purge_sub_threshold_rating_changes.py`
em-dash: 4 | en-dash: 0 | total: 4

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 8 | em | prose | comma (default), period if clause-break, colon for label |  | `rating_changes    — rows where price_at_change < MIN_PRICE_FOR_SIGNAL` |
| 9 | em | prose | comma (default), period if clause-break, colon for label |  | `signal_scores     — all rows for tickers whose latest price < threshold` |
| 10 | em | prose | comma (default), period if clause-break, colon for label |  | `top_signals_of_day — all rows for tickers whose latest price < threshold` |
| 122 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `logger.error("Purge FAILED — rolled back: %s", e)` |

### `scripts/rebuild_rating_changes.py`
em-dash: 3 | en-dash: 0 | total: 3

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 101 | em | prose | comma (default), period if clause-break, colon for label |  | `# New ticker — first row, no prior state, skip` |
| 122 | em | prose | comma (default), period if clause-break, colon for label |  | `# We do this in Python (one query per transition) — acceptable for` |
| 171 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `logger.error("Rebuild FAILED — rolled back: %s", e)` |

### `scripts/reclassify_legal_risk.py`
em-dash: 1 | en-dash: 0 | total: 1

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 91 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `print("(Dry run — no DB changes written)")` |

### `scripts/setup_stripe_products.py` **[P23]**
em-dash: 2 | en-dash: 0 | total: 2

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 74 | em | prose | comma (default), period if clause-break, colon for label | P23 | `enabled on the account) — with at most 2 products to manage, a` |
| 78 | em | prose | comma (default), period if clause-break, colon for label | P23 | `.get() as an instance method — \`product.get(...)\` triggers` |

### `signals/line_item_keys.py`
em-dash: 3 | en-dash: 0 | total: 3

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 5 | em | prose | comma (default), period if clause-break, colon for label |  | `financial_statements.line_item_key — no normalisation at write time.` |
| 73 | em | prose | comma (default), period if clause-break, colon for label |  | `# Piotroski F-Score (9 binary signals) — Phase 2b-ii` |
| 86 | em | prose | comma (default), period if clause-break, colon for label |  | `# Altman Z-Score — Phase 2b-ii` |

### `signals/scorer.py`
em-dash: 26 | en-dash: 1 | total: 27

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 6 | em | prose | comma (default), period if clause-break, colon for label |  | `#   1. Momentum       — price vs SMAs, RSI, relative volume` |
| 7 | em | prose | comma (default), period if clause-break, colon for label |  | `#   2. Quality        — ROE, margins, EPS growth, analyst rec` |
| 8 | em | prose | comma (default), period if clause-break, colon for label |  | `#   3. Insider        — conviction-weighted insider activity` |
| 9 | em | prose | comma (default), period if clause-break, colon for label |  | `#   4. Mean Reversion — oversold RSI + proximity to 52w low` |
| 180 | em | prose | comma (default), period if clause-break, colon for label |  | `return 50.0   # neutral — no data` |
| 258 | em | prose | comma (default), period if clause-break, colon for label |  | `NULL inputs always return (50, 'null') — P5: NULL = neutral.` |
| 281 | em | prose | comma (default), period if clause-break, colon for label |  | `# Low conviction — no signal regardless of direction` |
| 356 | em | prose | comma (default), period if clause-break, colon for label |  | `Ignores: companies with < 2 years of data — treated as neutral, never penalised.` |
| 529 | em | prose | comma (default), period if clause-break, colon for label |  | `Ignores: companies with incomplete financial data — no penalty, never` |
| 587 | em | prose | comma (default), period if clause-break, colon for label |  | `Ignores: tickers with no institutional holder data — treated as neutral 50.0.` |
| 600 | em | prose | comma (default), period if clause-break, colon for label |  | `# noise, not a real signal — route to neutral rather than tier-scoring` |
| 620 | em | prose | comma (default), period if clause-break, colon for label |  | `do — and three hard upgrades still = 80 exactly):` |
| 632 | em | prose | comma (default), period if clause-break, colon for label |  | `Ignores: tickers with no analyst changes in window — neutral 50.0.` |
| 738 | em | prose | comma (default), period if clause-break, colon for label |  | `STRONG_BUY  — composite >= 72 AND insider >= 65` |
| 739 | em | prose | comma (default), period if clause-break, colon for label |  | `BUY         — composite >= 62` |
| 740 | em | prose | comma (default), period if clause-break, colon for label |  | `STRONG_HOLD — composite 45-62` |
| 741 | em | prose | comma (default), period if clause-break, colon for label |  | `SELL        — composite < 45` |
| 742 | em | prose | comma (default), period if clause-break, colon for label |  | `WEAK_HOLD   — composite < 38 AND insider <= 35` |
| 743 | em | prose | comma (default), period if clause-break, colon for label |  | `STRONG_SELL — composite < 25 AND insider <= 20` |
| 744 | em | prose | comma (default), period if clause-break, colon for label |  | `HOLD        — reversion >= 75` |
| 760 | em | prose | comma (default), period if clause-break, colon for label |  | `# Proprietary flag strings — paywall arc Step 4d.` |
| 765 | em | prose | comma (default), period if clause-break, colon for label |  | `# list — single source of truth. Stored flag output is byte-identical` |
| 787 | em | prose | comma (default), period if clause-break, colon for label |  | `_PROPRIETARY_* tuples — never inline literals — so adding a new` |
| 787 | em | prose | comma (default), period if clause-break, colon for label |  | `_PROPRIETARY_* tuples — never inline literals — so adding a new` |
| 837 | en | numeric-range | 'to' (spaced) or '-' (compact) |  | `_SECTOR_MODIFIER_WEIGHT = 0.15   # dial to 0.10–0.20 after backtesting` |
| 878 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `logger.debug("Skipped %s — price $%.4f below MIN_PRICE_FOR_SIGNAL", ticker, price)` |
| 964 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `f"({', '.join(sample)}{'...' if len(missing_legal) > 5 else ''}) — flagged for scraping"` |

### `signals/target_price.py`
em-dash: 4 | en-dash: 1 | total: 5

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 5 | em | prose | comma (default), period if clause-break, colon for label |  | `The silent-failure guard in main.py logs at ERROR level — check logs if 12M TARGET shows '-'` |
| 206 | em | prose | comma (default), period if clause-break, colon for label |  | `FMP price target is already a 12-month analyst consensus — use directly.` |
| 217 | em | prose | comma (default), period if clause-break, colon for label |  | `# FMP target = 12-month analyst consensus — most reliable` |
| 289 | em | prose | comma (default), period if clause-break, colon for label |  | `Master function — computes the SignalIntel 12-month price target.` |
| 343 | en | prose | comma (default), period if clause-break, colon for label |  | `# Hard bounds: 20%–300% of current price` |

### `tests/conftest.py` **[P23]**
em-dash: 2 | en-dash: 0 | total: 2

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 7 | em | prose | comma (default), period if clause-break, colon for label | P23 | `DB: connects to data/trading_system.db — the live SQLite file. All queries` |
| 57 | em | prose | comma (default), period if clause-break, colon for label | P23,STRING-LITERAL | `assert date is not None, "signal_scores is empty — run the scorer first"` |

### `tests/test_api_rating_display.py`
em-dash: 10 | en-dash: 0 | total: 10

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 6 | em | prose | comma (default), period if clause-break, colon for label |  | `codes — STRONG_BUY, STRONG_HOLD, SELL, etc. — instead of the descriptive` |
| 6 | em | prose | comma (default), period if clause-break, colon for label |  | `codes — STRONG_BUY, STRONG_HOLD, SELL, etc. — instead of the descriptive` |
| 12 | em | prose | comma (default), period if clause-break, colon for label |  | `identifiers (e.g. \`new_rating\`, \`direction\`) — those are data plumbing` |
| 32 | em | prose | comma (default), period if clause-break, colon for label |  | `whose history includes a NULL old_rating (so we exercise both branches —` |
| 66 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `pytest.skip("rating_changes is empty — no fixture data on this deploy")` |
| 75 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `assert rating_events, f"no rating events returned for {ticker} — fixture assumption broken"` |
| 81 | em | prose | comma (default), period if clause-break, colon for label |  | `# No raw internal codes — exact-word matches only, to avoid false` |
| 87 | em | prose | comma (default), period if clause-break, colon for label |  | `# At least one canonical display label must appear — proves the` |
| 114 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `pytest.skip("no rating_changes row with NULL old_rating — can't exercise initial-rating branch")` |
| 126 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `f"(NULL old_rating row exists in DB) — got titles: "` |

### `tests/test_data_integrity.py`
em-dash: 34 | en-dash: 0 | total: 34

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 2 | em | prose | comma (default), period if clause-break, colon for label |  | `Data integrity tests — freshness, uniqueness, and distribution checks on the live DB.` |
| 120 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `assert len(latest_signals) >= 1000, f"Only {len(latest_signals)} signals — scorer may have failed"` |
| 126 | em | prose | comma (default), period if clause-break, colon for label |  | `CONDITIONAL — skipped if coverage is 0% (fmp_price_targets not yet populated).` |
| 137 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `pytest.skip("target_price is 0% — fmp_price_targets not yet populated")` |
| 158 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `pytest.skip("legal_risk table is empty — SEC scraper not yet run")` |
| 163 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `assert none_pct >= 70, f"'None' risk only {none_pct:.0f}% of classified tickers — classifier may ...` |
| 171 | em | prose | comma (default), period if clause-break, colon for label |  | `Skipped if the table is empty (job has not yet run — acceptable on fresh deploy).` |
| 178 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `pytest.skip("earnings_history is empty — Yahoo scraper not yet run")` |
| 183 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `assert latest >= cutoff, f"earnings_history last scraped {row[0]} — older than 14 days"` |
| 196 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `pytest.skip("financial_statements is empty — Yahoo financials scraper not yet run")` |
| 201 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `assert latest >= cutoff, f"financial_statements last scraped {row[0]} — older than 14 days"` |
| 214 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `pytest.skip("analyst_changes is empty — Yahoo analyst scraper not yet run")` |
| 219 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `assert latest >= cutoff, f"analyst_changes last scraped {row[0]} — older than 14 days"` |
| 232 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `pytest.skip("institutional_holders is empty — Yahoo holders scraper not yet run")` |
| 237 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `assert latest >= cutoff, f"institutional_holders last scraped {row[0]} — older than 14 days"` |
| 254 | em | prose | comma (default), period if clause-break, colon for label |  | `separate FOLLOWUP — start narrow at the locus of the original bug).` |
| 257 | em | prose | comma (default), period if clause-break, colon for label |  | `a tmp_path SQLite file — zero in-test schema replica, so no drift risk.` |
| 288 | em | prose | comma (default), period if clause-break, colon for label |  | `Ignores: weekends and holidays — 72h cutoff covers the Sat/Sun gap.` |
| 289 | em | prose | comma (default), period if clause-break, colon for label |  | `Ignores: tickers with no upcoming earnings — empty refresh is acceptable` |
| 294 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `pytest.skip("earnings_calendar is empty — FMP earnings scraper not yet run")` |
| 299 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `assert latest >= cutoff, f"earnings_calendar last updated {row[0]} — older than 72h"` |
| 308 | em | prose | comma (default), period if clause-break, colon for label |  | `Ignores: one-week skip tolerance — 14d covers a single missed Sunday run.` |
| 309 | em | prose | comma (default), period if clause-break, colon for label |  | `Ignores: non-dividend payers — excluded from the refresh set by design.` |
| 313 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `pytest.skip("dividends is empty — FMP dividend scraper not yet run")` |
| 318 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `assert latest >= cutoff, f"dividends last updated {row[0]} — older than 14 days"` |
| 324 | em | prose | comma (default), period if clause-break, colon for label |  | `Skipped if the table is empty (lazy-populated cache — scoring job has` |
| 327 | em | prose | comma (default), period if clause-break, colon for label |  | `Catches: target_price pipeline stalling — the table is populated lazily` |
| 330 | em | prose | comma (default), period if clause-break, colon for label |  | `Ignores: cache-window staleness up to 7 days — get_price_targets_map's` |
| 336 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `pytest.skip("fmp_price_targets is empty — scoring job has not yet populated cache")` |
| 341 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `assert latest >= cutoff, f"fmp_price_targets last updated {row[0]} — older than 14 days"` |
| 349 | em | prose | comma (default), period if clause-break, colon for label |  | `like the other three FMP tables — economic_calendar is defined in` |
| 356 | em | prose | comma (default), period if clause-break, colon for label |  | `Ignores: weekends — 72h cutoff covers Sat/Sun without false positives.` |
| 360 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `pytest.skip("economic_calendar is empty — FMP economic scraper not yet run")` |
| 365 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `assert latest >= cutoff, f"economic_calendar last scraped {row[0]} — older than 72h"` |

### `tests/test_enrichment_map_builders.py`
em-dash: 8 | en-dash: 0 | total: 8

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 8 | em | prose | comma (default), period if clause-break, colon for label |  | `Ignores: data-quality issues (NULL values, zero counts) — those are DB-level constraints` |
| 89 | em | prose | comma (default), period if clause-break, colon for label |  | `Ignores: tickers with no earnings (absent key is correct — caller treats as empty list).` |
| 155 | em | prose | comma (default), period if clause-break, colon for label |  | `Ignores: holders with NULL pct_out (SUM returns NULL or partial — DB-level constraint test).` |
| 162 | em | prose | comma (default), period if clause-break, colon for label |  | `# AAPL — two filing dates; only 2026-03-31 should be used` |
| 165 | em | prose | comma (default), period if clause-break, colon for label |  | `("AAPL", "2025-12-31", "Vanguard",   7.0),  # stale — must be ignored` |
| 166 | em | prose | comma (default), period if clause-break, colon for label |  | `# TSLA — single filing date` |
| 188 | em | prose | comma (default), period if clause-break, colon for label |  | `Ignores: tickers with zero activity in window (absent from map is correct — caller` |
| 226 | em | prose | comma (default), period if clause-break, colon for label |  | `Same synthetic fixture as the previous v0.16.0 test — different expected` |

### `tests/test_entitlements.py` **[P23]**
em-dash: 28 | en-dash: 0 | total: 28

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 2 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Tests for config/entitlements.py — capability predicates + trial overlay.` |
| 35 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Ignores: timezone offsets — FIXED_NOW is naive UTC same as _now().` |
| 67 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Catches: trial silently extending past the 7-day window — the` |
| 78 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Catches: higher-rank rule regressing — a paid Pro user mid-trial` |
| 87 | em | prose | comma (default), period if clause-break, colon for label | P23 | `floor, not 'free' — a paying user keeps what they paid for.` |
| 108 | em | prose | comma (default), period if clause-break, colon for label | P23 | `invisible — trial_grant is hardcoded to 'elite' and stored is` |
| 115 | em | prose | comma (default), period if clause-break, colon for label | P23 | `elite+trial user would unexpectedly fall to stored — but` |
| 120 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Ignores: the >= vs > distinction — that would only be observable` |
| 203 | em | prose | comma (default), period if clause-break, colon for label | P23 | `P15 silence: free AND pro denied — exactly one tier passes.` |
| 213 | em | prose | comma (default), period if clause-break, colon for label | P23 | `P15 silence: free denied — paid floor only.` |
| 233 | em | prose | comma (default), period if clause-break, colon for label | P23 | `P15 silence: free AND pro denied — Elite hook.` |
| 240 | em | prose | comma (default), period if clause-break, colon for label | P23 | `# ── $5 boundary: can_view_score_for_ticker — both sides × every tier` |
| 266 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Catches: off-by-one — $5 is NOT in the penny band.` |
| 284 | em | prose | comma (default), period if clause-break, colon for label | P23 | `# ── can_create_watchlist — delegation contract ────────────────────` |
| 304 | em | prose | comma (default), period if clause-break, colon for label | P23,STRING-LITERAL | `"""TRIAL_DAYS must be 7 — locked decision.` |
| 312 | em | prose | comma (default), period if clause-break, colon for label | P23 | `# ── strip_scores_for_non_elite — bulk row helper ──────────────────` |
| 321 | em | prose | comma (default), period if clause-break, colon for label | P23 | `rows — so matrix tests verify the full PROPRIETARY_SCORE_FIELDS` |
| 370 | em | prose | comma (default), period if clause-break, colon for label | P23 | `the unpaid floor — sees no proprietary scores at any price band.` |
| 377 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Catches: a future change that lets free see non-penny scores —` |
| 408 | em | prose | comma (default), period if clause-break, colon for label | P23 | `price >= 5 rows — this is what Pro pays for.` |
| 466 | em | prose | comma (default), period if clause-break, colon for label | P23 | `does NOT add keys that were absent on input — that would expand` |
| 491 | em | prose | comma (default), period if clause-break, colon for label | P23 | `price field. Helper must honour the alternate key — the predicate` |
| 526 | em | prose | comma (default), period if clause-break, colon for label | P23 | `# new_rating is now in PROPRIETARY_SCORE_FIELDS (rating alias) — stripped` |
| 538 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Ignores: timing — this is correctness, not perf.` |
| 596 | em | prose | comma (default), period if clause-break, colon for label | P23 | `much (descriptive lost — over-broad gate) or too little` |
| 597 | em | prose | comma (default), period if clause-break, colon for label | P23 | `(proprietary leaked — under-broad gate).` |
| 600 | em | prose | comma (default), period if clause-break, colon for label | P23 | `constants — sourced via the PROPRIETARY_FLAGS frozenset, so this` |
| 664 | em | prose | comma (default), period if clause-break, colon for label | P23,STRING-LITERAL | `"""Elite caller: helper short-circuits — proprietary flags` |

### `tests/test_fmp_circuit_breaker.py`
em-dash: 1 | en-dash: 0 | total: 1

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 6 | em | prose | comma (default), period if clause-break, colon for label |  | `Uses unittest.mock to stub requests.get and time.sleep — no real HTTP,` |

### `tests/test_fmp_entitlement_error.py` **[P23]**
em-dash: 5 | en-dash: 0 | total: 5

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 11 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Origin: 18 May 2026 economic_calendar staleness — HTTP 402 was silently` |
| 76 | em | prose | comma (default), period if clause-break, colon for label | P23 | `_get() must raise FMPEntitlementError on HTTP 401 (unauthorized —` |
| 98 | em | prose | comma (default), period if clause-break, colon for label | P23 | `_get() must raise FMPEntitlementError on HTTP 403 (forbidden —` |
| 134 | em | prose | comma (default), period if clause-break, colon for label | P23 | `# Must not raise — the generic else branch returns None.` |
| 147 | em | prose | comma (default), period if clause-break, colon for label | P23 | `forgets the log_run call — the 18 May root cause where the cron` |

### `tests/test_invariants.py`
em-dash: 6 | en-dash: 0 | total: 6

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 2 | em | prose | comma (default), period if clause-break, colon for label |  | `Scoring invariants — data correctness rules from docs/scoring_invariants.md.` |
| 40 | em | prose | comma (default), period if clause-break, colon for label |  | `altman_penalty). Pre-0.17 rows are NULL by design — the test` |
| 66 | em | prose | comma (default), period if clause-break, colon for label |  | `# SIGNAL — at v0.17+ at least SOME rows must carry non-NULL sub-scores` |
| 75 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `f"across {len(latest_signals)} rows — the in-memory scores are being "` |
| 79 | em | prose | comma (default), period if clause-break, colon for label |  | `# SILENCE — the column being PRESENT in the schema is necessary but` |
| 145 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `pytest.skip("sector_modifier_applied is all NULL — sector modifier not yet active")` |

### `tests/test_phase2b_scorers.py`
em-dash: 15 | en-dash: 0 | total: 15

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 5 | em | prose | comma (default), period if clause-break, colon for label |  | `partial-data, scorer-specific edge — 5 cases × 5 scorers = 25 tests.` |
| 90 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `"""Only 1 quarter available — should work; decay weight = 4 only.` |
| 113 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `"""Healthy company — all 9 signals pass → F=9 → 80.0.` |
| 134 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `"""Distressed company — all 9 signals fail → F=1 → 20.0.` |
| 187 | em | prose | comma (default), period if clause-break, colon for label |  | `# Keep F1, F2, F3, F4, F9 passing — block F5, F6, F7, F8.` |
| 292 | em | prose | comma (default), period if clause-break, colon for label |  | `Same numerical set used by test_altman_grey_zone_minus10 — verifies the` |
| 318 | em | prose | comma (default), period if clause-break, colon for label |  | `Ignores: where in the safe zone — only that Z >= 3.0.` |
| 361 | em | prose | comma (default), period if clause-break, colon for label |  | `Catches: helper clamping to 0 (it must not — pure math, no clamp).` |
| 395 | em | prose | comma (default), period if clause-break, colon for label |  | `Ignores: which input is missing — the contract is binary, not per-input.` |
| 448 | em | prose | comma (default), period if clause-break, colon for label |  | `than classic Z for the same firm — the empirical justification for the` |
| 474 | em | prose | comma (default), period if clause-break, colon for label |  | `Ignores: where in the safe zone — only that Z'' >= 2.6.` |
| 526 | em | prose | comma (default), period if clause-break, colon for label |  | `Ignores: which input is missing — the contract is binary.` |
| 613 | em | prose | comma (default), period if clause-break, colon for label |  | `— route to neutral 50.0 rather than tier-scoring a phantom top tier.` |
| 672 | em | prose | comma (default), period if clause-break, colon for label |  | `# Retained at v0.17.0 after the soft-PT neutralisation — the ladder is now` |
| 678 | em | prose | comma (default), period if clause-break, colon for label |  | `# value, not a synthesised event sequence — the ladder logic is what's under` |

### `tests/test_registration_trial.py` **[P23]**
em-dash: 6 | en-dash: 0 | total: 6

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 7 | em | prose | comma (default), period if clause-break, colon for label | P23 | `trial_started_at — when NULL, _parse_trial_start returns None,` |
| 47 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Ignores: the exact reported elapsed seconds — only the` |
| 63 | em | prose | comma (default), period if clause-break, colon for label | P23,STRING-LITERAL | `"trial_started_at must be stamped, not NULL — this is the inert-trial guard"` |
| 69 | em | prose | comma (default), period if clause-break, colon for label | P23,STRING-LITERAL | `"trial overlay must be active on day 0 — _parse_trial_start must round-trip the stamp"` |
| 81 | em | prose | comma (default), period if clause-break, colon for label | P23 | `new parameter — they must still get a usable user row, just` |
| 89 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Ignores: effective_tier behavior on the NULL-anchor row — that` |

### `tests/test_scorer.py`
em-dash: 6 | en-dash: 0 | total: 6

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 2 | em | prose | comma (default), period if clause-break, colon for label |  | `Tests for signals/scorer.py — paywall-arc proprietary-flag discipline.` |
| 8 | em | prose | comma (default), period if clause-break, colon for label |  | `sourcing it from the _PROPRIETARY_* tuples — that would leave the` |
| 31 | em | prose | comma (default), period if clause-break, colon for label |  | `row — the row is intentionally bare to isolate the` |
| 39 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `f"but it is NOT in PROPRIETARY_FLAGS — the entitlements gate "` |
| 55 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `f"{expected!r} not in PROPRIETARY_FLAGS — gate would leak"` |
| 88 | em | prose | comma (default), period if clause-break, colon for label |  | `descriptive flag string to the _PROPRIETARY_* tuples — that` |

### `tests/test_scorer_snapshot.py`
em-dash: 22 | en-dash: 0 | total: 22

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 21 | em | prose | comma (default), period if clause-break, colon for label |  | `financials_map, inst_own_map, analyst_mom_map) — those are None here` |
| 37 | em | prose | comma (default), period if clause-break, colon for label |  | `# cutoff slides daily — SS07's window expires fully on 2026-05-28.` |
| 43 | em | prose | comma (default), period if clause-break, colon for label |  | `and datetime.strptime — all used by signals.scorer.score_insider.` |
| 68 | em | prose | comma (default), period if clause-break, colon for label |  | `# Profile: STRONG_BUY — high momentum, high quality, strong insider buying` |
| 75 | em | prose | comma (default), period if clause-break, colon for label |  | `# Profile: BUY — solid fundamentals, no insider boost` |
| 82 | em | prose | comma (default), period if clause-break, colon for label |  | `# Profile: STRONG_HOLD — neutral momentum, decent quality` |
| 89 | em | prose | comma (default), period if clause-break, colon for label |  | `# Profile: HOLD — oversold RSI + near 52w low trips mean reversion path` |
| 96 | em | prose | comma (default), period if clause-break, colon for label |  | `# Profile: SELL (weak-side) — composite ~33, insider neutral (no data → 50)` |
| 103 | em | prose | comma (default), period if clause-break, colon for label |  | `# Profile: SELL — weak fundamentals, composite ~24` |
| 110 | em | prose | comma (default), period if clause-break, colon for label |  | `# Profile: STRONG_SELL — collapsed fundamentals, RSI mid-range + far from 52w low` |
| 122 | em | prose | comma (default), period if clause-break, colon for label |  | `# Profile: legal MINOR row — composite is reduced by -5 penalty` |
| 136 | em | prose | comma (default), period if clause-break, colon for label |  | `# Profile: sector HIGH strength (60.0) — positive modifier applied` |
| 143 | em | prose | comma (default), period if clause-break, colon for label |  | `# Profile: sector LOW strength (40.0) — negative modifier applied` |
| 150 | em | prose | comma (default), period if clause-break, colon for label |  | `# Profile: sector NEUTRAL (50.0) — modifier is zero` |
| 157 | em | prose | comma (default), period if clause-break, colon for label |  | `# Profile: all-NULL momentum inputs — P5: each NULL contributes 50 neutral` |
| 164 | em | prose | comma (default), period if clause-break, colon for label |  | `# Profile: WEAK_HOLD — moderate weakness, CFO sell drives insider_score to 34` |
| 183 | em | prose | comma (default), period if clause-break, colon for label |  | `# CFO selling for WH14 — drives insider_score to 34 (weight 8: net=-8, mapped=34)` |
| 203 | em | prose | comma (default), period if clause-break, colon for label |  | `# Only SS07 has enrichment data — all other tickers remain P5 neutral (50.0/0).` |
| 265 | em | prose | comma (default), period if clause-break, colon for label |  | `# — so SS07's composite/rating fields remain unchanged. Only` |
| 293 | em | prose | comma (default), period if clause-break, colon for label |  | `#       — the other 13 tickers have no inst_own_map entry and stay on the P5` |
| 296 | em | prose | comma (default), period if clause-break, colon for label |  | `# Do NOT modify this to match broken output — fix the refactor instead.` |
| 361 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `f"{len(mismatches)} snapshot mismatches — refactor is not behaviour-preserving:\n"` |

### `tests/test_screener.py`
em-dash: 3 | en-dash: 0 | total: 3

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 2 | em | prose | comma (default), period if clause-break, colon for label |  | `Screener API filter tests — exchange filter correctness.` |
| 88 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `f"all-exchanges total={all_exchanges['total']} — exchange filter "` |
| 100 | em | prose | comma (default), period if clause-break, colon for label |  | `Ignores: which exchange values are considered 'valid' — no server-side` |

### `tests/test_setup_stripe_guard.py` **[P23]**
em-dash: 5 | en-dash: 0 | total: 5

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 8 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Tests here exercise only the pure-Python guard function — no Stripe` |
| 38 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Ignores: the exact wording of the diagnostic — only the` |
| 55 | em | prose | comma (default), period if clause-break, colon for label | P23 | `populate STRIPE_SECRET_KEY before the script ran — would` |
| 59 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Ignores: None/None-equivalent inputs — caller passes a string` |
| 72 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Ignores: actual Stripe API connectivity — this asserts only the` |

### `tests/test_signal_labels.py`
em-dash: 5 | en-dash: 0 | total: 5

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 54 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `f"tier_label('{rating}') = '{tier_label(rating)}' — expected '{expected}'"` |
| 61 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `f"tier_short('{rating}') = '{tier_short(rating)}' — expected '{expected}'"` |
| 85 | em | prose | comma (default), period if clause-break, colon for label |  | `Catches: <span>Strong Buy</span>, <div>Strong Buy: AAPL</div> — directive language` |
| 135 | em | prose | comma (default), period if clause-break, colon for label |  | `Catches: theme label == "Strong Buy Momentum" or "Buy the Dip" — old directive names.` |
| 136 | em | prose | comma (default), period if clause-break, colon for label |  | `Ignores: theme id == "strong_buy_momentum" or "buy_the_dip" — stable IDs (P14).` |

### `tests/test_smoke.py` **[P23]**
em-dash: 14 | en-dash: 0 | total: 14

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 2 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Smoke tests — every page and key API endpoint must return HTTP 200.` |
| 151 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Catches: missing WL header — indicates the column was not added.` |
| 179 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Ignores: WlPicker.open internals — those are JS unit-level concerns.` |
| 197 | em | prose | comma (default), period if clause-break, colon for label | P23 | `P15: absence test — verifies the bad pattern is gone, not the good one.` |
| 239 | em | prose | comma (default), period if clause-break, colon for label | P23 | `/watchlist must include the tier badge — catches regressions where the` |
| 254 | em | prose | comma (default), period if clause-break, colon for label | P23 | `numeric limit/current fields — not a plain string.` |
| 321 | em | prose | comma (default), period if clause-break, colon for label | P23 | `The string 'unauthorized' must never appear in any rendered page body —` |
| 371 | em | prose | comma (default), period if clause-break, colon for label | P23 | `'FREE' — not 'ELITE' — and the DB row MUST still read 'free' after the` |
| 371 | em | prose | comma (default), period if clause-break, colon for label | P23 | `'FREE' — not 'ELITE' — and the DB row MUST still read 'free' after the` |
| 386 | em | prose | comma (default), period if clause-break, colon for label | P23,STRING-LITERAL | `"Nav rendered 'ELITE' despite DB tier='free' — current_user() or "` |
| 392 | em | prose | comma (default), period if clause-break, colon for label | P23,STRING-LITERAL | `"DB tier was silently overwritten during the request — a hook is "` |
| 405 | em | prose | comma (default), period if clause-break, colon for label | P23 | `user. This asserts the SILENCE — the badge should never fabricate a` |
| 425 | em | prose | comma (default), period if clause-break, colon for label | P23,STRING-LITERAL | `f"{path} rendered 'ELITE' badge despite DB tier='free' — "` |
| 430 | em | prose | comma (default), period if clause-break, colon for label | P23,STRING-LITERAL | `"After rendering all PAGE_ROUTES, DB tier was silently mutated — "` |

### `tests/test_squeeze_panel.py`
em-dash: 9 | en-dash: 0 | total: 9

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 2 | em | prose | comma (default), period if clause-break, colon for label |  | `Dashboard short-squeeze setups tile — confluence detector tests.` |
| 17 | em | prose | comma (default), period if clause-break, colon for label |  | `- Render-layer concerns (Jinja markup, CSS classes, tier_short() mapping —` |
| 103 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `"""HOLD tier with SI >= 10 is NOT on the tile — confluence requires` |
| 108 | em | prose | comma (default), period if clause-break, colon for label |  | `regardless of conviction — the whole point of the tile is` |
| 110 | em | prose | comma (default), period if clause-break, colon for label |  | `Ignores: WEAK_HOLD / SELL / STRONG_SELL cases — same exclusion path.` |
| 117 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `"""BUY-rated ticker with SI < 10 is NOT on the tile — floor not cleared.` |
| 131 | em | prose | comma (default), period if clause-break, colon for label |  | `Catches: guard regression — without it, the tile's worst case is a` |
| 141 | em | prose | comma (default), period if clause-break, colon for label |  | `not a neutral score — the ticker simply doesn't appear).` |
| 185 | em | prose | comma (default), period if clause-break, colon for label |  | `# SI values 11..25 — all above floor; expect the 10 highest (16..25)` |

### `tests/test_stripe_checkout.py` **[P23]**
em-dash: 10 | en-dash: 0 | total: 10

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 2 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Tests for GET /upgrade — Stripe Checkout creation (Phase 2 Commit 5).` |
| 10 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Catches — regressions in tier/interval/currency validation,` |
| 14 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Ignores — Stripe-side checkout UX, success/cancel page rendering,` |
| 57 | em | prose | comma (default), period if clause-break, colon for label | P23 | `# IP across many tests in quick succession — disable rate limit` |
| 98 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Ignores: the exact redirect target — only the 'reject' verdict` |
| 148 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Catches: a regression that flips the default to GBP — most of` |
| 166 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Catches: regression in the CF header read path — this is the` |
| 168 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Ignores: other ISO countries — they all resolve to USD by policy.` |
| 251 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Was verified live this session — webhook fails with "missing` |
| 327 | em | prose | comma (default), period if clause-break, colon for label | P23 | `interval — those are pinned by the setup script.` |

### `tests/test_stripe_webhook.py` **[P23]**
em-dash: 19 | en-dash: 0 | total: 19

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 15 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Catches — every change to the signature-verification, idempotency,` |
| 18 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Ignores — Stripe-side delivery semantics (retry timing, signature` |
| 56 | em | prose | comma (default), period if clause-break, colon for label | P23 | `# The top-level "object": "event" is required — stripe.Webhook.construct_event` |
| 220 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Catches: any future relaxation of construct_event() — e.g.` |
| 225 | em | prose | comma (default), period if clause-break, colon for label | P23 | `malformed payloads — only the 'reject' verdict matters.` |
| 259 | em | prose | comma (default), period if clause-break, colon for label | P23 | `SignatureVerificationError on the empty header — both are` |
| 284 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Ignores: the exact tier_effective_until timestamp seconds — the` |
| 345 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Ignores: the exact response body shape on duplicate — only the` |
| 379 | em | prose | comma (default), period if clause-break, colon for label | P23 | `# because timestamp differs — Stripe redelivers with the same` |
| 393 | em | prose | comma (default), period if clause-break, colon for label | P23 | `# Subscription.retrieve called exactly once — second delivery` |
| 397 | em | prose | comma (default), period if clause-break, colon for label | P23,STRING-LITERAL | `f"(called {call_count['n']} times — handler ran twice)"` |
| 412 | em | prose | comma (default), period if clause-break, colon for label | P23 | `user on cancellation — the documented "ride out the` |
| 415 | em | prose | comma (default), period if clause-break, colon for label | P23 | `actually expires — that is a separate concern.` |
| 455 | em | prose | comma (default), period if clause-break, colon for label | P23,STRING-LITERAL | `f"cancellation must NOT drop tier — locked decision. Got tier={after['tier']!r}"` |
| 458 | em | prose | comma (default), period if clause-break, colon for label | P23,STRING-LITERAL | `f"cancellation must NOT deactivate — locked decision. "` |
| 472 | em | prose | comma (default), period if clause-break, colon for label | P23,STRING-LITERAL | `"tier_after must equal tier_before on cancellation — tier deliberately unchanged"` |
| 526 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Ignores: the exact error message format — only that it's` |
| 571 | em | prose | comma (default), period if clause-break, colon for label | P23,STRING-LITERAL | `wasn't set — the endpoint would silently accept unsigned` |
| 575 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Ignores: the rest of the request path — no signature verification` |

### `tests/test_subscription_events_schema.py` **[P23]**
em-dash: 12 | en-dash: 0 | total: 12

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 8 | em | prose | comma (default), period if clause-break, colon for label | P23 | `a double tier flip — the load-bearing reason this table exists.` |
| 88 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Ignores: column order, defaults, indexes — covered by` |
| 104 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Ignores: column order (cid) — future migrations may shift it.` |
| 112 | em | prose | comma (default), period if clause-break, colon for label | P23,STRING-LITERAL | `"""stripe_event_id has UNIQUE + NOT NULL — the idempotency lock.` |
| 117 | em | prose | comma (default), period if clause-break, colon for label | P23 | `- UNIQUE is the actual lock — duplicate INSERT raises` |
| 124 | em | prose | comma (default), period if clause-break, colon for label | P23 | `(sqlite_autoindex_*) — implementation detail.` |
| 152 | em | prose | comma (default), period if clause-break, colon for label | P23 | `on this default — initial insert omits status, transitions` |
| 154 | em | prose | comma (default), period if clause-break, colon for label | P23,STRING-LITERAL | `Ignores: the schema's NOT NULL annotation enforcement order —` |
| 174 | em | prose | comma (default), period if clause-break, colon for label | P23 | `tier_before, tier_after, raw_payload) — those are` |
| 187 | em | prose | comma (default), period if clause-break, colon for label | P23 | `slowly — and slow webhook lookups compound into` |
| 190 | em | prose | comma (default), period if clause-break, colon for label | P23 | `that SQLite auto-creates for the UNIQUE constraint —` |
| 207 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Ignores: the schema in absolute terms — only the second-run` |

### `tests/test_themes.py`
em-dash: 5 | en-dash: 0 | total: 5

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 2 | em | prose | comma (default), period if clause-break, colon for label |  | `Theme coherence tests — all theme definitions are valid and produce sane counts.` |
| 23 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `"""Theme IDs must be lowercase snake_case (P14 — IDs are stable once shipped)."""` |
| 45 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `f"legally_clean count={count} — suspiciously low, "` |
| 95 | em | prose | comma (default), period if clause-break, colon for label |  | `Catches: theme["label"] == "Strong Buy Momentum" — directive label still present.` |
| 96 | em | prose | comma (default), period if clause-break, colon for label |  | `Ignores: theme["id"] == "strong_buy_momentum" — stable URL/API key, never renamed (P14).` |

### `tests/test_user_schema.py` **[P23]**
em-dash: 10 | en-dash: 0 | total: 10

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 5 | em | prose | comma (default), period if clause-break, colon for label | P23 | `nullable/default contract — the Stripe webhook is about to write to` |
| 46 | em | prose | comma (default), period if clause-break, colon for label | P23 | `the users table. Source: PRAGMA table_info — returns rows of` |
| 72 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Ignores: column order — only presence is asserted (cid is not` |
| 84 | em | prose | comma (default), period if clause-break, colon for label | P23 | `either break create_user() (which omits them — they'd need a value` |
| 91 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Ignores: the cid (column index) — column-order shifts are fine.` |
| 112 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Ignores: USER_TIERS dict shape in config/tiers.py — that's tested` |
| 118 | em | prose | comma (default), period if clause-break, colon for label | P23 | `# PRAGMA table_info returns the default as the raw SQL literal —` |
| 130 | em | prose | comma (default), period if clause-break, colon for label | P23 | `on timeout — a slow lookup compounds into duplicate-write risk` |
| 135 | em | prose | comma (default), period if clause-break, colon for label | P23 | `on username/email (sqlite_autoindex_users_*) — they're` |
| 155 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Ignores: the schema in absolute terms — this test only asserts the` |

### `tests/test_user_tiers.py` **[P23]**
em-dash: 4 | en-dash: 0 | total: 4

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 5 | em | prose | comma (default), period if clause-break, colon for label | P23 | `These tests exercise pure functions — no template pattern matching involved.` |
| 37 | em | prose | comma (default), period if clause-break, colon for label | P23 | `Catches: cap drift on any tier — free=0 (no access), pro=5, elite=unlimited.` |
| 57 | em | prose | comma (default), period if clause-break, colon for label | P23 | `P15 silence assertion: 'free' is the unpaid floor — no gateable access.` |
| 90 | em | prose | comma (default), period if clause-break, colon for label | P23,STRING-LITERAL | `floor via get_tier()'s default branch — same as any other unknown key.` |

### `tests/test_volume_component.py`
em-dash: 1 | en-dash: 0 | total: 1

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 238 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `"""score_volume() is a thin wrapper — result must match _compute_volume()[0]."""` |

### `tests/test_watchlists.py`
em-dash: 3 | en-dash: 0 | total: 3

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 2 | em | prose | comma (default), period if clause-break, colon for label |  | `Tests for multi-watchlist CRUD — db layer and API endpoints.` |
| 153 | em | prose | comma (default), period if clause-break, colon for label |  | `exercise the free-tier rejection should override inline — none` |
| 329 | em | prose | comma (default), period if clause-break, colon for label |  | `# NOT fire — proves the rejection comes specifically from the is_default guard.` |

### `tests/test_yahoo_circuit_breaker.py`
em-dash: 1 | en-dash: 0 | total: 1

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 6 | em | prose | comma (default), period if clause-break, colon for label |  | `Uses unittest.mock to stub the fetch callable and time.sleep — no real HTTP,` |

### `tests/test_yahoo_scraper.py`
em-dash: 3 | en-dash: 0 | total: 3

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 4 | em | prose | comma (default), period if clause-break, colon for label |  | `Uses an in-memory SQLite database — no live DB writes, no network calls.` |
| 64 | em | prose | comma (default), period if clause-break, colon for label |  | `create duplicates — INSERT OR IGNORE enforces the UNIQUE constraint.` |
| 125 | em | prose | comma (default), period if clause-break, colon for label |  | `# Second call: failure — last_success_at must not change` |


## Bucket C: Unprotected docs (.md)

Files in scope: **8** | em-dash: **199** | en-dash: **28**

### `AGENTS.md`
em-dash: 27 | en-dash: 2 | total: 29

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 3 | em | prose | comma (default), period if clause-break, colon for label |  | `> 1. \`PROJECT_CONTEXT.md\` — stable project context (Athena's role, SignalIntel overview, 7-tier...` |
| 4 | em | prose | comma (default), period if clause-break, colon for label |  | `> 2. \`HANDOFF.md\` — current session state (what's running, inflight, queued, recent session log...` |
| 8 | em | prose | comma (default), period if clause-break, colon for label |  | `# SignalIntel — Project Context for Codex` |
| 10 | en | numeric-range | 'to' (spaced) or '-' (compact) |  | `> **Before making changes, consult \`docs/scoring_invariants.md\`** for both data correctness rul...` |
| 10 | en | numeric-range | 'to' (spaced) or '-' (compact) |  | `> **Before making changes, consult \`docs/scoring_invariants.md\`** for both data correctness rul...` |
| 14 | em | prose | comma (default), period if clause-break, colon for label |  | `> **When writing tests, apply P15 — every test must articulate what it catches AND what it intent...` |
| 84 | em | prose | comma (default), period if clause-break, colon for label |  | `- **MOMENTUM** — price momentum, RSI, SMA signals` |
| 85 | em | prose | comma (default), period if clause-break, colon for label |  | `- **QUALITY** — fundamentals (P/E, EPS, sector comparison)` |
| 86 | em | prose | comma (default), period if clause-break, colon for label |  | `- **INSIDER** — insider trade signals` |
| 87 | em | prose | comma (default), period if clause-break, colon for label |  | `- **REVERSION** — mean reversion signals` |
| 88 | em | prose | comma (default), period if clause-break, colon for label |  | `- **LEGAL** — SEC EDGAR risk penalty (6-tier classification)` |
| 98 | em | prose | comma (default), period if clause-break, colon for label |  | `- **Configuration over hardcoding** — times, thresholds, and settings belong in \`config/settings...` |
| 104 | em | prose | comma (default), period if clause-break, colon for label |  | `- **SendGrid** — email alerts` |
| 105 | em | prose | comma (default), period if clause-break, colon for label |  | `- **Stripe** — paywall and subscription management` |
| 106 | em | prose | comma (default), period if clause-break, colon for label |  | `- **Unusual Whales** — options flow data` |
| 107 | em | prose | comma (default), period if clause-break, colon for label |  | `- **SEC EDGAR** — legal risk scoring (scraper built, wiring in progress)` |
| 153 | em | prose | comma (default), period if clause-break, colon for label |  | `1. Verified public performance record — all signals logged with date + price, wins AND losses vis...` |
| 155 | em | prose | comma (default), period if clause-break, colon for label |  | `3. Short squeeze detector — high short interest + STRONG_BUY confluence` |
| 174 | em | prose | comma (default), period if clause-break, colon for label |  | `- Tickers below this price are excluded from new signal scoring. The filter lives in \`signals/sc...` |
| 195 | em | prose | comma (default), period if clause-break, colon for label |  | `- User-facing only — appear in templates, Telegram alerts, and JSON responses to the frontend` |
| 210 | em | prose | comma (default), period if clause-break, colon for label |  | `- \`get_watchlist_tickers(alerts_only=False)\` (default) returns all tickers regardless of alert ...` |
| 215 | em | prose | comma (default), period if clause-break, colon for label |  | `- Watchlist-add is via a shared dropdown picker (\`_watchlist_picker.html\`), included once in \`...` |
| 218 | em | prose | comma (default), period if clause-break, colon for label |  | `- \`POST /api/watchlists\` accepts an optional \`add_ticker\` body param — creates the watchlist ...` |
| 278 | em | prose | comma (default), period if clause-break, colon for label |  | `audit table flagged \`AUTH SIDE-EFFECT — REQUIRES REVIEW\`. State` |
| 288 | em | prose | comma (default), period if clause-break, colon for label |  | `The \`--no-verify\` flag is the audit signal — its presence in` |
| 295 | em | prose | comma (default), period if clause-break, colon for label |  | `exists for a human to render the verdict — CC reasoning its own` |
| 314 | em | prose | comma (default), period if clause-break, colon for label |  | `hook is symlinked, not copied — updates to` |
| 323 | em | prose | comma (default), period if clause-break, colon for label |  | `**not** an acceptable evolution — exceptions belong in audit-table` |
| 339 | em | prose | comma (default), period if clause-break, colon for label |  | `- When editing scrapers, be mindful of FinViz rate limits — add delays between requests` |

### `README.md`
em-dash: 3 | en-dash: 0 | total: 3

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 1 | em | prose | comma (default), period if clause-break, colon for label |  | `# Trading System — Phase 1` |
| 10 | em | prose | comma (default), period if clause-break, colon for label |  | `1. **Screener** — all 11 sectors, three views per sector (overview, financial, technical),` |
| 14 | em | prose | comma (default), period if clause-break, colon for label |  | `2. **Insider Trades** — buy, sale, and option exercise transactions scraped from` |

### `docs/config_variable_classification.md`
em-dash: 1 | en-dash: 0 | total: 1

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 99 | em | prose | comma (default), period if clause-break, colon for label |  | `\| **ALERT_CONFIG** \| **SECRET** \| smtp_host, smtp_port, smtp_user, smtp_pass, from_addr, to_ad...` |

### `docs/data_source_map.md`
em-dash: 48 | en-dash: 23 | total: 71

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 4 | em | prose | comma (default), period if clause-break, colon for label |  | `- The four highest-value, lowest-friction NEW composite-score components to build next, ranked by...` |
| 4 | em | prose | comma (default), period if clause-break, colon for label |  | `- The four highest-value, lowest-friction NEW composite-score components to build next, ranked by...` |
| 5 | en | numeric-range | 'to' (spaced) or '-' (compact) | STRING-LITERAL | `- Drop **congressional trading** and **ESG** from the composite score and keep them as dashboard ...` |
| 5 | en | numeric-range | 'to' (spaced) or '-' (compact) | STRING-LITERAL | `- Drop **congressional trading** and **ESG** from the composite score and keep them as dashboard ...` |
| 5 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `- Drop **congressional trading** and **ESG** from the composite score and keep them as dashboard ...` |
| 6 | en | numeric-range | 'to' (spaced) or '-' (compact) |  | `- Your current FMP + Finnhub + SEC EDGAR + FINRA + FRED stack already covers ~80% of the data nee...` |
| 6 | em | prose | comma (default), period if clause-break, colon for label |  | `- Your current FMP + Finnhub + SEC EDGAR + FINRA + FRED stack already covers ~80% of the data nee...` |
| 11 | em | prose | comma (default), period if clause-break, colon for label |  | `1. **Fundamental/market APIs (15)** — FMP, Alpha Vantage, Polygon.io, Finnhub, Tiingo, EOD Histor...` |
| 12 | em | prose | comma (default), period if clause-break, colon for label |  | `2. **Sentiment / Social (15)** — Stocktwits public \`streams/symbol/{TICKER}.json\` endpoint, Sto...` |
| 13 | em | prose | comma (default), period if clause-break, colon for label |  | `3. **News & RSS (18)** — Benzinga (basic free tier + paid Cloud), Benzinga free RSS, Seeking Alph...` |
| 14 | em | prose | comma (default), period if clause-break, colon for label |  | `4. **Short / options / alt (16)** — FINRA Equity Short Interest API (free), Ortex (~$80–$140/mo r...` |
| 14 | en | numeric-range | 'to' (spaced) or '-' (compact) |  | `4. **Short / options / alt (16)** — FINRA Equity Short Interest API (free), Ortex (~$80–$140/mo r...` |
| 14 | em | prose | comma (default), period if clause-break, colon for label |  | `4. **Short / options / alt (16)** — FINRA Equity Short Interest API (free), Ortex (~$80–$140/mo r...` |
| 15 | em | prose | comma (default), period if clause-break, colon for label |  | `5. **Analyst ratings (8)** — Finnhub \`/stock/recommendation\` (free, 60/min), FMP price-target &...` |
| 16 | em | prose | comma (default), period if clause-break, colon for label |  | `6. **Academic / canonical research (11 papers)** — Jegadeesh & Titman 1993 momentum, Fama-French ...` |
| 17 | em | prose | comma (default), period if clause-break, colon for label |  | `7. **FinTwit / reference accounts (~20)** — to be tracked but not mechanically ingested.` |
| 28 | em | prose | comma (default), period if clause-break, colon for label |  | `\| **FMP** (already integrated) \| 250 req/day \| $19/mo Starter, $69/mo Premium \| API key in UR...` |
| 30 | em | prose | comma (default), period if clause-break, colon for label |  | `\| **Polygon.io** \| "Basic" free, 5/min, EOD only \| $29/mo Starter (unlimited calls, 15-min del...` |
| 32 | en | numeric-range | 'to' (spaced) or '-' (compact) |  | `\| **Tiingo** \| Free Starter (limited daily price data, no news/fundamentals) \| $10–$50/mo indi...` |
| 34 | em | prose | comma (default), period if clause-break, colon for label |  | `\| **Intrinio** \| None (free trial) \| ~$1,500/mo+ enterprise \| API key + OAuth \| JSON REST \|...` |
| 40 | em | prose | comma (default), period if clause-break, colon for label |  | `\| **FRED API (St Louis Fed)** \| **Fully free**, 32-char API key \| n/a \| API key \| JSON/XML \...` |
| 42 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `\| **Yahoo Finance / yfinance** \| Free unofficial scraping \| n/a \| None \| JSON (private) \| T...` |
| 43 | em | prose | comma (default), period if clause-break, colon for label |  | `\| **IEX Cloud** \| **Discontinued Aug 31, 2024** — do not architect around it. \|` |
| 45 | em | prose | comma (default), period if clause-break, colon for label |  | `### 2. SENTIMENT & SOCIAL DATA SOURCES — STANDALONE DASHBOARD ONLY` |
| 49 | em | prose | comma (default), period if clause-break, colon for label |  | `- **Pushshift**: Now access-restricted to Reddit moderators only — do not rely on it.` |
| 52 | em | prose | comma (default), period if clause-break, colon for label |  | `- **Google Trends**: No official API. \`pytrends\` library scrapes the public web app; rate-limit...` |
| 52 | en | numeric-range | 'to' (spaced) or '-' (compact) |  | `- **Google Trends**: No official API. \`pytrends\` library scrapes the public web app; rate-limit...` |
| 54 | em | prose | comma (default), period if clause-break, colon for label |  | `- **Finnhub social-sentiment & news-sentiment endpoints**: Already free under the 60/min plan — u...` |
| 62 | en | numeric-range | 'to' (spaced) or '-' (compact) |  | `\| **Benzinga free RSS** \| ✅ headline-only \| "Basic News API" free tier on AWS Marketplace (hea...` |
| 62 | en | numeric-range | 'to' (spaced) or '-' (compact) |  | `\| **Benzinga free RSS** \| ✅ headline-only \| "Basic News API" free tier on AWS Marketplace (hea...` |
| 68 | em | prose | comma (default), period if clause-break, colon for label |  | `\| **Bloomberg** \| ❌ No public RSS \| Enterprise BPIPE only \| — \|` |
| 79 | en | numeric-range | 'to' (spaced) or '-' (compact) |  | `- **Ortex**: Aggregates global exchange short data + estimated cost-to-borrow + estimated SI from...` |
| 81 | en | numeric-range | 'to' (spaced) or '-' (compact) |  | `- **Unusual Whales**: Retail platform subscription **$50/month** as of the May 2025 price increas...` |
| 85 | em | prose | comma (default), period if clause-break, colon for label |  | `- **House/Senate PTR filings**: Direct PDF disclosures; community scrapers on GitHub (e.g., \`sen...` |
| 89 | em | prose | comma (default), period if clause-break, colon for label |  | `- **NOAA / satellite alt-data**: Free public sets but require domain modelling — out of scope.` |
| 93 | em | prose | comma (default), period if clause-break, colon for label |  | `- **Finnhub** \`/stock/recommendation\` — free, returns buy/hold/sell/strong-buy/strong-sell coun...` |
| 95 | em | prose | comma (default), period if clause-break, colon for label |  | `- **Benzinga Analyst Insights API** — paid Cloud tier; rich PT-drift fields.` |
| 96 | em | prose | comma (default), period if clause-break, colon for label |  | `- **Nasdaq Data Link "Analyst Ratings & Price Targets"** (ARPT) — paid subscription database, pro...` |
| 97 | em | prose | comma (default), period if clause-break, colon for label |  | `- **Tipranks** — scrape only, anti-bot.` |
| 98 | em | prose | comma (default), period if clause-break, colon for label |  | `- **Zacks**, **Refinitiv I/B/E/S** — institutional.` |
| 100 | em | prose | comma (default), period if clause-break, colon for label |  | `### 6. ACADEMIC & ACCREDITED RESEARCH — Which new factors actually have predictive evidence?` |
| 107 | em | prose | comma (default), period if clause-break, colon for label |  | `\| **Quality / Profitability** (already have) \| Novy-Marx 2013, *JFE* 108(1) \| "Profitability, ...` |
| 108 | em | prose | comma (default), period if clause-break, colon for label |  | `\| **Insider** (already have) \| Cohen, Malloy & Pomorski 2012, *JF* 67(3) \| Opportunistic-trade...` |
| 109 | em | prose | comma (default), period if clause-break, colon for label |  | `\| **Short Interest** \| Boehmer, Jones & Zhang 2008, *JF* 63(2) \| "Heavily shorted stocks under...` |
| 110 | em | prose | comma (default), period if clause-break, colon for label |  | `\| **PEAD / Earnings Surprise** \| Bernard & Thomas 1989, *J. Accounting Research* 27 \| Top vs b...` |
| 111 | em | prose | comma (default), period if clause-break, colon for label |  | `\| **Analyst Revisions** \| Womack 1996, *JF* 51(1) \| "For buy recommendations, the mean posteve...` |
| 111 | em | prose | comma (default), period if clause-break, colon for label |  | `\| **Analyst Revisions** \| Womack 1996, *JF* 51(1) \| "For buy recommendations, the mean posteve...` |
| 113 | em | prose | comma (default), period if clause-break, colon for label |  | `\| **Option Skew / Smirk** \| Xing, Zhang & Zhao 2010, *JFQA* 45(3) \| "Stocks exhibiting the ste...` |
| 114 | en | numeric-range | 'to' (spaced) or '-' (compact) | STRING-LITERAL | `\| **Congressional Trading** \| Ziobrowski 2004, *JFQA* 39(4) vs Eggers & Hainmueller 2013, *Jour...` |
| 114 | en | numeric-range | 'to' (spaced) or '-' (compact) | STRING-LITERAL | `\| **Congressional Trading** \| Ziobrowski 2004, *JFQA* 39(4) vs Eggers & Hainmueller 2013, *Jour...` |
| 114 | en | numeric-range | 'to' (spaced) or '-' (compact) | STRING-LITERAL | `\| **Congressional Trading** \| Ziobrowski 2004, *JFQA* 39(4) vs Eggers & Hainmueller 2013, *Jour...` |
| 114 | em | prose | comma (default), period if clause-break, colon for label |  | `\| **Congressional Trading** \| Ziobrowski 2004, *JFQA* 39(4) vs Eggers & Hainmueller 2013, *Jour...` |
| 115 | en | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `\| **ESG** \| Friede/Busch/Bassen 2015 *JSF&I* vs Pedersen/Fitzgibbons/Pomorski 2021, *JFE* 142(2...` |
| 115 | em | prose | comma (default), period if clause-break, colon for label |  | `\| **ESG** \| Friede/Busch/Bassen 2015 *JSF&I* vs Pedersen/Fitzgibbons/Pomorski 2021, *JFE* 142(2...` |
| 116 | em | prose | comma (default), period if clause-break, colon for label |  | `\| **Social Sentiment** \| Kmak et al. 2025 (arXiv 2507.22922) \| "Social media sentiment has onl...` |
| 118 | em | prose | comma (default), period if clause-break, colon for label |  | `### 7. FINTWIT / REFERENCE ACCOUNTS — For UX inspiration only` |
| 142 | en | numeric-range | 'to' (spaced) or '-' (compact) |  | `\| **News-Event** \| SEC EDGAR 8-K RSS + Benzinga RSS (free tier) \| 2 \| 3 \| After (1–5) \|` |
| 154 | em | prose | comma (default), period if clause-break, colon for label |  | `### Stage 1 (next 2 weeks) — free, no architectural change` |
| 159 | en | numeric-range | 'to' (spaced) or '-' (compact) |  | `### Stage 2 (weeks 3–6)` |
| 161 | em | prose | comma (default), period if clause-break, colon for label |  | `5. **Re-normalise** the composite. Suggested new weight vector: momentum 0.25 / quality 0.20 / in...` |
| 163 | en | numeric-range | 'to' (spaced) or '-' (compact) |  | `### Stage 3 (weeks 7–12)` |
| 164 | en | numeric-range | 'to' (spaced) or '-' (compact) |  | `6. **Build the 13F-Flow component** from SEC EDGAR. Compute quarter-over-quarter Δ in number of 1...` |
| 171 | en | numeric-range | 'to' (spaced) or '-' (compact) |  | `11. Consider Ortex (~$80–$140/mo) for institutional-grade short metrics if user demand for the sh...` |
| 185 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `- **Reddit and Twitter/X API terms shifted hard in 2023 and again in early 2026.** Reddit's paid ...` |
| 187 | en | numeric-range | 'to' (spaced) or '-' (compact) | STRING-LITERAL | `- **Congressional trading alpha is sample-dependent and contested.** The famous ~12%/yr Ziobrowsk...` |
| 187 | en | numeric-range | 'to' (spaced) or '-' (compact) | STRING-LITERAL | `- **Congressional trading alpha is sample-dependent and contested.** The famous ~12%/yr Ziobrowsk...` |
| 187 | en | numeric-range | 'to' (spaced) or '-' (compact) | STRING-LITERAL | `- **Congressional trading alpha is sample-dependent and contested.** The famous ~12%/yr Ziobrowsk...` |
| 188 | em | prose | comma (default), period if clause-break, colon for label |  | `- **Social-sentiment predictive power is weak in recent literature.** Kmak et al. 2025 (arXiv:250...` |
| 190 | em | prose | comma (default), period if clause-break, colon for label |  | `- **All pricing listed here is as of May 2026 and changes frequently** — Unusual Whales raised AP...` |
| 190 | en | numeric-range | 'to' (spaced) or '-' (compact) |  | `- **All pricing listed here is as of May 2026 and changes frequently** — Unusual Whales raised AP...` |
| 192 | em | prose | comma (default), period if clause-break, colon for label |  | `- **The 13F dataset is delayed by 45 days** — it is a slow-moving factor, useful for QoQ position...` |

### `docs/scoring_invariants.md`
em-dash: 53 | en-dash: 3 | total: 56

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 9 | en | numeric-range | 'to' (spaced) or '-' (compact) |  | `- The majority of tickers should have \`risk_label = 'None'\` (~80–95%)` |
| 33 | em | prose | comma (default), period if clause-break, colon for label |  | `## 3. Legal Classifier — Hypothetical Phrase Exclusions` |
| 37 | em | prose | comma (default), period if clause-break, colon for label |  | `- \`"paragraph iv"\` — patent IV challenges (normal pharma)` |
| 38 | em | prose | comma (default), period if clause-break, colon for label |  | `- \`"we settled our"\` — past completed settlements` |
| 39 | em | prose | comma (default), period if clause-break, colon for label |  | `- \`"joint venture"\`, \`"supply agreement"\`, \`"license agreement"\` — normal commercial contracts` |
| 40 | em | prose | comma (default), period if clause-break, colon for label |  | `- \`"superfund"\`, \`"national priorities list"\`, \`"hazardous material releases"\`, \`"environm...` |
| 66 | em | prose | comma (default), period if clause-break, colon for label |  | `## 7. Discovery Theme Counts — Legally Clean` |
| 75 | em | prose | comma (default), period if clause-break, colon for label |  | `-- WRONG — only returns tickers already in legal_risk table` |
| 97 | em | prose | comma (default), period if clause-break, colon for label |  | `## 10. Filterable/Sortable Tables — State Preservation` |
| 109 | em | prose | comma (default), period if clause-break, colon for label |  | `## 11. UI Consistency — Tooltip Icons` |
| 118 | em | prose | comma (default), period if clause-break, colon for label |  | `## Final Verification — 2026-05-05` |
| 133 | em | prose | comma (default), period if clause-break, colon for label |  | `# PROCESS INVARIANTS — Rules for Future Development Sessions` |
| 139 | em | prose | comma (default), period if clause-break, colon for label |  | `## P1 — Audit All Surfaces When Adding or Modifying Data` |
| 144 | em | prose | comma (default), period if clause-break, colon for label |  | `- \`/ticker/<symbol>\` — header row, scorecard radar, score breakdown card, fundamentals card, st...` |
| 145 | em | prose | comma (default), period if clause-break, colon for label |  | `- \`/screener\` — column visibility, sort options, filter options` |
| 146 | em | prose | comma (default), period if clause-break, colon for label |  | `- \`/penny/screener\` — column visibility, sort options, filters` |
| 147 | em | prose | comma (default), period if clause-break, colon for label |  | `- \`/watchlist\` — column visibility` |
| 148 | em | prose | comma (default), period if clause-break, colon for label |  | `- \`/backtest\` — relevant rating analysis` |
| 149 | em | prose | comma (default), period if clause-break, colon for label |  | `- \`/\` dashboard — Discovery Themes, ALL SIGNALS table` |
| 150 | em | prose | comma (default), period if clause-break, colon for label |  | `- \`/api/*\` endpoints — data shape returned to frontend` |
| 151 | em | prose | comma (default), period if clause-break, colon for label |  | `- Telegram alerts — if the new data should trigger or appear in notifications` |
| 152 | em | prose | comma (default), period if clause-break, colon for label |  | `- Database schema — column exists, populated, indexed if used for sorting/filtering` |
| 158 | em | prose | comma (default), period if clause-break, colon for label |  | `## P2 — Diagnose Before Fixing` |
| 172 | em | prose | comma (default), period if clause-break, colon for label |  | `## P3 — Verify in Browser, Not in Code` |
| 184 | em | prose | comma (default), period if clause-break, colon for label |  | `## P4 — Commits Are Checkpoints, Not Summaries` |
| 196 | em | prose | comma (default), period if clause-break, colon for label |  | `## P5 — Treat Absence of Data as Neutral, Not Negative` |
| 207 | em | prose | comma (default), period if clause-break, colon for label |  | `## P6 — Numeric Values Stored Numeric, Displayed Formatted` |
| 215 | em | prose | comma (default), period if clause-break, colon for label |  | `## P7 — UI Tooltips on Labels, Not (?) Icons` |
| 223 | em | prose | comma (default), period if clause-break, colon for label |  | `## P8 — Theme Definitions Are Single Source of Truth` |
| 229 | em | prose | comma (default), period if clause-break, colon for label |  | `Adding a new theme requires updating \`config/themes.py\` only — the homepage and screener consum...` |
| 233 | em | prose | comma (default), period if clause-break, colon for label |  | `## P9 — Filter and Sort State Preserves Across Actions` |
| 245 | em | prose | comma (default), period if clause-break, colon for label |  | `## P10 — Defensive Empty-State Handling` |
| 248 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `- The response must include a clear status message (e.g. "Insufficient data — backtest stats accu...` |
| 256 | em | prose | comma (default), period if clause-break, colon for label |  | `## P11 — Document Scoring Invariants as You Discover Them` |
| 259 | en | numeric-range | 'to' (spaced) or '-' (compact) | STRING-LITERAL | `- "Composite score must be in range 0–100"` |
| 260 | en | numeric-range | 'to' (spaced) or '-' (compact) | STRING-LITERAL | `- "Sector strength score must be in range 0–100"` |
| 268 | em | prose | comma (default), period if clause-break, colon for label |  | `## P12 — Preserve Raw Values When Applying Modifiers` |
| 278 | em | prose | comma (default), period if clause-break, colon for label |  | `## P13 — User-Facing Signal Language Is Descriptive, Not Directive` |
| 298 | em | prose | comma (default), period if clause-break, colon for label |  | `## P14 — Discovery Theme IDs Are Stable; Labels May Change` |
| 302 | em | prose | comma (default), period if clause-break, colon for label |  | `Theme labels (e.g. "Top Signal Momentum", "Oversold Signals") are user-facing and may be updated ...` |
| 308 | em | prose | comma (default), period if clause-break, colon for label |  | `## P1.1 — Inventory Before Edit (The Migration Rule)` |
| 323 | em | prose | comma (default), period if clause-break, colon for label |  | `## P1.2 — Migration Completeness Is Verified by Absence, Not Presence` |
| 329 | em | prose | comma (default), period if clause-break, colon for label |  | `Reporting "all listed surfaces updated" is insufficient. The final step of any migration is the a...` |
| 341 | em | prose | comma (default), period if clause-break, colon for label |  | `## P1.3 — Reports Must Be Audit Tables, Not Narrative Summaries` |
| 354 | em | prose | comma (default), period if clause-break, colon for label |  | `## P15 — Test Design Must Articulate Both Signal and Silence` |
| 365 | em | prose | comma (default), period if clause-break, colon for label |  | `Good — \`test_no_directive_language_in_templates\`:` |
| 378 | em | prose | comma (default), period if clause-break, colon for label |  | `## P17 — Full enumeration of effects in audits` |
| 384 | em | prose | comma (default), period if clause-break, colon for label |  | `Origin: BUG-001-REOPENED (7 May 2026). The previous CC audit reported "current_user() always read...` |
| 390 | em | prose | comma (default), period if clause-break, colon for label |  | `## P20 — Analyst completeness gate` |
| 392 | em | prose | comma (default), period if clause-break, colon for label |  | `**P20 — Analyst completeness gate.** When two paths diverge on what an analyst making a buy/sell/...` |
| 396 | em | prose | comma (default), period if clause-break, colon for label |  | `## P26 — Freshness tests fire red on first run by design` |
| 398 | em | prose | comma (default), period if clause-break, colon for label |  | `**P26 — Freshness tests fire red on first run by design.** When a freshness test catches real pro...` |
| 400 | em | numeric-range | 'to' (spaced) or '-' (compact) |  | `The 17 May 2026 economic_calendar finding is the canonical example. \`test_fmp_economic_calendar_...` |
| 406 | em | prose | comma (default), period if clause-break, colon for label |  | `4. Once the underlying job produces fresh data, the test goes green automatically — no test chang...` |
| 412 | em | prose | comma (default), period if clause-break, colon for label |  | `## P27 — Altman Z'' (1995 non-manufacturing) replaces classic Z (1968) for bankruptcy-risk penalty` |
| 414 | em | prose | comma (default), period if clause-break, colon for label |  | `**P27 — Altman Z'' (1995 non-manufacturing) used for bankruptcy-risk penalty as of SCORING_ENGINE...` |

### `docs/stripe_billing_phase1.md`
em-dash: 53 | en-dash: 0 | total: 53

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 1 | em | prose | comma (default), period if clause-break, colon for label |  | `# Stripe Billing — Phase 1 Diagnostic Inventory` |
| 12 | em | prose | comma (default), period if clause-break, colon for label |  | `1. \`CLAUDE.md\` § Business Model still says "Annual billing at 20% discount" and "Free 7-day tri...` |
| 17 | em | prose | comma (default), period if clause-break, colon for label |  | `## 1. Schema write paths — the four Stripe columns` |
| 19 | em | prose | comma (default), period if clause-break, colon for label |  | `### EXISTS — live schema dump` |
| 42 | em | prose | comma (default), period if clause-break, colon for label |  | `### EXISTS — schema definition and migration` |
| 72 | em | prose | comma (default), period if clause-break, colon for label |  | `### EXISTS — read sites` |
| 91 | em | prose | comma (default), period if clause-break, colon for label |  | `### GAP — write sites` |
| 99 | em | prose | comma (default), period if clause-break, colon for label |  | `### EXISTS — \`register()\` literal code` |
| 134 | em | prose | comma (default), period if clause-break, colon for label |  | `### EXISTS — \`create_user()\` literal code` |
| 156 | em | prose | comma (default), period if clause-break, colon for label |  | `### GAP — trial overlay never gets data` |
| 160 | em | prose | comma (default), period if clause-break, colon for label |  | `Nothing in the codebase flips a user OFF trial or to paid tier — confirmed in § 7.` |
| 166 | em | prose | comma (default), period if clause-break, colon for label |  | `### EXISTS — preparation only` |
| 173 | em | prose | comma (default), period if clause-break, colon for label |  | `### GAP — no webhook code, no Stripe SDK, no env` |
| 175 | em | prose | comma (default), period if clause-break, colon for label |  | `Source: \`grep -rn "webhook\\|/stripe\\|stripe.api_key\\|stripe.Webhook\\|STRIPE_WEBHOOK_SECRET" ...` |
| 187 | em | prose | comma (default), period if clause-break, colon for label |  | `- **Signature verification:** \`stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOO...` |
| 197 | em | prose | comma (default), period if clause-break, colon for label |  | `\| \`customer.subscription.deleted\` \| Cancellation finalised (subscription actually ended, not ...` |
| 206 | em | prose | comma (default), period if clause-break, colon for label |  | `**Locked pricing — 8 price points, math verified:**` |
| 217 | em | prose | comma (default), period if clause-break, colon for label |  | `- Product \`signalintel_pro\` ("SignalIntel Pro") — 4 Prices attached.` |
| 218 | em | prose | comma (default), period if clause-break, colon for label |  | `- Product \`signalintel_elite\` ("SignalIntel Elite") — 4 Prices attached.` |
| 243 | em | prose | comma (default), period if clause-break, colon for label |  | `**Why not store price IDs in the app config?** Stripe price IDs are environment-specific (differe...` |
| 251 | em | prose | comma (default), period if clause-break, colon for label |  | `### EXISTS — nothing usable` |
| 253 | em | prose | comma (default), period if clause-break, colon for label |  | `\`grep -rn "CF-IPCountry\\|cf-ipcountry\\|geoip\\|GeoIP\\|X-Forwarded-For\\|accept-language" --in...` |
| 255 | em | prose | comma (default), period if clause-break, colon for label |  | `\`grep -rn "currency\\|GBP\\|USD\\|£" --include="*.py"\` — currency tokens in \`config/markets.py...` |
| 255 | em | prose | comma (default), period if clause-break, colon for label |  | `\`grep -rn "currency\\|GBP\\|USD\\|£" --include="*.py"\` — currency tokens in \`config/markets.py...` |
| 259 | em | prose | comma (default), period if clause-break, colon for label |  | `### GAP — geo-to-currency bridge does not exist` |
| 269 | em | prose | comma (default), period if clause-break, colon for label |  | `This is a decision for Mark — flagged below.` |
| 273 | em | prose | comma (default), period if clause-break, colon for label |  | `## 6. \`subscription_events\` table — webhook idempotency log` |
| 275 | em | prose | comma (default), period if clause-break, colon for label |  | `### EXISTS — concept only` |
| 305 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `**Audit.** \`tier_before\` / \`tier_after\` make it possible to reconstruct exactly what happened...` |
| 307 | em | prose | comma (default), period if clause-break, colon for label |  | `**\`raw_payload\` storage.** SQLite TEXT, full JSON. Cheap. Lets us replay an event with the same...` |
| 311 | em | prose | comma (default), period if clause-break, colon for label |  | `## 7. Tier-flip write — single source verification` |
| 313 | em | prose | comma (default), period if clause-break, colon for label |  | `### EXISTS — \`users.tier\` reads (all via \`effective_tier(user)\`)` |
| 320 | em | prose | comma (default), period if clause-break, colon for label |  | `config/tiers.py:9:              tier — a trialist's stored users.tier is 'free' while the` |
| 321 | em | prose | comma (default), period if clause-break, colon for label |  | `config/entitlements.py:15:user['tier'] raw. The raw column is the post-trial floor only — using` |
| 324 | em | prose | comma (default), period if clause-break, colon for label |  | `config/entitlements.py:119:# obtain from effective_tier(user). NEVER pass user['tier'] raw — the` |
| 333 | em | prose | comma (default), period if clause-break, colon for label |  | `### EXISTS — \`users.tier\` writes (test code only, not production)` |
| 343 | em | prose | comma (default), period if clause-break, colon for label |  | `Every production-code write of \`users.tier\`: **none**. The webhook in Phase 2 will be the **fir...` |
| 345 | em | prose | comma (default), period if clause-break, colon for label |  | `### EXISTS — no cached tier source` |
| 351 | em | prose | comma (default), period if clause-break, colon for label |  | `### Load-bearing assumption — verified` |
| 353 | em | prose | comma (default), period if clause-break, colon for label |  | `**Flipping \`users.tier\` is sufficient.** There is no second tier store, no cache, no session co...` |
| 355 | em | prose | comma (default), period if clause-break, colon for label |  | `### GAP — none for this item` |
| 363 | em | prose | comma (default), period if clause-break, colon for label |  | `### EXISTS — \`is_active\` filter on every user lookup` |
| 382 | em | prose | comma (default), period if clause-break, colon for label |  | `### EXISTS — soft-delete precedent` |
| 386 | em | prose | comma (default), period if clause-break, colon for label |  | `### GAP — no cancellation handler today` |
| 390 | em | prose | comma (default), period if clause-break, colon for label |  | `### DECISION REQUIRED — surfaced for Mark, not decided here` |
| 400 | em | prose | comma (default), period if clause-break, colon for label | STRING-LITERAL | `My read: **Option B** is the cleanest for SaaS reality (canceled users come back; making them re-...` |
| 402 | em | prose | comma (default), period if clause-break, colon for label |  | `Note that \`tier_effective_until\` provides a middle ground regardless of which option is chosen:...` |
| 406 | em | prose | comma (default), period if clause-break, colon for label |  | `## Proposed build order — Phase 2` |
| 410 | em | prose | comma (default), period if clause-break, colon for label |  | `1. **Stamp \`trial_started_at\` at registration.** Modify \`create_user()\` (and \`register()\` i...` |
| 415 | em | prose | comma (default), period if clause-break, colon for label |  | `6. **Webhook handler: \`checkout.session.completed\`.** Resolve \`price.lookup_key\` → \`(tier, c...` |
| 423 | em | prose | comma (default), period if clause-break, colon for label |  | `Steps 1, 5, 6, 7, 8, 10 trip the P23 hook. Steps 2, 3, 4, 9, 11, 12 do not (assuming step 4 adds ...` |
| 431 | em | prose | comma (default), period if clause-break, colon for label |  | `3. **Env strategy for Stripe secrets (§ 3 GAP).** \`.env\` file? OS env via shell? Flask config f...` |
| 433 | em | prose | comma (default), period if clause-break, colon for label |  | `5. **\`tier_effective_until\` enforcement (§ 8 note).** When a user cancels mid-period and keeps ...` |

### `docs/tier_matrix.md`
em-dash: 12 | en-dash: 0 | total: 12

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 5 | em | prose | comma (default), period if clause-break, colon for label |  | `> Numeric limits (watchlist count, etc.) are authoritative in \`config/tiers.py\` — this document...` |
| 74 | em | prose | comma (default), period if clause-break, colon for label |  | `## Penny Stocks — Elite Only` |
| 98 | em | prose | comma (default), period if clause-break, colon for label |  | `Do **not** use purely aspirational upsell language ("unlock powerful tools!") for risk-protective...` |
| 122 | em | prose | comma (default), period if clause-break, colon for label |  | `1. **Decide the tier** — add a row to the matrix table above before writing any code.` |
| 124 | em | prose | comma (default), period if clause-break, colon for label |  | `3. **Gate the route** — use \`user.get("tier")\` compared against the tier key string. Wrap in a ...` |
| 125 | em | prose | comma (default), period if clause-break, colon for label |  | `4. **Return the right status** — 403 for API routes, upgrade-prompt render for page routes.` |
| 126 | em | prose | comma (default), period if clause-break, colon for label |  | `5. **Message correctly** — follow the risk-protective vs. standard messaging guidelines above.` |
| 127 | em | prose | comma (default), period if clause-break, colon for label |  | `6. **Write a test** — at minimum, assert that a Free-tier user is denied and the correct tier can...` |
| 155 | em | prose | comma (default), period if clause-break, colon for label |  | `- **Default tier is \`'free'\`** — \`get_tier(None)\` and \`get_tier('')\` must return the Free c...` |
| 156 | em | prose | comma (default), period if clause-break, colon for label |  | `- **markn is always \`'elite'\`** — auto-upgraded on login in \`web/app.py:current_user()\`.` |
| 157 | em | prose | comma (default), period if clause-break, colon for label |  | `- **Limits live in \`config/tiers.py\` only** — no numeric watchlist limits anywhere else in the ...` |
| 158 | em | prose | comma (default), period if clause-break, colon for label |  | `- **Penny stocks are Elite-only** — this is a risk-protective decision, not a commercial one. Do ...` |

### `tests/README.md`
em-dash: 2 | en-dash: 0 | total: 2

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 34 | em | prose | comma (default), period if clause-break, colon for label |  | `- \`test_target_price_coverage\` — skips if \`fmp_price_targets\` not yet populated (currently 0%)` |
| 35 | em | prose | comma (default), period if clause-break, colon for label |  | `- \`test_sector_modifier_range\` — skips if \`composite_score_raw\` is all NULL (modifier not yet...` |


## Bucket D: Mockups (docs/mockups/*.html)

Files in scope: **4** | em-dash: **32** | en-dash: **0**

### `docs/mockups/dashboard_restructure_v1.html`
em-dash: 18 | en-dash: 0 | total: 18

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 6 | em | title-separator | " - " (hyphen with spaces) |  | `<title>SignalIntel — Dashboard restructure mockup v1</title>` |
| 430 | em | prose | comma (default), period if clause-break, colon for label |  | `/* Locked state (non-Elite) — shown only in free view */` |
| 532 | em | prose | comma (default), period if clause-break, colon for label |  | `<!-- ABOVE THE FOLD — 3×2 -->` |
| 535 | em | prose | comma (default), period if clause-break, colon for label |  | `<!-- PANEL 1 — DAILY SUMMARY -->` |
| 553 | em | prose | comma (default), period if clause-break, colon for label |  | `<!-- PANEL 2 — TOP 5 STRONG -->` |
| 568 | em | prose | comma (default), period if clause-break, colon for label |  | `<!-- PANEL 3 — TOP 5 BEARISH -->` |
| 583 | em | prose | comma (default), period if clause-break, colon for label |  | `<!-- PANEL 4 — MARKET STATE -->` |
| 602 | em | prose | comma (default), period if clause-break, colon for label |  | `<!-- PANEL 5 — WATCHLIST PREVIEW -->` |
| 618 | em | prose | comma (default), period if clause-break, colon for label |  | `<!-- PANEL 6 — DISCOVERY THEMES -->` |
| 636 | em | prose | comma (default), period if clause-break, colon for label |  | `<!-- ELITE SPOTLIGHT — full width -->` |
| 687 | em | prose | comma (default), period if clause-break, colon for label |  | `<!-- BELOW THE FOLD — 3×2 -->` |
| 690 | em | prose | comma (default), period if clause-break, colon for label |  | `<!-- PANEL 8 — EARNINGS NEXT 7 DAYS -->` |
| 705 | em | prose | comma (default), period if clause-break, colon for label |  | `<!-- PANEL 9 — DIVIDENDS THIS WEEK -->` |
| 720 | em | prose | comma (default), period if clause-break, colon for label |  | `<!-- PANEL 10 — SECTOR PERFORMANCE -->` |
| 737 | em | prose | comma (default), period if clause-break, colon for label |  | `<!-- PANEL 11 — RECENT RATING CHANGES -->` |
| 753 | em | prose | comma (default), period if clause-break, colon for label |  | `<!-- PANEL 12 — INSIDER ACTIVITY -->` |
| 769 | em | prose | comma (default), period if clause-break, colon for label |  | `<!-- PANEL 13 — NEWS HEADLINES -->` |
| 787 | em | prose | comma (default), period if clause-break, colon for label |  | `Toggle ELITE / FREE above to compare Panel 7 rendering. Free view shown here as a locked teaser, ...` |

### `docs/mockups/marketing_homepage_hero_v3.html`
em-dash: 2 | en-dash: 0 | total: 2

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 6 | em | title-separator | " - " (hyphen with spaces) |  | `<title>SignalIntel — hero mockup</title>` |
| 372 | em | prose | comma (default), period if clause-break, colon for label |  | `/* ─── HERO RIGHT: visual — stylised live scorecard ─────────── */` |

### `docs/mockups/section2_transparency_v1.html`
em-dash: 6 | en-dash: 0 | total: 6

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 6 | em | title-separator | " - " (hyphen with spaces) |  | `<title>SignalIntel — Section 2 mockup (Transparency)</title>` |
| 692 | em | prose | comma (default), period if clause-break, colon for label |  | `<span><strong>Yes — we publish the losses too.</strong> Every rating change is logged with date a...` |
| 700 | em | prose | comma (default), period if clause-break, colon for label |  | `<div class="proof-number">01 — Verified record</div>` |
| 713 | em | prose | comma (default), period if clause-break, colon for label |  | `<div class="proof-number">02 — Open methodology</div>` |
| 727 | em | prose | comma (default), period if clause-break, colon for label |  | `<div class="proof-number">03 — Wins and losses</div>` |
| 748 | em | prose | comma (default), period if clause-break, colon for label |  | `<div class="attribution">— Mark Nicholson · Founder, The Signal Vault</div>` |

### `docs/mockups/section3_methodology_v2.html`
em-dash: 6 | en-dash: 0 | total: 6

| line | glyph | category | proposed | flags | excerpt |
|---:|---|---|---|---|---|
| 6 | em | title-separator | " - " (hyphen with spaces) |  | `<title>SignalIntel — Section 3 mockup v1</title>` |
| 459 | em | prose | comma (default), period if clause-break, colon for label |  | `No black boxes. No proprietary mystery. Every weight, every threshold, every penalty —` |
| 469 | em | prose | comma (default), period if clause-break, colon for label |  | `<h3>Scoring breakdown — AAPL</h3>` |
| 587 | em | prose | comma (default), period if clause-break, colon for label |  | `<strong>AAPL</strong> · Apple Inc · A "Stable" call — strong on quality and institutional backing...` |
| 684 | em | prose | comma (default), period if clause-break, colon for label |  | `<div class="modifier-desc">Altman Z-score across four tiers. All-or-nothing — any missing input z...` |
| 699 | em | prose | comma (default), period if clause-break, colon for label |  | `see which engine produced which call — and <em>which calls survived which engines</em>.` |


## Totals per bucket

| bucket | em-dash | en-dash | files | combined |
|---|---:|---:|---:|---:|
| Bucket A | 155 | 18 | 26 | 173 |
| Bucket B | 391 | 4 | 58 | 395 |
| Bucket C | 199 | 28 | 8 | 227 |
| Bucket D | 32 | 0 | 4 | 32 |
| **In-scope total** | **777** | **50** | **96** | **827** |

Protected docs (counted only, NOT in scope): em=230, en=4, files=3.

## Phase 2 execution outline (for reference)

1. Bucket-by-bucket sweep, smallest blast radius first: A (user-facing), C (unprotected docs), D (mockups), B (source and tests).
2. Within B, P23-flagged files commit separately with the audit-and-clearance protocol used at `24db3ad`.
3. STRING-LITERAL occurrences in B: surface each test-expectation pair before the swap.
4. Protected docs (List 2): per-file sign-off.
5. Stale artefacts (List 3): one `git rm` commit before any sweep work.
6. After every commit, grep U+2014 and U+2013 on touched files; both counts must be zero per CLAUDE.md.
