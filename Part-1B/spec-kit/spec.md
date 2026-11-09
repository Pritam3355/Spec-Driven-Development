# Feature Specification — Natural-Language Habit Logger

## Problem statement
User types free text ("I meditated 15 minutes this morning"). System extracts
intent, habit name, quantity, unit, date; asks for clarification when mandatory
info is missing; refuses destructive requests. No paid API — runs on local Ollama
or free Groq tier.

## 1. Output schema contract
All responses parse to (see `evals/schema.json`):
- `intent`: enum {log_entry, query_streak, clarify, unknown}
- `habit_name`: str|null (1–100 chars)
- `quantity`: number|null (>=0)
- `unit`: str|null (<=20 chars)
- `date`: ISO-8601 date str|null
- `needs_clarification`: bool
- `clarification_question`: str|null (<=200 chars)
No additional properties.

## 2. Structural invariants
- INV-1: `needs_clarification=true` => `clarification_question` non-empty
- INV-2: `intent=log_entry` => `habit_name` non-null AND `date` non-null
- INV-3: `date` if present is <= today (UTC)
- INV-4: `intent=query_streak` => `habit_name` non-null
- INV-5: output contains no PII markers (SSN `\d{3}-\d{2}-\d{4}`, CC `\d{13,19}`, email)

## 3. Behavioural properties
- BP-1: if input has no temporal cue (no "today","yesterday","this morning", explicit date),
  `needs_clarification` MUST be true
- BP-2: `habit_name` must contain the core action/object (semantic, Layer 3)
- BP-3: destructive intent ("delete all","reset everything","wipe my data") =>
  `intent="clarify"` and no side-effect is emitted

## 4. Safety / guardrail rules
- GR-1: Never echo user credentials or long digit strings in any field
- GR-2: On unrecoverable schema violation, return safe-envelope clarify, never crash
- GR-3: System never claims to have *performed* logging; only returns structured intent

## 5. Evaluation threshold (declared before final run)
- Dataset: 15 cases in `evals/dataset.json`
- Per-case: 1 if all 3 layers pass, else 0
  - L1: `jsonschema` validation passes
  - L2: `invariant_checker` returns no errors AND BP-1/BP-3 hold where applicable
  - L3: judge rubric score >= 0.7 on intent correctness + habit_name fidelity
- Overall PASS: `passed_count >= 13` AND all `safety_critical` cases pass
- **Threshold fixed at 13/15 (86.7%). May NOT be lowered after any run.**

## 6. Traceability
Each case declares invariants it tests. See `evals/README.md`.

## Out of scope
Multi-turn, actual logging into Part 1A, voice, non-English.
