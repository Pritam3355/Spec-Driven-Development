# Analyze — Habit Tracker

## Coverage
- Every AC has a corresponding test task: yes (see spec AC table).
- Every constitution rule maps to a plan decision or harness gate: yes.
- Every FR traces to >=1 task: yes.
- Every task has a "done when": yes.

## Discrepancies found
- FR-2.5 (`value > 0`) had no AC initially; added test_ac_2_5_invalid_value to T-8.
- AC-3.2b (streak 0 on gap) was implicit; now explicit and testable.
- v1.0 listed **Deletion** as OUT OF SCOPE while the PM now requires it:
  reversed by the product owner; recorded in spec.md Change log.
- PM wording "instead of only daily, weekly" is ambiguous (replace vs
  extend): resolved as ADDITIVE (clarify Q13) so existing data files stay
  valid and no store migration is needed.
- Partial-week schedules made streak semantics ambiguous (does a missed
  Friday break the streak on Saturday?): pinned in FR-3.5 + clarify Q14 so
  the AC-3.5* tests are deterministic.
- argparse `choices` cannot express the strict DoW grammar: validation moved
  fully into the service (plan D9); CLI stays thin (constitution 3).
- `[Fri,Mon]` vs `[Mon,Fri]`: canonical Sun→Sat order rule added (clarify
  Q12) so each schedule has exactly one canonical spelling.


## Verdict
Tasks cover spec. Ready to write harness + tests, then build.
