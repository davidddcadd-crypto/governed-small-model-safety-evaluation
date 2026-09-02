#!/usr/bin/env python3
"""Create an additive manifest for Round 2A publication disclosures."""

from __future__ import annotations

import sys
from pathlib import Path

from round2_common import (
    RESULTS, ROOT, PilotError, load_json, sha256_bytes, utc_text,
    write_json_exclusive,
)

BASE_RESULT_MANIFEST_SHA256 = (
    "ae8e0ff43ae9f57245310b744741a87ce59040f76664a5ab2b59fc36cdf9c7c3"
)
ADDITIVE_PATHS = (
    RESULTS / "ROUND2_PUBLICATION_ADDENDUM.md",
    RESULTS / "publication_disclosures" / "SCHEMA_REJECTION_PROVENANCE.json",
    RESULTS / "publication_disclosures" / "STAGE1_SCHEMA_REJECTION.jsonl",
    RESULTS / "publication_disclosures" / "STAGE2_SCHEMA_REJECTION.jsonl",
)


def build() -> dict:
    base = RESULTS / "RESULT_MANIFEST.json"
    if sha256_bytes(base.read_bytes()) != BASE_RESULT_MANIFEST_SHA256:
        raise PilotError("frozen Round-2 result manifest hash mismatch")
    base_value = load_json(base)
    if base_value.get("file_count") != 92 or len(base_value.get("files", [])) != 92:
        raise PilotError("frozen Round-2 result manifest does not contain 92 files")
    missing = [str(path) for path in ADDITIVE_PATHS if not path.is_file()]
    if missing:
        raise PilotError(f"publication disclosure files are incomplete: {missing}")
    files = []
    for path in sorted(ADDITIVE_PATHS):
        payload = path.read_bytes()
        files.append({
            "path": path.relative_to(ROOT).as_posix(),
            "size_bytes": len(payload),
            "sha256": sha256_bytes(payload),
        })
    return {
        "publication_manifest_version": "round2a-publication-v1",
        "generated_at": utc_text(),
        "manifest_purpose": (
            "Bind additive Round 2A publication disclosures without changing "
            "the frozen 92-file result set."
        ),
        "base_result_manifest": {
            "path": "results/round2_ministral3b/RESULT_MANIFEST.json",
            "sha256": BASE_RESULT_MANIFEST_SHA256,
            "file_count": 92,
        },
        "additive_file_count": len(files),
        "additive_files": files,
    }


def main() -> int:
    try:
        target = RESULTS / "PUBLICATION_MANIFEST.json"
        if target.exists():
            raise PilotError("refusing to overwrite publication manifest")
        value = build()
        write_json_exclusive(target, value)
        print(
            f"PASS: Round 2A publication manifest created for "
            f"{value['additive_file_count']} additive files"
        )
        return 0
    except (PilotError, OSError) as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
