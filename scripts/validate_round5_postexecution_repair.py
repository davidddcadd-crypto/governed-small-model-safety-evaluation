#!/usr/bin/env python3
"""Validate the additive Round 5A post-execution custody/lifecycle repair."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from round5_common import (
    CHECKPOINT_PATH,
    CHECKPOINT_SHA256,
    CHECKPOINT_SIZE,
    MODEL_BLOB_SHA256,
    MODEL_MANIFEST_SHA256,
    MODEL_TAG,
    RESULTS,
    ROOT,
    SETTINGS,
    PilotError,
    canonical_json,
    extract_formal_output,
    load_json,
    load_jsonl,
    load_order,
    protocol_manifest_sha256,
    sha256_bytes,
    sha256_text,
    validate_sources,
)

FROZEN_HASHES = {
    "round5/round5_protocol_manifest_v3.json": "a556679cc276422f250d556f0b512334652b40eb7c35bbe07a45551d4290fd5b",
    "round5/LIFECYCLE_VALIDATION_PLAN.md": "6389a621a2a849c5bbb531e4c806e7c4471b3aeeb07e1f7555eb6afe4d7005cb",
    "round5/schemas/runtime_surrogate_extraction_output.schema.json": "8b00434b0db5ad15dbd487b16dd4e5d7f04e80fcb0780892412b5fd30fde833a",
    "scripts/validate_round5_preparation.py": "31e47433279d37c79f6e740515daf5d3f49cefd2fb906f21e68c73a6290e8d6b",
    "scripts/validate_round5_postexecution.py": "fb00b69a51fe559e23577f33a9f734731118cc2a87a251f6101a9adef5b03182",
    "tests/test_round5_preparation.py": "eef2e4d556771da7e432b5f6a4d504462ee1f2977a55c2b97dc4c3b2e550b35d",
    "results/round5_granite4_3b/formal_raw_results.jsonl": "11ed3d64f40ca072ba57e744171c528be92cf0db10cba475a093e8d6c8e76ab3",
    "results/round5_granite4_3b/blinded_extraction_packet.jsonl": "38c1ef004758dcd0cc64c54d624e683f8f7dddd948e552c73bc067de914157cc",
    "results/round5_granite4_3b/blinding_key.json": "79e4c6b55a1059595f6fff9f1ba89e01106487c314e91421c2c12a2bda45496b",
    "results/round5_granite4_3b/stage1_prompt.txt": "c29e582edeb4fca8ee9c050b5f51631232b2bc96793b20decf1ce5b23ac814c5",
    "results/round5_granite4_3b/attempts/R5A-RUN-016-INTERRUPTION-CUSTODY.json": "c6c1bb89916719556354cae48ed92641bed45a5d51ab341f3d38b371448b2d9c",
    "results/round5_granite4_3b/attempts/R5A-RUN-016-INTERRUPTION-CUSTODY-CORRECTION.json": "c73b505506df2fcfb00ff9592615e39c744d42e78d14dfcb2ca70af87036d0c6",
    "results/round5_granite4_3b/requests/R5A-RUN-016.request.json": "20ea0c3fc86916ee45dcc0be92861bb4627cb0e410e64c3c79ff10d149322f1c",
    "results/round5_granite4_3b/attempts/R5A-RUN-016-ATTEMPT-01.json": "653d8484e20bcc6daf46b735844104aa24e6286175a93e266f000e78974d0228",
    "results/round5_granite4_3b/raw_runs/R5A-RUN-016.json": "e8b8dbf2e58cdc70ee01496779a0128428e2da15bcbfb50ee20ca7cc373af9bd",
}

ADDITIVE_HASHES = {
    "results/round5_granite4_3b/POSTEXECUTION_REPAIR_AUTHORIZATION.json": "a4c543a08dda60e6f72c48b0cfa3c0fd58590d791c42575abeb1f09d8a5e5165",
    "results/round5_granite4_3b/ROUND5_POSTEXECUTION_CUSTODY_REPAIR.json": "7fa72bdb32b08f93339c82a10b5d6a1c58a620148cc3af1c34e39e84ec12ef36",
    "results/round5_granite4_3b/ROUND5_POSTEXECUTION_CUSTODY_DISCLOSURE.md": "a47d6f94b5ad08066743ae67845d02008901ab22cf614a0955f13ca4386fcbc3",
    "results/round5_granite4_3b/ROUND5_FROZEN_POSTEXECUTION_INVENTORY.json": "7f70e694db7bb808e9b4644ca711292f1a85f5a1279f7cb4fdb9a61e0e39ebe1",
}

STAGE1_HASHES = {
    "results/round5_granite4_3b/STAGE1_TRANSMISSION_AUTHORIZATION.json": "66fc7af5d606186e02124d95808d0cde758c5b4e4b2af9bfba96c54188aa60d2",
    "results/round5_granite4_3b/stage1_events.jsonl": "2b82fdc998f7c1eb9dc228d35ed3c9afd1c720e64c4850d0520e843330bf3a3c",
    "results/round5_granite4_3b/stage1_raw_output.json": "cf249fe6b9886e841b72a9470906aabb353114166121667322d2d1ef992ea0c1",
    "results/round5_granite4_3b/stage1_combined.log": "44fe2917380e694cb3f1f43cf338b97299b929e74644f6f2254dee7b37aab0b7",
    "results/round5_granite4_3b/STAGE1_SESSION_CUSTODY.json": "1938fb32dcb2979695d8a63ef3d56231fdbe576c4abbf58b9cae9d93280f0762",
    "results/round5_granite4_3b/STAGE1_VALIDATION.json": "0866f3bcf1fd918643de1412f0a05a4bc3ec1f1e18748a8b29807ac856dce714",
    "results/round5_granite4_3b/STAGE1_LIFECYCLE_DIAGNOSTIC.json": "9ccb21964800716256151fcca38621e36bbc5ae06ccde73818cf4b78698c6d91",
}

STAGE1_REPAIR_HASHES = {
    "results/round5_granite4_3b/STAGE2_LOCAL_PREPARATION_AUTHORIZATION.json": "ef6c420053c5fe262dd08cdbe164bae50fef438a610493f12417d2bba9a40588",
    "results/round5_granite4_3b/ROUND5_STAGE1_POSTCOMPLETION_LIFECYCLE_REPAIR.json": "38eb9f8589e6353730387ab207f80fbae9bba2047c835093d625a0ada285965a",
    "results/round5_granite4_3b/ROUND5_STAGE1_POSTCOMPLETION_DISCLOSURE.md": "82698b4575feac70a0bcb57d7de1625dc011b5c1ff0c1b2d4d505c14bd9bc4c3",
}

TRANSITIONS = [
    "tests/test_round5_preparation.py::test_zero_formal_observations",
    "tests/test_round5_preparation.py::test_result_manifest_refuses_incomplete_evidence",
    "tests/test_round5_preparation.py::test_lifecycle_architecture_is_frozen",
]

STAGE1_COMPLETION_TRANSITIONS = [
    "scripts/validate_round5_postexecution_repair.py::validate_stage1_preparation pre-Stage-1 absence gate",
    "tests/test_round5_postexecution_repair.py::test_stage1_remains_local_frozen_and_untransmitted",
]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PilotError(message)


def _require_hashes(bindings: dict[str, str]) -> None:
    for relative, expected in bindings.items():
        path = ROOT / relative
        _require(
            path.is_file() and sha256_bytes(path.read_bytes()) == expected,
            f"artifact byte mismatch: {relative}",
        )


def validate_checkpoint() -> None:
    if not CHECKPOINT_PATH.exists():
        return
    _require(CHECKPOINT_PATH.is_file(), "excluded checkpoint is not a file")
    _require(CHECKPOINT_PATH.stat().st_size == CHECKPOINT_SIZE, "excluded checkpoint size changed")
    _require(sha256_bytes(CHECKPOINT_PATH.read_bytes()) == CHECKPOINT_SHA256, "excluded checkpoint bytes changed")


def validate_inventory() -> None:
    value = load_json(RESULTS / "ROUND5_FROZEN_POSTEXECUTION_INVENTORY.json")
    rows = value.get("files")
    _require(isinstance(rows, list) and value.get("file_count") == len(rows) == 82, "evidence inventory count mismatch")
    _require(len({row.get("path") for row in rows}) == len(rows), "evidence inventory contains duplicate paths")
    counts = value.get("counts", {})
    _require(counts == {"request_files": 24, "first_attempt_files": 24, "raw_run_files": 24}, "evidence inventory role counts mismatch")
    for row in rows:
        path = ROOT / row["path"]
        payload = path.read_bytes()
        _require(len(payload) == row.get("size_bytes"), f"inventory size mismatch: {row.get('path')}")
        _require(sha256_bytes(payload) == row.get("sha256"), f"inventory hash mismatch: {row.get('path')}")


def validate_formal_evidence() -> dict[str, Any]:
    order = load_order()
    request_paths = sorted((RESULTS / "requests").glob("R5A-RUN-*.request.json"))
    attempt_paths = sorted((RESULTS / "attempts").glob("R5A-RUN-*-ATTEMPT-*.json"))
    raw_paths = sorted((RESULTS / "raw_runs").glob("R5A-RUN-*.json"))
    _require(len(request_paths) == len(attempt_paths) == len(raw_paths) == 24, "formal evidence count mismatch")
    _require(all(path.name.endswith("-ATTEMPT-01.json") for path in attempt_paths), "non-first formal attempt exists")
    rows: list[dict[str, Any]] = []
    arms: Counter[str] = Counter()
    formats: Counter[str] = Counter()
    for spec, raw_path in zip(order, raw_paths, strict=True):
        raw = load_json(raw_path)
        run_id = spec["run_id"]
        _require(raw_path.name == f"{run_id}.json", f"raw-run order mismatch: {raw_path.name}")
        _require(all(raw.get(key) == spec[key] for key in ("run_id", "sequence", "arm", "case_id")), f"run identity mismatch: {run_id}")
        request = load_json(RESULTS / "requests" / f"{run_id}.request.json")
        attempt = load_json(RESULTS / "attempts" / f"{run_id}-ATTEMPT-01.json")
        expected_options = {key: SETTINGS[key] for key in ("temperature", "seed", "num_ctx", "num_predict")}
        _require(request.get("model") == MODEL_TAG and request.get("options") == expected_options, f"request settings mismatch: {run_id}")
        _require("tools" not in request and "tool_choice" not in request and len(request.get("messages", [])) == 2, f"tools/history enabled: {run_id}")
        request_sha = sha256_text(canonical_json(request))
        _require(attempt.get("status") == "OK", f"formal attempt is not OK: {run_id}")
        _require(attempt.get("attempt_id") == raw.get("attempt_id") == f"{run_id}-ATTEMPT-01", f"attempt binding mismatch: {run_id}")
        _require(attempt.get("request_sha256") == raw.get("request_sha256") == request_sha, f"request hash mismatch: {run_id}")
        body = attempt.get("raw_api_body")
        _require(isinstance(body, str), f"raw API body missing: {run_id}")
        body_sha = sha256_text(body)
        _require(attempt.get("raw_api_body_sha256") == raw.get("raw_api_body_sha256") == body_sha, f"API body hash mismatch: {run_id}")
        _require(json.loads(body) == attempt.get("api_response"), f"API body parse mismatch: {run_id}")
        response, format_status, parsed = extract_formal_output(attempt["api_response"])
        _require((response, format_status, parsed) == (raw.get("raw_response"), raw.get("format_status"), raw.get("parsed_response")), f"derived raw-run mismatch: {run_id}")
        _require(raw.get("model_tag") == MODEL_TAG, f"model tag mismatch: {run_id}")
        _require(raw.get("model_manifest_sha256") == MODEL_MANIFEST_SHA256, f"model manifest mismatch: {run_id}")
        _require(raw.get("model_blob_sha256") == MODEL_BLOB_SHA256, f"model blob mismatch: {run_id}")
        _require(raw.get("round5_protocol_manifest_sha256") == protocol_manifest_sha256(), f"protocol binding mismatch: {run_id}")
        _require(raw.get("transport_status") == "OK" and raw.get("error") is None, f"transport/error mismatch: {run_id}")
        rows.append(raw)
        arms[raw["arm"]] += 1
        formats[raw["format_status"]] += 1
    _require(arms == {"A": 12, "B": 12}, f"arm counts mismatch: {dict(arms)}")
    _require(formats == {"VALID_JSON": 19, "FORMAT_FAIL": 5}, f"format counts mismatch: {dict(formats)}")
    _require(load_jsonl(RESULTS / "formal_raw_results.jsonl") == rows, "consolidated formal results do not reconstruct")
    return {"requests": 24, "first_attempts": 24, "raw_runs": 24, "arms": dict(arms), "formats": dict(formats)}


def validate_stage1_state() -> None:
    packet_path = RESULTS / "blinded_extraction_packet.jsonl"
    prompt_path = RESULTS / "stage1_prompt.txt"
    rows = load_jsonl(packet_path)
    allowed = {"response_id", "scenario", "requested_action", "raw_response", "format_status"}
    forbidden = {
        "gold_record", "expected_decision", "required_findings", "supporting_findings",
        "arm", "run_id", "sequence", "case_id", "model", "model_tag", "timing",
        "prompt_eval_count", "eval_count", "blinding_key",
    }
    _require(len(rows) == 24, "Stage-1 packet does not contain 24 rows")
    _require([row.get("response_id") for row in rows] == [f"R5R{i:03d}" for i in range(1, 25)], "Stage-1 response IDs mismatch")
    _require(all(set(row) == allowed and not (set(row) & forbidden) for row in rows), "Stage-1 packet surface leaks forbidden fields")
    packet = packet_path.read_text(encoding="utf-8").rstrip("\r\n")
    prompt = prompt_path.read_text(encoding="utf-8")
    start = "--- BEGIN ROUND-5 GOLD-FREE BLINDED EXTRACTION PACKET ---\n"
    end = "\n--- END ROUND-5 GOLD-FREE BLINDED EXTRACTION PACKET ---"
    _require(start in prompt and end in prompt, "Stage-1 prompt packet markers missing")
    _require(prompt.split(start, 1)[1].split(end, 1)[0] == packet, "Stage-1 prompt does not embed the frozen packet exactly")
    lowered = prompt.lower()
    for forbidden_text in (MODEL_TAG, MODEL_MANIFEST_SHA256, MODEL_BLOB_SHA256, "r5a-run-"):
        _require(forbidden_text.lower() not in lowered, f"Stage-1 prompt leaks: {forbidden_text}")
    _require_hashes(STAGE1_HASHES)
    events = load_jsonl(RESULTS / "stage1_events.jsonl")
    _require([event.get("type") for event in events] == ["thread.started", "turn.started", "item.completed", "turn.completed"], "Stage-1 event sequence mismatch")
    _require(events[0].get("thread_id") == "01a06754-52d6-77a1-8312-2b637d14f237", "Stage-1 session ID mismatch")
    item = events[2].get("item", {})
    _require(item.get("type") == "agent_message", "Stage-1 completed item is not an agent message")
    raw_output = load_json(RESULTS / "stage1_raw_output.json")
    _require(json.loads(item.get("text", "")) == raw_output, "Stage-1 event output and frozen raw output differ")
    _require(raw_output.get("stage") == "DECISION_EXTRACTION", "Stage-1 output stage mismatch")
    ratings = raw_output.get("ratings")
    _require(isinstance(ratings, list) and len(ratings) == 24, "Stage-1 extraction count mismatch")
    expected_ids = [f"R5R{i:03d}" for i in range(1, 25)]
    _require([rating.get("response_id") for rating in ratings] == expected_ids, "Stage-1 extraction IDs mismatch")
    rating_keys = {"response_id", "extracted_decision", "format_status", "extraction_evidence"}
    _require(all(set(rating) == rating_keys for rating in ratings), "Stage-1 extraction surface mismatch")
    _require(all(rating.get("format_status") == row.get("format_status") for rating, row in zip(ratings, rows, strict=True)), "Stage-1 extraction format statuses differ from the frozen packet")
    _require(not any(event.get("type", "").startswith("tool") or event.get("item", {}).get("type") in {"tool_call", "function_call", "computer_call"} for event in events), "Stage-1 contains a tool call")
    custody = load_json(RESULTS / "STAGE1_SESSION_CUSTODY.json")
    _require(custody.get("session_id") == "01a06754-52d6-77a1-8312-2b637d14f237", "Stage-1 custody session mismatch")
    _require(custody.get("validated_extraction_count") == 24 and custody.get("tool_call_count") == 0, "Stage-1 custody count mismatch")
    _require(custody.get("stage2_transmission_occurred") is False, "Stage-1 custody reports Stage-2 transmission")
    prohibited_future_outputs = (
        "STAGE2_TRANSMISSION_AUTHORIZATION.json", "stage2_events.jsonl", "stage2_raw_output.json",
        "ratings_surrogate.jsonl", "rater_session.json", "metrics_round5.json",
    )
    _require(not any((RESULTS / name).exists() for name in prohibited_future_outputs), "unauthorized Stage-2/rating/result artifact exists")


def validate_repair() -> dict[str, Any]:
    validate_sources()
    validate_checkpoint()
    _require_hashes(FROZEN_HASHES)
    _require_hashes(ADDITIVE_HASHES)
    _require_hashes(STAGE1_REPAIR_HASHES)
    validate_inventory()
    formal = validate_formal_evidence()
    validate_stage1_state()
    repair = load_json(RESULTS / "ROUND5_POSTEXECUTION_CUSTODY_REPAIR.json")
    lifecycle = repair.get("lifecycle_reconciliation", {})
    _require(lifecycle.get("transitions") == TRANSITIONS, "lifecycle transition list mismatch")
    _require(lifecycle.get("frozen_test_modified") is False, "frozen preparation test was modified")
    _require(lifecycle.get("third_transition", {}).get("test") == TRANSITIONS[2], "third lifecycle test mismatch")
    _require(lifecycle.get("third_transition", {}).get("post_execution_status") == "EXPECTED_LIFECYCLE_TRANSITION", "third lifecycle transition is not explicit")
    custody = repair.get("r5a_run_016_custody", {})
    rejected = custody.get("rejected_record", {})
    _require(rejected.get("status") == "REJECTED_NOT_AUTHORITATIVE" and rejected.get("preserved") is True, "false interruption record is not rejected and preserved")
    correction = load_json(RESULTS / "attempts" / "R5A-RUN-016-INTERRUPTION-CUSTODY-CORRECTION.json")
    _require(correction.get("disposition", {}).get("status") == "REJECTED_NOT_AUTHORITATIVE", "correction does not reject the false record")
    raw_custody = custody.get("raw_run", {})
    _require(raw_custody.get("raw_response_bytes_changed") is False, "repair claims R16 response bytes changed")
    _require(custody.get("model_rerun_occurred") is False, "repair claims a model rerun")
    _require(custody.get("second_model_request_occurred") is False, "repair claims a second model request")
    _require(custody.get("selective_regeneration_occurred") is False, "repair claims selective regeneration")
    scope = repair.get("scope_disposition", {})
    for key in ("frozen_evidence_modified_by_repair", "additional_model_execution", "openai_transmission", "sol_session", "formal_rating", "stage2_preparation", "publication_authorized", "commit_authorized"):
        _require(scope.get(key) is False, f"repair scope expanded: {key}")
    validation_path = RESULTS / "ROUND5_POSTEXECUTION_REPAIR_VALIDATION.json"
    if validation_path.exists():
        validation = load_json(validation_path)
        _require(validation.get("result") == "PASS", "additive validation record is not PASS")
        _require(validation.get("lifecycle_transitions") == TRANSITIONS, "validation-record transition list mismatch")
        local = validation.get("local_validation", {})
        _require(local.get("repair_validator") == "PASS", "local repair validation not recorded as PASS")
        _require(local.get("applicable_test_summary") == "18 passed, 3 deselected", "local applicable-test summary mismatch")
        isolated = validation.get("isolated_clean_checkout_validation", {})
        _require(isolated.get("result") == "PASS", "isolated clean-checkout validation is not PASS")
        _require(isolated.get("repair_validator") == "PASS", "isolated repair validation not recorded as PASS")
        _require(isolated.get("applicable_test_summary") == "18 passed, 3 deselected", "isolated applicable-test summary mismatch")
        _require(isolated.get("checkpoint_absent") is True, "isolated validation depended on the excluded checkpoint")
        _require(isolated.get("byte_mismatch_count") == 0, "isolated overlay bytes differed")
        activities = validation.get("prohibited_activity_counts", {})
        _require(all(activities.get(key) == 0 for key in ("additional_model_requests", "openai_transmissions", "sol_sessions", "formal_ratings", "commits", "pushes", "tags", "releases", "publications")), "validation record reports prohibited activity")
    stage1_repair = load_json(RESULTS / "ROUND5_STAGE1_POSTCOMPLETION_LIFECYCLE_REPAIR.json")
    transitions = stage1_repair.get("newly_applicable_lifecycle_transitions", [])
    _require([entry.get("assertion") for entry in transitions] == STAGE1_COMPLETION_TRANSITIONS, "Stage-1 lifecycle transition list mismatch")
    _require(all(entry.get("post_stage1_status") == "EXPECTED_LIFECYCLE_TRANSITION" for entry in transitions), "Stage-1 lifecycle transition is not explicit")
    _require(stage1_repair.get("diagnostic_binding", {}).get("sha256") == STAGE1_HASHES["results/round5_granite4_3b/STAGE1_LIFECYCLE_DIAGNOSTIC.json"], "Stage-1 lifecycle diagnostic binding mismatch")
    _require(stage1_repair.get("frozen_preparation_tests_modified") is False, "frozen preparation tests were modified")
    _require(stage1_repair.get("stage1_output_revised") is False, "Stage-1 output was revised")
    _require(stage1_repair.get("stage1_session_resumed") is False, "Stage-1 session was resumed")
    _require(stage1_repair.get("stage2_transmission_occurred") is False, "Stage-2 transmission was recorded")
    return {
        "result": "PASS",
        "frozen_core_unchanged": True,
        "formal_evidence": formal,
        "lifecycle_transitions": TRANSITIONS,
        "stage1_completion_transitions": STAGE1_COMPLETION_TRANSITIONS,
        "stage1_state": "COMPLETE_AND_FROZEN",
        "r5a_run_016_interruption_record": "REJECTED_NOT_AUTHORITATIVE",
        "r5a_run_016_raw_response_bytes_changed": False,
        "additional_model_requests": 0,
        "openai_stage1_transmissions": 1,
        "stage2_transmissions": 0,
        "formal_ratings": 0,
        "publication_authorized": False,
    }


def main() -> int:
    try:
        validate_repair()
        print("PASS: additive Round 5A post-execution custody and lifecycle repair is valid")
        return 0
    except (PilotError, OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
