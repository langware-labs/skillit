"""Flowpad ad display — shown when Flowpad is not running."""

from flow_sdk.discovery import FlowpadStatus
from flow_sdk.discovery.notify import get_flowpad_status
from utils.config import FLOWPAD_APP_URI_SCHEME

# Flowpad ad text (shown when not installed)
FLOWPAD_INSTALL_AD = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   📱  Try Flowpad - Your AI Workflow Companion                   ║
║                                                                  ║
║   Build, automate, and streamline your workflows with AI.        ║
║   Download now at: https://flowpad.ai                            ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""

# Flowpad launch prompt (shown when installed but not running)
# Uses OSC 8 hyperlink escape sequence for clickable terminal link
FLOWPAD_LAUNCH_PROMPT = f"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   📱  Flowpad is installed but not running                       ║
║                                                                  ║
║   Launch \x1b]8;;{FLOWPAD_APP_URI_SCHEME}://\x1b\\Flowpad\x1b]8;;\x1b\\                                                  ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""


def get_ad_if_needed() -> str:
    """Return appropriate message based on Flowpad status.

    Returns:
        - Empty string if Flowpad is running
        - Launch prompt if installed but not running
        - Install ad if not installed
    """
    status = get_flowpad_status()

    if status == FlowpadStatus.RUNNING:
        return ""

    if status == FlowpadStatus.INSTALLED_NOT_RUNNING:
        return FLOWPAD_LAUNCH_PROMPT

    return FLOWPAD_INSTALL_AD
