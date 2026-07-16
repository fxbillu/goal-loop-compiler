---
name: goal-loop-compiler
description: Use when a non-trivial finite task should become a file-shaped, verifiable, stoppable Goal Loop execution package. Compile GoalPro-style intent, decision, evidence, scope, state, validation, and Change Brief structure into a compact V4 package after a Goal Alignment Card is confirmed. Do not use for recurring automation, monitoring, daily/weekly routines, or prompt-only GoalPro output.
---

# Goal Loop Compiler compact-v4

Compile a user's intention into a small finite execution package that another
agent can execute, verify, pause, and explain back to a human.

GoalPro is the semantic blueprint. V4 is the file-shaped runtime authority.
Do not output `Goal Prompt`, `Loop Prompt`, or `Launch Prompt` as package
artifacts. A launch prompt is chat text only, never source of truth.

## First Response

When invoked, do not create files or execute work immediately. First output:

```md
# Goal Alignment Card

## My Understanding
<one-sentence interpretation>

## Proposed Route
one_shot | finite_goal | strategic | repair | governed | recurring_system

Reason:
<short reason>

## Proposed Package Mode
Delivery / Experiment / Not a finite package

## Please Confirm

### Goal
Suggested default:
<finite result to achieve or discover>

### Success Evidence
Suggested default:
<tests, diff, screenshot, data result, audit verdict, or manual evidence>

### Boundaries
Suggested default:
<allowed paths/actions and forbidden changes>

### Stop / Pause Rules
Suggested default:
<max cycles, no-progress rule, missing evidence rule, human review trigger>

Reply `confirm` to use the defaults, or edit any field.
```

Wait for explicit confirmation before creating files, compiling a package, or
executing work. There is no best-judgment bypass for this skill.

## Router

Classify before package creation:

- `one_shot`: simple, low-risk, better handled directly. Do not create a full package.
- `finite_goal`: clear terminal result with verifiable evidence.
- `strategic`: route/architecture/long-term decision; require evidence gate before package completion.
- `repair`: previous output ran off course; diagnose failure before compiling the fix package.
- `governed`: high-risk, multi-file, production-adjacent, permissions, data, or release work; require inventory and pause gates.
- `recurring_system`: daily, weekly, automatic, monitoring, operations, release queue, long-running review, or background loop. Do not compile as a finite package; return a handoff or system-loop proposal.

Use lifecycle first. Keywords are weak signals. If a request mixes setup and
ongoing operation, compile only the finite setup milestone or route to
`recurring_system`.

## Compiler Pipeline

After confirmation, run these stages:

1. `CLASSIFY`: choose the lifecycle route above.
2. `INTENT_INTAKE`: derive surface request, real intent, dissatisfaction, strategic outcome, wrong-turn risk, and acceptance evidence.
3. `EVIDENCE_GATE`: for strategic, governed, external-fact, platform-version, legal, pricing, standards, or user-requested research work, collect evidence before finalizing the contract. Evidence must change at least one contract field.
4. `WORKFLOW_LENS`: detect repeating work only to route or annotate. Never create automation here.
5. `INVENTORY`: list affected skill instructions, templates, references, scripts, tests, and source-of-truth files before mutation.
6. `CONTRACT_COMPILE`: create exactly the default package files.
7. `CONTRACT_REVIEW`: check source-of-truth consistency, remove duplicate authority, and run any applicable adversarial gate below.
8. `LOOP_INITIALIZATION`: initialize state, open gaps, loop budget, and next focus.
9. `EXPRESSION_ECONOMY`: remove repetition, not judgment, boundaries, or evidence.

## Compiler Completion

The compiler is complete only when it has created exactly the five default
package files, run compile validation, and reported the package path and
result. Then stop. Product execution, product files, and `create_goal` belong
to a separate explicit Executor request.

## Adversarial Review Gates

Use a fresh, read-only `goal_loop_evaluator` subagent. Give it the raw package
artifacts, evidence, and a narrow review question, never the builder's
conclusion. Run it:

