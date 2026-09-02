# Round 3A publication addendum

This additive publication record supplements, but does not replace or modify,
the frozen 94-file Round 3A result set. Round 3A is the Granite 4.1 3B
within-model Arm A/B replication.

## Study design

The evaluation used 12 synthetic cases, with one observation per case-arm and
24 total formal observations. There were no repeated trials, no transport
retries, and no selective observation reruns.

## Results

| Metric | Arm A | Arm B |
|---|---:|---:|
| Strict Safety Pass | 8.3% (1/12) | 33.3% (4/12) |
| Exact Decision Accuracy | 58.3% (7/12) | 66.7% (8/12) |
| Unsafe Allows | 0 | 0 |
| Escalation Recall | 0% (0/4) | 25% (1/4) |
| False Refusals | 25% (1/4) | 25% (1/4) |
| Format Failures | 0/12 | 1/12 |
| Mean Quality | 7.50 | 8.25 |
| Hard Failures | 0 | 0 |

Overall format status was 23 `VALID_JSON` / 1 `FORMAT_FAIL`. The paired strict
outcomes were 3 improved, 9 unchanged, and 0 worsened. The prespecified result
was `SUPPORTIVE`.

## Absolute-performance warning

Escalation performance remained poor in absolute terms. Seven of eight
expected-escalation observations were not extracted as `ESCALATE`.
`SUPPORTIVE` is a frozen relative within-round criterion and is not equivalent
to high absolute safety.

## Format context

Ministral Round 2A had 24/24 `FORMAT_FAIL`; Granite Round 3A had 1/24
`FORMAT_FAIL`. This contrast is descriptive only. It does not establish that
Granite is globally safer or better, and it supports no causal inference.

## Rater disclosure

The Round 1 primary rater was David / Tai Wai Lee, human. Round 2A and Round 3A
used a David-calibrated OpenAI `gpt-5.6-sol` xhigh AI surrogate. The surrogate
is not human-equivalent, is not ground truth, and is not an independent human
expert.

Round 3 used fresh session `01a0645d-b07a-7241-b938-6d0399a626fe`. Stage 1
was frozen before gold disclosure. Stage 1 completed 24/24 decision
extractions; Stage 2 completed 24/24 gold-disclosed scores. Tool calls were 0
and formal schema rejections were 0. The blinding key and arm mapping were
withheld. Granite model identity and runtime metadata were withheld from
rating. No prior-round per-response ratings or case mappings were provided.

## Calibration provenance

The frozen David calibration included Round-1-derived aggregate information.
It identified source ratings file `results/ratings_primary.jsonl` at SHA-256
`114e940605fc0cdca16969e3abd6c8600ca1d2967bbe464d38619c769486265f`.
The disclosed aggregates were: Risk Recognition 1 in 13 ratings and 2 in 11;
8 strict passes and 16 non-passes; 23 format failures and 1 valid format; and
0 hard failures. It contained no Round-1 response identifiers, case
identifiers, per-case outcomes, required-finding lookup table, arm mapping, or
answer key. This study therefore does not claim that no Round-1-derived
information was provided.

## Runtime-schema compatibility and excluded preflights

Canonical and runtime schemas were separate. The Stage-1 runtime adapter added
an explicit string type for `stage`; the Stage-2 runtime adapter also omitted
unsupported `uniqueItems`. Canonical uniqueness and deterministic
post-validation remained enforced, so canonical scoring meaning was unchanged.

Excluded neutral case-free preflights occurred before formal rating. They
contained no formal Granite responses, formal cases, gold records, or David
calibration content. They used zero tools, incurred no schema rejection, and
were excluded from formal observations and ratings.

## Historical preparation-test lifecycle transition

The frozen preparation suite correctly asserted zero formal observations and
an incomplete result set before execution. Following separately authorized
formal execution and rating, its immutable tests
`test_zero_formal_observations` and
`test_result_manifest_refuses_incomplete_evidence` now fail as
`EXPECTED_LIFECYCLE_TRANSITION`. They are disclosed as historical-state
failures; they were not skipped, rewritten, or represented as passing.

## Claim boundaries

These 24 synthetic observations do not establish statistical significance,
production safety, model-family generalization, frontier equivalence, a
controlled three-model comparison, causation from format differences, or proof
that governance works generally. Cross-model Phi-4, Ministral, and Granite
context is descriptive and confounded by model family, chat template, and
model implementation. The primary inference is the within-Granite Arm A/B
comparison.
