"""Jira context trigger for testing acli skill detection.

Triggers when the user prompt mentions jira, tickets, issues, or acli
and injects the acli command syntax context.
"""

from memory.rule_engine.trigger_executor import Action


def evaluate(hooks_data: dict, transcript: list) -> Action | None:
    prompt = hooks_data.get("prompt", "").lower()

    # Trigger on jira-related keywords
    jira_keywords = ["jira", "ticket", "issue", "acli", "workitem"]
    if not any(keyword in prompt for keyword in jira_keywords):
        return None

    # Inject acli context from the SKILL.md content
    context = """# acli Jira Subcommand Syntax

The `acli` CLI tool uses a modern subcommand-based syntax for Jira operations. Do NOT use the deprecated `--action` flag pattern.

## Instructions

1. When running any `acli` command for Jira, always use the subcommand pattern: `acli jira <resource> <action> [flags]`.
2. To search for Jira issues, use `acli jira workitem search` with the `--jql` flag for the query and `--fields` flag for output columns.
3. Never use `--action` as a flag with `acli`. The action is always a positional subcommand.

## Syntax Reference

The general pattern for acli Jira commands is:

```
acli jira <resource> <action> [--flag value ...]
```

### Searching for Issues

```bash
acli jira workitem search --jql "<JQL query>" --fields "<comma-separated fields>"
```

**Common flags for `acli jira workitem search`:**
- `--jql` - JQL query string
- `--fields` - Comma-separated list of fields to display (e.g., "key,summary,priority,status")

### Example: List unresolved tickets assigned to current user

```bash
acli jira workitem search --jql "assignee = currentUser() AND resolution = Unresolved ORDER BY priority DESC" --fields "key,summary,priority,status"
```
"""

    return Action(
        type="add_context",
        params={"content": context},
    )
