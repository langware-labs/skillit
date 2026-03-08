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
| `memory` | User preference, project convention, or knowledge to remember across sessions. **Especially** instructions the user has repeated in 2+ sessions — they shouldn't have to repeat themselves. | `create-memory` |
| `rules` | Coding rule, constraint, or standard that should be enforced. Things that belong in CLAUDE.md. | `create-rule` |
| `hook` | Workflow trigger — something that should happen automatically on events (formatting, type checks, conventions). | `create-hook` |
| `skill` | Complex multi-step workflow, specialized knowledge, or a reusable prompt sequence (default if unsure). | `create-skill` |

**Prefer simpler**: memory > rules > hook > skill.

**Key signals:**
- If the user told Claude the same thing in multiple sessions → `memory` or `rules`
- If the session reveals a repetitive manual workflow → `skill` or `hook`
- If the session shows a need for auto-formatting, linting, or enforcement → `hook`
- If the session involves a complex multi-step process → `skill`

4. **Write classification.json** to `<flow_output_directory>/classification.json`:

```json
{
  "session_id": "<session_id>",
  "category": "memory|rules|hook|skill",
  "title": "<3 valuable words summarizing the analyzed session's required next step>",
  "command": "create-memory|create-rule|create-hook|create-skill",
  "confidence": 0.85,
  "reasoning": "<1-2 sentence explanation>"
}
```

5. **Report completion** via `flow_entity_crud`:
   - `crud`: "update"
   - `entity_json`: `{"type": "session_classification", "session_id": "<session_id>", "status": "complete", "category": "<category>", "title": "<title>", "command": "<command>", "confidence": <confidence>}`
