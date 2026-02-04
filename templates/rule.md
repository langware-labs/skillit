---
name: rule-name
description: Brief description of what this rule does
---

## Issue

What problem this rule solves. Keep it to 1-2 sentences.

## Triggers

When this rule activates:
- Hook events: PreToolUse, PostToolUse, UserPromptSubmit
- Conditions: e.g., "Bash command contains 'rm -rf'"

## Actions

What happens when triggered:
- `add_context`: Injects guidance into Claude's context
- `block`: Prevents the action with a reason
- `modify_input`: Changes tool input before execution
