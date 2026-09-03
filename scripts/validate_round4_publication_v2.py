#!/usr/bin/env python3
"""Validate repaired Round 4A prepublication or publication-v2 custody."""

from __future__ import annotations

import json
import sys

from round4_common import RESULTS, ROOT, ROUND4, PilotError, load_json, sha256_bytes
from validate_round4_postmanifest_repair import (
    FUTURE_ADDITIVE_PATHS,
    GITATTRIBUTES_SHA256,
    validate_additive,
)

REQUIRED_RELEASE_NOTE_TERMS = (
    "12 frozen synthetic cases",
    "one observation per case-arm",
    "24 formal observations",
    "no repeated trials",
    "No output-format repair, model-specific parser repair, selective format normalization, or equivalent repair was applied to any formal Llama Round-4 observation.",
    "SUPPORTIVE",
    "Strict Safety Pass",
    "Unsafe Allow",
    "Escalation Recall",
    "False Refusal",
    "Format Failure",
    "Hard Failure",
    "Paired Strict Safety Pass",
    "David-calibrated OpenAI `gpt-5.6-sol` `xhigh` AI surrogate",
    "not a human rater",
    "runtime adapter",
    "pre-sampling CLI trusted-directory rejection",
    "zero event bytes",
    "EXPECTED_LIFECYCLE_TRANSITION",
    ".gitattributes",
    "results/ratings_primary.partial.jsonl",
    "No statistical significance",
    "cross-model comparisons are descriptive and confounded",
    "production safety",
    "frontier-model equivalence",
    "proof that governance works generally",
)

REQUIRED_FROZEN_PATHS = {
    "round4/MODEL_AND_ENVIRONMENT.json",
    "results/round4_llama32_3b/PROJECT_OWNER_AUTHORIZATION.json",
    "results/round4_llama32_3b/STAGE1_TRANSMISSION_AUTHORIZATION.json",
    "results/round4_llama32_3b/STAGE2_TRANSMISSION_AUTHORIZATION.json",
    "results/round4_llama32_3b/execution_environment.json",
    "results/round4_llama32_3b/formal_raw_results.jsonl",
    "results/round4_llama32_3b/stage1_raw_output.json",
    "results/round4_llama32_3b/stage2_raw_output.json",
    "results/round4_llama32_3b/ratings_surrogate.jsonl",
    "results/round4_llama32_3b/ROUND4_METRICS.json",
    "results/round4_llama32_3b/ROUND4_REPORT.md",
}


def _binding(path):
    value = load_json(path)
    rows = value.get("files")
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256_bytes(path.read_bytes()), "file_count": len(rows) if isinstance(rows, list) else -1}


def _validated_rows(path):
    value = load_json(path)
    rows = value.get("files")
    if not isinstance(rows, list) or value.get("file_count") != len(rows):
        raise PilotError(f"invalid bound manifest: {path.relative_to(ROOT).as_posix()}")
    for row in rows:
        target = ROOT / row["path"]
        payload = target.read_bytes()
        expected = {"path": row["path"], "size_bytes": len(payload), "sha256": sha256_bytes(payload)}
        if row != expected:
            raise PilotError(f"frozen file binding mismatch: {row['path']}")
    return rows


def validate_release_notes() -> None:
    text = (RESULTS / "ROUND4_RELEASE_NOTES_DRAFT.md").read_text(encoding="utf-8")
    normalized = " ".join(text.split()).lower()
    missing = [term for term in REQUIRED_RELEASE_NOTE_TERMS if term.lower() not in normalized]
    if missing:
        raise PilotError(f"release-note draft missing disclosures: {missing}")


def validate() -> str:
    validate_additive()
    validate_release_notes()
    target = RESULTS / "PUBLICATION_MANIFEST.json"
    if not target.exists():
        return "PREPUBLICATION_REPAIR_READY"
    value = load_json(target)
    if value.get("publication_manifest_version") != "round4a-publication-v2":
        raise PilotError("Round-4 publication manifest is not repaired v2")
    if value.get("frozen_protocol_manifest") != _binding(ROUND4 / "round4_protocol_manifest_v3.json"):
        raise PilotError("protocol-manifest publication binding mismatch")
    if value.get("frozen_result_manifest") != _binding(RESULTS / "RESULT_MANIFEST.json"):
        raise PilotError("result-manifest publication binding mismatch")
    protocol_rows = _validated_rows(ROUND4 / "round4_protocol_manifest_v3.json")
    result_rows = _validated_rows(RESULTS / "RESULT_MANIFEST.json")
    if value.get("frozen_protocol_files") != protocol_rows:
        raise PilotError("direct protocol-file publication bindings mismatch")
    if value.get("frozen_result_files") != result_rows:
        raise PilotError("direct result-file publication bindings mismatch")
    frozen_paths = {row["path"] for row in protocol_rows} | {row["path"] for row in result_rows}
    missing_frozen = sorted(REQUIRED_FROZEN_PATHS - frozen_paths)
    if missing_frozen:
        raise PilotError(f"required frozen publication custody is absent: {missing_frozen}")
    rows = value.get("publication_package_files")
    if not isinstance(rows, list) or value.get("publication_package_file_count") != len(FUTURE_ADDITIVE_PATHS) or len(rows) != len(FUTURE_ADDITIVE_PATHS):
        raise PilotError("publication package count mismatch")
    for row, relative in zip(rows, FUTURE_ADDITIVE_PATHS, strict=True):
        path = ROOT / relative
        payload = path.read_bytes()
        expected = {"path": relative, "size_bytes": len(payload), "sha256": sha256_bytes(payload)}
        if row != expected:
            raise PilotError(f"publication package binding mismatch: {relative}")
    if rows[0].get("path") != ".gitattributes" or rows[0].get("sha256") != GITATTRIBUTES_SHA256:
        raise PilotError("authorized .gitattributes is not bound first and unchanged")
    excluded = value.get("excluded_local_checkpoint", {})
    if excluded.get("path") != "results/ratings_primary.partial.jsonl" or excluded.get("published") is not False:
        raise PilotError("local checkpoint exclusion is not explicit")
    if value.get("release_status") != "DRAFT_ONLY_NOT_AUTHORIZED":
        raise PilotError("release status exceeds authorization")
    return "PUBLICATION_VALID"


def main() -> int:
    try:
        print(f"PASS: Round 4A repaired publication custody state = {validate()}")
        return 0
    except (PilotError, OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
