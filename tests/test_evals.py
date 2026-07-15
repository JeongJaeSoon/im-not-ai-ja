from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "evals" / "validate_results.py"
SPEC = importlib.util.spec_from_file_location("humanize_eval_validator", VALIDATOR_PATH)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)


class EvalHarnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = validator.load_json(ROOT / "evals" / "cases.json")
        cls.reference = validator.load_json(
            ROOT / "evals" / "fixtures" / "reference-results.json"
        )

    def test_reference_fixture_passes_all_contracts(self) -> None:
        report = validator.validate_payload(self.cases, self.reference)
        self.assertTrue(report["passed"])
        self.assertEqual(report["score"], 1.0)

    def test_proper_name_mutation_fails_contract(self) -> None:
        payload = copy.deepcopy(self.reference)
        result = next(
            item for item in payload["results"] if item["case_id"] == "r3_adversarial_contract"
        )
        result["output"] = result["output"].replace("佐藤美咲", "佐藤美沙")
        report = validator.validate_payload(self.cases, payload)
        case = next(item for item in report["cases"] if item["case_id"] == result["case_id"])
        self.assertFalse(case["passed"])
        self.assertIn("protected content changed", " ".join(case["errors"]))

    def test_modality_strengthening_fails_contract(self) -> None:
        payload = copy.deepcopy(self.reference)
        result = next(
            item for item in payload["results"] if item["case_id"] == "r3_adversarial_contract"
        )
        result["output"] = result["output"].replace("停止する場合があります", "停止します")
        report = validator.validate_payload(self.cases, payload)
        case = next(item for item in report["cases"] if item["case_id"] == result["case_id"])
        self.assertFalse(case["passed"])
        self.assertIn("modality categories changed", " ".join(case["errors"]))

    def test_missing_case_fails_harness(self) -> None:
        payload = copy.deepcopy(self.reference)
        payload["results"].pop()
        report = validator.validate_payload(self.cases, payload)
        self.assertFalse(report["passed"])
        self.assertEqual(report["passed_cases"], 9)

    def test_unknown_finding_id_fails_case(self) -> None:
        payload = copy.deepcopy(self.reference)
        payload["results"][0]["findings"][0]["id"] = "E-404"
        report = validator.validate_payload(self.cases, payload)
        self.assertFalse(report["passed"])
        self.assertIn("unknown finding IDs", " ".join(report["cases"][0]["errors"]))


if __name__ == "__main__":
    unittest.main()
