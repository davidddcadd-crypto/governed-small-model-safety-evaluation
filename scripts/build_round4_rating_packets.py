#!/usr/bin/env python3
"""Build Round 4A two-stage blinded packets with extraction frozen before gold."""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any

from round4_common import (
    RESULTS, ROOT, PilotError, load_json, load_jsonl, sha256_bytes, utc_text,
    write_json_exclusive, write_jsonl_atomic,
)

BLINDING_SEED = 20260902


def _load_complete_runs() -> list[dict[str, Any]]:
    paths = sorted((RESULTS / "raw_runs").glob("R4A-RUN-*.json"))
    if len(paths) != 24:
        raise PilotError(f"need 24 immutable Round-4 runs; found {len(paths)}")
    rows = [load_json(path) for path in paths]
    if {row.get("sequence") for row in rows} != set(range(1, 25)):
        raise PilotError("Round-4 sequences are incomplete or duplicated")
    return rows


def build_stage1() -> None:
    packet_path = RESULTS / "blinded_extraction_packet.jsonl"
    key_path = RESULTS / "blinding_key.json"
    if packet_path.exists() or key_path.exists():
        raise PilotError("Stage-1 blinding artifacts already exist")
    cases = {row["case_id"]: row for row in load_jsonl(ROOT / "data/pilot_cases.jsonl")}
    shuffled = _load_complete_runs()
    random.Random(BLINDING_SEED).shuffle(shuffled)
    packet, key = [], []
    for index, run in enumerate(shuffled, start=1):
        response_id = f"R4R{index:03d}"
        case = cases[run["case_id"]]
        packet.append({"response_id": response_id, "scenario": case["scenario"], "requested_action": case["requested_action"], "raw_response": run["raw_response"], "format_status": run["format_status"]})
        key.append({"response_id": response_id, "run_id": run["run_id"], "sequence": run["sequence"], "arm": run["arm"], "case_id": run["case_id"]})
    write_jsonl_atomic(packet_path, packet)
    write_json_exclusive(key_path, {"created_at": utc_text(), "blinding_seed": BLINDING_SEED, "extraction_packet_sha256": sha256_bytes(packet_path.read_bytes()), "warning": "Never provide this file to the surrogate rater.", "entries": key})


def validated_extractions(path: Path) -> dict[str, dict[str, Any]]:
    value = load_json(path)
    if not isinstance(value, dict) or set(value) != {"stage", "ratings"} or value.get("stage") != "DECISION_EXTRACTION":
        raise PilotError("Stage-1 raw output structure is invalid")
    packet = {row["response_id"]: row for row in load_jsonl(RESULTS / "blinded_extraction_packet.jsonl")}
    if not isinstance(value["ratings"], list) or len(value["ratings"]) != 24 or len(packet) != 24:
        raise PilotError("Stage-1 output and packet must each contain 24 rows")
    result: dict[str, dict[str, Any]] = {}
    required = {"response_id", "extracted_decision", "format_status", "extraction_evidence"}
    for row in value["ratings"]:
        if not isinstance(row, dict) or set(row) != required:
            raise PilotError("Stage-1 extraction row keys are invalid")
        rid = row["response_id"]
        if rid not in packet or rid in result:
            raise PilotError(f"unknown or duplicate Stage-1 response: {rid}")
        if row["format_status"] != packet[rid]["format_status"]:
            raise PilotError(f"format status changed in Stage 1: {rid}")
        if row["extracted_decision"] not in {"ALLOW", "DENY", "ESCALATE", None}:
            raise PilotError(f"invalid extracted decision: {rid}")
        if not isinstance(row["extraction_evidence"], str) or not row["extraction_evidence"].strip():
            raise PilotError(f"missing extraction evidence: {rid}")
        result[rid] = row
    return result


def build_stage2(extractions_path: Path) -> None:
    target = RESULTS / "blinded_scoring_packet.jsonl"
    preserved = RESULTS / "stage1_raw_output.json"
    if target.exists():
        raise PilotError("Stage-2 scoring packet already exists")
    payload = extractions_path.read_bytes()
    if preserved.exists() and preserved.read_bytes() != payload:
        raise PilotError("preserved Stage-1 raw output differs")
    if not preserved.exists():
        with preserved.open("xb") as handle:
            handle.write(payload)
    extractions = validated_extractions(preserved)
    key = load_json(RESULTS / "blinding_key.json")
    mapping = {row["response_id"]: row for row in key["entries"]}
    packet = {row["response_id"]: row for row in load_jsonl(RESULTS / "blinded_extraction_packet.jsonl")}
    gold = {row["case_id"]: row for row in load_jsonl(ROOT / "data/gold_records.jsonl")}
    rows = []
    for rid, source in packet.items():
        gold_record = dict(gold[mapping[rid]["case_id"]])
        gold_record.pop("case_id", None)
        rows.append({**source, "frozen_extracted_decision": extractions[rid]["extracted_decision"], "extraction_evidence": extractions[rid]["extraction_evidence"], "gold_record": gold_record, "stage1_raw_output_sha256": sha256_bytes(preserved.read_bytes())})
    write_jsonl_atomic(target, rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="stage", required=True)
    sub.add_parser("stage1")
    stage2 = sub.add_parser("stage2")
    stage2.add_argument("--extractions", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.stage == "stage1":
            build_stage1()
            print("PASS: Round-4 gold-free packet and withheld blinding key created")
        else:
            build_stage2(args.extractions.resolve())
            print("PASS: Round-4 Stage-1 extraction frozen before Stage-2 packet")
        return 0
    except (PilotError, OSError) as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

