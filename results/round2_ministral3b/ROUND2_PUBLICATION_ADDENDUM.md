# Round 2A publication addendum

This additive publication record supplements, but does not replace or modify,
the frozen 92-file Round 2A result set. Round 2A is the second prespecified
within-model Arm A/B evaluation and a cross-model replication attempt using
`ministral-3:3b`.

## Study design

The evaluation used 12 synthetic cases, with one observation per case-arm and
24 total formal observations. All 24/24 responses were `FORMAT_FAIL` under the
frozen output contract. Format failure is reported separately from the
substantive decision and safety ratings.

## Positive findings

- Strict Safety Pass: 33.3% -> 66.7%.
- Exact Decision Accuracy: 75.0% -> 83.3%.
- Unsafe Allow: 0 -> 0.
- Hard Failures: 1 -> 0.
- Prespecified signal: `SUPPORTIVE`.

## Negative and mixed findings

- Escalation Recall: 100% -> 75%.
- `FORMAT_FAIL`: 100% -> 100%.
- Arm B produced one false refusal.
- Arm A produced one `PROHIBITED_BYPASS_GUIDANCE` hard failure.

## Rater disclosure

The Round 1 primary rater was David / Tai Wai Lee, human. Round 2 used a
David-calibrated OpenAI `gpt-5.6-sol` xhigh AI surrogate. The surrogate is not
human-equivalent, is not ground truth, and is not an independent human expert.

No per-response Round-1 ratings, blinding key, arm mapping, latency/token
metadata, or repository access reached the surrogate rater. The permitted
calibration did contain Round-1-derived aggregate information and the source
ratings filename and SHA-256; this aggregate calibration was disclosed to the
surrogate before rating.

## Cross-round limitation

The model family changed, the model-specific chat template changed, and the
primary rater type changed. Round 1 versus Round 2 is therefore not a
controlled model comparison.

## Pre-sampling API schema rejections

Two API schema requests were rejected before model sampling. The Stage 1
request was rejected because the `stage` property lacked an explicit `type`.
The Stage 2 request was rejected because `uniqueItems` was unsupported. Neither
rejected request produced sampled model output: each preserved event log ends
with `turn.failed` and contains no `item.completed` event.

Only isolated runtime-schema compatibility hints changed. The frozen
evaluation schemas, scoring semantics, canonical rating records, and
deterministic post-validation did not change. Exact rejection event bytes and
their provenance are preserved under `publication_disclosures/` and bound by
`PUBLICATION_MANIFEST.json`.

## Claim boundaries

These 24 synthetic observations do not establish statistical significance,
production safety, model-family generalization, frontier equivalence, proof
that governance works generally, or a controlled Round-1/Round-2 comparison.
