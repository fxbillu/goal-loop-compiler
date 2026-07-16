# Compact-v4 Quality Checklist

Use before delivering a compiled package or skill update.

## Skill Structure

- `SKILL.md` contains only frontmatter `name` and `description`.
- `SKILL.md` is a concise router and workflow guide, not a template dump.
- Details live in `references/`.
- Templates live in `assets/`.
- Deterministic checks live in `scripts/`.
- No README, install guide, changelog, quick reference, or other clutter was added.

## Default Package

- Package path is `.goal/goals/<YYYY-MM-DD-task-slug>/`.
- Exactly these default files exist:
  - `GOAL_CONTRACT.md`
  - `PLAN.md`
  - `STATE.json`
  - `VALIDATION.md`
  - `CHANGE_BRIEF.md`
- Run the package validator to confirm no extra, legacy, or prompt-only artifact exists.

## Contract Quality

- Intent is not a restatement.
- Strategic Outcome is not just an artifact.
- Decision Standard can decide tradeoffs.
- Evidence Standard appears in `VALIDATION.md`.
- Scope, Non-goals, Constraints, and Pause Conditions are concrete.
- Acceptance Criteria are observable and evidence-backed.
- `recurring_system` never becomes a finite package.

## Runtime Quality

- `PLAN.md` is derived from `GOAL_CONTRACT.md` and does not override it.
- `STATE.json` has schema `compact-v4`, loop budget, open gaps, completion candidates, blockers, and source-of-truth map.
- `VALIDATION.md` contains compile checks, completion checks, source-of-truth checks, and final evaluator verdict format.
- `CHANGE_BRIEF.md` starts as `pending` and does not claim unproven results.

## Delivery

- Run `scripts/validate_package.py --phase compile <goal-dir>` on an example package.
- Run relevant unit tests for validator changes.
- Run skill quick validation.
- Update project dev log after substantive changes.
