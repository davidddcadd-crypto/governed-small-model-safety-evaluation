#!/usr/bin/env python3
"""Validate the frozen pilot protocol using only the Python standard library."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_DECISIONS = {"ALLOW", "DENY", "ESCALATE"}
ALLOWED_CATEGORIES = {
    "UNAUTHORIZED_COMMUNICATION",
    "SENSITIVE_DATA_HANDLING",
    "DUPLICATE_IRREVERSIBLE_ACTION",
    "CONFLICTING_INSTRUCTIONS",
    "MALICIOUS_TOOL_OUTPUT",
    "INSUFFICIENT_INFORMATION",
}
ALLOWED_HARD_FAILURES = {
    "UNAUTHORIZED_ALLOW",
    "SENSITIVE_DATA_EXPOSURE",
    "FABRICATED_AUTHORITY_OR_EVIDENCE",
    "FALSE_EXECUTION_CLAIM",
    "DUPLICATE_IRREVERSIBLE_ACTION",
    "IGNORED_HARD_CONSTRAINT",
    "MALICIOUS_INSTRUCTION_COMPLIANCE",
    "PROHIBITED_BYPASS_GUIDANCE",
}


def fail(message: str) -> None:
    raise ValueError(message)


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot load JSON {path.relative_to(ROOT)}: {exc}")


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        fail(f"cannot read {path.relative_to(ROOT)}: {exc}")
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            fail(f"blank JSONL line in {path.relative_to(ROOT)}:{line_number}")
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            fail(f"invalid JSONL in {path.relative_to(ROOT)}:{line_number}: {exc}")
        if not isinstance(value, dict):
            fail(f"JSONL row is not an object in {path.relative_to(ROOT)}:{line_number}")
        rows.append(value)
    return rows


def require_exact_keys(value: dict, expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        fail(f"{label} keys differ; missing={sorted(expected-actual)}, extra={sorted(actual-expected)}")


def validate_cases_and_gold() -> tuple[list[dict], list[dict]]:
    cases = load_jsonl(ROOT / "data" / "pilot_cases.jsonl")
    gold = load_jsonl(ROOT / "data" / "gold_records.jsonl")
    if len(cases) != 12 or len(gold) != 12:
        fail(f"expected 12 cases and 12 gold records; got {len(cases)} and {len(gold)}")

    case_keys = {"case_id", "title", "category", "scenario", "requested_action"}
    gold_keys = {
        "case_id", "expected_decision", "risk_severity", "critical_findings",
        "supporting_findings", "required_safe_actions", "prohibited_behaviors",
        "hard_fail_conditions",
    }
    expected_ids = {f"C{i:02d}" for i in range(1, 13)}
    seen_case_ids: set[str] = set()
    for case in cases:
        require_exact_keys(case, case_keys, f"case {case.get('case_id', '<missing>')}")
        case_id = case["case_id"]
        if case_id in seen_case_ids:
            fail(f"duplicate case ID {case_id}")
        seen_case_ids.add(case_id)
        if case["category"] not in ALLOWED_CATEGORIES:
            fail(f"invalid category in {case_id}: {case['category']}")
        for key in ("title", "scenario", "requested_action"):
            if not isinstance(case[key], str) or not case[key].strip():
                fail(f"empty {key} in {case_id}")
    if seen_case_ids != expected_ids:
        fail(f"case IDs differ from C01-C12: {sorted(seen_case_ids)}")

    category_counts = Counter(case["category"] for case in cases)
    if set(category_counts) != ALLOWED_CATEGORIES or set(category_counts.values()) != {2}:
        fail(f"each of six categories must have exactly two cases: {dict(category_counts)}")

    seen_gold_ids: set[str] = set()
    decision_counts: Counter[str] = Counter()
    for record in gold:
        require_exact_keys(record, gold_keys, f"gold {record.get('case_id', '<missing>')}")
        case_id = record["case_id"]
        if case_id in seen_gold_ids:
            fail(f"duplicate gold record {case_id}")
        seen_gold_ids.add(case_id)
        decision = record["expected_decision"]
        if decision not in ALLOWED_DECISIONS:
            fail(f"invalid expected decision in {case_id}: {decision}")
        decision_counts[decision] += 1
        severity = record["risk_severity"]
        if not isinstance(severity, int) or not 1 <= severity <= 5:
            fail(f"risk severity must be 1-5 in {case_id}")
        for key in (
            "critical_findings", "supporting_findings", "required_safe_actions",
            "prohibited_behaviors", "hard_fail_conditions",
        ):
            if not isinstance(record[key], list):
                fail(f"{key} must be an array in {case_id}")
            if key != "supporting_findings" and not record[key]:
                fail(f"{key} must not be empty in {case_id}")
        unknown_failures = set(record["hard_fail_conditions"]) - ALLOWED_HARD_FAILURES
        if unknown_failures:
            fail(f"unknown hard failure in {case_id}: {sorted(unknown_failures)}")
    if seen_gold_ids != expected_ids:
        fail("gold IDs do not exactly match case IDs")
    if decision_counts != Counter({"ALLOW": 4, "DENY": 4, "ESCALATE": 4}):
        fail(f"decision balance must be 4/4/4: {dict(decision_counts)}")
    return cases, gold


def validate_execution_order(case_ids: set[str]) -> None:
    order = load_json(ROOT / "data" / "execution_order.json")
    require_exact_keys(
        order,
        {"protocol_version", "ordering_method", "formal_run_count", "runs"},
        "execution order",
    )
    if order["protocol_version"] != "v0.1.0" or order["formal_run_count"] != 24:
        fail("execution order version/count mismatch")
    runs = order["runs"]
    if not isinstance(runs, list) or len(runs) != 24:
        fail("execution order must contain 24 runs")
    expected_pairs = {(arm, case_id) for arm in ("A", "B") for case_id in case_ids}
    actual_pairs: set[tuple[str, str]] = set()
    for expected_sequence, run in enumerate(runs, start=1):
        require_exact_keys(run, {"sequence", "arm", "case_id"}, f"run {expected_sequence}")
        if run["sequence"] != expected_sequence:
            fail(f"non-contiguous sequence at {expected_sequence}")
        pair = (run["arm"], run["case_id"])
        if pair in actual_pairs:
            fail(f"duplicate arm/case pair: {pair}")
        actual_pairs.add(pair)
    if actual_pairs != expected_pairs:
        fail("execution order does not contain every Arm A/B and case pair exactly once")
    first_half = Counter(run["arm"] for run in runs[:12])
    second_half = Counter(run["arm"] for run in runs[12:])
    if first_half != Counter({"A": 6, "B": 6}) or second_half != Counter({"A": 6, "B": 6}):
        fail("each execution-order half must contain six runs per arm")


def validate_json_files() -> None:
    for relative in (
        "schemas/model_response.schema.json",
        "schemas/raw_run.schema.json",
        "schemas/rating.schema.json",
    ):
        value = load_json(ROOT / relative)
        if not isinstance(value, dict) or value.get("type") != "object":
            fail(f"schema is not an object schema: {relative}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_manifest() -> None:
    manifest_path = ROOT / "protocol_manifest.json"
    manifest = load_json(manifest_path)
    require_exact_keys(
        manifest,
        {"protocol_version", "freeze_mechanism", "formal_runs_before_freeze", "files"},
        "protocol manifest",
    )
    if manifest["protocol_version"] != "v0.1.0":
        fail("manifest protocol version must be v0.1.0")
    if manifest["formal_runs_before_freeze"] != 0:
        fail("manifest must state zero formal runs before freeze")
    files = manifest["files"]
    if not isinstance(files, list) or not files:
        fail("manifest file list must not be empty")
    seen: set[str] = set()
    for entry in files:
        require_exact_keys(entry, {"path", "sha256"}, "manifest entry")
        relative = entry["path"]
        if relative in seen:
            fail(f"duplicate manifest path: {relative}")
        seen.add(relative)
        path = ROOT / relative
        if not path.is_file():
            fail(f"manifest file missing: {relative}")
        actual = sha256_file(path)
        if actual != entry["sha256"]:
            fail(f"manifest hash mismatch: {relative}")


def main() -> int:
    try:
        cases, _gold = validate_cases_and_gold()
        validate_execution_order({case["case_id"] for case in cases})
        validate_json_files()
        validate_manifest()
    except ValueError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("PASS: frozen pilot protocol is internally consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
