#!/usr/bin/env python3
"""Validate the additive Round 5A publication package without external execution."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from round5_common import CHECKPOINT_PATH, CHECKPOINT_SHA256, CHECKPOINT_SIZE, RESULTS, ROOT, ROUND5, PilotError, load_json, sha256_bytes
from validate_round5_core_result import validate_core_result

BASE_COMMIT = "dd0ca6afdf3e255f45a8c4d5f3596498d55ca2f0"
COMMIT_MESSAGE = "Add prespecified Granite 4 Round 5A replication evidence"
ROOT_GITATTRIBUTES_SHA256 = "d4b93c3c3844665b7a33dc30f73384f467406b3adaba0da7f3c93b6a9d18e285"
PROTOCOL_SHA256 = "a556679cc276422f250d556f0b512334652b40eb7c35bbe07a45551d4290fd5b"
CORE_MANIFEST_SHA256 = "70b8d757fb8ba8b9c475512a35405bf02881973df95f7ee5662f28eb78fe03ec"
MANIFEST_PATH = RESULTS / "PUBLICATION_MANIFEST.json"

REQUIRED_RELEASE_TERMS = (
    "`granite4:3b`",
    "12 frozen synthetic safety cases",
    "one observation per case-arm",
    "24 formal observations",
    "no repeated trials",
    "**supportive**",
    "25.0% (3/12)",
    "41.7% (5/12)",
    "75.0% (9/12)",
    "91.7% (11/12)",
    "12.5% (1/8)",
    "50.0% (2/4)",
    "75.0% (3/4)",
    "25.0% (1/4)",
    "0.0% (0/4)",
    "41.7% (5/12)",
    "0.0% (0/12)",
    "7.67",
    "8.42",
    "paired strict safety pass outcomes were 2 improved, 10 unchanged, and 0 worsened",
    "paired quality outcomes were 4 improved, 8 unchanged, and 0 worsened",
    "more prompt tokens and generated tokens and had higher mean client-wall and total latency",
    "one unsafe allow and two hard failures remained in each arm",
    "all five `format_fail` observations",
    "no output-format repair, model-specific parser rescue, selective format normalization, omission, selective rerun, selective regeneration, or equivalent repair",
    "improved formatting is not itself treated as evidence of safety improvement",
    "r5a-run-016",
    "rejected as non-authoritative",
    "no second model request",
    "david-calibrated openai `gpt-5.6-sol` `xhigh` ai surrogate",
    "frozen two-stage procedure",
    "expected_lifecycle_transition",
    "no statistical significance is claimed",
    "production safety",
    "frontier-model equivalence",
    "model-family generalization",
    "proof that governance works generally",
    "exactly one prespecified within-model arm a/b replication",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PilotError(message)


def binding(path: Path) -> dict[str, Any]:
    value = load_json(path)
    rows = value.get("files")
    require(isinstance(rows, list) and value.get("file_count") == len(rows), f"invalid manifest: {path}")
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256_bytes(path.read_bytes()), "file_count": len(rows)}


def validated_manifest_rows(path: Path) -> list[dict[str, Any]]:
    value = load_json(path)
    rows = value.get("files")
    require(isinstance(rows, list) and value.get("file_count") == len(rows), f"invalid manifest rows: {path}")
    for row in rows:
        require(isinstance(row, dict) and set(row) == {"path", "size_bytes", "sha256"}, f"invalid manifest row in {path}")
        target = ROOT / str(row["path"])
        payload = target.read_bytes()
        require(row == {"path": row["path"], "size_bytes": len(payload), "sha256": sha256_bytes(payload)}, f"frozen binding mismatch: {row['path']}")
    return [dict(row) for row in rows]


def collect_commit_paths(*, include_manifest: bool = True) -> list[str]:
    paths: set[str] = set()
    for directory in (ROUND5, RESULTS):
        for path in directory.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                paths.add(path.relative_to(ROOT).as_posix())
    for directory in (ROOT / "scripts", ROOT / "tests"):
        for path in directory.glob("*round5*.py"):
            if path.is_file():
                paths.add(path.relative_to(ROOT).as_posix())
    paths.discard("results/ratings_primary.partial.jsonl")
    if not include_manifest:
        paths.discard("results/round5_granite4_3b/PUBLICATION_MANIFEST.json")
    return sorted(paths)


def rows_for_paths(paths: list[str]) -> list[dict[str, Any]]:
    rows = []
    for relative in paths:
        payload = (ROOT / relative).read_bytes()
        rows.append({"path": relative, "size_bytes": len(payload), "sha256": sha256_bytes(payload)})
    return rows


def canonical_inventory() -> tuple[dict[str, Any], str]:
    rows = [{"path": row["path"], "status": "CREATE", "size_bytes": row["size_bytes"], "sha256": row["sha256"]} for row in rows_for_paths(collect_commit_paths())]
    value = {
        "inventory_version": "round5a-local-publication-commit-v1",
        "base_commit": BASE_COMMIT,
        "commit_message": COMMIT_MESSAGE,
        "path_count": len(rows),
        "status_counts": {"CREATE": len(rows), "MODIFY": 0, "DELETE": 0},
        "files": rows,
    }
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return value, hashlib.sha256(raw).hexdigest()


def validate_release_notes() -> None:
    text = " ".join((RESULTS / "ROUND5_RELEASE_NOTES_DRAFT.md").read_text(encoding="utf-8").split()).lower()
    missing = [term for term in REQUIRED_RELEASE_TERMS if term.lower() not in text]
    require(not missing, f"release-note disclosures missing: {missing}")
    forbidden = (
        "governance is proven generally effective",
        "statistically significant",
        "safe for production",
        "equivalent to frontier",
        "generalizes across model families",
        "round 5 had zero unsafe behavior",
    )
    present = [term for term in forbidden if term in text]
    require(not present, f"release-note overclaim detected: {present}")


def validate_publication(*, require_manifest: bool = True) -> dict[str, Any]:
    core = validate_core_result()
    require(core["signal"] == "SUPPORTIVE", "frozen Round-5 result is not SUPPORTIVE")
    require(sha256_bytes((ROOT / ".gitattributes").read_bytes()) == ROOT_GITATTRIBUTES_SHA256, "public root .gitattributes changed")
    if CHECKPOINT_PATH.exists():
        require(CHECKPOINT_PATH.is_file() and CHECKPOINT_PATH.stat().st_size == CHECKPOINT_SIZE and sha256_bytes(CHECKPOINT_PATH.read_bytes()) == CHECKPOINT_SHA256, "excluded checkpoint changed")
    validate_release_notes()

    addendum = " ".join((RESULTS / "ROUND5_PUBLICATION_ADDENDUM.md").read_text(encoding="utf-8").split()).lower()
    for term in ("supportive", "five `format_fail`", "no output-format repair", "r5a-run-016", "zero tool calls", "ten expected transitions", "no statistical significance"):
        require(term in addendum, f"publication addendum missing disclosure: {term}")

    plan = load_json(RESULTS / "ROUND5_PUBLICATION_CUSTODY_PLAN.json")
    require(plan.get("state_sequence", [])[-1] == "PUBLICATION_PACKAGE_FROZEN", "publication lifecycle state mismatch")
    require(plan.get("expected_lifecycle_transition_count") == 10 and plan.get("new_publication_transition_classifications") == [], "publication lifecycle disposition mismatch")
    require(plan.get("exact_byte_custody", {}).get("root_gitattributes_modified_for_round5") is False, "root .gitattributes mutation claimed")
    require(plan.get("future_release", {}).get("authorized_now") is False and plan.get("remote_mutation_authorized") is False, "publication plan exceeds authority")

    authorization = load_json(RESULTS / "ROUND5_PUBLICATION_PACKAGING_AUTHORIZATION.json")
    require(authorization.get("authorized_base_commit") == BASE_COMMIT and authorization.get("authorized_result") == "SUPPORTIVE", "publication authorization binding mismatch")
    validation = load_json(RESULTS / "ROUND5_PUBLICATION_VALIDATION.json")
    require(validation.get("checkpoint_excluded") is True and validation.get("model_execution_occurred") is False and validation.get("openai_transmission_occurred") is False, "publication validation boundary mismatch")

    if not require_manifest:
        return {"result": "PASS_PREMANIFEST", "commit_paths": len(collect_commit_paths())}

    if not MANIFEST_PATH.exists():
        raise PilotError("publication manifest is missing")

    manifest = load_json(MANIFEST_PATH)
    require(manifest.get("publication_manifest_version") == "round5a-publication-v1", "publication manifest version mismatch")
    protocol = ROUND5 / "round5_protocol_manifest_v3.json"
    core_manifest = RESULTS / "RESULT_MANIFEST.json"
    require(sha256_bytes(protocol.read_bytes()) == PROTOCOL_SHA256 and manifest.get("frozen_protocol_manifest") == binding(protocol), "protocol publication binding mismatch")
    require(sha256_bytes(core_manifest.read_bytes()) == CORE_MANIFEST_SHA256 and manifest.get("frozen_core_result_manifest") == binding(core_manifest), "core-result publication binding mismatch")
    require(manifest.get("frozen_protocol_files") == validated_manifest_rows(protocol), "direct protocol rows mismatch")
    require(manifest.get("frozen_core_result_files") == validated_manifest_rows(core_manifest), "direct core-result rows mismatch")
    expected_paths = collect_commit_paths(include_manifest=False)
    expected_rows = rows_for_paths(expected_paths)
    require(manifest.get("publication_package_file_count") == len(expected_rows) and manifest.get("publication_package_files") == expected_rows, "publication package rows mismatch")
    require("results/ratings_primary.partial.jsonl" not in expected_paths, "excluded checkpoint entered publication set")
    require(manifest.get("excluded_local_checkpoint", {}).get("published") is False, "checkpoint exclusion not bound")
    require(manifest.get("release_status") == "LOCAL_COMMIT_ONLY_REMOTE_PUBLICATION_NOT_AUTHORIZED", "release status exceeds authorization")
    return {"result": "PASS_PUBLICATION_PACKAGE", "commit_paths": len(collect_commit_paths()), "manifest_bound_files": len(expected_rows)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pre-manifest", action="store_true")
    parser.add_argument("--inventory", action="store_true")
    args = parser.parse_args()
    try:
        result = validate_publication(require_manifest=not args.pre_manifest)
        if args.inventory:
            inventory, digest = canonical_inventory()
            print(json.dumps({"inventory_sha256": digest, "path_count": inventory["path_count"], "status_counts": inventory["status_counts"]}, sort_keys=True))
        else:
            print(json.dumps(result, sort_keys=True))
        return 0
    except (PilotError, OSError, KeyError, TypeError, ValueError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
