#!/usr/bin/env python3
"""
Flowpad Discovery Module

Discovers the running Flowpad server via port file and health check.
Provides three-state detection: running, installed-not-running, not-installed.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from config import FLOWPAD_APP_NAME

# Rate limiting constants
MAX_FAILURES_PER_HOUR = 3
HOUR_IN_SECONDS = 3600


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


class _ServerState:
    """Cached server state with rate-limited failure tracking."""

    def __init__(self):
        self._discovery_result: Optional[FlowpadDiscoveryResult] = None
        self._port_file_mtime: Optional[float] = None
        self._failure_timestamps: list[float] = []

    def _get_port_file_mtime(self) -> Optional[float]:
        """Get modification time of port file, or None if not exists."""
        try:
            return get_port_file_path().stat().st_mtime
        except OSError:
            return None

    def _is_cache_valid(self) -> bool:
        """Check if cached result is still valid."""
        if self._discovery_result is None:
            return False
        # Invalidate if port file changed
        current_mtime = self._get_port_file_mtime()
        if current_mtime != self._port_file_mtime:
            return False
        # Invalidate if rate-limited (re-check if server came back)
        if self.is_rate_limited():
            return False
        return True

    def get_discovery_result(self) -> FlowpadDiscoveryResult:
        """Get discovery result, re-discovering if cache is invalid."""
        if not self._is_cache_valid():
            self._discovery_result = _discover_flowpad_impl()
            self._port_file_mtime = self._get_port_file_mtime()
            # Clear failures on successful re-discovery if server is running
            if self._discovery_result.status == FlowpadStatus.RUNNING:
                self._failure_timestamps = []
        return self._discovery_result

    def record_webhook_failure(self) -> None:
        """Record a webhook failure timestamp."""
        now = time.time()
        self._failure_timestamps.append(now)
        # Keep only failures from the last hour
        cutoff = now - HOUR_IN_SECONDS
        self._failure_timestamps = [t for t in self._failure_timestamps if t > cutoff]

    def is_rate_limited(self) -> bool:
        """Check if we've exceeded failure limit (3 failures in the last hour).

        Clears failures if port file changed (server may have restarted).
        """
        # If port file changed, clear failures - server may have restarted
        current_mtime = self._get_port_file_mtime()
        if current_mtime != self._port_file_mtime:
            self._failure_timestamps = []
            return False

        now = time.time()
        cutoff = now - HOUR_IN_SECONDS
        recent_failures = [t for t in self._failure_timestamps if t > cutoff]
        return len(recent_failures) >= MAX_FAILURES_PER_HOUR


# Global cached state
_server_state = _ServerState()


def get_port_file_path() -> Path:
    """Get path to server.json port file."""
    return get_flowpad_data_dir() / "server.json"


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
    port_file = get_port_file_path()
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


def _discover_flowpad_impl() -> FlowpadDiscoveryResult:
    """Internal discovery implementation with health check.

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


def discover_flowpad() -> FlowpadDiscoveryResult:
    """Get cached Flowpad discovery result.

    Health check is performed once on first call (startup).
    Subsequent calls return the cached result.

    Returns:
        Cached FlowpadDiscoveryResult.
    """
    return _server_state.get_discovery_result()


def record_webhook_failure() -> None:
    """Record a webhook failure for rate limiting."""
    _server_state.record_webhook_failure()


def is_webhook_rate_limited() -> bool:
    """Check if webhooks are rate-limited due to repeated failures.

    Returns:
        True if 3+ failures occurred in the last hour.
    """
    return _server_state.is_rate_limited()


if __name__ == "__main__":
    # CLI interface for testing
    result = discover_flowpad()
    print(f"Status: {result.status}")
    if result.server_info:
        print(f"Server URL: {result.server_info.url}")
        print(f"Health URL: http://localhost:{result.server_info.port}{result.server_info.health_path}")
    if result.error:
        print(f"Error: {result.error}")
