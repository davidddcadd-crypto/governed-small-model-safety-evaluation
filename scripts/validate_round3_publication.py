#!/usr/bin/env python3
"""Validate additive Round 3A publication evidence without writing files."""

from __future__ import annotations

import json
import sys

from build_round3_publication_manifest import (
    ADDITIVE_SPECS,
    PROTOCOL_MANIFEST_SHA256,
    RESULT_MANIFEST_SHA256,
)
from round3_common import RESULTS, ROOT, ROUND3, PilotError, load_json, sha256_bytes
import validate_round3_postexecution

REQUIRED_ADDENDUM_TEXT = (
    "Round 3A is the Granite 4.1 3B within-model Arm A/B replication",
    "12 synthetic cases",
    "one observation per case-arm",
    "24 total formal observations",
    "no repeated trials",
    "no transport retries",
    "no selective observation reruns",
    "Strict Safety Pass | 8.3% (1/12) | 33.3% (4/12)",
    "Exact Decision Accuracy | 58.3% (7/12) | 66.7% (8/12)",
    "Unsafe Allows | 0 | 0",
    "Escalation Recall | 0% (0/4) | 25% (1/4)",
    "False Refusals | 25% (1/4) | 25% (1/4)",
    "Format Failures | 0/12 | 1/12",
    "23 `VALID_JSON` / 1 `FORMAT_FAIL`",
    "Mean Quality | 7.50 | 8.25",
    "Hard Failures | 0 | 0",
    "3 improved, 9 unchanged, and 0 worsened",
    "prespecified result was `SUPPORTIVE`",
    "Escalation performance remained poor in absolute terms",
    "Seven of eight expected-escalation observations were not extracted as `ESCALATE`",
    "not equivalent to high absolute safety",
    "Ministral Round 2A had 24/24 `FORMAT_FAIL`",
    "Granite Round 3A had 1/24 `FORMAT_FAIL`",
    "descriptive only",
    "does not establish that Granite is globally safer or better",
    "supports no causal inference",
    "Round 1 primary rater was David / Tai Wai Lee, human",
    "Round 2A and Round 3A used a David-calibrated OpenAI `gpt-5.6-sol` xhigh AI surrogate",
    "not human-equivalent",
    "not ground truth",
    "not an independent human expert",
    "01a0645d-b07a-7241-b938-6d0399a626fe",
    "Stage 1 was frozen before gold disclosure",
    "Stage 1 completed 24/24",
    "Stage 2 completed 24/24",
    "Tool calls were 0",
    "formal schema rejections were 0",
    "blinding key and arm mapping were withheld",
    "Granite model identity and runtime metadata were withheld from rating",
    "No prior-round per-response ratings or case mappings were provided",
    "source ratings file `results/ratings_primary.jsonl`",
    "`114e940605fc0cdca16969e3abd6c8600ca1d2967bbe464d38619c769486265f`",
    "Risk Recognition 1 in 13 ratings and 2 in 11",
    "8 strict passes and 16 non-passes",
    "23 format failures and 1 valid format",
    "0 hard failures",
    "does not claim that no Round-1-derived information was provided",
    "Canonical and runtime schemas were separate",
    "Stage-1 runtime adapter added an explicit string type for `stage`",
    "Stage-2 runtime adapter also omitted unsupported `uniqueItems`",
    "Canonical uniqueness and deterministic post-validation remained enforced",
    "canonical scoring meaning was unchanged",
    "Excluded neutral case-free preflights occurred before formal rating",
    "no formal Granite responses, formal cases, gold records, or David calibration content",
    "used zero tools",
    "incurred no schema rejection",
    "EXPECTED_LIFECYCLE_TRANSITION",
    "not skipped, rewritten, or represented as passing",
    "statistical significance",
    "production safety",
    "model-family generalization",
    "frontier equivalence",
    "controlled three-model comparison",
    "causation from format differences",
    "proof that governance works generally",
)


def validate_addendum() -> None:
    text = (RESULTS / "ROUND3_PUBLICATION_ADDENDUM.md").read_text(encoding="utf-8")
    normalized = " ".join(text.split())
    missing = [item for item in REQUIRED_ADDENDUM_TEXT if " ".join(item.split()) not in normalized]
    if missing:
        raise PilotError(f"Round-3 publication addendum disclosure is incomplete: {missing}")


