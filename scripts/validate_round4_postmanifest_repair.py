#!/usr/bin/env python3
"""Validate the additive Round 4A post-manifest custody repair."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from round4_common import RESULTS, ROOT, PilotError, load_json, sha256_bytes, utc_text, write_json_exclusive
from validate_round4_postexecution import validate_completed_evidence

GITATTRIBUTES_SHA256 = "d4b93c3c3844665b7a33dc30f73384f467406b3adaba0da7f3c93b6a9d18e285"
FROZEN_HASHES = {
    "round4/round4_protocol_manifest_v3.json": "37fd588a4103b39c267978b845843ce85da067c078be94811582a67b3fad6ba8",
    "results/round4_llama32_3b/formal_raw_results.jsonl": "d44da543c1b1a0aed1cb691b5ec9b6427e2c5f180d7e2afbe2d5e8c86cb7225c",
    "results/round4_llama32_3b/stage1_raw_output.json": "977a78a34037a34ded9faa50995e18ff754362d48c0d32e6080b3ef7b2f3c89e",
    "results/round4_llama32_3b/stage2_raw_output.json": "e1025eae81af53c21cf71ee537c51229478151c4c9fe0fe5dbef3c5313f61431",
    "results/round4_llama32_3b/ratings_surrogate.jsonl": "0d461c97b52b707896af9b403e6ae61988f149deb70d78bcdf02f8b6005c6e2b",
    "results/round4_llama32_3b/ROUND4_METRICS.json": "621bd759185a0491f6e983777774f94d87d2200246f9a2fd4f0cdfaa5eab83a3",
    "results/round4_llama32_3b/ROUND4_REPORT.md": "89b72eabc09c13f52323adfc52a6837ac488af012c20058358158f4a53daafc0",
    "results/round4_llama32_3b/RESULT_MANIFEST.json": "b7c00219ce87ad8bae5cdf5d599b005b5928f7d1bc05e622aa95adeb254a7033",
    "tests/test_round4_postexecution.py": "0191aa4428f6756c65a8a6e2bcd62789d63c3ff547dde168729a059e69af1d3f",
    "tests/test_round4_preparation.py": "6a45f23f2b60b0b43baff168a17db16d09bca8eb34d9bf3bdc6f909a9368448c",
    "tests/test_round4_publication.py": "530b26188d8e01bdd49a7700dcf18c93f9fe85e7e4dfd27dbed70c08b898c77d",
}
TRANSITIONS = [
    "test_zero_formal_observations",
    "test_result_manifest_refuses_incomplete_evidence",
    "test_pre_execution_lifecycle_is_explicit",
    "test_lifecycle_and_publication_architecture_is_frozen",
    "test_publication_state_is_prepublication",
]
FUTURE_ADDITIVE_PATHS = [
    ".gitattributes",
    "results/round4_llama32_3b/PUBLICATION_PACKAGING_AUTHORIZATIONS.json",
    "results/round4_llama32_3b/POSTMANIFEST_REPAIR_AUTHORIZATION.json",
    "results/round4_llama32_3b/POSTMANIFEST_REPAIR_EXTENSION_AUTHORIZATION.json",
    "results/round4_llama32_3b/ROUND4_POSTMANIFEST_REPAIR.json",
    "results/round4_llama32_3b/POSTEXECUTION_VALIDATION.json",
    "results/round4_llama32_3b/PYTHON314_VALIDATION_DIAGNOSTIC.json",
    "results/round4_llama32_3b/ROUND4_PUBLICATION_ADDENDUM.md",
    "results/round4_llama32_3b/ROUND4_RELEASE_NOTES_DRAFT.md",
    "results/round4_llama32_3b/stage1_combined.log",
    "results/round4_llama32_3b/stage2_combined.log",
    "results/round4_llama32_3b/STAGE2_RESUME_REJECTION.json",
    "results/round4_llama32_3b/stage2_resume_rejection_events.jsonl",
    "results/round4_llama32_3b/ROUND4_PUBLICATION_CUSTODY_PLAN_V2.json",
    "scripts/validate_round4_postmanifest_repair.py",
    "scripts/build_round4_publication_manifest_v2.py",
    "scripts/validate_round4_publication_v2.py",
    "tests/test_round4_postmanifest_repair.py",
    "tests/test_round4_publication_readiness.py",
]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PilotError(message)


def validate_frozen() -> None:
    for relative, expected in FROZEN_HASHES.items():
        path = ROOT / relative
        _require(path.is_file() and sha256_bytes(path.read_bytes()) == expected, f"frozen artifact changed: {relative}")
    validate_completed_evidence()


def validate_rejection() -> None:
    record_path = RESULTS / "STAGE2_RESUME_REJECTION.json"
    events_path = RESULTS / "stage2_resume_rejection_events.jsonl"
    _require(sha256_bytes(record_path.read_bytes()) == "4607624ef8df25ab5e03d802c0650b5a6e0d32bddb5cc0f068b5c433c024fecd", "Stage-2 rejection record changed")
    _require(events_path.read_bytes() == b"", "Stage-2 rejection event stream is not zero bytes")
    record = load_json(record_path)
    _require(record.get("failure_stage") == "CLI_TRUSTED_DIRECTORY_GATE_BEFORE_SAMPLING", "rejection stage mismatch")
    _require(record.get("model_sampling_occurred") is False and record.get("raw_output_created") is False, "rejection was not pre-sampling")
    _require(record.get("stage1_output_revised") is False, "rejection record claims Stage-1 revision")


def validate_python314_diagnostic() -> None:
    path = RESULTS / "PYTHON314_VALIDATION_DIAGNOSTIC.json"
    _require(sha256_bytes(path.read_bytes()) == "23156e151915304871f2d2aa06c428d8abcf61dc10f11bf82d84ea58fc167bf6", "Python 3.14 diagnostic custody changed")
    value = load_json(path)
    _require(value.get("runtime") == "Python 3.14", "Python diagnostic runtime mismatch")
    _require(value.get("failed_tests") == [
        "tests/test_round2_tools.py::Round2ToolTests::test_frozen_sources_and_calibration_validate",
        "tests/test_v02_tools.py::V02ToolTests::test_frozen_protocol_still_validates",
    ], "Python diagnostic failed-test list mismatch")
    _require(value.get("failure_class") == "Windows subprocess error", "Python diagnostic failure class mismatch")
    _require(value.get("failure_message") == "WinError 6: The handle is invalid", "Python diagnostic failure message mismatch")
    _require(value.get("observed_python314_result", {}).get("summary") == "70 passed, 2 failed, 7 deselected", "Python 3.14 result mismatch")
    _require(value.get("equivalent_python313_result", {}).get("summary") == "72 passed, 7 deselected", "Python 3.13 result mismatch")
    disposition = value.get("disposition", {})
    required_true = (
        "failures_were_subprocess_runtime_handle_failures",
        "equivalent_applicable_suite_completed_under_python313",
    )
    required_false = (
        "scientific_assertion_failed",
        "frozen_protocol_validation_failed",
        "formal_observation_validation_failed",
        "rater_output_validation_failed",
        "canonical_rating_validation_failed",
        "metric_validation_failed",
        "report_validation_failed",
        "result_manifest_validation_failed",
        "model_execution_occurred",
        "openai_transmission_occurred",
        "formal_evidence_bytes_modified",
    )
    _require(all(disposition.get(key) is True for key in required_true), "Python diagnostic positive disposition mismatch")
    _require(all(disposition.get(key) is False for key in required_false), "Python diagnostic no-impact disposition mismatch")


def validate_additive() -> dict[str, Any]:
    validate_frozen()
    validate_rejection()
    validate_python314_diagnostic()
    gitattributes = ROOT / ".gitattributes"
    _require(sha256_bytes(gitattributes.read_bytes()) == GITATTRIBUTES_SHA256, "authorized .gitattributes bytes changed")
    packaging_authorization = RESULTS / "PUBLICATION_PACKAGING_AUTHORIZATIONS.json"
    _require(sha256_bytes(packaging_authorization.read_bytes()) == "21e261e0f454c271c444c82a84b176bcfaac9b44d7c394c1039f3ccfecf478cd", "publication-packaging authorization changed")
    packaging = load_json(packaging_authorization)
    _require(packaging.get("authorized_gitattributes_sha256") == GITATTRIBUTES_SHA256, "publication authorization does not bind .gitattributes")
    _require(packaging.get("staging_authorized") is False and packaging.get("publication_authorized") is False, "publication authorization scope expanded")
    authorization = RESULTS / "POSTMANIFEST_REPAIR_AUTHORIZATION.json"
    _require(sha256_bytes(authorization.read_bytes()) == "9947bb4ec5b92f7a7b2fa5422ddce059f642bf7359fc957496e8e7629b33ec36", "repair authorization changed")
    extension_authorization = RESULTS / "POSTMANIFEST_REPAIR_EXTENSION_AUTHORIZATION.json"
    _require(sha256_bytes(extension_authorization.read_bytes()) == "99109396fc7abf88f952985326c47e35cfe9a695757d47c9ae25d1e309c2ce09", "repair extension authorization changed")
    repair = load_json(RESULTS / "ROUND4_POSTMANIFEST_REPAIR.json")
    _require(repair.get("extension_authorization", {}).get("sha256") == "99109396fc7abf88f952985326c47e35cfe9a695757d47c9ae25d1e309c2ce09", "repair extension authorization binding mismatch")
    lifecycle = repair.get("lifecycle_reconciliation", {})
    _require(lifecycle.get("frozen_test_modified") is False, "frozen lifecycle test was modified")
    _require(lifecycle.get("additional_frozen_test_modified") is False, "additional frozen lifecycle test was modified")
    _require(lifecycle.get("publication_frozen_test_modified") is False, "frozen publication-state test was modified")
    _require(lifecycle.get("transitions") == TRANSITIONS, "lifecycle transition list mismatch")
    _require(lifecycle.get("third_transition", {}).get("post_execution_status") == "EXPECTED_LIFECYCLE_TRANSITION", "third lifecycle transition is not explicit")
    _require(lifecycle.get("fourth_transition", {}).get("post_execution_status") == "EXPECTED_LIFECYCLE_TRANSITION", "fourth lifecycle transition is not explicit")
    _require(lifecycle.get("fifth_transition", {}).get("publication_packaging_status") == "EXPECTED_LIFECYCLE_TRANSITION", "fifth lifecycle transition is not explicit")
    addendum = (RESULTS / "ROUND4_PUBLICATION_ADDENDUM.md").read_text(encoding="utf-8")
    required = (
        "12 synthetic cases", "one observation per case-arm", "24 total formal observations",
        "no repeated trials", "SUPPORTIVE", "Unsafe Allow", "Escalation Recall",
        "False Refusal", "Format Failure", "Hard Failure", "paired strict",
        "David-calibrated AI surrogate", "runtime-schema", "pre-sampling CLI rejection",
        "EXPECTED_LIFECYCLE_TRANSITION", "clean checkout", "statistical significance",
        "production safety", "frontier equivalence", "proof that governance works generally",
        "exact-byte publication reproducibility", ".gitattributes",
    )
    normalized = " ".join(addendum.split()).lower()
    missing = [term for term in required if term.lower() not in normalized]
    _require(not missing, f"additive disclosure missing concepts: {missing}")
    record_path = RESULTS / "POSTEXECUTION_VALIDATION.json"
    if record_path.exists():
        record = load_json(record_path)
        _require(record.get("result") == "PASS", "post-execution validation record is not PASS")
        _require(record.get("lifecycle_transitions") == TRANSITIONS[:4], "post-execution validation transition list mismatch")
        local = record.get("local_validation", {})
        _require(local.get("applicable_test_summary") == "69 passed, 6 deselected", "local applicable-test result mismatch")
        _require(local.get("round4_postmanifest_repair_validator") == "PASS", "local additive validation result mismatch")
        isolated = record.get("isolated_clean_checkout_validation", {})
        _require(isolated.get("final_result") == "PASS", "isolated clean-checkout result mismatch")
        _require(isolated.get("checkpoint_absent") is True, "isolated checkout unexpectedly depended on local checkpoint")
        _require(isolated.get("applicable_test_summary") == "67 passed, 8 deselected", "isolated applicable-test result mismatch")
        _require(isolated.get("round4_postmanifest_repair_validator") == "PASS", "isolated additive validation result mismatch")
        _require(isolated.get("round4_publication_v2_state") == "PREPUBLICATION_REPAIR_READY", "isolated publication state mismatch")
    plan_path = RESULTS / "ROUND4_PUBLICATION_CUSTODY_PLAN_V2.json"
    if plan_path.exists():
        plan = load_json(plan_path)
        _require(plan.get("future_additive_paths") == FUTURE_ADDITIVE_PATHS, "future publication path list mismatch")
        bindings = plan.get("current_bindings", {})
        expected_bindings = set(FUTURE_ADDITIVE_PATHS) - {"results/round4_llama32_3b/ROUND4_PUBLICATION_CUSTODY_PLAN_V2.json"}
        _require(set(bindings) == expected_bindings, "publication custody binding set mismatch")
        for relative, expected in bindings.items():
            path = ROOT / relative
            _require(path.is_file() and sha256_bytes(path.read_bytes()) == expected, f"publication custody binding mismatch: {relative}")
    return {
        "result": "PASS",
        "frozen_core_unchanged": True,
        "core_postexecution_validation": "PASS",
        "stage2_rejection_preserved": True,
        "stage2_rejection_model_sampling": False,
        "lifecycle_transitions": TRANSITIONS,
        "publication_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-record", action="store_true")
    args = parser.parse_args()
    try:
        result = validate_additive()
        if args.write_record:
            target = RESULTS / "POSTEXECUTION_VALIDATION.json"
            if target.exists():
                raise PilotError("refusing to overwrite post-execution validation record")
            write_json_exclusive(target, {"recorded_at": utc_text(), **result})
        print("PASS: additive Round 4A post-manifest custody repair is valid")
        return 0
    except (PilotError, OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
