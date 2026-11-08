# Harness Log — Part 1B

## 0. Model & configuration (no secrets)
- Provider: (Gemini free tier | Ollama local)
- Model id: (e.g. gemini-2.0-flash, or the newest free-tier model listed in AI Studio)
- Judge model: 
- Judge prompt hash (sha256 of `.harness/judge_prompt.txt`): 
- Temperature: 0.2
- **Threshold declared pre-run:** >=13/15 AND all safety_critical pass (spec.md §5)
- Date runs: 

## 1. Initial generation
- Context given: constitution, spec, clarify, plan, tasks, evals/schema.json
- Agent/model: 
- Snapshot: `evidence/initial-generation/`

## 2. Evaluation run #1
- Command: `python .harness/evaluation_runner.py`
- File: `evidence/eval-results/run-1.json`
- Result: passed=__/15 (need 13), safety_ok=___
- Failing cases (paste from run-1.json):
  - Case ___: schema_errors / invariant_errors / semantic:
    ```
    <paste>
    ```
  - Case ___: 
- Root causes:
  - 

## 3. Feedback to agent
- Attached: `evidence/eval-results/run-1.json` + relevant spec sections
- Instruction: "Fix prompts/guardrails/agent. Do NOT edit evals. Do NOT lower threshold."

## 4. Repair
- Files changed: prompts.py / guardrails.py / agent.py (which and why)
- Diff: `evidence/final-generation/diff.patch`
- Spec unchanged: yes / no (if no, explain the legitimate upstream revision)

## 5. Evaluation run #2
- Command: `python .harness/evaluation_runner.py`
- File: `evidence/eval-results/run-2.json`
- Result: passed=__/15, safety_ok=___
- Note: threshold unchanged, no cases deleted.

## 6. Human decision
- Reviewer: 
- Decision: **ACCEPT** / **REJECT**
- Justification: 
- Known limitations (e.g. specific failing case): 
- Residual risk after PASS: 
- Additional control before production: 
