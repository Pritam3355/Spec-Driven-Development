# Tasks — Natural-Language Habit Logger

| ID | Task | Depends | Satisfies | Done when |
|----|------|---------|-----------|-----------|
| T-1 | `provider.py`: protocol + Fake | — | plan D1 | Importable, fake returns preset |
| T-2 | `config.py`: `.env` loader; `provider.py`: GeminiProvider | T-1 | tech stack, const. 26 | Key from env or gitignored `.env` via `src/config.py` (env wins, never logged); free-tier REST |
| T-3 | `prompts.py`: system prompt | — | plan D2 | Embeds all §1 fields |
| T-4 | `agent.py`: parse skeleton + safe envelope | T-1 | GR-2 | Safe on empty input |
| T-5 | `guardrails.py`: envelope + PII + destructive | — | GR-1,GR-3,BP-3 | Unit-testable |
| T-6 | `agent.py`: wire provider + parse + guardrails | T-2..T-5 | §1 | Schema-valid on happy path |
| T-7 | `tests/test_agent_fake.py` | T-4,T-5 | plan D1 | No network needed |
| T-8 | Manual 3-sample smoke test | T-6 | §3 | 3/3 trivial cases pass |

## AC traceability
- §1 schema -> T-3, T-6
- §2 invariants -> T-5, T-6
- §4 guardrails -> T-5
