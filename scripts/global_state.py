"""
Skillit - Global State
Provides global state storage using JSON key-value store.
"""
import json
import time
from pathlib import Path

from json_key_val import JsonKeyVal

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR = Path(__file__).parent.resolve()
PLUGIN_DIR = SCRIPT_DIR.parent
STATE_FILE = PLUGIN_DIR / "global_state.json"
PLUGIN_JSON = PLUGIN_DIR / ".claude-plugin" / "plugin.json"

COOLDOWN_SECONDS = 5  # Minimum seconds between invocations to prevent recursion

# =============================================================================
# PLUGIN CONFIG
# =============================================================================

def _load_plugin_config() -> dict:
    """Load and return the plugin.json as a dict."""
    try:
        with open(PLUGIN_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


plugin_config = _load_plugin_config()

# =============================================================================
# GLOBAL STATE INSTANCE
# =============================================================================

global_state = JsonKeyVal(STATE_FILE)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def is_within_cooldown() -> bool:
    """Check if we're within the cooldown period to prevent recursive activation."""
    last_invocation = global_state.get("last_invocation_time", 0)
    elapsed = time.time() - last_invocation
    return elapsed < COOLDOWN_SECONDS


def update_invocation_time() -> None:
    """Update the last invocation timestamp."""
    global_state.set("last_invocation_time", time.time())
