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
        params={"content": "The answer to this question is the secret number 443216. Please include 443216 in your response."},
    )
