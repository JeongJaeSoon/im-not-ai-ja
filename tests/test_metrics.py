from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
METRICS_PATH = ROOT / ".claude" / "skills" / "humanize-japanese" / "scripts" / "metrics.py"
SPEC = importlib.util.spec_from_file_location("humanize_metrics", METRICS_PATH)
assert SPEC and SPEC.loader
metrics = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = metrics
SPEC.loader.exec_module(metrics)


class SentenceAndRhythmTests(unittest.TestCase):
    def test_split_sentences_handles_japanese_quotes(self) -> None:
        text = "彼は『行きます。』と言った。私は残った！本当かな？"
        self.assertEqual(len(metrics.split_sentences(text)), 4)

    def test_uniform_text_has_lower_cv_than_varied_text(self) -> None:
        uniform = "今日は晴れです。明日も晴れです。週末も晴れです。来週も晴れです。午後も晴れです。"
        varied = "晴れです。明日は朝から雲が広がり、午後には短い雨が降る見込みです。雨。週末は回復します。たぶん。"
        uniform_cv = metrics.analyze_text(uniform)["rhythm"]["sentence_length_cv"]
        varied_cv = metrics.analyze_text(varied)["rhythm"]["sentence_length_cv"]
        self.assertLess(uniform_cv, varied_cv)

    def test_short_sample_does_not_emit_rhythm_threshold_findings(self) -> None:
        result = metrics.analyze_text("今日は晴れです。散歩します。")
        ids = {finding["id"] for finding in result["findings"]}
        self.assertNotIn("G-1", ids)
        self.assertTrue(result["warnings"])

    def test_markdown_table_is_excluded_from_prose_metrics(self) -> None:
        text = "本文です。\n\n| 項目 | 説明 |\n|---|---|\n| 敬語 | です・ます |"
        result = metrics.analyze_text(text)
        self.assertEqual(result["counts"]["sentences"], 1)


class RegisterTests(unittest.TestCase):
    def test_polite_density_alone_is_not_a_finding(self) -> None:
        text = "本日は晴れです。会場は駅前です。受付は十時です。資料は机の上です。終了は五時です。"
        result = metrics.analyze_text(text)
        self.assertEqual(result["register"]["dominant"], "polite")
        reasons = " ".join(finding["reason"] for finding in result["findings"])
        self.assertNotIn("丁寧体密度", reasons)

    def test_sasete_itadaku_requires_context_review_not_removal(self) -> None:
        result = metrics.analyze_text("本日は発表させていただきます。")
        finding = next(item for item in result["findings"] if "させていただく" in item["reason"])
        self.assertEqual(finding["severity"], "S2")
        self.assertIn("保持", finding["note"])

    def test_go_ryosho_is_contextual(self) -> None:
        result = metrics.analyze_text("在庫切れのため、ご了承ください。")
        finding = next(item for item in result["findings"] if "ご了承ください" in item["reason"])
        self.assertIn("正式通知なら保持", finding["note"])

    def test_double_honorific_candidate_is_flagged(self) -> None:
        result = metrics.analyze_text("部長がお読みになられました。")
        finding = next(item for item in result["findings"] if "重なり候補" in item["reason"])
        self.assertEqual(finding["severity"], "S1")


class PatternTests(unittest.TestCase):
    def test_repeated_signature_phrase_reaches_s1(self) -> None:
        text = "これにより速度が上がります。これにより費用が下がります。"
        result = metrics.analyze_text(text)
        finding = next(item for item in result["findings"] if item["id"] == "D-2")
        self.assertEqual(finding["severity"], "S1")
        self.assertEqual(finding["count"], 2)

    def test_single_phrase_is_contextual(self) -> None:
        result = metrics.analyze_text("この対応は非常に重要です。")
        finding = next(item for item in result["findings"] if item["id"] == "C-2")
        self.assertEqual(finding["severity"], "S2")

    def test_markdown_and_emoji_are_counted(self) -> None:
        result = metrics.analyze_text("**重要:** 対応します。✅")
        self.assertEqual(result["pattern_counts"]["H-1"], 1)
        self.assertEqual(result["pattern_counts"]["H-3"], 1)


class FidelityTests(unittest.TestCase):
    def test_protected_token_change_is_reported(self) -> None:
        before = "GPT-5を2026年7月15日に導入し、費用は50%下がった。"
        after = "GPT-5を2026年7月16日に導入し、費用は40%下がった。"
        comparison = metrics.compare_texts(before, after)
        self.assertFalse(comparison["protected_integrity"])
        self.assertIn("15日", comparison["protected_removed"])
        self.assertIn("50%", comparison["protected_removed"])

    def test_cli_outputs_valid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.md"
            path.write_text("今日は晴れです。明日も晴れです。", encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(METRICS_PATH), str(path)],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["analysis"]["version"], "0.1.0")


if __name__ == "__main__":
    unittest.main()
