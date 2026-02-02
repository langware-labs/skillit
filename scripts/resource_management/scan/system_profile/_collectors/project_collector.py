"""Project collector - projects enumeration."""

import json
import sys
from pathlib import Path

# Add parent directory to path for standalone execution
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import (
    CLAUDE_HOME,
    load_jsonl,
    shorten_path,
)


def get_project_cwd(project_dir: Path) -> str | None:
    """Extract real cwd from project session files."""
    for jsonl_file in project_dir.glob("*.jsonl"):
        try:
            with open(jsonl_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if cwd := entry.get("cwd"):
                            return cwd
                    except json.JSONDecodeError:
                        continue
        except IOError:
            continue
    return None


def get_projects() -> list[dict]:
    """Get all projects."""
    projects = []
    projects_dir = CLAUDE_HOME / "projects"

    if not projects_dir.exists():
        return projects

    for project_dir in projects_dir.iterdir():
        if not project_dir.is_dir():
            continue

        cwd = get_project_cwd(project_dir) or project_dir.name
        session_files = list(project_dir.glob("*.jsonl"))
        session_count = len(session_files)

        latest_activity = None
        total_messages = 0

        for sf in session_files:
            entries = load_jsonl(sf, limit=5)
            for entry in entries:
                if ts := entry.get("timestamp"):
                    if not latest_activity or ts > latest_activity:
                        latest_activity = ts
                    break

        projects.append(
            {
                "id": f"project:{project_dir.name}",
                "type": "project",
                "name": shorten_path(cwd),
                "scope": "user",
                "source_file": str(project_dir),
                "path": str(project_dir),
                "modified_at": latest_activity,
                "encoded_name": project_dir.name,
                "cwd": cwd,
                "session_count": session_count,
                "total_messages": total_messages,
            }
        )

    projects.sort(key=lambda x: x["modified_at"] or "", reverse=True)
    return projects
