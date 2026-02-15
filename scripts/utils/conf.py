"""Skillit - Central path configuration."""

import sys
from enum import StrEnum
from pathlib import Path


class Platform(StrEnum):
    WINDOWS = "win32"
    MACOS = "darwin"
    LINUX = "linux"

    @classmethod
    def current(cls) -> "Platform":
        """Return the Platform matching the running OS."""
        for member in cls:
            if sys.platform.startswith(member.value):
                return member
        return cls.LINUX  # fallback for other unix-likes


CURRENT_PLATFORM = Platform.current()

USER_HOME = Path.home()
FLOW_HOME = USER_HOME / ".flow"
SKILLIT_HOME = FLOW_HOME / "skillit"

SCRIPT_DIR = Path(__file__).resolve().parent.parent
PLUGIN_DIR = SCRIPT_DIR.parent

SERVER_JSON_PATH = FLOW_HOME / "server.json"
LOG_FILE = SKILLIT_HOME / "skill.log"

RECORDS_PATH = FLOW_HOME / "records"