# SIGNALINTEL: HANDOFF

**Tactical session state.** Updated end of each session. For stable
project context (who/what/how), see `PROJECT_CONTEXT.md`.

Last updated: 14 May 2026, end of session (Phase 2b-i shipped).
Next session: Phase 2b-ii: 5 new scorer functions + composite rebalance + version bump. FRESH CHAT recommended (large scoring session).

---

## JUST SHIPPED -- 14 May 2026 (Phase 2b-i: substrate refactor)

### Tail-end Phase 2a cleanup (no commits)

- Yahoo benchmark residue cleared from all 5 tables: `analyst_changes` (4,833 rows), `financial_statements` (4,214 rows), `institutional_holders` (50 rows), `earnings_history` (20 rows), `external_scrape_log` (20 rows). All rows dated 2026-05-14T06:18 UTC benchmark window. No post-07:29 rows existed. Tables now empty, waiting for first scheduled cron.
- Backup file `data/trading_system.db.backup_pre_vacuum_20260513_064920` (363MB) deleted from filesystem. File was never git-tracked; no commit possible or needed.

### New module (commit c7b7dc1)

- `signals/line_item_keys.py`: canonical snake_case vocabulary mapping raw yfinance PascalCase strings to canonical names. Scorer functions reference this module's constants; if yfinance renames a field, only this file needs updating.
- 12 INCOME_KEYS, 15 BALANCE_KEYS, 7 CASHFLOW_KEYS. Keys verified against yfinance 1.2.0 AAPL output 14 May 2026.
- `common_stock_equity` intentionally absent (not present in yfinance 1.2.0 output).
- PIOTROSKI_LOOKUPS (9 entries): all line items for the 9 binary Piotroski F-Score signals.
- ALTMAN_LOOKUPS (6 entries): Altman Z-Score formula. X4 uses `TotalLiabilitiesNetMinorityInterest` (classic Altman formula), NOT `TotalDebt`. `total_debt` stays in BALANCE_KEYS for future use but is not in ALTMAN_LOOKUPS.

### Rename (commit 28c5fcf)

- `screener_rows` → `ticker_data_rows` across 4 files: `main.py` (6 lines), `signals/scorer.py` (2 lines), `signals/scanner.py` (12 lines), `signals/target_price.py` (2 lines). 22 lines total.
- `insert_screener_rows` (DB helper function name for writing to `screener_snapshots`) intentionally unchanged — different concept.
- Post-rename absence grep confirms zero remaining `screener_rows` variable references.

### Signature extension (commit babebb3)

- `score_all_tickers` extended with 4 no-op kwargs for Phase 2b-ii: `earnings_map`, `financials_map`, `inst_own_map`, `analyst_mom_map`. All default None with `or {}` pattern inside function body. Not consumed by any scoring logic yet; Phase 2b-ii diff will be purely additive.

### Snapshot test (commits 386a745, 68fe8b6)

- New file `tests/test_scorer_snapshot.py`: behaviour-preservation snapshot for `score_all_tickers`. 14 synthetic tickers covering all 7 rating tiers (STRONG_BUY through STRONG_SELL), 3 legal rendering states (MINOR penalty / NONE explicit / absent), 3 sector modifier paths (HighSector 60, LowSector 40, NeutralSector 50), 1 all-NULL P5 ticker.
- Asserts `composite_score_raw`, `composite_score`, `rating`, `legal_penalty`, `sector_modifier_applied` per ticker to 1dp.
- SS07 rebuilt mid-session: original inputs (`rsi_14=28`, `low_52w_pct=5`) produced `reversion_score=78` which tripped the HOLD branch before STRONG_SELL. Rebuilt with `rsi_14=58`, `low_52w_pct=45` → `reversion_score=15` → STRONG_SELL correctly (composite 18.0). Diagnosis B (no bug in `assign_rating`, synthetic data quirk).
- WH14 added for previously missing WEAK_HOLD coverage: composite 31.9, insider_score 34.0 (CFO sell), sector neutral. Verified WEAK_HOLD fires correctly (composite < 38 AND insider <= 35).
- Snapshot baseline regenerated post-patch. Test passes.

