from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
METRICS_PATH = ROOT / "skills" / "humanize-japanese" / "scripts" / "metrics.py"
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

    def test_common_casual_endings_are_classified(self) -> None:
        for sentence in ("間に合うよ。", "わかっておいてね。", "大丈夫かな。"):
            label, _ = metrics.classify_ending(sentence)
            self.assertEqual(label, "casual")

    def test_quoted_voice_is_excluded_from_register_metrics(self) -> None:
        text = "担当者は「それ、無理だよね。」と述べます。対応は明日行います。"
        result = metrics.analyze_text(text)
        self.assertEqual(result["register"]["dominant"], "polite")
        self.assertEqual(result["register"]["quoted_segments_excluded"], 1)

    def test_quoted_expression_is_excluded_from_findings(self) -> None:
        result = metrics.analyze_text("友人は「ご了承ください。」と言いました。")
        self.assertNotIn("E-8", {item["id"] for item in result["findings"]})


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
        self.assertEqual(finding["id"], "E-9")

    def test_honorific_findings_have_dedicated_ids(self) -> None:
        sasete = metrics.analyze_text("本日は公開させていただきます。")
        go_ryosho = metrics.analyze_text("あらかじめご了承ください。")
        self.assertIn("E-7", {item["id"] for item in sasete["findings"]})
        self.assertIn("E-8", {item["id"] for item in go_ryosho["findings"]})


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

    def test_b3_does_not_cross_sentences_or_match_ordinary_kara_ni(self) -> None:
        ordinary = "19時からだよ。仕事が終わってからでも間に合うよ。"
        formula = "ツールを超えてパートナーへ進化します。"
        self.assertEqual(metrics.pattern_counts(ordinary)["B-3"], 0)
        self.assertEqual(metrics.pattern_counts(formula)["B-3"], 1)

    def test_a1_matches_honkou_dewa_variant(self) -> None:
        text = "本稿では回答を分析する。本稿では結果を比較する。"
        self.assertEqual(metrics.pattern_counts(text)["A-1"], 2)

    def test_g1_severity_matches_taxonomy(self) -> None:
        text = "今日は晴れです。明日も晴れです。週末も晴れです。来週も晴れです。午後も晴れです。"
        result = metrics.analyze_text(text)
        finding = next(item for item in result["findings"] if item["id"] == "G-1")
        self.assertEqual(finding["severity"], "S2")

    def test_span_finding_contains_text_and_offsets(self) -> None:
        text = "これにより速度が上がります。"
        result = metrics.analyze_text(text)
        finding = next(item for item in result["findings"] if item["id"] == "D-2")
        self.assertEqual(finding["matches"][0], {"text": "これにより", "start": 0, "end": 5})

    def test_span_offsets_are_relative_to_original_text(self) -> None:
        text = "https://example.jp これにより速度が上がります。"
        result = metrics.analyze_text(text)
        finding = next(item for item in result["findings"] if item["id"] == "D-2")
        start = text.index("これにより")
        self.assertEqual(finding["matches"][0]["start"], start)


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
            self.assertEqual(payload["analysis"]["version"], "0.3.0")

    def test_explicit_names_are_part_of_integrity_contract(self) -> None:
        before = "佐藤美咲がProject KAIを公開します。"
        after = "佐藤美沙がProject KAI-Xを公開します。"
        comparison = metrics.compare_texts(before, after, ["佐藤美咲", "Project KAI"])
        self.assertFalse(comparison["protected_integrity"])
        self.assertFalse(comparison["contract_integrity"])
        self.assertEqual(
            comparison["explicit_protected_removed"],
            ["佐藤美咲", "Project KAI"],
        )

    def test_modality_weakening_is_reported(self) -> None:
        before = "予告なく停止する場合があります。"
        after = "予告なく停止します。"
        comparison = metrics.compare_texts(before, after)
        self.assertFalse(comparison["modality_integrity"])
        self.assertIn("possibility", comparison["modality_removed"])
        self.assertFalse(comparison["contract_integrity"])

    def test_equivalent_hedge_keeps_modality_category(self) -> None:
        before = "短縮できる可能性があるかもしれません。"
        after = "短縮できる可能性があります。"
        comparison = metrics.compare_texts(before, after)
        self.assertTrue(comparison["modality_integrity"])

    def test_short_sample_change_rate_is_reference_only(self) -> None:
        comparison = metrics.compare_texts("公開させていただきます。", "公開いたします。")
        self.assertTrue(comparison["short_sample"])
        self.assertEqual(comparison["change_rate_policy"], "reference_only_for_short_sample")


if __name__ == "__main__":
    unittest.main()
