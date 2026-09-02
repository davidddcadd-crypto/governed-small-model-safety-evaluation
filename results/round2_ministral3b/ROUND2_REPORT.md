# Round 2A governed small-model safety replication

## Rater disclosure

Primary Round-2 rating: David-calibrated AI surrogate rater (OpenAI
`gpt-5.6-sol`, `xhigh`). This is not a human rating or ground truth.

## Within-Round-2 results

| Metric | Arm A | Arm B |
|---|---:|---:|
| Strict Safety Pass | 33.3% (4/12) | 66.7% (8/12) |
| Exact Decision Accuracy | 75.0% | 83.3% |
| Unsafe Allow | 0.0% | 0.0% |
| Format Failure | 100.0% | 100.0% |
| Mean Quality | 8.17 | 8.92 |
| Hard Failures | 1 | 0 |

Prespecified replication signal: **SUPPORTIVE**.

## Cross-round limitation

The Phi-4 Mini and Ministral results are descriptive, not a controlled model
comparison. Model family/chat template and primary rater type both change.

## Reporting limits

These 24 synthetic observations do not establish statistical significance,
production safety, model-family generalization, frontier-model equivalence, or
proof that governed small models are safer. Null, negative, mixed, and format
failures remain part of the evidence.
