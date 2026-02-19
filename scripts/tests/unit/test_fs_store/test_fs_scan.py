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
    """Collect the same info as FlowPad's project_collector — using fs_modified_at."""
    import time

    claude = ClaudeRootFsRecord.default()

    start = time.perf_counter()

    projects = claude.projects
    projects.sort(key=lambda p: p.fs_modified_at or "", reverse=True)

    elapsed_ms = (time.perf_counter() - start) * 1000

    for p in projects:
        mod = p.fs_modified_at.isoformat() if p.fs_modified_at else "n/a"
        print(
            f"  {p.name:<50}  sessions={p.session_count:>3}"
            f"  modified={mod}"
        )

    print(f"\n  Total projects: {len(projects)}")
    print(f"  Scan time: {elapsed_ms:.1f} ms")
