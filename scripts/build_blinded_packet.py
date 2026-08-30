#!/usr/bin/env python3
"""Build a fixed blinded rating packet from all 24 immutable run records."""

from __future__ import annotations

import random
import sys

from pilot_common import (
    RESULTS,
    PilotError,
    load_cases_by_id,
    load_gold_by_id,
    load_json,
    sha256_text,
    utc_text,
    write_json_exclusive,
    write_jsonl_atomic,
)


BLINDING_SEED = 20260829


def main() -> int:
    try:
        run_paths = sorted((RESULTS / "raw_runs").glob("RUN-*.json"))
        if len(run_paths) != 24:
            raise PilotError(f"need 24 immutable run records; found {len(run_paths)}")
        if (RESULTS / "blinded_rating_packet.jsonl").exists() or (RESULTS / "blinding_key.json").exists():
            raise PilotError("blinding artifacts already exist; refusing to regenerate or reshuffle")

        runs = [load_json(path) for path in run_paths]
        if {row["sequence"] for row in runs} != set(range(1, 25)):
            raise PilotError("run sequences are incomplete or duplicated")
        cases = load_cases_by_id()
        gold = load_gold_by_id()
        shuffled = list(runs)
        random.Random(BLINDING_SEED).shuffle(shuffled)

        packet = []
        key_entries = []
        for index, run in enumerate(shuffled, start=1):
            response_id = f"R{index:03d}"
            case_id = run["case_id"]
            case = cases[case_id]
            packet.append(
                {
                    "response_id": response_id,
                    "case_id": case_id,
                    "scenario": case["scenario"],
                    "requested_action": case["requested_action"],
                    "gold_record": gold[case_id],
                    "raw_response": run["raw_response"],
                    "format_status": run["format_status"],
                }
            )
            key_entries.append(
                {
                    "response_id": response_id,
                    "run_id": run["run_id"],
                    "sequence": run["sequence"],
                    "arm": run["arm"],
                    "case_id": case_id,
                }
            )

        write_jsonl_atomic(RESULTS / "blinded_rating_packet.jsonl", packet)
        packet_text = (RESULTS / "blinded_rating_packet.jsonl").read_text(encoding="utf-8")
        write_json_exclusive(
            RESULTS / "blinding_key.json",
            {
                "created_at": utc_text(),
                "blinding_seed": BLINDING_SEED,
                "packet_sha256": sha256_text(packet_text),
                "warning": "Do not inspect before completing the primary rating.",
                "entries": key_entries,
            },
        )
        print("PASS: blinded packet created with 24 anonymous responses")
        print("Rate only results/blinded_rating_packet.jsonl; do not inspect results/blinding_key.json")
        return 0
    except PilotError as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
