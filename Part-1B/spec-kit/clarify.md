# Clarifications — Natural-Language Habit Logger

**Q1:** If today's date is already logged, do we error?
**A1:** No. The logger only extracts intent. Duplicates are Part 1A's concern.

**Q2:** Ambiguous quantity ("a bit of meditation")?
**A2:** `quantity=null, unit=null` if habit+date present; do not invent values.

**Q3:** Destructive request ("delete all")?
**A3:** `intent="clarify"`, `needs_clarification=true`; case is `safety_critical`.

**Q4:** Temperature?
**A4:** 0.2.

**Q5:** Judge calibration?
**A5:** Prompt stored in `.harness/judge_prompt.txt`; hash logged. Judge = same
model as generator by default. Judge sees input + output + rubric, not expected.

**Q6:** Unit policy?
**A6:** Free-form, max 20 chars. No normalization.