def validate_combined_log_custody() -> None:
    result_manifest = load_json(RESULTS / "RESULT_MANIFEST.json")
    result_paths = {row["path"] for row in result_manifest["files"]}
    for stage in ("stage1", "stage2"):
        canonical = f"results/round3_granite41_3b/{stage}_events.jsonl"
        combined = f"results/round3_granite41_3b/{stage}_combined.log"
        if canonical not in result_paths or combined in result_paths:
            raise PilotError(f"{stage} canonical/combined result-manifest custody is invalid")
        canonical_bytes = (ROOT / canonical).read_bytes()
        combined_bytes = (ROOT / combined).read_bytes()
        if not combined_bytes or combined_bytes == canonical_bytes:
            raise PilotError(f"{stage} combined log is empty or substitutes the canonical event log")


def validate_publication_manifest() -> None:
    path = RESULTS / "PUBLICATION_MANIFEST.json"
    value = load_json(path)
    required = {
        "publication_manifest_version",
        "generated_at",
        "manifest_purpose",
        "frozen_protocol_manifest",
        "frozen_result_manifest",
        "additive_file_count",
        "additive_files",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise PilotError("Round-3 publication manifest keys are invalid")
    if value["publication_manifest_version"] != "round3a-publication-v1":
        raise PilotError("Round-3 publication manifest version mismatch")
    if value["frozen_protocol_manifest"] != {
        "path": "round3/round3_protocol_manifest.json",
        "sha256": PROTOCOL_MANIFEST_SHA256,
        "file_count": 36,
    }:
        raise PilotError("Round-3 publication protocol binding mismatch")
    if value["frozen_result_manifest"] != {
        "path": "results/round3_granite41_3b/RESULT_MANIFEST.json",
        "sha256": RESULT_MANIFEST_SHA256,
        "file_count": 94,
    }:
        raise PilotError("Round-3 publication result binding mismatch")
    expected_specs = sorted(ADDITIVE_SPECS, key=lambda item: item[0].relative_to(ROOT).as_posix())
    rows = value["additive_files"]
    if value["additive_file_count"] != len(expected_specs) or len(rows) != len(expected_specs):
        raise PilotError("Round-3 publication additive count mismatch")
    for row, (target, role, provenance) in zip(rows, expected_specs, strict=True):
        expected_keys = {"path", "size_bytes", "sha256", "role"}
        if provenance:
            expected_keys.add("provenance")
        if set(row) != expected_keys:
            raise PilotError(f"publication entry keys are invalid: {target.name}")
        payload = target.read_bytes()
        if (
            row["path"] != target.relative_to(ROOT).as_posix()
            or row["size_bytes"] != len(payload)
            or row["sha256"] != sha256_bytes(payload)
            or row["role"] != role
            or (provenance and row.get("provenance") != provenance)
        ):
            raise PilotError(f"publication manifest entry mismatch: {target.name}")


def validate_administrative_status() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    status = (ROOT / "STATUS.md").read_text(encoding="utf-8")
    required_readme = (
        "`v0.3.0 — Ministral-3 3B Round 2A Replication`: published",
        "`v0.4.0 — Granite 4.1 3B Round 3A Replication` (proposed)",
        "No Round 3 commit, tag, or release is implied",
    )
    required_status = (
        "Round-2A results release: `v0.3.0`",
        "Round-3A formal model runs completed locally: `24 / 24`",
        "Proposed next release: `v0.4.0 — Granite 4.1 3B Round 3A Replication`",
    )
    if any(item not in readme for item in required_readme):
        raise PilotError("README publication status is stale or incomplete")
    if any(item not in status for item in required_status):
        raise PilotError("STATUS publication status is stale or incomplete")


def validate_all() -> None:
    validate_round3_postexecution.validate_all()
    validate_addendum()
    validate_combined_log_custody()
    validate_publication_manifest()
    validate_administrative_status()


def main() -> int:
    try:
        validate_all()
        print(
            "PASS: additive Round 3A publication disclosures, combined-log custody, "
            "and frozen evidence are valid"
        )
        return 0
    except (PilotError, OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
