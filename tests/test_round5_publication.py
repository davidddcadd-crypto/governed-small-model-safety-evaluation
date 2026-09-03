from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_round5_publication as publication  # noqa: E402


def test_round5_publication_package_is_valid() -> None:
    result = publication.validate_publication()
    assert result["result"] == "PASS_PUBLICATION_PACKAGE"


def test_release_notes_cover_metrics_custody_and_claim_boundaries() -> None:
    publication.validate_release_notes()


def test_publication_manifest_binds_every_round5_commit_path_except_itself() -> None:
    value = publication.load_json(publication.MANIFEST_PATH)
    paths = publication.collect_commit_paths(include_manifest=False)
    assert [row["path"] for row in value["publication_package_files"]] == paths
    assert value["publication_package_file_count"] == len(paths)


def test_checkpoint_and_public_root_gitattributes_are_excluded_from_commit_delta() -> None:
    paths = publication.collect_commit_paths()
    assert "results/ratings_primary.partial.jsonl" not in paths
    assert ".gitattributes" not in paths
    assert publication.sha256_bytes((publication.ROOT / ".gitattributes").read_bytes()) == publication.ROOT_GITATTRIBUTES_SHA256


def test_publication_lifecycle_adds_no_new_expected_transition() -> None:
    plan = publication.load_json(publication.RESULTS / "ROUND5_PUBLICATION_CUSTODY_PLAN.json")
    assert plan["expected_lifecycle_transition_count"] == 10
    assert plan["new_publication_transition_classifications"] == []
    assert plan["state_sequence"][-1] == "PUBLICATION_PACKAGE_FROZEN"
