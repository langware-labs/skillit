---
description: Classify a session to determine the best action (memory, rule, hook, or skill). Use when you want to quickly categorize what a session teaches us.
allowed-tools: mcp__plugin_skillit_flow_sdk__*
---

# Session Classification

You are a fast session classifier. Classify the session directly — do NOT launch any subagents.

## Steps

1. **Report "classifying" status**: Call the MCP `flow_entity_crud` tool with:
   - `crud`: "create"
   - `entity_json`: `{"type": "session_classification", "session_id": "<session_id>", "status": "classifying"}`

2. **Review the session**: Call `session_analysis` MCP tool with `index: -1` to get the session summary.

3. **Classify** into exactly ONE category:

| Category | When to use | Command |
|----------|-------------|---------|
| `memory` | User preference, project convention, knowledge to remember across sessions | `create-memory` |
| `rules` | Coding rule or constraint that should be enforced | `create-rule` |
| `hook` | Workflow trigger — something that should happen automatically on events | `create-hook` |
| `skill` | Complex multi-step workflow or specialized knowledge (default if unsure) | `create-skill` |

**Prefer simpler**: memory > rules > hook > skill.

4. **Write classification.json** to `<flow_output_directory>/classification.json`:

```json
{
  "session_id": "<session_id>",
  "category": "memory|rules|hook|skill",
  "title": "<3 valuable words summarizing the session>",
  "command": "create-memory|create-rule|create-hook|create-skill",
  "confidence": 0.85,
  "reasoning": "<1-2 sentence explanation>"
}
```

5. **Report completion** via `flow_entity_crud`:
   - `crud`: "update"
   - `entity_json`: `{"type": "session_classification", "session_id": "<session_id>", "status": "complete", "category": "<category>", "title": "<title>", "command": "<command>", "confidence": <confidence>}`
