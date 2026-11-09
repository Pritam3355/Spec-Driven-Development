# Feature Specification — Habit Tracker CLI

## Problem statement
Single user tracks daily, weekly, or specific-weekday habits (e.g.
`[Mon,Wed,Fri]`), logs completions by date, sees current streaks, and can
delete habits. No account, no network, JSON persistence, works offline.

> **Spec version 1.1 (2026-11-08).** v1.0 → v1.1 per PM enhancement request:
> adds days-of-week frequency (FR-1.5) and habit deletion (FR-6, FR-7.1).
> "Deletion" was explicitly OUT OF SCOPE in v1.0 — this reversal is recorded
> in the Change log (bottom). Thresholds/gates unchanged.

## Functional requirements

### FR-1 — Add habit
- FR-1.1 `add_habit(name: str, frequency: str) -> Habit`
- FR-1.2 `frequency` is `"daily"`, `"weekly"`, or a days-of-week list per
  FR-1.5; anything else raises `InvalidFrequencyError`
- FR-1.3 `name` 1–100 non-whitespace chars else `InvalidNameError`
- FR-1.4 Duplicate `(name, frequency)` returns existing habit (same `id`)
- FR-1.5 Days-of-week (DoW) frequency grammar — STRICT, per PM:
  format `[Sun,Mon,Tue,Wed,Thu,Fri,Sat]`. Rules: square brackets; ≥1 token;
  tokens are exactly the 3-letter codes `Sun|Mon|Tue|Wed|Thu|Fri|Sat`;
  separated by single commas with NO spaces; tokens MUST appear in canonical
  Sun→Sat order (subsequence of the full week); no duplicates.
  Valid: `[Mon,Wed,Fri]`, `[Sun,Sat]`, the full 7-day list.
  Invalid: `[Fri,Mon]` (order), `[mon]` (case), `[Monday]` (spelling),
  `[Mon, Wed]` (space), `[Mon,Mon]` (duplicate), `[]` (empty), `Mon,Wed`
  (no brackets).

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
- FR-3.5 DoW streak (frequency per FR-1.5): a date is SCHEDULED iff its
  weekday is in the habit's day list. Streak = number of consecutive
  scheduled dates, walking backwards from the latest scheduled date ≤ today,
  that each have a log. A scheduled TODAY without a log => 0 (same strict
  rule as FR-3.2). Unscheduled dates ("rest days") never count and never
  break the streak; logs on non-scheduled dates are allowed (clarify Q15)
  and ignored by the streak. A missed scheduled date breaks the streak even
  if today is a rest day.


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

### FR-6 — Delete habit (NEW in v1.1)
- FR-6.1 `delete_habit(habit_id: str) -> None` removes the habit
- FR-6.2 Cascade: ALL log entries of that habit are removed in the same
  change — no orphan logs may remain in the store (checked after reload)
- FR-6.3 Unknown `habit_id` raises `HabitNotFoundError`
- FR-6.4 Deletion takes effect on the next `save()` (CLI saves immediately);
  hard delete, no undo/tombstone in v1.1

### FR-7 — CLI surface (NEW in v1.1)
- FR-7.1 New subcommand: `delete <habit_id>`; on success prints
  `{"deleted": "<habit_id>"}` and saves; unknown id → `error: ...` exit 1
- FR-7.2 `add` accepts the FR-1.5 bracket form as a single quoted argument
  (argparse must NOT restrict choices — validation lives in the service,
  plan D9); `add ... "[Mon,Wed,Fri]"`
- FR-7.3 Existing subcommands (`add`, `log`, `streak`, `list`, `logs`)
  behave unchanged for `daily`/`weekly` habits


## API / interface contract

All functions live in `src.service.HabitTracker` (v1.1 adds
`delete_habit(habit_id) -> None`). Streak math lives in `src.streaks`
(`daily_streak`, `weekly_streak`, and v1.1 `days_of_week_streak`). Errors in
`src/errors.py`:
`HabitError, InvalidFrequencyError, InvalidNameError, InvalidDateError,
FutureDateError, DuplicateLogError, InvalidValueError, HabitNotFoundError,
CorruptDataError`.


Data model (`src/models.py`):
```python
@dataclass(frozen=True)
class Habit:
    id: str        # UUIDv4
    name: str
    frequency: str # "daily" | "weekly" | "[Day,...]" (FR-1.5)
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
| AC-1.5 | valid DoW list accepted, stored verbatim, FR-1.4 dup check | test_ac_1_5_dow_add |
| AC-1.6 | malformed DoW (order/case/space/spelling/dup/empty/no-brackets) raises | test_ac_1_6_dow_invalid |
| AC-3.5 | DoW streak counts consecutive scheduled logged days | test_ac_3_5_dow_streak |
| AC-3.5b | scheduled today, unlogged => 0 | test_ac_3_5b_dow_today_unlogged |
| AC-3.5c | rest-day today neither counts nor breaks; missed scheduled day breaks | test_ac_3_5c_dow_rest_today |
| AC-3.5d | full-week list streaks like daily via service dispatch | test_ac_3_5d_full_week |
| AC-6.1 | delete removes habit AND its logs (persisted, no orphans) | test_ac_6_1_delete |
| AC-6.2 | delete unknown id raises | test_ac_6_2_delete_unknown |
| AC-7.1 | CLI parses `delete <id>` and bracket-form `add` | test_ac_7_1_cli_parser |


## Edge cases
- Future date rejected (AC-2.3).
- Duplicate log rejected (AC-2.4).
- Missing today's log => streak 0 (AC-3.2b).
- Weekly streak is ISO Monday-based.
- `load` on missing file => empty tracker.
- `save` on read-only dir => `OSError` propagates (not a HabitError).
- DoW: full 7-day list is streak-equivalent to daily but stored verbatim
  (clarify Q16); different token order = different frequency string = a
  DISTINCT habit under FR-1.4 (documented quirk, clarify Q12).
- DoW: logging a non-scheduled date is accepted and ignored by the streak
  (clarify Q15).
- Delete: logging to a deleted id => `HabitNotFoundError`; second delete of
  the same id => `HabitNotFoundError` (no tombstones).

## Out of scope
Editing habits after creation (rename/frequency change), editing past logs,
multi-user, HTTP API, notifications, non-UTC tz, intervals like "every N days",
undo of deletion.


## Change log
- **v1.1** — PM enhancement request:
  1. Habit deletion added (FR-6, FR-7.1). v1.0 listed deletion as out of
     scope; that decision is reversed by the product owner and recorded here.
  2. Days-of-week frequency added (FR-1.5, FR-3.5, FR-7.2) in the strict
     bracket format. `daily`/`weekly` are RETAINED (clarify Q13) so existing
     data files stay valid; store schema unchanged (`"version": 1`).
  3. New ACs: 1.5, 1.6, 3.5, 3.5b, 3.5c, 3.5d, 6.1, 6.2, 7.1; clarifications
     Q10–Q16; plan decisions D9–D11; tasks T-13..T-16.
- **v1.0** — initial baseline (FR-1..FR-5).
