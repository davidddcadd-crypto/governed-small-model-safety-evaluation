# Governed Small-Model Safety Evaluation

A reproducible empirical study of whether a fixed governance workflow can improve safety-relevant behaviour in small local language models.

**Current status: Phase 1 complete — five within-model A/B evaluation rounds across five local small-model configurations.**

The central research question is intentionally narrow:

> Can a fixed governance workflow improve the safety-relevant behaviour of the same small model compared with a minimal decision prompt?

This repository contains the frozen protocols, synthetic cases, prompts, model outputs, ratings, validation scripts, manifests, negative results, publication disclosures, and cross-model synthesis used to investigate that question.

---

## 30-second summary

Phase 1 evaluated five local small-model configurations using the same fixed 12-case safety framework.

Each model was tested under two conditions:

- **Arm A — Minimal decision workflow:** the model receives the case, decision definitions, and output contract.
- **Arm B — Governed workflow:** the same model receives the same case and output contract, plus fixed checks covering risk, authority, evidence, reversibility, duplication, and safe next action.

Across the five within-model rounds:

- **Strict Safety Pass:** `11/60 (18.3%) → 26/60 (43.3%)`
- **Exact Decision Accuracy:** `47/60 (78.3%) → 52/60 (86.7%)`
- **Unsafe Allows:** `2/40 (5.0%) → 2/40 (5.0%)`
- **Hard Failures:** `6 → 4`
- **Paired Strict Safety outcomes:** `16 improved / 43 unchanged / 1 worsened`
- **Frozen round-level outcome:** `5 SUPPORTIVE / 0 NOT_SUPPORTIVE / 0 NOT_EVALUABLE`

These pooled values are **descriptive only**. The observations are not treated as statistically independent samples.

Full Phase 1 synthesis:

[PHASE1_FIVE_MODEL_SYNTHESIS.md](PHASE1_FIVE_MODEL_SYNTHESIS.md)

---

## Phase 1 results by model

| Round | Local model | Strict Safety Pass A → B | Frozen outcome |
|---|---|---:|---|
| 1 | Phi-4 Mini 3.8B | 2/12 → 6/12 | SUPPORTIVE |
| 2 | Ministral 3B | 4/12 → 8/12 | SUPPORTIVE |
| 3 | Granite 4.1 3B | 1/12 → 4/12 | SUPPORTIVE |
| 4 | Llama 3.2 3B | 1/12 → 3/12 | SUPPORTIVE |
| 5 | Granite 4 3B | 3/12 → 5/12 | SUPPORTIVE |

The frozen cross-model SUPPORTIVE criterion required:

1. 24 eligible observations, with 12 observations per arm;
2. Arm B to produce at least two additional Strict Safety Passes;
3. no increase in Unsafe Allows;
4. no increase in Hard Failures.

The result was not uniformly positive across every metric.

Escalation behaviour was mixed across models, formatting behaviour varied substantially, and recurring hard-failure classes remained in later rounds.

---

## What Phase 1 supports

The strongest claim supported by the current evidence is:

> Under this fixed 12-case, one-observation-per-case-arm evaluation and its frozen rating procedures, Arm B produced more Strict Safety Passes than Arm A in each of five prespecified within-model small-model rounds, and all five rounds met their frozen SUPPORTIVE criterion without increasing Unsafe Allows or Hard Failures.

---

## What Phase 1 does not establish

Phase 1 does **not** establish that:

- governance is generally or causally effective;
- the evaluated models are production-safe;
- pooled observations are statistically independent;
- the result is statistically significant;
- the effect generalizes to unseen hard cases or model families;
- the calibrated AI surrogate is equivalent to independent human experts;
- small models approach frontier-model safety.

The project treats the Phase 1 result as a reason for stronger testing, not as a closed conclusion.

---

## Main methodological limitations

The principal limitations are:

- the same 12 synthetic cases were reused across all five rounds;
- each model-case-arm has only one formal observation;
- Arm B changes multiple factors simultaneously, including governance structure, risk cues, procedural instruction, and prompt length;
- Round 1 used a human primary rater, while Rounds 2–5 used a fixed David-calibrated AI surrogate;
- model family, chat template, quantization, and runtime differences remain potential cross-round confounds;
- no external expert benchmark adjudication has yet been performed.

These limitations directly motivate the next phase of work.

---

## Experimental integrity

The project uses a reproducibility-first evidence process.

Depending on the round, the repository preserves:

- protocol and case freezes before formal execution;
- exact model and environment records;
- fixed execution orders;
- original requests and raw model responses;
- malformed, negative, and unfavourable outputs without selective reruns;
- blinded decision extraction before gold-visible scoring;
- frozen scoring rules and hard-failure definitions;
- human or fixed calibrated-surrogate rating evidence;
- SHA-256 manifests and source bindings;
- validation scripts;
- publication and custody disclosures;
- corrective records when process mistakes occurred.

A failed, malformed, or unfavourable result is treated as evidence and is not silently replaced.

No real email, payment, deletion, deployment, credential, personal data, external tool action, or irreversible real-world action is used in the Phase 1 benchmark.

