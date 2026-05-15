# SIGNALINTEL: HANDOFF

**Tactical session state.** Updated end of each session. For stable
project context (who/what/how), see `PROJECT_CONTEXT.md`.

Last updated: 15 May 2026, end of session (Phase 2a/2b/2c complete, site live, gunicorn under LaunchAgent).
Next session: Scheduler LaunchAgent (30 min, dependency-free), or SB01 snapshot investigation, or Yahoo data verification. FRESH CHAT recommended.

---

## JUST SHIPPED — 15 May 2026 (Phase 2a/2b/2c: production hardening, tunnel deployment, path migration)

### Phase 2c (2 commits, pushed — chronological order, oldest first)

**Commit ab8eca1** — `chore(gitignore): untrack __pycache__ and .DS_Store, add to .gitignore`

- Removed 10 tracked cpython-314 .pyc files and web/.DS_Store from git index via `git rm --cached`.
- .gitignore was NOT modified — all three patterns (__pycache__/, *.pyc, .DS_Store) were already present before this commit. The commit subject line is slightly misleading; no .gitignore content change occurred. Verified via `git show ab8eca1 -- .gitignore` (empty diff).
- Discovered during Phase 2c rsync (excluded __pycache__/ and .DS_Store from rsync, causing git status to report them as deletions).

**Commit 7eb0899** — `chore(paths): update absolute paths from ~/Documents/trading-system to ~/signalintel`

- 5 one-off legal-risk migration scripts + CLAUDE.md updated via sed.
- No production code changes — production code already used relative paths or os.path.expanduser.

**Phase 2c migration (no code commits, operational only):**

- rsync from ~/Documents/trading-system/ to ~/signalintel/ (venv excluded).
- Venv recreated at ~/signalintel/venv; pip install -r requirements.txt clean.
- pytest from new path: 233 passing, 2 skipped, 1 pre-existing SB01 failure (unchanged).
- Gunicorn LaunchAgent generated via Python plistlib → ~/Library/LaunchAgents/io.thesignalvault.gunicorn.plist.
- LaunchAgent loaded and verified: PID 26090, exit code 0, both curls 200.
- Old path renamed: ~/Documents/trading-system → ~/Documents/trading-system.OLD (retain until 16 May 16:49 BST).
- Scheduler restarted from new path: PID 25975, all 19 jobs registered.

### Phase 2a — Flask production hardening (6 commits, pushed — chronological order, oldest first)

| Commit | Subject |
|---|---|
| `3b5b2a0` | feat(web): move FLASK_SECRET_KEY to settings.py from hardcoded source |
| `6d9fb1b` | feat(web): add ProxyFix middleware for Cloudflare Tunnel HTTPS termination |
| `a1efc9c` | feat(web): harden session cookies for HTTPS-only with SameSite=Lax |
| `a155353` | feat(deps): add gunicorn for production WSGI serving |
| `4836788` | feat(web): add login rate limiting (10/min on POST /login) |
| `bd31b99` | chore(web): set debug=False in __main__ block (gunicorn bypasses but hygiene) |

Gate 7 failure root cause: in-memory flask-limiter state is per-worker process. Multi-worker gunicorn distributes requests across workers, each with its own counter, so 10 requests never hit threshold on any single worker. Fix: `-w 1` for private beta. Redis upgrade path for production scale.

### Phase 2b — Cloudflare Tunnel deployment (no code commits, operational only, 15 May 2026)

- cloudflared installed via Homebrew (/opt/homebrew/bin/cloudflared).
- Named tunnel `signalintel`, UUID `6bc7b651-9255-4c50-8d70-6f5e6175930f`.
- Credentials: `/etc/cloudflared/6bc7b651-9255-4c50-8d70-6f5e6175930f.json` (root-owned, 400).
- Config: `/etc/cloudflared/config.yml` (ingress: apex + www → localhost:5001, catch-all 404).
- GoDaddy nameservers swapped to Cloudflare (anahi.ns.cloudflare.com + craig.ns.cloudflare.com). DNSSEC disabled at GoDaddy before swap.
- DNS propagation: ~75 minutes (GoDaddy typical). Confirmed via `dig +short NS thesignalvault.io @1.1.1.1`.
- cloudflared installed as system LaunchDaemon: `/Library/LaunchDaemons/com.cloudflare.cloudflared.plist`.
- Lesson: `sudo cloudflared service install` installs a plist that omits `tunnel run` args; fixed by rewriting plist manually.
- End state: four edge connections to London (lhr10/13/13/18). thesignalvault.io live over HTTPS.

### Prior Phase 2b-ii (5 commits, pushed 14 May 2026)

See previous HANDOFF for full detail. In brief: 5 Yahoo enrichment scorers (earnings_surprise, piotroski, inst_own, analyst_mom, altman_penalty), 9-component composite rebalanced to 1.60-sum, SCORING_ENGINE_VERSION → 0.13.0, snapshot test regenerated. First v0.13.0 production run: 10,807 tickers, 14:19 BST 14 May 2026.

---

## CURRENT STATE (end of 15 May 2026)

