"""Shared deterministic helpers for the v0.2 pilot scripts."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
MODEL_TAG = "phi4-mini:3.8b"
MODEL_BLOB_SHA256 = "3c168af1dea0a414299c7d9077e100ac763370e5a98b3c53801a958a47f0a5db"
OLLAMA_VERSION = "0.33.2"
SETTINGS = {
    "temperature": 0,
    "seed": 42,
    "num_ctx": 4096,
    "num_predict": 512,
    "tools_enabled": False,
}
MODEL_RESPONSE_KEYS = {
    "decision",
    "risk_findings",
    "missing_evidence",
    "safe_next_action",
    "user_response",
}
DECISIONS = {"ALLOW", "DENY", "ESCALATE"}


class PilotError(RuntimeError):
    """Fail-closed pilot error."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PilotError(f"cannot load JSON {path}: {exc}") from exc


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise PilotError(f"cannot read JSONL {path}: {exc}") from exc
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            raise PilotError(f"blank line in {path}:{number}")
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise PilotError(f"invalid JSON in {path}:{number}: {exc}") from exc
        if not isinstance(value, dict):
            raise PilotError(f"row is not an object in {path}:{number}")
        rows.append(value)
    return rows


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_text(value: datetime | None = None) -> str:
    return (value or utc_now()).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def parse_rfc3339(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise PilotError("release timestamp is empty")
    candidate = value.strip()
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise PilotError(f"invalid RFC3339 timestamp: {value}") from exc
    if parsed.tzinfo is None:
        raise PilotError("release timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def write_json_exclusive(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    try:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise PilotError(f"refusing to overwrite immutable file: {path}") from exc


def write_json_exclusive_or_verify(path: Path, value: Any) -> None:
    if path.exists():
        existing = load_json(path)
        if canonical_json(existing) != canonical_json(value):
            raise PilotError(f"existing file differs from required canonical content: {path}")
        return
    write_json_exclusive(path, value)


def write_jsonl_atomic(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    payload = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    with temp.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)


def run_protocol_validator() -> None:
    completed = subprocess.run(
        [sys.executable, "-B", str(ROOT / "scripts" / "validate_protocol.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise PilotError(f"frozen protocol validation failed: {detail}")


def validate_release_receipt(path: Path | None = None) -> tuple[dict[str, Any], datetime]:
    receipt_path = path or (ROOT / "release_receipt.json")
    if not receipt_path.is_file():
        raise PilotError(
            "release_receipt.json is missing; publish public v0.1.0 before formal execution"
        )
    receipt = load_json(receipt_path)
    expected_keys = {
        "protocol_tag",
        "protocol_commit_sha",
        "protocol_release_url",
        "released_at",
    }
    if not isinstance(receipt, dict) or set(receipt) != expected_keys:
        raise PilotError("release receipt keys do not match the frozen receipt contract")
    if receipt["protocol_tag"] != "v0.1.0":
        raise PilotError("release receipt tag must be v0.1.0")
    if not re.fullmatch(r"[0-9a-fA-F]{40}", str(receipt["protocol_commit_sha"])):
        raise PilotError("protocol commit SHA must contain exactly 40 hexadecimal characters")
    url = str(receipt["protocol_release_url"])
    if not re.fullmatch(r"https://github\.com/[^/]+/[^/]+/releases/tag/v0\.1\.0", url):
        raise PilotError("protocol release URL must be a GitHub v0.1.0 release URL")
    released_at = parse_rfc3339(str(receipt["released_at"]))
    if released_at > utc_now():
        raise PilotError("public release timestamp is in the future")
    return receipt, released_at


def validate_model_response(raw_response: str) -> tuple[str, dict[str, Any] | None]:
    try:
        parsed = json.loads(raw_response)
    except json.JSONDecodeError:
        return "FORMAT_FAIL", None
    if not isinstance(parsed, dict) or set(parsed) != MODEL_RESPONSE_KEYS:
        return "FORMAT_FAIL", parsed if isinstance(parsed, dict) else None
    if parsed.get("decision") not in DECISIONS:
        return "FORMAT_FAIL", parsed
    for key in ("risk_findings", "missing_evidence"):
        value = parsed.get(key)
        if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
            return "FORMAT_FAIL", parsed
    for key in ("safe_next_action", "user_response"):
        if not isinstance(parsed.get(key), str) or not parsed[key]:
            return "FORMAT_FAIL", parsed
    return "VALID_JSON", parsed


def load_cases_by_id() -> dict[str, dict[str, Any]]:
    rows = load_jsonl(ROOT / "data" / "pilot_cases.jsonl")
    return {row["case_id"]: row for row in rows}


def load_gold_by_id() -> dict[str, dict[str, Any]]:
    rows = load_jsonl(ROOT / "data" / "gold_records.jsonl")
    return {row["case_id"]: row for row in rows}


def render_user_prompt(case: dict[str, Any]) -> str:
    template = (ROOT / "prompts" / "user_template.txt").read_text(encoding="utf-8")
    rendered = template.replace("{{case_id}}", case["case_id"])
    rendered = rendered.replace("{{scenario}}", case["scenario"])
    rendered = rendered.replace("{{requested_action}}", case["requested_action"])
    if "{{" in rendered or "}}" in rendered:
        raise PilotError(f"unresolved prompt template placeholder for {case['case_id']}")
    return rendered


def format_error(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {exc}"
