# Round 5A additive publication and custody disclosure

## Scope and result

This package publishes exactly one prespecified within-model Granite 4 3B
replication using `granite4:3b`: 12 frozen synthetic safety cases, one
observation per case-arm, 12 observations per arm, 24 total observations, and
no repeated trials. All 24 observations remained eligible. The frozen result
is **SUPPORTIVE** under the prespecified rule.

Arm A versus Arm B results were: Strict Safety Pass 3/12 (25.0%) versus 5/12
(41.7%); Exact Decision Accuracy 9/12 (75.0%) versus 11/12 (91.7%); Unsafe
Allow 1/8 versus 1/8; Escalation Recall 2/4 (50.0%) versus 3/4 (75.0%); False
Refusal 1/4 (25.0%) versus 0/4 (0.0%); Format Failure 5/12 versus 0/12; Mean
Quality 7.67 versus 8.42; and Hard Failures 2 versus 2. Paired Strict Safety
Pass outcomes were 2 improved, 10 unchanged, and 0 worsened; paired quality
outcomes were 4 improved, 8 unchanged, and 0 worsened.

The SUPPORTIVE threshold was met narrowly because Arm B gained exactly two
Strict Safety Passes while neither Unsafe Allows nor Hard Failures increased.
One Unsafe Allow and two Hard Failures remained in each arm. Arm B used more
prompt and generated tokens and had higher mean latency.

## Output and observation custody

All five `FORMAT_FAIL` observations were preserved. No output-format repair,
model-specific parser rescue, selective format normalization, omission,
selective rerun, selective regeneration, or equivalent repair was applied.
Improved formatting is not itself treated as safety evidence.

The R5A-RUN-016 interruption inference is rejected and non-authoritative. The
authoritative raw-run file was unnecessarily rewritten with byte-identical
content at SHA-256
`e8b8dbf2e58cdc70ee01496779a0128428e2da15bcbfb50ee20ca7cc373af9bd`.
There was no second model request, rerun, response change, or selective
regeneration.

## Rater and lifecycle custody

Primary rating used a David-calibrated OpenAI `gpt-5.6-sol` `xhigh` AI
surrogate under the frozen two-stage procedure, not a human rater or
independent expert. Stage 1 extracted decisions while gold, arm identity,
model identity, and run metadata were withheld. Stage 2 resumed the same
frozen session and did not revise Stage-1 extraction. Both sampled event logs
contained zero tool calls. Runtime schemas were mechanical compatibility
adapters; canonical schemas and deterministic post-validation remained
authoritative.

The additive lifecycle record preserves ten expected transitions across the
preparation, formal-execution, Stage-1, Stage-2, and core-result gates. The
publication layer adds a `PUBLICATION_PACKAGE_FROZEN` state without changing
any frozen test or reclassifying another assertion. No unanticipated lifecycle
or custody issue was found.

Round-5 scoped `.gitattributes` rules preserve byte-sensitive evidence. The
already-public root `.gitattributes` remains byte-identical and is not part of
the Round-5 commit delta. Clean-checkout validation may omit the intentionally
excluded `results/ratings_primary.partial.jsonl` checkpoint; if present
locally, it must retain its frozen 31,022-byte size and SHA-256.

## Claim boundaries

This is a small synthetic sample with no repeated trials. No statistical
significance, production safety, frontier-model equivalence, model-family
generalization, controlled cross-model comparison, or proof that governance
works generally is claimed. Cross-round results remain descriptive and
confounded by model family, implementation, and chat template.
