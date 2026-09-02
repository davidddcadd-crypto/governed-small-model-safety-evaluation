#!/usr/bin/env python3
"""Validate immutable Round 3A evidence in its post-execution lifecycle state."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from build_round3_result_manifest import evidence_paths
from round3_common import (
    BASELINE_HASHES,
    CHECKPOINT_PATH,
    CHECKPOINT_SHA256,
    CHECKPOINT_SIZE,
    MODEL_BLOB_SHA256,
    MODEL_MANIFEST_SHA256,
    MODEL_TAG,
    RESULTS,
    ROOT,
    ROUND3,
    SETTINGS,
    PilotError,
    canonical_json,
    load_json,
    load_jsonl,
    load_order,
    parse_rfc3339,
    sha256_bytes,
    sha256_text,
)
from validate_round3_ratings import construct

PROTOCOL_MANIFEST_SHA256 = (
    "399aafe74784d85e06b7fb0cfb4640f417de4a39545dc83bdb68e189de8c90dc"
)
RESULT_MANIFEST_SHA256 = (
    "c9d2dc906f0450f3c5eae8d5ce057a894bb2b3d144474d513bef18743b1b8ccd"
)
PREPARATION_TEST_SHA256 = (
    "baf9445dbd4db258cb66213360dae535d2c83c4a7d1e3ba50c4b7bac874c2148"
)
PREPARATION_TEST_SIZE = 4476
CANONICAL_RATINGS_SHA256 = (
    "65f4fb0501c0a53be6bb0c3423bf361919fb13c26bb21c29633562a1d4cf0bb3"
)
EXPECTED_LIFECYCLE_TRANSITIONS = (
    {
        "test": "test_zero_formal_observations",
        "status": "EXPECTED_LIFECYCLE_TRANSITION",
        "current_reason": "authorized formal execution completed; formal observations are 24/24",
    },
    {
        "test": "test_result_manifest_refuses_incomplete_evidence",
        "status": "EXPECTED_LIFECYCLE_TRANSITION",
        "current_reason": "authorized execution and rating completed; the 94-file result evidence is complete",
    },
)


def _validate_bound_manifest(path: Path, expected_sha256: str, expected_count: int) -> dict[str, Any]:
    payload = path.read_bytes()
    if sha256_bytes(payload) != expected_sha256:
        raise PilotError(f"frozen manifest changed: {path.relative_to(ROOT).as_posix()}")
    value = json.loads(payload)
    rows = value.get("files")
    if value.get("file_count") != expected_count or not isinstance(rows, list) or len(rows) != expected_count:
        raise PilotError(f"frozen manifest count mismatch: {path.relative_to(ROOT).as_posix()}")
    seen: set[str] = set()
    for row in rows:
        relative = row.get("path")
        if not isinstance(relative, str) or relative in seen:
            raise PilotError(f"invalid or duplicate manifest path: {relative!r}")
        seen.add(relative)
        target = ROOT / relative
        if not target.is_file():
            raise PilotError(f"manifest file is missing: {relative}")
        bound = target.read_bytes()
        if len(bound) != row.get("size_bytes") or sha256_bytes(bound) != row.get("sha256"):
            raise PilotError(f"manifest file mismatch: {relative}")
    return value


def validate_excluded_checkpoint() -> None:
    """Allow public absence; fail closed if a local checkpoint is present but changed."""
    if not CHECKPOINT_PATH.exists():
        return
    if (
        not CHECKPOINT_PATH.is_file()
        or CHECKPOINT_PATH.stat().st_size != CHECKPOINT_SIZE
        or sha256_bytes(CHECKPOINT_PATH.read_bytes()) != CHECKPOINT_SHA256
    ):
        raise PilotError("excluded local checkpoint changed")


def validate_frozen_evidence() -> None:
    protocol = _validate_bound_manifest(
        ROUND3 / "round3_protocol_manifest.json", PROTOCOL_MANIFEST_SHA256, 36
    )
    result = _validate_bound_manifest(
        RESULTS / "RESULT_MANIFEST.json", RESULT_MANIFEST_SHA256, 94
    )
    test_path = ROOT / "tests/test_round3_preparation.py"
    if test_path.stat().st_size != PREPARATION_TEST_SIZE or sha256_bytes(test_path.read_bytes()) != PREPARATION_TEST_SHA256:
        raise PilotError("frozen preparation test changed")
    test_rows = [row for row in protocol["files"] if row["path"] == "tests/test_round3_preparation.py"]
    if len(test_rows) != 1 or test_rows[0]["sha256"] != PREPARATION_TEST_SHA256:
        raise PilotError("protocol manifest does not bind the frozen preparation test")
    result_paths = {row["path"] for row in result["files"]}
    required_result_paths = {
        "results/round3_granite41_3b/stage1_events.jsonl",
        "results/round3_granite41_3b/stage2_events.jsonl",
        "results/round3_granite41_3b/ratings_surrogate.jsonl",
    }
    if not required_result_paths <= result_paths:
        raise PilotError("result manifest lacks canonical rating custody paths")
    for relative, expected in BASELINE_HASHES.items():
        path = ROOT / relative
        if not path.is_file() or sha256_bytes(path.read_bytes()) != expected:
            raise PilotError(f"prior-round manifest changed: {relative}")
    validate_excluded_checkpoint()


def validate_lifecycle_transition() -> tuple[dict[str, str], ...]:
    test_path = ROOT / "tests/test_round3_preparation.py"
    source = test_path.read_text(encoding="utf-8")
    for item in EXPECTED_LIFECYCLE_TRANSITIONS:
        if f"def {item['test']}" not in source:
            raise PilotError(f"frozen historical assertion is missing: {item['test']}")
    protocol = load_json(ROUND3 / "round3_protocol_manifest.json")
    if protocol.get("formal_observations_before_freeze") != 0:
        raise PilotError("protocol does not prove the zero-observation preparation state")
    plan = load_json(ROUND3 / "RESULT_MANIFEST_PLAN.json")
    if plan.get("version") != "round3a-result-manifest-plan-v1" or len(plan.get("required_artifacts", [])) < 20:
        raise PilotError("frozen result-manifest plan is invalid")
    if len(evidence_paths()) != 94:
        raise PilotError("post-execution result evidence is not complete")
    return EXPECTED_LIFECYCLE_TRANSITIONS


def validate_formal_custody() -> None:
    order = load_order()
    expected_ids = [row["run_id"] for row in order]
    expected_names = {f"{run_id}.request.json" for run_id in expected_ids}
    request_paths = sorted((RESULTS / "requests").glob("R3A-RUN-*.request.json"))
    raw_paths = sorted((RESULTS / "raw_runs").glob("R3A-RUN-*.json"))
    attempt_paths = sorted((RESULTS / "attempts").glob("R3A-RUN-*-ATTEMPT-*.json"))
    if len(request_paths) != 24 or {path.name for path in request_paths} != expected_names:
        raise PilotError("formal request inventory is not exact 24/24")
    if len(raw_paths) != 24 or {path.stem for path in raw_paths} != set(expected_ids):
        raise PilotError("formal raw-run inventory is not exact 24/24")
    expected_attempt_names = {f"{run_id}-ATTEMPT-01.json" for run_id in expected_ids}
    if len(attempt_paths) != 24 or {path.name for path in attempt_paths} != expected_attempt_names:
        raise PilotError("attempt inventory is not one first attempt per formal run")
    formal_rows = load_jsonl(RESULTS / "formal_raw_results.jsonl")
    if len(formal_rows) != 24 or [row.get("run_id") for row in formal_rows] != expected_ids:
        raise PilotError("formal result JSONL order or count mismatch")
    seen: set[str] = set()
    arms = {"A": 0, "B": 0}
    formats = {"VALID_JSON": 0, "FORMAT_FAIL": 0}
    for order_row, formal in zip(order, formal_rows, strict=True):
        run_id = order_row["run_id"]
        if run_id in seen:
            raise PilotError(f"duplicate formal run: {run_id}")
        seen.add(run_id)
        request_path = RESULTS / "requests" / f"{run_id}.request.json"
        attempt_path = RESULTS / "attempts" / f"{run_id}-ATTEMPT-01.json"
        raw_path = RESULTS / "raw_runs" / f"{run_id}.json"
        request = load_json(request_path)
        attempt = load_json(attempt_path)
        raw = load_json(raw_path)
        if raw != formal:
            raise PilotError(f"raw-run and formal JSONL record differ: {run_id}")
        if (raw.get("sequence"), raw.get("arm"), raw.get("case_id")) != (
            order_row["sequence"], order_row["arm"], order_row["case_id"]
        ):
            raise PilotError(f"run-order binding mismatch: {run_id}")
        if request.get("model") != MODEL_TAG or request.get("options") != {
            key: SETTINGS[key] for key in ("temperature", "seed", "num_ctx", "num_predict")
        }:
            raise PilotError(f"formal request settings mismatch: {run_id}")
        if "tools" in request or "tool_choice" in request:
            raise PilotError(f"formal request enabled tools: {run_id}")
        request_sha = sha256_text(canonical_json(request))
        if attempt.get("run_id") != run_id or attempt.get("attempt_id") != f"{run_id}-ATTEMPT-01":
            raise PilotError(f"attempt identity mismatch: {run_id}")
        if attempt.get("status") != "OK" or attempt.get("request_sha256") != request_sha:
            raise PilotError(f"attempt did not complete normally: {run_id}")
        raw_body = attempt.get("raw_api_body")
        if not isinstance(raw_body, str) or sha256_bytes(raw_body.encode("utf-8")) != attempt.get("raw_api_body_sha256"):
            raise PilotError(f"attempt API-body hash mismatch: {run_id}")
        if (
            raw.get("run_id") != run_id
            or raw.get("attempt_id") != attempt["attempt_id"]
            or raw.get("request_sha256") != request_sha
            or raw.get("raw_api_body_sha256") != attempt["raw_api_body_sha256"]
            or raw.get("transport_status") != "OK"
            or raw.get("error") is not None
            or raw.get("model_tag") != MODEL_TAG
            or raw.get("model_manifest_sha256") != MODEL_MANIFEST_SHA256
            or raw.get("model_blob_sha256") != MODEL_BLOB_SHA256
            or raw.get("round3_protocol_manifest_sha256") != PROTOCOL_MANIFEST_SHA256
        ):
            raise PilotError(f"formal custody binding mismatch: {run_id}")
        arms[raw["arm"]] += 1
        formats[raw["format_status"]] = formats.get(raw["format_status"], 0) + 1
    if arms != {"A": 12, "B": 12}:
        raise PilotError(f"formal arm counts are invalid: {arms}")
    if formats != {"VALID_JSON": 23, "FORMAT_FAIL": 1}:
        raise PilotError(f"formal format counts are invalid: {formats}")


def validate_canonical_reconstruction() -> None:
    ratings_path = RESULTS / "ratings_surrogate.jsonl"
    if sha256_bytes(ratings_path.read_bytes()) != CANONICAL_RATINGS_SHA256:
        raise PilotError("canonical rating bytes changed")
    reconstructed = construct(
        RESULTS / "stage1_raw_output.json",
        RESULTS / "stage2_raw_output.json",
        RESULTS / "rater_session.json",
    )
    frozen = load_jsonl(ratings_path)
    if len(reconstructed) != 24 or reconstructed != frozen:
        raise PilotError("canonical ratings do not reconstruct exactly 24/24")


def validate_record() -> None:
    path = RESULTS / "POSTEXECUTION_VALIDATION.json"
    value = load_json(path)
    if value.get("record_type") != "ROUND3A_POSTEXECUTION_LIFECYCLE_VALIDATION":
        raise PilotError("post-execution validation record type mismatch")
    parse_rfc3339(value["recorded_at"])
    expected = {
        "protocol_manifest_sha256": PROTOCOL_MANIFEST_SHA256,
        "protocol_manifest_file_count": 36,
        "result_manifest_sha256": RESULT_MANIFEST_SHA256,
        "result_manifest_file_count": 94,
        "preparation_test_sha256": PREPARATION_TEST_SHA256,
        "preparation_test_size_bytes": PREPARATION_TEST_SIZE,
    }
    if value.get("frozen_bindings") != expected:
        raise PilotError("post-execution validation frozen bindings mismatch")
    custody = value.get("postexecution_custody")
    if custody != {
        "formal_observations": 24,
        "requests": 24,
        "attempts": 24,
        "raw_runs": 24,
        "attempts_per_run": 1,
        "transport_retries": 0,
        "selective_reruns": 0,
        "arm_a_observations": 12,
        "arm_b_observations": 12,
        "canonical_ratings": 24,
        "canonical_ratings_sha256": CANONICAL_RATINGS_SHA256,
        "canonical_reconstruction": "PASS_EXACT_24_OF_24",
    }:
        raise PilotError("post-execution validation custody summary mismatch")
    if value.get("historical_preparation_tests") != list(EXPECTED_LIFECYCLE_TRANSITIONS):
        raise PilotError("post-execution lifecycle disclosure mismatch")
    prior = value.get("prior_manifest_bindings")
    expected_prior = [
        {"path": path, "sha256": digest, "status": "UNCHANGED"}
        for path, digest in BASELINE_HASHES.items()
    ]
    if prior != expected_prior:
        raise PilotError("post-execution prior-manifest bindings mismatch")
    excluded = value.get("excluded_checkpoint")
    if excluded != {
        "path": "results/ratings_primary.partial.jsonl",
        "size_bytes": CHECKPOINT_SIZE,
        "sha256": CHECKPOINT_SHA256,
        "status": "UNCHANGED_AND_EXCLUDED",
    }:
        raise PilotError("post-execution checkpoint disclosure mismatch")


def validate_all() -> None:
    validate_frozen_evidence()
    validate_lifecycle_transition()
    validate_formal_custody()
    validate_canonical_reconstruction()
    validate_record()


def main() -> int:
    try:
        validate_all()
        print(
            "PASS: Round 3A post-execution evidence is complete and immutable; "
            "2 frozen preparation assertions are EXPECTED_LIFECYCLE_TRANSITION"
        )
        return 0
    except (PilotError, OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
