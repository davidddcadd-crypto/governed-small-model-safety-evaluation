from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_round4_publication  # noqa: E402


def test_publication_templates_and_additive_plan_are_complete() -> None:
    validate_round4_publication.validate_templates()


def test_publication_state_is_prepublication() -> None:
    assert validate_round4_publication.publication_state() == "PREPUBLICATION"

