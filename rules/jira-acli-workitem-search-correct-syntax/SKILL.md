---
name: jira-acli-workitem-search-correct-syntax
description: >
  Use the Atlassian CLI (acli) to list and search Jira tickets assigned to the current user.
  Activates when the user asks to show, list, display, or query their Jira tickets, issues,
  or work items using acli. Provides the correct acli jira workitem search command syntax,
  avoiding common mistakes such as using legacy --action flags or wasting time with
  excessive help chain exploration before running the actual command.
---

# Jira Tickets via acli (Atlassian CLI)

This skill provides the correct syntax for listing Jira work items with the modern `acli` CLI,
preventing wasted time from wrong syntax attempts and unnecessary help command chains.

## Instructions

1. When the user asks to show their Jira tickets or work items using acli, do NOT first check browser tabs or navigate to Jira in a browser.
2. Do NOT use legacy flags such as `--action`, `--outputFormat`, or `--jql` at the top-level `acli jira` command. These are old JIRA CLI (Bob Swift) flags and do NOT work with the modern Atlassian `acli`.
3. Do NOT run a chain of `--help` commands to discover the correct syntax. Use the correct command below directly.
4. Run the search command immediately with the correct syntax:

```bash
acli jira workitem search --jql "assignee = currentUser() AND resolution = Unresolved ORDER BY updated DESC" --fields "key,summary,status,priority"
```

5. If the command fails with an authentication error, run `acli jira auth` to authenticate first, then retry.
6. Present the results in a clean markdown table format summarizing key, priority, status, and summary.

## Correct acli Command Syntax

The modern Atlassian CLI (`acli`) uses a subcommand hierarchy, NOT `--action` flags:

| Goal | Correct Command |
|------|----------------|
| List my open tickets | `acli jira workitem search --jql "assignee = currentUser() AND resolution = Unresolved ORDER BY updated DESC"` |
| Search with specific fields | `acli jira workitem search --jql "..." --fields "key,summary,assignee,priority,status"` |
| Get JSON output | `acli jira workitem search --jql "..." --json` |
| Paginate all results | `acli jira workitem search --jql "..." --paginate` |
| Limit results | `acli jira workitem search --jql "..." --limit 20` |

## Examples

### Example 1: Show my open Jira tickets

**User request:**
```
show my jira tickets
```

**Correct action:**
```bash
acli jira workitem search --jql "assignee = currentUser() AND resolution = Unresolved ORDER BY updated DESC" --fields "key,summary,status,priority"
```

**Expected output:**
```
Key                 Priority            Status              Summary
PROJ-1647           Medium              Triage              Some bug description
PROJ-1619           Medium              In progress         Feature work item
```

### Example 2: Wrong approach to avoid

**DO NOT run:**
```bash
# Wrong - uses legacy Bob Swift JIRA CLI syntax
acli jira --action getIssueList --jql "assignee = currentUser()" --outputFormat 2

# Wrong - wastes 4 roundtrips just to discover the search syntax
acli --help
acli jira --help
acli jira workitem --help
acli jira workitem search --help
```

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `unknown flag: --action` | Using old Bob Swift JIRA CLI syntax | Use `acli jira workitem search --jql "..."` instead |
| `unknown flag: --outputFormat` | Legacy flag not supported | Remove the flag; use `--json` or `--csv` for structured output |
| Authentication error | Not authenticated to Atlassian | Run `acli jira auth` first |
| `acli: command not found` | acli not installed | Install via `brew install atlassian/tap/atlassian-cli` on macOS |
