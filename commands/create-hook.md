---
description: Create a hook/trigger from a session insight. Use when a session reveals a workflow that should happen automatically in response to events.
allowed-tools: mcp__plugin_skillit_flow_sdk__*
---

Before launching the agent, report creation start to the server:

1. **Report "creating" status**: Call the MCP `flow_entity_crud` tool with:
   - `crud`: "create"
   - `entity_json`: `{"type": "hook", "status": "creating", "description": "<brief description of the hook>"}`

Launch ONLY ONE agent: `skillit:skillit-hook-creator`. Do NOT launch any other agent.

Use the Task tool with EXACTLY these parameters:
- `subagent_type: "skillit:skillit-hook-creator"`
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

## Relay signals from background agent
After the background agent completes successfully, read the signal file at `<flow_output_directory>/flow_signals.jsonl`. For each line in the file, relay the signal to the appropriate MCP tool:

- Lines with `"type": "entity_crud"`: Call `flow_entity_crud` with the `crud` and `entity_json` values from the signal. Include `claude_session_id`.
- Lines with `"type": "flow_tag"`: Call `flow_tag` with the `xml` value as `flow_tag_xml`. Include `claude_session_id`.

This is necessary because the background agent cannot call MCP tools directly. The parent (foreground) agent acts as the relay.

## Verify hook was installed
After relaying signals, verify the Trigger entity was created via the graph API or that the hook configuration was written to the expected location.
