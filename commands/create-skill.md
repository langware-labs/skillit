---
description: Create a skill to fix and prevent issues. Use when you need help fixing bugs, debugging code, solving problems, or preventing issues from happening again.
---

Before launching the agent, determine the skill name upfront so the UI can show progress immediately:

1. **Generate a skill name**: Based on the conversation context, generate a descriptive natural language name (capital letter for the first word, max 64 chars) that summarizes the main issue or automation opportunity. Examples: `Jira acli tickets`, `Search results validation`, `Prevent hardcoded config`.

2. **Report "creating" status**: Call the MCP `flow_entity_crud` tool with:
   - `crud`: "create"
   - `entity_json`: `{"type": "skill", "name": "<skill-name>", "description": "<brief description>", "status": "creating"}`

Use the Task tool with EXACTLY these parameters:
- `subagent_type: "skillit:skillit-creator"`
- `run_in_background: true`
- `prompt`: Pass the user's request and conversation context. Session properties:
  - `session_id`: <session_id>
  - `skillit_home`: <skillit_home>
  - `flow_output_directory`: <flow_output_directory>

## Permission fallback
When the background agent completes, check its result. If the agent failed due to **permission issues** (e.g. tool calls were denied, "not allowed", "permission", or the agent could not read/write files):
1. Inform the user: "The background agent couldn't get the permissions it needs. Resuming in the foreground so it can ask for approval."
2. **Resume** the same agent in the foreground using the Task tool with:
   - `resume`: the agent ID returned from the background launch
   - `run_in_background: false`
   - `prompt`: "Continue from where you left off. You previously failed due to permission issues — you are now running in the foreground and can request tool permissions interactively."

   This preserves the agent's full context and continues from the exact point where it got stuck, avoiding redundant work.

## Verify skill was installed
After the agent completes (whether from background or foreground), verify the skill was actually copied to the correct location based on its `recommended_scope`:
- If `recommended_scope` is `"project"`: check the **project's** `.claude/skills/` folder (relative to the project root)
- If `recommended_scope` is `"user"` (or not specified): check `~/.claude/skills/`

If the skill folder does NOT exist at the expected location but the skill files are present in the `flow_output_directory`, the agent likely missed the `flow_tag` call. In that case, call the MCP `flow_tag` tool yourself:
- `flow_tag_xml`: `<flow-skill event="skill_ready" name="<kebab-case-skill-name>" scope="<recommended_scope>" />`
- `claude_session_id`: the session_id
