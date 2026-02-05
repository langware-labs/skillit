#!/usr/bin/env python3
"""CLI entry point for system_profile scanner.

This script is designed to run standalone when the folder is copied to a compute node.
It sets up the Python path and then runs the scanner.
"""

import argparse
import json
import sys
from pathlib import Path

# Add this folder to path for standalone execution
_script_dir = Path(__file__).parent
sys.path.insert(0, str(_script_dir))

from scanner import (  # noqa: E402
    get_resource_summary,
    list_projects_fast,
    scan_full,
    scan_item,
    scan_project,
    scan_resources,
)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Claude Code system profile scanner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--action",
        "-a",
        type=str,
        default="full",
        choices=["full", "scan", "summary", "item", "list-projects", "scan-project"],
        help="Action: full (full profile), scan (targeted resource scan), summary (quick counts), item (legacy), list-projects (fast project list), scan-project (per-project scan)",
    )

    parser.add_argument(
        "--project",
        type=str,
        help="Project encoded name for scan-project action",
    )

    parser.add_argument(
        "--mode",
        "-m",
        type=str,
        default="full",
        choices=["full", "quick"],
        help="Scan mode for full action: full (default) or quick",
    )

    parser.add_argument(
        "--type",
        "-t",
        type=str,
        help="Resource type for targeted scan (e.g., hook, mcp_server, session, system_resource_claude_hook)",
    )

    parser.add_argument(
        "--time-start",
        type=str,
        help="Time window start (ISO format) for scan action",
    )

    parser.add_argument(
        "--time-end",
        type=str,
        help="Time window end (ISO format) for scan action",
    )

    parser.add_argument(
        "--parent-id",
        type=str,
        help="Parent ID for child resources (e.g., project_encoded_name for sessions)",
    )

    parser.add_argument(
        "--item",
        "-i",
        type=str,
        help="Scan specific item type (legacy, use --action=item --type=X instead)",
    )

    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=100,
        help="Limit number of items to return (default: 100, 0=unlimited)",
    )

    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Pagination offset (default: 0)",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output file path (default: stdout)",
    )

    parser.add_argument(
        "--pretty",
        "-p",
        action="store_true",
        help="Pretty print JSON output",
    )

    args = parser.parse_args()

    # Handle legacy --item argument (maps to action=item)
    if args.item:
        args.action = "item"
        args.type = args.item

    # Run based on action
    if args.action == "scan":
        # Targeted resource scan
        if not args.type:
            print(json.dumps({"error": "--type is required for scan action"}))  # noqa: T201
            sys.exit(1)

        time_window = None
        if args.time_start or args.time_end:
            time_window = {}
            if args.time_start:
                time_window["start"] = args.time_start
            if args.time_end:
                time_window["end"] = args.time_end

        result = scan_resources(
            resource_type=args.type,
            time_window=time_window,
            parent_id=args.parent_id,
            limit=args.limit,
            offset=args.offset,
        )

    elif args.action == "summary":
        # Quick resource counts
        result = get_resource_summary()

    elif args.action == "list-projects":
        # Fast project enumeration
        result = list_projects_fast()

    elif args.action == "scan-project":
        # Per-project scan
        if not args.project:
            print(json.dumps({"error": "--project is required for scan-project action"}))  # noqa: T201
            sys.exit(1)
        result = scan_project(args.project, session_limit=args.limit)

    elif args.action == "item":
        # Legacy item scan
        if not args.type:
            print(json.dumps({"error": "--type is required for item action"}))  # noqa: T201
            sys.exit(1)
        result = scan_item(args.type, limit=args.limit)
        if result is None:
            print(json.dumps({"error": f"Unknown item type: {args.type}"}))  # noqa: T201
            sys.exit(1)

    else:
        # Full profile scan (default)
        result = scan_full(session_limit=args.limit, mode=args.mode)

    # Format output
    indent = 2 if args.pretty else None
    output = json.dumps(result, indent=indent, default=str)

    # Write output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
    else:
        print(output)  # noqa: T201


if __name__ == "__main__":
    main()
