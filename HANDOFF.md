# SIGNALINTEL: HANDOFF

**Tactical session state.** Updated end of each session. For stable
project context (who/what/how), see `PROJECT_CONTEXT.md`.

Last updated: 15 May 2026, end of session (Yahoo verification, venv rebuild, SB01 fix, scheduler LaunchAgent — all shipped and pushed).
Next session: Sunday 17 May overnight bulk-job verification, then Phase 2c direction lock. FRESH CHAT recommended.

---

## JUST SHIPPED — 15 May 2026

### Yahoo overnight cron verification (read-only, no commits)

First post-deployment verification of the Phase 2b-i Yahoo enrichment crons. Both priority crons fired cleanly from the new ~/signalintel path overnight 14→15 May:

- Yahoo Analyst Changes (02:00 BST): 13.2s, 903 rows into analyst_changes
- Yahoo Earnings Priority (02:15 BST): 21.5s, 60 rows into earnings_history

No errors in external_scrape_log. Bulk-job tables (institutional_holders, financial_statements, earnings_history bulk) remain empty pending their Sun/Mon/Tue runs. Closed via Phase 1 + Phase 1-follow-up diagnostic round.

**Corrections to 14 May HANDOFF surfaced during verification:**
- `yahooquery_raw` table does not exist. The 14 May HANDOFF listed it as one of five Phase 2b-i enrichment tables. There are four. Empirical grep returned zero references across .py, .md, .sql files. Either planned-but-never-implemented or a name discarded before any code was written.
- `last_error_at` column does not exist on external_scrape_log. Actual column is `last_error`. Empirical grep returned zero references in code. No silent NULL risk.

### SB01 snapshot baseline correction (commit 0290c10, pushed)

tests/test_scorer_snapshot.py had been failing since commit 48fdf49 (14 May). Phase 1 diagnostic confirmed the scorer was producing the correct v0.13.0 output for SB01 (74.7), but EXPECTED_SNAPSHOT was set to 76.6 — a value that does not match any coherent combination of SB01's inputs and the v0.13.0 weight table.

Arithmetic confirmation: 100×0.35 + 100×0.30 + 86×0.25 + 0×0.10 + 80×0.10 + 50×0.125×4 = 119.5; 119.5 / 1.60 = 74.6875 → 74.7.

One-line fix: EXPECTED_SNAPSHOT["SB01"] composite_score_raw and composite_score updated from 76.6 to 74.7. No scorer change, no version bump, no other fixture rows touched. P16 held: trusted the arithmetic over the recorded baseline.

### Venv rebuild (no commit — environment-only)

The ~/signalintel/venv was broken since the 14 May ~/Documents/trading-system → trading-system.OLD rename. python3 symlinked to the dead path; pyvenv.cfg home pointed there too. Gunicorn PID 26090 and scheduler PID 25975 were running on in-memory CLT Python interpreters and would survive until exit but could not restart.

Rebuild sequence:
1. mv venv → venv.OLD (preserved, not deleted)
2. New venv from /Library/Developer/CommandLineTools/usr/bin/python3 (3.9.6, same as before)
3. pip install -r requirements.txt — clean, all 18 declared packages plus deps
4. pytest: 234 passing, 2 skipped (financial_statements + institutional_holders empty, expected), 0 failures. SB01 fix verified before commit.
5. SB01 commit landed (0290c10)
6. launchctl kickstart -k gunicorn → new PIDs 30323/30326, lsof confirms CLT Python and ~/signalintel cwd
7. Kill nohup scheduler 25975, nohup new one against venv/bin/python → PID 30476, banner shows v0.13.0 and HEAD 0290c10
8. curl https://thesignalvault.io → HTTP/2 302 to /login (site live)

venv.OLD left in place at ~/signalintel/venv.OLD. Delete after a few days of healthy operation.

### Scheduler LaunchAgent (no commit — system config)

Closed the asymmetry: gunicorn under LaunchAgent (reboot-resilient, crash-recoverable), scheduler under bare nohup (neither). Created io.thesignalvault.scheduler at ~/Library/LaunchAgents/, generated via plistlib (not heredoc XML).

Locked design, with rationale where it deviates from gunicorn's plist:

