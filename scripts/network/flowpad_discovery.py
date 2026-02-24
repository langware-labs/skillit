"""Re-export Flowpad discovery from flow_sdk.

All logic lives in flow_sdk.discovery; this module provides backward
compatibility so existing ``from network.flowpad_discovery import …``
imports continue to work.
"""

from flow_sdk.discovery import (
    HOUR_IN_SECONDS,
    MAX_FAILURES_PER_HOUR,
    FlowpadDiscoveryResult,
    FlowpadServerInfo,
    FlowpadStatus,
    check_server_health,
    discover_flowpad,
    get_port_file_path,
    is_flowpad_installed,
    is_webhook_rate_limited,
    read_server_info,
    record_webhook_failure,
)
from flow_sdk.discovery.flowpad_discovery import _ServerState  # for tests

__all__ = [
    "HOUR_IN_SECONDS",
    "MAX_FAILURES_PER_HOUR",
    "FlowpadDiscoveryResult",
    "FlowpadServerInfo",
    "FlowpadStatus",
    "_ServerState",
    "check_server_health",
    "discover_flowpad",
    "get_port_file_path",
    "is_flowpad_installed",
    "is_webhook_rate_limited",
    "read_server_info",
    "record_webhook_failure",
]
