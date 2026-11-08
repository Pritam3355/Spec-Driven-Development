"""Layer 3 — semantic score, normalized against each case's declared expects.

score = earned / possible over the expectation keys present in `expect`,
capped at 1.0. Weights: intent 0.40, habit_contains 0.35, quantity 0.10,
unit 0.05, needs_clarification 0.30. Cases whose expect declares only
deterministic checks (e.g. g02 `no_pii_in_output`) are carried by Layers 1-2
and score 1.0 here. Pass bar 0.7 comes from spec.md §5.

To use an LLM judge instead, replace semantic_score() with a call to
provider.generate(JUDGE_PROMPT) and parse the JSON score; keep the return shape.
"""

_WEIGHTS = {"intent": 0.40, "habit_contains": 0.35, "quantity": 0.10,
            "unit": 0.05, "needs_clarification": 0.30}

def keyword_overlap(case: dict, out: dict) -> dict:
    exp = case.get("expect", {})
    earned = 0.0
    possible = 0.0
    misses: list[str] = []
    if "intent" in exp:
        possible += _WEIGHTS["intent"]
        if out.get("intent") == exp["intent"]:
            earned += _WEIGHTS["intent"]
        else:
            misses.append(f"intent {out.get('intent')!r} != {exp['intent']!r}")
    if "habit_contains" in exp:
        possible += _WEIGHTS["habit_contains"]
        name = (out.get("habit_name") or "").lower()
        if any(k in name for k in exp["habit_contains"]):
            earned += _WEIGHTS["habit_contains"]
        else:
            misses.append("habit_name missing expected keyword(s)")
    if "quantity" in exp:
        possible += _WEIGHTS["quantity"]
        try:
            ok = (out.get("quantity") is not None
                  and float(out["quantity"]) == float(exp["quantity"]))
        except (TypeError, ValueError):
            ok = False
        if ok:
            earned += _WEIGHTS["quantity"]
        else:
            misses.append("quantity mismatch")
    if "unit" in exp:
        possible += _WEIGHTS["unit"]
        if (out.get("unit") or "").lower() == str(exp["unit"]).lower():
            earned += _WEIGHTS["unit"]
        else:
            misses.append("unit mismatch")
    if "needs_clarification" in exp:
        possible += _WEIGHTS["needs_clarification"]
        if bool(out.get("needs_clarification")) == bool(exp["needs_clarification"]):
            earned += _WEIGHTS["needs_clarification"]
        else:
            misses.append("needs_clarification mismatch")
    score = 1.0 if possible == 0.0 else min(1.0, earned / possible)
    return {"score": round(score, 3), "reason": "; ".join(misses) or "all expects matched"}

def semantic_score(case: dict, out: dict) -> dict:
    return keyword_overlap(case, out)
