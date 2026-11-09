# Design Plan — Habit Tracker CLI

## Objective
Deliver a Python CLI implementing spec.md FR-1..FR-5, testable by a harness
(lint + SAST + pytest at 50% coverage).

## Tech stack
- Python 3.11+
- Runtime: stdlib only (`uuid`, `json`, `dataclasses`, `pathlib`, `datetime`, `argparse`)
- Dev: `pytest`, `pytest-cov`, `ruff`, `bandit`

## Architecture
- `src/models.py` — frozen dataclasses
- `src/errors.py` — exception hierarchy
- `src/store.py` — load/save JSON with atomic write
- `src/streaks.py` — pure functions: `daily_streak`, `weekly_streak`, `days_of_week_streak` (v1.1)
- `src/service.py` — `HabitTracker` class incl. `delete_habit` (v1.1) + DoW validation (v1.1)
- `src/cli.py` — argparse entry: `add`, `log`, `streak`, `list`, `logs`, `delete` (v1.1)
- `tests/` — one file per module

## Data model (JSON format)
```json
{
  "version": 1,
  "habits": [{"id": "uuid", "name": "x", "frequency": "daily", "created_at": "..."}],
  "logs":   [{"habit_id": "uuid", "date": "YYYY-MM-DD", "value": 1}]
}
```


## Design decisions
| # | Decision | Traces to |
|---|----------|-----------|
| D1 | Atomic write via `os.replace` | constitution 12 |
| D2 | Domain errors inherit `HabitError` | constitution 14 |
| D3 | UUIDv4 for habit IDs | constitution 11, AC-1.1 |
| D4 | Streak functions are pure (no I/O) | testability |
| D5 | `save`/`load` accept `path: Path` | testability |
| D6 | Weekly streak uses `date.isocalendar()[:2]` | AC-3.3 |
| D7 | CLI uses `argparse` subcommands `add`,`log`,`streak`,`list`,`logs`,`delete` | FR-1..4, FR-7.1 |
| D8 | Data path from `--data`, default `./data/habits.json` | clarify Q8 |
| D9 | DoW frequency validated by ONE strict parser in service (regex + canonical Sun→Sat order + no duplicates); argparse has NO choices, service is single source of truth (FR-7.2) | spec FR-1.5 |
| D10 | DoW streak is pure `days_of_week_streak(dates, today, scheduled: frozenset[int])` — Python weekday ints Mon=0..Sun=6, service maps tokens (Sun→6, Mon→0, Tue→1, Wed→2, Thu→3, Fri→4, Sat→5); scheduled-today-unlogged => 0, rest days skip (clarify Q14) | spec FR-3.5, D4 |
| D11 | Delete = filter habits + cascade-filter logs in service, then one atomic save; store.py unchanged, schema still `"version": 1` | spec FR-6, clarify Q10 |


## Functional flows
- Add: `cli.add -> service.add_habit -> validate (daily|weekly|DoW per D9) -> uuid4 -> append -> return`
- Log: `cli.log -> service.log -> validate -> check dup -> append`
- Streak: `service.current_streak -> dispatch by frequency: daily_streak |weekly_streak | days_of_week_streak(parsed_days) -> int`
- Delete (v1.1): `cli.delete -> service.delete_habit -> check exists -> remove habit + cascade logs -> cli saves -> print {"deleted": id}`

## Development plan (build order)
1. `errors.py`  2. `models.py`  3. `store.py`  4. `streaks.py`  5. `service.py`  6. `cli.py`

## Constitution mapping
| Rule | Honored by |
|------|-----------|
| 1 | All modules annotated; Ruff ANN |
| 2 | pytest-cov --cov-fail-under=50 |
| 11 | `uuid.uuid4()` |
| 12 | store.save: tmp + os.replace |
| 14 | All raises reference `src.errors` |

## Context wall
Agent sees: constitution, spec, clarify, plan, tasks.
Agent does NOT see: `tests/`, `.harness/`.
