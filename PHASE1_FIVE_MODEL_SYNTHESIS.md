Phase 1 Five-Model Safety Synthesis



Phase 1 is now complete across five local small-language-model evaluation rounds using the same fixed 12-case A/B safety evaluation framework.



Across these five within-model rounds, Arm B produced more Strict Safety Passes than Arm A in every round, and all five rounds met their frozen SUPPORTIVE criterion.



Descriptive cross-round results



Across 60 observations per arm:



Strict Safety Pass: 11/60 (18.3%) → 26/60 (43.3%)

Exact Decision Accuracy: 47/60 (78.3%) → 52/60 (86.7%)

Unsafe Allows: 2/40 (5.0%) → 2/40 (5.0%)

Hard Failures: 6 → 4

Format Failures: 30/60 (50.0%) → 27/60 (45.0%)

Paired Strict Safety outcomes across 60 model-case pairs: 16 improved, 43 unchanged, 1 worsened



Each of the five rounds individually satisfied its frozen SUPPORTIVE criterion:



5 SUPPORTIVE / 0 NOT\_SUPPORTIVE / 0 NOT\_EVALUABLE



These pooled values are descriptive only. The 60 observations are not treated as statistically independent samples.



Important mixed findings



The result was not uniformly positive across every metric.



Escalation behavior was mixed across models. One round showed worse escalation recall under Arm B, while later rounds improved but in some cases remained poor in absolute terms.



Formatting behavior also varied substantially by model. In some rounds Arm B improved formatting, while in others formatting was unchanged or worse. This makes a pure formatting explanation insufficient to account for the full Strict Safety Pass pattern.



Later rounds also exposed recurring hard-failure classes, particularly duplicate irreversible actions and unauthorized allows.



Post-hoc robustness analyses



Exploratory exact paired label-swap audits were performed separately for each round using all 4,096 possible within-round label assignments.



The proportion of permutations satisfying the original frozen SUPPORTIVE criterion was:



Round 1: 34.375%

Round 2: 25.0%

Round 3: 12.5%

Round 4: 25.0%

Round 5: 25.0%



Under an exploratory joint calculation using independent round-level permutation schemes, 11 / 16,384 = 0.0671% of combinations satisfied the criterion in all five rounds.



This is a post-hoc robustness audit, not a preregistered confirmatory p-value. The same cases were reused across rounds, and this analysis does not establish causal or statistical significance.



Criterion sensitivity



The original frozen criterion remains authoritative.



Exploratory sensitivity checks showed:



Original +2 Strict Pass criterion: 5/5 rounds

Require +3 Strict Passes: 3/5

Require +4 Strict Passes: 2/5

+2 and escalation recall must not worsen: 4/5

+2 and zero Arm-B Unsafe Allows: 3/5



These analyses do not alter any frozen round result.



What Phase 1 supports



Under this fixed 12-case, one-observation-per-case-arm evaluation and its frozen rating procedures, Arm B produced more Strict Safety Passes than Arm A in each of five prespecified within-model small-model rounds, and all five rounds met their frozen SUPPORTIVE criterion without increasing Unsafe Allows or Hard Failures.



What Phase 1 does not establish



Phase 1 does not establish that governance is generally or causally effective, that the evaluated models are production-safe, that pooled observations are independent, that the result is statistically significant, that the effect generalizes to unseen hard cases or model families, that the calibrated AI surrogate is equivalent to independent human experts, or that these small models approach frontier-model safety.



Main methodological limitations



The principal limitations are:



the same 12 synthetic cases were reused across all five rounds;

each model-case-arm has only one formal observation;

Arm B changes multiple factors simultaneously, including governance structure, risk cues, procedural instruction, and prompt length;

Round 1 used a human primary rater, while Rounds 2–5 used a fixed David-calibrated AI surrogate;

model family, chat template, quantization, and runtime differences remain potential cross-round confounds;

no external expert benchmark adjudication has yet been performed.



The Phase-1 hypothesis was motivated by prior informal engineering observations from workflow-based small-model automation and earlier governed-system design work. Those observations were not part of the formal Phase-1 evidence.



Phase 2



These results motivate stronger tests rather than closing the question.



The next planned sequence, subject to evidence-driven updates, is:



Mechanism isolation: compare a minimal baseline, a matched structured sham control, and the real governance condition.

Held-out hard-case generalization: evaluate the same framework on a newly frozen, independently reviewed harder benchmark.

Repeated trials: measure stability across repeated samples and seeds.

Workflow v2: develop improvements using separate development cases, freeze the revised workflow, then test it only on fresh held-out cases.

Larger and composed systems: if compute allows, test larger local models, routed multi-model systems, verifiers, and frontier-model comparison panels with explicit safety-performance-cost accounting.



Negative or contradictory results will be preserved and may change this roadmap.

