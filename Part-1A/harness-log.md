# Harness Log — Part 1A

## 0. Environment
- Python: 
- Ruff: 
- Bandit: 
- pytest: 
- Spec version (commit SHA): 

## 1. Initial generation
- Date: 
- Context given: `constitution.md`, `spec.md`, `clarify.md`, `plan.md`, `tasks.md`
- Agent/model: 
- Snapshot: `evidence/initial-generation/`
- Notes: 

## 2. Harness run #1
- Command: `python .harness/run_harness.py`
- File: `evidence/harness-runs/run-1.json`
- Results: lint=? security=? tests=?
- Evidence (paste snippets from run-1.json):
  - Lint gate:
    ```
    <paste failures>
    ```
  - Security gate:
    ```
    <paste failures>
    ```
  - Test gate:
    ```
    <paste failures>
    ```
- Root causes (one per failure, trace to constitution rule or AC):
  - 

## 3. Feedback to agent
- Exact evidence supplied: 
- Instruction given: 
  - e.g. "Fix violations. Do not edit `tests/`. Do not edit `spec-kit/`. Do not edit `.harness/`."

## 4. Repair
- Files changed: 
- Summary: 
- Diff: `evidence/final-generation/diff.patch`

## 5. Harness run #2
- Command: `python .harness/run_harness.py`
- File: `evidence/harness-runs/run-2.json`
- Results: lint=? security=? tests=?
- Note: same gates re-run, no threshold lowered, no test deleted.

## 6. Human decision
- Reviewer: 
- Decision: **ACCEPT** / **REJECT**
- Justification: 
- Known limitations: 
- Residual risk after PASS: 
- Additional control before production (if any): 
