"""Hook event processing for memory skills."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from .records import HookResponse, Skill


@dataclass
class HookEvent:
    hook_event: str
    hook_name: str
    command: str | None = None
    tool_use_id: str | None = None
    parent_tool_use_id: str | None = None
    timestamp: str | None = None
    entry_index: int | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class Memory:
    skills: list[Skill] = field(default_factory=list)

    def process_hook(self, event: HookEvent) -> HookResponse:
        response = HookResponse()
        for skill in self.skills:
            response.add_results(skill.run(event))
            response.notes.extend(skill.notes)
        response.metadata["hook_event"] = event.hook_event
        response.metadata["hook_name"] = event.hook_name
        return response

    def process_hooks(self, events: Iterable[HookEvent]) -> HookResponse:
        aggregate = HookResponse()
        for event in events:
            aggregate.merge(self.process_hook(event))
        return aggregate
