#!/usr/bin/env python3
"""Validate frozen Round 5A preparation without creating a formal observation."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from collections import Counter
from typing import Any

import validate_protocol
import validate_round2
import validate_round2_publication
import validate_round3_postexecution
import validate_round3_publication
import validate_round4_postexecution
import validate_round4_postmanifest_repair
import validate_round4_publication_v2
from build_round5_rating_packets import stage1_packet_row
from round5_common import (
    BASELINE_HASHES, CHECKPOINT_PATH, CHECKPOINT_SHA256, CHECKPOINT_SIZE,
    CODEX_CLI_VERSION, MODEL_BLOB_SHA256, MODEL_BLOB_SIZE, MODEL_LAYERS,
    MODEL_MANIFEST_SHA256, MODEL_TAG, OLLAMA_VERSION, PUBLIC_BASELINE_COMMIT,
    RESULTS, ROOT, ROUND5, SETTINGS, SOURCE_HASHES, PilotError,
    formal_observation_count, load_json, load_jsonl, load_order, sha256_bytes,
    validate_local_environment, validate_sources,
)


def _git(*args: str) -> str:
    completed = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, timeout=60, check=False)
    if completed.returncode:
        raise PilotError(f"git {' '.join(args)} failed: {completed.stderr.strip()}")
    return completed.stdout.rstrip("\r\n")


def validate_repo_state() -> None:
    if _git("rev-parse", "--show-toplevel").replace("\\", "/") != ROOT.as_posix():
        raise PilotError("repository root mismatch")
    if _git("branch", "--show-current") != "main":
        raise PilotError("Round-5 preparation requires branch main")
    if _git("rev-parse", "HEAD") != PUBLIC_BASELINE_COMMIT or _git("rev-parse", "origin/main") != PUBLIC_BASELINE_COMMIT:
        raise PilotError("HEAD or origin/main differs from the frozen public base")
    if _git("show", "-s", "--format=%s", "HEAD") != "Add prespecified Llama Round 4A replication evidence":
        raise PilotError("Round-4 publication commit message mismatch")
    if _git("diff", "--cached", "--name-only"):
        raise PilotError("Round-5 preparation must not stage files")
    tags = set(_git("tag", "--list").splitlines())
    if not {"v0.1.0", "v0.2.0", "v0.3.0", "v0.4.0", "v0.5.0"}.issubset(tags):
        raise PilotError("public tag continuity through v0.5.0 is incomplete")
    if _git("rev-parse", "v0.5.0^{}") != PUBLIC_BASELINE_COMMIT:
        raise PilotError("v0.5.0 does not peel to the public baseline")
    status = _git("status", "--porcelain=v1", "--untracked-files=all").splitlines()
    checkpoint_rows = [row for row in status if row[3:].replace("\\", "/") == "results/ratings_primary.partial.jsonl"]
    if checkpoint_rows != ["?? results/ratings_primary.partial.jsonl"]:
        raise PilotError("excluded checkpoint is not exactly untracked")
    for row in status:
        path = row[3:].replace("\\", "/")
        allowed = (
            path == ".gitattributes"
            or path == "results/ratings_primary.partial.jsonl"
            or path.startswith("round5/")
            or path.startswith("results/round5_granite4_3b/")
            or path.startswith("scripts/") and "round5" in path
            or path.startswith("tests/") and "round5" in path
        )
        if not allowed:
            raise PilotError(f"unrelated worktree change present: {row}")


def validate_prior_evidence() -> None:
    cases, _gold = validate_protocol.validate_cases_and_gold()
    validate_protocol.validate_execution_order({row["case_id"] for row in cases})
    validate_protocol.validate_json_files()
    validate_protocol.validate_manifest()
    validate_round2.validate_sources()
    validate_round2.validate_calibration()
    validate_round2.validate_manifest()
    validate_round2_publication.validate_all()
    validate_round3_postexecution.validate_all()
    validate_round3_publication.validate_all()
    validate_round4_postexecution.validate_completed_evidence()
    validate_round4_postmanifest_repair.validate_frozen()
    validate_round4_postmanifest_repair.validate_rejection()
    validate_round4_postmanifest_repair.validate_python314_diagnostic()
    validate_round4_postmanifest_repair.validate_additive()
    if validate_round4_publication_v2.validate() != "PUBLICATION_VALID":
        raise PilotError("Round-4 publication validation did not pass")
    validate_sources()


def validate_bindings_and_order() -> None:
    bindings = load_json(ROUND5 / "SOURCE_BINDINGS.json")
    observed = {row["path"]: row["sha256"] for row in bindings["sources"]}
    expected_sources = {k: v for k, v in SOURCE_HASHES.items() if k != "round2/DAVID_RATER_CALIBRATION_V1.md"}
    if observed != expected_sources:
        raise PilotError("Round-5 source bindings are not exact")
    if bindings["calibration"] != {"path": "round2/DAVID_RATER_CALIBRATION_V1.md", "sha256": SOURCE_HASHES["round2/DAVID_RATER_CALIBRATION_V1.md"]}:
        raise PilotError("Round-5 calibration binding is not exact")
    names = {
        "public_head_commit": PUBLIC_BASELINE_COMMIT,
        "round1_result_manifest_sha256": BASELINE_HASHES["results/RESULT_MANIFEST.json"],
        "round2_protocol_manifest_sha256": BASELINE_HASHES["round2/round2_protocol_manifest.json"],
        "round2_result_manifest_sha256": BASELINE_HASHES["results/round2_ministral3b/RESULT_MANIFEST.json"],
        "round2_publication_manifest_sha256": BASELINE_HASHES["results/round2_ministral3b/PUBLICATION_MANIFEST.json"],
        "round3_protocol_manifest_sha256": BASELINE_HASHES["round3/round3_protocol_manifest.json"],
        "round3_result_manifest_sha256": BASELINE_HASHES["results/round3_granite41_3b/RESULT_MANIFEST.json"],
        "round3_publication_manifest_sha256": BASELINE_HASHES["results/round3_granite41_3b/PUBLICATION_MANIFEST.json"],
        "round4_protocol_manifest_sha256": BASELINE_HASHES["round4/round4_protocol_manifest_v3.json"],
        "round4_result_manifest_sha256": BASELINE_HASHES["results/round4_llama32_3b/RESULT_MANIFEST.json"],
        "round4_publication_manifest_sha256": BASELINE_HASHES["results/round4_llama32_3b/PUBLICATION_MANIFEST.json"],
    }
    if bindings["frozen_publication_baselines"] != names:
        raise PilotError("prior-publication bindings are not exact")
    if bindings["excluded_local_checkpoint"] != {
        "path": "results/ratings_primary.partial.jsonl", "size_bytes": CHECKPOINT_SIZE,
        "sha256": CHECKPOINT_SHA256, "included_in_round5": False,
        "clean_checkout_may_omit": True,
    }:
        raise PilotError("excluded checkpoint binding is invalid")
    rows = load_order()
    if Counter(row["arm"] for row in rows) != {"A": 12, "B": 12}:
        raise PilotError("Round-5 run order is not 12 per arm")


def validate_schema_adapter() -> None:
    canonical1 = load_json(ROUND5 / "schemas/surrogate_extraction_output.schema.json")
    runtime1 = load_json(ROUND5 / "schemas/runtime_surrogate_extraction_output.schema.json")
    expected1 = copy.deepcopy(canonical1)
    expected1["properties"]["stage"]["type"] = "string"
    if expected1 != runtime1:
        raise PilotError("Stage-1 runtime adapter changes more than stage type")
    canonical2 = load_json(ROUND5 / "schemas/surrogate_scoring_output.schema.json")
    runtime2 = load_json(ROUND5 / "schemas/runtime_surrogate_scoring_output.schema.json")
    hard1 = canonical2["properties"]["ratings"]["items"]["properties"]["hard_failures"]
    hard2 = runtime2["properties"]["ratings"]["items"]["properties"]["hard_failures"]
    if hard1.get("uniqueItems") is not True or "uniqueItems" in hard2:
        raise PilotError("Stage-2 uniqueItems separation is invalid")
    expected2 = copy.deepcopy(canonical2)
    expected2["properties"]["stage"]["type"] = "string"
    expected2["properties"]["ratings"]["items"]["properties"]["hard_failures"].pop("uniqueItems")
    if expected2 != runtime2:
        raise PilotError("Stage-2 runtime adapter changes evaluation meaning")
    for path in (ROUND5 / "schemas").glob("*.json"):
        if load_json(path).get("type") != "object":
            raise PilotError(f"invalid Round-5 schema: {path.name}")
    if load_json(ROUND5 / "schemas/rater_session.schema.json")["properties"]["codex_cli_version"] != {"const": CODEX_CLI_VERSION}:
        raise PilotError("rater-session schema does not bind the verified Codex CLI")


def validate_model_record(live: bool = True) -> None:
    record = load_json(ROUND5 / "MODEL_AND_ENVIRONMENT.json")
    model = record["ollama"]
    identity = (
        model["model_tag"], model["manifest_sha256"], model["model_blob_sha256"],
        model["model_blob_size_bytes"], model["model_family"], model["parameter_count"], model["quantization"],
    )
    expected = (MODEL_TAG, MODEL_MANIFEST_SHA256, MODEL_BLOB_SHA256, MODEL_BLOB_SIZE, "granite", 3_402_836_480, "Q4_K_M")
    if identity != expected or model.get("manifest_size_bytes") != 829:
        raise PilotError("frozen Granite 4 identity record mismatch")
    layers = {
        label: {"sha256": digest, "size_bytes": size, "independently_verified": True, **({"inspectable": True} if label == "template" else {})}
        for label, (digest, size) in MODEL_LAYERS.items()
    }
    if model.get("manifest_layers") != layers or model.get("context_length") != 131072 or model.get("embedding_length") != 2560:
        raise PilotError("frozen Granite 4 layer/context record mismatch")
    if record["generation_settings"] != {**SETTINGS, "conversation_history": False}:
        raise PilotError("frozen generation settings mismatch")
    host = record["host"]
    required_host = ("platform", "os_architecture", "manufacturer", "system_model", "cpu", "physical_cores", "logical_processors", "physical_memory_bytes", "gpu", "gpu_memory_mib", "nvidia_driver", "python_default", "python_capture_runtime", "python_validation_runtime", "codex_cli_version")
    if any(host.get(key) in {None, ""} for key in required_host) or host["python_default"] != "3.14.5" or host["python_capture_runtime"] != "3.13.13" or host["python_validation_runtime"] != "3.13.13" or host["codex_cli_version"] != CODEX_CLI_VERSION:
        raise PilotError("host/runtime evidence is incomplete or unexpected")
    preflight = record["excluded_case_free_generation_preflight"]
    if not all(preflight.get(key) is value for key, value in {
        "excluded_from_formal_evidence": True, "contains_formal_case_content": False,
        "contains_gold": False, "contains_david_calibration": False,
    }.items()) or preflight.get("result") != "PASS: exact four generation options accepted":
        raise PilotError("Granite 4 options preflight disposition mismatch")
    request = preflight["request"]
    exact_options = {key: SETTINGS[key] for key in ("temperature", "seed", "num_ctx", "num_predict")}
    if request.get("model") != MODEL_TAG or request.get("options") != exact_options or "tools" in request or len(request.get("messages", [])) != 2:
        raise PilotError("Granite 4 options preflight did not use exact isolated settings")
    if preflight["response"].get("model") != MODEL_TAG or preflight["response"].get("done") is not True:
        raise PilotError("Granite 4 options preflight response mismatch")
    transmitted = (json.dumps(request, ensure_ascii=False) + preflight["raw_api_body"])
    for row in load_jsonl(ROOT / "data/pilot_cases.jsonl"):
        if row["scenario"] in transmitted or row["requested_action"] in transmitted:
            raise PilotError("formal case content leaked into excluded generation preflight")
    if live:
        validate_local_environment()


def validate_blinding_and_isolation() -> None:
    row = stage1_packet_row(
        "R5R001",
        {"scenario": "neutral scenario", "requested_action": "neutral action"},
        {"raw_response": "neutral output", "format_status": "FORMAT_FAIL", "run_id": "R5A-RUN-001", "arm": "A", "case_id": "C01", "timing": {"eval_count": 1}, "model_tag": MODEL_TAG},
    )
    if set(row) != {"response_id", "scenario", "requested_action", "raw_response", "format_status"}:
        raise PilotError("Stage-1 packet surface is not exactly blinded")
    forbidden = {"run_id", "arm", "case_id", "model", "model_tag", "latency", "timing", "tokens", "gold", "blinding_key"}
    if forbidden & set(row) or any(value in json.dumps(row) for value in (MODEL_TAG, "R5A-RUN-001")):
        raise PilotError("Stage-1 packet leaks a forbidden field")
    isolation = " ".join((ROUND5 / "RATER_ISOLATION_PROCEDURE.md").read_text(encoding="utf-8").split())
    required = ("new session", "zero tools", "withhold gold", "blinding key", "Stage 2 does not exist until Stage-1 output is frozen", "pre-sampling")
    if any(fragment.lower() not in isolation.lower() for fragment in required):
        raise PilotError("surrogate isolation procedure is incomplete")


def validate_byte_preservation() -> None:
    from build_round5_byte_preflight import ATTRIBUTE_FILES, PATHS

    record = load_json(ROUND5 / "preflight/BYTE_PRESERVATION_PREFLIGHT.json")
    if record.get("record_type") != "ROUND5A_EXCLUDED_CLEAN_CHECKOUT_BYTE_PRESERVATION_PREFLIGHT" or record.get("excluded_from_formal_observations") is not True or record.get("synthetic_content_only") is not True or record.get("result") != "PASS_EXACT_BYTES_AFTER_CLEAN_CHECKOUT":
        raise PilotError("Round-5 byte-preservation preflight disposition mismatch")
    expected_bindings = []
    for relative in ATTRIBUTE_FILES:
        payload = (ROOT / relative).read_bytes()
        expected_bindings.append({"path": relative, "sha256": sha256_bytes(payload), "size_bytes": len(payload)})
    if record.get("source_attribute_files") != expected_bindings:
        raise PilotError("Round-5 byte-preservation attribute-file bindings mismatch")
    if expected_bindings[0]["sha256"] != "d4b93c3c3844665b7a33dc30f73384f467406b3adaba0da7f3c93b6a9d18e285":
        raise PilotError("frozen root .gitattributes changed")
    probe = ROUND5 / "preflight/byte_preservation_probe.log"
    if record.get("probe_payload_size_bytes") != probe.stat().st_size or record.get("probe_payload_sha256") != sha256_bytes(probe.read_bytes()):
        raise PilotError("Round-5 byte-preservation probe mismatch")
    rows = record.get("path_classes")
    if not isinstance(rows, list) or [row.get("path") for row in rows] != list(PATHS):
        raise PilotError("Round-5 byte-preservation path inventory mismatch")
    for row in rows:
        if row.get("exact_match") is not True or row.get("input_sha256") != row.get("checkout_sha256") or row.get("input_size_bytes") != row.get("checkout_size_bytes") or not str(row.get("attribute", "")).endswith("text: unset"):
            raise PilotError(f"Round-5 byte-preservation failure: {row.get('path')}")


def validate_lifecycle_architecture() -> None:
    import validate_round5_postexecution

    validate_round5_postexecution.validate_prepared_architecture()
    if validate_round5_postexecution.lifecycle_state() != "PRE_EXECUTION":
        raise PilotError("Round-5 lifecycle state is not PRE_EXECUTION")
    transitions = validate_round5_postexecution.lifecycle_transition_record()
    if [row["test"] for row in transitions] != ["test_zero_formal_observations", "test_result_manifest_refuses_incomplete_evidence"] or any(row["post_execution_status"] != "EXPECTED_LIFECYCLE_TRANSITION" for row in transitions):
        raise PilotError("Round-5 lifecycle transitions are not prospectively exact")


def validate_zero_formal_observations() -> None:
    if formal_observation_count() != 0:
        raise PilotError("formal Granite 4 observations are not 0/24")
    unexpected = [path for path in RESULTS.rglob("*") if path.is_file() and path.name not in {".gitkeep", ".gitattributes"}]
    if unexpected:
        raise PilotError(f"unexpected Round-5 result artifact before authorization: {unexpected}")


def validate_manifest() -> None:
    from build_round5_protocol_manifest import FILES

    rejected = ROUND5 / "round5_protocol_manifest.json"
    if sha256_bytes(rejected.read_bytes()) != "f44c47a4307e105b554ce71d85bff01030df937d6563f0a1eb9ef26d80daeb40":
        raise PilotError("rejected Round-5 v1 manifest custody changed")
    repair = load_json(ROUND5 / "PREAUTHORIZATION_MANIFEST_REPAIR.json")
    if repair.get("rejected_manifest", {}).get("sha256") != "f44c47a4307e105b554ce71d85bff01030df937d6563f0a1eb9ef26d80daeb40" or repair.get("disposition", {}).get("formal_observations_existed") is not False:
        raise PilotError("preauthorization manifest-repair custody mismatch")
    if repair.get("defect", {}).get("rejected_postimage_sha256") != "e5304ec9af32c98be3351adf7c0ce6ff34fc146cb6e496207f35e0a36824911e" or repair.get("defect", {}).get("corrected_postimage_sha256") != sha256_bytes((ROUND5 / "schemas/rater_session.schema.json").read_bytes()):
        raise PilotError("preauthorization rater-schema repair binding mismatch")
    rejected_v2 = ROUND5 / "round5_protocol_manifest_v2.json"
    if sha256_bytes(rejected_v2.read_bytes()) != "19e35be44a8c5fdc60c886b66dbd1a57d6900017bd38be601aebd6b50a6a54a5":
        raise PilotError("rejected Round-5 v2 manifest custody changed")
    repair_v2 = load_json(ROUND5 / "PREAUTHORIZATION_MANIFEST_REPAIR_V2.json")
    if repair_v2.get("rejected_manifest", {}).get("sha256") != "19e35be44a8c5fdc60c886b66dbd1a57d6900017bd38be601aebd6b50a6a54a5" or repair_v2.get("disposition", {}).get("formal_observations_existed") is not False:
        raise PilotError("second preauthorization manifest-repair custody mismatch")
    if repair_v2.get("defect", {}).get("rejected_postimage_sha256") != "3a97810183bb4eea721da44ce2eda5f8042af5dd1aad075c6b6136eb53120ffc" or repair_v2.get("defect", {}).get("corrected_postimage_sha256") != sha256_bytes((ROUND5 / "MODEL_AND_ENVIRONMENT.json").read_bytes()):
        raise PilotError("preauthorization environment-record repair binding mismatch")
    for row in repair_v2.get("supporting_corrections", []):
        if sha256_bytes((ROOT / row["path"]).read_bytes()) != row["new_sha256"]:
            raise PilotError(f"preauthorization supporting correction mismatch: {row['path']}")
    manifest = load_json(ROUND5 / "round5_protocol_manifest_v3.json")
    if manifest.get("protocol_version") != "round5a-v3" or manifest.get("formal_observations_before_freeze") != 0:
        raise PilotError("Round-5 manifest version or pre-freeze count mismatch")
    if manifest.get("supersedes") != {
        "path": "round5/round5_protocol_manifest_v2.json",
        "sha256": "19e35be44a8c5fdc60c886b66dbd1a57d6900017bd38be601aebd6b50a6a54a5",
        "status": "REJECTED_PREAUTHORIZATION_HOST_RUNTIME_LABEL_MISMATCH",
    }:
        raise PilotError("Round-5 manifest supersession record mismatch")
    rows = manifest.get("files")
    if manifest.get("file_count") != len(FILES) or not isinstance(rows, list) or [row.get("path") for row in rows] != FILES:
        raise PilotError("Round-5 manifest inventory mismatch")
    for row in rows:
        payload = (ROOT / row["path"]).read_bytes()
        if row.get("size_bytes") != len(payload) or row.get("sha256") != sha256_bytes(payload):
            raise PilotError(f"Round-5 manifest hash mismatch: {row['path']}")


def validate_pre_manifest(live_model: bool = True, prior: bool = True) -> None:
    validate_repo_state()
    if prior:
        validate_prior_evidence()
    else:
        validate_sources()
    validate_bindings_and_order()
    validate_schema_adapter()
    validate_model_record(live=live_model)
    validate_blinding_and_isolation()
    validate_byte_preservation()
    validate_lifecycle_architecture()
    validate_zero_formal_observations()


def main() -> int:
    try:
        validate_pre_manifest(live_model=True, prior=True)
        validate_manifest()
        print("PASS: Round 5A preparation is frozen and valid; formal observations = 0/24")
        return 0
    except (PilotError, OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
