# Constitution — Part 1A Habit Tracker

## Scope
Applies to every file under `src/` and `tests/`. Violations are gate failures.

## Quality bars
1. All public functions/classes have type hints (Ruff ANN).
2. Test coverage of `src/` >= **50%** (`pytest --cov-fail-under=50`).
3. No `print()` in `src/` (Ruff T201), except `src/cli.py` (presentation layer).
4. No mutable default arguments (Ruff B006).
5. Public functions have a one-line docstring.

## Security (SAST-checkable)
6. No `eval`, `exec`, `pickle.loads`, `os.system`, `subprocess(shell=True)` (Bandit B301/B307/B602/B605).
7. No `assert` in `src/` (Bandit B101) — asserts belong only in `tests/`.
8. No bare `except:` or `except Exception: pass` (Bandit B110/B112).
9. Paths built via `pathlib.Path`.
10. No hardcoded secrets or PII in source.

## Engineering invariants
11. Habit IDs are UUIDv4 strings.
12. JSON persistence is atomic: write `<path>.tmp`, `os.replace(tmp, path)`.
13. Dates stored as ISO-8601 `YYYY-MM-DD`; comparisons in UTC.
14. All domain errors inherit `HabitError` in `src/errors.py`.

## Process
15. Agent must not edit `spec-kit/`, `tests/`, or `.harness/`.
16. If a test fails, fix `src/`, never the test.
17. Spec changes are made upstream, reviewed, then re-analyzed before any code change.
18. Harness must PASS on a clean clone before the human ACCEPT decision.
