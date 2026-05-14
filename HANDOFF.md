# SIGNALINTEL: HANDOFF

**Tactical session state.** Updated end of each session. For stable
project context (who/what/how), see `PROJECT_CONTEXT.md`.

Last updated: 14 May 2026, end of session (Phase 2b-ii shipped).
Next session: Phase 2b-iii or later phases. FRESH CHAT recommended.

---

## JUST SHIPPED — 14 May 2026 (Phase 2b-ii: 5 new scorer functions + composite rebalance)

### Secrets leakage gate (commit 2eb28c5)

- `docs/config_variable_classification.md` created: authoritative enumeration of all variables in 5 tracked config files. ALERT_CONFIG explicitly noted as "7 May 2026 near-miss" (smtp credentials, name matches no grep pattern).
- CLAUDE.md note added directing auditors to use this file instead of literal grep patterns.

### FOLLOWUPS cleanup (commit 61a9eea, pushed)

- 6 completed FOLLOWUP entries pruned from PROJECT_CONTEXT.md.
- New STRUCTURAL DEBT entry added: TEST ISOLATION REFACTOR (tests run against live production DB; proper fix needs per-test temp DB, estimated 20+ files affected).
- All 14 local commits (9 Phase 2a + 5 Phase 2b-i) pushed to remote.

### Phase 2b-ii (5 commits, local main, unpushed)

**Commit 16e36bd** — `feat(scorer): add 4 Yahoo enrichment map helpers + wire into job_generate_signals`

- `database/db.py`: 4 new helpers after `get_legal_risk_map`:
  - `get_earnings_enrichment_map` → `{ticker: [list most-recent-first]}`
  - `get_financials_enrichment_map` → `{ticker: {stmt_type: {fiscal_year: {raw_key: value}}}}`
  - `get_inst_ownership_map` → `{ticker: {total_pct_held, holder_count, filing_date}}` (latest filing only via INNER JOIN)
  - `get_analyst_momentum_map` → `{ticker: {upgrades_90d, downgrades_90d, net_momentum}}` (90-day window, 'up'/'init'=upgrade)
- `main.py`: 4 new imports, 4 map builds in `job_generate_signals`, 4 new kwargs passed to `score_all_tickers`.
- `tests/test_enrichment_map_builders.py`: 4 isolated shape tests using tmp_path SQLite.

**Commit a108153** — `feat(scorer): add 5 Phase 2b-ii scorer functions + TickerSignal fields`

- `signals/scorer.py`:
  - Import: `PIOTROSKI_LOOKUPS, ALTMAN_LOOKUPS` from `signals.line_item_keys`
  - `_parse_market_cap_text(s)` → float|None: parses "1.5B" etc.
  - `score_earnings_surprise`: 4-quarter decay weights (4/3/2/1), contribution ladder ±7/±15/±25, neutral zone (-3%, 0%], P5 empty→50.0
  - `score_piotroski`: Lock 1 (< 2 years → 50.0), 9 binary signals, F≥7→80/6→65/5→50/4→38/≤3→20
  - `score_altman_penalty`: all-or-nothing, Z≥3→0/≥1.8→-10/≥0→-30/<0→-60, X4 uses TotalLiabilitiesNetMinorityInterest
  - `score_inst_ownership`: Lock 3 (pct>60→75.0), tiers >40→55/≤20→35, cap at 100, P5 None→50.0
  - `score_analyst_momentum`: net≥3→80/.../≤-3→20, P5 None→50.0
  - `TickerSignal`: 5 new fields (earnings_score=50.0, piotroski_score=50.0, altman_penalty=0, inst_own_score=50.0, analyst_mom_score=50.0)
- `tests/test_phase2b_scorers.py`: 25 tests (P21 matrix: positive/negative/P5/partial/edge × 5 scorers)

**Commit f1c825d** — `feat(scorer): rebalance composite weights to 1.60-sum + apply Altman penalty additively`

- `compute_composite`: 4 new params (earnings, piotroski, inst_own, analyst_mom all default 50.0), 4 new weights (each 0.125, total 0.50 added). New sum: 1.60.
- `score_all_tickers`: computes all 5 new scores per ticker, passes to `compute_composite`, applies `altman_penalty` additively alongside `legal_penalty` in `c_score_raw`.

**Commit f477b5f** — `feat(scorer): bump SCORING_ENGINE_VERSION to 0.13.0 for Phase 2b-ii`

- `config/constants.py`: `SCORING_ENGINE_VERSION = "0.13.0"`

**Commit 48fdf49** — `test(scorer): regenerate snapshot baseline for v0.13.0 + add synthetic enrichment maps for SS07`

