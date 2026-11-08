# Feature Specification — Habit Tracker CLI

## Problem statement
Single user tracks daily/weekly habits, logs completions by date, sees current
streaks. No account, no network, JSON persistence, works offline.

## Functional requirements

### FR-1 — Add habit
- FR-1.1 `add_habit(name: str, frequency: str) -> Habit`
- FR-1.2 `frequency` in `{"daily","weekly"}` else `InvalidFrequencyError`
- FR-1.3 `name` 1–100 non-whitespace chars else `InvalidNameError`
- FR-1.4 Duplicate `(name, frequency)` returns existing habit (same `id`)

### FR-2 — Log completion
- FR-2.1 `log(habit_id, date, value=1) -> LogEntry`
- FR-2.2 `date` must be ISO-8601 `YYYY-MM-DD` else `InvalidDateError`
- FR-2.3 `date` must not be in the future (UTC) else `FutureDateError`
- FR-2.4 Duplicate `(habit_id, date)` raises `DuplicateLogError`
- FR-2.5 `value > 0` else `InvalidValueError`

### FR-3 — Streak
- FR-3.1 `current_streak(habit_id) -> int`
- FR-3.2 Daily streak = consecutive days ending today (UTC). No log today => 0.
- FR-3.3 Weekly streak = consecutive ISO weeks (Mon-based) ending this week.
- FR-3.4 Unknown habit id raises `HabitNotFoundError`

### FR-4 — Listing
- FR-4.1 `list_habits() -> list[HabitSummary]` sorted by name asc
- FR-4.2 Summary: `name, frequency, current_streak, last_logged_date|null`
- FR-4.3 `list_logs(habit_id) -> list[LogEntry]` sorted by date desc

### FR-5 — Persistence
- FR-5.1 `save(path)` writes valid JSON
- FR-5.2 `save` is atomic (constitution 12)
- FR-5.3 `load(path)` reconstructs equal state
- FR-5.4 `load` on missing file returns empty tracker
- FR-5.5 `load` on malformed JSON raises `CorruptDataError`

## API / interface contract

All functions live in `src.service.HabitTracker`. Errors in `src/errors.py`:
`HabitError, InvalidFrequencyError, InvalidNameError, InvalidDateError,
FutureDateError, DuplicateLogError, InvalidValueError, HabitNotFoundError,
CorruptDataError`.

Data model (`src/models.py`):
```python
@dataclass(frozen=True)
class Habit:
    id: str        # UUIDv4
    name: str
    frequency: str # "daily" | "weekly"
    created_at: str

@dataclass(frozen=True)
class LogEntry:
    habit_id: str
    date: str
    value: int

@dataclass(frozen=True)
class HabitSummary:
    name: str
    frequency: str
    current_streak: int
    last_logged_date: str | None
```

## Acceptance criteria
| AC | Statement | Test |
|----|-----------|------|
| AC-1.1 | UUIDv4 id (len 36, `id[14]=='4'`) | test_ac_1_1_uuidv4 |
| AC-1.2 | invalid frequency raises | test_ac_1_2_bad_frequency |
| AC-1.3 | empty name raises | test_ac_1_3_bad_name |
| AC-1.4 | duplicate returns existing | test_ac_1_4_idempotent_add |
| AC-2.2 | bad date raises | test_ac_2_2_bad_date |
| AC-2.3 | future date raises | test_ac_2_3_future_date |
| AC-2.4 | duplicate log raises | test_ac_2_4_duplicate_log |
| AC-2.5 | `value <= 0` raises | test_ac_2_5_invalid_value |
| AC-3.2 | daily streak | test_ac_3_2_daily_streak |
| AC-3.2b | streak 0 on gap | test_ac_3_2b_streak_zero_on_gap |
| AC-3.3 | weekly streak | test_ac_3_3_weekly_streak |
| AC-3.4 | unknown habit raises | test_ac_3_4_unknown_habit |
| AC-4.1 | sorted by name | test_ac_4_1_sorted |
| AC-4.3 | logs sorted desc | test_ac_4_3_desc |
| AC-5.1 | save writes JSON | test_ac_5_1_save_json |
| AC-5.2 | save atomic | test_ac_5_2_atomic |
| AC-5.3 | load roundtrip | test_ac_5_3_roundtrip |
| AC-5.4 | missing file OK | test_ac_5_4_missing_file_ok |
| AC-5.5 | corrupt raises | test_ac_5_5_corrupt |

## Edge cases
- Future date rejected (AC-2.3).
- Duplicate log rejected (AC-2.4).
- Missing today's log => streak 0 (AC-3.2b).
- Weekly streak is ISO Monday-based.
- `load` on missing file => empty tracker.
- `save` on read-only dir => `OSError` propagates (not a HabitError).

## Out of scope
Deletion, editing past logs, multi-user, HTTP API, notifications, non-UTC tz.
