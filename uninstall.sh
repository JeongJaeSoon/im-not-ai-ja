#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
DRY_RUN=0

case "${1:-}" in
  --dry-run) DRY_RUN=1 ;;
  -h|--help) echo "Usage: ./uninstall.sh [--dry-run]"; exit 0 ;;
  "") ;;
  *) echo "Unknown option: $1" >&2; exit 2 ;;
esac

remove_link() {
  local target="$1"
  local source="$2"
  if [ -L "$target" ] && [ "$(readlink "$target")" = "$source" ]; then
    echo "+ rm $target"
    if [ "$DRY_RUN" -eq 0 ]; then
      rm "$target"
    fi
  elif [ -e "$target" ] || [ -L "$target" ]; then
    echo "Skipped (not this repository's link): $target"
  fi
}

remove_link "$CLAUDE_HOME/skills/humanize-japanese" "$REPO/.claude/skills/humanize-japanese"
remove_link "$CLAUDE_HOME/skills/humanize" "$REPO/.claude/skills/humanize"
remove_link "$CLAUDE_HOME/skills/humanize-redo" "$REPO/.claude/skills/humanize-redo"
remove_link "$CODEX_HOME/skills/humanize-japanese" "$REPO/codex/skills/humanize-japanese"

for agent in "$REPO"/agents/*.md; do
  remove_link "$CLAUDE_HOME/agents/$(basename "$agent")" "$agent"
done

echo "Done. Copy-mode installations and backups were not removed."
