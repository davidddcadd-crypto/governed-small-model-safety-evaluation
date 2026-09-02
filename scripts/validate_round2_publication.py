#!/usr/bin/env python3
"""Validate additive Round 2A publication evidence without writing files."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from round2_common import RESULTS, ROOT, PilotError, load_json, sha256_bytes
from build_round2_publication_manifest import (
    ADDITIVE_PATHS, BASE_RESULT_MANIFEST_SHA256,
)

ROUND1_RESULT_MANIFEST_SHA256 = (
    "49e6726a849a71842564fc33dcde328680683ae85981ebebe7261c0f9f83da97"
)
ROUND1_RATINGS_SHA256 = (
    "114e940605fc0cdca16969e3abd6c8600ca1d2967bbe464d38619c769486265f"
)
ROUND1_METRICS_SHA256 = (
    "d8798a3bda1d8435458f0e3efd5f37762c4063c60596ae130e0b6b885cba58de"
)
REQUIRED_ADDENDUM_TEXT = (
    "second prespecified within-model Arm A/B evaluation",
    "cross-model replication attempt using `ministral-3:3b`",
    "12 synthetic cases",
    "one observation per case-arm",
    "24 total formal observations",
    "24/24 responses were `FORMAT_FAIL`",
    "Strict Safety Pass: 33.3% -> 66.7%",
    "Exact Decision Accuracy: 75.0% -> 83.3%",
    "Unsafe Allow: 0 -> 0",
    "Hard Failures: 1 -> 0",
    "Prespecified signal: `SUPPORTIVE`",
    "Escalation Recall: 100% -> 75%",
    "`FORMAT_FAIL`: 100% -> 100%",
    "Arm B produced one false refusal",
    "Arm A produced one `PROHIBITED_BYPASS_GUIDANCE` hard failure",
    "Round 1 primary rater was David / Tai Wai Lee, human",
    "David-calibrated OpenAI `gpt-5.6-sol` xhigh AI surrogate",
    "not human-equivalent",
    "not ground truth",
    "not an independent human expert",
    "No per-response Round-1 ratings, blinding key, arm mapping, latency/token",
    "calibration did contain Round-1-derived aggregate information",
    "not a controlled model comparison",
    "rejected before model sampling",
    "`stage` property lacked an explicit `type`",
    "`uniqueItems` was unsupported",
    "contains no `item.completed` event",
    "Only isolated runtime-schema compatibility hints changed",
    "frozen evaluation schemas, scoring semantics, canonical rating records, and",
    "do not establish statistical significance",
    "production safety",
    "model-family generalization",
    "frontier equivalence",
    "proof that governance works generally",
)


def _validate_bound_manifest(path: Path, expected_count: int) -> None:
    value = load_json(path)
    files = value.get("files")
    if value.get("file_count") != expected_count or not isinstance(files, list):
        raise PilotError(f"manifest file count mismatch: {path}")
    if len(files) != expected_count:
        raise PilotError(f"manifest entry count mismatch: {path}")
    for entry in files:
        target = ROOT / entry["path"]
        if not target.is_file():
            raise PilotError(f"manifest file is missing: {entry['path']}")
        payload = target.read_bytes()
        if len(payload) != entry["size_bytes"] or sha256_bytes(payload) != entry["sha256"]:
            raise PilotError(f"manifest file mismatch: {entry['path']}")


def validate_frozen_evidence() -> None:
    round2 = RESULTS / "RESULT_MANIFEST.json"
    if sha256_bytes(round2.read_bytes()) != BASE_RESULT_MANIFEST_SHA256:
        raise PilotError("frozen Round-2 result manifest changed")
    _validate_bound_manifest(round2, 92)
    round1 = ROOT / "results" / "RESULT_MANIFEST.json"
    if sha256_bytes(round1.read_bytes()) != ROUND1_RESULT_MANIFEST_SHA256:
        raise PilotError("frozen Round-1 result manifest changed")
    _validate_bound_manifest(round1, 82)
    if sha256_bytes((ROOT / "results/ratings_primary.jsonl").read_bytes()) != ROUND1_RATINGS_SHA256:
        raise PilotError("frozen Round-1 ratings changed")
    if sha256_bytes((ROOT / "results/PILOT_METRICS.json").read_bytes()) != ROUND1_METRICS_SHA256:
        raise PilotError("frozen Round-1 metrics changed")


def validate_addendum() -> None:
    text = (RESULTS / "ROUND2_PUBLICATION_ADDENDUM.md").read_text(encoding="utf-8")
    normalized = " ".join(text.split())
    missing = [
        item for item in REQUIRED_ADDENDUM_TEXT
        if " ".join(item.split()) not in normalized
    ]
    if missing:
        raise PilotError(f"publication addendum disclosure is incomplete: {missing}")


def validate_rejection_log(path: Path, required_error_text: str) -> dict[str, Any]:
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            raise PilotError(f"blank rejection-log line: {path}:{number}")
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise PilotError(f"invalid rejection-log JSON: {path}:{number}") from exc
    types = [row.get("type") for row in rows]
    if types != ["thread.started", "turn.started", "error", "turn.failed"]:
        raise PilotError(f"unexpected rejection-log event sequence: {path.name}")
    if "item.completed" in types:
        raise PilotError(f"sampled model output present in rejection log: {path.name}")
    combined = json.dumps(rows, ensure_ascii=False)
    if "invalid_json_schema" not in combined or required_error_text not in combined:
        raise PilotError(f"schema rejection reason mismatch: {path.name}")
    return {
        "event_types": types,
        "item_completed_count": 0,
        "turn_failed_count": 1,
        "model_response_sampled": False,
        "size_bytes": len(path.read_bytes()),
        "sha256": sha256_bytes(path.read_bytes()),
    }


def validate_provenance() -> None:
    provenance = load_json(
        RESULTS / "publication_disclosures/SCHEMA_REJECTION_PROVENANCE.json"
    )
    if provenance.get("record_type") != "ROUND2A_PRE_SAMPLING_SCHEMA_REJECTION_PROVENANCE":
        raise PilotError("schema-rejection provenance type mismatch")
    frozen = provenance.get("frozen_result_manifest", {})
    if (
        frozen.get("sha256") != BASE_RESULT_MANIFEST_SHA256
        or frozen.get("file_count") != 92
        or frozen.get("modified_by_repair") is not False
    ):
        raise PilotError("schema-rejection provenance does not bind frozen results")
    records = provenance.get("rejections")
    if not isinstance(records, list) or len(records) != 2:
        raise PilotError("schema-rejection provenance must contain two records")
    expected = (
        ("STAGE1_SCHEMA_REJECTION.jsonl", "must have a 'type' key"),
        ("STAGE2_SCHEMA_REJECTION.jsonl", "'uniqueItems' is not permitted"),
    )
    for record, (name, reason) in zip(records, expected, strict=True):
        path = RESULTS / "publication_disclosures" / name
        observed = validate_rejection_log(path, reason)
        if (
            record.get("preserved_path") != path.relative_to(ROOT).as_posix()
            or record.get("size_bytes") != observed["size_bytes"]
            or record.get("sha256") != observed["sha256"]
            or record.get("event_types") != observed["event_types"]
            or record.get("item_completed_count") != 0
            or record.get("turn_failed_count") != 1
            or record.get("model_response_sampled") is not False
        ):
            raise PilotError(f"schema-rejection provenance mismatch: {name}")


def validate_publication_manifest() -> None:
    path = RESULTS / "PUBLICATION_MANIFEST.json"
    value = load_json(path)
    required = {
        "publication_manifest_version", "generated_at", "manifest_purpose",
        "base_result_manifest", "additive_file_count", "additive_files",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise PilotError("publication manifest keys are invalid")
    if value["publication_manifest_version"] != "round2a-publication-v1":
        raise PilotError("publication manifest version mismatch")
    base = value["base_result_manifest"]
    if base != {
        "path": "results/round2_ministral3b/RESULT_MANIFEST.json",
        "sha256": BASE_RESULT_MANIFEST_SHA256,
        "file_count": 92,
    }:
        raise PilotError("publication manifest base binding mismatch")
    expected_paths = [
        path.relative_to(ROOT).as_posix() for path in sorted(ADDITIVE_PATHS)
    ]
    rows = value["additive_files"]
    if value["additive_file_count"] != 4 or len(rows) != 4:
        raise PilotError("publication manifest additive file count mismatch")
    if [row.get("path") for row in rows] != expected_paths:
        raise PilotError("publication manifest additive paths mismatch")
    for row in rows:
        target = ROOT / row["path"]
        payload = target.read_bytes()
        if len(payload) != row["size_bytes"] or sha256_bytes(payload) != row["sha256"]:
            raise PilotError(f"publication manifest hash mismatch: {row['path']}")


def validate_all() -> None:
    validate_frozen_evidence()
    validate_addendum()
    validate_provenance()
    validate_publication_manifest()


def main() -> int:
    try:
        validate_all()
        print(
            "PASS: additive Round 2A publication disclosures and frozen "
            "Round-1/Round-2 evidence are valid"
        )
        return 0
    except (PilotError, OSError, KeyError, TypeError, ValueError) as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
