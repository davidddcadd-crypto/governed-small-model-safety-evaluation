from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_round3_publication  # noqa: E402


def test_publication_addendum_disclosures() -> None:
    validate_round3_publication.validate_addendum()


def test_combined_logs_are_additive_and_not_canonical_substitutions() -> None:
    validate_round3_publication.validate_combined_log_custody()


def test_round3_publication_manifest() -> None:
    validate_round3_publication.validate_publication_manifest()


def test_public_administrative_status() -> None:
    validate_round3_publication.validate_administrative_status()
