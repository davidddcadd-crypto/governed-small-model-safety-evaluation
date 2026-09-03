"""Shared fail-closed helpers for the Round 5A Granite 4 replication."""

from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from pilot_common import (
    PilotError, canonical_json, load_json, load_jsonl, parse_rfc3339,
    render_user_prompt, sha256_bytes, sha256_text, utc_now, utc_text,
    validate_model_response, write_json_exclusive, write_json_exclusive_or_verify,
    write_jsonl_atomic,
)

ROOT = Path(__file__).resolve().parents[1]
ROUND5 = ROOT / "round5"
RESULTS = ROOT / "results" / "round5_granite4_3b"
MODEL_TAG = "granite4:3b"
MODEL_MANIFEST_SHA256 = "89962fcc75239ac434cdebceb6b7e0669397f92eaef9c487774b718bc36a3e5f"
MODEL_BLOB_SHA256 = "6c02683809a8dc4eb05c78d44bc63bcd707703b078998fa58829c858ab337bb0"
MODEL_BLOB_SIZE = 2_099_502_528
OLLAMA_VERSION = "0.33.2"
CODEX_CLI_VERSION = "0.152.1"
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
    "schemas/model_response.schema.json": "a304c101ae7ee5477b28efcaae3476102a290a45f35efadf246e46c1127d7cdb",
    "docs/SCORING_RUBRIC.md": "385bb36679e7b5702ed2119864de922c31fb7723e19ec4781496e40c413fa306",
    "round2/DAVID_RATER_CALIBRATION_V1.md": "bdceb675e9f6af3e288cea29564891c5769cf23e70ea43ad66ad2aa926f33228",
}
BASELINE_HASHES = {
    "results/RESULT_MANIFEST.json": "49e6726a849a71842564fc33dcde328680683ae85981ebebe7261c0f9f83da97",
    "round2/round2_protocol_manifest.json": "b77c6f3282d026df2f23b8db5b64a61def325d8e4395e406e05b377df01d545f",
    "results/round2_ministral3b/RESULT_MANIFEST.json": "ae8e0ff43ae9f57245310b744741a87ce59040f76664a5ab2b59fc36cdf9c7c3",
    "results/round2_ministral3b/PUBLICATION_MANIFEST.json": "bfaba8a2c4543a64231d8dc48c43d70c9b355acfe9214e571af7c65d7b8af117",
    "round3/round3_protocol_manifest.json": "399aafe74784d85e06b7fb0cfb4640f417de4a39545dc83bdb68e189de8c90dc",
    "results/round3_granite41_3b/RESULT_MANIFEST.json": "c9d2dc906f0450f3c5eae8d5ce057a894bb2b3d144474d513bef18743b1b8ccd",
    "results/round3_granite41_3b/PUBLICATION_MANIFEST.json": "22b2ba694ac7b6207c367a942d73b81d48bc99d202fff03a2a04f3fedc9e45c4",
    "round4/round4_protocol_manifest_v3.json": "37fd588a4103b39c267978b845843ce85da067c078be94811582a67b3fad6ba8",
    "results/round4_llama32_3b/RESULT_MANIFEST.json": "b7c00219ce87ad8bae5cdf5d599b005b5928f7d1bc05e622aa95adeb254a7033",
    "results/round4_llama32_3b/PUBLICATION_MANIFEST.json": "db7bea53d57e8fbafe7e5f50cb41c7de33840a834cdb9ce345b7a61647225ad1",
}
PUBLIC_BASELINE_COMMIT = "dd0ca6afdf3e255f45a8c4d5f3596498d55ca2f0"
CHECKPOINT_PATH = ROOT / "results" / "ratings_primary.partial.jsonl"
CHECKPOINT_SHA256 = "114e940605fc0cdca16969e3abd6c8600ca1d2967bbe464d38619c769486265f"
CHECKPOINT_SIZE = 31_022
MODEL_LAYERS = {
    "config": ("ba32b08db168051148743c54d446b8b0d82d112ced661edc21b070d3038f6ff1", 417),
    "model": (MODEL_BLOB_SHA256, MODEL_BLOB_SIZE),
    "template": ("0f6ec9740c765c3fb0dc38fe25f4d283c3bc1ede32b76f81c3a971daef20f76c", 7_082),
    "license": ("cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30", 11_358),
}
FORMAL_AUTHORIZATION_STATEMENT = (
    "I, David / Tai Wai Lee, Project Owner, explicitly authorize exactly 24 formal "
    "Round 5A observations using granite4:3b (Ollama manifest SHA-256 "
    "89962fcc75239ac434cdebceb6b7e0669397f92eaef9c487774b718bc36a3e5f, "
    "model blob SHA-256 6c02683809a8dc4eb05c78d44bc63bcd707703b078998fa58829c858ab337bb0) "
    "under the frozen Round-5 protocol manifest identified by "
    "authorized_protocol_manifest_sha256. I authorize no surrogate-rating "
    "transmission, formal rating, change to frozen Round-1, Round-2, Round-3, or "
    "Round-4 evidence, selective rerun, publication, commit, push, tag, or release."
)
API_ROOT = "http://127.0.0.1:11434"


