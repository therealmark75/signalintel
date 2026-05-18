#!/usr/bin/env bash
# Idempotent installer for the auth-adjacent pre-commit hook (P23).
# Creates .git/hooks/pre-commit as a symlink → scripts/git-hooks/pre-commit
# so updates to the tracked source take effect immediately.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
    echo "ERROR: not inside a git repository" >&2
    exit 1
}

SOURCE="$REPO_ROOT/scripts/git-hooks/pre-commit"
TARGET="$REPO_ROOT/.git/hooks/pre-commit"
RELATIVE="../../scripts/git-hooks/pre-commit"

if [[ ! -f "$SOURCE" ]]; then
    echo "ERROR: source hook not found at $SOURCE" >&2
    exit 1
fi

chmod +x "$SOURCE"

if [[ -L "$TARGET" ]]; then
    current_link="$(readlink "$TARGET")"
    if [[ "$current_link" == "$RELATIVE" || "$current_link" == "$SOURCE" ]]; then
        echo "pre-commit hook already installed"
        exit 0
    fi
    echo "WARNING: existing symlink points to '$current_link' — replacing"
    rm "$TARGET"
elif [[ -e "$TARGET" ]]; then
    backup="$TARGET.backup.$(date +%Y%m%d%H%M%S)"
    echo "WARNING: existing non-symlink file at $TARGET — backing up to $backup"
    mv "$TARGET" "$backup"
fi

ln -s "$RELATIVE" "$TARGET"

# Probe executable bit via the hook's defensive no-op branch.
"$TARGET" --self-test 2>/dev/null || true

echo "pre-commit hook installed → scripts/git-hooks/pre-commit"
