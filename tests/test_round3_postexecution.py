from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_round3_postexecution  # noqa: E402


def test_frozen_protocol_result_and_prior_evidence() -> None:
    validate_round3_postexecution.validate_frozen_evidence()


def test_frozen_preparation_assertions_are_explicit_lifecycle_transitions() -> None:
    statuses = validate_round3_postexecution.validate_lifecycle_transition()
    assert [item["test"] for item in statuses] == [
        "test_zero_formal_observations",
        "test_result_manifest_refuses_incomplete_evidence",
    ]
    assert {item["status"] for item in statuses} == {"EXPECTED_LIFECYCLE_TRANSITION"}


def test_formal_custody_has_no_selective_reruns() -> None:
    validate_round3_postexecution.validate_formal_custody()


def test_canonical_ratings_reconstruct_exactly() -> None:
    validate_round3_postexecution.validate_canonical_reconstruction()


def test_postexecution_validation_record() -> None:
    validate_round3_postexecution.validate_record()


def test_excluded_checkpoint_may_be_absent_but_not_changed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    checkpoint = tmp_path / "ratings_primary.partial.jsonl"
    monkeypatch.setattr(validate_round3_postexecution, "CHECKPOINT_PATH", checkpoint)
    validate_round3_postexecution.validate_excluded_checkpoint()
    checkpoint.write_bytes(b"changed")
    with pytest.raises(validate_round3_postexecution.PilotError, match="checkpoint changed"):
        validate_round3_postexecution.validate_excluded_checkpoint()
