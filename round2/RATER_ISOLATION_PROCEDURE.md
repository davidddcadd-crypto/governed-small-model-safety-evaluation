# Round 2A surrogate-rater isolation procedure

## Disclosure and fixed identity

Rater label: **David-calibrated AI surrogate rater**. Provider: OpenAI.
Required model: `gpt-5.6-sol`. Required reasoning: `xhigh`. This is not a
human rating.

Preparation verified Codex CLI `0.152.0`; its bundled catalog lists the
required model and reasoning setting. Official OpenAI documentation also lists
`gpt-5.6-sol` with `xhigh` reasoning.

## Isolation rules

Start a new session after calibration is frozen. Use a newly created empty
working directory outside the repository. Pipe permitted material through
standard input; do not give repository paths to the rater. Disable user
configuration and project rules, use a read-only sandbox, and prohibit tools
in the prompt. Preserve `--json` events and raw final output. Fail if the
event log contains any tool/file access.

Never provide source ratings, case/response mappings, the blinding key, arm
information, model output order, hypothesis direction, latency, tokens, or
gold before Stage 1 is frozen.

## Stage 1: extraction before gold

After 24 immutable runs:

```powershell
python -B scripts/build_round2_rating_packets.py stage1
```

Construct stdin from the exact calibration, rubric, rating instructions, and
`blinded_extraction_packet.jsonl`. Launch:

```powershell
codex exec --model gpt-5.6-sol -c 'model_reasoning_effort="xhigh"' --strict-config --ignore-user-config --ignore-rules --sandbox read-only --skip-git-repo-check --json --output-schema surrogate_extraction_output.schema.json --output-last-message stage1_raw_output.json --cd EMPTY_ISOLATED_DIRECTORY -
```

Preserve the command, stdin hash, event log, raw output, timestamps, CLI
version, and returned session ID. Do not use `--ephemeral`, because Stage 2
must resume this exact session.

After validating Stage 1:

```powershell
python -B scripts/build_round2_rating_packets.py stage2 --extractions stage1_raw_output.json
```

## Stage 2: gold-disclosed scoring

Resume the same session. Stdin contains only the Stage-2 instruction and
`blinded_scoring_packet.jsonl`:

```powershell
codex exec resume --all --model gpt-5.6-sol -c 'model_reasoning_effort="xhigh"' --strict-config --ignore-user-config --ignore-rules --json --output-schema surrogate_scoring_output.schema.json --output-last-message stage2_raw_output.json SESSION_ID -
```

The blinding key remains withheld and Stage 2 cannot revise extraction.
Preserve prompts, event logs, raw outputs, and complete session metadata, then
construct canonical ratings:

```powershell
python -B scripts/validate_round2_ratings.py --extractions stage1_raw_output.json --scores stage2_raw_output.json --session rater_session.json --output ratings_surrogate.jsonl
```

Any model/reasoning mismatch, tool event, missing hash, incomplete response
set, or changed extraction invalidates the rating session.
