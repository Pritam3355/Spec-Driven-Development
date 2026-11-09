# Clarifications — Habit Tracker

**Q1:** Does today with no log break the streak?
**A1:** Yes. Current streak = consecutive days with logs ending today. No log today => 0.

**Q2:** What counts as "today"?
**A2:** UTC calendar day, evaluated at call time.

**Q3:** Date format for input/storage?
**A3:** ISO-8601 `YYYY-MM-DD`. All comparisons in UTC.

**Q4:** Logging a date before the habit was created?
**A4:** Allowed. Counts toward streaks (v1 simplification).

**Q5:** Habit ID format?
**A5:** UUIDv4 string, generated at creation. Never sequential.

**Q6:** Same name, different frequency?
**A6:** Allowed. Duplicate check is on `(name, frequency)` tuple.

**Q7:** `log` twice for same (habit, date)?
**A7:** Error (`DuplicateLogError`). Silent overwrite would hide mistakes.

**Q8:** Default data file location?
**A8:** `./data/habits.json` relative to CWD; `--data <path>` overrides.
Directory created if missing; file created on first `save`.

**Q9:** Where is `print()` allowed?
**A9:** Only in `src/cli.py`. All other `src/` modules must not print (Ruff T201).

---
**v1.1 clarifications (PM enhancement request)**

**Q10:** Does deleting a habit also delete its logs?
**A10:** Yes — cascade. `delete_habit` removes the habit AND every log entry
for it in one atomic save; no orphan logs remain in the JSON. Hard delete,
no undo/tombstone in v1.1.

**Q11:** What happens when deleting an unknown (or already deleted) id?
**A11:** `HabitNotFoundError` — consistent with `current_streak` on an
unknown id (FR-3.4). Delete is NOT idempotent.

**Q12:** How strict is the days-of-week format?
**A12:** Strictly `[Sun,Mon,Tue,Wed,Thu,Fri,Sat]` style: square brackets,
3-letter tokens `Sun|Mon|Tue|Wed|Thu|Fri|Sat`, single-comma separators with
NO spaces, tokens in canonical Sun→Sat order, at least one day, no
duplicates. `[Mon,Wed,Fri]` and `[Sun,Sat]` are valid; `[Fri,Mon]` (order),
`[mon]`, `[Monday]`, `[Mon, Wed]`, `[Mon,Mon]`, `[]`, `Mon,Wed` are all
rejected with `InvalidFrequencyError`. Note `[Mon,Fri,Wed]` is a DIFFERENT
string from `[Mon,Wed,Fri]` and would be a distinct habit under FR-1.4 —
the canonical order exists precisely to prevent that confusion.

**Q13:** Does "instead of only daily, weekly" mean daily/weekly are removed?
**A13:** No — interpreted as ADDITIVE. `daily` and `weekly` stay valid so
existing data files keep working; the store schema is unchanged
(`"version": 1`, frequency remains a plain string).


**Q14:** Streak semantics for a `[Mon,Wed,Fri]` habit — what if today has no
log, or today isn't scheduled at all?
**A14:** Walk backwards over SCHEDULED dates only. Scheduled today and
unlogged => 0 (same strict rule as Q1/A1). Unscheduled today is a rest day:
it neither counts nor breaks the streak — e.g. Mon/Wed/Fri all logged and
today is Saturday => streak 3. But a missed scheduled day (e.g. Friday not
logged) breaks the streak even when today is a rest day.

**Q15:** May the user log a completion on a non-scheduled date?
**A15:** Allowed (same spirit as Q4's v1 simplification). Streak math simply
ignores logs on non-scheduled dates.

**Q16:** Is `[Sun,Mon,Tue,Wed,Thu,Fri,Sat]` (all 7 days) the same as `daily`?
**A16:** Stored verbatim as given; streak-wise it behaves like a DoW habit
scheduled every day (equivalent result to daily). Duplicate detection stays
string-based (FR-1.4), so `"daily"` and the full-week list can coexist as
two habits.