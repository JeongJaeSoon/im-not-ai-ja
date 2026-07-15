#!/usr/bin/env python3
"""Validate repository manifests and skill frontmatter without dependencies."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def validate_json(path: Path) -> None:
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"invalid JSON {path.relative_to(ROOT)}: {error}")


def validate_skill(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
    if not match:
        fail(f"missing frontmatter: {path.relative_to(ROOT)}")
    keys = []
    for line in match.group(1).splitlines():
        key_match = re.match(r"^([a-z_]+):", line)
        if key_match:
            keys.append(key_match.group(1))
    if keys != ["name", "description"]:
        fail(f"frontmatter must contain only name, description: {path.relative_to(ROOT)} ({keys})")
    name_match = re.search(r"^name:\s*([^\n]+)$", match.group(1), flags=re.MULTILINE)
    if not name_match or not re.fullmatch(r"[a-z0-9-]{1,63}", name_match.group(1).strip()):
        fail(f"invalid skill name: {path.relative_to(ROOT)}")


def main() -> int:
    required = [
        "README.md",
        "LICENSE",
        "NOTICE.md",
        ".claude-plugin/plugin.json",
        ".claude-plugin/marketplace.json",
        ".claude/skills/humanize-japanese/SKILL.md",
        ".claude/skills/humanize-japanese/references/ai-tell-taxonomy.md",
        ".claude/skills/humanize-japanese/references/register-guide.md",
        ".claude/skills/humanize-japanese/scripts/metrics.py",
        "codex/skills/humanize-japanese/SKILL.md",
    ]
    for relative in required:
        if not (ROOT / relative).exists():
            fail(f"missing required path: {relative}")
    for path in ROOT.rglob("*.json"):
        if ".git" not in path.parts:
            validate_json(path)
    for path in ROOT.rglob("SKILL.md"):
        validate_skill(path)
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if "epoko77-ai/im-not-ai" not in readme or "GitHub の fork 機能は使っていません" not in readme:
        fail("README attribution is missing")
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    if "Copyright (c) 2026 epoko77-ai" not in license_text:
        fail("upstream copyright is missing")
    taxonomy = (
        ROOT
        / ".claude"
        / "skills"
        / "humanize-japanese"
        / "references"
        / "ai-tell-taxonomy.md"
    ).read_text(encoding="utf-8")
    pattern_ids = re.findall(r"^\| ([A-I]-\d+) \|", taxonomy, flags=re.MULTILINE)
    guard_ids = re.findall(r"^\| (J-\d+) \|", taxonomy, flags=re.MULTILINE)
    if len(pattern_ids) + len(guard_ids) != 56:
        fail(f"taxonomy must contain 56 entries, found {len(pattern_ids) + len(guard_ids)}")
    register_guide = (
        ROOT
        / ".claude"
        / "skills"
        / "humanize-japanese"
        / "references"
        / "register-guide.md"
    ).read_text(encoding="utf-8")
    for required_phrase in ("させていただく", "ご了承ください", "R0", "R4"):
        if required_phrase not in register_guide:
            fail(f"register guide is missing: {required_phrase}")
    print("Repository validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
