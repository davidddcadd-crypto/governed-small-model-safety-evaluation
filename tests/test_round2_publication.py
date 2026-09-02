from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_round2_publication  # noqa: E402


def test_frozen_round1_and_round2_evidence() -> None:
    validate_round2_publication.validate_frozen_evidence()


def test_publication_addendum_disclosures() -> None:
    validate_round2_publication.validate_addendum()


def test_schema_rejection_logs_and_provenance() -> None:
    validate_round2_publication.validate_provenance()


def test_publication_manifest() -> None:
    validate_round2_publication.validate_publication_manifest()
