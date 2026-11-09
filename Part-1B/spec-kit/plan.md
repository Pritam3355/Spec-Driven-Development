# Design Plan — Natural-Language Habit Logger

## Tech stack
- Python 3.11+, `requests`, `jsonschema`, stdlib
- Provider: `GroqProvider` (OpenAI-compatible REST, free tier, temp=0.2, model via `GROQ_MODEL`, default `openai/gpt-oss-20b`) primary
- Config: `src/config.py` — stdlib `.env` loader (no python-dotenv); `GROQ_API_KEY` from env or gitignored `.env` (env wins)
- `OllamaProvider` (localhost:11434, `llama3.2:1b`) optional offline fallback
- No paid tier.

## Architecture
- `src/config.py` — `load_dotenv()` + `get_groq_api_key()`; key from env, else first `.env` walking up from `src/`
- `src/provider.py` — `LLMProvider` protocol + `GroqProvider` (primary) + `OllamaProvider` (optional) + `FakeProvider` (tests)
- `src/prompts.py` — `SYSTEM_PROMPT`, `build_user_prompt(text)` — embeds spec §1–§4
- `src/agent.py` — `parse(text, provider=None) -> dict` — provider -> JSON -> guardrails -> return
- `src/guardrails.py` — `apply(out, raw) -> dict` — PII scan, destructive scan, safe envelope
- `tests/test_agent_fake.py` — plumbing tests, uses FakeProvider (no network)
- `tests/test_config.py` — offline tests for the `.env` loader

## Interface contract (harness depends on this)
```python
def parse(text: str, provider: LLMProvider | None = None) -> dict:
    """Parse free text into spec.md §1 schema.
    Never raises on well-formed input; returns safe envelope on parse failure (GR-2)."""
```

## Design decisions
| # | Decision | Traces |
|---|----------|--------|
| D1 | Provider abstraction | testability; §5 |
| D2 | System prompt generated from spec | traceability |
| D3 | Guardrails applied after JSON parse | GR-1, GR-2 |
| D4 | Safe-envelope on any exception | GR-2 |
| D5 | Destructive detection in guardrails, not only prompt | BP-3, GR-3 |
| D6 | Judge prompt in separate file, hashed | brief 4.10 |
| D7 | Temperature 0.2 | clarify Q4 |

## Context wall
Agent sees: constitution, spec, clarify, plan, tasks, evals/schema.json (contract).
Agent does NOT see: evals/dataset.json, .harness/, tests/.
