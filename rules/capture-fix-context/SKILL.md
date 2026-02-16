---
name: capture-fix-context
description: >
  Captures and documents fixes applied during conversations when the user says
  "remember this fix" or similar phrases. Stores the problem context, solution,
  affected files, and code changes in a structured format for future reference
  and potential automation. Use when the user wants to remember, save, or
  document a fix that was just applied.

license: MIT
metadata:
  author: skillit-creator
  version: "1.0"
---

# Capture Fix Context

This skill captures user-requested fixes with full context including the problem, solution, and affected files for future reference and automation.

## Instructions

When the user says "remember this fix" or similar phrases indicating they want to save a solution:

1. **Identify the fix context** by reviewing recent conversation history:
   - What was the problem or error that occurred?
   - What solution was applied to fix it?
   - Which files were modified?
   - What specific code changes were made?

2. **Create a structured fix record** in the user's fix repository:
   - Create or locate a `.fixes` directory in the project root
   - Generate a unique filename: `fix-YYYY-MM-DD-HHmmss-[short-description].md`
   - Use the Write tool to save the fix record

3. **Format the fix record** with the following structure:
   ```markdown
   # Fix: [Brief title]

   **Date:** YYYY-MM-DD HH:mm:ss
   **Session ID:** [if available]

   ## Problem
   [Clear description of what went wrong, including error messages]

   ## Solution
   [Step-by-step description of what was done to fix it]

   ## Files Modified
   - `path/to/file1.ext` - [what changed]
   - `path/to/file2.ext` - [what changed]

   ## Code Changes
   [Include relevant code snippets showing before/after if applicable]

   ## Tags
   [category], [technology], [component]

   ## Notes
   [Any additional context or future considerations]
   ```

4. **Confirm to the user**:
   - Report the absolute path where the fix was saved
   - Provide a brief summary of what was captured
   - Suggest they can retrieve this later by searching the `.fixes` directory

5. **Error handling**:
   - If unable to determine the fix context, ask the user to clarify what fix they want to remember
   - If the `.fixes` directory cannot be created, suggest an alternative location
   - If file write fails, report the error and offer to display the content for manual saving

## Examples

### Example 1: Remembering a bug fix

**Input:**
```
User: "remember this fix"
[After a conversation where a Python import error was fixed by adding a missing package to requirements.txt]
```

**Output:**
```
I've captured this fix and saved it to `.fixes/fix-2026-02-16-143022-missing-package-import.md`

Summary:
- Problem: ImportError for missing 'requests' package
- Solution: Added 'requests==2.28.0' to requirements.txt
- Files modified: requirements.txt

You can find this fix later by searching in the .fixes directory.
```

### Example 2: Remembering a configuration fix

**Input:**
```
User: "save this solution for later"
[After fixing a Docker configuration issue by updating docker-compose.yml]
```

**Output:**
```
I've documented this solution in `.fixes/fix-2026-02-16-144530-docker-port-conflict.md`

Summary:
- Problem: Port 8080 conflict preventing container startup
- Solution: Changed exposed port from 8080 to 8081 in docker-compose.yml
- Files modified: docker-compose.yml

The fix record includes the full context and code changes.
```

### Example 3: Unclear context

**Input:**
```
User: "remember this fix"
[No recent fix in conversation history]
```

**Output:**
```
I'd be happy to capture a fix for you! Could you clarify which fix you'd like me to remember?

I don't see a recent fix in our conversation history. Please let me know:
- What problem were you trying to solve?
- What solution did you apply?
- Which files were involved?
```

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| Cannot create `.fixes` directory | Permission issues or invalid path | Suggest creating fixes in user's home directory or a temporary location |
| Unclear what fix to capture | No recent fix in conversation or ambiguous context | Ask user to specify the problem and solution they want to remember |
| File already exists with same name | Multiple fixes saved in same second | Append counter suffix (-1, -2, etc.) to filename |
