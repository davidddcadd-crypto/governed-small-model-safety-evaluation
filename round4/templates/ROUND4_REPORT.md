# Round 4A Llama 3.2 3B direct-replication report

Status: `NOT_YET_EXECUTED`.

This is the frozen canonical report structure, not a result. Populate only from
validated Round-4 evidence after separate execution and rating authorization.

## Design

- 12 synthetic cases.
- One observation per case-arm; 24 total observations.
- No repeated trials and no selective reruns.
- Exact model, generation, prompt, rubric, format, retry, and rater bindings.

## Primary within-Llama results

Report Arm A and Arm B for Strict Safety Pass, Exact Decision Accuracy, Unsafe
Allow, Escalation Recall, False Refusal, Format Failure, Mean Quality, Hard
Failures and types, latency, prompt/generated tokens, categories, and paired
outcomes. State the frozen `SUPPORTIVE`, `NOT_SUPPORTIVE`, or `NOT_EVALUABLE`
result, including negative and mixed findings.

## Descriptive historical context

Phi-4 Round 1, Ministral Round 2A, and Granite Round 3A are descriptive only.
Disclose model-family, implementation, and chat-template confounds. Do not
present a controlled four-model comparison.

## Rater, schema, lifecycle, and custody disclosures

Identify the David-calibrated OpenAI GPT-5.6 Sol xhigh AI surrogate, calibration
provenance, fresh-session two-stage isolation, runtime adapters, excluded
preflights, all schema rejections if any, lifecycle transitions, exact format
and escalation performance, and clean-checkout byte custody.

## Claim boundaries

No statistical significance, production-safety, model-family-generalization,
frontier-equivalence, causal format, controlled cross-model, or general proof
of governance claim is permitted.

