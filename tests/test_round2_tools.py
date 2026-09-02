from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import analyze_round2  # noqa: E402
import build_round2_protocol_manifest  # noqa: E402
import build_round2_rating_packets  # noqa: E402
import build_round2_result_manifest  # noqa: E402
import round2_common  # noqa: E402
import validate_round2  # noqa: E402
import validate_round2_ratings  # noqa: E402
from pilot_common import PilotError, sha256_bytes  # noqa: E402


class Round2ToolTests(unittest.TestCase):
    def test_frozen_sources_and_calibration_validate(self) -> None:
        round2_common.run_round1_validator()
        round2_common.validate_sources()
        validate_round2.validate_calibration()

    def test_formal_request_reuses_round1_options_without_tools(self) -> None:
        request = round2_common.build_formal_request("system bytes", "user bytes")
        self.assertEqual(request["model"], "ministral-3:3b")
        self.assertEqual(request["options"], {
            "temperature": 0, "seed": 42, "num_ctx": 4096, "num_predict": 512,
        })
        self.assertNotIn("tools", request)
        self.assertNotIn("format", request)
        self.assertEqual([row["role"] for row in request["messages"]], ["system", "user"])

    def test_no_output_is_a_completed_format_state(self) -> None:
        raw, status, parsed = round2_common.extract_formal_output(
            {"model": "ministral-3:3b", "message": {"role": "assistant"}, "done": True}
        )
        self.assertEqual((raw, status, parsed), ("", "NO_OUTPUT", None))

    def test_authorization_statement_is_exact_and_hash_bound(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "authorization.json"
            path.write_text(json.dumps({
                "authorization_type": "ROUND2A_FORMAL_EXECUTION",
                "project_owner": "David / Tai Wai Lee",
                "authorized_protocol_manifest_sha256": "a" * 64,
                "statement": "not exact",
                "authorized_at": "2026-09-02T00:00:00Z",
            }), encoding="utf-8")
            with patch.object(
                round2_common, "protocol_manifest_sha256", return_value="a" * 64
            ):
                with self.assertRaises(PilotError):
                    round2_common.validate_authorization(path)

    def test_two_stage_packet_and_surrogate_rating_pipeline(self) -> None:
        modules = [
            round2_common, build_round2_rating_packets, validate_round2_ratings,
        ]
        old_results = {module: module.RESULTS for module in modules}
        with tempfile.TemporaryDirectory() as temp:
            results = Path(temp) / "results"
            raw_runs = results / "raw_runs"
            raw_runs.mkdir(parents=True)
            order = round2_common.load_order()
            for spec in order:
                identifier = round2_common.run_id(spec["sequence"])
                row = {
                    "run_id": identifier,
                    "sequence": spec["sequence"],
                    "arm": spec["arm"],
                    "case_id": spec["case_id"],
                    "raw_response": '{"decision":"ALLOW"}',
                    "format_status": "FORMAT_FAIL",
                    "timing": {
                        "client_wall_duration_ns": 1_000_000,
                        "total_duration_ns": 900_000,
                        "prompt_eval_count": 100,
                        "eval_count": 20,
                    },
                }
                (raw_runs / f"{identifier}.json").write_text(
                    json.dumps(row), encoding="utf-8"
                )
            try:
                for module in modules:
                    module.RESULTS = results
                build_round2_rating_packets.build_stage1()
                stage1_packet = round2_common.load_jsonl(
                    results / "blinded_extraction_packet.jsonl"
                )
                self.assertNotIn("gold_record", stage1_packet[0])
                self.assertNotIn("arm", stage1_packet[0])
                self.assertNotIn("case_id", stage1_packet[0])

                extraction_value = {
                    "stage": "DECISION_EXTRACTION",
                    "ratings": [{
                        "response_id": row["response_id"],
                        "extracted_decision": "ALLOW",
                        "format_status": row["format_status"],
                        "extraction_evidence": "The response states ALLOW.",
                    } for row in stage1_packet],
                }
                extraction_path = results / "incoming_stage1.json"
                extraction_path.write_text(json.dumps(extraction_value), encoding="utf-8")
                build_round2_rating_packets.build_stage2(extraction_path)
                scoring_packet = round2_common.load_jsonl(
                    results / "blinded_scoring_packet.jsonl"
                )
                self.assertIn("gold_record", scoring_packet[0])
                self.assertEqual(scoring_packet[0]["frozen_extracted_decision"], "ALLOW")

                scoring_value = {
                    "stage": "GOLD_DISCLOSED_SCORING",
                    "ratings": [{
                        "response_id": row["response_id"],
                        "risk_score": 2,
                        "authority_evidence_score": 1,
                        "action_control_score": 2,
                        "safe_next_step_score": 1,
                        "hard_failures": [],
                        "remaining_strict_conditions_met": True,
                        "critical_findings_present": row["gold_record"]["critical_findings"],
                        "critical_findings_missing": [],
                        "evidence": ["Synthetic response-grounded test observation."],
                        "reason": "Synthetic deterministic pipeline test.",
                    } for row in scoring_packet],
                }
                score_path = results / "stage2_raw_output.json"
                score_path.write_text(json.dumps(scoring_value), encoding="utf-8")
                prompt1 = results / "stage1_prompt.txt"
                prompt2 = results / "stage2_prompt.txt"
                events1 = results / "stage1_events.jsonl"
                events2 = results / "stage2_events.jsonl"
                prompt1.write_text("stage 1 synthetic prompt", encoding="utf-8")
                prompt2.write_text("stage 2 synthetic prompt", encoding="utf-8")
                events1.write_text('{"type":"thread.started"}\n', encoding="utf-8")
                events2.write_text('{"type":"thread.completed"}\n', encoding="utf-8")
                session = {
                    "rater_id": "round2-test-rater",
                    "rater_type": "DAVID_CALIBRATED_AI_SURROGATE",
                    "provider": "OpenAI",
                    "model": "gpt-5.6-sol",
                    "reasoning": "xhigh",
                    "codex_cli_version": "0.152.0",
                    "session_id": "00000000-0000-0000-0000-000000000001",
                    "stage1_started_at": "2026-09-02T00:00:00Z",
                    "stage1_completed_at": "2026-09-02T00:01:00Z",
                    "stage2_started_at": "2026-09-02T00:02:00Z",
                    "stage2_completed_at": "2026-09-02T00:03:00Z",
                    "stage1_command": "codex exec --model gpt-5.6-sol",
                    "stage2_command": "codex exec resume --model gpt-5.6-sol",
                    "stage1_prompt_path": str(prompt1),
                    "stage2_prompt_path": str(prompt2),
                    "stage1_events_path": str(events1),
                    "stage2_events_path": str(events2),
                    "calibration_sha256": sha256_bytes(
                        (ROOT / "round2/DAVID_RATER_CALIBRATION_V1.md").read_bytes()
                    ),
                    "rubric_sha256": sha256_bytes(
                        (ROOT / "docs/SCORING_RUBRIC.md").read_bytes()
                    ),
                    "extraction_packet_sha256": sha256_bytes(
                        (results / "blinded_extraction_packet.jsonl").read_bytes()
                    ),
                    "scoring_packet_sha256": sha256_bytes(
                        (results / "blinded_scoring_packet.jsonl").read_bytes()
                    ),
                    "stage1_prompt_sha256": sha256_bytes(prompt1.read_bytes()),
                    "stage2_prompt_sha256": sha256_bytes(prompt2.read_bytes()),
                    "stage1_events_sha256": sha256_bytes(events1.read_bytes()),
                    "stage2_events_sha256": sha256_bytes(events2.read_bytes()),
                    "stage1_raw_output_sha256": sha256_bytes(
                        (results / "stage1_raw_output.json").read_bytes()
                    ),
                    "stage2_raw_output_sha256": sha256_bytes(score_path.read_bytes()),
                    "tool_calls_observed": 0,
                }
                session_path = results / "rater_session.json"
                session_path.write_text(json.dumps(session), encoding="utf-8")
                rows = validate_round2_ratings.construct(
                    results / "stage1_raw_output.json", score_path, session_path
                )
                self.assertEqual(len(rows), 24)
                self.assertEqual(
                    rows[0]["rater_type"], "DAVID_CALIBRATED_AI_SURROGATE"
                )
            finally:
                for module, value in old_results.items():
                    module.RESULTS = value

    def test_rater_tool_event_fails_closed(self) -> None:
        self.assertTrue(validate_round2_ratings._tool_event(
            {"type": "item.started", "item": {"type": "command_execution"}}
        ))

    def test_prespecified_replication_signal(self) -> None:
        a = {"eligible_runs": 12, "strict_safety_pass_count": 2,
             "unsafe_allow_count": 0, "hard_failure_count": 0}
        b = {"eligible_runs": 12, "strict_safety_pass_count": 4,
             "unsafe_allow_count": 0, "hard_failure_count": 0}
        self.assertEqual(analyze_round2.replication_signal(a, b), "SUPPORTIVE")
        b["unsafe_allow_count"] = 1
        self.assertEqual(analyze_round2.replication_signal(a, b), "NOT_SUPPORTIVE")
        b["eligible_runs"] = 11
        self.assertEqual(analyze_round2.replication_signal(a, b), "NOT_EVALUABLE")

    def test_result_manifest_refuses_incomplete_evidence(self) -> None:
        old = build_round2_result_manifest.RESULTS
        with tempfile.TemporaryDirectory() as temp:
            try:
                build_round2_result_manifest.RESULTS = Path(temp)
                with self.assertRaises(PilotError):
                    build_round2_result_manifest.evidence_paths()
            finally:
                build_round2_result_manifest.RESULTS = old

    def test_manifest_file_inventory_is_complete(self) -> None:
        missing = [
            path for path in build_round2_protocol_manifest.FILES
            if not (ROOT / path).is_file()
        ]
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
