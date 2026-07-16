<!-- generated-by: goal-loop-compiler compact-v4 -->
# Validation: {{TASK_NAME}}

## Source

Derived from `GOAL_CONTRACT.md` Evidence Standard and Acceptance Criteria.
This file is the evidence gate and final audit rule source.

## Compile Phase Requirements

- Required files exist: `GOAL_CONTRACT.md`, `PLAN.md`, `STATE.json`, `VALIDATION.md`, `CHANGE_BRIEF.md`.
- These are the only default runtime package files; no legacy or prompt-only artifact is present.
- `GOAL_CONTRACT.md` contains non-restated Intent, Strategic Outcome, Decision Standard, Evidence Standard, Scope, Non-goals, Constraints, Pause Conditions, and Acceptance Criteria.
- `PLAN.md` states it is derived from `GOAL_CONTRACT.md` and does not redefine intent.
- `STATE.json` uses schema `compact-v4`, includes loop budget, open gaps, completion candidates, and source-of-truth map.
- `CHANGE_BRIEF.md` status is `pending`.
- `recurring_system` is not compiled as a finite goal package.

## Completion Phase Requirements

- Each Acceptance Criterion has real, reviewable evidence.
- `STATE.json.current_status` may be `Done` only when open gaps, blockers,
  `next_focus`, and `pause_reasons` are empty.
- `STATE.json.current_status` is not `Continue` after `max_cycles` or `no_progress_threshold` is reached.
- Required contract/drift gates have auditable `goal_loop_evaluator` records for the applicable cycle.
- `STATE.json.verification_delta` records an independent `pre_done` review by `goal_loop_evaluator` with verdict `pass`, the exact runtime-returned reviewer reference, matching canonical five-file artifact digest, current cycle, and all five reviewed artifacts before completion validation.
- `CHANGE_BRIEF.md` contains no unsupported behavior changes, result claims, or validation claims.
- A completed Change Brief has no stale `awaiting`, `pending`, or `remaining validation` language in Outcome or Unresolved Gaps.
- Non-goals and constraints were not violated.
- Verification includes target evidence, not only package structure checks.

## Required Evidence

- {{REQUIRED_EVIDENCE_ITEM}}

## Forbidden Completion Claims

- Do not claim tests, builds, screenshots, human review, production status, or external validation passed unless the actual evidence is present.
- Do not use `CHANGE_BRIEF.md` as evidence for itself.

## Source-of-truth Consistency Checks

- `GOAL_CONTRACT.md` is the only semantic source.
- `STATE.json` is the only runtime state source.
- `VALIDATION.md` is the only evidence gate.
- `CHANGE_BRIEF.md` is the only human delivery summary.
- Any launch prompt is chat text only and must not become package authority.
- `CONTINUATION_SUMMARY.md` may be exported outside the goal directory only after a Continue or Pause decision and must state that `STATE.json` remains the source of truth.

## Final Evaluator

### Role

You are a read-only evaluator. Do not edit files.

### Required Checks

- Contract alignment: Does the result satisfy Goal, Intent, Strategic Outcome, Decision Standard, and Acceptance Criteria?
- Evidence: Is every completion claim supported by actual command output, diff, screenshot, artifact, or user-provided evidence?
- Scope: Were Scope, Non-goals, Constraints, and Pause Conditions respected?
- State: Is `STATE.json` consistent with evidence and remaining gaps?
- Loop control: Were cycle limits, no-progress handling, and independent review gates respected?
- Change Brief truthfulness: Does `CHANGE_BRIEF.md` accurately summarize only proven behavior changes, validation evidence, risks, manual review focus, and rollback notes?

### Verdict Format

```text
verdict: pass | revise | blocked
summary:
acceptance_criteria:
scope_or_non_goal_issues:
evidence_gaps:
change_brief_truthfulness:
  status: pass | revise | blocked
  unsupported_claims:
  missing_human_context:
  validation_evidence_mapping:
  manual_verification_reality:
  rollback_reality:
state_consistency:
recommended_next_step:
requires_human: yes | no
```
