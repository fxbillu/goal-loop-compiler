# Goal Contract Quality

Use this when compiling `GOAL_CONTRACT.md` or reviewing contract quality.

## Alignment Chain

Every compact-v4 package must preserve this chain:

`Real Intent -> Strategic Outcome -> Decision Standard -> Evidence Standard -> Acceptance Criteria -> Required Evidence`

If any link is generic enough to fit another project after renaming the noun,
rewrite it with the user's actual context and wrong-turn risk.

## GoalPro-derived Intake

Capture:

- surface request;
- real intent;
- current dissatisfaction;
- strategic outcome;
- biggest wrong-turn risk;
- acceptance evidence.

`Intent` should explain the underlying result, dissatisfaction, or wrong-turn
risk when that adds decision value. If the surface request is already the most
accurate intent, keep it and let the validator emit a review warning rather than
inventing a paraphrase. `Strategic Outcome` must describe what becomes better,
not only which file or prompt is produced.

## Decision Standard

Write tradeoff rules that can decide conflicts:

- speed vs. evidence;
- compact package vs. source-of-truth clarity;
- local implementation vs. public interface changes;
- exploration value vs. human understandability;
- continuing vs. pausing.

Avoid vague standards such as "high quality" unless they are tied to evidence.

## Evidence Gate

Require evidence before finalizing a strategic, governed, external-fact,
platform-version, legal, pricing, standards, or research-dependent contract.

Evidence is useful only if it changes at least one of:

- Decision Standard;
- Evidence Standard;
- Scope;
- Non-goals;
- Execution Policy;
- Verification;
- Pause Conditions;
- Loop Budget.

If evidence is insufficient, emit a draft package or research plan instead of a
final execution package.

## Source-of-truth Discipline

- `GOAL_CONTRACT.md` owns semantics.
- `PLAN.md` may derive actions but must not override semantics.
- `STATE.json` owns runtime status only.
- `VALIDATION.md` owns evidence checks and final evaluator rubric.
- `CHANGE_BRIEF.md` explains proven results to humans and is not evidence for itself.
