# Round 3A runtime-schema compatibility contract

Round 2 preserved two pre-sampling API schema rejections:

1. Stage 1 rejected a `stage` constant without an explicit `type`.
2. Stage 2 rejected the unsupported `uniqueItems` keyword.

Round 3 therefore freezes separate canonical and runtime schemas. The adapter
is mechanical and meaning-preserving:

- add `"type": "string"` beside each `stage` constant;
- remove only `uniqueItems` from the runtime hard-failures array;
- retain hard-failure uniqueness in deterministic canonical post-validation;
- make no change to response IDs, rating dimensions, bounds, enums, required
  properties, array length, scoring, strict-pass logic, or evidence rules.

The excluded preflight uses placeholder IDs and neutral dummy content only. It
must contain none of the 12 case IDs, scenarios, requested actions, expected
decisions, source prompts, Granite formal responses, or David calibration. Its
outputs are schema-compatibility evidence, not formal observations, Stage-1
extractions, Stage-2 scores, or canonical ratings.

Any future API schema rejection is preserved immediately in the Round-3
namespace. A pre-sampling rejection is not a model observation. If repair would
change evaluation meaning, stop and require a new frozen protocol.
