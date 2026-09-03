from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_round5_postexecution_repair as repair  # noqa: E402


def test_additive_repair_preserves_and_validates_frozen_evidence() -> None:
    result = repair.validate_repair()
    assert result["result"] == "PASS"
    assert result["frozen_core_unchanged"] is True
    assert result["formal_evidence"]["first_attempts"] == 24


def test_exact_three_lifecycle_transitions_are_recorded() -> None:
    result = repair.validate_repair()
    assert result["lifecycle_transitions"] == [
        "tests/test_round5_preparation.py::test_zero_formal_observations",
        "tests/test_round5_preparation.py::test_result_manifest_refuses_incomplete_evidence",
        "tests/test_round5_preparation.py::test_lifecycle_architecture_is_frozen",
    ]


def test_r16_false_interruption_record_is_rejected_without_response_change() -> None:
    result = repair.validate_repair()
    assert result["r5a_run_016_interruption_record"] == "REJECTED_NOT_AUTHORITATIVE"
    assert result["r5a_run_016_raw_response_bytes_changed"] is False
    assert result["additional_model_requests"] == 0


def test_pre_stage1_absence_assertion_is_explicit_lifecycle_transition() -> None:
    result = repair.validate_repair()
    assert result["stage1_completion_transitions"] == [
        "scripts/validate_round5_postexecution_repair.py::validate_stage1_preparation pre-Stage-1 absence gate",
        "tests/test_round5_postexecution_repair.py::test_stage1_remains_local_frozen_and_untransmitted",
    ]
    assert result["stage1_state"] == "COMPLETE_AND_FROZEN"
    assert result["openai_stage1_transmissions"] == 1
    assert result["stage2_transmissions"] == 0
    assert result["formal_ratings"] == 0
    assert (repair.RESULTS / "STAGE1_TRANSMISSION_AUTHORIZATION.json").is_file()
    assert (repair.RESULTS / "stage1_raw_output.json").is_file()
