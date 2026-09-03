# Round 4A Llama 3.2 3B governed safety replication

## Design and rater disclosure

This direct replication contains 12 synthetic cases, one observation per
case-arm, and 24 total observations, with no repeated trials. Primary rating used a David-calibrated AI
surrogate rater (OpenAI `gpt-5.6-sol`, `xhigh`), not a human rater or ground
truth. The exact frozen Round-2 David calibration was reused.

## Within-Llama results

| Metric | Arm A | Arm B |
|---|---:|---:|
| Strict Safety Pass | 8.3% (1/12) | 25.0% (3/12) |
| Exact Decision Accuracy | 83.3% | 91.7% |
| Unsafe Allow | 12.5% | 12.5% |
| Escalation Recall | 50.0% | 75.0% |
| False Refusal | 0.0% | 0.0% |
| Format Failure | 8.3% | 25.0% |
| Mean Quality | 6.83 | 8.00 |
| Hard Failures | 3 | 2 |

Prespecified signal: **SUPPORTIVE**.

## Required limitations

All positive, negative, mixed, null, and worse findings remain evidence. API
schema preflights and any pre-sampling rejections are disclosed separately.
Phi/Ministral/Granite/Llama comparisons are descriptive, not controlled: model
family, chat template, and model implementation differ. These 24 synthetic
observations do not establish statistical significance, production safety,
model-family generalization, frontier equivalence, or proof that governance
works generally.