### Test count

- pytest: 203 passing, 4 Yahoo freshness skipped (tables still empty, correct behaviour).
- Prior count was 202 (206 Phase 2a count − 4 Yahoo freshness that now correctly skip). +1 snapshot test.

### Commits (5 total, local main, unpushed)

```
c7b7dc1 feat(scorer): add line_item_keys.py canonical vocabulary module
28c5fcf refactor(scorer): rename screener_rows to ticker_data_rows
babebb3 feat(scorer): add Phase 2b-ii enrichment kwargs (no consumption)
386a745 test(scorer): add snapshot test for behaviour preservation
68fe8b6 test(scorer): patch snapshot coverage — fix SS07 STRONG_SELL routing, add WH14 WEAK_HOLD
```

Combined with 9 Phase 2a commits, 14 commits sit on local main unpushed.

**SCORING_ENGINE_VERSION unchanged at 0.12.0** (substrate-only refactor, no scoring logic changed, no version bump warranted).

---

## CURRENT STATE (end of 14 May 2026)

- Scheduler PID 1867 running on Phase 2a code since 07:29 BST 14 May. Phase 2b-i commits are on disk but scheduler has not been restarted (substrate refactor is not scoring-live until Phase 2b-ii adds scorer functions).
- 5 Phase 2b-i commits + 9 Phase 2a commits on local main, not yet pushed.
- 5 Yahoo data tables empty, waiting for first scheduled cron: tonight 02:00 BST (analyst priority) and 02:15 BST (earnings priority).
- pytest: 203 passing, 4 Yahoo freshness skipped.
- SCORING_ENGINE_VERSION: 0.12.0. Bump to 0.13.0 happens in Phase 2b-ii after composite rebalance.
- Backup file deleted, 363MB reclaimed, DB at ~328MB.
- `signals/line_item_keys.py` in place. PIOTROSKI_LOOKUPS and ALTMAN_LOOKUPS ready for Phase 2b-ii.

---

## PROCESS TELLS -- 14 May 2026 (Phase 2b-i session)

- **Snapshot coverage gap caught at gate-walk, not in CC's audit output.** CC implemented the 12-15 ticker profile coverage matrix from the locked spec, all 7 rating tiers nominally assigned, but SS07 (`rsi_14=28`, `low_52w_pct=5`) produced `reversion_score=78` which tripped the `reversion >= 75` HOLD branch before the `composite < 25 AND insider <= 20` STRONG_SELL branch. Diagnosis B confirmed: no bug in `assign_rating`, the synthetic inputs for a "deep bearish" ticker were inadvertently perfect for the reversion scorer. Patched mid-session. Lesson: when a Phase 2 prompt locks a profile coverage matrix, the verification gate must require empirical confirmation that each matrix row is represented with the expected rating, not just that the total ticker count matches. P21 codified.

- **Two-cleanup-prompts-instead-of-one was over-ceremony.** Mark pushed back on the Phase 2a tail-end cleanup being drafted as two sequential prompts (audit prompt → DELETE prompt). Collapsed to a single audit-and-DELETE prompt with embedded self-check; finished cleanly in 10 minutes. Lesson: Phase 1 + Phase 2 rigour earns its weight on substrate refactors, schema migrations, scoring logic. It is over-ceremony on housekeeping (file deletions, table truncations, residue cleanups). Rule codified: refactor / scoring / schema = two-turn; housekeeping / one-off DELETEs / file removals = single-turn with self-check.

- **Date-blindness as a failure mode (both sides).** During the morning scheduler-state check, Athena read "scheduler dead" from empty pgrep output without sanity-checking the date stamp on the log file. CC's first reply assumed "today is 15 May" from conversation context priming. Both corrected by Mark explicitly stating the date. P22 codified: any session involving "yesterday / today / tomorrow / overnight" temporal reasoning requires grounding on the actual date at session start.

