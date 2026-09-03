# Round 5A runtime-schema compatibility contract

Round 5 reuses the proven Round-4 mechanical adapter while canonical schemas
remain authoritative:

- Stage 1 adds only `"type": "string"` beside the `stage` constant.
- Stage 2 makes that same addition and omits only unsupported `uniqueItems`
  from the runtime hard-failures array.
- Deterministic canonical post-validation still rejects duplicate hard-failure
  values and enforces every frozen scoring constraint.

These adapters do not change formal model outputs, gold, response identity,
rating dimensions, bounds, enums, scoring, strict-pass logic, or evidence
requirements. A later excluded compatibility preflight, if required before an
authorized rating stage, must use neutral placeholders with no formal cases,
gold, Granite output, prompts, or David calibration. Any pre-sampling
rejection and zero sampled output must be preserved distinctly and is never a
formal observation or rating. No OpenAI preflight or transmission occurs in
this preparation.
