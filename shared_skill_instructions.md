# Shared Skill Creation Instructions

## Input Parameters
- `skills_dir`: Base directory for skills (`<cwd>/.claude/skills/`)
- `activation_rules_script`: Path to the activation_rules.py script for reporting
- `cwd`: Current working directory

## Conversation Context
You have access to the current conversation context. Analyze the conversation that led to this skill creation request to understand what needs to be addressed.

## Skill Creation Workflow (REQUIRED)

After analyzing the conversation and determining a meaningful skill name, follow these steps IN ORDER:

### Step 1: Report skill creation started
```bash
python3 "<activation_rules_script>" started_generating_skill '{"skill_name": "<skill-name>", "session_id": "${CLAUDE_SESSION_ID}", "cwd": "<cwd>"}'
```

### Step 2: Create the skill file

⚠️ **CRITICAL: Directory Structure**
Skills MUST be created in a subdirectory, NOT as a flat file:
- ✅ CORRECT: `<skills_dir>/<skill-name>/SKILL.md`
- ❌ WRONG: `<skills_dir>/<skill-name>.md`

First create the directory `<skills_dir>/<skill-name>/`, then create the file `SKILL.md` inside it.

Use the SKILL.md format below.

### Step 3: Report skill creation completed
```bash
python3 "<activation_rules_script>" skill_ready '{"skill_name": "<skill-name>", "session_id": "${CLAUDE_SESSION_ID}", "cwd": "<cwd>"}'
```

## Skill Name Rules
- Use kebab-case (lowercase with hyphens)
- Be descriptive of what the skill does
- Do NOT use generic names like `test-123` or `skill-<timestamp>`
- Examples: `search-results-validation`, `prevent-hardcoded-config`, `form-submission-test`

## SKILL.md Format

```markdown
---
name: <skill-name>
description: <What this skill does>. Use when <trigger phrases and contexts>.
---

# <Name>

## Steps
1. <Action>
   - Expected: <Result>

## Success Criteria
- <Criterion>
```

## Frontmatter Rules
- `name`: kebab-case skill name
- `description`: CRITICAL - this is how Claude decides when to invoke the skill. Must include:
  - What the skill does (first sentence)
  - Trigger phrases: "Use when user asks to...", "Invoke for...", "Run when..."
  - Relevant contexts and scenarios
