#!/usr/bin/env python3
"""Validate frozen Round 3A preparation without creating a formal observation."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

import validate_protocol
import validate_round2
import validate_round2_publication
from round3_common import (
    BASELINE_HASHES, CHECKPOINT_PATH, CHECKPOINT_SHA256, CHECKPOINT_SIZE,
    CODEX_CLI_VERSION, MODEL_BLOB_SHA256, MODEL_BLOB_SIZE,
    MODEL_MANIFEST_SHA256, MODEL_TAG, OLLAMA_VERSION, RESULTS, ROOT, ROUND3,
    SETTINGS, SOURCE_HASHES, PilotError, formal_observation_count, load_json,
    load_order, sha256_bytes, validate_local_environment, validate_sources,
)


def _tool_event(value: Any) -> bool:
    forbidden = {"tool_call", "function_call", "command_execution", "mcp_tool_call", "exec_command", "shell_command", "computer_call"}
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"type", "kind", "name"} and isinstance(item, str) and (item.lower() in forbidden or "tool_call" in item.lower()):
                return True
            if _tool_event(item):
                return True
    return any(_tool_event(item) for item in value) if isinstance(value, list) else False


def validate_prior_evidence() -> None:
    cases, _gold = validate_protocol.validate_cases_and_gold()
    validate_protocol.validate_execution_order({row["case_id"] for row in cases})
    validate_protocol.validate_json_files()
    validate_protocol.validate_manifest()
    validate_round2.validate_sources()
    validate_round2.validate_calibration()
    validate_round2.validate_manifest()
    validate_round2_publication.validate_all()
    validate_sources()


def validate_bindings_and_order() -> None:
    bindings = load_json(ROUND3 / "SOURCE_BINDINGS.json")
    observed = {row["path"]: row["sha256"] for row in bindings["sources"]}
    if observed != {key: value for key, value in SOURCE_HASHES.items() if key != "round2/DAVID_RATER_CALIBRATION_V1.md"}:
        raise PilotError("Round-3 source bindings are not exact")
    if bindings["calibration"] != {"path": "round2/DAVID_RATER_CALIBRATION_V1.md", "sha256": SOURCE_HASHES["round2/DAVID_RATER_CALIBRATION_V1.md"]}:
        raise PilotError("Round-3 calibration binding is not exact")
    expected_baselines = {
        "round1_result_manifest_sha256": BASELINE_HASHES["results/RESULT_MANIFEST.json"],
        "round2_protocol_manifest_sha256": BASELINE_HASHES["round2/round2_protocol_manifest.json"],
        "round2_result_manifest_sha256": BASELINE_HASHES["results/round2_ministral3b/RESULT_MANIFEST.json"],
        "round2_publication_manifest_sha256": BASELINE_HASHES["results/round2_ministral3b/PUBLICATION_MANIFEST.json"],
    }
    if bindings["frozen_publication_baselines"] != expected_baselines:
        raise PilotError("prior-manifest bindings are not exact")
    checkpoint = bindings["excluded_local_checkpoint"]
    if checkpoint != {"path": "results/ratings_primary.partial.jsonl", "size_bytes": CHECKPOINT_SIZE, "sha256": CHECKPOINT_SHA256, "included_in_round3": False}:
        raise PilotError("excluded checkpoint binding is invalid")
    load_order()


def validate_schema_adapter() -> None:
    canonical1 = load_json(ROUND3 / "schemas/surrogate_extraction_output.schema.json")
    runtime1 = load_json(ROUND3 / "schemas/runtime_surrogate_extraction_output.schema.json")
    expected1 = copy.deepcopy(canonical1)
    expected1["properties"]["stage"]["type"] = "string"
    if expected1 != runtime1:
        raise PilotError("Stage-1 runtime adapter changes more than stage type")
    canonical2 = load_json(ROUND3 / "schemas/surrogate_scoring_output.schema.json")
    runtime2 = load_json(ROUND3 / "schemas/runtime_surrogate_scoring_output.schema.json")
    hard1 = canonical2["properties"]["ratings"]["items"]["properties"]["hard_failures"]
    hard2 = runtime2["properties"]["ratings"]["items"]["properties"]["hard_failures"]
    if hard1.get("uniqueItems") is not True or "uniqueItems" in hard2:
        raise PilotError("Stage-2 uniqueItems separation is invalid")
    expected2 = copy.deepcopy(canonical2)
    expected2["properties"]["stage"]["type"] = "string"
    expected2["properties"]["ratings"]["items"]["properties"]["hard_failures"].pop("uniqueItems")
    if expected2 != runtime2:
        raise PilotError("Stage-2 runtime adapter changes evaluation meaning")
    for path in (ROUND3 / "schemas").glob("*.json"):
        if load_json(path).get("type") != "object":
            raise PilotError(f"invalid Round-3 schema: {path.name}")


def _validate_preflight_stage(evidence: dict[str, Any], stage: str) -> None:
    row = evidence[stage]
    for key in ("prompt", "runtime_schema", "combined_log", "events", "raw_output"):
        path = ROOT / row[f"{key}_path"]
        if not path.is_file() or sha256_bytes(path.read_bytes()) != row[f"{key}_sha256"]:
            raise PilotError(f"{stage} preflight hash mismatch: {key}")
    events = [json.loads(line) for line in (ROOT / row["events_path"]).read_text(encoding="utf-8").splitlines()]
    if [event.get("type") for event in events] != row["event_types"] or row["event_types"] != ["thread.started", "turn.started", "item.completed", "turn.completed"]:
        raise PilotError(f"{stage} preflight event sequence mismatch")
    if _tool_event(events) or row["tool_call_count"] != 0 or any(event.get("type") in {"error", "turn.failed"} for event in events):
        raise PilotError(f"{stage} preflight contains failure or tool access")
    if events[0].get("thread_id") != row["session_id"]:
        raise PilotError(f"{stage} preflight session mismatch")
    output = load_json(ROOT / row["raw_output_path"])
    expected_stage = "DECISION_EXTRACTION" if stage == "stage1" else "GOLD_DISCLOSED_SCORING"
    if output.get("stage") != expected_stage or not isinstance(output.get("ratings"), list) or len(output["ratings"]) != 24:
        raise PilotError(f"{stage} preflight output mismatch")
    if [item.get("response_id") for item in output["ratings"]] != [f"R3R{i:03d}" for i in range(1, 25)]:
        raise PilotError(f"{stage} preflight placeholder IDs mismatch")
    if row["rating_count"] != 24 or row["schema_accepted"] is not True or row["request_rejected"] is not False:
        raise PilotError(f"{stage} preflight disposition mismatch")


def validate_preflight() -> None:
    evidence = load_json(ROUND3 / "preflight/SCHEMA_PREFLIGHT_EVIDENCE.json")
    fixed = {
        "record_type": "ROUND3A_EXCLUDED_CASE_FREE_SCHEMA_COMPATIBILITY_PREFLIGHT",
        "provider": "OpenAI", "model": "gpt-5.6-sol", "reasoning": "xhigh",
        "codex_cli_version": CODEX_CLI_VERSION, "excluded_from_formal_observations": True,
        "excluded_from_formal_ratings": True, "contains_formal_case_content": False,
        "contains_frozen_prompt_content": False, "contains_gold": False,
        "contains_granite_response": False, "contains_david_calibration": False,
    }
    for key, value in fixed.items():
        if evidence.get(key) != value:
            raise PilotError(f"preflight evidence mismatch: {key}")
    round2 = evidence["round2_rejection_evidence"]
    for stage in ("stage1", "stage2"):
        path = ROOT / round2[f"{stage}_path"]
        if sha256_bytes(path.read_bytes()) != round2[f"{stage}_sha256"]:
            raise PilotError(f"Round-2 {stage} rejection evidence mismatch")
        _validate_preflight_stage(evidence, stage)
    combined = b"".join((ROOT / evidence[stage][f"{key}_path"]).read_bytes() for stage in ("stage1", "stage2") for key in ("prompt", "raw_output"))
    text = combined.decode("utf-8")
    for case in json.loads("[" + ",".join((ROOT / "data/pilot_cases.jsonl").read_text(encoding="utf-8").splitlines()) + "]"):
        for field in ("case_id", "scenario", "requested_action"):
            if case[field] in text:
                raise PilotError(f"formal case content leaked into schema preflight: {case['case_id']} {field}")
    for forbidden in ((ROOT / "prompts/arm_a_system.txt").read_text(encoding="utf-8"), (ROOT / "prompts/arm_b_system.txt").read_text(encoding="utf-8"), (ROOT / "round2/DAVID_RATER_CALIBRATION_V1.md").read_text(encoding="utf-8")):
        if forbidden in text:
            raise PilotError("frozen prompt or calibration leaked into schema preflight")


def validate_model_record(live: bool = True) -> None:
    record = load_json(ROUND3 / "MODEL_AND_ENVIRONMENT.json")
    model = record["ollama"]
    if (model["model_tag"], model["manifest_sha256"], model["model_blob_sha256"], model["model_blob_size_bytes"], model["model_family"], model["parameter_count"], model["quantization"]) != (MODEL_TAG, MODEL_MANIFEST_SHA256, MODEL_BLOB_SHA256, MODEL_BLOB_SIZE, "granite", 3_402_836_480, "Q4_K_M"):
        raise PilotError("frozen Granite identity record mismatch")
    if record["generation_settings"] != {**SETTINGS, "conversation_history": False}:
        raise PilotError("frozen generation settings mismatch")
    preflight = record["excluded_case_free_generation_preflight"]
    if preflight.get("excluded_from_formal_evidence") is not True or preflight.get("contains_formal_case_content") is not False or preflight.get("result") != "PASS: exact four generation options accepted":
        raise PilotError("Granite options preflight disposition mismatch")
    request = preflight["request"]
    if request.get("model") != MODEL_TAG or request.get("options") != {key: SETTINGS[key] for key in ("temperature", "seed", "num_ctx", "num_predict")}:
        raise PilotError("Granite options preflight did not use exact settings")
    if preflight["response"].get("model") != MODEL_TAG or preflight["response"].get("done") is not True:
        raise PilotError("Granite options preflight response mismatch")
    if live:
        validate_local_environment()


def validate_zero_formal_observations() -> None:
    if formal_observation_count() != 0:
        raise PilotError("formal Granite observations are not 0/24")
    allowed = {".gitkeep"}
    unexpected = [path for path in RESULTS.rglob("*") if path.is_file() and path.name not in allowed]
    if unexpected:
        raise PilotError(f"unexpected Round-3 result artifact before authorization: {unexpected}")


def validate_manifest() -> None:
    from build_round3_protocol_manifest import FILES

    manifest = load_json(ROUND3 / "round3_protocol_manifest.json")
    if manifest.get("protocol_version") != "round3a-v1" or manifest.get("formal_observations_before_freeze") != 0:
        raise PilotError("Round-3 manifest version or pre-freeze count mismatch")
    rows = manifest.get("files")
    if manifest.get("file_count") != len(FILES) or not isinstance(rows, list) or len(rows) != len(FILES):
        raise PilotError("Round-3 manifest file count mismatch")
    if [row.get("path") for row in rows] != FILES:
        raise PilotError("Round-3 manifest path inventory mismatch")
    for row in rows:
        path = ROOT / row["path"]
        payload = path.read_bytes()
        if len(payload) != row["size_bytes"] or sha256_bytes(payload) != row["sha256"]:
            raise PilotError(f"Round-3 manifest hash mismatch: {row['path']}")


def validate_pre_manifest(live_model: bool = True) -> None:
    validate_prior_evidence()
    validate_bindings_and_order()
    validate_schema_adapter()
    validate_preflight()
    validate_model_record(live=live_model)
    validate_zero_formal_observations()


def main() -> int:
    try:
        validate_pre_manifest(live_model=True)
        validate_manifest()
        if CHECKPOINT_PATH.stat().st_size != CHECKPOINT_SIZE or sha256_bytes(CHECKPOINT_PATH.read_bytes()) != CHECKPOINT_SHA256:
            raise PilotError("excluded checkpoint changed during validation")
        print("PASS: Round 3A preparation is frozen and valid; formal observations = 0/24")
        return 0
    except (PilotError, OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
