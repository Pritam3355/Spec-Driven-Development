#!/usr/bin/env python3
"""Part 1B smoke check — pre-harness sanity.

Replaces the inline `python - <<'PY' ... PY` blocks from the prompt guide
(Chat 1B-1 / 1B-2 / 1B-3 verifications). Run BEFORE
`.harness/evaluation_runner.py` for fast feedback on wiring issues that don't
need an LLM call.

Sections:
  1. Imports       — every src/*.py module imports cleanly; expected modules present
  2. Schema        — evals/schema.json is valid Draft-07 and covers required fields
  3. Config        — .env loader: parses, env wins, missing key raises RuntimeError
  4. Provider      — FakeProvider returns preset; LLMProvider base raises;
                     GeminiProvider missing-key path raises before any network
  5. Guardrails    — safe envelope schema-valid; destructive / PII handled
  6. Agent offline — parse(""/"garbage") via FakeProvider never raises
  7. Forbidden     — AST scan of src/ for print/eval/exec/assert

Exit code: 0 = all clean, 1 = any failure.

Sections whose source module isn't generated yet are reported SKIP — section 1
still fails on the missing module, so the overall verdict is unambiguous.
"""
from __future__ import annotations

import ast
import importlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]   # Part-1B/
SRC = ROOT / "src"
SCHEMA_PATH = ROOT / "evals" / "schema.json"

FORBIDDEN_CALLS = {"print", "eval", "exec"}
EXPECTED_MODULES = {"config", "provider", "prompts", "guardrails", "agent"}
REQUIRED_SCHEMA_FIELDS = {
    "intent", "habit_name", "quantity", "unit", "date",
    "needs_clarification", "clarification_question",
}
VALID_INTENTS = {"log_entry", "query_streak", "clarify", "unknown"}


# ---------------------------------------------------------------- helpers

def _module_missing(mod: str) -> bool:
    return not (SRC / f"{mod}.py").exists()


def _apply_guardrails(apply_fn, out: dict, user_text: str):
    """Call guardrails.apply() supporting both the 2-arg signature (plan D3:
    `apply(out, raw)`) and the 3-arg signature (prompt guide 1B-2:
    `apply(out, raw, user_text)`). If the plan and prompt disagreed, this
    still exercises the function so we can see behaviour."""
    try:
        return apply_fn(out, user_text)
    except TypeError as e:
        if "positional" not in str(e).lower():
            raise
        return apply_fn(out, json.dumps(out), user_text)


# ---------------------------------------------------------------- 1. imports

def check_imports() -> list[str]:
    errors: list[str] = []
    if not SRC.exists():
        return [f"src/ not found at {SRC} (agent hasn't generated it yet?)"]
    if not (SRC / "__init__.py").exists():
        errors.append("src/__init__.py missing — required for `from src.X import Y`")

    present = {p.stem for p in SRC.glob("*.py") if p.stem != "__init__"}
    for mod in sorted(EXPECTED_MODULES - present):
        errors.append(f"missing module: src/{mod}.py (plan expects it)")

    sys.path.insert(0, str(ROOT))
    for path in sorted(SRC.glob("*.py")):
        if path.name == "__init__.py":
            continue
        try:
            importlib.import_module(f"src.{path.stem}")
        except Exception as e:
            errors.append(f"{path.name} -> {type(e).__name__}: {e}")
    return errors


# ---------------------------------------------------------------- 2. schema

def check_schema() -> list[str]:
    errors: list[str] = []
    if not SCHEMA_PATH.exists():
        return [f"missing: {SCHEMA_PATH}"]
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        return [f"evals/schema.json does not parse: {type(e).__name__}: {e}"]

    try:
        from jsonschema import Draft7Validator
        Draft7Validator.check_schema(schema)
    except Exception as e:
        errors.append(f"schema not valid Draft-07: {type(e).__name__}: {e}")

    missing = REQUIRED_SCHEMA_FIELDS - set(schema.get("required", []))
    if missing:
        errors.append(f"schema.required missing: {sorted(missing)}")

    intent_enum = ((schema.get("properties") or {}).get("intent") or {}).get("enum")
    if intent_enum:
        extra = set(intent_enum) - VALID_INTENTS
        if extra:
            errors.append(f"intent enum has unknown values: {sorted(extra)}")

    return errors


