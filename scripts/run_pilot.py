#!/usr/bin/env python3
"""Fail-closed formal runner for the frozen 24-run local Ollama pilot."""

from __future__ import annotations

import argparse
import json
import platform
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from pilot_common import (
    MODEL_BLOB_SHA256,
    MODEL_TAG,
    OLLAMA_VERSION,
    RESULTS,
    ROOT,
    SETTINGS,
    PilotError,
    format_error,
    canonical_json,
    load_cases_by_id,
    load_json,
    render_user_prompt,
    run_protocol_validator,
    sha256_text,
    sha256_bytes,
    utc_now,
    utc_text,
    validate_model_response,
    validate_release_receipt,
    write_json_exclusive,
    write_json_exclusive_or_verify,
    write_jsonl_atomic,
)


API_ROOT = "http://127.0.0.1:11434"
API_TIMEOUT_SECONDS = 300


class TransportFailure(PilotError):
    def __init__(self, message: str, response_body: str | None = None):
        super().__init__(message)
        self.response_body = response_body


def http_request(path: str, method: str = "GET", payload: dict[str, Any] | None = None) -> tuple[str, Any]:
    data = None
    headers: dict[str, str] = {}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(API_ROOT + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=API_TIMEOUT_SECONDS) as response:
            raw = response.read().decode("utf-8", errors="strict")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise TransportFailure(f"Ollama HTTP {exc.code}", body) from exc
    except (urllib.error.URLError, TimeoutError, UnicodeError) as exc:
        raise TransportFailure(f"Ollama transport failed: {exc}") from exc
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise TransportFailure("Ollama returned non-JSON API body", raw) from exc
    return raw, parsed


