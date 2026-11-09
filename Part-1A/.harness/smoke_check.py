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
"""every src/*.py imports cleanly"""
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
"""daily_streak behaves per spec FR-3.2"""
def check_streaks() -> list[str]:
    """Exact spot checks against spec FR-3.2."""
    errors: list[str] = []
    try:
        from src.streaks import daily_streak
    except Exception as e:
        return [f"cannot import src.streaks.daily_streak: {e}"]
    try:
        from src.streaks import weekly_streak
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

"""DoW streak check (spec FR-3.5)"""
def check_dow_streak() -> list[str]:
    """v1.1 spot checks for days_of_week_streak (spec FR-3.5, T-15)."""
    errors: list[str] = []
    try:
        from src.streaks import days_of_week_streak
    except Exception as e:
        return [f"cannot import src.streaks.days_of_week_streak (v1.1 T-15): {e}"]

    MWF = frozenset({0, 2, 4})  # Python weekdays: Mon=0, Wed=2, Fri=4
    cases = [
        # name                          logs                                          today         expected
        ("MWF streak=5",
         ["2026-01-05","2026-01-07","2026-01-09","2026-01-12","2026-01-14"], "2026-01-14", 5),
        ("scheduled today unlogged => 0",
         ["2026-01-05","2026-01-07","2026-01-09"], "2026-01-12", 0),
        ("rest day preserves streak",
         ["2026-01-05","2026-01-07","2026-01-09"], "2026-01-10", 3),
        ("missed scheduled breaks even on rest day",
         ["2026-01-05","2026-01-07"], "2026-01-10", 0),
    ]
    for name, logs, today, expected in cases:
        try:
            got = days_of_week_streak(logs, today, MWF)
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

"""Service smoke (add/log/save/reload) 
HabitTracker end-to-end per spec FR-1/2/3/5
"""
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
""" Delete cascade check (spec FR-6)"""
def check_delete_cascade() -> list[str]:
    """v1.1 spot checks for delete_habit cascade (spec FR-6, T-13)."""
    errors: list[str] = []
    try:
        from src.service import HabitTracker
        from src.errors import HabitNotFoundError
    except Exception as e:
        return [f"import failed: {e}"]

    import datetime, json, tempfile
    data_path = pathlib.Path(tempfile.mkdtemp(prefix="habit-del-")) / "h.json"
    try:
        t = HabitTracker(data_path=data_path)
        h = t.add_habit("temp", "daily")
        today = datetime.datetime.now(datetime.timezone.utc).date()
        t.log(h.id, (today - datetime.timedelta(days=1)).isoformat())
        t.delete_habit(h.id)
        t.save()

        data = json.loads(data_path.read_text(encoding="utf-8"))
        if any(x["id"] == h.id for x in data["habits"]):
            errors.append("delete: habit still in store after save")
        if any(x["habit_id"] == h.id for x in data["logs"]):
            errors.append("delete: orphan logs remain after save — cascade broken")

        # second delete must raise (no tombstones, clarify Q11)
        try:
            HabitTracker(data_path=data_path).delete_habit(h.id)
            errors.append("delete: second delete did NOT raise HabitNotFoundError")
        except HabitNotFoundError:
            pass
    except AttributeError as e:
        errors.append(f"delete_habit missing on HabitTracker (v1.1 T-13): {e}")
    except Exception as e:
        errors.append(f"delete smoke raised {type(e).__name__}: {e}")
    return errors


# ---------------------------------------------------------------- main
"""CLI parser check (spec FR-7.1/7.2)"""

def check_cli_parser() -> list[str]:
    """v1.1 spot checks: delete subcommand + free-form DoW frequency (FR-7)."""
    errors: list[str] = []
    try:
        from src.cli import build_parser
    except Exception as e:
        return [f"cannot import src.cli.build_parser: {e}"]

    parser = build_parser()

    try:
        args = parser.parse_args(["delete", "abc-123"])
        if getattr(args, "command", None) != "delete":
            errors.append(f"delete subcommand: command={args.command!r}")
        if getattr(args, "habit_id", None) != "abc-123":
            errors.append(f"delete subcommand: habit_id={args.habit_id!r}")
    except SystemExit:
        errors.append("delete subcommand not recognized (v1.1 T-16)")

    try:
        args = parser.parse_args(["add", "gym", "[Mon,Wed,Fri]"])
        if args.frequency != "[Mon,Wed,Fri]":
            errors.append(f"add DoW frequency: got {args.frequency!r}")
    except SystemExit:
        errors.append(
            "add with DoW frequency rejected — argparse must NOT restrict "
            "choices; validation lives in service (plan D9, FR-7.2)"
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

    print("\n== 4. DoW streak spot checks (v1.1) ==")
    dow_errors = check_dow_streak()
    if dow_errors:
        print("  FAIL")
        for e in dow_errors:
            print(f"    - {e}")
    else:
        print("  OK  — days_of_week_streak behaves per spec FR-3.5")

    print("\n== 5. Delete cascade (v1.1) ==")
    del_errors = check_delete_cascade()
    if del_errors:
        print("  FAIL")
        for e in del_errors:
            print(f"    - {e}")
    else:
        print("  OK  — delete_habit cascades and rejects double-delete")

    print("\n== 6. CLI parser (v1.1) ==")
    cli_errors = check_cli_parser()
    if cli_errors:
        print("  FAIL")
        for e in cli_errors:
            print(f"    - {e}")
    else:
        print("  OK  — delete subcommand and DoW frequency parse")

    print("\n== 7. Forbidden constructs in src/ ==")
    findings = scan_forbidden()
    if findings:
        print(f"  FAIL  ({len(findings)} finding(s))")
        for rel, lineno, desc in findings:
            print(f"    {rel}:{lineno}  {desc}")
    else:
        print("  OK  — no print/eval/exec/assert in src/")

    overall = not (
        imp_errors or streak_errors or svc_errors or dow_errors
        or del_errors or cli_errors or findings
    )
    print("\nOVERALL:", "PASS" if overall else "FAIL")
    return 0 if overall else 1
    


if __name__ == "__main__":
    sys.exit(main())