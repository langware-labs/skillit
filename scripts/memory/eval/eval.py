"""Skill evaluation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from ..types.hooks import Memory
from ..types.records import HookResponse, Skill
from .replay import TranscriptReplay


@dataclass
class SkillEvalResult:
    passed: bool
    expected: Any
    actual: HookResponse


@dataclass
class SkillEval:
    skill: Skill
    transcript: Any
    expected_response: Any

    def run(self, start_index: int = 0, limit: int | None = None) -> SkillEvalResult:
        replay = TranscriptReplay(self.transcript, start_index=start_index, limit=limit)
        memory = Memory(skills=[self.skill])
        actual = memory.process_hooks(replay)
        passed = _matches_expected(actual, self.expected_response)
        return SkillEvalResult(passed=passed, expected=self.expected_response, actual=actual)


def _matches_expected(actual: HookResponse, expected: Any) -> bool:
    if isinstance(expected, HookResponse):
        return actual.to_dict() == expected.to_dict()
    if isinstance(expected, dict):
        actual_dict = actual.to_dict()
        for key, value in expected.items():
            if actual_dict.get(key) != value:
                return False
        return True
    if callable(expected):
        return bool(expected(actual))
    return actual == expected
