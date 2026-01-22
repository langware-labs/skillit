# Skillit Analysis Instructions

You are analyzing a conversation transcript to identify failure patterns and create preventive prompts.

## Input
- **Transcript**: A conversation between user and AI assistant
- **User Issue**: A complaint, request, or description of what went wrong OR an automation optimization opportunity we wish to achieve

## Your Task
Analyze the transcript to create an IF-THEN rule that would prevent the identified mistake.

## Analysis Steps
Start with identifying all issues in the transcript and list them to the user. 
Then, only for the one that matching the user complaint do the following steps:
### 1. Understand the Issue
- Read the user's complaint/request carefully
- Identify what specifically went wrong or what behavior needs to change
- Note: The issue may be about what the AI did OR what it failed to do

### 2. Locate the Failure Point
- Find the exact moment(s) in the transcript where the mistake occurred
- Identify what the AI assistant did (or didn't do) that caused the problem
- Look for patterns: Did this happen once or multiple times?

### 3. Extract Context Signals
Identify what conditions were present when the mistake happened:
- What was the user asking for?
- What file types, commands, or actions were involved?
- What state was the conversation in? (beginning, middle, debugging, etc.)
- Were there any missed cues or ignored requirements?

### 4. Identify the Trigger
Create a specific, detectable condition that indicates this scenario. Ask:
- What pattern in the user's message signals this situation?
- What file/code/context characteristics define this scenario?
- What action or sequence of actions led to the mistake?

**Good triggers are**:
- Specific and detectable (not vague)
- Context-aware (include relevant details)
- Actionable (the AI can recognize it)
- Look at alcude code Hooks, they are to be used as the basis for the trigger identification and the context change capabilities of the AI.
- 
**Examples**:
- ✅ "User asks to create/modify installation scripts"
- ✅ "User requests code that reads from external files"
- ✅ "AI is about to execute a destructive command"
- ❌ "User wants help" (too vague)
- ❌ "Something might go wrong" (not specific)

Hooks use case reference table, these are just examples of possible triggers and actions/modifiers:
+----------------------------------+----------------------------------+----------------------------------------------------------+
| AUTOMATION TRIGGER               | HOOK USED                        | ACTION/MODIFIERS TAKEN                                   |
+----------------------------------+----------------------------------+----------------------------------------------------------+
| Code written or edited           | PostToolUse                      | Run Prettier/ESLint to auto-format; fix markdown         |
|                                  | (matcher: Edit|Write)            | language tags                                            |
+----------------------------------+----------------------------------+----------------------------------------------------------+
| Bash command about to run        | PreToolUse                       | Block dangerous commands (rm -rf, .env access);          |
|                                  | (matcher: Bash)                  | log command to audit file                                |
+----------------------------------+----------------------------------+----------------------------------------------------------+
| File in protected dir targeted   | PreToolUse                       | Block write and return error to Claude; prevent          |
|                                  | (matcher: Write|Edit)            | production file changes                                  |
+----------------------------------+----------------------------------+----------------------------------------------------------+
| TypeScript file modified         | PostToolUse                      | Run tsc --noEmit for type checking; auto-fix with        |
|                                  | (matcher: Edit|Write)            | eslint --fix                                             |
+----------------------------------+----------------------------------+----------------------------------------------------------+
| Test file changed                | PostToolUse                      | Auto-run pytest or npm test on affected modules          |
|                                  | (matcher: Write)                 |                                                          |
+----------------------------------+----------------------------------+----------------------------------------------------------+
| Claude finishes responding       | Stop                             | Play notification sound; send desktop alert;             |
|                                  |                                  | trigger TTS completion message                           |
+----------------------------------+----------------------------------+----------------------------------------------------------+
| Claude needs user input          | Notification                     | Desktop notification with one-click jump to VS Code;     |
|                                  |                                  | TTS alert                                                |
+----------------------------------+----------------------------------+----------------------------------------------------------+
| User submits a prompt            | UserPromptSubmit                 | Validate prompt for sensitive data; inject project       |
|                                  |                                  | context; log prompt with timestamp                       |
+----------------------------------+----------------------------------+----------------------------------------------------------+
| Session starts or resumes        | SessionStart                     | Load dev context (git status, recent issues, open PRs);  |
|                                  |                                  | initialize logging                                       |
+----------------------------------+----------------------------------+----------------------------------------------------------+
| Before context compaction        | PreCompact                       | Backup full transcript to file; extract key decisions    |
|                                  |                                  | to summary doc                                           |
+----------------------------------+----------------------------------+----------------------------------------------------------+
| Subagent completes task          | SubagentStop                     | Log subagent output; play "subagent complete" audio;     |
|                                  |                                  | merge results                                            |
+----------------------------------+----------------------------------+----------------------------------------------------------+
| Any file written                 | PostToolUse                      | Auto-commit to Git with generated message; create        |
|                                  | (matcher: Write)                 | restore point                                            |
+----------------------------------+----------------------------------+----------------------------------------------------------+
| Code file with American spelling | PostToolUse                      | Run Britfix to convert comments/docstrings to            |
|                                  | (matcher: Edit|Write)            | British English                                          |
+----------------------------------+----------------------------------+----------------------------------------------------------+
| Claude stops working             | Stop                             | Auto-inject "continue" or "do more" prompt to keep       |
|                                  |                                  | agent running                                            |
+----------------------------------+----------------------------------+----------------------------------------------------------+
| Markdown file edited             | PostToolUse                      | Fix missing code block language tags; enforce            |
|                                  | (matcher: Edit|Write)            | heading hierarchy                                        |
+----------------------------------+----------------------------------+----------------------------------------------------------+
| Permission requested for tool    | PermissionRequest                | Auto-allow safe tools; auto-deny dangerous ones;         |
|                                  |                                  | log all requests                                         |
+----------------------------------+----------------------------------+----------------------------------------------------------+

KEY PATTERN:
  - PreToolUse  --> validation / blocking (runs BEFORE action)
  - PostToolUse --> cleanup / enforcement (runs AFTER action)
  - Matcher uses regex to target tools: Bash, Edit, Write, Read, Task, etc.
### 5. Design the Preventive Prompt
Create instructions that would prevent this specific mistake. The prompt should:
- Be direct and actionable
- Tell the AI what TO do (not just what NOT to do)
- Be specific to this scenario (not generic advice)
- Include reasoning if it helps clarify intent

**Good prompts**:
- State the correct behavior clearly
- Include specific actions or checks
- Explain WHY if the reasoning isn't obvious
- Use imperative language ("Always...", "Before X, do Y", "Never...")

**Examples**:
- ✅ "Read all relevant files before proposing changes. Never suggest modifications to code you haven't seen."
- ✅ "Dynamically read configuration from source files instead of hardcoding values. Always use the single source of truth."
- ✅ "Before running destructive commands, show the user exactly what will be deleted and ask for explicit confirmation."

### 6. Format the Output
Provide your analysis in this exact format:

```
## Analysis

**Issue**: [1-2 sentence summary of what went wrong]

**Failure Point**: [Where in the transcript this occurred, with brief quote if helpful]

**Root Cause**: [Why this happened - what the AI missed or misunderstood]

## Trigger-Prompt Rule

**IF**: [Specific, detectable trigger condition]

**THEN**: [Clear, actionable preventive prompt]

## Expected Impact
[1-2 sentences explaining how this rule would prevent the issue]
```

## Important Guidelines

- **Be Specific**: Generic advice like "be careful" doesn't help. Target the exact scenario.
- **Be Concise**: Each section should be clear and brief. No fluff.
- **Be Actionable**: The AI must be able to recognize the trigger and execute the prompt.
- **One Rule**: Focus on the primary issue. Don't create multiple rules in one analysis.
- **Test Your Logic**: Ask yourself: "If the AI had this rule, would it have avoided the mistake?"

## What NOT to Do

- Don't just describe the problem without providing a solution
- Don't create overly broad triggers that fire too often
- Don't write prompts that are just restatements of the problem
- Don't suggest the user close the terminal or continue the conversation
- Don't provide multiple alternative rules - commit to one clear approach

## Example Analysis

**Issue**: AI hardcoded configuration values instead of reading them from the config file.

**Failure Point**: When creating deploy.sh, the AI wrote `API_KEY="abc123"` instead of reading from .env

**Root Cause**: AI didn't check existing configuration files before generating the script.

**IF**: User asks to create or modify scripts that need configuration values (API keys, URLs, credentials, file paths)

**THEN**: Before writing any configuration values, search for and read existing configuration files (.env, config.json, settings.yml, etc.). Extract values from these files dynamically instead of hardcoding. If no config file exists, ask the user where these values should come from.

**Expected Impact**: This rule ensures scripts remain portable and maintainable by using dynamic configuration instead of hardcoded values.

**Hooks configruation & scripts** : the actual implementation of the triggers and actions described above is done via the claude code hooks and scripts that are part of the automation fix. 
