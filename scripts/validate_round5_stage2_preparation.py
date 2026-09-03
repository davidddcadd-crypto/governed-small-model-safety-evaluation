#!/usr/bin/env python3
"""Validate local-only Round 5A Stage-2 construction without transmission."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from build_round5_stage2_preparation import END, PREAMBLE, START
from round5_common import RESULTS, ROOT, PilotError, load_json, load_jsonl, sha256_bytes

STAGE1_SESSION_ID = "01a06754-52d6-77a1-8312-2b637d14f237"
STAGE1_RAW_OUTPUT_SHA256 = "cf249fe6b9886e841b72a9470906aabb353114166121667322d2d1ef992ea0c1"
STAGE2_RUNTIME_SCHEMA_SHA256 = "3ad19c65303dd4774458fff146434dfccef960d79e2acfd5d3ae47e1abfb70a1"
FROZEN_HASHES = {
    "round5/round5_protocol_manifest_v3.json": "a556679cc276422f250d556f0b512334652b40eb7c35bbe07a45551d4290fd5b",
    "round5/schemas/runtime_surrogate_scoring_output.schema.json": STAGE2_RUNTIME_SCHEMA_SHA256,
    "results/round5_granite4_3b/formal_raw_results.jsonl": "11ed3d64f40ca072ba57e744171c528be92cf0db10cba475a093e8d6c8e76ab3",
    "results/round5_granite4_3b/stage1_prompt.txt": "c29e582edeb4fca8ee9c050b5f51631232b2bc96793b20decf1ce5b23ac814c5",
    "results/round5_granite4_3b/blinded_extraction_packet.jsonl": "38c1ef004758dcd0cc64c54d624e683f8f7dddd948e552c73bc067de914157cc",
    "results/round5_granite4_3b/STAGE1_TRANSMISSION_AUTHORIZATION.json": "66fc7af5d606186e02124d95808d0cde758c5b4e4b2af9bfba96c54188aa60d2",
    "results/round5_granite4_3b/stage1_events.jsonl": "2b82fdc998f7c1eb9dc228d35ed3c9afd1c720e64c4850d0520e843330bf3a3c",
    "results/round5_granite4_3b/stage1_raw_output.json": STAGE1_RAW_OUTPUT_SHA256,
    "results/round5_granite4_3b/stage1_combined.log": "44fe2917380e694cb3f1f43cf338b97299b929e74644f6f2254dee7b37aab0b7",
    "results/round5_granite4_3b/STAGE1_SESSION_CUSTODY.json": "1938fb32dcb2979695d8a63ef3d56231fdbe576c4abbf58b9cae9d93280f0762",
    "results/round5_granite4_3b/STAGE1_VALIDATION.json": "0866f3bcf1fd918643de1412f0a05a4bc3ec1f1e18748a8b29807ac856dce714",
    "results/round5_granite4_3b/STAGE1_LIFECYCLE_DIAGNOSTIC.json": "9ccb21964800716256151fcca38621e36bbc5ae06ccde73818cf4b78698c6d91",
    "results/round5_granite4_3b/STAGE2_LOCAL_PREPARATION_AUTHORIZATION.json": "ef6c420053c5fe262dd08cdbe164bae50fef438a610493f12417d2bba9a40588",
    "results/round5_granite4_3b/ROUND5_STAGE1_POSTCOMPLETION_LIFECYCLE_REPAIR.json": "38eb9f8589e6353730387ab207f80fbae9bba2047c835093d625a0ada285965a",
    "results/round5_granite4_3b/ROUND5_STAGE1_POSTCOMPLETION_DISCLOSURE.md": "82698b4575feac70a0bcb57d7de1625dc011b5c1ff0c1b2d4d505c14bd9bc4c3",
}
ROW_KEYS = {
    "response_id", "scenario", "requested_action", "raw_response", "format_status",
    "frozen_extracted_decision", "extraction_evidence", "gold_record",
    "stage1_raw_output_sha256",
}
FORBIDDEN_KEYS = {
    "arm", "run_id", "sequence", "case_id", "model", "model_tag", "timing",
    "latency", "prompt_eval_count", "eval_count", "blinding_key",
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PilotError(message)


def _require_hashes(bindings: dict[str, str]) -> None:
    for relative, expected in bindings.items():
        path = ROOT / relative
        _require(path.is_file() and sha256_bytes(path.read_bytes()) == expected, f"artifact byte mismatch: {relative}")


def _expected_rows() -> list[dict[str, Any]]:
    stage1_packet = load_jsonl(RESULTS / "blinded_extraction_packet.jsonl")
    stage1_output = load_json(RESULTS / "stage1_raw_output.json")
    extractions = {row["response_id"]: row for row in stage1_output["ratings"]}
    key = load_json(RESULTS / "blinding_key.json")
    mapping = {row["response_id"]: row for row in key["entries"]}
    gold = {row["case_id"]: row for row in load_jsonl(ROOT / "data/gold_records.jsonl")}
    expected = []
    for source in stage1_packet:
        rid = source["response_id"]
        record = dict(gold[mapping[rid]["case_id"]])
        record.pop("case_id", None)
        expected.append({
            **source,
            "frozen_extracted_decision": extractions[rid]["extracted_decision"],
            "extraction_evidence": extractions[rid]["extraction_evidence"],
            "gold_record": record,
            "stage1_raw_output_sha256": STAGE1_RAW_OUTPUT_SHA256,
        })
    return expected


def validate_stage2_preparation() -> dict[str, Any]:
    _require_hashes(FROZEN_HASHES)
    custody = load_json(RESULTS / "STAGE1_SESSION_CUSTODY.json")
    _require(custody.get("session_id") == STAGE1_SESSION_ID, "Stage-1 session ID mismatch")
    _require(custody.get("stage1_output_frozen") is True and custody.get("stage1_revision_authorized") is False, "Stage-1 is not frozen")
    packet_path = RESULTS / "blinded_scoring_packet.jsonl"
    prompt_path = RESULTS / "stage2_prompt.txt"
    rows = load_jsonl(packet_path)
    _require(len(rows) == 24, "Stage-2 packet does not contain 24 rows")
    _require([row.get("response_id") for row in rows] == [f"R5R{i:03d}" for i in range(1, 25)], "Stage-2 response IDs mismatch")
    _require(all(set(row) == ROW_KEYS and not (set(row) & FORBIDDEN_KEYS) for row in rows), "Stage-2 packet surface leaks forbidden fields")
    _require(rows == _expected_rows(), "Stage-2 packet does not deterministically derive from frozen Stage-1 and gold")
    _require(all(row.get("stage1_raw_output_sha256") == STAGE1_RAW_OUTPUT_SHA256 for row in rows), "Stage-2 rows do not bind frozen Stage-1")
    packet = packet_path.read_text(encoding="utf-8").rstrip("\r\n")
    prompt = prompt_path.read_text(encoding="utf-8")
    _require(prompt == PREAMBLE + START + packet + END, "Stage-2 prompt does not embed the packet exactly")
    lowered = prompt.lower()
    for forbidden_text in ("granite4:3b", "r5a-run-", "blinding_seed", "prompt_eval_count", "eval_count"):
        _require(forbidden_text not in lowered, f"Stage-2 prompt leaks forbidden content: {forbidden_text}")
    future_artifacts = (
        "STAGE2_TRANSMISSION_AUTHORIZATION.json", "stage2_events.jsonl", "stage2_raw_output.json",
        "rater_session.json", "ratings_surrogate.jsonl", "metrics_round5.json",
    )
    _require(not any((RESULTS / name).exists() for name in future_artifacts), "unauthorized Stage-2/rating/result artifact exists")
    custody_path = RESULTS / "STAGE2_PREPARATION_CUSTODY.json"
    if custody_path.exists():
        stage2_custody = load_json(custody_path)
        _require(stage2_custody.get("frozen_stage1_binding", {}).get("raw_output_sha256") == STAGE1_RAW_OUTPUT_SHA256, "Stage-2 custody Stage-1 binding mismatch")
        derivation = stage2_custody.get("deterministic_derivation", {})
        _require(derivation.get("stage2_scoring_payload", {}).get("sha256") == sha256_bytes(packet_path.read_bytes()), "Stage-2 custody payload binding mismatch")
        _require(derivation.get("stage2_prompt", {}).get("sha256") == sha256_bytes(prompt_path.read_bytes()), "Stage-2 custody prompt binding mismatch")
        _require(derivation.get("stage2_runtime_schema", {}).get("sha256") == STAGE2_RUNTIME_SCHEMA_SHA256, "Stage-2 custody runtime-schema binding mismatch")
        _require(stage2_custody.get("isolation_audit", {}).get("result") == "PASS", "Stage-2 custody isolation audit is not PASS")
        activities = stage2_custody.get("activity_counts", {})
        _require(all(activities.get(key) == 0 for key in ("stage1_session_resumes", "stage2_transmissions", "gold_disclosures_to_openai", "formal_ratings", "model_executions", "observation_reruns", "commits", "pushes", "tags", "releases", "publications")), "Stage-2 custody reports prohibited activity")
    validation_path = RESULTS / "STAGE2_PREPARATION_VALIDATION.json"
    if validation_path.exists():
        validation = load_json(validation_path)
        _require(validation.get("result") == "PASS_WAITING_FOR_STAGE2_OWNER_AUTHORIZATION", "Stage-2 validation record result mismatch")
        _require(validation.get("frozen_stage1", {}).get("raw_output_sha256") == STAGE1_RAW_OUTPUT_SHA256, "Stage-2 validation record Stage-1 binding mismatch")
        stage2 = validation.get("stage2", {})
        _require(stage2.get("custody_sha256") == sha256_bytes(custody_path.read_bytes()), "Stage-2 validation record custody binding mismatch")
        _require(stage2.get("prompt_sha256") == sha256_bytes(prompt_path.read_bytes()), "Stage-2 validation record prompt binding mismatch")
        _require(stage2.get("scoring_payload_sha256") == sha256_bytes(packet_path.read_bytes()), "Stage-2 validation record payload binding mismatch")
        _require(stage2.get("runtime_schema_sha256") == STAGE2_RUNTIME_SCHEMA_SHA256, "Stage-2 validation record schema binding mismatch")
        _require(stage2.get("deterministic_derivation") == "PASS" and stage2.get("isolation_content_audit") == "PASS", "Stage-2 validation record audit mismatch")
        isolated = validation.get("isolated_clean_checkout_validation", {})
        _require(isolated.get("result") == "PASS" and isolated.get("byte_mismatch_count") == 0 and isolated.get("excluded_checkpoint_absent") is True, "isolated clean-checkout validation record mismatch")
        prohibited = validation.get("prohibited_activity_counts", {})
        _require(all(prohibited.get(key) == 0 for key in ("stage2_transmissions", "stage1_session_resumes", "gold_disclosures_to_openai", "formal_ratings", "model_executions", "observation_reruns", "commits", "pushes", "tags", "releases", "publications")), "Stage-2 validation record reports prohibited activity")
    return {
        "result": "PASS",
        "stage1_session_id": STAGE1_SESSION_ID,
        "stage1_output_sha256": STAGE1_RAW_OUTPUT_SHA256,
        "stage1_output_unchanged": True,
        "stage1_extraction_revision_count": 0,
        "stage2_row_count": 24,
        "stage2_prompt_sha256": sha256_bytes(prompt_path.read_bytes()),
        "stage2_payload_sha256": sha256_bytes(packet_path.read_bytes()),
        "stage2_runtime_schema_sha256": STAGE2_RUNTIME_SCHEMA_SHA256,
        "isolation_audit": "PASS",
        "stage2_transmissions": 0,
        "stage1_session_resumes": 0,
        "formal_ratings": 0,
    }


def main() -> int:
    try:
        validate_stage2_preparation()
        print("PASS: local-only Round 5A Stage-2 preparation is valid and untransmitted")
        return 0
    except (PilotError, OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
