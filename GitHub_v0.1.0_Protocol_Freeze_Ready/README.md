# Governed Small-Model Safety Evaluation

This repository contains a preregistered exploratory pilot testing whether a fixed, structured governance workflow improves the safety decisions of the same small local language model on synthetic action-risk scenarios.

The comparison is intentionally narrow:

- **Arm A — Minimal single-pass decision:** the model receives the case, decision definitions, and output contract.
- **Arm B — Governed single-pass decision:** the same model receives the same case and output contract plus a fixed sequence of risk, authority, evidence, reversibility, duplication, and safe-next-action checks.

No real email, payment, deletion, deployment, credential, personal data, external tool, or irreversible action is used. All cases are synthetic. The pilot does not establish that the model or workflow is safe for deployment.

## Release plan

- `v0.1.0 — Frozen Pilot Protocol and Safety Case Set`: protocol, cases, gold records, prompts, schemas, scoring rules, execution order, and environment plan frozen before formal model runs.
- `v0.2.0 — First Governed Small-Model Safety Pilot`: immutable raw outputs, ratings, analysis, and a limitations-first pilot report.

## Frozen primary model

- Model: `phi4-mini:3.8b`
- Developer: Microsoft
- Quantization: `Q4_K_M`
- Ollama blob SHA-256: `3c168af1dea0a414299c7d9077e100ac763370e5a98b3c53801a958a47f0a5db`
- Formal runs: 24 total, one Arm A and one Arm B run for each of 12 cases

See [docs/PROTOCOL.md](docs/PROTOCOL.md), [docs/SCORING_RUBRIC.md](docs/SCORING_RUBRIC.md), and [docs/MODEL_AND_ENVIRONMENT.md](docs/MODEL_AND_ENVIRONMENT.md).

## Validate the release candidate

The validator uses only the Python standard library:

```powershell
python -B scripts/validate_protocol.py
```

Expected result:

```text
PASS: frozen pilot protocol is internally consistent
```

## Status

This package is a `v0.1.0` release candidate. It becomes the frozen public protocol only when the project owner reviews it, runs the validator, publishes the Git tag/release, and records the final manifest hashes. No formal pilot result should be generated before that freeze.

## Project lead

Tai Wai Lee (David), independent builder and researcher in Ontario, Canada.

## License

MIT. See [LICENSE](LICENSE).
