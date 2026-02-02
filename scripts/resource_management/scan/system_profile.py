"""System profile scan entry point (bundled scanner)."""

from __future__ import annotations

import sys
from pathlib import Path

_script_dir = Path(__file__).parent
sys.path.insert(0, str(_script_dir / "system_profile"))

from scanner import (  # noqa: E402
    get_resource_summary,
    list_projects_fast,
    scan_full,
    scan_item,
    scan_project,
    scan_resources,
)

__all__ = [
    "scan_full",
    "scan_item",
    "scan_resources",
    "scan_project",
    "list_projects_fast",
    "get_resource_summary",
]
