"""Shared fail-closed helpers for the Round 2A direct replication."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from pilot_common import (
    DECISIONS,
    PilotError,
    canonical_json,
    load_json,
    load_jsonl,
    parse_rfc3339,
    render_user_prompt,
    sha256_bytes,
    sha256_text,
    utc_now,
    utc_text,
    validate_model_response,
    write_json_exclusive,
    write_json_exclusive_or_verify,
    write_jsonl_atomic,
)

ROOT = Path(__file__).resolve().parents[1]
ROUND2 = ROOT / "round2"
RESULTS = ROOT / "results" / "round2_ministral3b"
MODEL_TAG = "ministral-3:3b"
MODEL_MANIFEST_SHA256 = "f04aa1c738f64e13c625b82ae92504fc0260fa6723b509ed1ece0fa188179b1d"
MODEL_BLOB_SHA256 = "910e4bf4e2338f181e99796d7452404e85c1b6bbbf8cd0bb094672cf9b6f2f22"
OLLAMA_VERSION = "0.33.2"
SETTINGS = {
    "temperature": 0,
    "seed": 42,
    "num_ctx": 4096,
    "num_predict": 512,
    "tools_enabled": False,
}
SOURCE_HASHES = {
    "data/pilot_cases.jsonl": "be296ce47e854ed69a02cc140eab41441d5f6536b12dc348c4a53a9fb474fabe",
    "data/gold_records.jsonl": "644101ce2e81d73025e7d490f11a4c27c18c099af78dd92052989ec84daee190",
    "data/execution_order.json": "98e11430f543ba0bd01f6a7536e9cae4240d378ac8fde71f8b020af2e76d4037",
    "prompts/arm_a_system.txt": "bf7b3b8e897db7a38eb3174085398dc74b0468325e10381bfc75bb916876c979",
    "prompts/arm_b_system.txt": "3ad49c8418833702ae8b7c3b2d56a53ab44da8388c7be5483990ed180d375f81",
    "prompts/user_template.txt": "c54e5774e2da82084a497e971b4e7df48d3621eec7f712ae7c8ccaaa5ae060ab",
    "docs/SCORING_RUBRIC.md": "385bb36679e7b5702ed2119864de922c31fb7723e19ec4781496e40c413fa306",
}
AUTHORIZATION_STATEMENT = (
    "I, David / Tai Wai Lee, Project Owner, explicitly authorize the 24 formal "
    "Round 2A observations using ministral-3:3b under the frozen Round-2 protocol "
    "manifest identified by authorized_protocol_manifest_sha256. I authorize the "
    "subsequent blinded David-calibrated AI surrogate rating procedure. I do not "
    "authorize changes to frozen Round-1 evidence, selective reruns, publication, "
    "push, tag, or release."
)
API_ROOT = "http://127.0.0.1:11434"


def http_json(path: str, method: str = "GET", payload: dict[str, Any] | None = None) -> tuple[str, Any]:
    data = None
    headers: dict[str, str] = {}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(API_ROOT + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            raw = response.read().decode("utf-8", errors="strict")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, UnicodeError) as exc:
        raise PilotError(f"Ollama transport failed: {exc}") from exc
    try:
        return raw, json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PilotError("Ollama returned non-JSON API body") from exc


def run_round1_validator() -> None:
    completed = subprocess.run(
        [sys.executable, "-B", str(ROOT / "scripts" / "validate_protocol.py")],
        cwd=ROOT, text=True, capture_output=True, timeout=60, check=False,
    )
    if completed.returncode != 0:
        raise PilotError((completed.stderr or completed.stdout).strip())


def validate_sources() -> None:
    for relative, expected in SOURCE_HASHES.items():
        path = ROOT / relative
        if not path.is_file() or sha256_bytes(path.read_bytes()) != expected:
            raise PilotError(f"frozen source mismatch: {relative}")


def load_order() -> list[dict[str, Any]]:
    order = load_json(ROOT / "data" / "execution_order.json")
    runs = order.get("runs")
    if order.get("protocol_version") != "v0.1.0" or not isinstance(runs, list) or len(runs) != 24:
        raise PilotError("frozen execution order is invalid")
    if [row.get("sequence") for row in runs] != list(range(1, 25)):
        raise PilotError("frozen sequence is not exactly 1 through 24")
    return runs


def run_id(sequence: int) -> str:
    return f"R2A-RUN-{sequence:03d}"


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
    obj = api_response if isinstance(api_response, dict) else {}
    message = obj.get("message")
    raw = message.get("content") if isinstance(message, dict) else ""
    if not isinstance(raw, str):
        raw = ""
    if not raw.strip():
        return raw, "NO_OUTPUT", None
    status, parsed = validate_model_response(raw)
    return raw, status, parsed


def protocol_manifest_sha256() -> str:
    path = ROUND2 / "round2_protocol_manifest.json"
    if not path.is_file():
        raise PilotError("Round-2 protocol manifest is missing")
    return sha256_bytes(path.read_bytes())


def validate_authorization(path: Path) -> tuple[dict[str, Any], Any]:
    value = load_json(path)
    required = {
        "authorization_type", "project_owner", "authorized_protocol_manifest_sha256",
        "statement", "authorized_at",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise PilotError("Project Owner authorization keys are invalid")
    if value["authorization_type"] != "ROUND2A_FORMAL_EXECUTION":
        raise PilotError("authorization type is not ROUND2A_FORMAL_EXECUTION")
    if value["project_owner"] != "David / Tai Wai Lee":
        raise PilotError("Project Owner identity mismatch")
    if value["authorized_protocol_manifest_sha256"] != protocol_manifest_sha256():
        raise PilotError("authorization does not bind the current Round-2 manifest")
    if value["statement"] != AUTHORIZATION_STATEMENT:
        raise PilotError("authorization statement is not exact")
    return value, parse_rfc3339(value["authorized_at"])


def validate_local_environment() -> dict[str, Any]:
    completed = subprocess.run(
        ["ollama", "--version"], text=True, capture_output=True, timeout=30, check=False
    )
    version_text = (completed.stdout + completed.stderr).strip()
    if completed.returncode or f"ollama version is {OLLAMA_VERSION}" not in version_text:
        raise PilotError(f"expected Ollama {OLLAMA_VERSION}; received: {version_text}")
    show = subprocess.run(
        ["ollama", "show", MODEL_TAG, "--modelfile"],
        text=True, capture_output=True, timeout=60, check=False,
    )
    match = re.search(r"sha256-([0-9a-f]{64})", show.stdout)
    if show.returncode or not match or match.group(1) != MODEL_BLOB_SHA256:
        raise PilotError("Ministral model blob mismatch")
    _vr, version = http_json("/api/version")
    _tr, tags = http_json("/api/tags")
    entries = [row for row in tags.get("models", []) if row.get("name") == MODEL_TAG]
    if version.get("version") != OLLAMA_VERSION or len(entries) != 1:
        raise PilotError("Ollama API version or model tag mismatch")
    entry = entries[0]
    details = entry.get("details", {})
    if entry.get("digest") != MODEL_MANIFEST_SHA256:
        raise PilotError("Ministral manifest digest mismatch")
    if details.get("quantization_level") != "Q4_K_M" or details.get("family") != "mistral3":
        raise PilotError("Ministral family or quantization mismatch")
    return {
        "ollama_cli_output": version_text,
        "ollama_api_version": version["version"],
        "model_tag": MODEL_TAG,
        "model_manifest_sha256": MODEL_MANIFEST_SHA256,
        "model_blob_sha256": MODEL_BLOB_SHA256,
        "details": details,
    }
