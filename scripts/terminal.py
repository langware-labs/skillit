"""Cross-platform terminal launcher."""

import subprocess
import sys
from pathlib import Path


def open_terminal(cwd: str | Path, command: str | None = None) -> None:
    """Open a visible terminal window at the given directory.

    Args:
        cwd: Directory to open the terminal in.
        command: Optional command to run in the new terminal.
    """
    cwd = str(cwd)

    if sys.platform == "darwin":
        if command:
            script = (
                'tell application "Terminal"\n'
                f'    do script "cd {cwd} && {command}"\n'
                '    activate\n'
                'end tell'
            )
            subprocess.run(["osascript", "-e", script])
        else:
            script = (
                'tell application "Terminal"\n'
                f'    do script "cd {cwd}"\n'
                '    activate\n'
                'end tell'
            )
            subprocess.run(["osascript", "-e", script])
    elif sys.platform == "win32":
        if command:
            subprocess.Popen(["cmd", "/c", "start", "cmd", "/K", f"cd /d {cwd} && {command}"])
        else:
            subprocess.Popen(["cmd", "/c", "start", "cmd", "/K", f"cd /d {cwd}"])
    else:
        # Linux - try common terminal emulators
        shell_cmd = f"cd {cwd} && {command}; exec $SHELL" if command else f"cd {cwd} && $SHELL"
        for term in ["gnome-terminal", "konsole", "xfce4-terminal", "xterm"]:
            try:
                if term == "gnome-terminal":
                    if command:
                        subprocess.Popen([term, "--working-directory", cwd, "--", "bash", "-c", shell_cmd])
                    else:
                        subprocess.Popen([term, "--working-directory", cwd])
                elif term == "konsole":
                    if command:
                        subprocess.Popen([term, "--workdir", cwd, "-e", "bash", "-c", shell_cmd])
                    else:
                        subprocess.Popen([term, "--workdir", cwd])
                else:
                    subprocess.Popen([term, "-e", f"cd {cwd} && $SHELL"])
                return
            except FileNotFoundError:
                continue
        raise RuntimeError("No supported terminal emulator found")
