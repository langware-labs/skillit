---
name: jira-acli-workitem-search-syntax
description: >
  Provides the correct acli command syntax for querying, listing, searching,
  or showing Jira tickets and work items via the Atlassian CLI (acli). Use when
  the user asks to show, list, find, view, or search their Jira tickets, issues,
  or work items using acli. Prevents wasted multi-step help-discovery calls by
  providing the correct syntax upfront. Trigger keywords: jira, acli, tickets,
  issues, work items, list jira, show jira, search jira.
---

# Jira acli Workitem Search

This skill provides the correct `acli` command syntax for listing and searching Jira tickets. It prevents the common mistake of using legacy or incorrect flag syntax (e.g., `--action getIssueList`) that causes command failures and multiple unnecessary help-discovery calls.

## Instructions

1. When the user asks to show, list, find, or search their Jira tickets using `acli`, use the following command directly without first running `acli --help` or intermediate help discovery calls:

   ```bash
   acli jira workitem search --jql "assignee = currentUser() AND resolution = Unresolved ORDER BY updated DESC" --fields "key,summary,status,priority"
   ```

2. Do NOT use legacy or incorrect flag syntax such as:
   - `acli jira --action getIssueList` (wrong — `--action` flag does not exist in modern acli)
   - `acli jira getIssueList` (wrong subcommand)

3. The correct command structure is:
   ```
   acli jira workitem search [flags]
   ```
   Key flags:
   - `--jql "..."` — JQL query string (use `assignee = currentUser()` for current user's tickets)
   - `--fields "field1,field2,..."` — Fields to display (default: `issuetype,key,assignee,priority,status,summary`)
   - `--limit N` — Maximum number of work items to fetch
   - `--paginate` — Fetch all results with pagination
   - `--json` — Output as JSON
   - `--csv` — Output as CSV

4. If `acli` is not installed, check with `which acli 2>/dev/null` and inform the user if not found.

5. Display the results in a clean markdown table format to the user.

## Examples

### Example 1: Show current user's open tickets

**Input:**
```
show my jira tickets
```

**Command to run:**
```bash
acli jira workitem search --jql "assignee = currentUser() AND resolution = Unresolved ORDER BY updated DESC" --fields "key,summary,status,priority"
```

**Expected result:**
```
Key                 Priority            Status              Summary
PROJECT-1234        Medium              In progress         Fix login bug
PROJECT-1235        High                Triage              Performance regression
```

### Example 2: Search tickets with pagination

**Input:**
```
show all my jira tickets including resolved ones
```

**Command to run:**
```bash
acli jira workitem search --jql "assignee = currentUser() ORDER BY updated DESC" --fields "key,summary,status,priority" --paginate
```

### Example 3: acli not installed

**Input:**
```
show my jira tickets using acli
```

If `acli` is not found after `which acli 2>/dev/null`:
```
acli is not installed. Install it via Homebrew: brew install atlassian/tap/acli
Then authenticate with: acli jira auth login
```

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `unknown flag: --action` | Using legacy/wrong syntax from older Atlassian CLI versions | Use `acli jira workitem search --jql "..."` instead |
| `command not found: acli` | acli not installed | Install via `brew install atlassian/tap/acli` (macOS) |
| Authentication error | Not authenticated to Jira | Run `acli jira auth login` first |
| Empty results | JQL returns nothing or wrong user | Check JQL, try removing `resolution = Unresolved` filter |
