---
name: acli-jira-subcommand-syntax
description: >
  Correct syntax for the acli (Atlassian CLI) tool when querying Jira.
  Use when the user asks to search Jira issues, list tickets, query workitems,
  or use the acli CLI with Jira. The acli tool uses subcommand-based syntax
  (acli jira workitem search) NOT the deprecated --action flag pattern.
  Trigger keywords: acli, jira, workitem, search, tickets, issues, JQL.
---

# acli Jira Subcommand Syntax

The `acli` CLI tool uses a modern subcommand-based syntax for Jira operations. Do NOT use the deprecated `--action` flag pattern. This skill prevents the common mistake of using `acli jira --action getIssueList` and similar flag-based patterns that will fail.

## Instructions

1. When running any `acli` command for Jira, always use the subcommand pattern: `acli jira <resource> <action> [flags]`.
2. To search for Jira issues, use `acli jira workitem search` with the `--jql` flag for the query and `--fields` flag for output columns.
3. Never use `--action` as a flag with `acli`. The action is always a positional subcommand.
4. If a command fails with "unknown flag: --action", rewrite it using the subcommand pattern described here.

## Syntax Reference

The general pattern for acli Jira commands is:

```
acli jira <resource> <action> [--flag value ...]
```

### Searching for Issues

```bash
acli jira workitem search --jql "<JQL query>" --fields "<comma-separated fields>"
```

**Common flags for `acli jira workitem search`:**
- `--jql` - JQL query string
- `--fields` - Comma-separated list of fields to display (e.g., "key,summary,priority,status")
- `--csv` - Output in CSV format
- `--json` - Output in JSON format
- `--limit` - Limit number of results
- `--paginate` - Enable pagination
- `--filter` - Use a saved filter
- `--web` - Open results in web browser
- `--count` - Show count only

## Examples

### Example 1: List unresolved tickets assigned to current user

**Input:**
```
Show me my open Jira tickets
```

**Command:**
```bash
acli jira workitem search --jql "assignee = currentUser() AND resolution = Unresolved ORDER BY priority DESC" --fields "key,summary,priority,status"
```

### Example 2: Common mistake to avoid

**Incorrect (will fail with "unknown flag: --action"):**
```bash
acli jira --action getIssueList --jql "assignee = currentUser()"
```

**Correct:**
```bash
acli jira workitem search --jql "assignee = currentUser()"
```

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `Error: unknown flag: --action` | Using deprecated `--action` flag syntax | Rewrite using subcommand pattern: `acli jira workitem search` instead of `acli jira --action getIssueList` |
| `Error: unknown command` | Wrong resource or action name | Run `acli jira --help` to see available subcommands, then `acli jira workitem --help` for actions |
