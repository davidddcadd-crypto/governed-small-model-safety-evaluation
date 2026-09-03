# Round 4A lifecycle-aware validation plan

Round 4 separates immutable historical assertions from validators of later
authorized states.

## PRE_EXECUTION

`validate_round4_preparation.py` is authoritative. It requires a frozen
protocol manifest, exact prior/source/model/preflight bindings, and zero formal
observations. `test_zero_formal_observations` and
`test_result_manifest_refuses_incomplete_evidence` are preparation assertions.

## POST_EXECUTION

After separately authorized execution, the two preparation assertions remain
unchanged and are reported as `EXPECTED_LIFECYCLE_TRANSITION`. They are not
skipped, rewritten, or represented as passing. The independent
`validate_round4_postexecution.py` then requires exactly 24 immutable requests
and raw runs, 12 per arm, bounded attempts, exact model/protocol bindings,
canonical rating reconstruction, metrics/report evidence, and a result
manifest.

## PREPUBLICATION and PUBLICATION

Before result evidence exists, `validate_round4_publication.py` validates the
frozen disclosure templates and manifest architecture only and reports
`PREPUBLICATION`. After an additive publication manifest exists, it validates
the frozen protocol/result bindings, disclosure artifacts, and byte-preserved
combined logs without modifying result evidence.

Any incomplete intermediate state is `INCOMPLETE_FAIL_CLOSED`, never PASS.

