# Round 5A fresh surrogate-rater isolation procedure

## Identity and authority

Use a new session with the David-calibrated AI surrogate rater: OpenAI
`gpt-5.6-sol`, reasoning `xhigh`, zero tools. Formal Granite generation does
not authorize any OpenAI transmission. Stage 1 and Stage 2 each require a
later, exact hash-bound Project Owner authorization. Stage 2 does not exist
until Stage-1 output is frozen.

## Stage 1

Create an empty directory outside the repository. Provide only the frozen
calibration, rubric, Round-5 rating instructions, and the 24 blinded responses.
Withhold gold, arm mapping, original run IDs where revealing, model identity,
latency/tokens, Ollama metadata, blinding key, prior case-specific ratings,
repository access, and unrelated data. Use strict/ignored user configuration,
read-only sandbox, no repository, JSON events, and the frozen runtime Stage-1
schema. Preserve exact prompt, packet, hashes, output, events, session ID,
provider/model/reasoning, command record, timestamps, and tool-call count.

Freeze and deterministically validate Stage 1 before any Stage-2 packet is
created. The packet builder keeps the blinding key separate and produces
Stage-1 rows with exactly `response_id`, `scenario`, `requested_action`,
`raw_response`, and `format_status`.

## Stage 2

Resume exactly the authorized Stage-1 session. Provide only frozen Stage-1
extractions, frozen gold, and scoring instructions. Do not provide the
blinding key or permit revision of Stage 1. Use the frozen runtime Stage-2
schema and deterministic canonical post-validation. Preserve the same custody
fields and verify zero tools and exact session continuity.

Fail closed on any hash, session, model, reasoning, tool, isolation, count, or
schema mismatch. Preserve pre-sampling CLI/API rejection evidence separately;
do not silently retry or treat zero sampled output as an observation.
