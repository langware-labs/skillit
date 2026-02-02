# Create Test Skill Instructions

## Input Parameters
- `transcript_path`: JSONL conversation transcript
- `skills_dir`: Base directory for skills (`<cwd>/.claude/skills/`)
- `cwd`: Current working directory

## Task

1. Read the transcript (JSONL, one JSON object per line)
2. Analyze the conversation to understand what was being tested/done
3. Determine a meaningful skill name based on the content (e.g., `bing-search-test`, `login-flow-test`, `button-color-test`)
4. Create the skill at `<skills_dir>/<skill-name>/SKILL.md`
5. Run the skill and report results

## Skill Name Rules
- Use kebab-case (lowercase with hyphens)
- Be descriptive of what the test does (e.g., `search-results-validation`, `form-submission-test`)
- Do NOT use generic names like `test-123` or `test-<timestamp>`

## SKILL.md Format

```markdown
---
name: <skill-name>
description: <What this test does>. Use when <trigger phrases and contexts>.
---

# <Name> Test

## Steps
1. <Action>
   - Expected: <Result>

## Success Criteria
- <Criterion>
```

## Frontmatter Rules
- `name`: kebab-case skill name (same as folder name)
- `description`: CRITICAL - this is how Claude decides when to invoke the skill. Must include:
  - What the test verifies (first sentence)
  - Trigger phrases: "Use when user asks to...", "Invoke for...", "Run when testing..."
  - Relevant contexts and scenarios

## Step Types
- Navigation: "Open browser at URL" / "Navigate to URL"
- Assertion: "Assert <condition>"
- Action: "Click on X" / "Enter Y in Z"
- Wait: "Wait for <condition>"

## Rules
- One action per step
- Include expected result for each step
- Use specific selectors/identifiers when mentioned
- Note assumptions if info is unclear
