# test_rule

Test rule for unit testing trigger execution across all Claude hook types.

## Rule Definition

- **IF**: prompt or command contains 'test_keyword'
- **THEN**: add context with test information, or block if dangerous
- **Hook Events**: UserPromptSubmit, PreToolUse, PostToolUse, SessionStart, Stop, Notification, SubagentStop, PreCompact, PermissionRequest
- **Actions**: add_context, block
- **Source**: unit_test
- **Created**: 2024-01-01
