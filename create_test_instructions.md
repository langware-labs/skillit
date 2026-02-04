# Create Test Skill Instructions

First, read the shared instructions at `{plugin_dir}/shared_skill_instructions.md`.

## Task

1. Analyze the conversation that led to this skill creation request
2. Understand what was being tested/done
3. Determine a meaningful skill name based on the content (e.g., `bing-search-test`, `login-flow-test`)
4. Follow the **Skill Creation Workflow** in shared instructions (report started → create skill → report completed)

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
