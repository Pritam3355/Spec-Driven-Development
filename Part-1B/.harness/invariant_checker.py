"""Layer 2 — deterministic invariants from spec.md §2."""
import datetime, re

_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_CC = re.compile(r"\b\d{13,19}\b")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")

def check_invariants(out: dict, case: dict) -> list[str]:
    errs: list[str] = []
    if out.get("needs_clarification"):
        if not (out.get("clarification_question") or "").strip():
            errs.append("INV-1: clarification_question empty")
    if out.get("intent") == "log_entry":
        if not out.get("habit_name"): errs.append("INV-2: habit_name null")
        if not out.get("date"):       errs.append("INV-2: date null")
    if out.get("date"):
        try:
            dt = datetime.date.fromisoformat(out["date"])
            utc_today = datetime.datetime.now(datetime.timezone.utc).date()
            if dt > utc_today:
                errs.append("INV-3: future date")
        except Exception:
            errs.append("INV-3: not ISO-8601")
    if out.get("intent") == "query_streak" and not out.get("habit_name"):
        errs.append("INV-4: query_streak needs habit_name")
    blob = str(out)
    if _SSN.search(blob) or _CC.search(blob) or _EMAIL.search(blob):
        errs.append("INV-5: possible PII in output")
    return errs
