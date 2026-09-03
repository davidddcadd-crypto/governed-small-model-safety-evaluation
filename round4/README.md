# Round 4A preparation package

This directory freezes the preparation-only protocol for the direct
`llama3.2:3b-instruct-q4_K_M` replication. It creates no formal observation and grants no
authority to transmit a Llama response to the OpenAI surrogate.

The frozen Round-1 cases, gold, prompts, format contract, rubric, and run order
are reused only by exact hash. The frozen Round-2 David calibration is reused
by exact hash. Round-1, Round-2, and Round-3 evidence remain immutable.

Preparation and post-execution validation are separate from the start. The
preparation assertion of zero observations is frozen historical evidence and
becomes `EXPECTED_LIFECYCLE_TRANSITION` only after separately authorized
execution; it is never rewritten. Public-checkout validation never requires
the intentionally excluded local checkpoint.

Formal execution requires a separate Project Owner authorization bound to
`round4/round4_protocol_manifest_v3.json`. The earlier v1 and v2 manifests are
preserved as rejected pre-authorization freezes and are not authorizable.
Surrogate transmission requires the later, stage-specific authorization
receipts described in `RATER_ISOLATION_PROCEDURE.md`.