# ---------------------------------------------------------------- 3. config

def check_config() -> list[str]:
    if _module_missing("config"):
        return []
    errors: list[str] = []
    try:
        from src import config
    except Exception as e:
        return [f"cannot import src.config: {e}"]

    import tempfile

    # a) load_dotenv parses, quotes stripped, malformed ignored
    try:
        p = pathlib.Path(tempfile.mkdtemp()) / ".env"
        p.write_text(
            'GROQ_API_KEY="abc 123"\nGROQ_MODEL=openai/gpt-oss-20b\nBROKEN LINE\n',
            encoding="utf-8",
        )
        env: dict[str, str] = {}
        config.load_dotenv(p, env)
        if env.get("GROQ_API_KEY") != "abc 123":
            errors.append(f"load_dotenv: key={env.get('GROQ_API_KEY')!r} (want 'abc 123')")
        if env.get("GROQ_MODEL") != "openai/gpt-oss-20b":
            errors.append(f"load_dotenv: model={env.get('GROQ_MODEL')!r}")
        if "BROKEN" in env:
            errors.append("load_dotenv: malformed line not ignored")
    except Exception as e:
        errors.append(f"load_dotenv raised {type(e).__name__}: {e}")

    # b) env wins over .env
    try:
        p = pathlib.Path(tempfile.mkdtemp()) / ".env"
        p.write_text("GROQ_API_KEY=from-file\n", encoding="utf-8")
        env = {"GROQ_API_KEY": "from-export"}
        config.load_dotenv(p, env)
        if env["GROQ_API_KEY"] != "from-export":
            errors.append(f"load_dotenv overwrote env var (got {env['GROQ_API_KEY']!r})")
    except Exception as e:
        errors.append(f"load_dotenv override-check raised {type(e).__name__}: {e}")

    # c) missing key raises RuntimeError (not silent None)
    try:
        orig = getattr(config, "_find_dotenv", None)
        if orig is not None:
            config._find_dotenv = lambda *a, **k: None
        try:
            try:
                config.get_groq_api_key({})
                errors.append("get_groq_api_key({}) did NOT raise on missing key")
            except RuntimeError:
                pass
            except Exception as e:
                errors.append(f"missing-key raised {type(e).__name__}, want RuntimeError")
        finally:
            if orig is not None:
                config._find_dotenv = orig
    except Exception as e:
        errors.append(f"missing-key check raised {type(e).__name__}: {e}")

    return errors

# ---------------------------------------------------------------- 4. provider

def check_provider() -> list[str]:
    if _module_missing("provider"):
        return []
    errors: list[str] = []
    try:
        from src.provider import FakeProvider, LLMProvider
    except Exception as e:
        return [f"cannot import src.provider: {e}"]

    try:
        f = FakeProvider('{"intent":"clarify"}')
        if f.generate("x") != '{"intent":"clarify"}':
            errors.append(f"FakeProvider.generate returned {f.generate('x')!r}, want preset")
    except Exception as e:
        errors.append(f"FakeProvider raised {type(e).__name__}: {e}")

    try:
        LLMProvider().generate("x")
        errors.append("LLMProvider.generate() did NOT raise NotImplementedError")
    except NotImplementedError:
        pass
    except Exception as e:
        errors.append(f"LLMProvider.generate raised {type(e).__name__}, want NotImplementedError")

    # GroqProvider: missing key → RuntimeError BEFORE any network call.
    import os
    try:
        from src.provider import GroqProvider
    except Exception as e:
        errors.append(f"GroqProvider missing from src.provider: {e}")
        return errors

    saved = os.environ.pop("GROQ_API_KEY", None)
    try:
        from src import config as _cfg
        orig_find = getattr(_cfg, "_find_dotenv", None)
        if orig_find is not None:
            _cfg._find_dotenv = lambda *a, **k: None
        try:
            try:
                p = GroqProvider()
            except RuntimeError:
                p = None
            if p is not None:
                try:
                    p.generate("x")
                    errors.append("GroqProvider.generate() with no key did NOT raise")
                except RuntimeError:
                    pass
                except Exception as e:
                    errors.append(
                        f"GroqProvider no-key generate raised {type(e).__name__}, want RuntimeError"
                    )
        finally:
            if orig_find is not None:
                _cfg._find_dotenv = orig_find
    except Exception as e:
        errors.append(f"GroqProvider no-key check raised {type(e).__name__}: {e}")
    finally:
        if saved is not None:
            os.environ["GROQ_API_KEY"] = saved

    return errors

