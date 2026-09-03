# v0.5.0 — Llama 3.2 3B Round 4A Replication

This release would publish the prespecified Round 4A within-model Arm A/B
replication using exactly `llama3.2:3b-instruct-q4_K_M`. The release is a
replication attempt, not an attempt to obtain a positive result.

## Design and prespecified result

Round 4A used 12 frozen synthetic cases, one observation per case-arm, for 24
formal observations and no repeated trials. All 24 observations were eligible.
All were first attempts, with no transport retries and no selective reruns.
No output-format repair, model-specific parser repair, selective format
normalization, or equivalent repair was applied to any formal Llama Round-4
observation.
Generation used temperature 0, seed 42, context 4096, prediction limit 512,
no tools, and no conversation history.

The prespecified result was **SUPPORTIVE**. Arm B produced exactly two more
Strict Safety Passes than Arm A, did not increase Unsafe Allows, and reduced
Hard Failures by one.

| Metric | Arm A | Arm B |
|---|---:|---:|
| Strict Safety Pass | 8.3% (1/12) | 25.0% (3/12) |
| Exact Decision Accuracy | 83.3% (10/12) | 91.7% (11/12) |
| Unsafe Allow | 12.5% (1/8) | 12.5% (1/8) |
| Escalation Recall | 50.0% (2/4) | 75.0% (3/4) |
| False Refusal | 0.0% (0/4) | 0.0% (0/4) |
| Format Failure | 8.3% (1/12) | 25.0% (3/12) |
| Mean Quality | 6.83 | 8.00 |
| Hard Failure | 3 | 2 |

Paired Strict Safety Pass outcomes improved for 2 cases, were unchanged for
10, and worsened for 0. Paired quality improved for 7 cases, was unchanged for
5, and worsened for 0.

## Positive, negative, and mixed findings

Arm B improved Strict Safety Pass, Exact Decision Accuracy, Escalation Recall,
and Mean Quality, and had one fewer Hard Failure. These relative improvements
do not imply high absolute safety.

Each arm still produced one Unsafe Allow. Arm B retained two Hard Failures,
missed one of four required escalations, passed strictly on only 3 of 12
observations, and increased Format Failure from 1/12 to 3/12. Arm A hard
failures comprised one `DUPLICATE_IRREVERSIBLE_ACTION`, one
`PROHIBITED_BYPASS_GUIDANCE`, and one `UNAUTHORIZED_ALLOW`; Arm B comprised one
`DUPLICATE_IRREVERSIBLE_ACTION` and one `UNAUTHORIZED_ALLOW`.

Historical format context is descriptive only: Ministral Round 2A had 24/24
format failures, Granite Round 3A had 1/24, and Llama Round 4A had 4/24.

## Surrogate rater and runtime custody

Ratings came from a David-calibrated OpenAI `gpt-5.6-sol` `xhigh` AI surrogate
rater. This was not a human rater, human-equivalent judgment, ground truth, or
an independent expert. The exact frozen David calibration was reused. Stage 1
performed blinded decision extraction before gold disclosure. Stage 2 resumed
the same fresh session after Stage-1 output was frozen. Both sampled event
streams contained zero tool calls.

Canonical rating schemas remained authoritative. The mechanical runtime
adapter added an explicit string type for `stage`; Stage 2 also omitted the
unsupported `uniqueItems` keyword, while deterministic post-validation still
enforced uniqueness. Excluded neutral schema preflights contained no formal
case content, no formal Llama response, and no gold content.

The first authorized Stage-2 resume invocation encountered a preserved
pre-sampling CLI trusted-directory rejection because
`--skip-git-repo-check` was absent. It generated zero event bytes, created no
raw model output, and did not revise Stage-1 extraction. The same authorized
prompt, payload, schema, model, reasoning level, and Stage-1 session succeeded
after adding only the mechanical isolation flag.

Five frozen preparation/lifecycle assertions are disclosed as
`EXPECTED_LIFECYCLE_TRANSITION`; their bytes were not changed. The publication
package also binds the exact `.gitattributes` byte-preservation rules needed to
retain the frozen CRLF probe in a clean checkout. The intentionally excluded
local `results/ratings_primary.partial.jsonl` checkpoint is not published; if
present locally it must retain its frozen 31,022-byte size and SHA-256.

## Limits and claim boundaries

This is a small synthetic sample: 12 cases, one observation per case-arm, and
no repeated trials. No statistical significance is claimed. Phi-4, Ministral,
Granite, and Llama differ in model family, implementation, and chat template,
so cross-model comparisons are descriptive and confounded rather than
controlled. Holding the surrogate-rater regime constant improves procedural
comparability but does not remove those confounds.

The result does not establish production safety, frontier-model equivalence,
model-family generalization, or proof that governance works generally.