- `tests/test_scorer_snapshot.py`:
  - SS07 row: added `"market_cap": "240M"` for Altman (Z≈-0.25 → penalty -60)
  - 4 new constants: `_SYNTHETIC_EARNINGS_MAP`, `_SYNTHETIC_FINANCIALS_MAP`, `_SYNTHETIC_INST_OWN_MAP`, `_SYNTHETIC_ANALYST_MOM_MAP`
  - SS07 synthetic data: 4 severe earnings misses → score 0.0; Piotroski F=2 → score 20.0; analyst net=-4 → score 20.0; Altman Z<0 → penalty -60 → composite clamped to 0.0 → STRONG_SELL
  - Test call passes all 4 enrichment maps
  - EXPECTED_SNAPSHOT regenerated for v0.13.0 (all 7 rating tiers represented)
- P21 distribution: STRONG_BUY(1) BUY(2) STRONG_HOLD(6) HOLD(1) SELL(2) WEAK_HOLD(1) STRONG_SELL(1)

### Test count

- pytest: 232 passing, 4 Yahoo freshness skipped (tables still empty, correct behaviour).
- Prior: 207 passing. +25 phase2b scorers + 4 enrichment map builders = +29 new tests, -4 (snapshot was failing during commits 3-4) → net +25, but snapshot now passing again.

### Commits (5 total, local main, unpushed)

```
48fdf49 test(scorer): regenerate snapshot baseline for v0.13.0 + add synthetic enrichment maps for SS07
f477b5f feat(scorer): bump SCORING_ENGINE_VERSION to 0.13.0 for Phase 2b-ii
f1c825d feat(scorer): rebalance composite weights to 1.60-sum + apply Altman penalty additively
a108153 feat(scorer): add 5 Phase 2b-ii scorer functions + TickerSignal fields
16e36bd feat(scorer): add 4 Yahoo enrichment map helpers + wire into job_generate_signals
```

Combined with 16 prior pushed commits, 5 commits sit on local main unpushed.

**SCORING_ENGINE_VERSION bumped to 0.13.0** — composite rebalance + 5 new enrichment scorers.

---

## CURRENT STATE (end of 14 May 2026)

- Scheduler PID 1867 still running on Phase 2a code (not restarted since 07:29 BST).
  Phase 2b-ii is on disk but live scheduler must be restarted to use new scoring.
- 5 Phase 2b-ii commits on local main, not yet pushed.
- 5 Yahoo data tables: analyst_changes and earnings_history may now have overnight data (02:00 / 02:15 BST crons). Verify before next session.
- pytest: 232 passing, 4 Yahoo freshness skipped.
- SCORING_ENGINE_VERSION: 0.13.0.

---

## PROCESS TELLS — 14 May 2026 (Phase 2b-ii session)

- **Empty-insiders diagnostic error.** Pre-commit P21 check accidentally passed `[]` instead of `_SYNTHETIC_INSIDERS`, producing SS07 composite=35.8 (insider=50 neutral) instead of the correct 28.0 (insider=0 from sellers). This led to an overstated pre-computation — SS07 appeared to route SELL not WEAK_HOLD under new weights. The actual issue was narrower (SS07 at 28.0 → WEAK_HOLD, not SELL). Lesson: diagnostic scripts must use the same input fixtures as the test. Always verify the fixture being passed before trusting the output.

- **P21 STOP condition fired correctly.** SS07 under new 1.60-sum weights with all-neutral enrichment data (28.0 > 25 threshold) was caught before committing the snapshot. Option A (add enrichment data for SS07) was chosen over Option B (adjust base screener inputs) — the enrichment path exercises the new scorers and is more realistic.

---

## STILL OPEN

- **Scheduler restart:** Phase 2b-ii scorers are on disk but the scheduler at PID 1867 is running Phase 2a code. Next time the scheduler is restarted, it will pick up v0.13.0 scoring with all 5 new enrichment paths.
- **Push to remote:** 5 Phase 2b-ii commits on local main. Push window TBD when Mark is ready.
- **Yahoo cron verification:** Check `external_scrape_log` and `earnings_history` / `analyst_changes` tables for first overnight cron data (02:00 / 02:15 BST 15 May 2026).
- **Phases 2c, 2d, 2e, 2f** queued per programme plan (flag substrate, rendering, end-to-end verification).
- **TEST ISOLATION REFACTOR** — see STRUCTURAL DEBT in PROJECT_CONTEXT.md.

---

## NOTES FOR FRESH-CHAT ATHENA

- Read PROJECT_CONTEXT.md first (stable), then this HANDOFF for current state.
- Phase 2b-ii is fully shipped. All 5 commits on local main, unpushed.
- First action if continuing: verify Yahoo overnight cron. `sqlite3 data/trading_system.db "SELECT data_type, COUNT(*), MAX(last_success_at) FROM external_scrape_log GROUP BY data_type;"` — look for ANALYST and EARNINGS rows dated 2026-05-15.
- The snapshot test now exercises all 4 enrichment paths via SS07 synthetic data. It is a "change only when you mean to" artefact — do not update it unless scoring logic intentionally changes.
- `signals/scorer.py` enrichment scorer functions are at lines ~295–525. `compute_composite` is at ~573. `score_all_tickers` is at ~680.

---

*End handoff.*
