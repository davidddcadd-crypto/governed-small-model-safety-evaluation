from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_round4_publication_v2 as publication  # noqa: E402


def test_publication_manifest_directly_binds_frozen_and_additive_custody() -> None:
    assert publication.validate() == "PUBLICATION_VALID"
    value = publication.load_json(publication.RESULTS / "PUBLICATION_MANIFEST.json")
    assert len(value["frozen_protocol_files"]) == 57
    assert len(value["frozen_result_files"]) == 94
    assert len(value["publication_package_files"]) == len(publication.FUTURE_ADDITIVE_PATHS)


def test_unchanged_gitattributes_is_authorized_and_bound() -> None:
    value = publication.load_json(publication.RESULTS / "PUBLICATION_MANIFEST.json")
    rows = {row["path"]: row for row in value["publication_package_files"]}
    assert rows[".gitattributes"]["sha256"] == publication.GITATTRIBUTES_SHA256
    assert publication.sha256_bytes((publication.ROOT / ".gitattributes").read_bytes()) == publication.GITATTRIBUTES_SHA256


def test_release_notes_cover_required_disclosures() -> None:
    publication.validate_release_notes()


def test_publication_package_does_not_include_local_checkpoint() -> None:
    value = publication.load_json(publication.RESULTS / "PUBLICATION_MANIFEST.json")
    paths = {row["path"] for row in value["publication_package_files"]}
    assert "results/ratings_primary.partial.jsonl" not in paths
