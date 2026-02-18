---
description: Create a skill to fix and prevent issues. Use when you need help fixing bugs, debugging code, solving problems, or preventing issues from happening again.
---

Before launching the agent, determine the skill name upfront so the UI can show progress immediately:

1. **Generate a skill name**: Based on the conversation context, generate a descriptive natural language name (capital letter for the first word, max 64 chars) that summarizes the main issue or automation opportunity. Examples: `Jira acli tickets`, `Search results validation`, `Prevent hardcoded config`.

2. **Report "creating" status**: Call the MCP `flow_entity_crud` tool with:
   - `crud`: "create"
   - `entity_json`: `{"type": "skill", "name": "<skill-name>", "description": "<brief description>", "status": "creating"}`

3. **Launch the agent**: Use the Task tool with EXACTLY these parameters:
   - `subagent_type: "skillit:skillit-creator"`
   - `run_in_background: true`
   - `prompt`: Pass the user's request and conversation context. IMPORTANT: Include the pre-generated skill name by adding: `Pre-generated skill name: "<skill-name>". Use this name for the skill unless your analysis reveals it is clearly wrong.`

Launch ONLY ONE agent: `skillit:skillit-creator`. Do NOT launch any other agent.
