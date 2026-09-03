from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_round5_core_result as core  # noqa: E402


def test_core_result_reconstructs_from_frozen_evidence() -> None:
    result = core.validate_core_result()
    assert result["result"] == "PASS_CORE_RESULT_FROZEN"
    assert result["formal_observations"] == result["canonical_ratings"] == 24


def test_prespecified_signal_and_arm_counts_are_frozen() -> None:
    result = core.validate_core_result()
    assert result["signal"] == "SUPPORTIVE"
    assert result["arm_a"]["strict_safety_pass_count"] == 3
    assert result["arm_b"]["strict_safety_pass_count"] == 5
    assert result["arm_a"]["unsafe_allow_count"] == result["arm_b"]["unsafe_allow_count"] == 1
    assert result["arm_a"]["hard_failure_count"] == result["arm_b"]["hard_failure_count"] == 2


def test_paired_outcomes_are_frozen() -> None:
    result = core.validate_core_result()
    assert result["paired_strict"] == {"improved": 2, "unchanged": 10}
    assert result["paired_quality"] == {"improved": 4, "unchanged": 8}
