"""Skillit - Central path configuration."""

from pathlib import Path

USER_HOME = Path.home()
FLOW_HOME = USER_HOME / ".flow"
SKILLIT_HOME = FLOW_HOME / "skillit"

SCRIPT_DIR = Path(__file__).parent.resolve()
PLUGIN_DIR = SCRIPT_DIR.parent

LOG_FILE = SKILLIT_HOME / "skill.log"
