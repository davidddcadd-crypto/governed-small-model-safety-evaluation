#!/usr/bin/env python3
"""Freeze the complete analyzed pilot evidence set with SHA-256 hashes."""

from __future__ import annotations

import sys
from pathlib import Path

from pilot_common import ROOT, RESULTS, PilotError, sha256_bytes, utc_text, write_json_exclusive


def evidence_paths() -> list[Path]:
    required = [
        ROOT / "release_receipt.json",
        ROOT / "protocol_manifest.json",
        RESULTS / "execution_environment.json",
        RESULTS / "warmup.json",
        RESULTS / "formal_raw_results.jsonl",
        RESULTS / "blinded_rating_packet.jsonl",
        RESULTS / "blinding_key.json",
        RESULTS / "ratings_primary.jsonl",
        RESULTS / "PILOT_METRICS.json",
        RESULTS / "PILOT_REPORT.md",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise PilotError(f"result evidence is incomplete; missing: {missing}")
    if len(list((RESULTS / "requests").glob("RUN-*.request.json"))) != 24:
        raise PilotError("result manifest requires exactly 24 request files")
    if len(list((RESULTS / "raw_runs").glob("RUN-*.json"))) != 24:
        raise PilotError("result manifest requires exactly 24 raw-run files")
    if len(list((RESULTS / "attempts").glob("RUN-*-ATTEMPT-*.json"))) < 24:
        raise PilotError("result manifest requires at least 24 attempt files")
    paths = [path for path in required]
    for directory in (RESULTS / "requests", RESULTS / "attempts", RESULTS / "raw_runs"):
        paths.extend(path for path in directory.rglob("*") if path.is_file())
    for optional in (
        RESULTS / "ratings_secondary.jsonl",
        RESULTS / "adjudications.jsonl",
        RESULTS / "rater_session_secondary.json",
    ):
        if optional.is_file():
            paths.append(optional)
    return sorted(set(paths), key=lambda path: path.relative_to(ROOT).as_posix())


def main() -> int:
    try:
        target = RESULTS / "RESULT_MANIFEST.json"
        if target.exists():
            raise PilotError("result manifest already exists; refusing to regenerate")
        files = []
        for path in evidence_paths():
            payload = path.read_bytes()
            files.append(
                {
                    "path": path.relative_to(ROOT).as_posix(),
                    "size_bytes": len(payload),
                    "sha256": sha256_bytes(payload),
                }
            )
        write_json_exclusive(
            target,
            {
                "generated_at": utc_text(),
                "manifest_purpose": "Bind the complete v0.2.0 pilot evidence set before release.",
                "file_count": len(files),
                "files": files,
            },
        )
        print(f"PASS: result manifest created for {len(files)} evidence files")
        return 0
    except PilotError as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