# ---------------------------------------------------------------- 5. guardrails

def check_guardrails() -> list[str]:
    if _module_missing("guardrails"):
        return []
    errors: list[str] = []
    try:
        from src.guardrails import apply, safe_envelope
    except Exception as e:
        return [f"cannot import src.guardrails: {e}"]

    # safe_envelope: schema-valid + clarify + non-empty question
    try:
        env = safe_envelope("which day?")
        if not isinstance(env, dict):
            errors.append(f"safe_envelope returned {type(env).__name__}, want dict")
        else:
            if SCHEMA_PATH.exists():
                try:
                    from jsonschema import Draft7Validator
                    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
                    errs = list(Draft7Validator(schema).iter_errors(env))
                    if errs:
                        errors.append(f"safe_envelope not schema-valid: {errs[0].message}")
                except Exception:
                    pass
            if env.get("intent") != "clarify":
                errors.append(f"safe_envelope intent={env.get('intent')!r}, want 'clarify'")
            if not env.get("needs_clarification"):
                errors.append("safe_envelope needs_clarification is not True")
    except Exception as e:
        errors.append(f"safe_envelope raised {type(e).__name__}: {e}")

    bad = {
        "intent": "log_entry", "habit_name": "walked", "quantity": 1,
        "unit": None, "date": None, "needs_clarification": False,
        "clarification_question": None,
    }

    # destructive input → clarify + needs_clarification
    try:
        out = _apply_guardrails(apply, bad, "delete all my habits and log a walk")
        if out.get("intent") != "clarify":
            errors.append(f"destructive input → intent={out.get('intent')!r}, want 'clarify'")
        if not out.get("needs_clarification"):
            errors.append("destructive input → needs_clarification is not True")
    except Exception as e:
        errors.append(f"destructive apply raised {type(e).__name__}: {e}")

    # PII echo → masked (INV-5)
    try:
        pii_out = dict(bad, clarification_question="noted 123-45-6789 ok")
        out = _apply_guardrails(apply, pii_out, "walked today")
        if "123-45-6789" in str(out):
            errors.append("PII (SSN) leaked into output after apply()")
    except Exception as e:
        errors.append(f"PII apply raised {type(e).__name__}: {e}")
    
    # Cross-check: safe_envelope must satisfy every invariant in spec §2
    # that the eval-runner would enforce (INV-1, INV-2, INV-3, INV-4).
    try:
        from src.guardrails import safe_envelope as _se
        env = _se("which day did you mean?")
        errs = []
        if env.get("needs_clarification") and not (env.get("clarification_question") or "").strip():
            errs.append("INV-1: clarification_question empty")
        if env.get("intent") == "log_entry" and (not env.get("habit_name") or not env.get("date")):
            errs.append("INV-2: log_entry missing habit_name/date")
        if env.get("intent") == "query_streak" and not env.get("habit_name"):
            errs.append("INV-4: query_streak missing habit_name")
        if errs:
            errors.append(f"safe_envelope violates invariants: {'; '.join(errs)}")
    except Exception as e:
        errors.append(f"safe_envelope invariant cross-check raised {type(e).__name__}: {e}")

    return errors


# ---------------------------------------------------------------- 6. agent offline

