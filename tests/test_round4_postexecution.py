from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_round4_postexecution  # noqa: E402


def test_pre_execution_lifecycle_is_explicit() -> None:
    assert validate_round4_postexecution.lifecycle_state() == "PRE_EXECUTION"
    validate_round4_postexecution.validate_prepared_architecture()


def test_frozen_preparation_assertions_have_declared_transitions() -> None:
    rows = validate_round4_postexecution.lifecycle_transition_record()
    assert [row["test"] for row in rows] == [
        "test_zero_formal_observations",
        "test_result_manifest_refuses_incomplete_evidence",
    ]
    assert {row["post_execution_status"] for row in rows} == {"EXPECTED_LIFECYCLE_TRANSITION"}
    assert {row["frozen_test_modified"] for row in rows} == {"NO"}


def test_partial_execution_fails_closed(tmp_path: Path) -> None:
    raw = tmp_path / "raw_runs"
    raw.mkdir()
    (raw / "R4A-RUN-001.json").write_text("{}", encoding="utf-8")
    assert validate_round4_postexecution.lifecycle_state(tmp_path) == "INCOMPLETE_FAIL_CLOSED"


def test_excluded_checkpoint_may_be_absent_but_not_changed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    checkpoint = tmp_path / "ratings_primary.partial.jsonl"
    monkeypatch.setattr(validate_round4_postexecution, "CHECKPOINT_PATH", checkpoint)
    validate_round4_postexecution.validate_excluded_checkpoint()
    checkpoint.write_bytes(b"changed")
    with pytest.raises(validate_round4_postexecution.PilotError, match="checkpoint changed"):
        validate_round4_postexecution.validate_excluded_checkpoint()

