# Round 5A lifecycle-aware validation plan

`PRE_EXECUTION` is governed by `validate_round5_preparation.py`: exact
source/model/protocol bindings and zero formal observations. Two preparation
assertions are prospectively lifecycle-bound:

- `test_zero_formal_observations`
- `test_result_manifest_refuses_incomplete_evidence`

After separately authorized complete execution, these immutable assertions are
reported as `EXPECTED_LIFECYCLE_TRANSITION`; they are not rewritten or called
passing. The already-frozen independent `validate_round5_postexecution.py`
then governs 24 requests/raw runs, 12 per arm, bounded attempts, exact model
and protocol custody, rating reconstruction, metrics/report, and the result
manifest. Result-dependent publication artifacts are deferred until evidence
exists. Every incomplete intermediate state is `INCOMPLETE_FAIL_CLOSED`.