def check_agent_offline() -> list[str]:
    if _module_missing("agent") or _module_missing("provider"):
        return []
    errors: list[str] = []
    try:
        from src.agent import parse
        from src.provider import FakeProvider
    except Exception as e:
        return [f"cannot import src.agent / src.provider: {e}"]

    try:
        out = parse("", provider=FakeProvider(""))
        if not isinstance(out, dict):
            errors.append(f"parse('') returned {type(out).__name__}, want dict")
        elif out.get("intent") not in {"clarify", "unknown"}:
            errors.append(f"parse('') intent={out.get('intent')!r}, want clarify/unknown")
    except Exception as e:
        errors.append(f"parse('') raised {type(e).__name__}: {e}")

    try:
        out = parse("hi", provider=FakeProvider("not json"))
        if not out.get("needs_clarification"):
            errors.append("parse('hi','not json') → needs_clarification is not True")
        if not out.get("clarification_question"):
            errors.append("parse('hi','not json') → empty clarification_question (INV-1)")
    except Exception as e:
        errors.append(f"parse('hi','not json') raised {type(e).__name__}: {e}")

    return errors


# ---------------------------------------------------------------- 7. forbidden

def scan_forbidden() -> list[tuple[str, int, str]]:
    findings: list[tuple[str, int, str]] = []
    if not SRC.exists():
        return findings
    for path in sorted(SRC.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        rel = str(path.relative_to(ROOT))
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as e:
            findings.append((rel, e.lineno or 0, f"SyntaxError: {e.msg}"))
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Assert):
                findings.append((rel, node.lineno, "`assert` in src/ (constitution 7)"))
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in FORBIDDEN_CALLS:
                    findings.append(
                        (rel, node.lineno, f"`{node.func.id}()` in src/ (constitution 3/6)")
                    )
    return findings


# ---------------------------------------------------------------- main

def _print_section(title: str, errs: list[str], ok_msg: str,
                   findings: list[tuple[str, int, str]] | None = None) -> bool:
    print(f"\n== {title} ==")
    if findings is not None:
        if findings:
            print(f"  FAIL  ({len(findings)} finding(s))")
            for rel, lineno, desc in findings:
                print(f"    {rel}:{lineno}  {desc}")
            return False
        print(f"  OK  — {ok_msg}")
        return True
    if errs:
        print("  FAIL")
        for e in errs:
            print(f"    - {e}")
        return False
    print(f"  OK  — {ok_msg}")
    return True


def main() -> int:
    print(f"root: {ROOT}")
    print(f"src exists: {SRC.exists()}")

    results: list[bool] = []

    results.append(_print_section(
        "1. Imports", check_imports(),
        "every src/*.py imports cleanly"))

    results.append(_print_section(
        "2. Schema", check_schema(),
        "evals/schema.json valid + required fields present"))

    if _module_missing("config"):
        print("\n== 3. Config ==")
        print("  SKIP — src/config.py not generated yet")
    else:
        results.append(_print_section(
            "3. Config", check_config(),
            ".env loader: parses, env wins, missing raises RuntimeError"))

    if _module_missing("provider"):
        print("\n== 4. Provider ==")
        print("  SKIP — src/provider.py not generated yet")
    else:
        results.append(_print_section(
            "4. Provider", check_provider(),
            "FakeProvider returns preset; LLMProvider base raises; missing-key path clean"))

    if _module_missing("guardrails"):
        print("\n== 5. Guardrails ==")
        print("  SKIP — src/guardrails.py not generated yet")
    else:
        results.append(_print_section(
            "5. Guardrails", check_guardrails(),
            "safe_envelope schema-valid; destructive + PII cases handled"))

    if _module_missing("agent") or _module_missing("provider"):
        print("\n== 6. Agent offline ==")
        print("  SKIP — src/agent.py or src/provider.py not generated yet")
    else:
        results.append(_print_section(
            "6. Agent offline", check_agent_offline(),
            "parse() never raises on empty/malformed input"))

    forbidden = scan_forbidden()
    results.append(_print_section(
        "7. Forbidden constructs in src/", [],
        "no print/eval/exec/assert in src/",
        findings=forbidden))

    overall = all(results)
    print("\nOVERALL:", "PASS" if overall else "FAIL")
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())