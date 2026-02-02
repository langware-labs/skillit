"""Tests for user prompt rule skill evaluations."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "scripts"
TESTS_DIR = SCRIPTS_DIR / "tests"
TEST_SKILLS_DIR = TESTS_DIR / "test_skills"

sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(TESTS_DIR))

from memory.eval import SkillEval  # noqa: E402


def _load_expected(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _iter_eval_cases(skill_dir: Path):
    eval_dir = skill_dir / "eval"
    if not eval_dir.exists():
        return []
    return [p for p in eval_dir.iterdir() if p.is_dir()]


def run_eval(skill_folder_name: str) -> None:
    skill_dir = TEST_SKILLS_DIR / skill_folder_name
    cases = _iter_eval_cases(skill_dir)
    assert cases, f"No eval cases found for {skill_folder_name}"

    module_path = f"test_skills.{skill_folder_name}.skill"
    module = importlib.import_module(module_path)
    build_skill = getattr(module, "build_skill", None)
    assert callable(build_skill), f"Missing build_skill() in {module_path}"

    skill = build_skill()

    for case_dir in cases:
        transcript_path = case_dir / "transcript.jsonl"
        expected_path = case_dir / "expected.json"
        assert transcript_path.exists(), f"Missing transcript.jsonl in {case_dir}"
        assert expected_path.exists(), f"Missing expected.json in {case_dir}"

        expected = _load_expected(expected_path)
        evaluator = SkillEval(skill=skill, transcript=transcript_path, expected_response=expected)
        result = evaluator.run()

        assert result.passed, (
            f"Skill eval failed for {case_dir.name}. "
            f"Expected: {expected} Actual: {result.actual.to_dict()}"
        )


def test_eval_skill():
    run_eval("jira_acli")
