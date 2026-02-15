"""SessionStart hook handler — emit rules output only."""


def handle(data: dict, rules_output: dict) -> dict | None:
    """Handle SessionStart — emit rules output only."""
    return rules_output or None
