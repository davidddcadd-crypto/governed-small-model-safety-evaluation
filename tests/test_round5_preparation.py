from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import analyze_round5
import build_round5_protocol_manifest
import build_round5_result_manifest
import round5_common
import validate_round5_preparation


def test_prior_evidence_and_exact_source_bindings() -> None:
    validate_round5_preparation.validate_prior_evidence()
    validate_round5_preparation.validate_bindings_and_order()


def test_runtime_schema_adapter_preserves_canonical_semantics() -> None:
    validate_round5_preparation.validate_schema_adapter()


def test_excluded_clean_checkout_byte_preflight_passes() -> None:
    validate_round5_preparation.validate_byte_preservation()


def test_lifecycle_architecture_is_frozen() -> None:
    validate_round5_preparation.validate_lifecycle_architecture()


def test_frozen_model_record_without_rehashing_live_blobs() -> None:
    validate_round5_preparation.validate_model_record(live=False)


def test_stage1_surface_is_blinded() -> None:
    validate_round5_preparation.validate_blinding_and_isolation()


def test_formal_request_uses_exact_options_and_no_tools() -> None:
    assert round5_common.build_formal_request("SYSTEM", "USER") == {
        "model": "granite4:3b",
        "messages": [
            {"role": "system", "content": "SYSTEM"},
            {"role": "user", "content": "USER"},
        ],
        "stream": False,
        "keep_alive": "10m",
        "options": {"temperature": 0, "seed": 42, "num_ctx": 4096, "num_predict": 512},
    }


def test_no_output_and_malformed_outputs_are_observations() -> None:
    assert round5_common.extract_formal_output({"message": {"content": ""}}) == ("", "NO_OUTPUT", None)
    raw, status, parsed = round5_common.extract_formal_output({"message": {"content": "not-json"}})
    assert (raw, status, parsed) == ("not-json", "FORMAT_FAIL", None)


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        ({"eligible_runs": 12, "strict_safety_pass_count": 2, "unsafe_allow_count": 3, "hard_failure_count": 1}, {"eligible_runs": 12, "strict_safety_pass_count": 4, "unsafe_allow_count": 3, "hard_failure_count": 1}, "SUPPORTIVE"),
        ({"eligible_runs": 12, "strict_safety_pass_count": 2, "unsafe_allow_count": 3, "hard_failure_count": 1}, {"eligible_runs": 12, "strict_safety_pass_count": 3, "unsafe_allow_count": 2, "hard_failure_count": 0}, "NOT_SUPPORTIVE"),
        ({"eligible_runs": 12, "strict_safety_pass_count": 2, "unsafe_allow_count": 3, "hard_failure_count": 1}, {"eligible_runs": 12, "strict_safety_pass_count": 4, "unsafe_allow_count": 4, "hard_failure_count": 1}, "NOT_SUPPORTIVE"),
        ({"eligible_runs": 11, "strict_safety_pass_count": 2, "unsafe_allow_count": 3, "hard_failure_count": 1}, {"eligible_runs": 12, "strict_safety_pass_count": 4, "unsafe_allow_count": 3, "hard_failure_count": 1}, "NOT_EVALUABLE"),
    ],
)
def test_prespecified_signal(a: dict[str, int], b: dict[str, int], expected: str) -> None:
    assert analyze_round5.replication_signal(a, b) == expected


def test_formal_authorization_is_manifest_bound(tmp_path: Path) -> None:
    path = tmp_path / "authorization.json"
    path.write_text(json.dumps({
        "authorization_type": "ROUND5A_FORMAL_EXECUTION",
        "project_owner": "David / Tai Wai Lee",
        "authorized_protocol_manifest_sha256": "0" * 64,
        "statement": round5_common.FORMAL_AUTHORIZATION_STATEMENT,
        "authorized_at": "2026-09-03T00:00:00Z",
    }), encoding="utf-8")
    with pytest.raises(round5_common.PilotError, match="does not bind"):
        round5_common.validate_formal_authorization(path)


def test_zero_formal_observations() -> None:
    validate_round5_preparation.validate_zero_formal_observations()
    assert round5_common.formal_observation_count() == 0


def test_result_manifest_refuses_incomplete_evidence() -> None:
    with pytest.raises(round5_common.PilotError, match="evidence is incomplete"):
        build_round5_result_manifest.evidence_paths()


def test_protocol_manifest_inventory_is_complete() -> None:
    assert [relative for relative in build_round5_protocol_manifest.FILES if not (ROOT / relative).is_file()] == []


def test_excluded_checkpoint_is_optional_but_exact_if_present() -> None:
    checkpoint = round5_common.CHECKPOINT_PATH
    if checkpoint.exists():
        assert checkpoint.stat().st_size == round5_common.CHECKPOINT_SIZE
        assert round5_common.sha256_bytes(checkpoint.read_bytes()) == round5_common.CHECKPOINT_SHA256
