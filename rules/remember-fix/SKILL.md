---
name: remember-fix
description: >
  Captures and persists fixes, solutions, workarounds, and problem-solution pairs
  discovered during conversations. Use when the user says "remember this fix",
  "save this solution", "capture this workaround", or similar phrases indicating
  they want to preserve knowledge for future reference.
metadata:
  author: skillit
  version: "1.0"
---

# Remember Fix

Automatically captures fixes, solutions, and workarounds from conversations and persists them as structured knowledge artifacts for future retrieval.

## Instructions

<!-- INSTRUCTIONS: Write the step-by-step procedure Claude should follow.
     Be specific and actionable. Use imperative form ("Extract the text",
     not "You should extract the text").

     Choose a freedom level based on the task:
       - High freedom: text instructions (multiple valid approaches)
       - Medium freedom: pseudocode (preferred patterns with variation)
       - Low freedom: specific scripts (error-prone tasks needing consistency)

     Include error handling guidance where things can go wrong.
     If a step requires a tool, name the tool explicitly.
     DELETE this comment block when done. -->

1. [First step — what to do, what tool to use, what to check]
2. [Second step — build on the previous step's output]
3. [Third step — produce the final result]
4. [Error handling — what to do if something fails]

## Examples

<!-- INSTRUCTIONS: Provide 2-3 concrete input/output examples.
     Show realistic scenarios, not abstract ones.
     Include at least one edge case or error scenario.
     Use fenced code blocks for inputs and outputs.
     DELETE this comment block when done. -->

### Example 1: [Scenario name]

**Input:**
```
[Realistic user request or input data]
```

**Output:**
```
[Expected result or Claude's response]
```

### Example 2: [Scenario name]

**Input:**
```
[Another realistic scenario, ideally an edge case]
```

**Output:**
```
[Expected result]
```

## Reference Files

<!-- INSTRUCTIONS: List additional files in this skill directory that Claude
     should load on-demand (not at startup). These don't cost tokens until needed.
     Keep references one level deep from SKILL.md.
     Organize by domain (e.g., references/api.md, references/examples.md).
     DELETE this entire section if your skill has no reference files. -->

- [Detailed API reference](references/REFERENCE.md)
- [Extended examples and templates](references/EXAMPLES.md)

## Troubleshooting

<!-- INSTRUCTIONS: List common errors and their solutions.
     Format as: problem → cause → fix.
     DELETE this entire section if not applicable. -->

| Problem | Cause | Fix |
|---------|-------|-----|
| [Error message or symptom] | [Why it happens] | [How to resolve] |
| [Another common issue] | [Root cause] | [Solution] |
