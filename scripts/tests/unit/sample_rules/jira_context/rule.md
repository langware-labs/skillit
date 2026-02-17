---
name: jira_context
description: Injects acli Jira subcommand syntax when user asks about Jira tickets
---

## Triggers

- Hook events: UserPromptSubmit
- Condition: prompt contains jira-related keywords (jira, ticket, issue, acli, workitem)

## Actions

- `add_context`: Injects the acli command syntax reference and examples