def http_json(path: str, method: str = "GET", payload: dict[str, Any] | None = None) -> tuple[str, Any]:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {} if payload is None else {"Content-Type": "application/json"}
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


def validate_sources() -> None:
    for relative, expected in {**SOURCE_HASHES, **BASELINE_HASHES}.items():
        path = ROOT / relative
        if not path.is_file() or sha256_bytes(path.read_bytes()) != expected:
            raise PilotError(f"frozen source mismatch: {relative}")
    if CHECKPOINT_PATH.exists() and (
        not CHECKPOINT_PATH.is_file()
        or CHECKPOINT_PATH.stat().st_size != CHECKPOINT_SIZE
        or sha256_bytes(CHECKPOINT_PATH.read_bytes()) != CHECKPOINT_SHA256
    ):
        raise PilotError("excluded local checkpoint changed")


def load_order() -> list[dict[str, Any]]:
    source = load_json(ROOT / "data" / "execution_order.json")
    frozen = load_json(ROUND5 / "RUN_ORDER.json")
    rows = frozen.get("runs")
    if frozen.get("formal_run_count") != 24 or not isinstance(rows, list) or len(rows) != 24:
        raise PilotError("Round-5 run order is invalid")
    expected = source.get("runs")
    normalized = [{k: row[k] for k in ("sequence", "arm", "case_id")} for row in rows]
    if normalized != expected:
        raise PilotError("Round-5 order differs from the frozen source order")
    for sequence, row in enumerate(rows, start=1):
        if row.get("run_id") != f"R5A-RUN-{sequence:03d}":
            raise PilotError("Round-5 run IDs are not exact and contiguous")
    if {arm: sum(row["arm"] == arm for row in rows) for arm in ("A", "B")} != {"A": 12, "B": 12}:
        raise PilotError("Round-5 arm counts are not 12/12")
    return rows


def build_formal_request(system_prompt: str, user_prompt: str) -> dict[str, Any]:
    return {
        "model": MODEL_TAG,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "keep_alive": "10m",
        "options": {key: SETTINGS[key] for key in ("temperature", "seed", "num_ctx", "num_predict")},
    }


def extract_formal_output(api_response: Any) -> tuple[str, str, dict[str, Any] | None]:
    obj = api_response if isinstance(api_response, dict) else {}
    message = obj.get("message")
    raw = message.get("content") if isinstance(message, dict) else ""
    raw = raw if isinstance(raw, str) else ""
    if not raw.strip():
        return raw, "NO_OUTPUT", None
    status, parsed = validate_model_response(raw)
    return raw, status, parsed


