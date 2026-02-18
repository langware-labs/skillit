from records.claude import ClaudeRootFsRecord


def test_full_scan():
    claude = ClaudeRootFsRecord.default()
    projects = claude.projects
    for project in projects:
        print(f"Project: {project.name}")
        for session in project.sessions:
            print(f"  Session: {session.name}")
            for entry in session.entries:
                print(f"    Entry: {entry.name}")


def test_history_scan():
    claude = ClaudeRootFsRecord.default()
    history = claude.history
    entries = history.entries
    assert len(entries) > 0
    for entry in entries:
        print(f"  {entry.time_ago:>8}  {entry.display}")


def test_project_scan():
    """Collect the same info as FlowPad's project_collector.get_projects()."""
    import json
    import time
    from pathlib import Path

    HOME = str(Path.home())

    def shorten_path(path: str) -> str:
        return ("~" + path[len(HOME):]) if path.startswith(HOME) else path

    def get_cwd_from_file(jsonl_file: Path, max_lines: int = 20) -> str | None:
        try:
            with open(jsonl_file, encoding="utf-8") as f:
                for _ in range(max_lines):
                    line = f.readline()
                    if not line:
                        break
                    try:
                        entry = json.loads(line)
                        if cwd := entry.get("cwd"):
                            return cwd
                    except json.JSONDecodeError:
                        continue
        except IOError:
            return None
        return None

    def get_project_cwd(project_dir: Path) -> str | None:
        session_files = sorted(
            project_dir.glob("*.jsonl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for f in session_files[:3]:
            if cwd := get_cwd_from_file(f):
                return cwd
        for f in session_files[3:]:
            if cwd := get_cwd_from_file(f, max_lines=50):
                return cwd
        return None

    claude = ClaudeRootFsRecord.default()
    projects_dir = Path(claude.projects_dir)

    start = time.perf_counter()

    projects = []
    for project_dir in projects_dir.iterdir():
        if not project_dir.is_dir():
            continue

        cwd = get_project_cwd(project_dir) or project_dir.name
        session_files = list(project_dir.glob("*.jsonl"))
        session_count = len(session_files)

        latest_activity = None
        for sf in session_files:
            try:
                with open(sf, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            entry = json.loads(line)
                            if ts := entry.get("timestamp"):
                                if not latest_activity or ts > latest_activity:
                                    latest_activity = ts
                                break
                        except json.JSONDecodeError:
                            continue
            except IOError:
                continue

        projects.append({
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
            "total_messages": 0,
        })

    projects.sort(key=lambda x: x["modified_at"] or "", reverse=True)

    elapsed_ms = (time.perf_counter() - start) * 1000

    for p in projects:
        print(
            f"  {p['name']:<50}  sessions={p['session_count']:>3}"
            f"  modified={p['modified_at'] or 'n/a'}"
        )

    print(f"\n  Total projects: {len(projects)}")
    print(f"  Scan time: {elapsed_ms:.1f} ms")
