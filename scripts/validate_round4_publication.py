#!/usr/bin/env python3
"""Lifecycle-aware validator for Round 4A publication architecture/evidence."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from build_round4_publication_manifest import ADDITIVE_SPECS
from round4_common import RESULTS, ROOT, ROUND4, PilotError, load_json, sha256_bytes
from validate_round4_postexecution import validate_completed_evidence

TEMPLATES = (
    ROUND4 / "templates/ROUND4_REPORT.md",
    ROUND4 / "templates/ROUND4_PUBLICATION_ADDENDUM.md",
    ROUND4 / "templates/RELEASE_NOTES.md",
)
MANDATORY_TEMPLATE_CONCEPTS = (
    "12 synthetic cases", "one observation per case-arm", "24 total",
    "no repeated trials", "format", "escalation", "unsafe", "false refusal",
    "hard failure", "paired", "positive", "negative", "mixed",
    "David-calibrated", "calibration", "schema", "preflight", "lifecycle",
    "clean-checkout", "cross-model", "statistical significance",
    "production", "frontier", "general",
)
FINAL_DISCLOSURE_CONCEPTS = (
    "12 synthetic cases", "one observation per case-arm", "24 total formal observations",
    "no repeated trials", "Strict Safety Pass", "Exact Decision Accuracy",
    "Unsafe Allow", "Escalation Recall", "False Refusal", "Format Failure",
    "Mean Quality", "Hard Failure", "paired", "David-calibrated AI surrogate",
    "calibration", "runtime-schema", "preflight", "EXPECTED_LIFECYCLE_TRANSITION",
    "clean checkout", "descriptive", "statistical significance", "production safety",
    "frontier equivalence", "proof that governance works generally",
)


def publication_state() -> str:
    return "PUBLICATION" if (RESULTS / "PUBLICATION_MANIFEST.json").is_file() else "PREPUBLICATION"


def validate_templates() -> None:
    missing_files = [path.relative_to(ROOT).as_posix() for path in TEMPLATES if not path.is_file()]
    if missing_files:
        raise PilotError(f"Round-4 publication templates missing: {missing_files}")
    combined = " ".join(" ".join(path.read_text(encoding="utf-8").split()) for path in TEMPLATES).lower()
    missing = [term for term in MANDATORY_TEMPLATE_CONCEPTS if term.lower() not in combined]
    if missing:
        raise PilotError(f"Round-4 publication templates omit required concepts: {missing}")
    plan = load_json(ROUND4 / "PUBLICATION_MANIFEST_PLAN.json")
    if (
        plan.get("state_at_protocol_freeze") != "PREPUBLICATION"
        or plan.get("additive_only") is not True
        or plan.get("excluded_checkpoint_required_in_clean_checkout") is not False
    ):
        raise PilotError("Round-4 publication manifest plan is invalid")


def _validate_binding(binding: dict, path: Path) -> None:
    value = load_json(path)
    rows = value.get("files")
    expected = {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": sha256_bytes(path.read_bytes()),
        "file_count": len(rows) if isinstance(rows, list) else -1,
    }
    if binding != expected:
        raise PilotError(f"publication manifest binding mismatch: {expected['path']}")


def validate_publication_evidence() -> None:
    validate_completed_evidence()
    addendum = (RESULTS / "ROUND4_PUBLICATION_ADDENDUM.md").read_text(encoding="utf-8")
    normalized = " ".join(addendum.split()).lower()
    missing = [term for term in FINAL_DISCLOSURE_CONCEPTS if term.lower() not in normalized]
    if missing:
        raise PilotError(f"Round-4 publication addendum disclosures are incomplete: {missing}")
    manifest = load_json(RESULTS / "PUBLICATION_MANIFEST.json")
    if manifest.get("publication_manifest_version") != "round4a-publication-v1":
        raise PilotError("Round-4 publication manifest version mismatch")
    _validate_binding(manifest["frozen_protocol_manifest"], ROUND4 / "round4_protocol_manifest_v3.json")
    _validate_binding(manifest["frozen_result_manifest"], RESULTS / "RESULT_MANIFEST.json")
    expected = sorted(ADDITIVE_SPECS, key=lambda item: item[0].relative_to(ROOT).as_posix())
    rows = manifest.get("additive_files")
    if not isinstance(rows, list) or manifest.get("additive_file_count") != len(expected) or len(rows) != len(expected):
        raise PilotError("Round-4 publication additive count mismatch")
    for row, (path, role, provenance) in zip(rows, expected, strict=True):
        payload = path.read_bytes()
        if (
            row.get("path") != path.relative_to(ROOT).as_posix()
            or row.get("size_bytes") != len(payload)
            or row.get("sha256") != sha256_bytes(payload)
            or row.get("role") != role
            or (provenance and row.get("provenance") != provenance)
        ):
            raise PilotError(f"publication additive entry mismatch: {path.name}")


def main() -> int:
    try:
        validate_templates()
        state = publication_state()
        if state == "PUBLICATION":
            validate_publication_evidence()
            print("PASS: Round 4A additive publication evidence is valid")
        else:
            print("PASS: Round 4A publication validator is frozen; lifecycle state = PREPUBLICATION")
        return 0
    except (PilotError, OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
