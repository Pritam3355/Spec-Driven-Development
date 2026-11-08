# Tasks — Habit Tracker

| ID | Task | Depends | Satisfies | Done when |
|----|------|---------|-----------|-----------|
| T-1 | `src/errors.py` hierarchy | — | spec API | 9 error classes inherit HabitError |
| T-2 | `src/models.py` dataclasses | T-1 | spec Data model | Frozen, typed |
| T-3 | `store.save` atomic | T-2 | FR-5.1,5.2, const 12 | Tmp + os.replace |
| T-4 | `store.load` (missing/corrupt) | T-2 | FR-5.3,5.4,5.5 | All 3 cases |
| T-5 | `streaks.daily_streak` | T-2 | FR-3.2 | Pure function |
| T-6 | `streaks.weekly_streak` | T-2 | FR-3.3 | ISO weeks |
| T-7 | `HabitTracker.add_habit` | T-1..T-6 | FR-1.1..1.4 | AC-1.x |
| T-8 | `HabitTracker.log` | T-1..T-6 | FR-2.1..2.5 | AC-2.x |
| T-9 | `HabitTracker.current_streak` | T-5,T-6,T-7 | FR-3.1,3.4 | AC-3.x |
| T-10 | `HabitTracker.list_habits` | T-5,T-7 | FR-4.1,4.2 | AC-4.1 |
| T-11 | `HabitTracker.list_logs` | T-8 | FR-4.3 | AC-4.3 |
| T-12 | CLI argparse | T-7..T-11 | plan D7 | 5 subcommands |

## AC → Task traceability
AC-1.*:T-7 | AC-2.*:T-8 | AC-3.2/3.2b:T-5,T-9 | AC-3.3:T-6,T-9 | AC-3.4:T-9
AC-4.1:T-10 | AC-4.3:T-11 | AC-5.1/5.2:T-3 | AC-5.3/5.4/5.5:T-4
