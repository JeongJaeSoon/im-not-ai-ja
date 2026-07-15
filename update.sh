#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHECK_ONLY=0
INSTALL_ARGS=()

for argument in "$@"; do
  case "$argument" in
    --check) CHECK_ONLY=1 ;;
    -h|--help)
      echo "Usage: ./update.sh [--check] [install.sh options]"
      exit 0
      ;;
    *) INSTALL_ARGS+=("$argument") ;;
  esac
done

git -C "$REPO" rev-parse --is-inside-work-tree >/dev/null
upstream="$(git -C "$REPO" rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)"
if [ -z "$upstream" ]; then
  echo "No upstream branch is configured." >&2
  exit 2
fi

remote="${upstream%%/*}"
git -C "$REPO" fetch --quiet "$remote"
local_revision="$(git -C "$REPO" rev-parse HEAD)"
remote_revision="$(git -C "$REPO" rev-parse "$upstream")"

if [ "$local_revision" = "$remote_revision" ]; then
  echo "Already up to date."
  exit 0
fi

base="$(git -C "$REPO" merge-base HEAD "$upstream")"
if [ "$base" != "$local_revision" ]; then
  echo "Local and upstream histories have diverged; update manually." >&2
  exit 1
fi

echo "Update available: $(git -C "$REPO" rev-list --count "HEAD..$upstream") commit(s)."
if [ "$CHECK_ONLY" -eq 1 ]; then
  exit 10
fi

git -C "$REPO" pull --ff-only
"$REPO/install.sh" "${INSTALL_ARGS[@]}"
