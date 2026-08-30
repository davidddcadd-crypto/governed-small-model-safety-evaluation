# v0.2.0 Execution Guide

The formal runner is fail-closed. It will not execute a formal case until a public `v0.1.0` release receipt, the frozen protocol hashes, the Ollama version, and the exact local model blob all pass validation.

## 1. Verify the public v0.1.0 freeze

The public freeze has been completed. `release_receipt.json` records the release URL, exact commit, and public timestamp. Verify it before installing or running the tooling; do not replace it with estimated or local times.

PowerShell example:

```powershell
Get-Content release_receipt.json
git show v0.1.0:protocol_manifest.json | Out-Null
git rev-parse v0.1.0
```

The expected tag commit is `46028ff0ae5b9bdf5fd7f9a728eb96123ca42eb1`. The recorded release time is `2026-08-30T04:58:16Z`. Formal model runs completed before this time: `0`.

## 2. Close avoidable background load

For more stable latency, close Photoshop, unnecessary browser windows, game launchers, and other GPU-heavy applications. Do not alter GPU clocks or use unsafe overclocking. Keep normal Windows display services running.

## 3. Validate without running a case

```powershell
python -B scripts/run_pilot.py --dry-run
```

This checks the protocol, receipt, Ollama CLI/API version, exact model blob, case count, and 24-run order. It makes no model request.

## 4. Run the formal pilot

```powershell
python -B scripts/run_pilot.py
```

The runner performs one excluded neutral warm-up and then the 24 frozen formal runs. It writes request evidence, API attempt evidence, and one immutable run record at a time.

Immediately after warm-up it also writes `results/execution_environment.json`, including `nvidia-smi`, `ollama ps`, Windows inventory, model evidence, and the release receipt. An HTTP-success response with empty or absent assistant content is preserved as `NO_OUTPUT` and is not regenerated.

If a transport error stops the run, preserve all files and resume with:

```powershell
python -B scripts/run_pilot.py --resume
```

`--resume` never regenerates an existing model answer. It only continues missing sequences. A malformed or poor answer is a result, not a transport error, and is never retried.

## 5. Build the blinded packet

After all 24 runs complete:

```powershell
python -B scripts/build_blinded_packet.py
```

Do not inspect `results/blinding_key.json` before completing the primary rating. Use the interactive tool rather than manually opening the packet: it records the extracted decision before displaying gold, computes deterministic totals, binds the rubric and packet hashes, and safely resumes after each completed response:

```powershell
python -B scripts/rate_packet.py --rater-id David
```

## 6. Validate ratings and analyze

The interactive rater creates `results/ratings_primary.jsonl`. Then run:

```powershell
python -B scripts/validate_ratings.py results/ratings_primary.jsonl
python -B scripts/analyze_pilot.py --ratings results/ratings_primary.jsonl
```

The analysis creates `results/PILOT_METRICS.json` and `results/PILOT_REPORT.md`. Review every claim and limitation before the `v0.2.0` release.

After the report is final and before publishing `v0.2.0`, freeze the complete evidence set:

```powershell
python -B scripts/build_result_manifest.py
```

This creates `results/RESULT_MANIFEST.json`. Do not modify a covered result after creating it; if a legitimate correction is required, document it and create a new result version.

## Formal-run stop conditions

Stop without running when:

- `v0.1.0` is not publicly released;
- any protocol manifest hash fails;
- Ollama is not exactly `0.33.2`;
- the model blob differs from the frozen SHA-256;
- the model tag is missing;
- a formal run record already exists and `--resume` was not explicitly supplied;
- the system clock places a run before the public freeze timestamp.
