"""
Skillit - Logging Module
Provides centralized logging functionality for all scripts.
"""
from datetime import datetime

from conf import SCRIPT_DIR, LOG_FILE, SKILLIT_HOME

# =============================================================================
# CONFIGURATION
# =============================================================================

LOG = True  # Set to False to disable logging

first_line = True
# =============================================================================
# LOGGING
# =============================================================================

def skill_log(message: str) -> None:
    """Append log message to skill.log if LOG is enabled."""
    global first_line
    if not LOG:
        return
    if first_line:
        first_line = False
        SKILLIT_HOME.mkdir(parents=True, exist_ok=True)
        skill_log("--- New Skillit Session ---")
        skill_log("Script started folder: " + str(SCRIPT_DIR))
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
