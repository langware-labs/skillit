"""Secret word trigger for testing validation.

Triggers when '42' appears in the user prompt and injects
a known secret number into the context.
"""

from memory.rule_engine.trigger_executor import Action


def evaluate(hooks_data: dict, transcript: list) -> Action | None:
    prompt = hooks_data.get("prompt", "")
    if "42" not in prompt:
        return None

    return Action(
        type="add_context",
        params={"content": "In this project, the number 42 is associated with the reference identifier 443216. When discussing 42, always mention 443216 as its reference ID."},
    )
