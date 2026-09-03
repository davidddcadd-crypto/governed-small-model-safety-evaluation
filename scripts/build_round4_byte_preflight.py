#!/usr/bin/env python3
"""Prove Round-4 CRLF evidence path classes survive a clean Git checkout."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from round4_common import ROOT, ROUND4, PilotError

PATHS = (
    "round4/preflight/stage1_schema_combined.log",
    "round4/preflight/stage1_schema_events.jsonl",
    "round4/preflight/stage2_schema_combined.log",
    "round4/preflight/stage2_schema_events.jsonl",
    "round4/preflight/byte_preservation_probe.log",
    "results/round4_llama32_3b/stage1_combined.log",
    "results/round4_llama32_3b/stage1_events.jsonl",
    "results/round4_llama32_3b/stage2_combined.log",
    "results/round4_llama32_3b/stage2_events.jsonl",
)
PAYLOAD = b"ROUND4_BYTE_PRESERVATION_PROBE\r\nline=2\r\n"


def _run(command: list[str], cwd: Path) -> str:
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=60, check=False)
    if completed.returncode:
        raise PilotError(f"command failed: {command}: {completed.stderr.strip()}")
    return completed.stdout.strip()


def main() -> int:
    try:
        probe = ROUND4 / "preflight" / "byte_preservation_probe.log"
        record = ROUND4 / "preflight" / "BYTE_PRESERVATION_PREFLIGHT.json"
        if probe.exists() or record.exists():
            raise PilotError("refusing to overwrite byte-preservation preflight")
        attrs = (ROOT / ".gitattributes").read_bytes()
        with tempfile.TemporaryDirectory(prefix="round4_git_bytes_") as tmp:
            repo = Path(tmp) / "repo"
            checkout = Path(tmp) / "checkout"
            repo.mkdir()
            checkout.mkdir()
            (repo / ".gitattributes").write_bytes(attrs)
            for relative in PATHS:
                path = repo / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(PAYLOAD)
            _run(["git", "init", "--quiet"], repo)
            _run(["git", "config", "user.name", "Round4 Byte Preflight"], repo)
            _run(["git", "config", "user.email", "round4-preflight.invalid"], repo)
            _run(["git", "add", ".gitattributes", *PATHS], repo)
            _run(["git", "checkout-index", "-a", f"--prefix={checkout}{Path('/')}"] , repo)
            rows = []
            for relative in PATHS:
                source = (repo / relative).read_bytes()
                restored = (checkout / relative).read_bytes()
                attr = _run(["git", "check-attr", "text", "--", relative], repo)
                rows.append({
                    "path": relative,
                    "attribute": attr,
                    "input_size_bytes": len(source),
                    "checkout_size_bytes": len(restored),
                    "input_sha256": hashlib.sha256(source).hexdigest(),
                    "checkout_sha256": hashlib.sha256(restored).hexdigest(),
                    "exact_match": source == restored,
                })
            if not all(row["exact_match"] and row["attribute"].endswith("text: unset") for row in rows):
                raise PilotError("one or more Round-4 path classes changed bytes")
        probe.parent.mkdir(parents=True, exist_ok=True)
        with probe.open("xb") as handle:
            handle.write(PAYLOAD)
        value = {
            "record_type": "ROUND4A_EXCLUDED_CLEAN_CHECKOUT_BYTE_PRESERVATION_PREFLIGHT",
            "excluded_from_formal_observations": True,
            "synthetic_content_only": True,
            "source_gitattributes_sha256": hashlib.sha256(attrs).hexdigest(),
            "probe_payload_sha256": hashlib.sha256(PAYLOAD).hexdigest(),
            "probe_payload_size_bytes": len(PAYLOAD),
            "path_classes": rows,
            "result": "PASS_EXACT_BYTES_AFTER_CLEAN_CHECKOUT",
        }
        with record.open("xb") as handle:
            handle.write((json.dumps(value, indent=2) + "\n").encode("utf-8"))
        print(f"PASS: exact CRLF bytes preserved for {len(PATHS)} Round-4 path classes")
        return 0
    except (PilotError, OSError, subprocess.SubprocessError) as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
