#!/usr/bin/env python3
"""Exclusively bind the complete analyzed Round 2A evidence set."""

from __future__ import annotations

import sys
from pathlib import Path

from round2_common import (
    RESULTS, ROOT, PilotError, sha256_bytes, utc_text, write_json_exclusive,
)


def evidence_paths() -> list[Path]:
    required = [
        ROOT / "round2/round2_protocol_manifest.json",
        ROOT / "round2/DAVID_RATER_CALIBRATION_V1.md",
        ROOT / "docs/SCORING_RUBRIC.md",
        RESULTS / "PROJECT_OWNER_AUTHORIZATION.json",
        RESULTS / "warmup.json",
        RESULTS / "execution_environment.json",
        RESULTS / "formal_raw_results.jsonl",
        RESULTS / "blinded_extraction_packet.jsonl",
        RESULTS / "blinding_key.json",
        RESULTS / "stage1_prompt.txt",
        RESULTS / "stage1_events.jsonl",
        RESULTS / "stage1_raw_output.json",
        RESULTS / "blinded_scoring_packet.jsonl",
        RESULTS / "stage2_prompt.txt",
        RESULTS / "stage2_events.jsonl",
        RESULTS / "stage2_raw_output.json",
        RESULTS / "rater_session.json",
        RESULTS / "ratings_surrogate.jsonl",
        RESULTS / "ROUND2_METRICS.json",
        RESULTS / "ROUND2_REPORT.md",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise PilotError(f"Round-2 evidence is incomplete: {missing}")
    if len(list((RESULTS / "requests").glob("R2A-RUN-*.request.json"))) != 24:
        raise PilotError("result manifest requires exactly 24 requests")
    if len(list((RESULTS / "raw_runs").glob("R2A-RUN-*.json"))) != 24:
        raise PilotError("result manifest requires exactly 24 raw runs")
    if len(list((RESULTS / "attempts").glob("R2A-RUN-*-ATTEMPT-*.json"))) < 24:
        raise PilotError("result manifest requires at least 24 attempts")
    paths = list(required)
    for directory in (RESULTS / "requests", RESULTS / "attempts", RESULTS / "raw_runs"):
        paths.extend(path for path in directory.rglob("*") if path.is_file())
    return sorted(set(paths), key=lambda path: path.relative_to(ROOT).as_posix())


def main() -> int:
    try:
        target = RESULTS / "RESULT_MANIFEST.json"
        if target.exists():
            raise PilotError("Round-2 result manifest already exists")
        files = []
        for path in evidence_paths():
            payload = path.read_bytes()
            files.append({
                "path": path.relative_to(ROOT).as_posix(),
                "size_bytes": len(payload),
                "sha256": sha256_bytes(payload),
            })
        write_json_exclusive(target, {
            "generated_at": utc_text(),
            "manifest_purpose": "Bind complete Round 2A evidence before any publication.",
            "file_count": len(files),
            "files": files,
        })
        print(f"PASS: Round 2A result manifest created for {len(files)} files")
        return 0
    except (PilotError, OSError) as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
