"""Session collector - sessions with token tracking."""

import json
import sys
from pathlib import Path

# Add parent directory to path for standalone execution
sys.path.insert(0, str(Path(__file__).parent.parent))

from _collectors.project_collector import (
    get_project_cwd,
)
from utils import (
    CLAUDE_HOME,
    calculate_session_cost,
)


def get_session_info_quick(jsonl_path: Path, project_encoded_name: str | None = None) -> dict | None:
    """Get basic info about a session using file metadata only (FAST).

    This reads only the first few lines to get timestamps and slug,
    avoiding full file parsing.
    """
    if not jsonl_path.exists():
        return None

    session_id = jsonl_path.stem
    stat = jsonl_path.stat()
    size_bytes = stat.st_size
    modified_at = None

    # Read first few lines for created_at timestamp and slug
    first_timestamp = None
    slug = None
    try:
        with open(jsonl_path, "r", encoding="utf-8") as f:
            # Read up to 10 lines to find slug (it appears early in transcript)
            for _ in range(10):
                line = f.readline()
                if not line:
                    break
                try:
                    entry = json.loads(line)
                    if not first_timestamp:
                        first_timestamp = entry.get("timestamp")
                    if not slug and "slug" in entry:
                        slug = entry.get("slug")
                    # Stop if we found both
                    if first_timestamp and slug:
                        break
                except json.JSONDecodeError:
                    continue
    except IOError:
        pass

    # Use file mtime as modified_at (faster than reading last line)
    from datetime import datetime

    modified_at = datetime.fromtimestamp(stat.st_mtime).isoformat()

    # Check if plan file exists for this slug
    plan_path = None
    if slug:
        potential_plan = CLAUDE_HOME / "plans" / f"{slug}.md"
        if potential_plan.exists():
            plan_path = str(potential_plan)

    return {
        "id": f"{project_encoded_name}/{session_id}" if project_encoded_name else session_id,
        "type": "session",
        "name": session_id,
        "scope": "user",
        "source_file": str(jsonl_path),
        "path": str(jsonl_path),
        "modified_at": modified_at,
        "created_at": first_timestamp,
        "project_id": f"project:{project_encoded_name}" if project_encoded_name else None,
        "project_encoded_name": project_encoded_name,
        "size_bytes": size_bytes,
        "slug": slug,
        "plan_path": plan_path,
        # These fields are not available in quick mode
        "message_count": None,
        "user_messages": None,
        "assistant_messages": None,
        "tool_uses": None,
        "input_tokens": None,
        "output_tokens": None,
        "estimated_cost_usd": None,
        "models_used": None,
        "primary_model": None,
    }


def get_session_info(jsonl_path: Path, project_encoded_name: str | None = None) -> dict | None:
    """Get info about a single session including token usage and cost (SLOW - parses full file)."""
    if not jsonl_path.exists():
        return None

    session_id = jsonl_path.stem
    first_timestamp = None
    last_timestamp = None
    message_count = 0
    user_messages = 0
    assistant_messages = 0
    tool_uses = 0
    git_branch = None
    version = None
    slug = None

    input_tokens = 0
    output_tokens = 0
    cache_read_tokens = 0
    cache_creation_tokens = 0
    models_used = {}

    try:
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)

                    if ts := entry.get("timestamp"):
                        if not first_timestamp:
                            first_timestamp = ts
                        last_timestamp = ts

                    # Extract slug (plan name) - appears early and stays constant
                    if not slug and "slug" in entry:
                        slug = entry.get("slug")

                    entry_type = entry.get("type")
                    if entry_type == "user":
                        user_messages += 1
                        message_count += 1
                    elif entry_type == "assistant":
                        assistant_messages += 1
                        message_count += 1

                        msg = entry.get("message", {})

                        content = msg.get("content", [])
                        if isinstance(content, list):
                            tool_uses += sum(1 for c in content if isinstance(c, dict) and c.get("type") == "tool_use")

                        usage = msg.get("usage", {})
                        input_tokens += usage.get("input_tokens", 0)
                        output_tokens += usage.get("output_tokens", 0)
                        cache_read_tokens += usage.get("cache_read_input_tokens", 0)
                        cache_creation_tokens += usage.get("cache_creation_input_tokens", 0)

                        model = msg.get("model")
                        if model:
                            models_used[model] = models_used.get(model, 0) + 1

                    if not git_branch:
                        git_branch = entry.get("gitBranch")
                    if not version:
                        version = entry.get("version")

                except json.JSONDecodeError:
                    continue

    except IOError:
        return None

    primary_model = None
    if models_used:
        primary_model = max(models_used.items(), key=lambda x: x[1])[0]

    cost_info = calculate_session_cost(
        input_tokens,
        output_tokens,
        cache_read_tokens,
        cache_creation_tokens,
        primary_model,
    )

    # Check if plan file exists for this slug
    plan_path = None
    if slug:
        potential_plan = CLAUDE_HOME / "plans" / f"{slug}.md"
        if potential_plan.exists():
            plan_path = str(potential_plan)

    return {
        "id": f"{project_encoded_name}/{session_id}" if project_encoded_name else session_id,
        "type": "session",
        "name": session_id,
        "scope": "user",
        "source_file": str(jsonl_path),
        "path": str(jsonl_path),
        "modified_at": last_timestamp,
        "created_at": first_timestamp,
        "project_id": f"project:{project_encoded_name}" if project_encoded_name else None,
        "project_encoded_name": project_encoded_name,
        "message_count": message_count,
        "user_messages": user_messages,
        "assistant_messages": assistant_messages,
        "tool_uses": tool_uses,
        "git_branch": git_branch,
        "version": version,
        "slug": slug,
        "plan_path": plan_path,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_read_tokens": cache_read_tokens,
        "cache_creation_tokens": cache_creation_tokens,
        "estimated_cost_usd": cost_info["total"],
        "models_used": list(models_used.keys()),
        "primary_model": primary_model,
    }


def get_recent_sessions(limit: int = 10, per_project_limit: int = 0) -> list[dict]:
    """Get recent sessions across all projects.

    Args:
        limit: Maximum total sessions to return (0 = unlimited)
        per_project_limit: Max sessions per project (0 = unlimited, default)
    """
    recent = []
    projects_dir = CLAUDE_HOME / "projects"

    if not projects_dir.exists():
        return recent

    for project_dir in projects_dir.iterdir():
        if not project_dir.is_dir():
            continue

        project_encoded_name = project_dir.name
        cwd = get_project_cwd(project_dir) or project_dir.name

        session_files = sorted(
            project_dir.glob("*.jsonl"),
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )
        if per_project_limit > 0:
            session_files = session_files[:per_project_limit]

        for sf in session_files:
            session = get_session_info(sf, project_encoded_name)
            if session:
                session["cwd"] = cwd
                recent.append(session)

    recent.sort(key=lambda x: x["modified_at"] or "", reverse=True)
    if limit > 0:
        return recent[:limit]
    return recent
