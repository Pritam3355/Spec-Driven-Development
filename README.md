# Assignment 1 — Spec-Driven Development & Harness Engineering

Habit Tracker CLI (Part 1A, deterministic) + Natural-Language Habit Logger
(Part 1B, non-deterministic).

## Prereqs
```
pip install pytest pytest-cov ruff bandit jsonschema requests
```

## Part 1A — Habit Tracker
```
cd Part-1A
python .harness/run_harness.py
```

## Part 1B — NL Habit Logger 
```
cd Part-1B
export GEMINI_API_KEY="..."   # https://aistudio.google.com/apikey
python .harness/evaluation_runner.py
```

## Evidence
See `Part-1A/harness-log.md` and `Part-1B/harness-log.md`.
Snapshots live in `evidence/initial-generation/` and `evidence/final-generation/`.

