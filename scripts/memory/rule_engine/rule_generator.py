"""Generate rules programmatically from hook data and transcripts."""

import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .activation_rule import ActivationRule, ActivationRuleHeader


@dataclass
class GeneratedRule:
    """Metadata for a programmatically generated rule."""
    name: str
    keywords: list[str]
    if_condition: str
    then_action: str
    hook_events: list[str] = field(default_factory=lambda: ["UserPromptSubmit"])
    actions: list[str] = field(default_factory=lambda: ["add_context"])
    context_content: str = ""


# Keyword -> context mapping (extensible)
KEYWORD_CONTEXT_MAP = {
    "jira": "Use acli to work with jira tickets. The acli command provides access to Jira operations.",
    "ticket": "Use acli to work with jira tickets. The acli command provides access to Jira operations.",
}


def _extract_keywords(text: str) -> list[str]:
    """Extract significant keywords from text."""
    keywords = []
    text_lower = text.lower()
    for keyword in KEYWORD_CONTEXT_MAP:
        if keyword in text_lower:
            keywords.append(keyword)
    return keywords


def _get_context_for_keywords(keywords: list[str]) -> str:
    """Get context content for matched keywords."""
    for keyword in keywords:
        if keyword in KEYWORD_CONTEXT_MAP:
            return KEYWORD_CONTEXT_MAP[keyword]
    return f"Context for: {', '.join(keywords)}"


def _generate_trigger_code(keywords: list[str], context: str) -> str:
    """Generate trigger.py source code."""
    keywords_repr = repr(keywords)
    return f'''"""Auto-generated trigger for keyword matching."""

from memory.rule_engine.trigger_executor import Action


def evaluate(hooks_data: dict, transcript: list) -> Action | list[Action] | None:
    """Trigger when prompt contains any of the keywords."""
    prompt = str(hooks_data.get("prompt") or hooks_data.get("command") or "").lower()

    keywords = {keywords_repr}

    for keyword in keywords:
        if keyword in prompt:
            return Action(
                type="add_context",
                params={{"content": {repr(context)}}}
            )

    return None
'''


def gen_rule(
    hooks_data: dict[str, Any],
    transcript: Any,  # ClaudeTranscript or list[dict]
    name: str,
) -> ActivationRule:
    """Generate an ActivationRule from hook data and transcript.

    Extracts keywords from the prompt and creates a rule that triggers
    on similar prompts, adding relevant context.

    Args:
        hooks_data: Current hook event data with 'prompt' field.
        transcript: Transcript data (used for future AI-assisted generation).
        name: Name for the generated rule.

    Returns:
        ActivationRule ready to be loaded into a RuleEngine.
    """
    prompt = str(hooks_data.get("prompt") or "")
    keywords = _extract_keywords(prompt)

    if not keywords:
        keywords = [word.lower() for word in prompt.split() if len(word) > 3][:3]

    context = _get_context_for_keywords(keywords)
    trigger_code = _generate_trigger_code(keywords, context)

    # Create temporary rule directory
    rule_dir = Path(tempfile.mkdtemp(prefix=f"rule_{name}_")) / name
    rule_dir.mkdir(parents=True, exist_ok=True)

    # Write trigger.py
    (rule_dir / "trigger.py").write_text(trigger_code, encoding="utf-8")

    # Create header
    header = ActivationRuleHeader(
        name=name,
        if_condition=f"prompt contains: {', '.join(keywords)}",
        then_action=f"add context about {keywords[0] if keywords else 'topic'}",
        hook_events=["UserPromptSubmit"],
        actions=["add_context"],
        source="generated",
    )

    # Write rule.md
    rule = ActivationRule(path=rule_dir, header=header)
    (rule_dir / "rule.md").write_text(rule.to_md(), encoding="utf-8")

    return rule