| Key | Value | Notes |
|---|---|---|
| Label | io.thesignalvault.scheduler | Matches gunicorn naming |
| ProgramArguments | ["~/signalintel/venv/bin/python", "~/signalintel/main.py", "scheduler"] | Explicit python + script; no shebang wrapper |
| WorkingDirectory | /Users/markn/signalintel | Required — main.py uses relative paths |
| EnvironmentVariables PATH | /opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin | Matches gunicorn |
| RunAtLoad | true | Starts on login/reboot |
| KeepAlive | dict { SuccessfulExit: false } | Restart on crash, NOT on clean SIGTERM exit |
| StandardOutPath | logs/scheduler.out.log | Separate from trading_system.log to avoid double-write (main.py FileHandler already writes there) |
| StandardErrorPath | logs/scheduler.err.log | Catches Python tracebacks bypassing the logger |
| ThrottleInterval | 10 | Higher than gunicorn's 5; scheduler startup is heavier (~50s signal generation cold run) |
| ExitTimeOut | 90 | Default 20s would SIGKILL mid-job on launchctl unload. 90s lets scheduler.shutdown(wait=True) complete a worst-case ~50s signal generation cleanly. Diagnostic-noise mitigation, not data-corruption mitigation |
| UserName | markn | Matches gunicorn |

Empirical gates both proved (Step 6 + Step 8 of Phase 2):
- KeepAlive: SIGKILL on PID 31540 → launchd respawned within ThrottleInterval (10s), new PID 31885. Crash-recovery works.
- Clean shutdown: launchctl unload → SIGTERM → exit 0 → no respawn. SuccessfulExit=false logic works.

Stale log files deleted during install: scheduler.log (18KB, dead), scheduler_stdout.log (513KB, dead from earlier nohup sessions).

Final scheduler PID: 32257 (after load/unload/reload cycle).

---

## CURRENT STATE (end of 15 May 2026)

- gunicorn: PID 30323 under io.thesignalvault.gunicorn LaunchAgent
- scheduler: PID 32257 under io.thesignalvault.scheduler LaunchAgent
- venv: rebuilt on CLT Python 3.9.6 at /Library/Developer/CommandLineTools/usr/bin/python3, home set correctly in pyvenv.cfg
- venv.OLD: still present at ~/signalintel/venv.OLD, delete after healthy-operation window
- HEAD: 0290c10 — test(scorer): correct SB01 snapshot baseline from 76.6 to 74.7
- 0 commits ahead of remote, working tree clean (modulo SQLite WAL sidecar and venv.OLD/)
- pytest: 234 passing, 2 skipped (institutional_holders + financial_statements freshness checks awaiting bulk-job data)
- SCORING_ENGINE_VERSION: 0.13.0
- Yahoo enrichment tables: analyst_changes 903 rows, earnings_history 60 rows, three weekly bulk tables still empty pending Sun/Mon/Tue runs
- Site live: HTTP/2 302 via Cloudflare → /login

---

## PROCESS TELLS — 15 May 2026

- **Phase 1 + Phase 1-follow-up sequence on Yahoo verification.** Two short read-only diagnostic rounds beat one large one. First round confirmed crons fired and produced data, surfaced two open questions (yahooquery_raw, last_error_at). Follow-up grep round closed both empirically in 2 minutes. Cleaner than batching into a single multi-part prompt with branching gates.

- **P16 absolutism on SB01.** The snapshot recorded 76.6 with a "Do NOT modify — fix the refactor instead" comment. The arithmetic said 74.7. Trusting the arithmetic (not the comment, not the recorded baseline) was the right call. Future-Athena: comments asserting a value is correct do not make the value correct.

- **ExitTimeOut: 90 explicit note in HANDOFF.** Without this, future-Athena sees the number, doesn't know why it's not the launchd default 20s, and may second-guess. The line "ExitTimeOut: 90 lets scheduler.shutdown(wait=True) complete a worst-case ~50s signal generation cleanly" is the rationale, and the rationale belongs in HANDOFF, not in the plist as a comment (launchctl is picky about plist XML).

