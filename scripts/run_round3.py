#!/usr/bin/env python3
"""Authorization-gated fail-closed runner for 24 Round 3A Granite observations."""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from round3_common import (
    API_ROOT, MODEL_BLOB_SHA256, MODEL_MANIFEST_SHA256, MODEL_TAG,
    OLLAMA_VERSION, RESULTS, ROOT, SETTINGS, PilotError, build_formal_request,
    canonical_json, extract_formal_output, formal_observation_count, load_json,
    load_order, protocol_manifest_sha256, render_user_prompt, sha256_bytes,
    sha256_text, utc_now, utc_text, validate_formal_authorization,
    validate_local_environment, validate_sources, write_json_exclusive,
    write_json_exclusive_or_verify, write_jsonl_atomic,
)


class TransportFailure(PilotError):
    def __init__(self, message: str, response_body: str | None = None):
        super().__init__(message)
        self.response_body = response_body


def formal_http_request(payload: dict[str, Any]) -> tuple[str, Any]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(API_ROOT + "/api/chat", data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            raw = response.read().decode("utf-8", errors="strict")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise TransportFailure(f"Ollama HTTP {exc.code}", body) from exc
    except (urllib.error.URLError, TimeoutError, UnicodeError) as exc:
        raise TransportFailure(f"Ollama transport failed: {exc}") from exc
    try:
        return raw, json.loads(raw)
    except json.JSONDecodeError as exc:
        raise TransportFailure("Ollama returned a non-JSON API body", raw) from exc


def command_evidence(command: list[str], timeout: int = 60) -> dict[str, Any]:
    try:
        completed = subprocess.run(command, text=True, capture_output=True, timeout=timeout, check=False)
        return {"command": command, "available": True, "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}
    except (OSError, subprocess.SubprocessError) as exc:
        return {"command": command, "available": False, "returncode": None, "stdout": "", "stderr": f"{type(exc).__name__}: {exc}"}


def run_warmup() -> None:
    path = RESULTS / "warmup.json"
    if path.exists():
        return
    request = {
        "model": MODEL_TAG,
        "messages": [
            {"role": "system", "content": "Return only the word OK."},
            {"role": "user", "content": "Excluded neutral Round 3 model-loading warm-up."},
        ],
        "stream": False,
        "keep_alive": "10m",
        "options": {"temperature": 0, "seed": 42, "num_ctx": 4096, "num_predict": 8},
    }
    started = utc_text()
    raw, parsed = formal_http_request(request)
    write_json_exclusive(path, {"excluded_from_formal_metrics": True, "started_at": started, "completed_at": utc_text(), "request": request, "raw_api_body": raw, "api_response": parsed})


def ensure_execution_environment(authorization: dict[str, Any], validated: dict[str, Any]) -> str:
    path = RESULTS / "execution_environment.json"
    if path.exists():
        return sha256_bytes(path.read_bytes())
    inventory = "$cpu=Get-CimInstance Win32_Processor|Select-Object Name,NumberOfCores,NumberOfLogicalProcessors;$system=Get-CimInstance Win32_ComputerSystem|Select-Object TotalPhysicalMemory,Manufacturer,Model;[pscustomobject]@{cpu=$cpu;system=$system}|ConvertTo-Json -Depth 4 -Compress"
    value = {
        "captured_at": utc_text(),
        "authorization": authorization,
        "round3_protocol_manifest_sha256": protocol_manifest_sha256(),
        "validated_model_runtime": validated,
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "command_evidence": {
            "windows_inventory": command_evidence(["powershell", "-NoProfile", "-Command", inventory]),
            "nvidia_smi": command_evidence(["nvidia-smi"]),
            "ollama_ps_after_warmup": command_evidence(["ollama", "ps"]),
            "ollama_show": command_evidence(["ollama", "show", MODEL_TAG]),
            "ollama_template": command_evidence(["ollama", "show", MODEL_TAG, "--template"]),
        },
    }
    write_json_exclusive(path, value)
    return sha256_bytes(path.read_bytes())


def attempt_count(identifier: str) -> int:
    return len(list((RESULTS / "attempts").glob(f"{identifier}-ATTEMPT-*.json")))


def rebuild_consolidated() -> list[dict[str, Any]]:
    rows = [load_json(path) for path in sorted((RESULTS / "raw_runs").glob("R3A-RUN-*.json"))]
    rows.sort(key=lambda row: row["sequence"])
    write_jsonl_atomic(RESULTS / "formal_raw_results.jsonl", rows)
    return rows


def validate_existing_run(path: Path, expected: dict[str, Any]) -> None:
    actual = load_json(path)
    for key, value in expected.items():
        if actual.get(key) != value:
            raise PilotError(f"existing immutable run conflicts on {key}: {path.name}")


def execute(resume: bool, auth_path: Path) -> None:
    authorization, authorized_at = validate_formal_authorization(auth_path)
    if authorized_at >= utc_now():
        raise PilotError("authorization timestamp is not in the past")
    RESULTS.mkdir(parents=True, exist_ok=True)
    write_json_exclusive_or_verify(RESULTS / "PROJECT_OWNER_AUTHORIZATION.json", authorization)
    existing = list((RESULTS / "raw_runs").glob("R3A-RUN-*.json"))
    if existing and not resume:
        raise PilotError("formal runs already exist; use --resume without overwriting")
    validated = validate_local_environment()
    run_warmup()
    environment_sha = ensure_execution_environment(authorization, validated)
    cases = {row["case_id"]: row for row in (json.loads(line) for line in (ROOT / "data/pilot_cases.jsonl").read_text(encoding="utf-8").splitlines())}
    for spec in load_order():
        identifier = spec["run_id"]
        case = cases[spec["case_id"]]
        system_path = ROOT / "prompts" / ("arm_a_system.txt" if spec["arm"] == "A" else "arm_b_system.txt")
        system_prompt = system_path.read_text(encoding="utf-8")
        user_prompt = render_user_prompt(case)
        request_payload = build_formal_request(system_prompt, user_prompt)
        request_sha = sha256_text(canonical_json(request_payload))
        expected = {
            "run_id": identifier, "sequence": spec["sequence"], "arm": spec["arm"], "case_id": spec["case_id"],
            "model_tag": MODEL_TAG, "model_manifest_sha256": MODEL_MANIFEST_SHA256,
            "model_blob_sha256": MODEL_BLOB_SHA256, "ollama_version": OLLAMA_VERSION,
            "settings": SETTINGS, "system_prompt_sha256": sha256_text(system_prompt),
            "user_prompt_sha256": sha256_text(user_prompt), "request_sha256": request_sha,
            "environment_snapshot_sha256": environment_sha,
            "round3_protocol_manifest_sha256": protocol_manifest_sha256(),
        }
        run_path = RESULTS / "raw_runs" / f"{identifier}.json"
        if run_path.exists():
            if not resume:
                raise PilotError(f"refusing to overwrite {identifier}")
            validate_existing_run(run_path, expected)
            continue
        write_json_exclusive_or_verify(RESULTS / "requests" / f"{identifier}.request.json", request_payload)
        number = attempt_count(identifier) + 1
        if number > 2:
            raise PilotError(f"bounded retry exhausted for {identifier}")
        attempt_id = f"{identifier}-ATTEMPT-{number:02d}"
        started_dt = utc_now()
        if started_dt <= authorized_at:
            raise PilotError(f"{identifier} clock is not after authorization")
        started_at = utc_text(started_dt)
        wall_start = time.perf_counter_ns()
        try:
            raw_api_body, api_response = formal_http_request(request_payload)
        except TransportFailure as exc:
            write_json_exclusive(RESULTS / "attempts" / f"{attempt_id}.json", {"attempt_id": attempt_id, "run_id": identifier, "status": "TRANSPORT_FAIL", "started_at": started_at, "completed_at": utc_text(), "client_wall_duration_ns": time.perf_counter_ns() - wall_start, "error": f"{type(exc).__name__}: {exc}", "response_body": exc.response_body})
            raise PilotError(f"transport failure preserved for {identifier}; repair transport and use --resume") from exc
        wall_ns = time.perf_counter_ns() - wall_start
        completed_at = utc_text()
        raw_api_sha = sha256_text(raw_api_body)
        write_json_exclusive(RESULTS / "attempts" / f"{attempt_id}.json", {"attempt_id": attempt_id, "run_id": identifier, "status": "OK", "started_at": started_at, "completed_at": completed_at, "client_wall_duration_ns": wall_ns, "request_sha256": request_sha, "raw_api_body_sha256": raw_api_sha, "raw_api_body": raw_api_body, "api_response": api_response})
        raw_response, format_status, parsed_response = extract_formal_output(api_response)
        api = api_response if isinstance(api_response, dict) else {}
        record = {**expected, "attempt_id": attempt_id, "raw_api_body_sha256": raw_api_sha, "started_at": started_at, "completed_at": completed_at, "raw_response": raw_response, "parsed_response": parsed_response, "transport_status": "TRANSPORT_RETRY" if number > 1 else "OK", "format_status": format_status, "timing": {"client_wall_duration_ns": wall_ns, "total_duration_ns": api.get("total_duration"), "load_duration_ns": api.get("load_duration"), "prompt_eval_duration_ns": api.get("prompt_eval_duration"), "eval_duration_ns": api.get("eval_duration"), "prompt_eval_count": api.get("prompt_eval_count"), "eval_count": api.get("eval_count")}, "api_completion": {"model": api.get("model"), "created_at": api.get("created_at"), "done": api.get("done"), "done_reason": api.get("done_reason")}, "error": None}
        write_json_exclusive(run_path, record)
        rebuild_consolidated()
        print(f"completed {identifier}: arm={spec['arm']} case={spec['case_id']} format={format_status}")
    rows = rebuild_consolidated()
    if len(rows) != 24:
        raise PilotError(f"formal run set incomplete: {len(rows)} / 24")
    print("PASS: all 24 Round 3A formal observations are preserved")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    try:
        validate_sources()
        load_order()
        if protocol_manifest_sha256() == "":
            raise PilotError("unreachable empty protocol hash")
        environment = validate_local_environment()
        if args.dry_run:
            if args.authorization or args.resume:
                raise PilotError("dry-run does not accept authorization or resume")
            if formal_observation_count() != 0:
                raise PilotError("dry-run gate requires zero formal observations")
            print("PASS: Round 3A dry-run gates passed; no model request was made")
            print(json.dumps(environment, indent=2, sort_keys=True))
            return 0
        if args.authorization is None:
            raise PilotError("--execute requires --authorization")
        execute(args.resume, args.authorization.resolve())
        return 0
    except (PilotError, OSError) as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
