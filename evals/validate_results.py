#!/usr/bin/env python3
"""Validate model-produced skill eval results against deterministic contracts."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "evals" / "cases.json"
SKILL_ROOT = ROOT / "skills" / "humanize-japanese"
METRICS_PATH = SKILL_ROOT / "scripts" / "metrics.py"
TAXONOMY_PATH = (
    SKILL_ROOT / "references" / "ai-tell-taxonomy.md"
)

SPEC = importlib.util.spec_from_file_location("eval_humanize_metrics", METRICS_PATH)
assert SPEC and SPEC.loader
metrics = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = metrics
SPEC.loader.exec_module(metrics)


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def taxonomy_ids() -> set[str]:
    text = TAXONOMY_PATH.read_text(encoding="utf-8")
    return set(re.findall(r"^\| ([A-I]-\d+) \|", text, flags=re.MULTILINE))


def validate_case_document(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    cases = document.get("cases")
    if not isinstance(cases, list) or not cases:
        return ["cases must be a non-empty array"]
    required = {
        "id",
        "title",
        "context",
        "input",
        "target_register",
        "protected_exact",
        "must_keep",
        "must_remove",
        "must_include_any",
        "expected_finding_ids",
        "expected_kept",
        "allow_noop",
    }
    seen: set[str] = set()
    known_ids = taxonomy_ids()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            errors.append(f"case[{index}] must be an object")
            continue
        missing = sorted(required - set(case))
        if missing:
            errors.append(f"case[{index}] missing fields: {', '.join(missing)}")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id:
            errors.append(f"case[{index}] has invalid id")
        elif case_id in seen:
            errors.append(f"duplicate case id: {case_id}")
        else:
            seen.add(case_id)
        if case.get("target_register") not in {"R0", "R1", "R2", "R3", "R4"}:
            errors.append(f"{case_id}: invalid target_register")
        unknown = sorted(set(case.get("expected_finding_ids", [])) - known_ids)
        if unknown:
            errors.append(f"{case_id}: unknown expected finding IDs: {', '.join(unknown)}")
    return errors


def validate_payload(case_document: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    document_errors = validate_case_document(case_document)
    cases = case_document.get("cases", [])
    results = payload.get("results")
    top_errors = list(document_errors)
    if not isinstance(results, list):
        results = []
        top_errors.append("results must be an array")

    result_by_id: dict[str, dict[str, Any]] = {}
    for index, result in enumerate(results):
        if not isinstance(result, dict):
            top_errors.append(f"result[{index}] must be an object")
            continue
        case_id = result.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            top_errors.append(f"result[{index}] has invalid case_id")
        elif case_id in result_by_id:
            top_errors.append(f"duplicate result: {case_id}")
        else:
            result_by_id[case_id] = result

    expected_ids = {case["id"] for case in cases if isinstance(case, dict) and "id" in case}
    extra_ids = sorted(set(result_by_id) - expected_ids)
    if extra_ids:
        top_errors.append(f"unexpected result IDs: {', '.join(extra_ids)}")

    known_ids = taxonomy_ids()
    default_max = float(case_document.get("default_max_change_rate", 0.3))
    case_reports: list[dict[str, Any]] = []

    for case in cases:
        case_id = case["id"]
        errors: list[str] = []
        result = result_by_id.get(case_id)
        if result is None:
            case_reports.append(
                {"case_id": case_id, "passed": False, "errors": ["missing result"]}
            )
            continue

        output = result.get("output")
        if not isinstance(output, str) or not output.strip():
            output = ""
            errors.append("output must be a non-empty string")
        if result.get("register") != case["target_register"]:
            errors.append(
                f"register mismatch: expected {case['target_register']}, got {result.get('register')}"
            )
        if result.get("grade") not in {"A", "B"}:
            errors.append(f"grade must be A or B for a passing eval, got {result.get('grade')}")
        required_result_fields = {
            "case_id",
            "register",
            "output",
            "grade",
            "findings",
            "kept",
            "self_check",
        }
        missing_result_fields = sorted(required_result_fields - set(result))
        extra_result_fields = sorted(set(result) - required_result_fields)
        if missing_result_fields:
            errors.append(f"result fields missing: {', '.join(missing_result_fields)}")
        if extra_result_fields:
            errors.append(f"unexpected result fields: {', '.join(extra_result_fields)}")

        comparison = metrics.compare_texts(
            case["input"],
            output,
            case.get("protected_exact", []),
        )
        if not comparison["protected_integrity"]:
            removed = comparison["protected_removed"] + comparison["explicit_protected_removed"]
            added = comparison["protected_added"] + comparison["explicit_protected_added"]
            errors.append(f"protected content changed: removed={removed}, added={added}")
        if not comparison["modality_integrity"]:
            errors.append(
                "modality categories changed: "
                f"removed={comparison['modality_removed']}, added={comparison['modality_added']}"
            )

        for phrase in case.get("must_keep", []):
            if phrase not in output:
                errors.append(f"required phrase missing: {phrase}")
        for phrase in case.get("must_remove", []):
            if phrase in output:
                errors.append(f"forbidden phrase remains: {phrase}")
        for alternatives in case.get("must_include_any", []):
            if not any(phrase in output for phrase in alternatives):
                errors.append(f"none of required alternatives found: {alternatives}")

        findings = result.get("findings")
        if not isinstance(findings, list):
            findings = []
            errors.append("findings must be an array")
        finding_fields = {"id", "before", "after", "reason"}
        for index, finding in enumerate(findings):
            if not isinstance(finding, dict):
                errors.append(f"finding[{index}] must be an object")
                continue
            if set(finding) != finding_fields:
                errors.append(f"finding[{index}] fields must be {sorted(finding_fields)}")
            if any(not isinstance(finding.get(name), str) for name in finding_fields):
                errors.append(f"finding[{index}] values must be strings")
        finding_ids = {
            finding.get("id")
            for finding in findings
            if isinstance(finding, dict) and isinstance(finding.get("id"), str)
        }
        unknown_ids = sorted(finding_ids - known_ids)
        if unknown_ids:
            errors.append(f"unknown finding IDs: {', '.join(unknown_ids)}")
        missing_ids = sorted(set(case.get("expected_finding_ids", [])) - finding_ids)
        if missing_ids:
            errors.append(f"expected finding IDs missing: {', '.join(missing_ids)}")

        kept = result.get("kept")
        if not isinstance(kept, list):
            kept = []
            errors.append("kept must be an array")
        for index, item in enumerate(kept):
            if not isinstance(item, dict) or set(item) != {"text", "reason"}:
                errors.append(f"kept[{index}] must contain only text and reason")
            elif not isinstance(item.get("text"), str) or not isinstance(item.get("reason"), str):
                errors.append(f"kept[{index}] values must be strings")
        kept_texts = {
            item.get("text")
            for item in kept
            if isinstance(item, dict) and isinstance(item.get("text"), str)
        }
        missing_kept = sorted(set(case.get("expected_kept", [])) - kept_texts)
        if missing_kept:
            errors.append(f"kept reasons missing for: {', '.join(missing_kept)}")

        self_check = result.get("self_check")
        required_checks = {"facts", "modality", "register", "no_invention"}
        if not isinstance(self_check, dict):
            errors.append("self_check must be an object")
        else:
            failed_checks = sorted(name for name in required_checks if self_check.get(name) is not True)
            if failed_checks:
                errors.append(f"self_check failed: {', '.join(failed_checks)}")

        if output == case["input"] and not case.get("allow_noop", False):
            errors.append("unexpected no-op")
        max_change = float(case.get("max_change_rate", default_max))
        if not comparison["short_sample"] and comparison["change_rate"] > max_change:
            errors.append(
                f"change rate {comparison['change_rate']:.1%} exceeds {max_change:.1%}"
            )

        case_reports.append(
            {
                "case_id": case_id,
                "passed": not errors,
                "register": result.get("register"),
                "grade": result.get("grade"),
                "change_rate": comparison["change_rate"],
                "contract_integrity": comparison["contract_integrity"],
                "errors": errors,
            }
        )

    passed_count = sum(report["passed"] for report in case_reports)
    total = len(cases)
    return {
        "passed": not top_errors and passed_count == total,
        "score": round(passed_count / total, 4) if total else 0.0,
        "passed_cases": passed_count,
        "total_cases": total,
        "errors": top_errors,
        "cases": case_reports,
    }


def markdown_summary(report: dict[str, Any]) -> str:
    status = "PASS" if report["passed"] else "FAIL"
    lines = [
        "# Humanize Japanese skill eval",
        "",
        f"- Status: **{status}**",
        f"- Score: **{report['passed_cases']}/{report['total_cases']} ({report['score']:.0%})**",
        "",
        "| Case | Result | Register | Grade | Change | Notes |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for case in report["cases"]:
        notes = "<br>".join(case.get("errors", [])) or "-"
        change = case.get("change_rate")
        change_text = f"{change:.1%}" if isinstance(change, float) else "-"
        lines.append(
            f"| `{case['case_id']}` | {'PASS' if case['passed'] else 'FAIL'} | "
            f"{case.get('register', '-')} | {case.get('grade', '-')} | {change_text} | {notes} |"
        )
    if report["errors"]:
        lines.extend(["", "## Harness errors", ""])
        lines.extend(f"- {error}" for error in report["errors"])
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--results", type=Path)
    source.add_argument("--results-env")
    parser.add_argument("--write-results", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--summary", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    case_document = load_json(args.cases)
    if args.results:
        payload = load_json(args.results)
    else:
        raw = os.environ.get(args.results_env, "")
        if not raw:
            raise SystemExit(f"environment variable is empty: {args.results_env}")
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise SystemExit("structured output must be a JSON object")

    report = validate_payload(case_document, payload)
    if args.write_results:
        args.write_results.parent.mkdir(parents=True, exist_ok=True)
        args.write_results.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(markdown_summary(report), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
