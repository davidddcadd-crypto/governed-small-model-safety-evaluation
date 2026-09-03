#!/usr/bin/env python3
"""Build or refresh the additive Round 5A publication manifest."""

from __future__ import annotations

import argparse
import json
import os
import sys

from round5_common import RESULTS, ROOT, ROUND5, PilotError, load_json, sha256_bytes, utc_text
from validate_round5_publication import collect_commit_paths, rows_for_paths, validate_publication


def manifest_binding(path):
    value = load_json(path)
    rows = value.get("files")
    if not isinstance(rows, list) or value.get("file_count") != len(rows):
        raise PilotError(f"manifest count mismatch: {path}")
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256_bytes(path.read_bytes()), "file_count": len(rows)}


def manifest_rows(path):
    value = load_json(path)
    rows = value.get("files")
    if not isinstance(rows, list) or value.get("file_count") != len(rows):
        raise PilotError(f"manifest count mismatch: {path}")
    return rows


def build():
    validate_publication(require_manifest=False)
    protocol = ROUND5 / "round5_protocol_manifest_v3.json"
    core = RESULTS / "RESULT_MANIFEST.json"
    package_paths = collect_commit_paths(include_manifest=False)
    return {
        "publication_manifest_version": "round5a-publication-v1",
        "generated_at": utc_text(),
        "manifest_purpose": "Bind the frozen Round 5A protocol and core result plus additive publication, lifecycle, exact-byte, and custody evidence without changing scientific evidence.",
        "frozen_protocol_manifest": manifest_binding(protocol),
        "frozen_protocol_files": manifest_rows(protocol),
        "frozen_core_result_manifest": manifest_binding(core),
        "frozen_core_result_files": manifest_rows(core),
        "publication_package_file_count": len(package_paths),
        "publication_package_files": rows_for_paths(package_paths),
        "root_gitattributes": {
            "path": ".gitattributes",
            "sha256": "d4b93c3c3844665b7a33dc30f73384f467406b3adaba0da7f3c93b6a9d18e285",
            "modified_for_round5": False,
            "included_in_round5_commit_delta": False
        },
        "excluded_local_checkpoint": {
            "path": "results/ratings_primary.partial.jsonl",
            "published": False,
            "if_present_size_bytes": 31022,
            "if_present_sha256": "114e940605fc0cdca16969e3abd6c8600ca1d2967bbe464d38619c769486265f"
        },
        "prespecified_result": "SUPPORTIVE",
        "planned_release": {
            "tag": "v0.6.0",
            "title": "v0.6.0 — Granite 4 3B Round 5A Replication",
            "authorized": False
        },
        "release_status": "LOCAL_COMMIT_ONLY_REMOTE_PUBLICATION_NOT_AUTHORIZED"
    }


def write_manifest(value, *, refresh):
    target = RESULTS / "PUBLICATION_MANIFEST.json"
    if target.exists() and not refresh:
        raise PilotError("refusing to overwrite existing Round-5 publication manifest without --refresh")
    raw = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    temporary = target.with_name(target.name + ".tmp")
    with temporary.open("xb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, target)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    try:
        write_manifest(build(), refresh=args.refresh)
        print("PASS: Round 5A publication manifest created")
        return 0
    except (PilotError, OSError, KeyError, TypeError, ValueError) as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
