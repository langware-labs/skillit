#!/usr/bin/env python3
"""
Flowpad Discovery Module

Discovers the running Flowpad server via port file and health check.
Provides three-state detection: running, installed-not-running, not-installed.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from config import FLOWPAD_APP_NAME


@dataclass
class FlowpadServerInfo:
    """Server connection information from port file."""

    port: int
    webhook_path: str
    health_path: str
    url: str  # Computed: http://localhost:{port}{webhook_path}


class FlowpadStatus:
    """Status constants for Flowpad discovery result."""

    RUNNING = "running"
    INSTALLED_NOT_RUNNING = "installed_not_running"
    NOT_INSTALLED = "not_installed"


@dataclass
class FlowpadDiscoveryResult:
    """Result of Flowpad discovery."""

    status: str
    server_info: Optional[FlowpadServerInfo] = None
    error: Optional[str] = None


def get_flowpad_data_dir() -> Path:
    """Get Flowpad user data directory (matches Electron app.getPath('userData')).

    Returns:
        Path to Flowpad user data directory:
        - macOS: ~/Library/Application Support/{FLOWPAD_APP_NAME}
        - Windows: %APPDATA%/{FLOWPAD_APP_NAME}
        - Linux: ~/.config/{FLOWPAD_APP_NAME}
    """
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / FLOWPAD_APP_NAME
    elif sys.platform.startswith("win"):
        return Path(os.getenv("APPDATA", "")) / FLOWPAD_APP_NAME
    else:
        return Path.home() / ".config" / FLOWPAD_APP_NAME


def read_server_info() -> Optional[FlowpadServerInfo]:
    """Read server.json and return info if valid.

    Returns:
        FlowpadServerInfo if port file exists and is valid, None otherwise.
    """
    port_file = get_flowpad_data_dir() / "server.json"
    if not port_file.exists():
        return None
    try:
        data = json.loads(port_file.read_text())
        return FlowpadServerInfo(
            port=data["port"],
            webhook_path=data["webhook_path"],
            health_path=data["health_path"],
            url=f"http://localhost:{data['port']}{data['webhook_path']}",
        )
    except (json.JSONDecodeError, KeyError, OSError):
        return None


def check_server_health(server_info: FlowpadServerInfo, timeout: float = 2.0) -> bool:
    """Check if server is running via health endpoint.

    Args:
        server_info: Server connection info from port file.
        timeout: Request timeout in seconds.

    Returns:
        True if health check succeeds (HTTP 200), False otherwise.
    """
    health_url = f"http://localhost:{server_info.port}{server_info.health_path}"
    try:
        req = urllib.request.Request(health_url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        return False


def is_flowpad_installed() -> bool:
    """Check if Flowpad app is installed.

    Returns:
        True if Flowpad appears to be installed, False otherwise.
    """
    if sys.platform == "darwin":
        paths = [
            Path("/Applications/Flowpad.app"),
            Path.home() / "Applications" / "Flowpad.app",
        ]
    elif sys.platform.startswith("win"):
        program_files = os.getenv("ProgramFiles", "C:\\Program Files")
        local_appdata = os.getenv("LOCALAPPDATA", "")
        paths = [
            Path(program_files) / "Flowpad" / "Flowpad.exe",
            Path(local_appdata) / "Programs" / "Flowpad" / "Flowpad.exe",
        ]
    else:
        # Linux
        paths = [
            Path.home() / ".local" / "share" / "applications" / "flowpad.desktop",
            Path("/usr/share/applications/flowpad.desktop"),
            Path("/usr/bin/flowpad"),
        ]
    return any(p.exists() for p in paths)


def discover_flowpad() -> FlowpadDiscoveryResult:
    """Main discovery function.

    Checks for running Flowpad server in order:
    1. Read port file
    2. If found, health check to verify server is responding
    3. If no port file, check if app is installed

    Returns:
        FlowpadDiscoveryResult with status and optional server_info.
    """
    # 1. Read port file
    server_info = read_server_info()

    if server_info:
        # 2. Check if server is actually running via health check
        if check_server_health(server_info):
            return FlowpadDiscoveryResult(
                status=FlowpadStatus.RUNNING,
                server_info=server_info,
            )
        # Port file exists but server not responding
        return FlowpadDiscoveryResult(
            status=FlowpadStatus.INSTALLED_NOT_RUNNING,
            error="Server not responding",
        )

    # 3. No port file - check if app is installed
    if is_flowpad_installed():
        return FlowpadDiscoveryResult(
            status=FlowpadStatus.INSTALLED_NOT_RUNNING,
            error="App installed but not running",
        )

    # 4. Not installed
    return FlowpadDiscoveryResult(status=FlowpadStatus.NOT_INSTALLED)


if __name__ == "__main__":
    # CLI interface for testing
    result = discover_flowpad()
    print(f"Status: {result.status}")
    if result.server_info:
        print(f"Server URL: {result.server_info.url}")
        print(f"Health URL: http://localhost:{result.server_info.port}{result.server_info.health_path}")
    if result.error:
        print(f"Error: {result.error}")
