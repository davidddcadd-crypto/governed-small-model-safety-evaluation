# v0.6.0 — Granite 4 3B Round 5A Replication

This release publishes exactly one prespecified within-model Arm A/B
replication using the Ollama model `granite4:3b`. It is a replication attempt,
not an attempt to obtain a positive result.

## Design and prespecified result

Round 5A used 12 frozen synthetic safety cases, one observation per case-arm,
for 24 formal observations and no repeated trials. All 24 observations were
eligible. The prespecified result was **SUPPORTIVE**.

The label was reached narrowly: Arm B gained exactly two Strict Safety Passes,
while Unsafe Allows did not increase and Hard Failures did not increase. A
SUPPORTIVE label does not mean that every safety or operational metric
improved, or that unsafe behavior was absent.

| Metric | Arm A | Arm B |
|---|---:|---:|
| Strict Safety Pass | 25.0% (3/12) | 41.7% (5/12) |
| Exact Decision Accuracy | 75.0% (9/12) | 91.7% (11/12) |
| Unsafe Allow | 12.5% (1/8) | 12.5% (1/8) |
| Escalation Recall | 50.0% (2/4) | 75.0% (3/4) |
| False Refusal | 25.0% (1/4) | 0.0% (0/4) |
| Format Failure | 41.7% (5/12) | 0.0% (0/12) |
| Mean Quality | 7.67 | 8.42 |
| Hard Failures | 2 | 2 |

Paired Strict Safety Pass outcomes were 2 improved, 10 unchanged, and 0
worsened. Paired quality outcomes were 4 improved, 8 unchanged, and 0
worsened.

## Positive, negative, and mixed findings

Arm B had higher Strict Safety Pass, Exact Decision Accuracy, Escalation
Recall, and Mean Quality, and fewer false refusals. Arm B also used more prompt
tokens and generated tokens and had higher mean client-wall and total latency.

One Unsafe Allow and two Hard Failures remained in each arm. Each arm's Hard
Failures comprised one `DUPLICATE_IRREVERSIBLE_ACTION` and one
`UNAUTHORIZED_ALLOW`. Arm B still missed one of four required escalations and
passed strictly on only 5 of 12 observations.

All five `FORMAT_FAIL` observations were in Arm A and were preserved as
observed. No output-format repair, model-specific parser rescue, selective
format normalization, omission, selective rerun, selective regeneration, or
equivalent repair was applied to any formal Granite 4 Round-5 observation.
Improved formatting is not itself treated as evidence of safety improvement.

The preserved interruption inference for R5A-RUN-016 was rejected as
non-authoritative. Its raw-run file was unnecessarily rewritten with
byte-identical content; no second model request, rerun, response change, or
selective regeneration occurred.

## Surrogate-rating and lifecycle custody

Ratings came from a David-calibrated OpenAI `gpt-5.6-sol` `xhigh` AI surrogate
rater under the frozen two-stage procedure. This was not a human rater,
human-equivalent judgment, ground truth, or an independent expert. Stage 1
performed blinded decision extraction before gold disclosure. Stage 2 resumed
that exact frozen session for scoring without revising Stage-1 extraction.
Both sampled event streams contained zero tool calls.

The additive lifecycle record distinguishes preparation, formal execution,
Stage-1 completion, Stage-2 completion, core-result freeze, and publication
packaging. Ten earlier preparation or absence assertions are preserved as
`EXPECTED_LIFECYCLE_TRANSITION`; frozen tests were not modified. No additional
lifecycle exception was required for publication packaging.

Targeted Round-5 `.gitattributes` rules preserve the byte-sensitive evidence
classes; the public root `.gitattributes` was not modified. The intentionally
excluded local `results/ratings_primary.partial.jsonl` checkpoint is not part
of this release.

## Limits and claim boundaries

This is a small synthetic sample: 12 cases, one observation per case-arm, 24
observations, and no repeated trials. No statistical significance is claimed.
Cross-round comparisons are descriptive and confounded by model family, model
implementation, and chat-template differences; this is not a controlled
cross-model comparison.

The result does not establish production safety, frontier-model equivalence,
model-family generalization, or proof that governance works generally.
