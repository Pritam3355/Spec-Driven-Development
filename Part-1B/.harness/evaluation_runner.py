#!/usr/bin/env python3
"""Part 1B harness — 3-layer evaluation.

Run:  python .harness/evaluation_runner.py
Writes evidence/eval-results/run-N.json (auto-numbered).
Threshold (fixed pre-run, spec.md §5): >=13/15 AND every safety_critical case passes.
"""
import datetime
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))   # for src.*
sys.path.insert(0, str(HERE))   # for harness modules

try:
    from src.agent import parse
except ImportError as exc:  # src/ not generated yet
    print("ERROR: src/ not importable — generate src/ first (harness-log.md §1).")
    print(f"detail: {exc}")
    sys.exit(2)

from invariant_checker import check_invariants
from schema_validator import validate_schema
from semantic_evaluator import semantic_score

DATASET = json.loads((ROOT / "evals" / "dataset.json").read_text())
THRESHOLD_PASS = 13
EVIDENCE_DIR = ROOT / "evidence" / "eval-results"

def next_run_path() -> pathlib.Path:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    n = 1
    while (EVIDENCE_DIR / f"run-{n}.json").exists():
        n += 1
    return EVIDENCE_DIR / f"run-{n}.json"

def run_case(case):
    try:
        out = parse(case["input"])
    except Exception as e:  # harness must never crash on one case  # noqa: BLE001
        return {"id": case["id"], "category": case.get("category"),
                "status": "FAIL", "layer": "app", "error": str(e),
                "safety_critical": bool(case.get("safety_critical"))}
    e1 = validate_schema(out)
    e2 = check_invariants(out, case) if not e1 else ["skipped: schema errors"]
    sem = semantic_score(case, out) if not (e1 or e2) else {"score": 0.0, "reason": "skipped"}
    passed = not e1 and not e2 and sem["score"] >= 0.7
    return {"id": case["id"], "category": case.get("category"),
            "status": "PASS" if passed else "FAIL",
            "safety_critical": bool(case.get("safety_critical")),
            "output": out, "schema_errors": e1,
            "invariant_errors": e2, "semantic": sem}

if __name__ == "__main__":
    results = [run_case(c) for c in DATASET]
    passed = sum(r["status"] == "PASS" for r in results)
    safety_failures = [r["id"] for r in results
                       if r.get("safety_critical") and r["status"] != "PASS"]
    safety_ok = not safety_failures
    overall = "PASS" if (passed >= THRESHOLD_PASS and safety_ok) else "FAIL"
    now = datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")
    report = {"timestamp": now.replace("+00:00", "Z"),
              "overall": overall, "passed": passed, "total": len(results),
              "threshold": THRESHOLD_PASS, "safety_ok": safety_ok,
              "safety_failures": safety_failures, "results": results}
    path = next_run_path()
    path.write_text(json.dumps(report, indent=2))
    print(f"evidence file: {path.relative_to(ROOT)}")
    print(f"passed {passed}/{len(results)} (threshold {THRESHOLD_PASS})  safety_ok={safety_ok}")
    print("OVERALL:", overall)
    sys.exit(0 if overall == "PASS" else 1)
