"""Compare legacy vs new system profile scan numeric fields."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

_here = Path(__file__).resolve()
for parent in [_here.parent, *_here.parents]:
    if (parent / "flowpad").exists():
        sys.path.insert(0, str(parent))
        break

from flowpad.hub.core.resource_management.scan import system_profile as legacy  # noqa: E402
from flowpad.hub.core.resource_management.scan import system_profile as new_scan  # noqa: E402


def _is_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    return isinstance(value, (int, float))


def _compare_all(a: Any, b: Any, path: str, mismatches: list[str]) -> None:
    if _is_number(a) or _is_number(b):
        if not (_is_number(a) and _is_number(b) and a == b):
            mismatches.append(f"{path}: {a!r} != {b!r}")
        return

    if isinstance(a, dict) and isinstance(b, dict):
        keys = sorted(set(a.keys()) | set(b.keys()))
        for key in keys:
            _compare_all(a.get(key), b.get(key), f"{path}.{key}", mismatches)
        return

    if isinstance(a, list) and isinstance(b, list):
        max_len = max(len(a), len(b))
        for idx in range(max_len):
            _compare_all(
                a[idx] if idx < len(a) else None,
                b[idx] if idx < len(b) else None,
                f"{path}[{idx}]",
                mismatches,
            )
        return

    if a != b:
        mismatches.append(f"{path}: {a!r} != {b!r}")


def _patch_scanner_with_cache(
    cache: dict[str, Any],
    ide_connections: list,
    legacy_settings: dict | None,
    fixed_generated: str,
) -> None:
    legacy.get_installed_plugins = lambda: cache["plugins"]
    legacy.get_known_marketplaces = lambda: cache["marketplaces"]
    legacy.get_account_info = lambda: cache["account"]
    legacy.get_github_repos = lambda: cache["githubRepos"]
    legacy.get_claude_md_files = lambda: cache["claudeMdFiles"]
    legacy.get_directories = lambda: cache["directories"]
    legacy.get_plans = lambda: cache["plans"]
    legacy.get_todos = lambda: cache["todos"]

    legacy.get_all_hooks = lambda: cache["hooks"]
    legacy.get_mcp_servers = lambda: cache["mcpServers"]
    legacy.get_commands = lambda: cache["commands"]
    legacy.get_agents = lambda: cache["agents"]
    legacy.get_skills = lambda: cache["skills"]

    legacy.get_projects = lambda: cache["projects"]
    legacy.get_recent_sessions = lambda limit=0, per_project_limit=0: cache["sessions"]
    legacy.get_ide_connections = lambda: ide_connections

    legacy.get_cost_overview = lambda sessions: cache["costOverview"]
    legacy.get_recent_items = lambda sessions, projects, plans, todos: cache["recentItems"]
    legacy.get_legacy_settings = lambda: legacy_settings

    class _FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            fixed = datetime.fromisoformat(fixed_generated)
            if tz is not None and fixed.tzinfo is None:
                return fixed.replace(tzinfo=tz)
            return fixed

    legacy.datetime = _FixedDateTime


def compare_scans(session_limit: int, mode: str, deterministic: bool) -> list[str]:
    legacy_settings = legacy.get_legacy_settings()
    ide_connections = legacy.get_ide_connections()

    legacy_result = legacy.scan_full(session_limit=session_limit, mode=mode)

    if deterministic:
        _patch_scanner_with_cache(
            legacy_result,
            ide_connections,
            legacy_settings,
            legacy_result.get("generated", datetime.now().isoformat()),
        )

    new_result = new_scan.scan_full(session_limit=session_limit, mode=mode)

    mismatches: list[str] = []
    _compare_all(legacy_result, new_result, "root", mismatches)
    return mismatches


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare numeric fields in system profile scans.")
    parser.add_argument("--session-limit", type=int, default=100)
    parser.add_argument("--mode", type=str, default="quick")
    parser.add_argument("--deterministic", action="store_true", default=True)
    parser.add_argument("--no-deterministic", dest="deterministic", action="store_false")
    args = parser.parse_args()

    mismatches = compare_scans(args.session_limit, args.mode, args.deterministic)
    if mismatches:
        print("Numeric mismatches detected:")  # noqa: T201
        for line in mismatches:
            print(line)  # noqa: T201
        return 1

    print("OK: scans match for all fields.")  # noqa: T201
    return 0


if __name__ == "__main__":
    sys.exit(main())
