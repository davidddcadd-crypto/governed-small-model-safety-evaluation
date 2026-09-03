#!/usr/bin/env python3
"""Lifecycle-aware Round 5A post-execution validator, frozen before execution."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from round5_common import (
    CHECKPOINT_PATH, CHECKPOINT_SHA256, CHECKPOINT_SIZE, MODEL_BLOB_SHA256,
    MODEL_MANIFEST_SHA256, MODEL_TAG, RESULTS, ROOT, SETTINGS, PilotError,
    canonical_json, load_json, load_jsonl, load_order, protocol_manifest_sha256,
    sha256_bytes, sha256_text, validate_sources,
)
from validate_round5_ratings import construct

PREPARATION_TRANSITIONS = (
    "test_zero_formal_observations",
    "test_result_manifest_refuses_incomplete_evidence",
)
REQUIRED_COMPLETED = (
    "PROJECT_OWNER_AUTHORIZATION.json", "warmup.json", "execution_environment.json",
    "formal_raw_results.jsonl", "blinded_extraction_packet.jsonl", "blinding_key.json",
    "STAGE1_TRANSMISSION_AUTHORIZATION.json", "stage1_prompt.txt", "stage1_events.jsonl",
    "stage1_raw_output.json", "blinded_scoring_packet.jsonl",
    "STAGE2_TRANSMISSION_AUTHORIZATION.json", "stage2_prompt.txt", "stage2_events.jsonl",
    "stage2_raw_output.json", "rater_session.json", "ratings_surrogate.jsonl",
    "ROUND5_METRICS.json", "ROUND5_REPORT.md", "RESULT_MANIFEST.json",
)


def validate_excluded_checkpoint() -> None:
    """A public checkout may omit the checkpoint; a local copy must be exact."""
    if not CHECKPOINT_PATH.exists():
        return
    if (
        not CHECKPOINT_PATH.is_file()
        or CHECKPOINT_PATH.stat().st_size != CHECKPOINT_SIZE
        or sha256_bytes(CHECKPOINT_PATH.read_bytes()) != CHECKPOINT_SHA256
    ):
        raise PilotError("excluded local checkpoint changed")


def lifecycle_state(result_root: Path = RESULTS) -> str:
    raw_dir = result_root / "raw_runs"
    count = len(list(raw_dir.glob("R5A-RUN-*.json"))) if raw_dir.exists() else 0
    files = (
        [path for path in result_root.rglob("*") if path.is_file() and path.name not in {".gitkeep", ".gitattributes"}]
        if result_root.exists() else []
    )
    if count == 0 and not files:
        return "PRE_EXECUTION"
    if count == 24:
        return "POST_EXECUTION"
    return "INCOMPLETE_FAIL_CLOSED"


def validate_prepared_architecture() -> None:
    required = (
        ROOT / "round5/LIFECYCLE_VALIDATION_PLAN.md",
        ROOT / "round5/RESULT_MANIFEST_PLAN.json",
        ROOT / "scripts/run_round5.py",
        ROOT / "scripts/build_round5_rating_packets.py",
        ROOT / "scripts/validate_round5_ratings.py",
        ROOT / "scripts/analyze_round5.py",
        ROOT / "scripts/build_round5_result_manifest.py",
        ROOT / "scripts/validate_round5_postexecution.py",
    )
    missing = [path.relative_to(ROOT).as_posix() for path in required if not path.is_file()]
    if missing:
        raise PilotError(f"Round-5 lifecycle architecture is incomplete: {missing}")
    if lifecycle_state() != "PRE_EXECUTION":
        raise PilotError("preparation architecture gate requires PRE_EXECUTION")


def lifecycle_transition_record() -> list[dict[str, str]]:
    return [
        {
            "test": name,
            "pre_execution_status": "PASS",
            "post_execution_status": "EXPECTED_LIFECYCLE_TRANSITION",
            "frozen_test_modified": "NO",
        }
        for name in PREPARATION_TRANSITIONS
    ]


def _validate_result_manifest() -> None:
    manifest = load_json(RESULTS / "RESULT_MANIFEST.json")
    rows = manifest.get("files")
    if not isinstance(rows, list) or manifest.get("file_count") != len(rows):
        raise PilotError("Round-5 result manifest count mismatch")
    if len({row.get("path") for row in rows}) != len(rows):
        raise PilotError("Round-5 result manifest contains duplicate paths")
    for row in rows:
        target = ROOT / row["path"]
        payload = target.read_bytes()
        if row.get("size_bytes") != len(payload) or row.get("sha256") != sha256_bytes(payload):
            raise PilotError(f"Round-5 result manifest mismatch: {row.get('path')}")


def validate_completed_evidence() -> dict[str, Any]:
    if lifecycle_state() != "POST_EXECUTION":
        raise PilotError("Round-5 post-execution evidence is not complete")
    validate_sources()
    validate_excluded_checkpoint()
    missing = [name for name in REQUIRED_COMPLETED if not (RESULTS / name).is_file()]
    if missing:
        raise PilotError(f"Round-5 completed evidence is incomplete: {missing}")
    order = {row["run_id"]: row for row in load_order()}
    request_paths = sorted((RESULTS / "requests").glob("R5A-RUN-*.request.json"))
    attempt_paths = sorted((RESULTS / "attempts").glob("R5A-RUN-*-ATTEMPT-*.json"))
    raw_paths = sorted((RESULTS / "raw_runs").glob("R5A-RUN-*.json"))
    if len(request_paths) != 24 or len(raw_paths) != 24 or not 24 <= len(attempt_paths) <= 48:
        raise PilotError("Round-5 request/attempt/raw-run counts are invalid")
    manifest_hash = protocol_manifest_sha256()
    arms: Counter[str] = Counter()
    formats: Counter[str] = Counter()
    attempts_by_run: Counter[str] = Counter()
    for path in attempt_paths:
        attempt = load_json(path)
        attempts_by_run[attempt.get("run_id")] += 1
    for path in raw_paths:
        raw = load_json(path)
        run_id = raw.get("run_id")
        spec = order.get(run_id)
        if spec is None or any(raw.get(key) != spec[key] for key in ("sequence", "arm", "case_id")):
            raise PilotError(f"Round-5 run identity mismatch: {path.name}")
        request = load_json(RESULTS / "requests" / f"{run_id}.request.json")
        expected_options = {key: SETTINGS[key] for key in ("temperature", "seed", "num_ctx", "num_predict")}
        if request.get("model") != MODEL_TAG or request.get("options") != expected_options:
            raise PilotError(f"Round-5 request settings mismatch: {run_id}")
        if "tools" in request or "tool_choice" in request or len(request.get("messages", [])) != 2:
            raise PilotError(f"Round-5 request enabled tools/history: {run_id}")
        if (
            raw.get("model_tag") != MODEL_TAG
            or raw.get("model_manifest_sha256") != MODEL_MANIFEST_SHA256
            or raw.get("model_blob_sha256") != MODEL_BLOB_SHA256
            or raw.get("round5_protocol_manifest_sha256") != manifest_hash
            or raw.get("request_sha256") != sha256_text(canonical_json(request))
            or raw.get("error") is not None
        ):
            raise PilotError(f"Round-5 custody binding mismatch: {run_id}")
        if attempts_by_run[run_id] not in {1, 2}:
            raise PilotError(f"Round-5 bounded retry count invalid: {run_id}")
        arms[raw["arm"]] += 1
        formats[raw["format_status"]] += 1
    if arms != {"A": 12, "B": 12}:
        raise PilotError(f"Round-5 arm counts are invalid: {dict(arms)}")
    ratings_path = RESULTS / "ratings_surrogate.jsonl"
    reconstructed = construct(
        RESULTS / "stage1_raw_output.json",
        RESULTS / "stage2_raw_output.json",
        RESULTS / "rater_session.json",
    )
    if reconstructed != load_jsonl(ratings_path) or len(reconstructed) != 24:
        raise PilotError("Round-5 canonical ratings do not reconstruct exactly")
    _validate_result_manifest()
    return {
        "lifecycle_state": "POST_EXECUTION",
        "formal_observations": 24,
        "arms": dict(arms),
        "format_statuses": dict(formats),
        "attempts": len(attempt_paths),
        "canonical_ratings": 24,
        "preparation_transitions": lifecycle_transition_record(),
    }


def main() -> int:
    try:
        validate_excluded_checkpoint()
        state = lifecycle_state()
        if state == "PRE_EXECUTION":
            validate_prepared_architecture()
            print("PASS: Round 5A post-execution validator is frozen; lifecycle state = PRE_EXECUTION")
        elif state == "POST_EXECUTION":
            validate_completed_evidence()
            print("PASS: Round 5A post-execution evidence is complete and immutable")
        else:
            raise PilotError("Round-5 lifecycle is incomplete and fails closed")
        return 0
    except (PilotError, OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
