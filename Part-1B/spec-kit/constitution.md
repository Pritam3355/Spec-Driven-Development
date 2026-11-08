# Constitution — Part 1B Natural-Language Habit Logger

## Inherited from Part 1A
Rules 1–5 (quality), 6–10 (security), 11–14 (engineering), 15–18 (process) apply
to `src/` and `tests/` in this part as well. 50% coverage remains the bar.

## AI-specific rules
20. Every LLM call passes through `src/provider.py`; no SDK calls elsewhere.
21. System prompt loaded from `src/prompts.py`; its hash is logged in `harness-log.md`.
22. All model output passes through `guardrails.apply()` before returning.
23. The evaluation threshold in `spec.md §5` is declared before evaluation begins.
    Never lowered afterward.
24. A safety-critical case failing forces overall FAIL, regardless of aggregate.
25. LLM judge (Layer 3) may NOT replace Layers 1 or 2. Layers run in order.
26. Model ID, temperature, and max_tokens are logged. API keys live in the
    environment only — never in code, never printed, never committed. Loading
    them from a gitignored `.env` file into `os.environ` via `src/config.py`
    (an exported variable wins over `.env`) is the supported path.

## Process (AI)
27. Agent must not see `evals/dataset.json` during implementation.
28. Agent may modify `src/prompts.py`, `src/guardrails.py`, `src/agent.py`,
    `src/provider.py`, `src/config.py` during repair, but may not modify
    `evals/` or `.harness/`.
