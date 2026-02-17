---
name: jira-acli-tickets
description: >
  Retrieve and display the current user's Jira tickets using the Atlassian CLI (acli).
  Use when the user asks to show, list, view, search, or display their Jira tickets,
  issues, or work items via acli or the command line. Knows the correct acli v2 command
  structure: "acli jira workitem search --jql ..." instead of the older --action flag style.
  Avoids opening a browser or checking browser tabs when acli is available. Avoids
  multi-step --help discovery chains. Trigger keywords: jira tickets, jira issues,
  show tickets, list tickets, my tickets, acli jira, show my jira, use acli, my jira.
---

# Jira Tickets via acli

This skill enables Claude to fetch and display the current user's Jira work items using the
Atlassian CLI (acli). It avoids common mistakes: using outdated `--action` flags, checking
browser tabs when acli is available, and running multi-step `--help` discovery chains.

## Instructions

1. When the user asks to show their Jira tickets, prefer `acli` over browser navigation — do NOT check open browser tabs or ask for a Jira URL if acli can be used.
2. Do NOT call `acli --help`, `acli jira --help`, or `acli jira workitem --help` to discover the command — the correct syntax is already known (see step 4).
3. Do NOT use `acli jira --action getIssueList` — that flag does not exist in the current acli version and will fail with "unknown flag: --action".
4. Run the correct command directly:
   ```
   acli jira workitem search --jql "assignee = currentUser() AND resolution = Unresolved ORDER BY updated DESC" --fields "key,summary,status,priority"
   ```
4. If `acli` is not installed, check with `which acli` and inform the user if it is missing.
5. Present the results in a readable markdown table with columns: Key, Priority, Status, Summary.
6. Summarize the ticket count and breakdown by status at the end.

### Command reference

| Goal | Command |
|------|---------|
| List my open tickets | `acli jira workitem search --jql "assignee = currentUser() AND resolution = Unresolved ORDER BY updated DESC" --fields "key,summary,status,priority"` |
| List all open tickets in a project | `acli jira workitem search --jql "project = MYPROJECT AND resolution = Unresolved" --paginate` |
| Count my open tickets | `acli jira workitem search --jql "assignee = currentUser() AND resolution = Unresolved" --count` |
| Output as JSON | `acli jira workitem search --jql "..." --json` |
| Limit results | `acli jira workitem search --jql "..." --limit 20` |

## Examples

### Example 1: User asks to show their Jira tickets

**Input:**
```
show my jira tickets
```

**Action (correct):**
```bash
acli jira workitem search --jql "assignee = currentUser() AND resolution = Unresolved ORDER BY updated DESC" --fields "key,summary,status,priority"
```

**Output:**
```
| Key          | Priority | Status      | Summary                            |
|--------------|----------|-------------|------------------------------------|
| PROJ-123     | High     | In progress | Fix authentication bug             |
| PROJ-456     | Medium   | Triage      | Update onboarding flow             |

You have 2 open tickets — 1 in progress, 1 in Triage.
```

### Example 2: Wrong approach to avoid

**Do NOT run:**
```bash
acli jira --action getIssueList --jql "assignee = currentUser()" --outputFormat 2
```
This will fail with: `Error: unknown flag: --action`

**Use instead:**
```bash
acli jira workitem search --jql "assignee = currentUser() AND resolution = Unresolved ORDER BY updated DESC"
```

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `Error: unknown flag: --action` | Using outdated acli v1 syntax | Use `acli jira workitem search --jql "..."` instead |
| `command not found: acli` | acli not installed | Install via `brew install atlassian/acli/acli` (macOS) or check Atlassian docs |
| No results returned | User not authenticated | Run `acli jira auth` to authenticate first |
| `currentUser()` not recognized | Authentication issue | Re-authenticate with `acli jira auth` |