- **Mark's communication preference locked mid-session.** Athena was over-explaining prompt construction rationale, surfacing architectural questions, and walking through diagnostic reasoning. Mark explicitly redirected: he's not technical, he wants Athena to make the calls and tell him outcome + next prompt, briefly. Replies: outcome, single recommendation, next prompt. No meta-notes on prompt design, no "two options to surface," no process lessons mid-flow. Process lessons land in HANDOFF / PROJECT_CONTEXT at session close. Memory updated.

---

## STILL OPEN

- **Phase 2b-ii (next session, FRESH CHAT recommended — large session):** 5 new scorer functions (Earnings Surprise, Piotroski F-Score, Altman additive penalty, Institutional Ownership, Analyst Momentum), composite weight rebalance (1.10 → 1.60 sum, normalised), SCORING_ENGINE_VERSION bump 0.12.0 → 0.13.0, new unit tests for each scorer, snapshot baseline regeneration with new components. `signals/line_item_keys.py` PIOTROSKI_LOOKUPS and ALTMAN_LOOKUPS already in place.
- **Altman Z-Score tiers (locked):** Z >= 3.0 = 0, 1.8 <= Z < 3.0 = -10, Z < 1.8 = -30, Z < 0 = -60.
- **Phase 2b-ii prerequisite — Yahoo cron verification:** first action of next session must be verifying tonight's 02:00 / 02:15 BST Yahoo cron ran cleanly. Query `external_scrape_log` for `last_success_at > '2026-05-15T00:00'` and check the scheduler log for JOB START / JOB DONE envelope. If silent failure, characterise and fix before any Phase 2b-ii implementation proceeds.
- **Phase 2b-ii timing dependency:** Sunday 04:00 BST = first bulk `institutional_holders` run. Monday 04:00 BST = first bulk `financial_statements` run. Tuesday 04:00 BST = first bulk `earnings_history` (full historical) run. Phase 2b-ii scorers need these tables populated. The later in the week the next session runs, the more data will be available.
- **Push to remote:** 14 commits (9 Phase 2a + 5 Phase 2b-i) on local main. Push window TBD when Mark is ready.
- **Phases 2c, 2d, 2e, 2f** queued per programme plan (flag substrate, rendering, end-to-end verification).

---

## NOTES FOR FRESH-CHAT ATHENA (Phase 2b-ii)

- Read PROJECT_CONTEXT.md first (stable), then this HANDOFF for current state.
- Phase 2b-ii is a LARGE session: 5 new scorers + composite rebalance + version bump + tests + snapshot regeneration. Plan accordingly.
- First action: verify tonight's Yahoo cron ran. `sqlite3 data/trading_system.db "SELECT data_type, COUNT(*), MAX(last_success_at) FROM external_scrape_log GROUP BY data_type;"` — should show rows for ANALYST and EARNINGS dated 15 May 2026.
- The snapshot baseline in `tests/test_scorer_snapshot.py` will need updating in Phase 2b-ii (new components shift scores). This is expected and intentional — update it after all 5 scorer functions are wired in, using the same regeneration script pattern as Phase 2b-i Step 4a. The snapshot test is not a "do not change" artefact; it's a "change only when you mean to" artefact.
- The `score_all_tickers` signature already has 4 no-op kwargs (`earnings_map`, `financials_map`, `inst_own_map`, `analyst_mom_map`) — Phase 2b-ii's diff is purely additive within the existing function body.
- Composite weight rebalance target: from 1.10 current (momentum 0.35, quality 0.30, insider 0.25, reversion 0.10, volume 0.10) to 1.60 total with 5 new components added. Normalisation in `compute_composite` handles any total_w, so adding weights is safe.
- The flag system (Phases 2d/2e) is NOT touched in Phase 2b-ii. Short Squeeze waits.

---

*End handoff.*
