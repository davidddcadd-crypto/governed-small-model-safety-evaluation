# Round 5A additive post-execution custody disclosure

Round 5A completed all 24 prespecified `granite4:3b` observations as 24 first
attempts: 12 Arm A and 12 Arm B. No transport retry or selective rerun
occurred. This additive disclosure does not interpret or change the scientific
result and does not authorize surrogate rating or publication.

## R5A-RUN-016 custody correction

The formal runner continued normally after `R5A-RUN-016` and completed all 24
observations. A provisional orchestration inference nevertheless described the
runner as interrupted. The resulting
`R5A-RUN-016-INTERRUPTION-CUSTODY.json` record is preserved for auditability
but is **rejected and non-authoritative**.

Before the continuing-run timestamps were reconciled, the already-existing
`R5A-RUN-016.json` raw-run file was unnecessarily written again using the
deterministic first-attempt data. The post-write file was byte-identical at
SHA-256
`e8b8dbf2e58cdc70ee01496779a0128428e2da15bcbfb50ee20ca7cc373af9bd`.
The untouched first-attempt artifact retains the original API body and binds
the same response. No second model request, model rerun, response change,
selective regeneration, format repair, or parser rescue occurred.

The authoritative additive correction is
`R5A-RUN-016-INTERRUPTION-CUSTODY-CORRECTION.json`, SHA-256
`c73b505506df2fcfb00ff9592615e39c744d42e78d14dfcb2ca70af87036d0c6`.

## Lifecycle reconciliation

The frozen preparation architecture had already identified these future
transitions:

1. `tests/test_round5_preparation.py::test_zero_formal_observations`
2. `tests/test_round5_preparation.py::test_result_manifest_refuses_incomplete_evidence`

The completed formal execution exposed one additional preparation-only
assertion:

3. `tests/test_round5_preparation.py::test_lifecycle_architecture_is_frozen`

The third test invokes the `PRE_EXECUTION`-only architecture gate. Its failure
after the authorized lifecycle transition is recorded as
`EXPECTED_LIFECYCLE_TRANSITION`; the frozen test and validators remain
unchanged. This classification changes no case, prompt, model response,
rating semantics, metric, or prespecified signal criterion.

## Scope and external activity

The frozen protocol, 24 formal observations and attempts, consolidated result,
Stage-1 prompt, blinded Stage-1 payload, runtime schema, blinding key, and all
prior-round evidence remain unchanged. No OpenAI transmission, Sol session,
formal rating, Stage-2 construction, commit, push, tag, release, or publication
occurred during this repair.
