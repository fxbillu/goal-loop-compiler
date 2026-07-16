#!/usr/bin/env python3
"""Validate Goal Loop Compiler compact-v4 execution packages."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List
from uuid import UUID


REQUIRED_FILES = {
    "GOAL_CONTRACT.md",
    "PLAN.md",
    "STATE.json",
    "VALIDATION.md",
    "CHANGE_BRIEF.md",
}

FORBIDDEN_DEFAULT_FILES = {
    "GOAL.md",
    "STATE.md",
    "Goal Prompt.md",
    "Loop Prompt.md",
    "Launch Prompt.md",
    "FINAL_EVALUATOR.md",
    "Final Report.md",
    "CONTINUATION_SUMMARY.md",
}

GOAL_CONTRACT_SECTIONS = (
    "Lifecycle Classification",
    "Goal",
    "Intent",
    "Strategic Outcome",
    "Decision Standard",
    "Evidence Standard",
    "Scope",
    "Non-goals",
    "Constraints",
    "Pause Conditions",
    "Acceptance Criteria",
)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def section_pattern(section: str) -> re.Pattern[str]:
    return re.compile(rf"(?im)^\s{{0,3}}#{{1,6}}\s+{re.escape(section)}\s*$")


def has_section(text: str, section: str) -> bool:
    return bool(section_pattern(section).search(text))


def section_body(text: str, section: str) -> str:
    match = section_pattern(section).search(text)
    if not match:
        return ""
    rest = text[match.end() :]
    next_heading = re.search(r"(?m)^\s{0,3}#{1,6}\s+\S", rest)
    return rest[: next_heading.start()] if next_heading else rest


def section_tree_body(text: str, section: str) -> str:
    pattern = re.compile(
        rf"(?im)^\s{{0,3}}(?P<hashes>#{{1,6}})\s+{re.escape(section)}\s*$"
    )
    match = pattern.search(text)
    if not match:
        return ""
    rest = text[match.end() :]
    level = len(match.group("hashes"))
    next_peer = re.search(rf"(?m)^\s{{0,3}}#{{1,{level}}}\s+\S", rest)
    return rest[: next_peer.start()] if next_peer else rest


def status_from_change_brief(text: str) -> str:
    match = re.search(r"(?im)^\s*-?\s*status\s*:\s*([A-Za-z_-]+)\s*$", text)
    return match.group(1).lower() if match else ""


def route_from_contract(text: str) -> str:
    match = re.search(r"(?im)^\s*(?:-\s*)?route\s*:\s*([A-Za-z_|-]+)\s*$", text)
    return match.group(1).lower() if match else ""


def non_placeholder_lines(text: str) -> List[str]:
    lines: List[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line in {"-", "|---|---|---|---|"}:
            continue
        if "{{" in line or "}}" in line:
            continue
        if re.fullmatch(r"pending final validation\.?", line, re.IGNORECASE):
            continue
        lines.append(line)
    return lines


def intent_is_restatement(contract_text: str) -> bool:
    intent = section_body(contract_text, "Intent")
    surface_match = re.search(r"(?im)surface request\s*:\s*(.+)$", intent)
    real_match = re.search(r"(?im)real intent\s*:\s*(.+)$", intent)
    if not surface_match or not real_match:
        return False
    surface = surface_match.group(1).strip(" .")
    real = real_match.group(1).strip(" .")
    if not surface or not real or "{{" in surface or "{{" in real:
        return False
    return surface.lower() == real.lower()


def intent_fields_present(contract_text: str) -> bool:
    intent = section_body(contract_text, "Intent")
    surface_match = re.search(r"(?im)surface request\s*:\s*(.+)$", intent)
    real_match = re.search(r"(?im)real intent\s*:\s*(.+)$", intent)
    return bool(
        surface_match
        and real_match
        and surface_match.group(1).strip(" .")
        and real_match.group(1).strip(" .")
    )


def load_state(path: Path, diagnostics: List[str]) -> Dict[str, Any]:
    try:
        state = json.loads(read_text(path))
    except Exception as exc:  # noqa: BLE001 - report validation detail
        diagnostics.append(f"invalid STATE.json: {exc}")
        return {}
    if not isinstance(state, dict):
        diagnostics.append("STATE.json must be an object")
        return {}
    return state


def unexpected_files(goal_dir: Path) -> List[str]:
    files = {path.relative_to(goal_dir).as_posix() for path in goal_dir.rglob("*") if path.is_file()}
    return sorted(files - REQUIRED_FILES)


def final_evaluator_is_structured(validation_text: str) -> bool:
    evaluator = section_tree_body(validation_text, "Final Evaluator")
    if not evaluator:
        return False
    if not re.search(r"(?m)^\s*change_brief_truthfulness:\s*$", evaluator):
        return False
    nested = (
        "unsupported_claims",
        "missing_human_context",
        "validation_evidence_mapping",
        "manual_verification_reality",
        "rollback_reality",
    )
    if not all(re.search(rf"(?m)^\s{{2,}}{field}:\s*$", evaluator) for field in nested):
        return False
    top_level = ("state_consistency", "requires_human")
    return all(re.search(rf"(?m)^\s*{field}:\s*$", evaluator) for field in top_level)


def acceptance_ids(contract_text: str) -> List[str]:
    body = section_body(contract_text, "Acceptance Criteria")
    return sorted(set(re.findall(r"\bAC-\d+\b", body)))


def source_map_is_canonical(state: Dict[str, Any]) -> bool:
    return state.get("source_of_truth") == {
        "semantic_contract": "GOAL_CONTRACT.md",
        "execution_plan": "PLAN.md",
        "runtime_state": "STATE.json",
        "validation_gate": "VALIDATION.md",
        "human_delivery": "CHANGE_BRIEF.md",
    }


def is_non_negative_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def is_positive_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def validate_loop_controls(state: Dict[str, Any], diagnostics: List[str]) -> None:
    status = state.get("current_status")
    if status not in {"Continue", "Done", "Pause"}:
        diagnostics.append("STATE.json current_status must be Continue, Done, or Pause")

    current_cycle = state.get("current_cycle")
    if not is_non_negative_integer(current_cycle):
        diagnostics.append("STATE.json current_cycle must be a non-negative integer")

    no_progress_count = state.get("no_progress_count")
    if not is_non_negative_integer(no_progress_count):
        diagnostics.append("STATE.json no_progress_count must be a non-negative integer")

    loop_budget = state.get("loop_budget")
    if not isinstance(loop_budget, dict):
        diagnostics.append("STATE.json loop_budget must be an object")
        return

    max_cycles = loop_budget.get("max_cycles")
    if not is_positive_integer(max_cycles):
        diagnostics.append("STATE.json loop_budget.max_cycles must be a positive integer")

    no_progress_threshold = loop_budget.get("no_progress_threshold")
    if not is_positive_integer(no_progress_threshold):
        diagnostics.append("STATE.json loop_budget.no_progress_threshold must be a positive integer")

    if is_non_negative_integer(current_cycle) and is_positive_integer(max_cycles) and current_cycle > max_cycles:
        diagnostics.append("STATE.json current_cycle must not exceed loop_budget.max_cycles")
    if (
        is_non_negative_integer(no_progress_count)
        and is_positive_integer(no_progress_threshold)
        and no_progress_count > no_progress_threshold
    ):
        diagnostics.append("STATE.json no_progress_count must not exceed loop_budget.no_progress_threshold")

    if status != "Continue":
        return
    if is_non_negative_integer(current_cycle) and is_positive_integer(max_cycles) and current_cycle >= max_cycles:
        diagnostics.append("STATE.json must Pause when max_cycles is reached")
    if (
        is_non_negative_integer(no_progress_count)
        and is_positive_integer(no_progress_threshold)
        and no_progress_count >= no_progress_threshold
    ):
        diagnostics.append("STATE.json must Pause when no_progress_threshold is reached")


def valid_review_ref(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    if re.fullmatch(r"/root(?:/[A-Za-z0-9][A-Za-z0-9_-]*)+", value):
        return True
    try:
        parsed = UUID(value)
        return parsed.version == 7 and str(parsed) == value.lower()
    except ValueError:
        return False


def valid_artifact_digest(value: Any) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"sha256:[0-9a-f]{64}", value))


def package_review_digest(goal_dir: Path) -> str:
    digest = hashlib.sha256()
    for filename in sorted(REQUIRED_FILES):
        path = goal_dir / filename
        if filename == "STATE.json":
            state = json.loads(read_text(path))
            if not isinstance(state, dict):
                raise ValueError("STATE.json must be an object")
            state = dict(state)
            state["verification_delta"] = []
            content = json.dumps(
                state,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        else:
            content = read_text(path)
        digest.update(filename.encode("utf-8"))
        digest.update(b"\0")
        digest.update(content.encode("utf-8"))
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def valid_review_record(review: Any) -> bool:
    if not isinstance(review, dict):
        return False
    reviewed_artifacts = review.get("reviewed_artifacts")
    return (
        review.get("gate") in {"contract", "drift", "pre_done"}
        and review.get("reviewer") == "goal_loop_evaluator"
        and review.get("verdict") in {"pass", "revise", "blocked"}
        and valid_review_ref(review.get("review_ref"))
        and valid_artifact_digest(review.get("artifact_digest"))
        and is_non_negative_integer(review.get("cycle"))
        and isinstance(reviewed_artifacts, list)
        and all(isinstance(item, str) for item in reviewed_artifacts)
        and set(reviewed_artifacts) == REQUIRED_FILES
    )


def validate_review_records(state: Dict[str, Any], diagnostics: List[str]) -> None:
    reviews = state.get("verification_delta")
    if not isinstance(reviews, list):
        diagnostics.append("STATE.json verification_delta must be a list")
        return
    if any(not valid_review_record(review) for review in reviews):
        diagnostics.append("STATE.json verification_delta contains an invalid review record")


def effective_review_verdict(state: Dict[str, Any], gate: str, cycle: int) -> str:
    reviews = state.get("verification_delta")
    if not isinstance(reviews, list):
        return ""
    verdict = ""
    for review in reviews:
        if valid_review_record(review) and review.get("gate") == gate and review.get("cycle") == cycle:
            verdict = str(review["verdict"])
    return verdict


def effective_review_record(state: Dict[str, Any], gate: str, cycle: int) -> Dict[str, Any]:
    reviews = state.get("verification_delta")
    if not isinstance(reviews, list):
        return {}
    effective: Dict[str, Any] = {}
    for review in reviews:
        if valid_review_record(review) and review.get("gate") == gate and review.get("cycle") == cycle:
            effective = review
    return effective


def has_passing_review(state: Dict[str, Any], gate: str, cycle: int) -> bool:
    return effective_review_verdict(state, gate, cycle) == "pass"


def contains_placeholder(text: str) -> bool:
    return bool(re.search(r"\{\{[^{}]+\}\}", text))


def validate_structure(goal_dir: Path) -> Dict[str, Any]:
    diagnostics: List[str] = []
    warnings: List[str] = []
    missing = sorted(name for name in REQUIRED_FILES if not (goal_dir / name).is_file())
    extras = unexpected_files(goal_dir) if goal_dir.is_dir() else []

    if not goal_dir.exists():
        diagnostics.append("goal directory does not exist")
    elif not goal_dir.is_dir():
        diagnostics.append("goal path is not a directory")

    if missing:
        diagnostics.append("missing required compact-v4 file(s)")
    if extras:
        forbidden = sorted(name for name in extras if Path(name).name in FORBIDDEN_DEFAULT_FILES)
        if forbidden:
            diagnostics.append("forbidden compact-v4 artifact(s): " + ", ".join(forbidden))
        else:
            diagnostics.append("unexpected package file(s)")

    contract_text = read_text(goal_dir / "GOAL_CONTRACT.md") if not missing or (goal_dir / "GOAL_CONTRACT.md").is_file() else ""
    plan_text = read_text(goal_dir / "PLAN.md") if (goal_dir / "PLAN.md").is_file() else ""
    validation_text = read_text(goal_dir / "VALIDATION.md") if (goal_dir / "VALIDATION.md").is_file() else ""
    brief_text = read_text(goal_dir / "CHANGE_BRIEF.md") if (goal_dir / "CHANGE_BRIEF.md").is_file() else ""
    file_texts = {
        "GOAL_CONTRACT.md": contract_text,
        "PLAN.md": plan_text,
        "VALIDATION.md": validation_text,
        "CHANGE_BRIEF.md": brief_text,
    }
    if (goal_dir / "STATE.json").is_file():
        file_texts["STATE.json"] = read_text(goal_dir / "STATE.json")
    for filename, text in file_texts.items():
        if contains_placeholder(text):
            diagnostics.append(f"{filename} contains unresolved template placeholder")

    missing_sections = [section for section in GOAL_CONTRACT_SECTIONS if not has_section(contract_text, section)]
    if missing_sections:
        diagnostics.append("missing GOAL_CONTRACT.md section(s)")
    if contract_text and not acceptance_ids(contract_text):
        diagnostics.append("GOAL_CONTRACT.md Acceptance Criteria must include AC ids")
    if contract_text and not intent_fields_present(contract_text):
        diagnostics.append("GOAL_CONTRACT.md Intent must contain Surface request and Real intent")
    elif contract_text and intent_is_restatement(contract_text):
        warnings.append("Intent matches the surface request; confirm that no deeper intent needs recording")
    route = route_from_contract(contract_text)
    if contract_text and not route:
        diagnostics.append("GOAL_CONTRACT.md route is required")
    if route in {"one_shot", "recurring_system"}:
        diagnostics.append(f"{route} must not be compiled as finite goal package")
    if route and route not in {"finite_goal", "strategic", "repair", "governed", "one_shot", "recurring_system"}:
        diagnostics.append("GOAL_CONTRACT.md route is not recognized")

    if re.search(r"(?im)^\s{0,3}#{1,6}\s+Intent\s*$", plan_text):
        diagnostics.append("PLAN.md must not redefine Intent")
    if re.search(r"(?im)real intent\s*:", plan_text):
        diagnostics.append("PLAN.md contains Real intent field and may conflict with GOAL_CONTRACT.md")
    forbidden_plan_sections = (
        "Goal",
        "Strategic Outcome",
        "Decision Standard",
        "Evidence Standard",
        "Scope",
        "Non-goals",
        "Constraints",
        "Acceptance Criteria",
        "Completion Standard",
        "Human-readable Completion Standard",
    )
    plan_conflicts = [section for section in forbidden_plan_sections if has_section(plan_text, section)]
    if plan_conflicts:
        diagnostics.append("PLAN.md must not redefine semantic section(s): " + ", ".join(plan_conflicts))

    if "Evidence Standard" not in validation_text or "Required Evidence" not in validation_text:
        diagnostics.append("VALIDATION.md does not carry Evidence Standard / Required Evidence checks")
    if not final_evaluator_is_structured(validation_text):
        diagnostics.append("VALIDATION.md final evaluator does not check Change Brief truthfulness")

    state_path = goal_dir / "STATE.json"
    state_exists = state_path.is_file()
    state = load_state(state_path, diagnostics) if state_exists else {}
    for key in (
        "schema_version",
        "lifecycle_route",
        "current_status",
        "current_cycle",
        "no_progress_count",
        "loop_budget",
        "open_gaps",
        "closed_evidence",
        "completion_candidates",
        "verification_delta",
        "change_brief_status",
        "next_focus",
        "pause_reasons",
        "blockers",
        "source_of_truth",
    ):
        if state_exists and key not in state:
            diagnostics.append(f"STATE.json missing {key}")
    if state_exists and state.get("schema_version") != "compact-v4":
        diagnostics.append("STATE.json schema_version must be compact-v4")
    if state_exists and state.get("lifecycle_route") in {"one_shot", "recurring_system"}:
        diagnostics.append("STATE.json lifecycle_route must be a finite package route")
    if state_exists and route and state.get("lifecycle_route") != route:
        diagnostics.append("STATE.json lifecycle_route must match GOAL_CONTRACT.md route")
    if state_exists and not source_map_is_canonical(state):
        diagnostics.append("STATE.json source_of_truth must match compact-v4 canonical map")
    if state_exists:
        validate_loop_controls(state, diagnostics)
        validate_review_records(state, diagnostics)
        if route in {"strategic", "governed", "repair"} and not has_passing_review(state, "contract", 0):
            diagnostics.append("STATE.json verification_delta must record a passing contract review")
        no_progress_count = state.get("no_progress_count")
        current_cycle = state.get("current_cycle")
        if (
            is_positive_integer(no_progress_count)
            and is_non_negative_integer(current_cycle)
            and not has_passing_review(state, "drift", current_cycle)
        ):
            diagnostics.append("STATE.json verification_delta must record a passing drift review")

    return {
        "ok": not diagnostics,
        "phase": "structure",
        "review_provenance": "external_rollout_check_required",
        "missing_files": missing,
        "unexpected_files": extras,
        "missing_sections": missing_sections,
        "diagnostics": diagnostics,
        "warnings": warnings,
    }


def validate_compile(goal_dir: Path) -> Dict[str, Any]:
    result = validate_structure(goal_dir)
    diagnostics: List[str] = list(result["diagnostics"])
    brief_text = read_text(goal_dir / "CHANGE_BRIEF.md") if (goal_dir / "CHANGE_BRIEF.md").is_file() else ""

    if status_from_change_brief(brief_text) != "pending":
        diagnostics.append("CHANGE_BRIEF.md initial status must be pending")

    result.update({"ok": not diagnostics, "phase": "compile", "diagnostics": diagnostics})
    return result


def contract_sha256(goal_dir: Path) -> str:
    return "sha256:" + hashlib.sha256(
        read_text(goal_dir / "GOAL_CONTRACT.md").encode("utf-8")
    ).hexdigest()


def native_goal_projection(goal_dir: Path) -> Dict[str, Any]:
    compile_result = validate_compile(goal_dir)
    if not compile_result["ok"]:
        return {
            **compile_result,
            "phase": "native-goal",
            "native_goal": "",
            "contract_sha256": "",
            "projection_sha256": "",
            "runtime_provenance": "external_rollout_check_required",
        }

    contract_text = read_text(goal_dir / "GOAL_CONTRACT.md")
    sections = (
        "Goal",
        "Constraints",
        "Non-goals",
        "Pause Conditions",
        "Acceptance Criteria",
    )
    blocks = "\n\n".join(
        f"## {section}\n{section_body(contract_text, section).strip()}" for section in sections
    )
    goal_path = goal_dir.as_posix()
    native_goal = "\n\n".join(
        (
            f"Execute the confirmed Goal Loop package at `{goal_path}`.",
            f"Contract SHA-256: `{contract_sha256(goal_dir)}`.",
            "Read `GOAL_CONTRACT.md` before acting. It is the semantic authority; "
            "`PLAN.md` is derived strategy and `STATE.json` is runtime state.",
            blocks,
            "Do not reinterpret or change contract semantics. If Goal, constraints, "
            "non-goals, pause conditions, or acceptance criteria must change, Pause.",
            "Do not mark this native goal complete until target evidence exists, "
            "STATE.json is Done with empty open_gaps, blockers, next_focus, and "
            "pause_reasons, CHANGE_BRIEF.md is completed and truthful, and "
            "`validate_package.py --phase completion` returns ok true.",
        )
    )
    projection_sha256 = "sha256:" + hashlib.sha256(native_goal.encode("utf-8")).hexdigest()
    return {
        **compile_result,
        "phase": "native-goal",
        "contract_sha256": contract_sha256(goal_dir),
        "projection_sha256": projection_sha256,
        "native_goal": native_goal,
        "runtime_provenance": "external_rollout_check_required",
    }


def generate_review_digest(goal_dir: Path) -> Dict[str, Any]:
    missing = sorted(name for name in REQUIRED_FILES if not (goal_dir / name).is_file())
    diagnostics: List[str] = []
    artifact_digest = ""
    if missing:
        diagnostics.append("missing required compact-v4 file(s)")
    else:
        try:
            artifact_digest = package_review_digest(goal_dir)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            diagnostics.append(f"cannot compute package review digest: {exc}")
    return {
        "ok": not diagnostics,
        "phase": "review-digest",
        "artifact_digest": artifact_digest,
        "missing_files": missing,
        "diagnostics": diagnostics,
    }


def text_has_completion_claim(text: str) -> bool:
    return bool(
        re.search(
            r"\b(completed|done|passed|verified|implemented|shipped|通过|完成|已验证|已实现)\b",
            text,
            re.IGNORECASE,
        )
    )


def validation_evidence_present(brief_text: str) -> bool:
    evidence = section_body(brief_text, "Validation Evidence")
    lines = non_placeholder_lines(evidence)
    return bool(lines and not any("pending final validation" in line.lower() for line in lines))


def completed_brief_has_stale_finalization_language(brief_text: str) -> bool:
    final_sections = "\n".join(
        (
            section_body(brief_text, "Outcome"),
            section_body(brief_text, "Unresolved Gaps if not Done"),
        )
    )
    patterns = (
        r"\bawaiting\b.{0,80}\b(?:completion|validation|validator|confirmation)\b",
        r"\b(?:completion|validation|validator)\b.{0,80}\b(?:pending|outstanding|awaited)\b",
        r"\b(?:remaining|remains)\s+(?:command\s+)?gate\b",
        r"\bstill\s+(?:needs?|requires?)\b.{0,80}\b(?:completion|validation|validator)\b",
        r"\bnot\s+yet\b.{0,80}\b(?:complete|confirmed|run|validated)\b",
        r"(?:仍待|等待|尚未|还需|剩余).{0,40}(?:完成验证|验证|门禁)",
        r"(?:完成验证|验证|门禁).{0,40}(?:仍待|等待|尚未|还需|剩余)",
    )
    for sentence in re.split(r"(?<=[.!?。！？])\s+|\n+", final_sections):
        if re.search(
            r"\b(?:no|not|never)\b.{0,40}\b(?:awaiting|pending|remaining|outstanding)\b|"
            r"\bno\s+longer\b|(?:没有|不存在|不再|无需).{0,30}(?:等待|尚未|剩余|验证|门禁)",
            sentence,
            re.IGNORECASE,
        ):
            continue
        if any(re.search(pattern, sentence, re.IGNORECASE) for pattern in patterns):
            return True
    return False


def acceptance_evidence_mapping_present(contract_text: str, brief_text: str) -> bool:
    evidence = section_body(brief_text, "Validation Evidence")
    ids = acceptance_ids(contract_text)
    if not ids or not non_placeholder_lines(evidence):
        return False
    return all(any(is_concrete_evidence_line(line) for line in evidence_lines_for_ac(evidence, ac_id)) for ac_id in ids)


def evidence_lines_for_ac(evidence: str, ac_id: str) -> List[str]:
    return [line for line in non_placeholder_lines(evidence) if re.search(rf"\b{re.escape(ac_id)}\b", line)]


def is_concrete_evidence_line(line: str) -> bool:
    text = line.lower()
    if "change_brief.md" in text or "change brief" in text:
        return False
    generic_results = {
        "done",
        "completed",
        "passed",
        "ok",
        "verified",
        "完成",
        "通过",
        "已验证",
    }
    if line.lstrip().startswith("|"):
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3 or not re.fullmatch(r"AC-\d+", cells[0], re.IGNORECASE):
            return False
        reference, observed = (cell.lower().strip(" .") for cell in cells[1:3])
        if not reference or not observed or "pending" in reference or "pending" in observed:
            return False
        return reference not in generic_results and observed not in generic_results
    evidence = re.sub(r"^[-*\s]*ac-\d+\s*:\s*", "", text).strip(" .")
    if not evidence or evidence in generic_results:
        return False
    return len(evidence) >= 12


def unsupported_high_risk_claims(brief_text: str) -> List[str]:
    evidence = section_body(brief_text, "Validation Evidence").lower()
    claims_text = brief_text.replace(section_body(brief_text, "Validation Evidence"), "").lower()
    claim_groups = {
        "production/deploy claim lacks matching evidence": (
            r"\b(production|deployed|deploy|released|shipped|上线|发布)\b",
            r"\b(production|deployed|deploy|released|shipped|上线|发布)\b",
        ),
        "screenshot claim lacks matching evidence": (
            r"\b(screenshot|screen shot|image|截图)\b",
            r"\b(screenshot|screen shot|image|截图)\b",
        ),
        "external validation claim lacks matching evidence": (
            r"\b(external validation|external api|live validation|browser validation|外部验证|线上验证)\b",
            r"\b(external validation|external api|live validation|browser validation|外部验证|线上验证)\b",
        ),
        "human approval claim lacks matching evidence": (
            r"\b(?:human review (?:passed|approved|completed)|"
            r"human approval(?: was)? (?:granted|obtained|received)|"
            r"(?:a |the )?(?:human )?reviewer approved|"
            r"approval(?: was)? (?:granted|obtained|received)(?: by| from)?|"
            r"user approved|approved by)\b|"
            r"(?:人工验收(?:已)?通过|用户(?:已)?确认)",
            r"\b(?:human review (?:passed|approved|completed)|"
            r"human approval(?: was)? (?:granted|obtained|received)|"
            r"(?:a |the )?(?:human )?reviewer approved|"
            r"approval(?: was)? (?:granted|obtained|received)(?: by| from)?|"
            r"user approved|approved by)\b|"
            r"(?:人工验收(?:已)?通过|用户(?:已)?确认)",
        ),
        "test/build claim lacks matching evidence": (
            r"\b(tests? passed|pytest passed|build passed|构建通过|测试通过)\b",
            r"\b(tests? passed|pytest passed|build passed|构建通过|测试通过)\b",
        ),
    }
    unsupported: List[str] = []
    for message, (claim_pattern, evidence_pattern) in claim_groups.items():
        if re.search(claim_pattern, claims_text, re.IGNORECASE) and not re.search(evidence_pattern, evidence, re.IGNORECASE):
            unsupported.append(message)
    return unsupported


def requires_independent_pre_done(state: Dict[str, Any], route: str) -> bool:
    if route in {"strategic", "repair", "governed"}:
        return True
    if is_positive_integer(state.get("no_progress_count")):
        return True
    reviews = state.get("verification_delta")
    return isinstance(reviews, list) and any(
        valid_review_record(review) and review.get("gate") == "drift" for review in reviews
    )


def validate_completion(goal_dir: Path) -> Dict[str, Any]:
    base = validate_structure(goal_dir)
    diagnostics: List[str] = list(base["diagnostics"])

    brief_text = read_text(goal_dir / "CHANGE_BRIEF.md") if (goal_dir / "CHANGE_BRIEF.md").is_file() else ""
    contract_text = read_text(goal_dir / "GOAL_CONTRACT.md") if (goal_dir / "GOAL_CONTRACT.md").is_file() else ""
    validation_text = read_text(goal_dir / "VALIDATION.md") if (goal_dir / "VALIDATION.md").is_file() else ""
    state = load_state(goal_dir / "STATE.json", diagnostics) if (goal_dir / "STATE.json").is_file() else {}
    route = route_from_contract(contract_text)

    blockers = state.get("blockers") or []
    open_gaps = state.get("open_gaps") or []
    if state.get("current_status") != "Done":
        diagnostics.append("STATE.json current_status must be Done for completion validation")
    if state.get("change_brief_status") not in {"completed", "complete"}:
        diagnostics.append("STATE.json change_brief_status must be completed for completion validation")
    if open_gaps:
        diagnostics.append("STATE.json open_gaps must be empty for completion validation")
    if state.get("current_status") == "Done" and str(state.get("next_focus") or "").strip():
        diagnostics.append("STATE.json Done state must not retain pending next_focus")
    if state.get("current_status") == "Done" and (state.get("pause_reasons") or []):
        diagnostics.append("STATE.json Done state must not retain pause_reasons")
    if state.get("current_status") == "Done" and (blockers or any("blocker" in str(gap).lower() for gap in open_gaps)):
        diagnostics.append("STATE.json is Done with unresolved blockers")
    if requires_independent_pre_done(state, route) and not has_passing_review(
        state, "pre_done", state.get("current_cycle")
    ):
        diagnostics.append("STATE.json verification_delta must record a passing pre_done review record")
    elif has_passing_review(state, "pre_done", state.get("current_cycle")):
        review = effective_review_record(state, "pre_done", state.get("current_cycle"))
        try:
            current_digest = package_review_digest(goal_dir)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            diagnostics.append(f"cannot compute package review digest: {exc}")
        else:
            if review.get("artifact_digest") != current_digest:
                diagnostics.append("pre_done review artifact_digest does not match the final package")

    if status_from_change_brief(brief_text) not in {"completed", "complete"}:
        diagnostics.append("CHANGE_BRIEF.md status must be completed for completion validation")
    elif completed_brief_has_stale_finalization_language(brief_text):
        diagnostics.append("completed CHANGE_BRIEF.md contains stale finalization language")
    if text_has_completion_claim(brief_text) and not validation_evidence_present(brief_text):
        diagnostics.append("CHANGE_BRIEF.md contains completion claims without validation evidence")
    if not acceptance_evidence_mapping_present(contract_text, brief_text):
        diagnostics.append("CHANGE_BRIEF.md Validation Evidence must map evidence to every acceptance criterion")
    for unsupported in unsupported_high_risk_claims(brief_text):
        diagnostics.append(f"CHANGE_BRIEF.md unsupported claim: {unsupported}")
    if re.search(r"(?im)non[- ]goal.*violat|violated non[- ]goal|违反.*非目标", brief_text):
        diagnostics.append("Non-goal violation reported in CHANGE_BRIEF.md")
    if not final_evaluator_is_structured(validation_text):
        diagnostics.append("Final evaluator rubric does not check Change Brief truthfulness")

    base.update(
        {
            "ok": not diagnostics,
            "phase": "completion",
            "diagnostics": diagnostics,
        }
    )
    return base


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a compact-v4 Goal Loop package.")
    parser.add_argument("goal_dir", help="Path to the goal package directory")
    parser.add_argument(
        "--phase",
        choices=("compile", "review-digest", "completion", "native-goal"),
        default="compile",
        help="Validation phase to run",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    goal_dir = Path(args.goal_dir)
    if args.phase == "completion":
        result = validate_completion(goal_dir)
    elif args.phase == "review-digest":
        result = generate_review_digest(goal_dir)
    elif args.phase == "native-goal":
        result = native_goal_projection(goal_dir)
    else:
        result = validate_compile(goal_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
