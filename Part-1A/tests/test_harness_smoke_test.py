from __future__ import annotations

import ast
import importlib
import pathlib
import sys
import traceback

ROOT = pathlib.Path(__file__).resolve().parents[1]   # Part-1A/
SRC = ROOT / "src"

FORBIDDEN_CALLS = {"print", "eval", "exec"}


# ---------------------------------------------------------------- 1. imports

def check_imports() -> list[str]:
    errors: list[str] = []
    if not SRC.exists():
        return [f"src/ not found at {SRC} (agent hasn't generated it yet?)"]

    has_init = (SRC / "__init__.py").exists()
    if not has_init:
        errors.append(
            "src/__init__.py missing — spec uses `from src.X import Y`, "
            "so this file is required. Add it or ask the agent to."
        )

    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(SRC))
    for path in sorted(SRC.glob("*.py")):
        if path.name == "__init__.py":
            continue
        candidates = [f"src.{path.stem}"] if has_init else [f"src.{path.stem}", path.stem]
        last_err = None
        ok = False
        for mod in candidates:
            try:
                importlib.import_module(mod)
                ok = True
                break
            except Exception as e:
                last_err = f"{mod}: {type(e).__name__}: {e}"
        if not ok:
            errors.append(f"{path.name} -> {last_err}")
    return errors


# ---------------------------------------------------------------- 2. spot checks

def check_streaks() -> list[str]:
    """Exact spot checks against spec FR-3.2."""
    errors: list[str] = []
    try:
        from src.streaks import daily_streak
    except Exception as e:
        return [f"cannot import src.streaks.daily_streak: {e}"]

    cases = [
        # name                       logs                                          today         expected
        ("3-day run ending today",  ["2026-01-01", "2026-01-02", "2026-01-03"], "2026-01-03", 3),
        ("gap (today missing)",     ["2026-01-01"],                           "2026-01-03", 0),
        ("empty log",               [],                                       "2026-01-03", 0),
    ]
    for name, logs, today, expected in cases:
        try:
            got = daily_streak(logs, today)
        except TypeError as e:
            errors.append(
                f"{name}: signature mismatch ({e}). If `logs` is list[LogEntry] "
                f"not list[str], adapt the input in this check."
            )
            continue
        except Exception as e:
            errors.append(f"{name}: raised {type(e).__name__}: {e}")
            continue
        if got != expected:
            errors.append(f"{name}: expected {expected}, got {got!r}")
    return errors


# ---------------------------------------------------------------- 3. AST scan

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
                findings.append((rel, node.lineno,
                                 "`assert` in src/  (constitution rule 7)"))
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in FORBIDDEN_CALLS:
                    findings.append((rel, node.lineno,
                                     f"`{node.func.id}()` in src/  (constitution rules 3 / 6)"))
    return findings


# ---------------------------------------------------------------- main

def main() -> int:
    print(f"root: {ROOT}")
    print(f"src exists: {SRC.exists()}\n")

    print("== 1. Imports ==")
    imp_errors = check_imports()
    if imp_errors:
        print("  FAIL")
        for e in imp_errors:
            print(f"    - {e}")
    else:
        print("  OK  — every src/*.py imports cleanly")

    print("\n== 2. Streak spot checks ==")
    streak_errors = check_streaks()
    if streak_errors:
        print("  FAIL")
        for e in streak_errors:
            print(f"    - {e}")
    else:
        print("  OK  — daily_streak behaves per spec FR-3.2")

    print("\n== 3. Forbidden constructs in src/ ==")
    findings = scan_forbidden()
    if findings:
        print(f"  FAIL  ({len(findings)} finding(s))")
        for rel, lineno, desc in findings:
            print(f"    {rel}:{lineno}  {desc}")
    else:
        print("  OK  — no print/eval/exec/assert in src/")

    overall = not (imp_errors or streak_errors or findings)
    print("\nOVERALL:", "PASS" if overall else "FAIL")
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())