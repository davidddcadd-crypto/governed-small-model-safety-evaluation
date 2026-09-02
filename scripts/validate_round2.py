#!/usr/bin/env python3
"""Validate the frozen Round 2A preparation without running the model."""

from __future__ import annotations

import json
import re
import sys

from round2_common import (
    MODEL_BLOB_SHA256, MODEL_MANIFEST_SHA256, MODEL_TAG, ROUND2, ROOT,
    SOURCE_HASHES, PilotError, load_json, load_order, run_round1_validator,
    sha256_bytes, validate_sources,
)


def validate_calibration() -> None:
    text = (ROUND2 / "DAVID_RATER_CALIBRATION_V1.md").read_text(encoding="utf-8")
    if re.search(r"\bR\d{3}\b|\bC\d{2}\b", text):
        raise PilotError("calibration leaks a response or case identifier")
    lowered = text.lower()
    for phrase in ("arm a", "arm b", "case-to-response", "expected-decision lookup"):
        if phrase in lowered:
            raise PilotError(f"calibration contains forbidden mapping phrase: {phrase}")
    gold = [json.loads(line) for line in (ROOT / "data/gold_records.jsonl").read_text(
        encoding="utf-8"
    ).splitlines()]
    for row in gold:
        for finding in row["critical_findings"]:
            if finding.strip() and finding.strip() in text:
                raise PilotError("calibration leaks an exact required finding")


def validate_manifest() -> None:
    path = ROUND2 / "round2_protocol_manifest.json"
    manifest = load_json(path)
    if manifest.get("protocol_version") != "round2a-v1":
        raise PilotError("unexpected Round-2 protocol version")
    if manifest.get("formal_observations_before_freeze") != 0:
        raise PilotError("manifest does not declare zero pre-freeze observations")
    bindings = {row["path"]: row["sha256"] for row in manifest.get("source_bindings", [])}
    if bindings != SOURCE_HASHES:
        raise PilotError("source bindings differ from frozen Round-1 hashes")
    seen: set[str] = set()
    for entry in manifest.get("files", []):
        relative = entry.get("path")
        if relative in seen or relative == "round2/PROJECT_OWNER_AUTHORIZATION.json":
            raise PilotError("invalid or duplicate preparation-manifest path")
        seen.add(relative)
        target = ROOT / relative
        if not target.is_file() or sha256_bytes(target.read_bytes()) != entry.get("sha256"):
            raise PilotError(f"preparation file hash mismatch: {relative}")
    model = manifest.get("model_identity", {})
    if (
        model.get("tag") != MODEL_TAG
        or model.get("manifest_sha256") != MODEL_MANIFEST_SHA256
        or model.get("blob_sha256") != MODEL_BLOB_SHA256
    ):
        raise PilotError("manifest model identity mismatch")


def main() -> int:
    try:
        run_round1_validator()
        validate_sources()
        load_order()
        validate_calibration()
        for path in (ROUND2 / "schemas").glob("*.json"):
            load_json(path)
        validate_manifest()
    except (PilotError, OSError, json.JSONDecodeError) as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        return 1
    print("PASS: Round 2A preparation is internally consistent; no model request was made")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
