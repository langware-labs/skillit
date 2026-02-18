"""Analyze a Claude Code session transcript and print its summary log.

Usage:
    python -m analyzer.analyze [path/to/session.jsonl]

If no path is provided, uses the default transcript path below.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running from the scripts/ directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from records.claude import ClaudeSessionFsRecord

DEFAULT_TRANSCRIPT = (
    Path.home()
    / ".claude"
    / "projects"
    / "-Users-shlom-Documents-dev-skillit"
    / "9cccf790-2dd6-41ff-ad46-ecc2f29f55d9.jsonl"
)


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TRANSCRIPT
    if not path.is_file():
        print(f"Error: transcript not found: {path}", file=sys.stderr)
        sys.exit(1)

    session = ClaudeSessionFsRecord.from_jsonl(path)

    print(f"Session : {session.session_id}")
    print(f"Slug    : {session.slug}")
    print(f"Branch  : {session.git_branch}")
    print(f"Model   : {session.model}")
    print(f"Messages: {session.message_count} "
          f"(user={session.user_message_count}, "
          f"assistant={session.assistant_message_count})")
    print(f"Tokens  : in={session.input_tokens} out={session.output_tokens}")
    print(f"Duration: {session.duration_ms}ms")
    print(f"Tools   : {', '.join(session.tools_used) or '(none)'}")
    print(f"Plan    : {session.has_plan}")
    print()
    print("=== Summary Log ===")
    for i, entry in enumerate(session.filtered_entries, 1):
        print(f"{i:4d}  {entry.summary}")


if __name__ == "__main__":
    main()
