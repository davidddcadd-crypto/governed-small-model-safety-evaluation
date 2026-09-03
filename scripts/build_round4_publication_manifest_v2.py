#!/usr/bin/env python3
"""Build the future additive Round 4A publication manifest with repair custody."""

from __future__ import annotations

import sys
from pathlib import Path

from round4_common import RESULTS, ROOT, ROUND4, PilotError, load_json, sha256_bytes, utc_text, write_json_exclusive
from validate_round4_postmanifest_repair import FUTURE_ADDITIVE_PATHS, validate_additive


def _manifest_binding(path: Path) -> dict[str, object]:
    value = load_json(path)
    rows = value.get("files")
    if not isinstance(rows, list) or value.get("file_count") != len(rows):
        raise PilotError(f"manifest count mismatch: {path.relative_to(ROOT).as_posix()}")
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256_bytes(path.read_bytes()), "file_count": len(rows)}


def _manifest_rows(path: Path) -> list[dict[str, object]]:
    value = load_json(path)
    rows = value.get("files")
    if not isinstance(rows, list) or value.get("file_count") != len(rows):
        raise PilotError(f"manifest count mismatch: {path.relative_to(ROOT).as_posix()}")
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"path", "size_bytes", "sha256"}:
            raise PilotError(f"invalid manifest row: {path.relative_to(ROOT).as_posix()}")
        target = ROOT / str(row["path"])
        if not target.is_file():
            raise PilotError(f"manifest target missing: {row['path']}")
        payload = target.read_bytes()
        expected = {"path": row["path"], "size_bytes": len(payload), "sha256": sha256_bytes(payload)}
        if row != expected:
            raise PilotError(f"manifest target changed: {row['path']}")
    return [dict(row) for row in rows]


def build() -> dict[str, object]:
    validate_additive()
    paths = [ROOT / relative for relative in FUTURE_ADDITIVE_PATHS]
    missing = [path.relative_to(ROOT).as_posix() for path in paths if not path.is_file()]
    if missing:
        raise PilotError(f"additive publication custody is incomplete: {missing}")
    files = []
    for path in paths:
        payload = path.read_bytes()
        files.append({"path": path.relative_to(ROOT).as_posix(), "size_bytes": len(payload), "sha256": sha256_bytes(payload)})
    return {
        "publication_manifest_version": "round4a-publication-v2",
        "generated_at": utc_text(),
        "manifest_purpose": "Directly bind frozen Round 4A protocol/result evidence plus additive disclosures, lifecycle repair, exact-byte custody, and the preserved pre-sampling rejection without changing frozen evidence.",
        "frozen_protocol_manifest": _manifest_binding(ROUND4 / "round4_protocol_manifest_v3.json"),
        "frozen_protocol_files": _manifest_rows(ROUND4 / "round4_protocol_manifest_v3.json"),
        "frozen_result_manifest": _manifest_binding(RESULTS / "RESULT_MANIFEST.json"),
        "frozen_result_files": _manifest_rows(RESULTS / "RESULT_MANIFEST.json"),
        "publication_package_file_count": len(files),
        "publication_package_files": files,
        "excluded_local_checkpoint": {
            "path": "results/ratings_primary.partial.jsonl",
            "published": False,
            "if_present_size_bytes": 31022,
            "if_present_sha256": "114e940605fc0cdca16969e3abd6c8600ca1d2967bbe464d38619c769486265f",
        },
        "release_status": "DRAFT_ONLY_NOT_AUTHORIZED",
    }


def main() -> int:
    try:
        target = RESULTS / "PUBLICATION_MANIFEST.json"
        if target.exists():
            raise PilotError("refusing to overwrite Round-4 publication manifest")
        write_json_exclusive(target, build())
        print("PASS: Round 4A publication-v2 manifest created")
        return 0
    except (PilotError, OSError, KeyError, TypeError, ValueError) as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
