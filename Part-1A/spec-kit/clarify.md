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