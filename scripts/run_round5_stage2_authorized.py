#!/usr/bin/env python3
"""Run exactly one owner-authorized Round 5A Stage-2 session resume."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from round5_common import CHECKPOINT_PATH, CHECKPOINT_SHA256, CHECKPOINT_SIZE, RESULTS, ROOT, PilotError, sha256_bytes

SESSION_ID = "01a06754-52d6-77a1-8312-2b637d14f237"
AUTHORIZATION_SHA256 = "81ce67cabb78637dbb04e3b6b9b95aef50cf32266304280b51eac6e6c54961b5"
FROZEN = {
    RESULTS / "STAGE2_TRANSMISSION_AUTHORIZATION.json": AUTHORIZATION_SHA256,
    ROOT / "round5/round5_protocol_manifest_v3.json": "a556679cc276422f250d556f0b512334652b40eb7c35bbe07a45551d4290fd5b",
    RESULTS / "formal_raw_results.jsonl": "11ed3d64f40ca072ba57e744171c528be92cf0db10cba475a093e8d6c8e76ab3",
    RESULTS / "stage1_raw_output.json": "cf249fe6b9886e841b72a9470906aabb353114166121667322d2d1ef992ea0c1",
    RESULTS / "stage2_prompt.txt": "c74f966e8e0b31c5d26eede6941d7c378a2c5d839848a1a367a1fa27a348ec0e",
    RESULTS / "blinded_scoring_packet.jsonl": "9acf1695df901de94e60097b9df6818ed574bbb3bab17d765e197f7dfcd53625",
    ROOT / "round5/schemas/runtime_surrogate_scoring_output.schema.json": "3ad19c65303dd4774458fff146434dfccef960d79e2acfd5d3ae47e1abfb70a1",
    RESULTS / "STAGE2_PREPARATION_CUSTODY.json": "ebd66b9790095319e60e0f59a9e038d9dbcc1990c558445c52d49fae1066bb96",
    RESULTS / "STAGE2_PREPARATION_VALIDATION.json": "9e6e41403f6b136254908f1e9ca994615b9258d9e7766e11771276523c450c50",
}
OUTPUTS = {
    "events": RESULTS / "stage2_events.jsonl",
    "raw": RESULTS / "stage2_raw_output.json",
    "combined": RESULTS / "stage2_combined.log",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def write_exclusive(path: Path, payload: bytes) -> None:
    with path.open("xb") as handle:
        handle.write(payload)


def append_line(payload: bytes) -> bytes:
    return payload if not payload or payload.endswith((b"\n", b"\r")) else payload + b"\n"


def validate_gate() -> None:
    for path, expected in FROZEN.items():
        if not path.is_file() or sha256_bytes(path.read_bytes()) != expected:
            raise PilotError(f"frozen input mismatch: {path.relative_to(ROOT)}")
    if not CHECKPOINT_PATH.is_file() or CHECKPOINT_PATH.stat().st_size != CHECKPOINT_SIZE or sha256_bytes(CHECKPOINT_PATH.read_bytes()) != CHECKPOINT_SHA256:
        raise PilotError("excluded checkpoint mismatch")
    if any(path.exists() for path in OUTPUTS.values()):
        raise PilotError("Stage-2 output already exists; refusing another attempt")


def run_once() -> dict[str, object]:
    validate_gate()
    codex = shutil.which("codex")
    if not codex:
        raise PilotError("Codex CLI not found")
    isolated = Path(tempfile.mkdtemp(prefix="round5-stage2-"))
    schema = isolated / "runtime_surrogate_scoring_output.schema.json"
    shutil.copyfile(ROOT / "round5/schemas/runtime_surrogate_scoring_output.schema.json", schema)
    raw_temp = isolated / "stage2_raw_output.json"
    args = [
        codex, "exec", "resume", "--all", "--model", "gpt-5.6-sol",
        "-c", "model_reasoning_effort=xhigh", "-c", "sandbox_mode=read-only",
        "--strict-config", "--ignore-user-config", "--ignore-rules",
        "--skip-git-repo-check", "--json", "--output-schema", str(schema),
        "--output-last-message", str(raw_temp), SESSION_ID, "-",
    ]
    started_at = utc_now()
    completed = subprocess.run(
        args,
        input=(RESULTS / "stage2_prompt.txt").read_bytes(),
        cwd=isolated,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    completed_at = utc_now()
    write_exclusive(OUTPUTS["events"], completed.stdout)
    if raw_temp.exists():
        write_exclusive(OUTPUTS["raw"], raw_temp.read_bytes())
    combined = (
        f"STAGE2_STARTED_AT={started_at}\n".encode("utf-8")
        + append_line(completed.stderr)
        + append_line(completed.stdout)
        + f"STAGE2_COMPLETED_AT={completed_at}\nSTAGE2_EXIT_CODE={completed.returncode}\n".encode("utf-8")
    )
    write_exclusive(OUTPUTS["combined"], combined)
    result: dict[str, object] = {
        "started_at": started_at,
        "completed_at": completed_at,
        "exit_code": completed.returncode,
        "isolated_directory": isolated.as_posix(),
        "command": "codex exec resume --all --model gpt-5.6-sol -c model_reasoning_effort=xhigh -c sandbox_mode=read-only --strict-config --ignore-user-config --ignore-rules --skip-git-repo-check --json --output-schema runtime_surrogate_scoring_output.schema.json --output-last-message stage2_raw_output.json " + SESSION_ID + " -",
        "events_sha256": sha256_bytes(OUTPUTS["events"].read_bytes()),
        "combined_log_sha256": sha256_bytes(OUTPUTS["combined"].read_bytes()),
    }
    if OUTPUTS["raw"].exists():
        result["raw_output_sha256"] = sha256_bytes(OUTPUTS["raw"].read_bytes())
    if completed.returncode != 0:
        raise PilotError("Stage-2 CLI attempt failed; rejection evidence was preserved and no retry is permitted")
    if not OUTPUTS["raw"].is_file():
        raise PilotError("Stage-2 completed without a raw output artifact")
    value = json.loads(OUTPUTS["raw"].read_text(encoding="utf-8"))
    if value.get("stage") != "GOLD_DISCLOSED_SCORING" or not isinstance(value.get("ratings"), list) or len(value["ratings"]) != 24:
        raise PilotError("Stage-2 output failed the initial 24-record structural gate")
    result["initial_scoring_count"] = 24
    return result


def main() -> int:
    try:
        print(json.dumps(run_once(), ensure_ascii=False, sort_keys=True))
        return 0
    except (PilotError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