All Phase 1 cases are synthetic.

---

## Rating methodology

### Round 1

Round 1 used a human primary rater after blinded decision extraction.

### Rounds 2–5

Rounds 2–5 used a fixed AI surrogate calibrated against the Round 1 human ratings.

The surrogate procedure separates:

1. blinded decision extraction before gold is shown;
2. gold-visible rubric scoring in the same isolated rating session.

The surrogate is treated as a methodological limitation and is **not** claimed to be equivalent to independent expert human review.

See the round-specific rating procedures and preserved artifacts for exact implementation details.

---

## Post-hoc robustness work

Phase 1 also includes exploratory:

- exact paired label-swap audits;
- criterion-sensitivity analyses;
- descriptive cross-round aggregation;
- recurring hard-failure analysis.

These analyses are explicitly **post-hoc robustness checks**, not preregistered confirmatory hypothesis tests.

They do not alter any frozen round result.

See:

[PHASE1_FIVE_MODEL_SYNTHESIS.md](PHASE1_FIVE_MODEL_SYNTHESIS.md)

---

## Research roadmap

The next research stages are designed to test alternative explanations and generalization before expanding the claim.

### Phase 2 — Mechanism and generalization validation

Planned work includes:

1. **Mechanism isolation**

   Compare the minimal baseline against an equal-length / risk-cue-matched structured sham and the real governance workflow.

2. **Held-out hard-case generalization**

   Build and freeze a new, harder safety benchmark with stronger independent review and adjudication.

3. **Repeated trials**

   Measure stability across repeated samples and seeds rather than relying on one observation per case-arm.

4. **Workflow v2**

   Develop revisions only on separate development cases, freeze the revised workflow, and evaluate it on fresh held-out cases.

### Phase 3 — Scaling and composition

If compute and evaluation resources allow:

- test larger local models such as 8B–12B-class systems;
- measure how governance uplift changes with model scale;
- evaluate routing, verifier, and escalation architectures;
- test composed small/medium-model systems against single-model baselines.

### Phase 4 — Safety–Performance–Cost Frontier

A later-stage study would compare governed local or composed systems with frontier-model panels using prespecified:

- safety criteria;
- task-performance criteria;
- non-inferiority or comparison margins;
- complete end-to-end cost accounting;
- latency and failure-recovery costs.

The goal would be to measure:

> **Where system-level governance and composition help, where they fail, and what they cost.**

This roadmap is evidence-driven, not a fixed promise.

Negative or contradictory results may change, narrow, or terminate later stages.

---

## Research provenance

The hypothesis was motivated by prior informal engineering observations from workflow-based small-model automation and by earlier governed-system design work.

Those observations were **not** part of the formal Phase 1 evidence.

The formal evidence supporting the claims in this repository comes from the frozen experiments and artifacts published here.

---

## Release history

- `v0.1.0` — Frozen pilot protocol and safety case set
- `v0.2.0` — Phi-4 Mini first governed small-model safety pilot
- `v0.3.0` — Ministral 3B Round 2 replication
- `v0.4.0` — Granite 4.1 3B Round 3 replication
- `v0.5.0` — Llama 3.2 3B Round 4 replication
- `v0.6.0` — Granite 4 3B Round 5 replication
- `v0.7.0` — Phase 1 Five-Model Safety Synthesis

Latest synthesis release:

https://github.com/davidddcadd-crypto/governed-small-model-safety-evaluation/releases/tag/v0.7.0

---

## Repository structure

Key entry points:

- `PHASE1_FIVE_MODEL_SYNTHESIS.md` — cross-model Phase 1 synthesis
- `docs/` — original protocol, rubric, limitations, and execution documentation
- `data/` — frozen synthetic cases and gold records
- `prompts/` — Arm A and Arm B prompt definitions
- `round2/` to `round5/` — later-round protocol and preparation artifacts
- `results/` — raw outputs, ratings, metrics, manifests, and publication evidence
- `scripts/` — execution, analysis, manifest, and validation tooling
- `tests/` — validation and publication-readiness tests

The original frozen protocol files are preserved.

Material changes require a new protocol or workflow version rather than silent modification of prior evidence.

---

## Reproducibility

The project is designed so that published claims can be traced back to preserved experimental artifacts rather than reconstructed from memory.

Round-specific manifests and validators should be treated as authoritative for exact execution and evidence details.

The original pilot protocol can be validated with:

```powershell
python -B scripts/validate_protocol.py
```

Expected result:

```text
PASS: frozen pilot protocol is internally consistent
```

Later rounds include their own preparation, rating, post-execution, and publication validators.

---

## Project lead

**Tai Wai Lee (David)**

Independent researcher and builder focused on AI safety evaluation and governed AI systems

Ontario, Canada

Research interests include:

- small-model safety evaluation;
- agent safety and reliability;
- system-level AI governance;
- model routing, verification, and escalation;
- safety–performance–cost trade-offs in governed AI systems.

---

## License

MIT. See [LICENSE](LICENSE).