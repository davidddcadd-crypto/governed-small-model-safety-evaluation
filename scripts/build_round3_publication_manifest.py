#!/usr/bin/env python3
"""Create the additive Round 3A publication manifest without altering results."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from round3_common import (
    RESULTS,
    ROOT,
    ROUND3,
    PilotError,
    load_json,
    sha256_bytes,
    utc_text,
    write_json_exclusive,
)

PROTOCOL_MANIFEST_SHA256 = (
    "399aafe74784d85e06b7fb0cfb4640f417de4a39545dc83bdb68e189de8c90dc"
)
RESULT_MANIFEST_SHA256 = (
    "c9d2dc906f0450f3c5eae8d5ce057a894bb2b3d144474d513bef18743b1b8ccd"
)
ADDITIVE_SPECS: tuple[tuple[Path, str, dict[str, Any]], ...] = (
    (
        RESULTS / "POSTEXECUTION_VALIDATION.json",
        "Additive lifecycle and custody validation record",
        {},
    ),
    (
        RESULTS / "ROUND3_PUBLICATION_ADDENDUM.md",
        "Limitations-first public disclosure supplement",
        {},
    ),
    (
        RESULTS / "stage1_combined.log",
        "Preserved Stage-1 combined command/event output",
        {
            "origin": "Authorized Round 3A Stage-1 surrogate extraction session",
            "canonical_stage_event_log_path": "results/round3_granite41_3b/stage1_events.jsonl",
            "substitutes_canonical_stage_event_log": False,
        },
    ),
    (
        RESULTS / "stage2_combined.log",
        "Preserved Stage-2 combined command/event output",
        {
            "origin": "Authorized Round 3A Stage-2 surrogate scoring session",
            "canonical_stage_event_log_path": "results/round3_granite41_3b/stage2_events.jsonl",
            "substitutes_canonical_stage_event_log": False,
        },
    ),
)


def _validate_frozen_manifest(path: Path, expected_hash: str, expected_count: int) -> None:
    payload = path.read_bytes()
    if sha256_bytes(payload) != expected_hash:
        raise PilotError(f"frozen manifest hash mismatch: {path.relative_to(ROOT).as_posix()}")
    value = load_json(path)
    if value.get("file_count") != expected_count or len(value.get("files", [])) != expected_count:
        raise PilotError(f"frozen manifest count mismatch: {path.relative_to(ROOT).as_posix()}")


def build() -> dict[str, Any]:
    _validate_frozen_manifest(
        ROUND3 / "round3_protocol_manifest.json", PROTOCOL_MANIFEST_SHA256, 36
    )
    _validate_frozen_manifest(
        RESULTS / "RESULT_MANIFEST.json", RESULT_MANIFEST_SHA256, 94
    )
    missing = [str(path) for path, _role, _provenance in ADDITIVE_SPECS if not path.is_file()]
    if missing:
        raise PilotError(f"publication evidence is incomplete: {missing}")
    files: list[dict[str, Any]] = []
    for path, role, provenance in sorted(
        ADDITIVE_SPECS, key=lambda item: item[0].relative_to(ROOT).as_posix()
    ):
        payload = path.read_bytes()
        row: dict[str, Any] = {
            "path": path.relative_to(ROOT).as_posix(),
            "size_bytes": len(payload),
            "sha256": sha256_bytes(payload),
            "role": role,
        }
        if provenance:
            row["provenance"] = provenance
        files.append(row)
    return {
        "publication_manifest_version": "round3a-publication-v1",
        "generated_at": utc_text(),
        "manifest_purpose": (
            "Bind additive Round 3A publication disclosures and preserved combined "
            "logs without changing the frozen 94-file result set."
        ),
        "frozen_protocol_manifest": {
            "path": "round3/round3_protocol_manifest.json",
            "sha256": PROTOCOL_MANIFEST_SHA256,
            "file_count": 36,
        },
        "frozen_result_manifest": {
            "path": "results/round3_granite41_3b/RESULT_MANIFEST.json",
            "sha256": RESULT_MANIFEST_SHA256,
            "file_count": 94,
        },
        "additive_file_count": len(files),
        "additive_files": files,
    }


def main() -> int:
    try:
        target = RESULTS / "PUBLICATION_MANIFEST.json"
        if target.exists():
            raise PilotError("refusing to overwrite Round-3 publication manifest")
        value = build()
        write_json_exclusive(target, value)
        print(
            f"PASS: Round 3A publication manifest created for "
            f"{value['additive_file_count']} additive files"
        )
        return 0
    except (PilotError, OSError, KeyError, TypeError, ValueError) as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
