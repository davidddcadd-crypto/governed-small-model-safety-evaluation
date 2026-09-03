# Round 4A publication disclosure plan

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
- the Llama model identity and model-specific chat-template change;
- within-Llama A/B as the primary inference, with Phi-4 Round 1, Ministral
  Round 2A, and Granite Round 3A as descriptive historical context only;
- no repeated trials, exact lifecycle state, and clean-checkout custody that
  does not depend on the excluded local checkpoint;
- sample-size and single-observation limitations plus all cross-model confounds;
- no statistical-significance, production-safety, model-family-generalization,
  frontier-equivalence, controlled cross-model-comparison, or general proof of
governance claim.

The canonical templates are frozen under `round4/templates/`. Future completed
reports must fill every placeholder from validated evidence; leaving a required
disclosure unresolved is a publication failure, not editorial discretion.

Publication custody must use an additive manifest that binds the frozen result
manifest plus disclosure-only artifacts. Frozen result evidence must never be
edited to repair a publication disclosure.
