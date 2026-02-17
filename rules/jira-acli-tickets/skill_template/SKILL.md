<!-- ╔══════════════════════════════════════════════════════════════════╗
     ║              HOW TO FILL THIS TEMPLATE                           ║
     ║                                                                  ║
     ║  1. Fill in each [PLACEHOLDER] with your content                 ║
     ║  2. Delete all sections that are not relevant for the issue      ║
     ║  3. Delete all <!-- INSTRUCTIONS: ... -- > comment blocks        ║
     ║  4. Delete all yaml header comment blocks                        ║
     ║  5. Delete this entire boxed section when done                   ║
     ║                                                                  ║
     ║  Naming rules:                                                   ║
     ║  - Lowercase letters, numbers, hyphens only (max 64 chars)       ║
     ║  - Example: "pdf-extractor", "code-review", "jira-sync"          ║
     ║                                                                  ║
     ║  Description is critical:                                        ║
     ║  - Claude uses it to decide whether to load this skill           ║
     ║  - Include trigger keywords and use-case context                 ║
     ║  - Max 1024 characters                                           ║
     ║                                                                  ║
     ║  Size guidelines:                                                ║
     ║  - Keep SKILL.md under 500 lines (~5000 tokens)                  ║
     ║  - Move detailed content to reference files in references/       ║
     ║  - The context window is a public good — only include info       ║
     ║    Claude doesn't already have                                   ║
     ║                                                                  ║
     ║  Validate with: skills-ref validate ./your-skill                 ║
     ╚══════════════════════════════════════════════════════════════════╝ -->

---
name: [your-skill-name]
# ^ Required. Lowercase letters, numbers, hyphens only. Max 64 chars.
#   Must match the directory name. Example: "csv-analyzer"

description: >
  [What this skill does and when Claude should use it.
  Include trigger keywords so Claude knows when to activate.
  Example: "Extract text and tables from PDF files. Use when
  the user asks to read, parse, analyze, or convert PDF documents."]
# ^ Required. Max 1024 chars. This is the most important field —
#   Claude uses it to decide whether to load the skill at all.

# --- Optional fields (uncomment and fill as needed) ---
# license: MIT
# compatibility: Requires Python 3.10+, git
# allowed-tools: Read Grep Bash(python:*)
#   ^ Restrict which tools this skill can use. Omit to allow all.
#     Use Bash(command:*) globs to limit shell commands.
# metadata:
#   author: [your-name-or-org]
#   version: "1.0"
---

# [Skill Name]

<!-- INSTRUCTIONS: Write a 1-2 sentence overview of what this skill does.
     Keep it concise — the description field in frontmatter already covers
     "when to use". Focus on what value it provides.
     DELETE this comment block when done. -->

[Brief overview of this skill's purpose and value.]

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
