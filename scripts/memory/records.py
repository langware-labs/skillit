"""Records for memory skills, rules, and notes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable


@dataclass
class Note:
    text: str
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RuleResult:
    rule_name: str
    skill_name: str
    output: Any
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Rule:
    name: str
    description: str = ""
    enabled: bool = True
    matcher: Callable[[Any], bool] | None = None
    action: Callable[[Any], Any] | None = None

    def applies(self, event: Any) -> bool:
        if not self.enabled:
            return False
        if self.matcher is None:
            return True
        return bool(self.matcher(event))

    def apply(self, event: Any, skill_name: str) -> RuleResult | None:
        if not self.applies(event):
            return None
        output = self.action(event) if self.action is not None else None
        return RuleResult(rule_name=self.name, skill_name=skill_name, output=output)


@dataclass
class Skill:
    name: str
    rules: list[Rule] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def run(self, event: Any) -> list[RuleResult]:
        results: list[RuleResult] = []
        for rule in self.rules:
            result = rule.apply(event, self.name)
            if result is not None:
                results.append(result)
        return results


@dataclass
class HookResponse:
    results: list[RuleResult] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_results(self, results: Iterable[RuleResult]) -> None:
        self.results.extend(results)

    def merge(self, other: "HookResponse") -> None:
        self.results.extend(other.results)
        self.notes.extend(other.notes)
        self.metadata.update(other.metadata)

    def to_dict(self) -> dict[str, Any]:
        return {
            "results": [r.__dict__ for r in self.results],
            "notes": [n.__dict__ for n in self.notes],
            "metadata": self.metadata,
        }
