#!/usr/bin/env python3
"""Construct the authorized local-only Round 5A Stage-2 prompt."""

from __future__ import annotations

import sys

from round5_common import RESULTS, PilotError, sha256_bytes

STAGE1_RAW_OUTPUT_SHA256 = "cf249fe6b9886e841b72a9470906aabb353114166121667322d2d1ef992ea0c1"
PREAMBLE = (
    "STAGE 2 — GOLD-DISCLOSED SCORING\n\n"
    "Continue in the same David-calibrated AI surrogate-rater session. Use no tools, "
    "inspect no files, and use no external context. Stage 1 extraction is frozen: do not "
    "revise any frozen_extracted_decision or extraction_evidence. For each of the 24 "
    "response IDs, score every frozen rubric dimension, exactly partition every supplied "
    "gold_record.critical_findings item into critical_findings_present or "
    "critical_findings_missing, identify only actual hard failures, and provide concise "
    "response-grounded evidence and a reason. Return only one JSON object matching the "
    "supplied output schema, with all 24 ratings exactly once.\n\n"
)
START = "--- BEGIN ROUND-5 GOLD-DISCLOSED BLINDED SCORING PACKET ---\n"
END = "\n--- END ROUND-5 GOLD-DISCLOSED BLINDED SCORING PACKET ---\n"


def build() -> None:
    stage1_path = RESULTS / "stage1_raw_output.json"
    packet_path = RESULTS / "blinded_scoring_packet.jsonl"
    prompt_path = RESULTS / "stage2_prompt.txt"
    if prompt_path.exists():
        raise PilotError("Stage-2 prompt already exists")
    if not stage1_path.is_file() or sha256_bytes(stage1_path.read_bytes()) != STAGE1_RAW_OUTPUT_SHA256:
        raise PilotError("frozen Stage-1 output mismatch")
    if not packet_path.is_file():
        raise PilotError("Stage-2 scoring packet is absent")
    packet = packet_path.read_text(encoding="utf-8").rstrip("\r\n")
    prompt = PREAMBLE + START + packet + END
    with prompt_path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(prompt)


def main() -> int:
    try:
        build()
        print("PASS: local-only Round-5 Stage-2 prompt constructed")
        return 0
    except (PilotError, OSError) as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
