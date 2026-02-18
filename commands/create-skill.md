---
description: Create a skill to fix and prevent issues. Use when you need help fixing bugs, debugging code, solving problems, or preventing issues from happening again.
---

Launch ONLY ONE agent: `skillit:skillit-creator`. Do NOT launch any other agent.

Use the Task tool with EXACTLY these parameters:
- `subagent_type: "skillit:skillit-creator"`
- `run_in_background: true`
- `prompt`: Pass the user's request and conversation context. Session properties:
  - `session_id`: <session_id>
  - `skillit_home`: <skillit_home>
  - `flow_output_directory`: <flow_output_directory>