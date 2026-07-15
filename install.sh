#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"

MODE=symlink
DO_CLAUDE=auto
DO_CODEX=auto
DO_GEMINI=auto
FORCE=0
DRY_RUN=0
STAMP="$(date +%Y%m%d-%H%M%S)"

usage() {
  cat <<'EOF'
Usage: ./install.sh [options]

  --copy          Copy files instead of creating symbolic links.
  --claude-only   Install only for Claude Code.
  --codex-only    Install only for Codex.
  --gemini-only   Install only for Gemini CLI.
  --no-gemini     Skip Gemini CLI.
  --force         Back up an existing target before installation.
  --dry-run       Print actions without changing files.
  -h, --help      Show this help.
EOF
}

# Usage: ./install.sh [options]
#
#   --copy          Copy files instead of creating symbolic links.
#   --claude-only   Install only for Claude Code.
#   --codex-only    Install only for Codex.
#   --gemini-only   Install only for Gemini CLI.
#   --no-gemini     Skip Gemini CLI.
#   --force         Back up an existing target before installation.
#   --dry-run       Print actions without changing files.
#   -h, --help      Show this help.

while [ "$#" -gt 0 ]; do
  case "$1" in
    --copy) MODE=copy ;;
    --claude-only) DO_CLAUDE=yes; DO_CODEX=no; DO_GEMINI=no ;;
    --codex-only) DO_CLAUDE=no; DO_CODEX=yes; DO_GEMINI=no ;;
    --gemini-only) DO_CLAUDE=no; DO_CODEX=no; DO_GEMINI=yes ;;
    --no-gemini) DO_GEMINI=no ;;
    --force) FORCE=1 ;;
    --dry-run) DRY_RUN=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
  shift
done

run() {
  printf '+ '
  printf '%q ' "$@"
  printf '\n'
  if [ "$DRY_RUN" -eq 0 ]; then
    "$@"
  fi
}

install_one() {
  local source="$1"
  local target="$2"
  run mkdir -p "$(dirname "$target")"
  if [ -L "$target" ] && [ "$(readlink "$target")" = "$source" ]; then
    echo "Already installed: $target"
    return 0
  fi
  if [ -e "$target" ] || [ -L "$target" ]; then
    if [ "$FORCE" -ne 1 ]; then
      echo "Refusing to replace existing target: $target (use --force)" >&2
      return 1
    fi
    run mv "$target" "$target.bak.$STAMP"
  fi
  if [ "$MODE" = copy ]; then
    run cp -RL "$source" "$target"
  else
    run ln -s "$source" "$target"
  fi
  if [ "$DRY_RUN" -eq 1 ]; then
    echo "Planned: $target"
  else
    echo "Installed: $target"
  fi
}

if [ "$DO_CLAUDE" != no ] && { [ "$DO_CLAUDE" = yes ] || command -v claude >/dev/null 2>&1; }; then
  echo "== Claude Code =="
  install_one "$REPO/.claude/skills/humanize-japanese" "$CLAUDE_HOME/skills/humanize-japanese"
  install_one "$REPO/.claude/skills/humanize" "$CLAUDE_HOME/skills/humanize"
  install_one "$REPO/.claude/skills/humanize-redo" "$CLAUDE_HOME/skills/humanize-redo"
  for agent in "$REPO"/agents/*.md; do
    install_one "$agent" "$CLAUDE_HOME/agents/$(basename "$agent")"
  done
else
  echo "== Claude Code: skipped =="
fi

if [ "$DO_CODEX" != no ] && { [ "$DO_CODEX" = yes ] || command -v codex >/dev/null 2>&1; }; then
  echo "== Codex =="
  install_one "$REPO/codex/skills/humanize-japanese" "$CODEX_HOME/skills/humanize-japanese"
else
  echo "== Codex: skipped =="
fi

if [ "$DO_GEMINI" != no ] && { [ "$DO_GEMINI" = yes ] || command -v gemini >/dev/null 2>&1; }; then
  echo "== Gemini CLI =="
  if [ "$DRY_RUN" -eq 1 ]; then
    echo "+ gemini extensions link $REPO"
  else
    gemini extensions link "$REPO"
  fi
else
  echo "== Gemini CLI: skipped =="
fi

echo "Done. Claude: /humanize-japanese | Codex: \$humanize-japanese | Gemini: /humanize-japanese"
