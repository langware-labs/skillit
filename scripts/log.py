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
LOG_TO_STDERR = True  # Use stderr so logs don't pollute hook stdout
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
    log_line = f"[{timestamp}] {message}\n"
    if LOG_TO_STDERR:
        import sys
        sys.stderr.write(log_line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line)


def skill_log_print() -> None:
    """Print the contents of the log file to stdout."""
    if LOG_FILE.exists():
        log_contents = LOG_FILE.read_text(encoding="utf-8")
        if log_contents:
            print(log_contents, end="")
        else:
            print("[Skillit Log is empty]")
    else:
        print("[Skillit Log file does not exist]")


def skill_log_clear() -> None:
    """Delete the log file."""
    if LOG_FILE.exists():
        LOG_FILE.unlink()
