#!/usr/bin/env python3
"""Create an additive Round 4A publication manifest after completed evidence."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from round4_common import RESULTS, ROOT, ROUND4, PilotError, load_json, sha256_bytes, utc_text, write_json_exclusive
from validate_round4_postexecution import validate_completed_evidence

ADDITIVE_SPECS: tuple[tuple[Path, str, dict[str, Any]], ...] = (
    (RESULTS / "POSTEXECUTION_VALIDATION.json", "Additive lifecycle and custody validation record", {}),
    (RESULTS / "ROUND4_PUBLICATION_ADDENDUM.md", "Limitations-first public disclosure supplement", {}),
    (
        RESULTS / "stage1_combined.log",
        "Preserved Stage-1 combined command/event output",
        {
            "origin": "Authorized Round 4A Stage-1 surrogate extraction session",
            "canonical_stage_event_log_path": "results/round4_llama32_3b/stage1_events.jsonl",
            "substitutes_canonical_stage_event_log": False,
        },
    ),
    (
        RESULTS / "stage2_combined.log",
        "Preserved Stage-2 combined command/event output",
        {
            "origin": "Authorized Round 4A Stage-2 surrogate scoring session",
            "canonical_stage_event_log_path": "results/round4_llama32_3b/stage2_events.jsonl",
            "substitutes_canonical_stage_event_log": False,
        },
    ),
)


def _manifest_binding(path: Path) -> dict[str, Any]:
    value = load_json(path)
    rows = value.get("files")
    if not isinstance(rows, list) or value.get("file_count") != len(rows):
        raise PilotError(f"manifest count mismatch: {path.relative_to(ROOT).as_posix()}")
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": sha256_bytes(path.read_bytes()),
        "file_count": len(rows),
    }


def build() -> dict[str, Any]:
    validate_completed_evidence()
    missing = [path.relative_to(ROOT).as_posix() for path, _role, _provenance in ADDITIVE_SPECS if not path.is_file()]
    if missing:
        raise PilotError(f"publication evidence is incomplete: {missing}")
    files: list[dict[str, Any]] = []
    for path, role, provenance in sorted(ADDITIVE_SPECS, key=lambda item: item[0].relative_to(ROOT).as_posix()):
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
        "publication_manifest_version": "round4a-publication-v1",
        "generated_at": utc_text(),
        "manifest_purpose": "Bind additive Round 4A publication disclosures without changing frozen result evidence.",
        "frozen_protocol_manifest": _manifest_binding(ROUND4 / "round4_protocol_manifest_v3.json"),
        "frozen_result_manifest": _manifest_binding(RESULTS / "RESULT_MANIFEST.json"),
        "additive_file_count": len(files),
        "additive_files": files,
    }


def main() -> int:
    try:
        target = RESULTS / "PUBLICATION_MANIFEST.json"
        if target.exists():
            raise PilotError("refusing to overwrite Round-4 publication manifest")
        value = build()
        write_json_exclusive(target, value)
        print(f"PASS: Round 4A publication manifest created for {value['additive_file_count']} additive files")
        return 0
    except (PilotError, OSError, KeyError, TypeError, ValueError) as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