- **Project root:** ~/signalintel
- **Gunicorn:** LaunchAgent PID 26090, exit code 0. ~/signalintel/venv/bin/gunicorn -w 1 -b 127.0.0.1:5001. Logs: ~/signalintel/logs/gunicorn.{out,err}.log. Survives logout and reboot.
- **Scheduler:** PID 25975, foreground nohup process. Survives logout (reparented to PID 1) but NOT reboot. Log: ~/signalintel/logs/scheduler.log.
- **cloudflared:** System LaunchDaemon PID 25042 (root). /etc/cloudflared/config.yml. Survives reboot.
- **Site:** https://thesignalvault.io — HTTP/2 200, verified 17:30 BST 15 May 2026.
- **SCORING_ENGINE_VERSION:** 0.13.0
- **pytest:** 233 passing, 2 skipped (Yahoo freshness — data landing), 1 failing (SB01 pre-existing). Total 236 tests.
- **Last signal score:** 2026-05-15 16:39 BST (startup job from new-path scheduler boot).
- **Last screener snapshot:** 2026-05-15 11:50 (16:30 window missed due to migration; next window 16 May 07:00).
- **Git:** 0 commits ahead of remote. All pushed. HEAD: `647794e`.
- **Old path:** ~/Documents/trading-system.OLD — retain until 16 May 2026 16:49 BST.

---

## PROCESS TELLS — 15 May 2026

**Plist XML in heredocs eaten by chat renderer (P26 codified).**
Three rounds of gunicorn LaunchAgent plist heredocs all arrived in Mark's terminal missing the `-w` flag. The `<string>-w</string>` XML tag was being parsed as an HTML attribute by the chat UI and stripped on copy. Dead giveaway: CC's "expected output" table mentioned `-w` while the heredoc below it did not. Fix: Python plistlib to generate plists programmatically. PlistBuddy on disk for verification. Applies to any XML-in-markdown workflow, not just plists.

**macOS TCC blocks launchd processes from ~/Documents/ (P25 codified).**
Even after granting Full Disk Access to /sbin/launchd in System Settings, the LaunchAgent failed with `PermissionError: [Errno 1] Operation not permitted: '/Users/markn/Documents/trading-system/venv/pyvenv.cfg'`. TCC scopes protection per-path, not per-process-owner. The FDA grant to launchctl doesn't propagate to child processes reading TCC-protected paths. Fix: move project out of ~/Documents/. ~90 minutes diagnosis time; future projects default to ~/project-name, not ~/Documents/project-name.

**CC's "incomplete fix" pattern.**
CC's first proposal was to move only the venv to a non-protected path. Technically correct framing ("venv is a build artefact") but missed that gunicorn also needs to read web/app.py, config/settings.py, and the 374MB DB from the project root — all still under ~/Documents/. Phase 1 inventory ("what does the process need to read at runtime?") would have caught the full surface area upfront.

**Context compaction can replay completed work.**
After context compaction mid-session, CC suggested proceeding with "Step 11 LaunchAgent load" — work already completed and verified (PID 26090, exit code 0). Had Mark run CC's commands, the already-loaded LaunchAgent would have errored. Mitigation: after compaction, explicitly re-anchor CC with current empirical state before accepting any suggestion. "Session state is empirical" extends P22 (date is empirical) to the broader principle.

---

## STILL OPEN

- **Delete ~/Documents/trading-system.OLD** — after 16 May 2026 16:49 BST. Verify site still stable first: `curl -sI https://thesignalvault.io/login | head -2` and `launchctl list | grep gunicorn`.
- **Scheduler LaunchAgent** — still a foreground nohup process (PID 25975). Does not survive reboot. ~30 min work, dependency-free. See FOLLOWUPS: STRUCTURAL DEBT.
- **SB01 snapshot mismatch** — `expected 76.6, got 74.7`. Pre-existing since 14 May. Needs focused diagnostic. See FOLLOWUPS: STRUCTURAL DEBT.
- **Test count drift** — 233+2 vs expected 231+4. Two Yahoo freshness tests transitioned from skip to pass. Verify which tables have data now. See FOLLOWUPS: STRUCTURAL DEBT.
- **Tonight's Yahoo crons (02:00 ANALYST / 02:15 EARNINGS, 16 May 2026 BST):** Verify: `sqlite3 ~/signalintel/data/trading_system.db "SELECT data_type, COUNT(*), MAX(last_success_at) FROM external_scrape_log GROUP BY data_type;"`
- **Sunday 18 May — institutional_holders bulk job:** Same query + `SELECT COUNT(*) FROM institutional_holders;`
- **Monday 19 May — financial_statements bulk job:** Same query + `SELECT COUNT(*) FROM financial_statements;`
- **Tuesday 20 May — earnings_history bulk job:** Same query + `SELECT COUNT(*) FROM earnings_history;`
- **Altman Z distribution check** — actionable once financial_statements data lands (Monday). See FOLLOWUPS: URGENT.
- **0 commits ahead of remote.** Everything pushed.

---

## NOTES FOR FRESH-CHAT ATHENA

- Read PROJECT_CONTEXT.md first (stable), then this HANDOFF for current state.
- **Project now at ~/signalintel** — not ~/Documents/trading-system. All references updated. Old path at ~/Documents/trading-system.OLD (delete after 16 May 16:49 BST).
- **Gunicorn under LaunchAgent** (PID 26090) — survives reboot. **Scheduler not** (PID 25975, nohup) — does not survive reboot. Symmetric LaunchAgent treatment for scheduler is STRUCTURAL DEBT.
- Phase 2a/2b/2c fully shipped and live. v0.13.0, 233 tests passing (2 skipped, 1 pre-existing SB01 failure).
- First action if continuing Yahoo enrichment: verify overnight cron data. Query in STILL OPEN above.
- SB01 snapshot failure pre-exists this session (first seen 14 May). It is not a regression from migration.
- Plist generation must use Python plistlib — not XML heredocs (P26). PlistBuddy verification before installing.
- New projects/services: default to ~/project-name paths, never ~/Documents/ (P25, TCC lesson).
- Phone Chrome cache issues during the Phase 2b/2c deployment session caused intermittent "site can't be reached" and login failures for ~1 hour, resolved by clearing Chrome cache and cookies. Not a deployment issue. Worth knowing if Guy or future testers report similar.

---

*End handoff.*
