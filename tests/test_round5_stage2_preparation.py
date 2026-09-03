from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_round5_stage2_preparation as stage2  # noqa: E402


def test_stage2_packet_is_deterministically_bound_to_frozen_stage1() -> None:
    result = stage2.validate_stage2_preparation()
    assert result["result"] == "PASS"
    assert result["stage1_output_sha256"] == stage2.STAGE1_RAW_OUTPUT_SHA256
    assert result["stage1_output_unchanged"] is True
    assert result["stage2_row_count"] == 24


def test_stage2_isolation_audit_passes() -> None:
    result = stage2.validate_stage2_preparation()
    assert result["isolation_audit"] == "PASS"
    assert result["stage2_runtime_schema_sha256"] == stage2.STAGE2_RUNTIME_SCHEMA_SHA256


def test_stage2_remains_local_and_untransmitted() -> None:
    result = stage2.validate_stage2_preparation()
    assert result["stage2_transmissions"] == 0
    assert result["stage1_session_resumes"] == 0
    assert result["formal_ratings"] == 0
