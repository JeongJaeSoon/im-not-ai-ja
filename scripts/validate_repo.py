#!/usr/bin/env python3
"""Validate the portable Agent Skill and its repository tooling."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.3.0"
SKILL_ROOT = ROOT / "skills" / "humanize-japanese"


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

    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        field_match = re.match(r"^([a-z][a-z0-9-]*):\s*(.*)$", line)
        if field_match:
            fields[field_match.group(1)] = field_match.group(2).strip()

    allowed = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
    unknown = sorted(set(fields) - allowed)
    if unknown:
        fail(f"unsupported frontmatter fields: {', '.join(unknown)}")
    if "name" not in fields or "description" not in fields:
        fail("skill frontmatter requires name and description")

    name = fields["name"]
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64:
        fail(f"invalid skill name: {name!r}")
    if name != path.parent.name:
        fail(f"skill name must match parent directory: {name!r} != {path.parent.name!r}")
    description = fields["description"]
    if not 1 <= len(description) <= 1024:
        fail(f"skill description must be 1-1024 characters, found {len(description)}")
    if len(text.splitlines()) > 500:
        fail("SKILL.md must stay under 500 lines")


def main() -> int:
    required = {
        "README.md",
        "INSTALL.md",
        "LICENSE",
        "NOTICE.md",
        "skills/humanize-japanese/SKILL.md",
        "skills/humanize-japanese/assets/baseline.json",
        "skills/humanize-japanese/references/ai-tell-taxonomy.md",
        "skills/humanize-japanese/references/quick-rules.md",
        "skills/humanize-japanese/references/register-guide.md",
        "skills/humanize-japanese/references/research.md",
        "skills/humanize-japanese/references/rewriting-playbook.md",
        "skills/humanize-japanese/scripts/metrics.py",
        "evals/cases.json",
        "evals/result.schema.json",
        "evals/fixtures/reference-results.json",
        "evals/validate_results.py",
        ".github/workflows/skill-eval.yml",
    }
    for relative in sorted(required):
        if not (ROOT / relative).is_file():
            fail(f"missing required file: {relative}")

    forbidden = (
        ".agents",
        ".claude",
        ".claude-plugin",
        ".codex",
        ".codex-plugin",
        "agents",
        "codex",
        "commands",
        "GEMINI.md",
        "gemini-extension.json",
        "install.sh",
        "uninstall.sh",
        "update.sh",
        "skills/humanize-japanese/agents",
    )
    for relative in forbidden:
        if (ROOT / relative).exists() or (ROOT / relative).is_symlink():
            fail(f"runtime-specific or legacy path must not exist: {relative}")

    symlinks = [path.relative_to(ROOT) for path in ROOT.rglob("*") if path.is_symlink()]
    if symlinks:
        fail(f"repository must not use runtime adapter symlinks: {symlinks}")

    expected_skill_files = {
        Path("SKILL.md"),
        Path("assets/baseline.json"),
        Path("references/ai-tell-taxonomy.md"),
        Path("references/quick-rules.md"),
        Path("references/register-guide.md"),
        Path("references/research.md"),
        Path("references/rewriting-playbook.md"),
        Path("scripts/metrics.py"),
    }
    actual_skill_files = {
        path.relative_to(SKILL_ROOT) for path in SKILL_ROOT.rglob("*") if path.is_file()
    }
    if actual_skill_files != expected_skill_files:
        missing = sorted(str(path) for path in expected_skill_files - actual_skill_files)
        extra = sorted(str(path) for path in actual_skill_files - expected_skill_files)
        fail(f"unexpected skill inventory: missing={missing}, extra={extra}")

    skill_files = list(ROOT.rglob("SKILL.md"))
    if skill_files != [SKILL_ROOT / "SKILL.md"]:
        rendered = sorted(str(path.relative_to(ROOT)) for path in skill_files)
        fail(f"repository must contain exactly one SKILL.md: {rendered}")
    validate_skill(skill_files[0])

    skill_text = skill_files[0].read_text(encoding="utf-8")
    for relative in sorted(str(path) for path in expected_skill_files if path.name != "SKILL.md"):
        if f"`{relative}`" not in skill_text:
            fail(f"SKILL.md must explain when to use supporting file: {relative}")
    for relative in re.findall(r"`((?:assets|references|scripts)/[^`]+)`", skill_text):
        if not (SKILL_ROOT / relative).is_file():
            fail(f"SKILL.md contains a broken relative reference: {relative}")
    for forbidden_text in ("agents/", "subagent", "_workspace/"):
        if forbidden_text in skill_text:
            fail(f"SKILL.md contains a non-portable runtime dependency: {forbidden_text}")

    for path in ROOT.rglob("*.json"):
        if ".git" not in path.parts:
            validate_json(path)

    result_schema = json.loads((ROOT / "evals" / "result.schema.json").read_text(encoding="utf-8"))
    runtime_schema = {
        key: value for key, value in result_schema.items() if key not in {"$schema", "title"}
    }
    compact_schema = json.dumps(runtime_schema, ensure_ascii=False, separators=(",", ":"))
    eval_workflow = (ROOT / ".github" / "workflows" / "skill-eval.yml").read_text(
        encoding="utf-8"
    )
    if f"--json-schema '{compact_schema}'" not in eval_workflow:
        fail("skill-eval workflow JSON schema is out of sync with evals/result.schema.json")
    for required_workflow_text in (
        "default: claude-sonnet-5",
        "skills/humanize-japanese/**",
        "Read `skills/humanize-japanese/SKILL.md`",
        "CLAUDE_CODE_OAUTH_TOKEN",
        "ANTHROPIC_API_KEY",
        "github_token: ${{ github.token }}",
        "uses: actions/upload-artifact@v7",
    ):
        if required_workflow_text not in eval_workflow:
            fail(f"skill-eval workflow is missing: {required_workflow_text}")

    project_text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    project_match = re.search(r'^version\s*=\s*"([^"]+)"$', project_text, re.MULTILINE)
    metrics_text = (SKILL_ROOT / "scripts" / "metrics.py").read_text(encoding="utf-8")
    metrics_match = re.search(r'^VERSION\s*=\s*"([^"]+)"$', metrics_text, re.MULTILINE)
    versions = {project_match.group(1) if project_match else None, metrics_match.group(1) if metrics_match else None}
    if versions != {VERSION}:
        fail(f"project and metrics versions must both be {VERSION}: {versions}")

    cases = json.loads((ROOT / "evals" / "cases.json").read_text(encoding="utf-8"))
    if cases.get("skill") != "skills/humanize-japanese/SKILL.md":
        fail("eval corpus must point to the canonical skill")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if "epoko77-ai/im-not-ai" not in readme or "fork機能は使っていません" not in readme:
        fail("README attribution is missing")
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    if "Copyright (c) 2026 epoko77-ai" not in license_text:
        fail("upstream copyright is missing")

    taxonomy = (SKILL_ROOT / "references" / "ai-tell-taxonomy.md").read_text(
        encoding="utf-8"
    )
    pattern_ids = re.findall(r"^\| ([A-I]-\d+) \|", taxonomy, flags=re.MULTILINE)
    guard_ids = re.findall(r"^\| (J-\d+) \|", taxonomy, flags=re.MULTILINE)
    if len(pattern_ids) + len(guard_ids) != 59:
        fail(f"taxonomy must contain 59 entries, found {len(pattern_ids) + len(guard_ids)}")
    register_guide = (SKILL_ROOT / "references" / "register-guide.md").read_text(
        encoding="utf-8"
    )
    for required_phrase in ("させていただく", "ご了承ください", "R0", "R4"):
        if required_phrase not in register_guide:
            fail(f"register guide is missing: {required_phrase}")

    print("Portable Agent Skill validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
