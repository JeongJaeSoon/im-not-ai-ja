from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "humanize-japanese"


class PortableSkillStructureTests(unittest.TestCase):
    def test_skill_has_only_standard_resource_directories(self) -> None:
        children = {path.name for path in SKILL_ROOT.iterdir()}
        self.assertEqual(children, {"SKILL.md", "assets", "references", "scripts"})
        self.assertFalse(any(path.is_symlink() for path in SKILL_ROOT.rglob("*")))

    def test_skill_copy_runs_without_repository_adapters(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            copied_skill = Path(temporary_directory) / "humanize-japanese"
            shutil.copytree(SKILL_ROOT, copied_skill)
            sample = copied_skill / "sample.md"
            sample.write_text(
                "今日は晴れです。明日も晴れです。週末も晴れです。"
                "来週も晴れです。午後も晴れです。",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [sys.executable, str(copied_skill / "scripts" / "metrics.py"), str(sample)],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["analysis"]["version"], "0.3.0")
            self.assertIn("G-1", {item["id"] for item in payload["analysis"]["findings"]})

    def test_repository_has_one_skill_entrypoint(self) -> None:
        skill_files = list(ROOT.rglob("SKILL.md"))
        self.assertEqual(skill_files, [SKILL_ROOT / "SKILL.md"])


if __name__ == "__main__":
    unittest.main()
