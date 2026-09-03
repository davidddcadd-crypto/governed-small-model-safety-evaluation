#!/usr/bin/env python3
"""Freeze exact Granite 4 identity, host, and one excluded case-free options probe."""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

from round5_common import (
    CODEX_CLI_VERSION, MODEL_BLOB_SHA256, MODEL_BLOB_SIZE, MODEL_LAYERS,
    MODEL_MANIFEST_SHA256, MODEL_TAG, OLLAMA_VERSION, ROUND5, SETTINGS,
    PilotError, http_json, utc_text, validate_local_environment,
    write_json_exclusive,
)

PYTHON313 = Path(r"C:\Users\User\AppData\Local\Python\pythoncore-3.13-64\python.exe")


def _command(command: list[str]) -> dict[str, Any]:
    try:
        completed = subprocess.run(command, text=True, capture_output=True, timeout=60, check=False)
        return {"command": command, "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}
    except (OSError, subprocess.SubprocessError) as exc:
        return {"command": command, "returncode": None, "stdout": "", "stderr": f"{type(exc).__name__}: {exc}"}


def _registry_value(key_path: str, value_name: str) -> Any:
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            return winreg.QueryValueEx(key, value_name)[0]
    except (ImportError, OSError):
        return None


def _windows_hardware() -> tuple[int | None, int | None]:
    try:
        import ctypes
        from ctypes import wintypes

        class MemoryStatus(ctypes.Structure):
            _fields_ = [
                ("dwLength", wintypes.DWORD), ("dwMemoryLoad", wintypes.DWORD),
                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        memory = MemoryStatus()
        memory.dwLength = ctypes.sizeof(memory)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
            raise OSError("GlobalMemoryStatusEx failed")
        size = wintypes.DWORD(0)
        kernel = ctypes.windll.kernel32
        kernel.GetLogicalProcessorInformationEx(0, None, ctypes.byref(size))
        buffer = ctypes.create_string_buffer(size.value)
        if not kernel.GetLogicalProcessorInformationEx(0, buffer, ctypes.byref(size)):
            raise OSError("GetLogicalProcessorInformationEx failed")
        offset = cores = 0
        while offset < size.value:
            relationship = int.from_bytes(buffer.raw[offset:offset + 4], "little")
            record_size = int.from_bytes(buffer.raw[offset + 4:offset + 8], "little")
            if relationship == 0:
                cores += 1
            if record_size <= 0:
                raise OSError("invalid processor topology record")
            offset += record_size
        return int(memory.ullTotalPhys), cores
    except (AttributeError, OSError):
        return None, None


def _host() -> dict[str, Any]:
    memory, physical_cores = _windows_hardware()
    try:
        import psutil

        memory = psutil.virtual_memory().total or memory
        physical_cores = psutil.cpu_count(logical=False) or physical_cores
    except ImportError:
        pass
    gpu = _command(["nvidia-smi", "--query-gpu=name,memory.total,memory.free,driver_version", "--format=csv,noheader,nounits"])
    fields = [part.strip() for part in gpu["stdout"].strip().split(",")] if gpu["returncode"] == 0 else []
    validation_version = _command([str(PYTHON313), "--version"]) if PYTHON313.is_file() else {"stdout": "", "returncode": None}
    default_version = _command(["python", "--version"])
    return {
        "os_product_name_registry": _registry_value(r"SOFTWARE\Microsoft\Windows NT\CurrentVersion", "ProductName"),
        "os_display_version": _registry_value(r"SOFTWARE\Microsoft\Windows NT\CurrentVersion", "DisplayVersion"),
        "os_build": f"{_registry_value(r'SOFTWARE\Microsoft\Windows NT\CurrentVersion', 'CurrentBuild')}.{_registry_value(r'SOFTWARE\Microsoft\Windows NT\CurrentVersion', 'UBR')}",
        "os_architecture": platform.architecture()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "manufacturer": _registry_value(r"HARDWARE\DESCRIPTION\System\BIOS", "SystemManufacturer"),
        "system_model": _registry_value(r"HARDWARE\DESCRIPTION\System\BIOS", "SystemProductName"),
        "cpu": str(_registry_value(r"HARDWARE\DESCRIPTION\System\CentralProcessor\0", "ProcessorNameString") or "").strip(),
        "physical_cores": physical_cores,
        "logical_processors": os.cpu_count(),
        "physical_memory_bytes": memory,
        "gpu": fields[0] if len(fields) == 4 else None,
        "gpu_memory_mib": int(fields[1]) if len(fields) == 4 else None,
        "gpu_free_memory_mib_at_capture": int(fields[2]) if len(fields) == 4 else None,
        "nvidia_driver": fields[3] if len(fields) == 4 else None,
        "python_default": default_version.get("stdout", "").strip().removeprefix("Python "),
        "python_capture_runtime": platform.python_version(),
        "python_validation_runtime": validation_version.get("stdout", "").strip().removeprefix("Python "),
        "python_validation_note": "Use Python 3.13 for the applicable validation suite; do not repeatedly investigate the known unrelated Python 3.14 Windows subprocess WinError 6 behavior.",
        "codex_cli_version": CODEX_CLI_VERSION,
    }


def main() -> int:
    target = ROUND5 / "MODEL_AND_ENVIRONMENT.json"
    try:
        if target.exists():
            raise PilotError("refusing to overwrite Round-5 model/environment record")
        validated = validate_local_environment()
        started = utc_text()
        request = {
            "model": MODEL_TAG,
            "messages": [
                {"role": "system", "content": "Return only the word OK."},
                {"role": "user", "content": "Excluded case-free Round 5 generation-options compatibility preflight. No evaluation case content is present."},
            ],
            "stream": False,
            "keep_alive": "10m",
            "options": {key: SETTINGS[key] for key in ("temperature", "seed", "num_ctx", "num_predict")},
        }
        raw, response = http_json("/api/chat", method="POST", payload=request)
        completed = utc_text()
        if not isinstance(response, dict) or response.get("model") != MODEL_TAG or response.get("done") is not True:
            raise PilotError("excluded options preflight did not complete on exact target")
        manifest = Path.home() / ".ollama/models/manifests/registry.ollama.ai/library/granite4/3b"
        value = {
            "preparation_capture_utc": completed,
            "formal_environment_capture": "Required again immediately after excluded warm-up and before R5A-RUN-001",
            "ollama": {
                "cli_version": OLLAMA_VERSION,
                "api_version": validated["ollama_api_version"],
                "model_tag": MODEL_TAG,
                "manifest_path": manifest.as_posix(),
                "manifest_size_bytes": manifest.stat().st_size,
                "manifest_sha256": MODEL_MANIFEST_SHA256,
                "model_blob_sha256": MODEL_BLOB_SHA256,
                "model_blob_size_bytes": MODEL_BLOB_SIZE,
                "model_family": "granite",
                "parameter_count": 3_402_836_480,
                "ollama_parameter_label": "3.4B",
                "source_size_label": "3B",
                "quantization": "Q4_K_M",
                "context_length": 131072,
                "embedding_length": 2560,
                "capabilities": ["completion", "tools"],
                "manifest_layers": {
                    label: {"sha256": digest, "size_bytes": size, "independently_verified": True, **({"inspectable": True} if label == "template" else {})}
                    for label, (digest, size) in MODEL_LAYERS.items()
                },
            },
            "host": _host(),
            "generation_settings": {**SETTINGS, "conversation_history": False},
            "excluded_case_free_generation_preflight": {
                "excluded_from_formal_evidence": True,
                "contains_formal_case_content": False,
                "contains_gold": False,
                "contains_david_calibration": False,
                "started_at": started,
                "completed_at": completed,
                "request": request,
                "raw_api_body": raw,
                "response": response,
                "result": "PASS: exact four generation options accepted",
            },
            "material_differences": [
                "Granite 4 model implementation and Ollama chat template differ from prior rounds by design; supplied prompt bytes do not change.",
                "The exact tag is granite4:3b; Ollama reports 3.4B and the model metadata reports 3,402,836,480 parameters.",
                "The David-calibrated AI surrogate method remains constant, but cross-round comparisons remain descriptive and uncontrolled.",
            ],
        }
        write_json_exclusive(target, value)
        print("PASS: exact Granite 4 identity, host, and excluded case-free options preflight frozen")
        return 0
    except (PilotError, OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
