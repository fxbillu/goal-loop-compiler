---
name: goal-loop-compiler
description: Use when a non-trivial finite task needs a file-shaped, verifiable, stoppable Goal Loop package. Compile GoalPro-style intent, evidence, scope, state, validation, and human handoff into compact V4 artifacts. Do not use for recurring automation, monitoring, daily/weekly routines, or prompt-only GoalPro output.
---

# Goal Loop Compiler compact-v4

Compile a finite intention into a compact execution package that an agent can
execute, verify, pause, and explain to a human.

GoalPro is the semantic blueprint. V4 is the durable package authority. Native
Goal is the package's deterministic runtime projection, not a second authored
goal. Do not create `Goal Prompt`, `Loop Prompt`, or `Launch Prompt` artifacts.

## Alignment

Classify before package creation:

- `one_shot`: simple and low risk; handle directly without a package.
- `finite_goal`: clear terminal result with verifiable evidence.
- `strategic`: route, architecture, or long-term decision; require evidence.
- `repair`: prior output ran off course; diagnose before compiling a fix.
- `governed`: high-risk, release, permission, data, or production-adjacent work.
- `recurring_system`: ongoing automation, monitoring, operations, or routine; do not compile a finite package.

Output a Goal Alignment Card before compiling. Include the route, package mode,
Goal, Success Evidence, Boundaries, and Stop / Pause Rules.

Use `confirmed_by_request` only when all four fields are explicit, the user
explicitly invokes this skill to compile, the work is safe and local, and no
material field was inferred. Label that status in the card and continue.

Use `literal_confirm_required` and wait for `confirm` when a material goal,
evidence, boundary, or stop rule was inferred; when the action is external,
destructive, costly, permission-changing, or materially expands scope; or when
the user explicitly requests a confirmation gate. A user-requested literal gate
always wins.

## Compiler Pipeline

After confirmation or `confirmed_by_request`:

1. `CLASSIFY`: choose the lifecycle route.
2. `INTENT_INTAKE`: derive surface request, real intent, dissatisfaction,
   strategic outcome, wrong-turn risk, and acceptance evidence.
3. `EVIDENCE_GATE`: for strategic, governed, external-fact, platform-version,
   legal, pricing, standards, or research work, collect evidence that changes at
   least one contract field.
4. `INVENTORY`: list affected instructions, templates, references, scripts,
   tests, and source-of-truth files before mutation.
5. `CONTRACT_COMPILE`: create exactly the five default package files.
6. `CONTRACT_REVIEW`: remove duplicate authority and run required review gates.
7. `LOOP_INITIALIZATION`: initialize state, gaps, budget, and next focus.
8. `EXPRESSION_ECONOMY`: remove repetition, never boundaries or evidence.

## Package And Authority

Create only:

```text
.goal/goals/<YYYY-MM-DD-task-slug>/
  GOAL_CONTRACT.md
  PLAN.md
  STATE.json
  VALIDATION.md
  CHANGE_BRIEF.md
```

- `GOAL_CONTRACT.md`: durable semantic source: goal, intent, scope, non-goals,
  constraints, pause conditions, acceptance criteria, and evidence standard.
- `PLAN.md`: derived execution strategy only; it never redefines semantics.
- `STATE.json`: runtime status, evidence, gaps, controls, and review records.
- `VALIDATION.md`: compile/completion gates and evaluator rubric.
- `CHANGE_BRIEF.md`: human summary, never self-evidence; starts `pending`.

`CONTINUATION_SUMMARY.md` is optional, outside the package, and only after
Continue or Pause. It must say that `STATE.json` remains authoritative.

## Native Goal Handoff

The Compiler completes after it creates the package, runs compile validation,
renders the Native Goal projection, reports its path and digests, and stops at
the Executor checkpoint. This is a phase boundary, not a required new chat.

Run:

```bash
python3 scripts/validate_package.py --phase compile <goal-dir>
python3 scripts/validate_package.py --phase native-goal <goal-dir>
```

The Executor normally continues in the same Codex task after the user sends
`execute`. It must pass the returned `native_goal` text unchanged to
`create_goal`, then read the full contract before acting. Native Goal freezes
contract semantics. If semantics need to change, Pause, recompile, re-render,
and start a new Native Goal.

Use a separate Executor task only for blind review, permission or workspace
isolation, or explicit user direction.

## Review Gates

Use a fresh, read-only `goal_loop_evaluator`. Give raw artifacts, evidence, and
a narrow question, never the builder's conclusion.

Independent contract and pre-Done review are required for `strategic`, `repair`,
and `governed` packages. A drift review is required after no progress or a
strategy change. Any drift record requires an independent pre-Done review.

For a stable ordinary `finite_goal`, use executor self-check, target evidence,
and static completion validation; do not add a reviewer merely by default.

A `revise` or `blocked` verdict prevents progression. If a required independent
review is unavailable, Pause. Record review provenance in
`STATE.json.verification_delta` as described in `references/loop-runtime.md`.

## Validation

```bash
python3 scripts/validate_package.py --phase compile <goal-dir>
python3 scripts/validate_package.py --phase review-digest <goal-dir>
python3 scripts/validate_package.py --phase native-goal <goal-dir>
python3 scripts/validate_package.py --phase completion <goal-dir>
```

Compile validation rejects missing or extra package files, prompt-only
artifacts, semantic conflicts, missing evidence rules, invalid state controls,
and recurring routes. An Intent that matches the surface request is a warning,
not a failure.

Completion validation rejects unsupported claims, incomplete acceptance evidence,
Done with active gaps or blockers, non-goal violations, malformed review
records, and a final evaluator that does not check Change Brief truthfulness.
It requires pre-Done review only when the route or drift policy requires it.

## References

Read only when needed:

- `references/goal-quality.md`: contract quality and evidence gates.
- `references/loop-runtime.md`: state, native handoff, reviews, and finalization.
- `references/quality-checklist.md`: compact-v4 delivery checks.

## Stop Conditions

Pause or hand off when the route is `recurring_system`, the request is
`one_shot`, required evidence is unavailable, completion requires a semantic
contract change, validation cannot establish confidence, or the next decision
needs human business judgment or high-risk permission.

Ask only for fields that change route, evidence, boundaries, or stop rules.
