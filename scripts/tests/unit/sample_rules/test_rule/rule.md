---
name: test_rule
description: Test rule for unit testing trigger execution
---

## Issue

Validates that triggers execute correctly across all Claude hook event types.

## Triggers

- Hook events: UserPromptSubmit, PreToolUse, PostToolUse, SessionStart, Stop, Notification, SubagentStop
- Condition: prompt or command contains 'test_keyword'

## Actions

- `add_context`: Injects test information into context
- `block`: Blocks dangerous commands containing 'test_keyword'