- after contract compile for `strategic`, `governed`, or `repair`, or when intent, scope, evidence, or authority remains ambiguous;
- when `no_progress_count` increases, strategy changes, or drift is suspected;
- before `Done` for every finite package.

A `revise` or `blocked` verdict prevents progression. Record the auditable
result defined in `references/loop-runtime.md` in `STATE.json.verification_delta`.
If independent pre-Done review is unavailable, `Pause`; do not self-approve.

## Default Package

Create files under:

```text
.goal/goals/<YYYY-MM-DD-task-slug>/
  GOAL_CONTRACT.md
  PLAN.md
  STATE.json
  VALIDATION.md
  CHANGE_BRIEF.md
```

Create no other runtime package artifacts. The validator enforces legacy and
prompt-only artifact exclusions.

After Continue or Pause, a `CONTINUATION_SUMMARY.md` may be exported outside
the goal directory; it must state that `STATE.json` remains authoritative.

## Source-of-truth Map

- `GOAL_CONTRACT.md`: only semantic source. Holds goal, intent, strategic outcome, decision standard, evidence standard, scope, non-goals, constraints, pause conditions, human completion standard, and acceptance criteria.
- `PLAN.md`: derived execution strategy. It may list context, inventory, policy, checkpoints, slices, and per-slice verification. It must not redefine intent or scope.
- `STATE.json`: only runtime state. Holds status, cycle, open gaps, closed evidence, completion candidates, verification delta, change brief status, next focus, pause reasons, blockers, and loop budget.
- `VALIDATION.md`: only evidence gate. Holds compile checks, completion checks, source-of-truth checks, and the embedded final evaluator rubric.
- `CHANGE_BRIEF.md`: only human delivery summary. It is not evidence for itself and starts as `pending`.

Use the templates in `assets/`:

- `GOAL_CONTRACT.template.md`
- `PLAN.template.md`
- `STATE.template.json`
- `VALIDATION.template.md`
- `CHANGE_BRIEF.template.md`

## Validation

For deterministic package checks, use:

```bash
cd <goal-loop-compiler skill directory>
python3 scripts/validate_package.py --phase compile <goal-dir>
python3 scripts/validate_package.py --phase review-digest <goal-dir>
python3 scripts/validate_package.py --phase completion <goal-dir>
```

Compile validation must fail on missing default files, old default files,
restated Intent, missing Evidence Standard in validation, `PLAN.md` intent
conflict, `CHANGE_BRIEF.md` not pending, or `recurring_system` as a finite
package. It must also reject invalid loop counters, budgets, or `Continue` at
a configured stop limit, plus missing required contract or drift reviews.

Completion validation must fail on unsupported completion claims, `Done` with
nonempty open gaps, blockers, `next_focus`, or `pause_reasons`, non-goal
violations, missing target evidence, missing independent `pre_done` pass, or a
final evaluator rubric that does not check Change Brief truthfulness. Follow the finalization order in
`references/loop-runtime.md`; after completion validation passes, do not mutate
the package again.

## References

Read references only when needed:

- `references/goal-quality.md`: GoalPro-derived contract quality and evidence gate rules.
- `references/loop-runtime.md`: state, continuation, final evaluation, and Change Brief rules.
- `references/quality-checklist.md`: pre-delivery checks for compact-v4 packages.

## Stop Conditions

Pause and report instead of compiling or continuing when:

- the route is `recurring_system`;
- the route is `one_shot`; handle it directly or return a short handoff instead of compiling a package;
- the user has not confirmed the alignment card;
- evidence is required but unavailable;
- completing the task requires changing goal, success evidence, boundaries, or stop rules;
- package files would create duplicate source of truth;
- validation cannot be run for a reason that affects completion confidence;
- the next decision requires human business judgment or high-risk permission.

## Reply Style

Be concise. Ask only for fields that change the route, success evidence,
boundaries, or stop rules. Provide defaults so the user can reply `confirm`.
