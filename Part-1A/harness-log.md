# Harness Log — Part 1A

Repo: github.com/Pritam3355/Spec-Driven-Development — every commit id below is real (short hash in text, full SHAs in §0).
Course template §0–§6 kept as-is and extended with §6–§12 for runs #3–#5 + the midway PM cycle, because the assignment had two full fail→repair→pass loops, not one.

## 0. Environment
- Python: 3.12.10, Windows 11 (win32, Store build — from the run-JSON platform lines)
- Ruff: 0.17.4 (`requirements.txt`; config `.harness/ruff.toml`)
- Bandit: 1.9.4 (config `.harness/bandit.yaml`)
- pytest: 9.2.0 + pytest-cov 7.1.0, coverage floor 50% (constitution rule 2)
- Spec version (commit SHA): v1.0 = `85d8b574442275ae530cc71bdd8fe8b9e8474906`; final v1.1 = `056f4a51de9625dbfbe922ddba5f568a741ce6fb`
- Run JSONs store UTC; my wall-clock times below are IST

## 1. Initial generation
- Date: 2026-11-08 (T1–T6, commit `097d5a4`, PR #1)
- Context given: `constitution.md`, `spec.md`, `clarify.md`, `plan.md`, `tasks.md` (all v1.0)
- Agent/model: GitHub Copilot (VS Code agent chat); I stayed reviewer/integrator
- Snapshot: `evidence/initial-generation/` — honest note: its MANIFEST.md is still the blank template; the real snapshot is commit `097d5a4` itself
- Notes: agent produced `src/errors.py`, `models.py`, `store.py`, `streaks.py`. I authored `tests/test_harness_smoke_test.py` myself (scaffold owner per tasks.md; the AC tests are mine too — the agent never touches `tests/`). Remember that smoke test — it bites me in run #2.

## 2. Harness run #1 — baseline, failing on purpose
- Command: `python .harness/run_harness.py`
- File: `evidence/harness-runs/run-1.json` (2026-11-08, commit `85d8b57` = T0)
- Results: lint=FAIL security=PASS tests=FAIL → overall FAIL
- Evidence (paste snippets from run-1.json):
  - Lint gate:
    ```
    E902 The system cannot find the file specified. (os error 2)
    --> src:1:1    Found 1 error.
    ```
  - Security gate: PASS (empty output — bandit is perfectly happy scanning nothing)
  - Test gate:
    ```
    tests/test_service.py:6: in <module>    from src.errors import (...
    E   ModuleNotFoundError: No module named 'src'
    ```
- Root causes (one per failure, trace to constitution rule or AC):
  - Not a code defect: I committed T0 with an empty `src/` and ran the harness before generation on purpose — cheapest proof the gates bite before I trust them to grade my code.
  - Lint E902 = nothing to walk; ModuleNotFoundError = the AC tests import `src.*`, which didn't exist yet.

## 3. Feedback to agent
- Exact evidence supplied: run-1.json gate outputs + `tasks.md` T1–T6 + spec v1.0 AC table
- Instruction given:
  - "Generate `src/` per tasks.md. Do not edit `tests/`. Do not edit `spec-kit/`. Do not edit `.harness/`." (constitution rule 15)

## 4. Repair
- Files changed: `src/errors.py`, `src/models.py`, `src/store.py`, `src/streaks.py` (`097d5a4`); then `src/service.py`, `src/cli.py`, `conftest.py`, `.harness/ruff.toml`, `.harness/smoke_check.py` (`95efbf7`, T7–T12, PR #2)
- Summary: `HabitError` hierarchy (rule 14), atomic save via tmp + `os.replace` (rule 12), UUIDv4 ids (rule 11), pure streak math, then service layer + argparse CLI
- Diff: cycle 1 = commits `097d5a4` + `95efbf7`; `evidence/final-generation/diff.patch` only captures the v1.1 cycle (§10)

## 5. Harness run #2
- Command: `python .harness/run_harness.py`
- File: `evidence/harness-runs/run-2.json` (2026-11-08)
- Results: lint=FAIL security=PASS tests=PASS (11 passed, 50.23% — one foot over the rule-2 floor)
- Evidence (paste snippets from run-2.json):
  - Lint gate:
    ```
    F401 [*] `traceback` imported but unused  --> tests\test_harness_smoke_test.py:7:8
    E501 Line too long (105 > 100)            --> tests\test_harness_smoke_test.py:60:101
    ```
  - Security gate: PASS (clean)
  - Test gate: PASS — `11 passed in 0.09s`, total coverage 50.23%
- Root causes (one per failure, trace to constitution rule or AC):
  - My lint debt in my own smoke test file (scaffold-owner mistake, not the agent's): unused import + one 105-char case-table line.
  - I fixed my own file; rule 16 ("fix `src/`, never the test") binds the agent, and it never touched `tests/`.

## 6. Harness run #3 — cycle 1 green
- Command: `python .harness/run_harness.py`
- File: `evidence/harness-runs/run-3.json` (2026-11-08)
- Results: lint=PASS security=PASS tests=PASS → overall PASS (11 passed, 50.23%)
- Note: same gates re-run, no threshold lowered, no test deleted.

## 7. Change request — PM midway requirements (why the spec went v1.0 → v1.1)
- PM asked mid-assignment for: habit **deletion** + **days-of-week scheduling** in exactly `[Sun,Mon,Tue,Wed,Thu,Fri,Sat]`
- Awkward part: v1.0 listed deletion as OUT OF SCOPE — so per constitution rule 17 I changed the spec upstream first (commit `056f4a5`) and recorded the reversal in the change log; a silent scope flip would make the spec a lie
- v1.1 added FR-1.5 / FR-3.5 / FR-6 / FR-7, tasks T-13..T-17, 9 new AC tests (11 → 20)
- DoW grammar is stricter than it looks: 3-letter codes only, single commas NO spaces, canonical Sun→Sat order as a subsequence, no duplicates — `[Mon,Wed,Fri]` legal; `[Wed,Mon]`, `[mon]`, `[Mon, Wed]`, `[Mon,Mon]` must all raise `InvalidFrequencyError` (AC-1.5/1.6)

## 8. Harness run #4 — red by design, the run I'm proudest of
- Command: `python .harness/run_harness.py`
- File: `evidence/harness-runs/run-4.json` (2026-11-09, commit `056f4a5`)
- Results: lint=PASS security=PASS tests=FAIL → overall FAIL
- Evidence (paste snippets from run-4.json):
  - Lint gate: PASS ("All checks passed!") — Security gate: PASS (clean)
  - Test gate:
    ```
    tests/test_service.py:13: in <module>    from src.streaks import days_of_week_streak
    E   ImportError: cannot import name 'days_of_week_streak' from 'src.streaks'
    ```
- Root causes (one per failure, trace to constitution rule or AC):
  - Spec + AC tests updated first, `src/` still on v1.0 behaviour — rule 17 (spec upstream, then re-analyze, then code) makes this red run the to-do list; trace: FR-3.5 / AC-3.5, 3.5b–3.5d not implemented yet.

## 9. Feedback to agent (cycle 2)
- Exact evidence supplied: run-4.json test-gate output + v1.1 spec + the failing AC test names (`ac_1_5` … `ac_7_1`)
- Instruction given:
  - "Fix the import failure and implement FR-6/FR-7. Do not edit `tests/`. Do not edit `spec-kit/`. Do not edit `.harness/`."

## 10. Repair
- Files changed: `src/cli.py`, `src/service.py`, `src/streaks.py` (commit `8ebee14`, T13–T16)
- Summary: `delete_habit()` with cascade (logs die with the habit — no orphans after reload; unknown id → `HabitNotFoundError`; hard delete, no undo), strict DoW validation in `add_habit`, `days_of_week_streak()` (walks back from the latest *scheduled* day; scheduled-but-unlogged today → 0; rest day today → rewind to last scheduled day — AC-3.5c took me a second read to trust), CLI `delete <id>` printing `{"deleted": "<id>"}` + bracket-form `add`
- Diff: `evidence/final-generation/diff.patch`

## 11. Harness run #5 — final green
- Command: `python .harness/run_harness.py`
- File: `evidence/harness-runs/run-5.json` (2026-11-09)
- Results: lint=PASS security=PASS tests=PASS → overall PASS (**20 passed, coverage 73.26%**)
- Note: same gates re-run, no threshold lowered, no test deleted; tests only grew 11 → 20 — the new logic pulled coverage up, not down.

## 12. Human decision
- Reviewer: me (Pritam), with the harness as the strict-but-fair second reviewer
- Decision: **ACCEPT**
- Justification: 5 runs, every failure traced to a named cause + a commit, gates never moved, and rule 18 (harness PASS on clean clone) held — PR #3 (`a897a5f`) merged the feature; PR #4 (`9f3a0bd`) only refreshed the diff snapshot + README
- Known limitations: `cli.py` at 52% coverage (parser tested via `ac_7_1`, not every branch exercised), `store.py` at 57%; delete is a silent hard-delete — fine for one JSON file, would need a rethink with real users
- Residual risk after PASS: naive ISO dates, no timezone/DST story — deliberate, documented out of scope
- Additional control before production (if any): a `--dry-run`/confirm flag on delete, plus fuzz tests for the DoW parser
