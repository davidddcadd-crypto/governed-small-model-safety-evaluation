from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_round4_postmanifest_repair as repair  # noqa: E402
import validate_round4_publication_v2 as publication  # noqa: E402


def test_additive_repair_validates_without_changing_frozen_core() -> None:
    result = repair.validate_additive()
    assert result["result"] == "PASS"
    assert result["frozen_core_unchanged"] is True


def test_third_and_fourth_lifecycle_transitions_are_explicit_and_frozen_tests_are_unchanged() -> None:
    value = repair.load_json(repair.RESULTS / "ROUND4_POSTMANIFEST_REPAIR.json")
    lifecycle = value["lifecycle_reconciliation"]
    assert lifecycle["transitions"] == repair.TRANSITIONS
    assert lifecycle["third_transition"]["post_execution_status"] == "EXPECTED_LIFECYCLE_TRANSITION"
    assert lifecycle["fourth_transition"]["post_execution_status"] == "EXPECTED_LIFECYCLE_TRANSITION"
    assert lifecycle["fifth_transition"]["publication_packaging_status"] == "EXPECTED_LIFECYCLE_TRANSITION"
    assert lifecycle["frozen_test_modified"] is False
    assert lifecycle["additional_frozen_test_modified"] is False
    assert lifecycle["publication_frozen_test_modified"] is False


def test_presampling_rejection_and_zero_event_stream_are_bound() -> None:
    repair.validate_rejection()
    value = repair.load_json(repair.RESULTS / "STAGE2_RESUME_REJECTION.json")
    assert value["model_sampling_occurred"] is False
    assert value["raw_output_created"] is False


def test_future_publication_custody_contains_rejection_and_disclosure() -> None:
    assert "results/round4_llama32_3b/STAGE2_RESUME_REJECTION.json" in repair.FUTURE_ADDITIVE_PATHS
    assert "results/round4_llama32_3b/stage2_resume_rejection_events.jsonl" in repair.FUTURE_ADDITIVE_PATHS
    assert "results/round4_llama32_3b/ROUND4_PUBLICATION_ADDENDUM.md" in repair.FUTURE_ADDITIVE_PATHS
    assert publication.validate() == "PUBLICATION_VALID"
