"""
Skillit - Logging Module
Provides centralized logging functionality for all scripts.
"""
from datetime import datetime
from pathlib import Path

# =============================================================================
# CONFIGURATION
# =============================================================================

LOG = True  # Set to False to disable logging

SCRIPT_DIR = Path(__file__).parent.resolve()
PLUGIN_DIR = SCRIPT_DIR.parent
LOG_FILE = PLUGIN_DIR / "skill.log"

# =============================================================================
# LOGGING
# =============================================================================

def skill_log(message: str) -> None:
    """Append log message to skill.log if LOG is enabled."""
    if not LOG:
        return
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
