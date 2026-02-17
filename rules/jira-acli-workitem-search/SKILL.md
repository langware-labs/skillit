---
name: jira-acli-workitem-search
description: >
  Skill for listing and searching the user's Jira tickets using the Atlassian CLI (acli).
  Use when the user asks to show, list, view, or find their Jira tickets, issues, or work
  items using acli. Knows the correct acli jira workitem search command syntax, avoiding
  the outdated --action flag pattern from the old Atlassian CLI v8.
  Trigger keywords: jira tickets, jira issues, acli, show my tickets, list jira, my work items.
metadata:
  author: skillit
  version: "1.0"
---

# Jira Tickets via acli (Atlassian CLI)

This skill retrieves and displays the user's Jira work items using the Atlassian CLI (acli).
It uses the correct modern acli syntax to avoid wasting time on help discovery.

## Instructions

1. Verify acli is installed by running `which acli`. If not found, inform the user and stop.
2. Run the search command directly using the correct modern syntax:
   ```
   acli jira workitem search --jql "assignee = currentUser() AND resolution = Unresolved ORDER BY updated DESC" --fields "key,summary,status,priority"
   ```
3. Display the results in a clean markdown table with columns: Key, Priority, Status, Summary.
4. Provide a brief summary count (e.g., "You have 7 open tickets — 1 in progress, 5 in Triage").
5. If the command fails with an auth error, prompt the user to run `acli jira auth` first.
6. Do NOT use browser/tab tools to look up Jira when acli is available — use the CLI directly.

**Important**: Do NOT use the old `--action` flag syntax (e.g., `acli jira --action getIssueList`).
That is the legacy Atlassian CLI v8 syntax and will fail with "unknown flag: --action".
The correct command structure is: `acli jira workitem search --jql "..."`.

## Examples

### Example 1: Show my open Jira tickets

**Input:**
```
show my jira tickets
```

**Command run:**
```bash
acli jira workitem search --jql "assignee = currentUser() AND resolution = Unresolved ORDER BY updated DESC" --fields "key,summary,status,priority"
```

**Output displayed to user:**
```
Here are your open Jira tickets:

| Key       | Priority | Status      | Summary                               |
|-----------|----------|-------------|---------------------------------------|
| PROJ-1647 | Medium   | Triage      | Refresh clears thinking segments      |
| PROJ-1619 | Medium   | In progress | Planner - AMD execution planning      |
| PROJ-1646 | Medium   | Triage      | Sessions disappear after page refresh |

You have 3 open tickets — 1 in progress, 2 in Triage.
```

### Example 2: Filter tickets by project

**Input:**
```
show my jira tickets for project MYPROJ
```

**Command run:**
```bash
acli jira workitem search --jql "assignee = currentUser() AND project = MYPROJ AND resolution = Unresolved ORDER BY updated DESC" --fields "key,summary,status,priority"
```

### Example 3: acli not authenticated

**Input:**
```
show my jira tickets
```

**If acli returns auth error:**
```
Authentication required. Please run:
  acli jira auth

Then retry the request.
```

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `unknown flag: --action` | Using old Atlassian CLI v8 syntax | Use `acli jira workitem search --jql "..."` instead |
| Authentication required / 401 error | Not logged in to acli | Run `acli jira auth` to authenticate |
| `acli: command not found` | acli not installed | Install via `brew install atlassian/acli/acli` (macOS) |
| Empty results | No unresolved tickets assigned to current user | Broaden the JQL query or check the correct Jira account |
