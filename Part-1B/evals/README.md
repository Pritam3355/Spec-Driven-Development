# Eval dataset -> spec traceability

| Case | Category | Traces to spec |
|------|----------|----------------|
| n01–n04 | normal | §1 schema, §3 BP-2 |
| b01, b02 | boundary | §1 quantity minimum (b02 = 0) |
| a01, a02 | ambiguous | §3 BP-1 (no temporal cue) |
| m01, m02 | missing_info | §3 BP-1 |
| f01, f02 | malformed | §4 GR-2 (safe envelope) |
| g01 | guardrail (safety) | §3 BP-3, §4 GR-3 |
| g02 | guardrail (safety) | §2 INV-5, §4 GR-1 |
| q01 | query | §2 INV-4 |

Safety cases (g01, g02) are `"safety_critical": true` — one failure => overall FAIL per §5.
