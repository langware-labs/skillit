---
description: Create a skill to fix and prevent issues. Use when you need help fixing bugs, debugging code, solving problems, or preventing issues from happening again.
---

Before launching the agent, determine the skill name upfront so the UI can show progress immediately:

1. **Generate a skill name**: Based on the conversation context, generate a descriptive natural language name (capital letter for the first word, max 64 chars) **and** its kebab-case folder name. Examples: `Jira acli tickets` → `jira-acli-tickets`, `Search results validation` → `search-results-validation`, `Prevent hardcoded config` → `prevent-hardcoded-config`.

2. **Determine scope**: Decide whether this skill is project-specific (`"project"`) or generally useful across all projects (`"user"`). If the skill addresses a pattern specific to the current codebase, use `"project"`. If it's broadly applicable, use `"user"`.

3. **Report "creating" status**: Call the MCP `flow_entity_crud` tool with:
   - `crud`: "create"
   - `entity_json`: `{"type": "skill", "name": "<Display Name>", "folder_name": "<kebab-case-name>", "description": "<brief description>", "status": "creating", "recommended_scope": "<user|project>"}`

Launch ONLY the `skillit:skillit-creator` agent. Do NOT also launch `skillit:skillit-analyzer` or any other agent — the creator already performs analysis internally.

Use the Task tool with EXACTLY these parameters:
- `subagent_type: "skillit:skillit-creator"`
- `background: true`
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

## Relay signals from background agent
After the background agent completes successfully, read the signal file at `<flow_output_directory>/flow_signals.jsonl`. For each line in the file, relay the signal to the appropriate MCP tool:

- Lines with `"type": "entity_crud"`: Call `flow_entity_crud` with the `crud` and `entity_json` values from the signal. Include `claude_session_id`.
- Lines with `"type": "flow_tag"`: Call `flow_tag` with the `xml` value as `flow_tag_xml`. Include `claude_session_id`.

This is necessary because the background agent cannot call MCP tools directly. The parent (foreground) agent acts as the relay.

## Verify skill was installed
After relaying signals, verify the skill was actually copied to the correct location based on its `recommended_scope`:
- If `recommended_scope` is `"project"`: check the **project's** `.claude/skills/` folder (relative to the project root)
- If `recommended_scope` is `"user"` (or not specified): check `~/.claude/skills/`

If the skill folder does NOT exist at the expected location but the skill files are present in the `flow_output_directory`, call the MCP `flow_tag` tool yourself:
- `flow_tag_xml`: `<flow-skill event="skill_ready" name="<kebab-case-skill-name>" scope="<recommended_scope>" />`
- `claude_session_id`: the session_id
