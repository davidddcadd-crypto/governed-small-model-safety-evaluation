#!/usr/bin/env python3
"""Run excluded, case-free Round 4A Codex runtime-schema preflights."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from round4_common import CODEX_CLI_VERSION, ROOT, ROUND4, PilotError, sha256_bytes


def _tool_event(value: Any) -> bool:
    forbidden = {
        "tool_call", "function_call", "command_execution", "mcp_tool_call",
        "exec_command", "shell_command", "computer_call",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"type", "kind", "name"} and isinstance(item, str):
                lowered = item.lower()
                if lowered in forbidden or "tool_call" in lowered:
                    return True
            if _tool_event(item):
                return True
    return any(_tool_event(item) for item in value) if isinstance(value, list) else False


def _write_exclusive(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(payload)


def _run_stage(stage: str) -> dict[str, Any]:
    prompt_path = ROUND4 / "preflight" / f"{stage}_schema_prompt.txt"
    schema_name = (
        "runtime_surrogate_extraction_output.schema.json"
        if stage == "stage1"
        else "runtime_surrogate_scoring_output.schema.json"
    )
    schema_path = ROUND4 / "schemas" / schema_name
    events_path = ROUND4 / "preflight" / f"{stage}_schema_events.jsonl"
    combined_path = ROUND4 / "preflight" / f"{stage}_schema_combined.log"
    output_path = ROUND4 / "preflight" / f"{stage}_schema_raw_output.json"
    for path in (events_path, combined_path, output_path):
        if path.exists():
            raise PilotError(f"refusing to overwrite {path.relative_to(ROOT).as_posix()}")
    prompt = prompt_path.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix=f"round4_{stage}_schema_") as isolated:
        command = [
            "codex", "exec", "--model", "gpt-5.6-sol",
            "-c", 'model_reasoning_effort="xhigh"', "--strict-config",
            "--ignore-user-config", "--ignore-rules", "--sandbox", "read-only",
            "--skip-git-repo-check", "--ephemeral", "--json",
            "--output-schema", str(schema_path), "--cd", isolated, prompt,
        ]
        completed = subprocess.run(command, capture_output=True, timeout=300, check=False)
    combined = completed.stderr + completed.stdout
    if completed.returncode:
        _write_exclusive(combined_path, combined)
        raise PilotError(f"{stage} schema preflight failed with exit {completed.returncode}")
    try:
        event_lines = [line for line in completed.stdout.decode("utf-8").splitlines() if line.strip()]
        events = [json.loads(line) for line in event_lines]
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        _write_exclusive(combined_path, combined)
        raise PilotError(f"{stage} emitted invalid JSON events") from exc
    expected_types = ["thread.started", "turn.started", "item.completed", "turn.completed"]
    if [event.get("type") for event in events] != expected_types:
        _write_exclusive(combined_path, combined)
        raise PilotError(f"{stage} event sequence is not exact")
    if _tool_event(events):
        _write_exclusive(combined_path, combined)
        raise PilotError(f"{stage} used a tool")
    item = events[2].get("item", {})
    if item.get("type") != "agent_message" or not isinstance(item.get("text"), str):
        raise PilotError(f"{stage} did not return one agent message")
    try:
        output = json.loads(item["text"])
    except json.JSONDecodeError as exc:
        raise PilotError(f"{stage} agent message is not JSON") from exc
    expected_stage = "DECISION_EXTRACTION" if stage == "stage1" else "GOLD_DISCLOSED_SCORING"
    ids = [f"R4R{index:03d}" for index in range(1, 25)]
    if output.get("stage") != expected_stage or [row.get("response_id") for row in output.get("ratings", [])] != ids:
        raise PilotError(f"{stage} schema output content mismatch")
    events_bytes = ("\n".join(event_lines) + "\n").encode("utf-8")
    output_bytes = (json.dumps(output, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    _write_exclusive(combined_path, combined)
    _write_exclusive(events_path, events_bytes)
    _write_exclusive(output_path, output_bytes)
    usage = events[-1].get("usage", {})
    return {
        "session_id": events[0]["thread_id"],
        "prompt_path": prompt_path.relative_to(ROOT).as_posix(),
        "prompt_sha256": sha256_bytes(prompt_path.read_bytes()),
        "runtime_schema_path": schema_path.relative_to(ROOT).as_posix(),
        "runtime_schema_sha256": sha256_bytes(schema_path.read_bytes()),
        "combined_log_path": combined_path.relative_to(ROOT).as_posix(),
        "combined_log_sha256": sha256_bytes(combined_path.read_bytes()),
        "events_path": events_path.relative_to(ROOT).as_posix(),
        "events_sha256": sha256_bytes(events_path.read_bytes()),
        "raw_output_path": output_path.relative_to(ROOT).as_posix(),
        "raw_output_sha256": sha256_bytes(output_path.read_bytes()),
        "event_types": expected_types,
        "tool_call_count": 0,
        "rating_count": 24,
        "schema_accepted": True,
        "request_rejected": False,
        "usage": {
            "input_tokens": usage.get("input_tokens"),
            "output_tokens": usage.get("output_tokens"),
        },
    }


def main() -> int:
    try:
        version = subprocess.run(
            ["codex", "--version"], text=True, capture_output=True,
            timeout=30, check=False,
        )
        if version.returncode or f"codex-cli {CODEX_CLI_VERSION}" not in (version.stdout + version.stderr):
            raise PilotError("Codex CLI version mismatch")
        target = ROUND4 / "preflight" / "SCHEMA_PREFLIGHT_EVIDENCE.json"
        if target.exists():
            raise PilotError("refusing to overwrite schema preflight evidence")
        stage1 = _run_stage("stage1")
        stage2 = _run_stage("stage2")
        value = {
            "record_type": "ROUND4A_EXCLUDED_CASE_FREE_SCHEMA_COMPATIBILITY_PREFLIGHT",
            "provider": "OpenAI", "model": "gpt-5.6-sol", "reasoning": "xhigh",
            "codex_cli_version": CODEX_CLI_VERSION,
            "excluded_from_formal_observations": True,
            "excluded_from_formal_ratings": True,
            "contains_formal_case_content": False,
            "contains_frozen_prompt_content": False,
            "contains_gold": False,
            "contains_llama_response": False,
            "contains_david_calibration": False,
            "round2_rejection_evidence": {
                "stage1_path": "results/round2_ministral3b/publication_disclosures/STAGE1_SCHEMA_REJECTION.jsonl",
                "stage1_sha256": "aa5e78715968d6463d090603be1d02630f26e79e69b3ca9df2a0b32a0993acdc",
                "stage2_path": "results/round2_ministral3b/publication_disclosures/STAGE2_SCHEMA_REJECTION.jsonl",
                "stage2_sha256": "432b88f018d8b5af5082fc1e332a19e2dd2453061c99f66c6031d91f255df2ec",
            },
            "adapter": {
                "stage_type_added": True,
                "runtime_unique_items_omitted": True,
                "canonical_unique_items_retained": True,
                "deterministic_uniqueness_validation_retained": True,
                "scoring_semantics_changed": False,
            },
            "stage1": stage1, "stage2": stage2, "result": "PASS",
        }
        _write_exclusive(
            target,
            (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
        )
        print("PASS: Round 4A Stage-1 and Stage-2 runtime schemas accepted; tools = 0")
        return 0
    except (PilotError, OSError, subprocess.SubprocessError) as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
