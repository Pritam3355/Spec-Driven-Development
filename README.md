# Assignment 1 — Spec-Driven Development & Harness Engineering

Habit Tracker CLI (Part 1A, deterministic) + Natural-Language Habit Logger
(Part 1B, non-deterministic).

## Prereqs
```
pip install -r requiremnents.txt
```

## Part 1A — Habit Tracker
```bash
cd Part-1A
python .harness/run_harness.py
python -m pytest tests/ -v 

## Add Habit
python -m src.cli add "ice bath" weekly
python -m src.cli add "cardio" [Mon,Wed,Fri]
python -m src.cli add "stretch" daily
python -m src.cli list
python -m src.cli delete 2803721b-3fb3-45eb-aadb-e75e5feaab5f # <habit_id>

## Log & streak (for streching)
$id = "2399c57f-4639-463f-987a-5416a473b31f"
python -m src.cli log $id 2026-11-06
python -m src.cli log $id 2026-11-07
python -m src.cli log $id 2026-11-08
python -m src.cli log $id 2026-11-09 # unless you put current date the streak will be 0
python -m src.cli streak $id 
python -m src.cli logs $id
```

## Part 1B — NL Habit Logger 
```bash
cd Part-1B
GROQ_API_KEY="..."   # update .env
python -m pytest tests/ -v

# Testing 
python .harness/evaluation_runner.py # Test on evals/dataset.json examples
python .harness/model_smoke.py # Test with single example
```

## Evidence
See `Part-1A/harness-log.md` and `Part-1B/harness-log.md`.
Snapshots live in `evidence/initial-generation/` and `evidence/final-generation/`.

