# Round 3A Granite 4.1 3B governed safety replication

## Design and rater disclosure

This direct replication contains 12 synthetic cases, one observation per
case-arm, and 24 total observations. Primary rating used a David-calibrated AI
surrogate rater (OpenAI `gpt-5.6-sol`, `xhigh`), not a human rater or ground
truth. The exact frozen Round-2 David calibration was reused.

## Within-Granite results

| Metric | Arm A | Arm B |
|---|---:|---:|
| Strict Safety Pass | 8.3% (1/12) | 33.3% (4/12) |
| Exact Decision Accuracy | 58.3% | 66.7% |
| Unsafe Allow | 0.0% | 0.0% |
| Escalation Recall | 0.0% | 25.0% |
| False Refusal | 25.0% | 25.0% |
| Format Failure | 0.0% | 8.3% |
| Mean Quality | 7.50 | 8.25 |
| Hard Failures | 0 | 0 |

Prespecified signal: **SUPPORTIVE**.

## Required limitations

All positive, negative, mixed, null, and worse findings remain evidence. API
schema preflights and any pre-sampling rejections are disclosed separately.
Phi/Ministral/Granite comparisons are descriptive, not controlled: model
family, chat template, and model implementation differ. These 24 synthetic
observations do not establish statistical significance, production safety,
model-family generalization, frontier equivalence, or proof that governance
works generally.
