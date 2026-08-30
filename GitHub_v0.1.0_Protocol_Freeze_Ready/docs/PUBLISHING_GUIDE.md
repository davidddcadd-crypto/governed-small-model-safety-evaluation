# Publishing Guide for v0.1.0

Do not place this project inside the OWL repository. Use a separate public repository named:

```text
governed-small-model-safety-evaluation
```

## Project-owner review before publication

Confirm that you accept:

1. the 12 synthetic case scenarios;
2. the four `ALLOW`, four `DENY`, four `ESCALATE` gold decisions;
3. the Strict Safety Pass and 0–10 scoring rules;
4. the selected `phi4-mini:3.8b` blob and fixed generation settings;
5. the public disclosure of the project lead name and hardware/runtime metadata;
6. the MIT license.

If any freeze-critical file changes, regenerate `protocol_manifest.json` before publishing.

## Validate on Windows

From PowerShell in the repository root:

```powershell
python -B scripts/validate_protocol.py
```

Do not publish unless it returns:

```text
PASS: frozen pilot protocol is internally consistent
```

## Publish with Git command line

Create an empty GitHub repository first. Do not add an automatic README, license, or `.gitignore`, because this package already contains them.

Then run from the extracted repository folder, replacing the remote URL:

```powershell
git init
git branch -M main
git add .
git commit -m "Freeze pilot protocol and safety case set"
git remote add origin https://github.com/YOUR-ACCOUNT/governed-small-model-safety-evaluation.git
git push -u origin main
git tag -a v0.1.0 -m "Frozen Pilot Protocol and Safety Case Set"
git push origin v0.1.0
```

On GitHub, create a release from tag `v0.1.0` titled:

```text
v0.1.0 — Frozen Pilot Protocol and Safety Case Set
```

Suggested release text:

```text
This release freezes the exploratory pilot protocol before formal model execution. It includes 12 synthetic safety cases, balanced ALLOW/DENY/ESCALATE gold decisions, Arm A and Arm B prompts, scoring and hard-failure rules, JSON schemas, a fixed 24-run order, environment metadata, prespecified limitations, and a SHA-256 protocol manifest. Formal model runs completed before this release: 0.
```

After the release timestamp is visible, update `STATUS.md` in the next commit to record the release URL, commit SHA, tag, and freeze timestamp. That administrative update must not modify any manifest-listed protocol file.

## Stop condition

Do not start the 24 formal runs until:

- the public `v0.1.0` release exists;
- the validator passes on the Windows host;
- the release timestamp is recorded;
- the model blob and Ollama version still match the frozen metadata.
