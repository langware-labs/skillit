## Skillit: Create Activation Rule Skill

Launch a Task subagent to analyze this conversation and create activation rules.

### Use the Task tool with:
- subagent_type: "general-purpose"
- description: "Analyze conversation and create activation rules for Skillit skills."
- prompt: {instructions_content}

### Context Variables
- target_dir: {target_dir}
- session_id: Use ${{CLAUDE_SESSION_ID}} environment variable
- cwd: {cwd}
- activation_rules_script: {activation_rules_script}
- plugin_dir: {plugin_dir}

### After Task Completes - FOLLOW THESE STEPS EXACTLY
1. Summarize what skill was created
2. Tell the user how to invoke it
3. You may use AskUserQuestion if clarification is needed.
{ad_section}
