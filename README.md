# Governed Small-Model Safety Evaluation

This repository contains a preregistered exploratory pilot testing whether a fixed, structured governance workflow improves the safety decisions of the same small local language model on synthetic action-risk scenarios.

The comparison is intentionally narrow:

- **Arm A — Minimal single-pass decision:** the model receives the case, decision definitions, and output contract.
- **Arm B — Governed single-pass decision:** the same model receives the same case and output contract plus a fixed sequence of risk, authority, evidence, reversibility, duplication, and safe-next-action checks.

No real email, payment, deletion, deployment, credential, personal data, external tool, or irreversible action is used. All cases are synthetic. The pilot does not establish that the model or workflow is safe for deployment.

## Release plan

- `v0.1.0 — Frozen Pilot Protocol and Safety Case Set`: protocol, cases, gold records, prompts, schemas, scoring rules, execution order, and environment plan frozen before formal model runs.
- `v0.2.0 — First Governed Small-Model Safety Pilot`: immutable raw outputs, ratings, analysis, and a limitations-first pilot report.
- `v0.3.0 — Ministral-3 3B Round 2A Replication`: published additive cross-model replication evidence and publication disclosures.
- `v0.4.0 — Granite 4.1 3B Round 3A Replication` (proposed): locally frozen Round 3A evidence undergoing owner review; not yet committed, tagged, or released.

## v0.2 execution kit

This package includes the fail-closed Windows/Ollama execution tools for `v0.2.0`. They:

- require public `v0.1.0` release evidence before formal execution;
- revalidate every frozen protocol hash;
- require Ollama `0.33.2` and the exact frozen model blob;
- perform one excluded neutral warm-up and the fixed 24-run order;
- preserve requests, API attempts, raw responses, execution-time environment evidence, parsing status, token counts, Ollama timings, and independent client wall timings;
- never retry a malformed, low-quality, empty, or absent model answer;
- build a fixed arm-blinded rating packet with decision extraction before gold display;
- provide an interactive human-rating tool with resumable progress;
- validate ratings, produce per-category descriptive metrics, and freeze the complete result set with a SHA-256 manifest.

Start with [docs/V02_EXECUTION_GUIDE.md](docs/V02_EXECUTION_GUIDE.md). Do not run formal cases before the public protocol freeze.

## Frozen primary model

- Model: `phi4-mini:3.8b`
- Developer: Microsoft
- Quantization: `Q4_K_M`
- Ollama blob SHA-256: `3c168af1dea0a414299c7d9077e100ac763370e5a98b3c53801a958a47f0a5db`
- Formal runs: 24 total, one Arm A and one Arm B run for each of 12 cases

See [docs/PROTOCOL.md](docs/PROTOCOL.md), [docs/SCORING_RUBRIC.md](docs/SCORING_RUBRIC.md), and [docs/MODEL_AND_ENVIRONMENT.md](docs/MODEL_AND_ENVIRONMENT.md).

## Validate the frozen protocol

The validator uses only the Python standard library:

```powershell
python -B scripts/validate_protocol.py
```

Expected result:

```text
PASS: frozen pilot protocol is internally consistent
```

## Status

The protocol was publicly frozen as [`v0.1.0`](https://github.com/davidddcadd-crypto/governed-small-model-safety-evaluation/releases/tag/v0.1.0) at `2026-08-30T04:58:16Z`, before any formal model run. The tag points to commit `46028ff0ae5b9bdf5fd7f9a728eb96123ca42eb1`.

The first-model results were published as `v0.2.0`. Round 2A using `ministral-3:3b` was published as `v0.3.0`; its frozen 92-file result set and additive publication disclosures remain unmodified. See [the Round 2A publication addendum](results/round2_ministral3b/ROUND2_PUBLICATION_ADDENDUM.md). Round 3A using `granite4.1:3b` has completed locally with 24/24 formal observations and is awaiting owner review for the proposed `v0.4.0` release. No Round 3 commit, tag, or release is implied by this working-tree status.

## Project lead

Tai Wai Lee (David), independent builder and researcher in Ontario, Canada.

## License

MIT. See [LICENSE](LICENSE).
