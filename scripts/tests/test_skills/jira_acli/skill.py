"""Skill definition for jira acli reminder."""

from __future__ import annotations

from scripts.memory.records import Rule, Skill


def _extract_prompt(text: str) -> str:
    return text or ""


def _match_jira_or_ticket(event) -> bool:
    if event is None:
        return False
    prompt = ""
    if getattr(event, "command", None):
        prompt = str(event.command)
    elif isinstance(getattr(event, "raw", None), dict):
        raw = event.raw
        data = raw.get("data", {}) if isinstance(raw, dict) else {}
        prompt = str(data.get("command") or data.get("prompt") or "")
    prompt = _extract_prompt(prompt).lower()
    return "jira" in prompt or "ticket" in prompt


def _add_acli_context(event) -> str:
    return "use acli to work with jira"


def build_skill() -> Skill:
    rule = Rule(
        name="user_prompt_jira_or_ticket",
        description="Adds jira acli context when prompt mentions jira/ticket.",
        matcher=_match_jira_or_ticket,
        action=_add_acli_context,
    )
    return Skill(name="jira_acli", rules=[rule])
