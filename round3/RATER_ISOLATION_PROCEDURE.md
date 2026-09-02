# Round 3A fresh surrogate-rater isolation procedure

## Fixed identity and separate authority

Rater label: **David-calibrated AI surrogate rater**. Provider: OpenAI.
Required model: `gpt-5.6-sol`. Required reasoning: `xhigh`. This is not a
human rating. Current preparation verified Codex CLI `0.152.0` and official
model support for `xhigh`.

Formal Granite generation authority does not authorize any OpenAI
transmission. The surrogate workflow requires later, stage-specific Project
Owner authorizations. Stage 2 cannot be authorized by hash until Stage 1 is
preserved and the Stage-2 packet exists.

## Isolation

Create a new empty directory outside the repository and start a new Sol xhigh
session. Pipe only permitted material through standard input. Do not provide a
repository path. Use `--strict-config`, `--ignore-user-config`,
`--ignore-rules`, `--sandbox read-only`, `--skip-git-repo-check`, and JSON
events. Do not use `--ephemeral`, because Stage 2 must resume the exact Stage-1
session. Preserve exact prompts, payloads, event logs, raw outputs, command
lines, timestamps, session ID, provider/model/reasoning, CLI version, and tool
call count.

Fail closed if the event log shows any tool/file access, the resolved model or
reasoning differs, the session changes, a response set is incomplete, Stage 1
is revised after gold disclosure, or a hash does not match.

Never transmit the Round-3 blinding key, arm mapping, model identity where
blindness requires withholding it, Round-2 case-specific ratings, Round-1
per-response ratings, latency/token metadata, repository access, or unrelated
project/user data.

## Stage 1: extraction before gold

After 24 immutable formal runs, build and freeze the packet. Stage 1 may receive
only the frozen David calibration, frozen rubric, Round-3 rating instructions,
and 24 blinded Granite responses. It receives no gold, arm identity, case/run
mapping, or hypothesis direction.

Use the accepted runtime extraction schema, not the canonical schema file:

```powershell
codex exec --model gpt-5.6-sol -c 'model_reasoning_effort="xhigh"' --strict-config --ignore-user-config --ignore-rules --sandbox read-only --skip-git-repo-check --json --output-schema runtime_surrogate_extraction_output.schema.json --output-last-message stage1_raw_output.json --cd EMPTY_ISOLATED_DIRECTORY -
```

Preserve and deterministically validate Stage 1 before creating Stage 2.

## Stage 2: gold-disclosed scoring

Only after Stage 1 is frozen and separately validated may the Stage-2 packet be
created and independently authorized. Stage 2 may receive only the frozen
Stage-1 extractions, frozen gold records, and detailed scoring instructions.
It resumes the exact session and never receives the blinding key.

```powershell
codex exec resume --all --model gpt-5.6-sol -c 'model_reasoning_effort="xhigh"' --strict-config --ignore-user-config --ignore-rules --json --output-schema runtime_surrogate_scoring_output.schema.json --output-last-message stage2_raw_output.json SESSION_ID -
```

The runtime schema's omission of `uniqueItems` changes no scoring meaning;
canonical post-validation rejects duplicate hard-failure values.

## Exact later authorization statements

Formal generation receipt statement:

> I, David / Tai Wai Lee, Project Owner, explicitly authorize the 24 formal Round 3A observations using granite4.1:3b under the frozen Round-3 protocol manifest identified by authorized_protocol_manifest_sha256. I authorize no surrogate-rating transmission, formal rating, change to frozen Round-1 or Round-2 evidence, selective rerun, publication, commit, push, tag, or release.

Stage-1 transmission receipt statement:

> I, David / Tai Wai Lee, Project Owner, explicitly authorize transmission of exactly the frozen Round-3 Stage-1 blinded surrogate-rating prompt and payload identified by their authorized SHA-256 values to OpenAI's gpt-5.6-sol service for the Sol xhigh decision-extraction procedure. I authorize no transmission of gold records, the blinding key, arm mapping, model identity, Round-2 case-specific ratings, Round-1 per-response ratings, latency/token metadata, repository access, or unrelated data, and no Stage-2 transmission.

Stage-2 transmission receipt statement:

> I, David / Tai Wai Lee, Project Owner, explicitly authorize transmission of exactly the frozen Round-3 Stage-2 gold-disclosed scoring prompt and payload identified by their authorized SHA-256 values to OpenAI's gpt-5.6-sol service by resuming the authorized Stage-1 session at the authorized session ID. I authorize no transmission of the blinding key, arm mapping, model identity, Round-2 case-specific ratings, Round-1 per-response ratings, latency/token metadata, repository access, or unrelated data, and no revision of frozen Stage-1 extractions.
