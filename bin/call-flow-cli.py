#!/usr/bin/env python3
"""Hook forwarder: calls `flow report hooks` if the flow CLI is available, otherwise exits silently."""
import shutil
import subprocess
import sys

if __name__ == "__main__":
    exe = shutil.which("flow")
    if exe:
        raise SystemExit(subprocess.call([exe] + sys.argv[1:]))
