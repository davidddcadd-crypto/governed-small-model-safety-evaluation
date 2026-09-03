# Round 5A Granite 4 3B governed safety replication

## Design and rater disclosure

This direct replication contains 12 synthetic cases, one observation per
case-arm, and 24 total observations, with no repeated trials. Primary rating used a David-calibrated AI
surrogate rater (OpenAI `gpt-5.6-sol`, `xhigh`), not a human rater or ground
truth. The exact frozen Round-2 David calibration was reused.

## Within-Granite 4 results

| Metric | Arm A | Arm B |
|---|---:|---:|
| Strict Safety Pass | 25.0% (3/12) | 41.7% (5/12) |
| Exact Decision Accuracy | 75.0% | 91.7% |
| Unsafe Allow | 12.5% | 12.5% |
| Escalation Recall | 50.0% | 75.0% |
| False Refusal | 25.0% | 0.0% |
| Format Failure | 41.7% | 0.0% |
| Mean Quality | 7.67 | 8.42 |
| Hard Failures | 2 | 2 |

Prespecified signal: **SUPPORTIVE**.

The label is prespecified and narrow: all 24 observations were eligible, Arm B
had exactly two more Strict Safety Passes than Arm A, and Arm B did not increase
Unsafe Allows or Hard Failures. It does not mean that every safety or operational
metric improved.

## Positive, negative, and mixed findings

- Strict Safety Pass increased from 3/12 to 5/12; Exact Decision Accuracy rose
  from 75.0% to 91.7%; Escalation Recall rose from 50.0% to 75.0%; and False
  Refusal fell from 1/4 to 0/4.
- One Unsafe Allow remained in each arm. Hard Failures remained at two per arm:
  one `DUPLICATE_IRREVERSIBLE_ACTION` and one `UNAUTHORIZED_ALLOW` in each.
- There were five `FORMAT_FAIL` observations in total: Arm A 5/12 and Arm B
  0/12. All malformed outputs remain included exactly as observed. No
  model-specific output repair, parser rescue, selective format normalization,
  or selective rerun was applied. Better format adherence is not, by itself,
  evidence of improved safety.
- Paired Strict Safety Pass outcomes were 2 improved, 10 unchanged, and 0
  worsened. Paired quality outcomes were 4 improved, 8 unchanged, and 0
  worsened.
- Mean Quality increased from 7.67 to 8.42, while Arm B also used more prompt
  and generated tokens and had higher mean client-wall and total duration.

R5A-RUN-016's preserved interruption record is rejected and non-authoritative.
Its raw-run file was unnecessarily rewritten with byte-identical content at
SHA-256 `e8b8dbf2e58cdc70ee01496779a0128428e2da15bcbfb50ee20ca7cc373af9bd`.
No second model request, rerun, response change, or selective regeneration
occurred.

## Required limitations

All positive, negative, mixed, null, and worse findings remain evidence. API
schema preflights and any pre-sampling rejections are disclosed separately.
Phi/Ministral/Granite 4.1/Llama/Granite 4 comparisons are descriptive, not controlled: model
family, chat template, and model implementation differ. These 24 synthetic
observations do not establish statistical significance, production safety,
model-family generalization, frontier equivalence, or proof that governance
works generally.
