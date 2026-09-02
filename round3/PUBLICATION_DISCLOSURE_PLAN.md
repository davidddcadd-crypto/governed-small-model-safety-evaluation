# Round 3A publication disclosure plan

This plan is frozen before formal execution. It does not authorize publication.

Any future public report, addendum, release notes, and publication validator
must prominently disclose:

- 12 synthetic cases, one observation per case-arm, and 24 total observations;
- every exact positive, negative, mixed, null, and worse result;
- exact Strict Safety Pass, Exact Decision Accuracy, Unsafe Allow, Escalation
  Recall, False Refusal, Format Failure, Mean Quality, and Hard Failure results;
- hard failures by frozen type, category results, and paired A/B outcomes;
- the prespecified `SUPPORTIVE`/`NOT_SUPPORTIVE`/`NOT_EVALUABLE` result;
- the **David-calibrated AI surrogate rater** method and exact frozen
  calibration provenance, while denying human-rating or ground-truth status;
- the runtime-schema adapter, excluded schema preflights, and every future
  pre-sampling rejection event, whether or not sampling occurred;
- the Granite model identity and model-specific chat-template change;
- within-Granite A/B as the primary inference, Round 2A versus Round 3A as
  descriptive context, and Round 1 as historical context;
- sample-size and single-observation limitations plus all cross-model confounds;
- no statistical-significance, production-safety, model-family-generalization,
  frontier-equivalence, controlled cross-model-comparison, or general proof of
  governance claim.

Publication custody must use an additive manifest that binds the frozen result
manifest plus disclosure-only artifacts. Frozen result evidence must never be
edited to repair a publication disclosure.
