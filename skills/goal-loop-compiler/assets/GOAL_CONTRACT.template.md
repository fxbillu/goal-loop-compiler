<!-- generated-by: goal-loop-compiler compact-v4 -->
# Goal Contract: {{TASK_NAME}}

- Package path: `.goal/goals/{{TASK_SLUG}}/`
- Semantic source of truth: `GOAL_CONTRACT.md`

## Authority

This file is the only semantic source of truth for this finite goal package.
If chat history, old plans, `PLAN.md`, `STATE.json`, `VALIDATION.md`, or
`CHANGE_BRIEF.md` conflict with this contract, pause and resolve the conflict.

## Lifecycle Classification

- route: {{finite_goal|strategic|repair|governed}}
- rationale: {{WHY_THIS_ROUTE}}

Do not use this template for `one_shot` or `recurring_system` requests.

## Goal

{{ONE_SENTENCE_TASK}}

## Intent

- Surface request: {{USER_SURFACE_REQUEST}}
- Real intent: {{REAL_INTENT}}
- Current dissatisfaction: {{CURRENT_DISSATISFACTION}}
- Biggest wrong-turn risk: {{BIGGEST_WRONG_TURN_RISK}}

## Strategic Outcome

{{WHAT_BECOMES_BETTER_AND_WHY_IT_IS_WORTH_DOING}}

## Decision Standard

- {{TRADEOFF_OR_DONE_RULE}}

## Evidence Standard

- Required evidence: {{EVIDENCE_REQUIRED}}
- Trusted sources: {{SOURCE_OR_VERIFICATION_STANDARD}}
- Evidence that would change the plan: {{COUNTEREVIDENCE}}

## Scope

- {{IN_SCOPE_ITEM}}

## Non-goals

- {{NON_GOAL_ITEM}}

## Constraints

- {{HARD_CONSTRAINT}}

## Pause Conditions

- {{PAUSE_OR_ESCALATION_CONDITION}}

## Human-readable Completion Standard

The work is complete only when {{JUDGEABLE_COMPLETION_STANDARD}}.

## Acceptance Criteria

| ID | Observable result | Verification method | Required evidence |
|---|---|---|---|
| AC-01 | {{OBSERVABLE_RESULT}} | {{VERIFICATION_METHOD}} | {{REQUIRED_EVIDENCE}} |
