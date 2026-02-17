---
name: jira-browser-vs-acli
description: >
  Use the Atlassian CLI (acli) to fetch and display the user's Jira tickets
  instead of navigating the browser. Activate when the user asks to show, list,
  retrieve, or display their Jira tickets, issues, tasks, or work items. Prefer
  acli CLI commands over browser tab navigation for speed and reliability.
  Trigger keywords: jira tickets, jira issues, my tickets, show tickets,
  list issues, jira tasks, assigned tickets, open tickets.
---

# Jira Ticket Retrieval via Atlassian CLI (acli)

When the user asks to show or list their Jira tickets, use the `acli` Atlassian CLI tool to retrieve them directly. Do NOT attempt browser navigation as the first approach — the browser may not have Jira open and requires user interaction to obtain a URL.

## Instructions

1. Run `acli jira --action getIssueList --jql "assignee = currentUser() AND statusCategory != Done ORDER BY updated DESC"` to fetch the user's open tickets.
2. If `acli` is not found or fails with a command-not-found error, check if it is installed at a non-standard path (e.g., `which acli` or `acli --help`) before falling back to another approach.
3. If `acli` is unavailable in the environment, fall back to using the Jira REST API via `curl` with the user's credentials, or navigate the browser to the user's Jira instance as a last resort.
4. Present the results in a readable table with columns: Issue Key, Summary, Status, Priority, and Updated date.
5. If the JQL query returns no results, inform the user that no open tickets were found and suggest they may want to broaden the filter.

## Examples

### Example 1: User asks to list their Jira tickets

**Input:**
```
show my jira tickets
```

**Output (action taken):**
```bash
acli jira --action getIssueList --jql "assignee = currentUser() AND statusCategory != Done ORDER BY updated DESC"
```

**Displayed result:**
```
| Key      | Summary                          | Status      | Priority | Updated    |
|----------|----------------------------------|-------------|----------|------------|
| PROJ-123 | Fix login page redirect bug      | In Progress | High     | 2026-02-16 |
| PROJ-118 | Update onboarding documentation  | To Do       | Medium   | 2026-02-14 |
```

### Example 2: acli not available — fallback

**Input:**
```
list my open jira issues
```

**Action taken:**
```bash
# acli not found — inform the user and ask for Jira URL or credentials
```

**Output:**
```
The acli tool is not installed in this environment. To retrieve your Jira tickets,
please provide your Jira instance URL (e.g., yourcompany.atlassian.net) so I can
navigate there directly.
```

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `acli: command not found` | Atlassian CLI not installed or not on PATH | Check with `which acli`; if missing, fall back to browser or REST API |
| Authentication error from acli | Stored credentials expired or missing | Re-run `acli jira --configure` or use API token via environment variable |
| No tickets returned | JQL filter too restrictive | Broaden filter: remove `statusCategory != Done` or change assignee clause |
| Browser has no Jira tab | User does not have Jira open | Do NOT ask user to open Jira; use acli or REST API instead |
