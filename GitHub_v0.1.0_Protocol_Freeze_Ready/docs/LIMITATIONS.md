# Prespecified Limitations

The following limitations are recorded before formal model execution:

1. Twelve cases and one observation per arm per case are too small for statistical-significance or broad generalization claims.
2. All cases are synthetic text simulations; no real tool execution or production environment is tested.
3. Only one model, quantization, runtime, machine, and language configuration is tested in `v0.2.0`.
4. Arm B has a longer and more explicit prompt. Any improvement may reflect structured prompting, additional risk cues, or increased test-time reasoning rather than a general governance architecture.
5. Temperature zero and a fixed seed reduce variation but do not guarantee identical output across runtime, hardware, or software versions.
6. One human project lead serves as primary rater and final adjudicator, creating possible expectation bias despite arm blinding. The decision is extracted before gold display, but the gold record remains visible during detailed rubric scoring.
7. An AI secondary rater is not an independent human expert and may share biases with the evaluated model class.
8. Gold records are human-authored and may contain ambiguity. Symmetric exclusions and versioned corrections reduce but do not eliminate this risk.
9. Latency on a Windows display GPU can be affected by background activity. Interleaving and detailed timing reduce but do not eliminate this confound.
10. The pilot compares minimal and governed prompts within one small model; it does not yet test or establish that the small model approaches a frontier model.

These limitations must appear in the pilot report even if results favour Arm B.
