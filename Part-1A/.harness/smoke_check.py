from __future__ import annotations

import ast
import importlib
import pathlib
import sys
# import traceback

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

        # cli.py is the designated output layer (constitution rule 3, clarify Q9)
        is_cli = path.name == "cli.py"

        for node in ast.walk(tree):
            if isinstance(node, ast.Assert):
                findings.append((rel, node.lineno,
                                 "`assert` in src/  (constitution rule 7)"))
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == "print" and is_cli:
                    continue                                    # allowed in cli.py
                if node.func.id in FORBIDDEN_CALLS:
                    findings.append((rel, node.lineno,
                                     f"`{node.func.id}()` in src/  (constitution rules 3 / 6)"))
    return findings

def check_service_smoke() -> list[str]:
    """End-to-end: add_habit -> log x2 -> streak=2 -> save -> reload -> streak=2.

    Exercises the full service layer (spec FR-1, FR-2, FR-3, FR-5) in one
    pass. Catches constructor-signature mismatches, missing auto-load on
    __init__, save/load roundtrip bugs, and streak logic errors — things
    py_compile cannot see.
    """
    errors: list[str] = []
    try:
        from src.service import HabitTracker
    except Exception as e:
        return [f"cannot import src.service.HabitTracker: {e}"]

    import datetime
    import tempfile

    data_path = pathlib.Path(tempfile.mkdtemp(prefix="habit-smoke-")) / "h.json"

    # construct
    try:
        t = HabitTracker(data_path=data_path)
    except TypeError as e:
        return [
            f"HabitTracker(data_path=...) rejected: {e}. "
            f"If the constructor uses a different kwarg or positional arg, "
            f"adapt this check (see plan D5)."
        ]
    except Exception as e:
        return [f"HabitTracker() raised {type(e).__name__}: {e}"]

    # add
    try:
        h = t.add_habit("run", "daily")
    except Exception as e:
        return [f"add_habit raised {type(e).__name__}: {e}"]
    if not getattr(h, "id", None):
        errors.append("add_habit returned a habit without .id")

    # log today + yesterday
    today = datetime.datetime.now(datetime.timezone.utc).date()
    yesterday = today - datetime.timedelta(days=1)
    try:
        t.log(h.id, today.isoformat())
        t.log(h.id, yesterday.isoformat())
    except Exception as e:
        errors.append(f"log raised {type(e).__name__}: {e}")
        return errors

    # streak in-memory
    try:
        got = t.current_streak(h.id)
    except Exception as e:
        errors.append(f"current_streak raised {type(e).__name__}: {e}")
        return errors
    if got != 2:
        errors.append(f"streak in-memory: expected 2, got {got!r}")

    # save
    try:
        t.save()
    except Exception as e:
        errors.append(f"save raised {type(e).__name__}: {e}")
        return errors
    if not data_path.exists():
        errors.append(f"save did not create {data_path}")
        return errors

    # reload — requires auto-load on __init__ from data_path
    try:
        t2 = HabitTracker(data_path=data_path)
    except Exception as e:
        errors.append(f"HabitTracker() on existing file raised {type(e).__name__}: {e}")
        return errors
    try:
        got2 = t2.current_streak(h.id)
    except Exception as e:
        errors.append(f"current_streak after reload raised {type(e).__name__}: {e}")
        return errors
    if got2 != 2:
        errors.append(
            f"streak after save/reload: expected 2, got {got2!r}. "
            f"Check that HabitTracker auto-loads from data_path on __init__ "
            f"(spec FR-5.3, FR-5.4; plan D5)."
        )
    return errors

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

    print("\n== 3. Service smoke (add/log/save/reload) ==")
    svc_errors = check_service_smoke()
    if svc_errors:
        print("  FAIL")
        for e in svc_errors:
            print(f"    - {e}")
    else:
        print("  OK  — HabitTracker end-to-end per spec FR-1/2/3/5")

    
    print("\n== 4. Forbidden constructs in src/ ==")
    findings = scan_forbidden()
    if findings:
        print(f"  FAIL  ({len(findings)} finding(s))")
        for rel, lineno, desc in findings:
            print(f"    {rel}:{lineno}  {desc}")
    else:
        print("  OK  — no print/eval/exec/assert in src/")

    overall = not (imp_errors or streak_errors or svc_errors or findings)
    print("\nOVERALL:", "PASS" if overall else "FAIL")
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())