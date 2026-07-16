# Loop Runtime

Use this when initializing or updating `STATE.json`, deciding Continue/Done/Pause,
or preparing final evaluation.

## Runtime Loop

The loop is adaptive, not a fixed workflow:

`Anchor -> Observe -> Identify gap -> Decide -> Act -> Verify -> Reflect -> Write back -> Continue | Done | Pause`

The contract fixes result and boundaries. The loop keeps path autonomy inside
those boundaries.

## Cycle Accounting

- Increment `current_cycle` after each `Act -> Verify` attempt.
- Progress means new evidence closes or materially narrows an open gap.
- Reset `no_progress_count` to zero on progress; otherwise increment it.
- At `max_cycles` or `no_progress_threshold`, use `Pause` unless completion is already proven. Never run an extra cycle beyond the budget.

## STATE.json

`STATE.json` is the only runtime state source. Record only facts a future round
would otherwise have to rediscover:

- current status;
- current cycle;
- open gaps;
- closed evidence;
- completion candidates;
- verification delta;
- change brief status;
- next focus;
- pause reasons;
- blockers;
- no-progress count;
- loop budget.

Do not use `STATE.json` to redefine intent, scope, non-goals, constraints, or
acceptance criteria.

## Continue / Done / Pause

- `Continue`: meaningful open gaps remain and the next action is within scope.
- `Done`: all acceptance criteria have evidence, no blocker remains, final
  evaluator verdict is `pass`, `next_focus` is empty, and `pause_reasons` is an
  empty list. Historical pause facts belong in `closed_evidence`, not active
  terminal controls.
- `Pause`: evidence is missing, route is wrong, scope must change, risk needs user judgment, or no-progress threshold is reached.

Use a fresh, read-only `goal_loop_evaluator` at the review gates defined in
`SKILL.md`. `strategic`, `repair`, and `governed` packages require contract and
pre-Done review. Ordinary `finite_goal` packages require pre-Done review only
after drift or no progress. Pass raw artifacts and the review question, not a
builder summary.
Record each result in `verification_delta` using:

```json
{"gate":"contract|drift|pre_done","reviewer":"goal_loop_evaluator","verdict":"pass|revise|blocked","review_ref":"<exact runtime reference>","artifact_digest":"sha256:<canonical five-file digest>","cycle":0,"reviewed_artifacts":["GOAL_CONTRACT.md","PLAN.md","STATE.json","VALIDATION.md","CHANGE_BRIEF.md"]}
```

Use cycle `0` for the contract gate and the current cycle for drift or pre-Done.
Copy the exact reviewer reference returned by the runtime: use its UUIDv7 when
one is exposed, otherwise use the returned task path such as
`/root/pre_done_evaluator`. Never invent or replace `review_ref`. The validator
checks record shape and state consistency; an external audit must compare the
reference and verdict with the runtime rollout because package files cannot
prove reviewer provenance. Only packages whose route or drift policy requires
independent review need a `pre_done` `pass` for `Done`. Records are
chronological; the latest verdict for a gate and cycle governs, and malformed
records invalidate the package. `revise` or `blocked` keeps the package at
`Continue` or `Pause`.

Compute `artifact_digest` with the installed validator's canonical digest
function. It hashes all five package files in filename order and canonicalizes
`STATE.json` with `verification_delta` set to an empty list, so adding the
review record does not create a circular hash. Completion validation requires
the latest passing pre-Done digest to match the final package.

```bash
python3 scripts/validate_package.py --phase review-digest <goal-dir>
```

`CONTINUATION_SUMMARY.md` is optional. Export it outside the goal directory
only after Continue or Pause, and state that it is derived from `STATE.json`.

## Native Goal Projection

After compile validation, render the native runtime goal with:

```bash
python3 scripts/validate_package.py --phase native-goal <goal-dir>
```

The returned `native_goal` text is a deterministic projection of
`GOAL_CONTRACT.md`; it includes the contract digest and exact Goal,
Constraints, Non-goals, Pause Conditions, and Acceptance Criteria. The Executor
passes that text unchanged to `create_goal`. Record or audit the returned
projection digest from the Codex rollout, because files alone cannot prove the
runtime objective. Once Native Goal starts, semantic contract changes require
Pause, recompile, re-projection, and a new Goal.

## Final Evaluation

The final evaluator is embedded in `VALIDATION.md`. It must be read-only and
must check:

- contract alignment;
- real evidence for each completion claim;
- scope, non-goals, constraints, and pause conditions;
- state consistency;
- Change Brief truthfulness.

Builder self-claims do not count as evidence.

## Finalization Order

1. Finish all target evidence and write the exact final human-facing content.
   Set the completion candidate to state `Done`, clear proven gaps, and set the
   Change Brief status to `completed`. Do not leave
   `awaiting`, `pending`, or `remaining validation` language in Outcome or
   Unresolved Gaps. Do not claim completion validation already passed.
2. Compute the canonical package digest and run the fresh pre-Done evaluator on
   this exact completion candidate. A `revise` or `blocked` verdict requires
   restoring `Continue`/`pending` before fixes.
3. After `pass`, add only the returned review record with its exact
   `review_ref`, verdict, and pre-review `artifact_digest`. Do not rewrite any
   other package content.
4. Run completion validation. If it passes, do not edit any package file again;
   report the validator result outside the package. If it fails, restore
   `Continue`/`pending`, record the new gap, fix it, and obtain another pre-Done
   review before trying completion again.

## Change Brief

`CHANGE_BRIEF.md` is the human handoff. It starts pending. During final
preparation, fill only evidence-backed facts. Immediately before computing the
pre-Done digest, mark it `completed` as a provisional completion candidate so
the evaluator reviews the exact terminal handoff. It is not accepted as final
until the evaluator and completion validator pass. On either failure, restore
`pending` before making further changes.

It must explain:

- outcome;
- behavior changes;
- key decisions;
- validation evidence;
- risks and limitations;
- human review hotspots;
- manual verification;
- rollback notes;
- judgeable example;
- unresolved gaps if not done.
