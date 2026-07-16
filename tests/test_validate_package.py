#!/usr/bin/env python3
"""Tests for compact-v4 Goal Loop package validation."""

from __future__ import annotations

import json
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "skills" / "goal-loop-compiler" / "scripts" / "validate_package.py"


class CompactV4ValidatorTests(unittest.TestCase):
    def review_digest(self, goal_dir: Path) -> str:
        digest = hashlib.sha256()
        required_files = {
            "GOAL_CONTRACT.md",
            "PLAN.md",
            "STATE.json",
            "VALIDATION.md",
            "CHANGE_BRIEF.md",
        }
        for filename in sorted(required_files):
            path = goal_dir / filename
            if filename == "STATE.json":
                state = json.loads(path.read_text(encoding="utf-8"))
                state["verification_delta"] = []
                content = json.dumps(
                    state,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
            else:
                content = path.read_text(encoding="utf-8")
            digest.update(filename.encode("utf-8"))
            digest.update(b"\0")
            digest.update(content.encode("utf-8"))
            digest.update(b"\0")
        return f"sha256:{digest.hexdigest()}"

    def refresh_review_digests(self, goal_dir: Path) -> None:
        state_path = goal_dir / "STATE.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        artifact_digest = self.review_digest(goal_dir)
        for review in state.get("verification_delta", []):
            review["artifact_digest"] = artifact_digest
        state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

    def run_validator(
        self,
        goal_dir: Path,
        *,
        phase: str = "compile",
        script: Path = SCRIPT,
    ) -> tuple[int, dict]:
        completed = subprocess.run(
            [sys.executable, str(script), "--phase", phase, str(goal_dir)],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if completed.stderr:
            self.fail(f"unexpected stderr: {completed.stderr}")
        return completed.returncode, json.loads(completed.stdout)

    def write_package(
        self,
        goal_dir: Path,
        *,
        route: str = "finite_goal",
        route_bullet: bool = True,
        omit_route: bool = False,
        state_route: str | None = None,
        real_intent: str = "Make the compiler package auditable without adding prompt-only artifacts.",
        include_plan_intent: bool = False,
        include_plan_scope: bool = False,
        brief_status: str = "pending",
        state_status: str = "Continue",
        current_cycle: int = 0,
        no_progress_count: int = 0,
        max_cycles: int = 3,
        no_progress_threshold: int = 2,
        contract_review_passed: bool = False,
        drift_review_passed: bool = False,
        pre_done_review_passed: bool = False,
        blockers: list[str] | None = None,
        open_gaps: list[str] | None = None,
        next_focus: str | None = None,
        pause_reasons: list[str] | None = None,
        change_brief_status: str | None = None,
        validation_evidence: str = "Pending final validation.",
        behavior_change: str = "Pending final validation.",
        weak_evaluator: bool = False,
        token_only_evaluator: bool = False,
        second_ac: bool = False,
        wrong_source_map: bool = False,
        contract_placeholder: bool = False,
    ) -> None:
        goal_dir.mkdir(parents=True, exist_ok=True)
        reviewed_artifacts = sorted(
            ["GOAL_CONTRACT.md", "PLAN.md", "STATE.json", "VALIDATION.md", "CHANGE_BRIEF.md"]
        )
        review_records = []
        if contract_review_passed:
            review_records.append(
                {
                    "gate": "contract",
                    "reviewer": "goal_loop_evaluator",
                    "verdict": "pass",
                    "review_ref": "/root/contract_evaluator",
                    "cycle": 0,
                    "reviewed_artifacts": reviewed_artifacts,
                }
            )
        if drift_review_passed:
            review_records.append(
                {
                    "gate": "drift",
                    "reviewer": "goal_loop_evaluator",
                    "verdict": "pass",
                    "review_ref": "/root/drift_evaluator",
                    "cycle": current_cycle,
                    "reviewed_artifacts": reviewed_artifacts,
                }
            )
        if pre_done_review_passed:
            review_records.append(
                {
                    "gate": "pre_done",
                    "reviewer": "goal_loop_evaluator",
                    "verdict": "pass",
                    "review_ref": "/root/pre_done_evaluator",
                    "cycle": current_cycle,
                    "reviewed_artifacts": reviewed_artifacts,
                }
            )
        route_line = "" if omit_route else (f"- route: {route}" if route_bullet else f"route: {route}")
        extra_ac = "\n| AC-02 | Change Brief is truthful | completion validator | AC-02 evidence |" if second_ac else ""
        goal_text = "{{ONE_SENTENCE_TASK}}" if contract_placeholder else "Upgrade the package contract."
        (goal_dir / "GOAL_CONTRACT.md").write_text(
            f"""# Goal Contract: Example

## Lifecycle Classification

{route_line}
- rationale: finite and testable

## Goal

{goal_text}

## Intent

- Surface request: Upgrade the package contract.
- Real intent: {real_intent}
- Current dissatisfaction: The old package had weak source-of-truth boundaries.
- Biggest wrong-turn risk: Reintroducing prompt-only artifacts.

## Strategic Outcome

Future agents can compile and verify a compact package without duplicate authority.

## Decision Standard

- Prefer source-of-truth clarity over extra files.

## Evidence Standard

- Required evidence: compile validation output and unit tests.

## Scope

- Compact package files.

## Non-goals

- No recurring automation.

## Constraints

- Do not create Goal Prompt.md or Loop Prompt.md.

## Pause Conditions

- Pause if recurring_system is requested.

## Acceptance Criteria

| ID | Observable result | Verification method | Required evidence |
|---|---|---|---|
| AC-01 | Five-file package validates | validator compile phase | JSON ok true |
{extra_ac}
""",
            encoding="utf-8",
        )
        plan_extra = "\n## Intent\n\nConflicting intent." if include_plan_intent else ""
        if include_plan_scope:
            plan_extra += "\n## Scope\n\nConflicting scope."
        (goal_dir / "PLAN.md").write_text(
            f"""# Plan: Example

## Source

Derived from `GOAL_CONTRACT.md`. This file must not redefine intent.

## Context to Read First

- SKILL.md

## Inventory

- Runtime package files

## Execution Policy

- Keep changes compact.
{plan_extra}
""",
            encoding="utf-8",
        )
        (goal_dir / "STATE.json").write_text(
            json.dumps(
                {
                    "schema_version": "compact-v4",
                    "lifecycle_route": state_route or route,
                    "current_status": state_status,
                    "current_cycle": current_cycle,
                    "open_gaps": open_gaps if open_gaps is not None else ["Need implementation"],
                    "closed_evidence": [],
                    "completion_candidates": [],
                    "verification_delta": review_records,
                    "change_brief_status": change_brief_status or brief_status,
                    "next_focus": (
                        next_focus
                        if next_focus is not None
                        else ("" if state_status == "Done" else "Implement compact package")
                    ),
                    "pause_reasons": pause_reasons or [],
                    "blockers": blockers or [],
                    "no_progress_count": no_progress_count,
                    "loop_budget": {
                        "max_cycles": max_cycles,
                        "no_progress_threshold": no_progress_threshold,
                    },
                    "source_of_truth": {
                        "semantic_contract": "GOAL_CONTRACT.md",
                        "execution_plan": "PLAN.md",
                        "runtime_state": "STATE.json",
                        "validation_gate": "VALIDATION.md",
                        "human_delivery": "CHANGE_BRIEF.md",
                    }
                    if not wrong_source_map
                    else {
                        "semantic_contract": "PLAN.md",
                        "execution_plan": "GOAL_CONTRACT.md",
                        "runtime_state": "STATE.json",
                        "validation_gate": "VALIDATION.md",
                        "human_delivery": "CHANGE_BRIEF.md",
                    },
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        evaluator = (
            """This evaluator mentions change_brief_truthfulness unsupported_claims missing_human_context validation_evidence_mapping manual_verification_reality rollback_reality state_consistency requires_human in prose only.
"""
            if token_only_evaluator
            else (
            """change_brief_truthfulness:
  unsupported_claims:
"""
            if weak_evaluator
            else """change_brief_truthfulness:
  unsupported_claims:
  missing_human_context:
  validation_evidence_mapping:
  manual_verification_reality:
  rollback_reality:
state_consistency:
requires_human:
"""
            )
        )
        (goal_dir / "VALIDATION.md").write_text(
            f"""# Validation: Example

## Compile Phase Requirements

- Required files exist.

## Completion Phase Requirements

- Evidence exists.

## Evidence Standard

- Compile validation output and unit tests.

## Required Evidence

- Unit test output.

## Final Evaluator

{evaluator}
""",
            encoding="utf-8",
        )
        (goal_dir / "CHANGE_BRIEF.md").write_text(
            f"""# Change Brief: Example

- Status: {brief_status}

## Outcome

{behavior_change}

## Behavior Changes

{behavior_change}

## Validation Evidence

{validation_evidence}
""",
            encoding="utf-8",
        )
        if review_records:
            self.refresh_review_digests(goal_dir)

    def test_complete_five_file_package_passes_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "package"
            self.write_package(goal_dir)

            returncode, result = self.run_validator(goal_dir)

        self.assertEqual(returncode, 0)
        self.assertTrue(result["ok"])

    def test_review_digest_is_stable_when_review_record_is_added(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "digest-stability"
            self.write_package(goal_dir)

            returncode, before = self.run_validator(goal_dir, phase="review-digest")
            state_path = goal_dir / "STATE.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["verification_delta"] = [
                {
                    "gate": "pre_done",
                    "reviewer": "goal_loop_evaluator",
                    "verdict": "pass",
                    "review_ref": "/root/pre_done_evaluator",
                    "artifact_digest": before["artifact_digest"],
                    "cycle": 0,
                    "reviewed_artifacts": sorted(
                        ["GOAL_CONTRACT.md", "PLAN.md", "STATE.json", "VALIDATION.md", "CHANGE_BRIEF.md"]
                    ),
                }
            ]
            state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
            _, after = self.run_validator(goal_dir, phase="review-digest")

        self.assertEqual(returncode, 0)
        self.assertEqual(before["artifact_digest"], after["artifact_digest"])

    def test_repository_cli_entrypoint_runs_shipped_validator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "repository-package"
            self.write_package(goal_dir)

            returncode, result = self.run_validator(goal_dir)

        self.assertEqual(returncode, 0)
        self.assertTrue(result["ok"])

    def test_empty_state_object_fails_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "empty-state"
            self.write_package(goal_dir)
            (goal_dir / "STATE.json").write_text("{}", encoding="utf-8")

            returncode, result = self.run_validator(goal_dir)

        self.assertEqual(returncode, 1)
        self.assertIn("STATE.json missing schema_version", result["diagnostics"])

    def test_partial_state_object_fails_compile(self) -> None:
        required_runtime_fields = (
            "closed_evidence",
            "change_brief_status",
            "next_focus",
            "pause_reasons",
            "blockers",
        )
        for missing_field in required_runtime_fields:
            with self.subTest(missing_field=missing_field), tempfile.TemporaryDirectory() as tmp:
                goal_dir = Path(tmp) / "partial-state"
                self.write_package(goal_dir)
                state_path = goal_dir / "STATE.json"
                state = json.loads(state_path.read_text(encoding="utf-8"))
                del state[missing_field]
                state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

                returncode, result = self.run_validator(goal_dir)

            self.assertEqual(returncode, 1)
            self.assertIn(f"STATE.json missing {missing_field}", result["diagnostics"])

    def test_missing_required_file_fails_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "missing"
            self.write_package(goal_dir)
            (goal_dir / "VALIDATION.md").unlink()

            returncode, result = self.run_validator(goal_dir)

        self.assertEqual(returncode, 1)
        self.assertFalse(result["ok"])
        self.assertIn("VALIDATION.md", result["missing_files"])

    def test_change_brief_not_pending_fails_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "brief"
            self.write_package(goal_dir, brief_status="completed")

            returncode, result = self.run_validator(goal_dir)

        self.assertEqual(returncode, 1)
        self.assertIn("CHANGE_BRIEF.md initial status must be pending", result["diagnostics"])

    def test_plan_intent_conflict_fails_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "plan-conflict"
            self.write_package(goal_dir, include_plan_intent=True)

            returncode, result = self.run_validator(goal_dir)

        self.assertEqual(returncode, 1)
        self.assertIn("PLAN.md must not redefine Intent", result["diagnostics"])

    def test_recurring_system_route_fails_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "recurring"
            self.write_package(goal_dir, route="recurring_system")

            returncode, result = self.run_validator(goal_dir)

        self.assertEqual(returncode, 1)
        self.assertTrue(any("recurring_system" in item for item in result["diagnostics"]))

    def test_one_shot_route_fails_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "one-shot"
            self.write_package(goal_dir, route="one_shot")

            returncode, result = self.run_validator(goal_dir)

        self.assertEqual(returncode, 1)
        self.assertTrue(any("one_shot" in item for item in result["diagnostics"]))

    def test_one_shot_route_without_bullet_fails_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "one-shot-no-bullet"
            self.write_package(goal_dir, route="one_shot", route_bullet=False)

            returncode, result = self.run_validator(goal_dir)

        self.assertEqual(returncode, 1)
        self.assertTrue(any("one_shot" in item for item in result["diagnostics"]))

    def test_old_default_file_fails_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "old-file"
            self.write_package(goal_dir)
            (goal_dir / "GOAL.md").write_text("# Old Goal\n", encoding="utf-8")

            returncode, result = self.run_validator(goal_dir)

        self.assertEqual(returncode, 1)
        self.assertIn("GOAL.md", result["unexpected_files"])

    def test_extra_prompt_txt_fails_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "extra-prompt"
            self.write_package(goal_dir)
            (goal_dir / "Goal Prompt.txt").write_text("prompt-only artifact", encoding="utf-8")

            returncode, result = self.run_validator(goal_dir)

        self.assertEqual(returncode, 1)
        self.assertIn("Goal Prompt.txt", result["unexpected_files"])

    def test_launch_prompt_md_fails_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "launch-prompt"
            self.write_package(goal_dir)
            (goal_dir / "Launch Prompt.md").write_text("# Launch Prompt\n", encoding="utf-8")

            returncode, result = self.run_validator(goal_dir)

        self.assertEqual(returncode, 1)
        self.assertIn("Launch Prompt.md", result["unexpected_files"])
        self.assertTrue(any("Launch Prompt.md" in item for item in result["diagnostics"]))

    def test_missing_route_fails_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "missing-route"
            self.write_package(goal_dir, omit_route=True)

            returncode, result = self.run_validator(goal_dir)

        self.assertEqual(returncode, 1)
        self.assertIn("GOAL_CONTRACT.md route is required", result["diagnostics"])

    def test_state_route_mismatch_fails_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "route-mismatch"
            self.write_package(goal_dir, route="finite_goal", state_route="governed")

            returncode, result = self.run_validator(goal_dir)

        self.assertEqual(returncode, 1)
        self.assertIn("STATE.json lifecycle_route must match GOAL_CONTRACT.md route", result["diagnostics"])

    def test_plan_semantic_scope_fails_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "plan-scope"
            self.write_package(goal_dir, include_plan_scope=True)

            returncode, result = self.run_validator(goal_dir)

        self.assertEqual(returncode, 1)
        self.assertTrue(any("PLAN.md must not redefine semantic section" in item for item in result["diagnostics"]))

    def test_unresolved_placeholder_fails_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "placeholder"
            self.write_package(goal_dir, contract_placeholder=True)

            returncode, result = self.run_validator(goal_dir)

        self.assertEqual(returncode, 1)
        self.assertIn("GOAL_CONTRACT.md contains unresolved template placeholder", result["diagnostics"])

    def test_done_with_blocker_fails_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "done-blocked"
            self.write_package(
                goal_dir,
                brief_status="completed",
                state_status="Done",
                blockers=["blocker: evaluator missing"],
                open_gaps=["blocker: evaluator missing"],
                change_brief_status="completed",
                validation_evidence="- pytest passed",
                behavior_change="Completed compact package.",
            )

            returncode, result = self.run_validator(goal_dir, phase="completion")

        self.assertEqual(returncode, 1)
        self.assertIn("STATE.json is Done with unresolved blockers", result["diagnostics"])

    def test_change_brief_claim_without_evidence_fails_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "unsupported-claim"
            self.write_package(
                goal_dir,
                brief_status="completed",
                state_status="Done",
                pre_done_review_passed=True,
                blockers=[],
                open_gaps=[],
                change_brief_status="completed",
                validation_evidence="Pending final validation.",
                behavior_change="Completed compact package.",
            )

            returncode, result = self.run_validator(goal_dir, phase="completion")

        self.assertEqual(returncode, 1)
        self.assertIn("CHANGE_BRIEF.md contains completion claims without validation evidence", result["diagnostics"])

    def test_draft_change_brief_fails_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "draft-brief"
            self.write_package(
                goal_dir,
                brief_status="draft",
                state_status="Done",
                blockers=[],
                open_gaps=[],
                change_brief_status="completed",
                validation_evidence="- AC-01: validator compile phase returned ok true.",
                behavior_change="Completed compact package.",
            )

            returncode, result = self.run_validator(goal_dir, phase="completion")

        self.assertEqual(returncode, 1)
        self.assertIn("CHANGE_BRIEF.md status must be completed for completion validation", result["diagnostics"])

    def test_completed_brief_with_stale_finalization_language_fails_completion(self) -> None:
        stale_phrases = (
            "The completed state is awaiting final completion-validator confirmation.",
            "Final completion-validator confirmation is the remaining command gate.",
        )
        for phrase in stale_phrases:
            with self.subTest(phrase=phrase), tempfile.TemporaryDirectory() as tmp:
                goal_dir = Path(tmp) / "stale-finalization"
                self.write_package(
                    goal_dir,
                    brief_status="completed",
                    state_status="Done",
                    pre_done_review_passed=True,
                    blockers=[],
                    open_gaps=[],
                    change_brief_status="completed",
                    validation_evidence="- AC-01: validator completion phase returned ok true.",
                    behavior_change="Completed compact package.",
                )
                brief_path = goal_dir / "CHANGE_BRIEF.md"
                brief_path.write_text(
                    brief_path.read_text(encoding="utf-8")
                    + f"\n## Unresolved Gaps if not Done\n\n{phrase}\n",
                    encoding="utf-8",
                )

                returncode, result = self.run_validator(goal_dir, phase="completion")

            self.assertEqual(returncode, 1)
            self.assertIn(
                "completed CHANGE_BRIEF.md contains stale finalization language",
                result["diagnostics"],
            )

    def test_completed_brief_with_closed_finalization_language_passes_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "closed-finalization"
            self.write_package(
                goal_dir,
                brief_status="completed",
                state_status="Done",
                pre_done_review_passed=True,
                blockers=[],
                open_gaps=[],
                change_brief_status="completed",
                validation_evidence="- AC-01: validator completion phase returned ok true.",
                behavior_change="Completed compact package.",
            )
            brief_path = goal_dir / "CHANGE_BRIEF.md"
            brief_path.write_text(
                brief_path.read_text(encoding="utf-8")
                + "\n## Unresolved Gaps if not Done\n\nNo delivery gaps remain.\n",
                encoding="utf-8",
            )
            self.refresh_review_digests(goal_dir)

            returncode, result = self.run_validator(goal_dir, phase="completion")

        self.assertEqual(returncode, 0)
        self.assertTrue(result["ok"])

    def test_negated_stale_words_do_not_fail_completion(self) -> None:
        terminal_phrases = (
            "No validation is pending.",
            "The validation is no longer pending.",
            "We are not awaiting completion confirmation.",
            "No remaining validation gaps exist.",
        )
        for phrase in terminal_phrases:
            with self.subTest(phrase=phrase), tempfile.TemporaryDirectory() as tmp:
                goal_dir = Path(tmp) / "negated-finalization"
                self.write_package(
                    goal_dir,
                    brief_status="completed",
                    state_status="Done",
                    pre_done_review_passed=True,
                    blockers=[],
                    open_gaps=[],
                    change_brief_status="completed",
                    validation_evidence="- AC-01: validator completion phase returned ok true.",
                    behavior_change="Completed compact package.",
                )
                brief_path = goal_dir / "CHANGE_BRIEF.md"
                brief_path.write_text(
                    brief_path.read_text(encoding="utf-8")
                    + f"\n## Unresolved Gaps if not Done\n\n{phrase}\n",
                    encoding="utf-8",
                )
                self.refresh_review_digests(goal_dir)

                returncode, result = self.run_validator(goal_dir, phase="completion")

            self.assertEqual(returncode, 0)
            self.assertTrue(result["ok"])

    def test_post_review_package_rewrite_fails_completion_digest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "post-review-rewrite"
            self.write_package(
                goal_dir,
                brief_status="completed",
                state_status="Done",
                pre_done_review_passed=True,
                blockers=[],
                open_gaps=[],
                change_brief_status="completed",
                validation_evidence="- AC-01: validator completion phase returned ok true.",
                behavior_change="Completed compact package.",
            )
            brief_path = goal_dir / "CHANGE_BRIEF.md"
            brief_path.write_text(
                brief_path.read_text(encoding="utf-8").replace(
                    "Completed compact package.",
                    "Rewritten after the evaluator pass.",
                    1,
                ),
                encoding="utf-8",
            )

            returncode, result = self.run_validator(goal_dir, phase="completion")

        self.assertEqual(returncode, 1)
        self.assertIn(
            "pre_done review artifact_digest does not match the final package",
            result["diagnostics"],
        )

    def test_weak_final_evaluator_fails_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "weak-evaluator"
            self.write_package(goal_dir, weak_evaluator=True)

            returncode, result = self.run_validator(goal_dir)

        self.assertEqual(returncode, 1)
        self.assertIn("VALIDATION.md final evaluator does not check Change Brief truthfulness", result["diagnostics"])

    def test_final_evaluator_with_template_subheadings_passes_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "template-evaluator-headings"
            self.write_package(goal_dir)
            validation_path = goal_dir / "VALIDATION.md"
            validation_text = validation_path.read_text(encoding="utf-8")
            validation_path.write_text(
                validation_text.replace(
                    "## Final Evaluator\n\n",
                    "## Final Evaluator\n\n### Role\n\nRead-only evaluator.\n\n### Verdict Format\n\n",
                ),
                encoding="utf-8",
            )

            returncode, result = self.run_validator(goal_dir)

        self.assertEqual(returncode, 0)
        self.assertTrue(result["ok"])

    def test_token_only_final_evaluator_fails_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "token-only-evaluator"
            self.write_package(goal_dir, token_only_evaluator=True)

            returncode, result = self.run_validator(goal_dir)

        self.assertEqual(returncode, 1)
        self.assertIn("VALIDATION.md final evaluator does not check Change Brief truthfulness", result["diagnostics"])

    def test_wrong_source_map_fails_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "wrong-source-map"
            self.write_package(goal_dir, wrong_source_map=True)

            returncode, result = self.run_validator(goal_dir)

        self.assertEqual(returncode, 1)
        self.assertIn("STATE.json source_of_truth must match compact-v4 canonical map", result["diagnostics"])

    def test_non_positive_loop_budget_fails_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "invalid-loop-budget"
            self.write_package(goal_dir, max_cycles=0)

            returncode, result = self.run_validator(goal_dir)

        self.assertEqual(returncode, 1)
        self.assertIn("STATE.json loop_budget.max_cycles must be a positive integer", result["diagnostics"])

    def test_continue_at_max_cycles_fails_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "cycle-limit"
            self.write_package(goal_dir, current_cycle=3, max_cycles=3)

            returncode, result = self.run_validator(goal_dir)

        self.assertEqual(returncode, 1)
        self.assertIn("STATE.json must Pause when max_cycles is reached", result["diagnostics"])

    def test_continue_at_no_progress_threshold_fails_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "no-progress-limit"
            self.write_package(goal_dir, no_progress_count=2, no_progress_threshold=2)

            returncode, result = self.run_validator(goal_dir)

        self.assertEqual(returncode, 1)
        self.assertIn("STATE.json must Pause when no_progress_threshold is reached", result["diagnostics"])

    def test_pause_beyond_max_cycles_fails_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "over-budget-pause"
            self.write_package(goal_dir, state_status="Pause", current_cycle=4, max_cycles=3)

            returncode, result = self.run_validator(goal_dir)

        self.assertEqual(returncode, 1)
        self.assertIn("STATE.json current_cycle must not exceed loop_budget.max_cycles", result["diagnostics"])

    def test_pause_at_loop_limits_passes_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "paused-at-limit"
            self.write_package(
                goal_dir,
                state_status="Pause",
                current_cycle=3,
                no_progress_count=2,
                max_cycles=3,
                no_progress_threshold=2,
                drift_review_passed=True,
            )

            returncode, result = self.run_validator(goal_dir)

        self.assertEqual(returncode, 0)
        self.assertTrue(result["ok"])

    def test_done_at_max_cycles_passes_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "done-at-limit"
            self.write_package(
                goal_dir,
                brief_status="completed",
                state_status="Done",
                current_cycle=3,
                pre_done_review_passed=True,
                blockers=[],
                open_gaps=[],
                change_brief_status="completed",
                validation_evidence="- AC-01: validator completion phase returned ok true.",
                behavior_change="Completed compact package.",
            )

            returncode, result = self.run_validator(goal_dir, phase="completion")

        self.assertEqual(returncode, 0)
        self.assertTrue(result["ok"])

    def test_missing_acceptance_evidence_fails_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "missing-ac-evidence"
            self.write_package(
                goal_dir,
                second_ac=True,
                brief_status="completed",
                state_status="Done",
                blockers=[],
                open_gaps=[],
                change_brief_status="completed",
                validation_evidence="- AC-01: validator compile phase returned ok true.",
                behavior_change="Completed compact package.",
            )

            returncode, result = self.run_validator(goal_dir, phase="completion")

        self.assertEqual(returncode, 1)
        self.assertIn(
            "CHANGE_BRIEF.md Validation Evidence must map evidence to every acceptance criterion",
            result["diagnostics"],
        )

    def test_done_without_independent_pre_done_review_fails_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "missing-pre-done-review"
            self.write_package(
                goal_dir,
                brief_status="completed",
                state_status="Done",
                blockers=[],
                open_gaps=[],
                change_brief_status="completed",
                validation_evidence="- AC-01: validator completion phase returned ok true.",
                behavior_change="Completed compact package.",
            )

            returncode, result = self.run_validator(goal_dir, phase="completion")

        self.assertEqual(returncode, 1)
        self.assertIn(
            "STATE.json verification_delta must record a passing pre_done review record",
            result["diagnostics"],
        )

    def test_incomplete_pre_done_review_record_fails_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "incomplete-pre-done-review"
            self.write_package(
                goal_dir,
                brief_status="completed",
                state_status="Done",
                blockers=[],
                open_gaps=[],
                change_brief_status="completed",
                validation_evidence="- AC-01: validator completion phase returned ok true.",
                behavior_change="Completed compact package.",
            )
            state_path = goal_dir / "STATE.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["verification_delta"] = [
                {"gate": "pre_done", "reviewer": "goal_loop_evaluator", "verdict": "pass"}
            ]
            state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

            returncode, result = self.run_validator(goal_dir, phase="completion")

        self.assertEqual(returncode, 1)
        self.assertIn(
            "STATE.json verification_delta must record a passing pre_done review record",
            result["diagnostics"],
        )

    def test_later_pre_done_revise_blocks_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "revised-after-pass"
            self.write_package(
                goal_dir,
                brief_status="completed",
                state_status="Done",
                pre_done_review_passed=True,
                blockers=[],
                open_gaps=[],
                change_brief_status="completed",
                validation_evidence="- AC-01: validator completion phase returned ok true.",
                behavior_change="Completed compact package.",
            )
            state_path = goal_dir / "STATE.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["verification_delta"].append(
                {
                    "gate": "pre_done",
                    "reviewer": "goal_loop_evaluator",
                    "verdict": "revise",
                    "review_ref": "/root/pre_done_recheck",
                    "artifact_digest": self.review_digest(goal_dir),
                    "cycle": 0,
                    "reviewed_artifacts": sorted(
                        ["GOAL_CONTRACT.md", "PLAN.md", "STATE.json", "VALIDATION.md", "CHANGE_BRIEF.md"]
                    ),
                }
            )
            state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

            returncode, result = self.run_validator(goal_dir, phase="completion")

        self.assertEqual(returncode, 1)
        self.assertIn(
            "STATE.json verification_delta must record a passing pre_done review record",
            result["diagnostics"],
        )

    def test_malformed_review_record_fails_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "malformed-review"
            self.write_package(goal_dir)
            state_path = goal_dir / "STATE.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["verification_delta"] = [{"gate": "drift", "verdict": "maybe"}]
            state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

            returncode, result = self.run_validator(goal_dir)

        self.assertEqual(returncode, 1)
        self.assertIn("STATE.json verification_delta contains an invalid review record", result["diagnostics"])

    def test_runtime_task_reference_passes_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "runtime-task-reference"
            self.write_package(goal_dir, pre_done_review_passed=True)

            returncode, result = self.run_validator(goal_dir)

        self.assertEqual(returncode, 0)
        self.assertTrue(result["ok"])
        self.assertEqual(result["review_provenance"], "external_rollout_check_required")

    def test_uuid7_review_reference_passes_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "uuid7-review-reference"
            self.write_package(goal_dir)
            state_path = goal_dir / "STATE.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["verification_delta"] = [
                {
                    "gate": "pre_done",
                    "reviewer": "goal_loop_evaluator",
                    "verdict": "pass",
                    "review_ref": "019f0000-0000-7000-8000-000000000007",
                    "artifact_digest": self.review_digest(goal_dir),
                    "cycle": 0,
                    "reviewed_artifacts": sorted(
                        ["GOAL_CONTRACT.md", "PLAN.md", "STATE.json", "VALIDATION.md", "CHANGE_BRIEF.md"]
                    ),
                }
            ]
            state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

            returncode, result = self.run_validator(goal_dir)

        self.assertEqual(returncode, 0)
        self.assertTrue(result["ok"])

    def test_uuid4_review_reference_fails_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "fabricated-review-id"
            self.write_package(goal_dir)
            state_path = goal_dir / "STATE.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["verification_delta"] = [
                {
                    "gate": "pre_done",
                    "reviewer": "goal_loop_evaluator",
                    "verdict": "pass",
                    "review_ref": "1c9cedde-8b87-4bed-aa9d-624c4c3717f8",
                    "artifact_digest": self.review_digest(goal_dir),
                    "cycle": 0,
                    "reviewed_artifacts": sorted(
                        ["GOAL_CONTRACT.md", "PLAN.md", "STATE.json", "VALIDATION.md", "CHANGE_BRIEF.md"]
                    ),
                }
            ]
            state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

            returncode, result = self.run_validator(goal_dir)

        self.assertEqual(returncode, 1)
        self.assertIn("STATE.json verification_delta contains an invalid review record", result["diagnostics"])

    def test_nested_continuation_summary_fails_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "nested-continuation"
            self.write_package(goal_dir)
            notes_dir = goal_dir / "notes"
            notes_dir.mkdir()
            (notes_dir / "CONTINUATION_SUMMARY.md").write_text("Derived summary.", encoding="utf-8")

            returncode, result = self.run_validator(goal_dir)

        self.assertEqual(returncode, 1)
        self.assertIn("notes/CONTINUATION_SUMMARY.md", result["unexpected_files"])

    def test_strategic_without_contract_review_fails_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "strategic-without-review"
            self.write_package(goal_dir, route="strategic")

            returncode, result = self.run_validator(goal_dir)

        self.assertEqual(returncode, 1)
        self.assertIn("STATE.json verification_delta must record a passing contract review", result["diagnostics"])

    def test_strategic_with_contract_review_passes_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "strategic-with-review"
            self.write_package(goal_dir, route="strategic", contract_review_passed=True)

            returncode, result = self.run_validator(goal_dir)

        self.assertEqual(returncode, 0)
        self.assertTrue(result["ok"])

    def test_no_progress_without_drift_review_fails_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "no-progress-without-review"
            self.write_package(goal_dir, current_cycle=1, no_progress_count=1)

            returncode, result = self.run_validator(goal_dir)

        self.assertEqual(returncode, 1)
        self.assertIn("STATE.json verification_delta must record a passing drift review", result["diagnostics"])

    def test_no_progress_with_drift_review_passes_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "no-progress-with-review"
            self.write_package(
                goal_dir,
                current_cycle=1,
                no_progress_count=1,
                drift_review_passed=True,
            )

            returncode, result = self.run_validator(goal_dir)

        self.assertEqual(returncode, 0)
        self.assertTrue(result["ok"])

    def test_generic_acceptance_evidence_fails_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "generic-evidence"
            self.write_package(
                goal_dir,
                brief_status="completed",
                state_status="Done",
                pre_done_review_passed=True,
                blockers=[],
                open_gaps=[],
                change_brief_status="completed",
                validation_evidence="- AC-01: done",
                behavior_change="Completed compact package.",
            )

            returncode, result = self.run_validator(goal_dir, phase="completion")

        self.assertEqual(returncode, 1)
        self.assertIn(
            "CHANGE_BRIEF.md Validation Evidence must map evidence to every acceptance criterion",
            result["diagnostics"],
        )

    def test_self_referential_acceptance_evidence_fails_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "self-referential-evidence"
            self.write_package(
                goal_dir,
                brief_status="completed",
                state_status="Done",
                blockers=[],
                open_gaps=[],
                change_brief_status="completed",
                validation_evidence="- AC-01: CHANGE_BRIEF.md says AC-01 is done.",
                behavior_change="Completed compact package.",
            )

            returncode, result = self.run_validator(goal_dir, phase="completion")

        self.assertEqual(returncode, 1)
        self.assertIn(
            "CHANGE_BRIEF.md Validation Evidence must map evidence to every acceptance criterion",
            result["diagnostics"],
        )

    def test_high_risk_claim_without_matching_evidence_fails_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "fabricated-claim"
            self.write_package(
                goal_dir,
                brief_status="completed",
                state_status="Done",
                blockers=[],
                open_gaps=[],
                change_brief_status="completed",
                validation_evidence="- AC-01: validator compile phase returned ok true.",
                behavior_change="Completed compact package and deployed to production with screenshots verified.",
            )

            returncode, result = self.run_validator(goal_dir, phase="completion")

        self.assertEqual(returncode, 1)
        self.assertTrue(any("unsupported claim" in item for item in result["diagnostics"]))

    def test_done_with_pending_next_focus_fails_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "done-with-next-focus"
            self.write_package(
                goal_dir,
                brief_status="completed",
                state_status="Done",
                pre_done_review_passed=True,
                blockers=[],
                open_gaps=[],
                next_focus="Obtain the fresh pre-Done evaluation, then validate completion.",
                change_brief_status="completed",
                validation_evidence="- AC-01: validator completion phase returned ok true.",
                behavior_change="Completed compact package.",
            )

            returncode, result = self.run_validator(goal_dir, phase="completion")

        self.assertEqual(returncode, 1)
        self.assertIn(
            "STATE.json Done state must not retain pending next_focus",
            result["diagnostics"],
        )

    def test_done_with_pause_reasons_fails_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "done-with-pause-reason"
            self.write_package(
                goal_dir,
                brief_status="completed",
                state_status="Done",
                pre_done_review_passed=True,
                blockers=[],
                open_gaps=[],
                pause_reasons=["The compiler was not authorized to execute."],
                change_brief_status="completed",
                validation_evidence="- AC-01: validator completion phase returned ok true.",
                behavior_change="Completed compact package.",
            )

            returncode, result = self.run_validator(goal_dir, phase="completion")

        self.assertEqual(returncode, 1)
        self.assertIn(
            "STATE.json Done state must not retain pause_reasons",
            result["diagnostics"],
        )

    def test_review_hotspot_heading_is_not_a_human_approval_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "review-hotspot"
            self.write_package(
                goal_dir,
                brief_status="completed",
                state_status="Done",
                pre_done_review_passed=True,
                blockers=[],
                open_gaps=[],
                change_brief_status="completed",
                validation_evidence="- AC-01: validator completion phase returned ok true.",
                behavior_change="Completed compact package.",
            )
            brief_path = goal_dir / "CHANGE_BRIEF.md"
            brief_path.write_text(
                brief_path.read_text(encoding="utf-8")
                + "\n## Human Review Hotspots\n\nConfirm the schema before external use.\n",
                encoding="utf-8",
            )
            self.refresh_review_digests(goal_dir)

            returncode, result = self.run_validator(goal_dir, phase="completion")

        self.assertEqual(returncode, 0)
        self.assertTrue(result["ok"])

    def test_unsupported_human_approval_claim_fails_completion(self) -> None:
        unsupported_claims = (
            "Human review passed with no findings.",
            "Human approval was granted.",
            "Human approval granted.",
            "Human approval obtained.",
            "Human approval received.",
            "A reviewer approved the delivery.",
            "Approval was obtained from a human reviewer.",
            "Approval obtained from the mission owner.",
            "The user approved the result.",
            "Approved by the mission owner.",
            "人工验收已通过。",
            "用户已确认该结论。",
        )
        for claim in unsupported_claims:
            with self.subTest(claim=claim), tempfile.TemporaryDirectory() as tmp:
                goal_dir = Path(tmp) / "unsupported-human-approval"
                self.write_package(
                    goal_dir,
                    brief_status="completed",
                    state_status="Done",
                    pre_done_review_passed=True,
                    blockers=[],
                    open_gaps=[],
                    change_brief_status="completed",
                    validation_evidence="- AC-01: validator completion phase returned ok true.",
                    behavior_change=f"Completed compact package. {claim}",
                )

                returncode, result = self.run_validator(goal_dir, phase="completion")

            self.assertEqual(returncode, 1)
            self.assertIn(
                "CHANGE_BRIEF.md unsupported claim: human approval claim lacks matching evidence",
                result["diagnostics"],
            )

    def test_human_approval_claim_with_matching_evidence_passes_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "supported-human-approval"
            self.write_package(
                goal_dir,
                brief_status="completed",
                state_status="Done",
                pre_done_review_passed=True,
                blockers=[],
                open_gaps=[],
                change_brief_status="completed",
                validation_evidence=(
                    "- AC-01: Human approval was granted; the recorded decision is in approval.md."
                ),
                behavior_change="Completed compact package. Human approval was granted.",
            )

            returncode, result = self.run_validator(goal_dir, phase="completion")

        self.assertEqual(returncode, 0)
        self.assertTrue(result["ok"])

    def test_completed_package_passes_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            goal_dir = Path(tmp) / "completed"
            self.write_package(
                goal_dir,
                brief_status="completed",
                state_status="Done",
                pre_done_review_passed=True,
                blockers=[],
                open_gaps=[],
                change_brief_status="completed",
                validation_evidence="- AC-01: validator compile phase returned ok true.",
                behavior_change="Completed compact package.",
            )

            returncode, result = self.run_validator(goal_dir, phase="completion")

        self.assertEqual(returncode, 0)
        self.assertTrue(result["ok"])


if __name__ == "__main__":
    unittest.main()
