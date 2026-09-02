#!/usr/bin/env python3
"""Exclusively create the Round 2A preparation manifest."""

from __future__ import annotations

import sys

from round2_common import (
    MODEL_BLOB_SHA256, MODEL_MANIFEST_SHA256, MODEL_TAG, ROUND2, ROOT,
    SOURCE_HASHES, PilotError, run_round1_validator, sha256_bytes, utc_text,
    validate_sources, write_json_exclusive,
)

FILES = [
    "round2/README.md",
    "round2/ROUND2_PROTOCOL.md",
    "round2/DAVID_RATER_CALIBRATION_V1.md",
    "round2/RATER_ISOLATION_PROCEDURE.md",
    "round2/RATING_INSTRUCTIONS.md",
    "round2/MODEL_AND_ENVIRONMENT.json",
    "round2/RESULT_MANIFEST_PLAN.json",
    "round2/schemas/surrogate_extraction_output.schema.json",
    "round2/schemas/surrogate_scoring_output.schema.json",
    "round2/schemas/surrogate_rating.schema.json",
    "round2/schemas/raw_run.schema.json",
    "round2/schemas/rater_session.schema.json",
    "scripts/round2_common.py",
    "scripts/run_round2.py",
    "scripts/build_round2_rating_packets.py",
    "scripts/validate_round2_ratings.py",
    "scripts/analyze_round2.py",
    "scripts/build_round2_result_manifest.py",
    "scripts/validate_round2.py",
    "scripts/build_round2_protocol_manifest.py",
    "tests/test_round2_tools.py",
]


def main() -> int:
    try:
        run_round1_validator()
        validate_sources()
        missing = [relative for relative in FILES if not (ROOT / relative).is_file()]
        if missing:
            raise PilotError(f"cannot freeze incomplete preparation: {missing}")
        entries = []
        for relative in FILES:
            payload = (ROOT / relative).read_bytes()
            entries.append({
                "path": relative,
                "size_bytes": len(payload),
                "sha256": sha256_bytes(payload),
            })
        write_json_exclusive(
            ROUND2 / "round2_protocol_manifest.json",
            {
                "protocol_version": "round2a-v1",
                "generated_at": utc_text(),
                "manifest_purpose": "Bind Round 2A before any formal Ministral observation.",
                "formal_observations_before_freeze": 0,
                "round1_baseline": {
                    "commit": "9ced40bc11f5995f27ddd74d0104248af287a418",
                    "protocol_tag": "v0.1.0",
                    "results_tag": "v0.2.0",
                },
                "model_identity": {
                    "tag": MODEL_TAG,
                    "manifest_sha256": MODEL_MANIFEST_SHA256,
                    "blob_sha256": MODEL_BLOB_SHA256,
                    "ollama_version": "0.33.2",
                    "quantization": "Q4_K_M",
                },
                "source_bindings": [
                    {"path": path, "sha256": digest}
                    for path, digest in SOURCE_HASHES.items()
                ],
                "file_count": len(entries),
                "files": entries,
            },
        )
    except PilotError as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        return 1
    print(f"PASS: Round 2A protocol manifest created for {len(entries)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