- **Venv rebuild Phase 1 inventory found zero project-code contamination.** Confirmed empirically before touching anything. Without that sweep we'd have been guessing whether a full rebuild was sufficient or whether other project-side path references needed cleanup. Phase 1 read-only diagnostics earn their weight on any environmental change with potential for hidden references.

- **CC discipline held cleanly across the day.** No scope drift, no negative-instruction failures, no doc edits. The venv rebuild (12-step Phase 2) and scheduler LaunchAgent install (8-step Phase 2) both ran end-to-end without stops. STOP-on-broken-venv at Gate 2 of the SB01 prompt was correctly observed (CC did the edit, hit the broken venv, stopped, reported — did not try to fix the venv mid-prompt).

- **Pre-existing CC plugin terminal noise.** Throughout the day every Bash tool call surfaced "Failed with non-blocking status code: /bin/sh: node: command not found" and "Bun not found" warnings. These are pre-tool / post-tool hook errors from the Superpowers plugin that was installed but not enabled in the project. Non-blocking, no functional impact, ignorable. Worth knowing about so future sessions don't waste time investigating.

- **Mid-session terminal-window confusion (caught early).** A paste from a different project (Betfair / greyhound stats) landed in the SignalIntel chat. Caught and discarded before any action. Adds nothing to process — just a reminder that the multi-terminal workflow has the risk surface of "right command, wrong window." Athena response should always be to demand a `pwd` + `git remote -v` confirmation before touching anything if the output looks unfamiliar.

---

## STILL OPEN

- **Sunday 17 May overnight — institutional_holders bulk job.** Verify `sqlite3 data/trading_system.db "SELECT COUNT(*) FROM institutional_holders;"` returns nonzero. Also check external_scrape_log for the corresponding data_type row.
- **Monday 18 May overnight — financial_statements bulk job.** Same verification pattern. AND triggers the Altman Z distribution check from URGENT FOLLOWUPS (compute Z-scores for tickers with 2+ years of financial_statements data, plot distribution, verify penalty tiers calibrated for this universe before v0.13.0 data accumulates).
- **Tuesday 19 May overnight — earnings_history bulk job.** Same verification pattern. earnings_history will then have both the priority-cron-fed rows and the bulk-fed rows.
- **venv.OLD deletion green-light.** Sitting at ~/signalintel/venv.OLD. Delete after ~72h of healthy operation on the rebuilt venv (so by Monday 18 May we can decide).
- **Phase 2c direction TBD.** Programme plan lists flag substrate, rendering, end-to-end verification. Decision lock needed on: which flags first, where flag substrate lives (DB vs in-flight from signal_scores), rendering surfaces. Blocked on Yahoo bulk data volume — flag logic is only useful once enrichment tables have enough rows to produce meaningful signals.
- **234 vs 232 tests reconciliation.** 14 May HANDOFF recorded 232 passing. 15 May venv rebuild verified 234. Two extras since then, worth a quick `git log tests/` next session to identify. Non-urgent.
- **HANDOFF correction queued:** the 14 May entry listed five Phase 2b-i enrichment tables; correct number is four. Either the next HANDOFF update absorbs this (this one) or the 14 May entry gets retroactively corrected. Captured here, no action needed.

---

## NOTES FOR FRESH-CHAT ATHENA

- Read PROJECT_CONTEXT.md first (stable), then this HANDOFF.
- Today's three substantive pieces of work: Yahoo verification (read-only, no commits), SB01 snapshot fix (commit 0290c10 pushed), venv rebuild (environment-only, no commits), scheduler LaunchAgent (system config, no commits).
- Both gunicorn and scheduler are now reboot-resilient under LaunchAgents. The Mac Mini can reboot and the platform self-heals.
- If continuing on Sunday: first action is the institutional_holders bulk-job verification query in STILL OPEN above. Run before anything else to bank or surface that result.
- If continuing on Monday: same pattern, plus the Altman Z distribution check is now actionable (it was queued from 14 May and gated on financial_statements data).
- The Superpowers plugin is installed in CC but not enabled. Athena flagged it as a candidate for Phase 2c implementation work or for the Altman Z distribution analysis. Re-evaluate when one of those sessions starts.
- venv.OLD still on disk. Don't delete without 72h+ confidence interval on the new venv.

---

*End handoff.*