def validate_local_environment() -> dict[str, Any]:
    try:
        version_cmd = subprocess.run(
            ["ollama", "--version"], text=True, capture_output=True, timeout=30, check=False
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise PilotError(f"cannot execute ollama CLI: {exc}") from exc
    version_output = (version_cmd.stdout + version_cmd.stderr).strip()
    if version_cmd.returncode != 0 or f"ollama version is {OLLAMA_VERSION}" not in version_output:
        raise PilotError(f"expected Ollama {OLLAMA_VERSION}; received: {version_output}")

    show_cmd = subprocess.run(
        ["ollama", "show", MODEL_TAG, "--modelfile"],
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    if show_cmd.returncode != 0:
        raise PilotError(f"cannot inspect frozen model: {(show_cmd.stderr or show_cmd.stdout).strip()}")
    digest_match = re.search(r"sha256-([0-9a-f]{64})", show_cmd.stdout)
    if not digest_match or digest_match.group(1) != MODEL_BLOB_SHA256:
        actual = digest_match.group(1) if digest_match else "NOT_FOUND"
        raise PilotError(f"model blob mismatch; expected {MODEL_BLOB_SHA256}, got {actual}")

    _version_raw, version_api = http_request("/api/version")
    if version_api.get("version") != OLLAMA_VERSION:
        raise PilotError(f"Ollama API version mismatch: {version_api.get('version')}")
    _tags_raw, tags_api = http_request("/api/tags")
    names = {item.get("name") for item in tags_api.get("models", []) if isinstance(item, dict)}
    if MODEL_TAG not in names:
        raise PilotError(f"frozen model tag is absent from Ollama: {MODEL_TAG}")

    return {
        "ollama_cli_output": version_output,
        "ollama_api_version": version_api.get("version"),
        "model_tag": MODEL_TAG,
        "model_blob_sha256": MODEL_BLOB_SHA256,
    }


def command_evidence(command: list[str], timeout: int = 60) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command, text=True, capture_output=True, timeout=timeout, check=False
        )
        return {
            "command": command,
            "available": True,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    except (OSError, subprocess.SubprocessError) as exc:
        return {
            "command": command,
            "available": False,
            "returncode": None,
            "stdout": "",
            "stderr": format_error(exc),
        }


def ensure_execution_environment(
    receipt: dict[str, Any], validated_environment: dict[str, Any]
) -> str:
    path = RESULTS / "execution_environment.json"
    if not path.exists():
        powershell_inventory = (
            "$cpu=Get-CimInstance Win32_Processor | Select-Object Name;"
            "$system=Get-CimInstance Win32_ComputerSystem | Select-Object TotalPhysicalMemory;"
            "$os=Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion' | "
            "Select-Object ProductName,DisplayVersion,EditionID,CurrentBuild,UBR;"
            "[pscustomobject]@{cpu=$cpu;system=$system;os=$os} | ConvertTo-Json -Depth 4 -Compress"
        )
        snapshot = {
            "captured_at": utc_text(),
            "release_receipt": receipt,
            "validated_model_runtime": validated_environment,
            "python": sys.version,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "command_evidence": {
                "windows_inventory": command_evidence(
                    ["powershell", "-NoProfile", "-Command", powershell_inventory]
                ),
                "nvidia_smi": command_evidence(["nvidia-smi"]),
                "ollama_ps_after_warmup": command_evidence(["ollama", "ps"]),
                "ollama_show": command_evidence(["ollama", "show", MODEL_TAG]),
            },
        }
        write_json_exclusive(path, snapshot)
    return sha256_bytes(path.read_bytes())


def build_formal_request(system_prompt: str, user_prompt: str) -> dict[str, Any]:
    return {
        "model": MODEL_TAG,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "keep_alive": "10m",
        "options": {
            "temperature": SETTINGS["temperature"],
            "seed": SETTINGS["seed"],
            "num_ctx": SETTINGS["num_ctx"],
            "num_predict": SETTINGS["num_predict"],
        },
    }


def extract_formal_output(api_response: Any) -> tuple[str, str, dict[str, Any] | None]:
    api_object = api_response if isinstance(api_response, dict) else {}
    message = api_object.get("message")
    raw_response = message.get("content") if isinstance(message, dict) else None
    if not isinstance(raw_response, str):
        raw_response = ""
    if not raw_response.strip():
        return raw_response, "NO_OUTPUT", None
    format_status, parsed_response = validate_model_response(raw_response)
    return raw_response, format_status, parsed_response


def run_warmup() -> None:
    warmup_path = RESULTS / "warmup.json"
    if warmup_path.exists():
        return
    request = {
        "model": MODEL_TAG,
        "messages": [
            {"role": "system", "content": "Return only the word OK."},
            {"role": "user", "content": "Neutral model-loading warm-up. Do not analyze a pilot case."},
        ],
        "stream": False,
        "keep_alive": "10m",
        "options": {
            "temperature": 0,
            "seed": 42,
            "num_ctx": 4096,
            "num_predict": 8,
        },
    }
    started = utc_text()
    raw_body, parsed = http_request("/api/chat", method="POST", payload=request)
    completed = utc_text()
    write_json_exclusive(
        warmup_path,
        {
            "excluded_from_formal_metrics": True,
            "started_at": started,
            "completed_at": completed,
            "request": request,
            "raw_api_body": raw_body,
            "api_response": parsed,
        },
    )


def load_order() -> list[dict[str, Any]]:
    order = load_json(ROOT / "data" / "execution_order.json")
    runs = order.get("runs")
    if order.get("protocol_version") != "v0.1.0" or not isinstance(runs, list) or len(runs) != 24:
        raise PilotError("frozen execution order is invalid")
    return runs


def existing_attempt_count(run_id: str) -> int:
    return len(list((RESULTS / "attempts").glob(f"{run_id}-ATTEMPT-*.json")))


def validate_existing_run(path: Path, expected: dict[str, Any]) -> None:
    actual = load_json(path)
    for key in (
        "run_id", "sequence", "arm", "case_id", "model_tag", "model_blob_sha256",
        "ollama_version", "settings", "system_prompt_sha256", "user_prompt_sha256",
        "request_sha256", "environment_snapshot_sha256",
    ):
        if actual.get(key) != expected.get(key):
            raise PilotError(f"existing immutable run conflicts on {key}: {path}")


def rebuild_consolidated_results() -> list[dict[str, Any]]:
    run_paths = sorted((RESULTS / "raw_runs").glob("RUN-*.json"))
    rows = [load_json(path) for path in run_paths]
    rows.sort(key=lambda row: row["sequence"])
    write_jsonl_atomic(RESULTS / "formal_raw_results.jsonl", rows)
    return rows


def execute_formal_runs(
    resume: bool,
    released_at,
    receipt: dict[str, Any],
    validated_environment: dict[str, Any],
) -> None:
    cases = load_cases_by_id()
    order = load_order()
    existing_paths = sorted((RESULTS / "raw_runs").glob("RUN-*.json"))
    if existing_paths and not resume:
        raise PilotError("formal run records already exist; use --resume to continue without overwriting")

    run_warmup()
    environment_snapshot_sha256 = ensure_execution_environment(receipt, validated_environment)
    for spec in order:
        sequence = spec["sequence"]
        run_id = f"RUN-{sequence:03d}"
        case = cases[spec["case_id"]]
        arm = spec["arm"]
        system_path = ROOT / "prompts" / ("arm_a_system.txt" if arm == "A" else "arm_b_system.txt")
        system_prompt = system_path.read_text(encoding="utf-8")
        user_prompt = render_user_prompt(case)
        request_payload = build_formal_request(system_prompt, user_prompt)
        request_sha256 = sha256_text(canonical_json(request_payload))
        expected_identity = {
            "run_id": run_id,
            "sequence": sequence,
            "arm": arm,
            "case_id": case["case_id"],
            "model_tag": MODEL_TAG,
            "model_blob_sha256": MODEL_BLOB_SHA256,
            "ollama_version": OLLAMA_VERSION,
            "settings": SETTINGS,
            "system_prompt_sha256": sha256_text(system_prompt),
            "user_prompt_sha256": sha256_text(user_prompt),
            "request_sha256": request_sha256,
            "environment_snapshot_sha256": environment_snapshot_sha256,
        }
        run_path = RESULTS / "raw_runs" / f"{run_id}.json"
        if run_path.exists():
            if not resume:
                raise PilotError(f"refusing to overwrite existing formal run: {run_id}")
            validate_existing_run(run_path, expected_identity)
            continue

        request_path = RESULTS / "requests" / f"{run_id}.request.json"
        write_json_exclusive_or_verify(request_path, request_payload)
        attempt_number = existing_attempt_count(run_id) + 1
        attempt_id = f"{run_id}-ATTEMPT-{attempt_number:02d}"
        started_dt = utc_now()
        if started_dt <= released_at:
            raise PilotError(f"system clock places {run_id} before or at public protocol freeze")
        started_at = utc_text(started_dt)
        wall_started_ns = time.perf_counter_ns()
        try:
            raw_api_body, api_response = http_request("/api/chat", method="POST", payload=request_payload)
        except TransportFailure as exc:
            client_wall_duration_ns = time.perf_counter_ns() - wall_started_ns
            write_json_exclusive(
                RESULTS / "attempts" / f"{attempt_id}.json",
                {
                    "attempt_id": attempt_id,
                    "run_id": run_id,
                    "status": "TRANSPORT_FAIL",
                    "started_at": started_at,
                    "completed_at": utc_text(),
                    "client_wall_duration_ns": client_wall_duration_ns,
                    "error": format_error(exc),
                    "response_body": exc.response_body,
                },
            )
            raise PilotError(
                f"transport failure preserved for {run_id}; correct the transport issue and use --resume"
            ) from exc

        client_wall_duration_ns = time.perf_counter_ns() - wall_started_ns
        completed_at = utc_text()
        raw_api_body_sha256 = sha256_text(raw_api_body)
        write_json_exclusive(
            RESULTS / "attempts" / f"{attempt_id}.json",
            {
                "attempt_id": attempt_id,
                "run_id": run_id,
                "status": "OK",
                "started_at": started_at,
                "completed_at": completed_at,
                "client_wall_duration_ns": client_wall_duration_ns,
                "request_sha256": request_sha256,
                "raw_api_body_sha256": raw_api_body_sha256,
                "raw_api_body": raw_api_body,
                "api_response": api_response,
            },
        )
        api_object = api_response if isinstance(api_response, dict) else {}
        raw_response, format_status, parsed_response = extract_formal_output(api_response)
        run_record = {
            **expected_identity,
            "attempt_id": attempt_id,
            "raw_api_body_sha256": raw_api_body_sha256,
            "started_at": started_at,
            "completed_at": completed_at,
            "raw_response": raw_response,
            "parsed_response": parsed_response,
            "transport_status": "TRANSPORT_RETRY" if attempt_number > 1 else "OK",
            "format_status": format_status,
            "timing": {
                "client_wall_duration_ns": client_wall_duration_ns,
                "total_duration_ns": api_object.get("total_duration"),
                "load_duration_ns": api_object.get("load_duration"),
                "prompt_eval_duration_ns": api_object.get("prompt_eval_duration"),
                "eval_duration_ns": api_object.get("eval_duration"),
                "prompt_eval_count": api_object.get("prompt_eval_count"),
                "eval_count": api_object.get("eval_count"),
            },
            "api_completion": {
                "model": api_object.get("model"),
                "created_at": api_object.get("created_at"),
                "done": api_object.get("done"),
                "done_reason": api_object.get("done_reason"),
            },
            "error": None,
        }
        write_json_exclusive(run_path, run_record)
        rebuild_consolidated_results()
        print(f"completed {run_id}: arm={arm} case={case['case_id']} format={format_status}")

    rows = rebuild_consolidated_results()
    if len(rows) != 24:
        raise PilotError(f"formal run set incomplete after execution: {len(rows)} / 24")
    print("PASS: all 24 frozen formal runs are preserved")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="validate all gates without model generation")
    parser.add_argument("--resume", action="store_true", help="continue missing sequences without overwriting")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        run_protocol_validator()
        receipt, released_at = validate_release_receipt()
        environment = validate_local_environment()
        if args.dry_run:
            print("PASS: dry-run gates passed; no model request was made")
            print(json.dumps({"release": receipt, "environment": environment}, indent=2))
            return 0
        execute_formal_runs(
            resume=args.resume,
            released_at=released_at,
            receipt=receipt,
            validated_environment=environment,
        )
        return 0
    except PilotError as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
