---
description: Analyze conversation for issues and automation opportunities. Use when you want to review a session for mistakes, misunderstandings, inefficiencies, or automation opportunities.
allowed-tools: mcp__plugin_skillit_flow_sdk__*
---

Launch ONLY ONE agent: `skillit:skillit-analyzer`. Do NOT launch any other agent.

Use the Task tool with EXACTLY these parameters:
- `subagent_type: "skillit:skillit-analyzer"`
- `run_in_background: true`
- `prompt`: Pass the user's request and conversation context.