def protocol_manifest_sha256() -> str:
    path = ROUND5 / "round5_protocol_manifest_v3.json"
    if not path.is_file():
        raise PilotError("Round-5 protocol manifest is missing")
    return sha256_bytes(path.read_bytes())


def validate_formal_authorization(path: Path) -> tuple[dict[str, Any], Any]:
    value = load_json(path)
    required = {"authorization_type", "project_owner", "authorized_protocol_manifest_sha256", "statement", "authorized_at"}
    if not isinstance(value, dict) or set(value) != required:
        raise PilotError("Project Owner authorization keys are invalid")
    if value["authorization_type"] != "ROUND5A_FORMAL_EXECUTION":
        raise PilotError("authorization type is not ROUND5A_FORMAL_EXECUTION")
    if value["project_owner"] != "David / Tai Wai Lee":
        raise PilotError("Project Owner identity mismatch")
    if value["authorized_protocol_manifest_sha256"] != protocol_manifest_sha256():
        raise PilotError("authorization does not bind the frozen Round-5 manifest")
    if value["statement"] != FORMAL_AUTHORIZATION_STATEMENT:
        raise PilotError("authorization statement is not exact")
    return value, parse_rfc3339(value["authorized_at"])


def validate_local_environment() -> dict[str, Any]:
    completed = subprocess.run(["ollama", "--version"], text=True, capture_output=True, timeout=30, check=False)
    cli = (completed.stdout + completed.stderr).strip()
    if completed.returncode or f"ollama version is {OLLAMA_VERSION}" not in cli:
        raise PilotError(f"expected Ollama {OLLAMA_VERSION}; received: {cli}")
    _vr, version = http_json("/api/version")
    _tr, tags = http_json("/api/tags")
    entries = [row for row in tags.get("models", []) if row.get("name") == MODEL_TAG]
    if version.get("version") != OLLAMA_VERSION or len(entries) != 1:
        raise PilotError("Ollama API version or granite4:3b tag mismatch")
    entry = entries[0]
    details = entry.get("details", {})
    if entry.get("digest") != MODEL_MANIFEST_SHA256:
        raise PilotError("Granite 4 manifest digest mismatch")
    if details.get("family") != "granite" or details.get("parameter_size") != "3.4B" or details.get("quantization_level") != "Q4_K_M":
        raise PilotError("Granite 4 family, size, or quantization mismatch")
    if details.get("context_length") != 131072 or details.get("embedding_length") != 2560:
        raise PilotError("Granite 4 context or embedding length mismatch")
    manifest = Path.home() / ".ollama/models/manifests/registry.ollama.ai/library/granite4/3b"
    if not manifest.is_file() or manifest.stat().st_size != 829 or sha256_bytes(manifest.read_bytes()) != MODEL_MANIFEST_SHA256:
        raise PilotError("local Granite 4 manifest bytes mismatch")
    blobs = Path.home() / ".ollama/models/blobs"
    for label, (digest, size) in MODEL_LAYERS.items():
        layer = blobs / f"sha256-{digest}"
        if not layer.is_file() or layer.stat().st_size != size or sha256_bytes(layer.read_bytes()) != digest:
            raise PilotError(f"Granite 4 {label} layer mismatch")
    return {
        "ollama_cli_output": cli,
        "ollama_api_version": version["version"],
        "model_tag": MODEL_TAG,
        "model_manifest_sha256": MODEL_MANIFEST_SHA256,
        "model_blob_sha256": MODEL_BLOB_SHA256,
        "model_blob_size_bytes": MODEL_BLOB_SIZE,
        "details": details,
        "layers": {label: {"sha256": digest, "size_bytes": size} for label, (digest, size) in MODEL_LAYERS.items()},
    }


def formal_observation_count() -> int:
    return len(list((RESULTS / "raw_runs").glob("R5A-RUN-*.json"))) if (RESULTS / "raw_runs").exists() else 0
