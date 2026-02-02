# Shared Skill Creation Instructions

## Input Parameters
- `transcript_path`: JSONL conversation transcript
- `skills_dir`: Base directory for skills (`<cwd>/.claude/skills/`)
- `session_events_script`: Path to the session_events.py script for reporting
- `skill_session_id`: Unique ID for this skill creation session (use this in all reports)
- `parent_session_id`: Session ID of the parent Claude session
- `cwd`: Current working directory

## Skill Creation Workflow (REQUIRED)

After analyzing the transcript and determining a meaningful skill name, follow these steps IN ORDER:

### Step 1: Report skill creation started
```bash
python3 "<session_events_script>" started_generating_skill '{"skill_name": "<skill-name>", "skill_session_id": "<skill_session_id>", "cwd": "<cwd>"}'
```

### Step 2: Create the skill file
Create the skill at `<skills_dir>/<skill-name>/SKILL.md` using the SKILL.md format below.

### Step 3: Report skill creation completed
```bash
python3 "<session_events_script>" skill_ready '{"skill_name": "<skill-name>", "skill_session_id": "<skill_session_id>", "cwd": "<cwd>"}'
```

Use the exact `skill_session_id` value provided in the input parameters.

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
