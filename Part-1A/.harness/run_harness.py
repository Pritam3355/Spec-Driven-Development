#!/usr/bin/env python3
"""Part 1A harness — independent deterministic validator.

Run:  python .harness/run_harness.py
Gates: ruff (config .harness/ruff.toml), bandit SAST (.harness/bandit.yaml),
pytest at >=50% coverage. Writes evidence/harness-runs/run-N.json (auto-numbered).
"""
import datetime
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "evidence" / "harness-runs"

GATES = [
    {"name": "lint",
     "cmd": ["ruff", "check", "--config", ".harness/ruff.toml", "src", "tests"]},
    {"name": "security",
     "cmd": ["bandit", "-c", ".harness/bandit.yaml", "-r", "src", "-q"]},
    {"name": "tests",
     "cmd": ["pytest", "-q", "tests", "--cov=src",
             "--cov-report=term-missing", "--cov-fail-under=50"]},
]

def run(g):
    try:
        p = subprocess.run(g["cmd"], cwd=ROOT, capture_output=True, text=True)
        rc = p.returncode
        out, err = p.stdout[-4000:], p.stderr[-4000:]
    except FileNotFoundError as e:
        rc = 127
        out, err = "", str(e)
    return {"gate": g["name"], "command": " ".join(g["cmd"]),
            "exit_code": rc,
            "status": "PASS" if rc == 0 else "FAIL",
            "stdout": out, "stderr": err}

def next_run_path() -> pathlib.Path:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    n = 1
    while (EVIDENCE_DIR / f"run-{n}.json").exists():
        n += 1
    return EVIDENCE_DIR / f"run-{n}.json"

if __name__ == "__main__":
    results = [run(g) for g in GATES]
    overall = "PASS" if all(r["status"] == "PASS" for r in results) else "FAIL"
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    report = {"timestamp": now.replace("+00:00", "Z"),
              "overall": overall, "gates": results}
    path = next_run_path()
    path.write_text(json.dumps(report, indent=2))
    print(f"evidence file: {path.relative_to(ROOT)}")
    print(json.dumps({r["gate"]: r["status"] for r in results}, indent=2))
    print("OVERALL:", overall)
    sys.exit(0 if overall == "PASS" else 1)
