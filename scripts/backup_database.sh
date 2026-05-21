#!/bin/bash
# SignalIntel — nightly DB backup.
#
# WAL-aware online backup of data/trading_system.db. Integrity-checked before
# being promoted to a dated filename. Rotated as 7 daily + 4 weekly (Sunday).
#
# Bash 3.2 compatible (system /bin/bash on macOS). No associative arrays,
# no mapfile. Keep-set tracked as a delimited string.
#
# Invariants enforced:
#   - A failed integrity_check NEVER overwrites an existing good backup.
#   - Rotation builds an explicit keep-set; only files NOT in the keep-set
#     get deleted. Filename pattern is strictly matched so unrelated files
#     in the backup dir are never touched.
#   - On any abnormal exit, the temp .partial file is removed via trap.

set -euo pipefail

SRC="$HOME/signalintel/data/trading_system.db"
DEST_DIR="$HOME/signalintel-backups"
STAMP="$(date -u '+%Y-%m-%d-%H%M')"
DEST_TMP="${DEST_DIR}/.trading_system-${STAMP}.db.partial"
DEST_FINAL="${DEST_DIR}/trading_system-${STAMP}.db"

DAILY_KEEP=7
WEEKLY_KEEP=4
PATTERN_GLOB='trading_system-*-*-*-*.db'
# Strict shell regex for date-part extraction (matches "trading_system-YYYY-MM-DD-HHMM.db")
STRICT_RE='^trading_system-([0-9]{4}-[0-9]{2}-[0-9]{2})-[0-9]{4}\.db$'

log()  { printf '[%s] %s\n'        "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*"; }
err()  { printf '[%s] ERROR: %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*" >&2; }

cleanup_tmp() { [ -f "$DEST_TMP" ] && rm -f -- "$DEST_TMP"; }
trap cleanup_tmp EXIT

if [ ! -f "$SRC" ]; then
    err "source DB not found: $SRC"
    exit 1
fi
mkdir -p "$DEST_DIR"

# ── 1) WAL-aware backup to temp ──────────────────────────────────────────────
if ! sqlite3 "$SRC" ".backup '${DEST_TMP}'"; then
    err "sqlite3 .backup failed (src=$SRC, tmp=$DEST_TMP)"
    exit 1
fi

# ── 2) Integrity check on the temp file ──────────────────────────────────────
# integrity_check returns the single string "ok" on success, or one+ rows of
# error text on failure. Anything other than literal "ok" → abort and prune temp.
result=$(sqlite3 "$DEST_TMP" 'PRAGMA integrity_check;' 2>&1) || result="sqlite3 exited non-zero"
if [ "$result" != "ok" ]; then
    err "integrity_check failed: $result"
    exit 1
fi

# ── 3) Atomic promotion → dated final ────────────────────────────────────────
if ! mv -- "$DEST_TMP" "$DEST_FINAL"; then
    err "atomic rename failed: $DEST_TMP → $DEST_FINAL"
    exit 1
fi
trap - EXIT  # temp is gone; no need to clean up
size=$(du -h "$DEST_FINAL" | cut -f1 || echo "?")
log "backup ok: $DEST_FINAL ($size)"

# ── 4) Rotation — explicit keep-set; everything else gets pruned ─────────────
#
# Keep-set construction:
#   DAILY_KEEP  = 7 most-recent files (by date encoded in filename)
#   WEEKLY_KEEP = 4 most-recent files whose date falls on a Sunday (ISO %u=7)
# A file is kept iff it appears in EITHER set. Everything else is pruned.
#
# bash 3.2 has no associative arrays — we track the keep-set as a delimited
# string and test membership with case matching. Pipe is the delimiter (safe
# because filenames contain no '|' under our naming).

# Enumerate matching files newest-first (filename embeds the date in sort order)
candidates=()
while IFS= read -r f; do
    [ -n "$f" ] && candidates+=("$f")
done < <(find "$DEST_DIR" -maxdepth 1 -type f -name "$PATTERN_GLOB" | sort -r)

KEEP="|"
add_keep() { KEEP="${KEEP}${1}|"; }
is_keep()  { case "$KEEP" in *"|$1|"*) return 0;; *) return 1;; esac; }

# DAILY set — top N most recent (strict pattern check on each, defensive)
daily_added=0
for f in "${candidates[@]:-}"; do
    [ -z "${f:-}" ] && continue
    [ "$daily_added" -ge "$DAILY_KEEP" ] && break
    base=$(basename -- "$f")
    if [[ "$base" =~ $STRICT_RE ]]; then
        add_keep "$f"
        daily_added=$((daily_added + 1))
    fi
done

# WEEKLY set — top N most recent Sunday backups
weekly_added=0
for f in "${candidates[@]:-}"; do
    [ -z "${f:-}" ] && continue
    [ "$weekly_added" -ge "$WEEKLY_KEEP" ] && break
    base=$(basename -- "$f")
    if [[ "$base" =~ $STRICT_RE ]]; then
        date_part="${BASH_REMATCH[1]}"
        dow=$(date -j -f "%Y-%m-%d" "$date_part" "+%u" 2>/dev/null || echo "")
        if [ "$dow" = "7" ]; then
            if ! is_keep "$f"; then
                add_keep "$f"
            fi
            weekly_added=$((weekly_added + 1))
        fi
    fi
done

# Prune — only files matching the strict pattern that are NOT in the keep-set
pruned_list=""
pruned_count=0
kept_count=0
for f in "${candidates[@]:-}"; do
    [ -z "${f:-}" ] && continue
    base=$(basename -- "$f")
    if [[ ! "$base" =~ $STRICT_RE ]]; then
        # filename did not match strict pattern — skip (defensive: never touch
        # files we don't recognise)
        continue
    fi
    if is_keep "$f"; then
        kept_count=$((kept_count + 1))
    else
        if rm -f -- "$f"; then
            pruned_list="${pruned_list}${base} "
            pruned_count=$((pruned_count + 1))
        else
            err "failed to remove: $f"
        fi
    fi
done

if [ "$pruned_count" -gt 0 ]; then
    log "rotation: kept=$kept_count pruned=$pruned_count [${pruned_list% }]"
else
    log "rotation: kept=$kept_count pruned=0"
fi

exit 0
