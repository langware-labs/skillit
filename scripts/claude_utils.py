"""
Utility functions for invoking Claude Code from Python scripts.
"""
import subprocess
import platform
import shlex


def invoke_claude(prompt: str, working_dir: str = None) -> None:
    """
    Open a persistent terminal window and run Claude Code with the given prompt.
    """
    system = platform.system()
    escaped_prompt = shlex.quote(prompt)

    # Build command with optional directory change
    if working_dir:
        cmd = f"cd {shlex.quote(working_dir)} && clear && claude {escaped_prompt}"
    else:
        cmd = f"clear && claude {escaped_prompt}"

    if system == "Darwin":  # macOS
        script = f'''
        tell application "Terminal"
            activate
            do script "{cmd}"
        end tell
        '''
        subprocess.Popen(
            ["osascript", "-e", script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

    elif system == "Linux":
        terminals = [
            ["gnome-terminal", "--", "bash", "-c", f"{cmd}; exec bash"],
            ["xterm", "-e", f"bash -c '{cmd}; exec bash'"],
            ["konsole", "-e", "bash", "-c", f"{cmd}; exec bash"],
        ]
        for term_cmd in terminals:
            try:
                subprocess.Popen(
                    term_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                break
            except FileNotFoundError:
                continue

    elif system == "Windows":
        subprocess.Popen(
            ["cmd", "/k", cmd.replace("clear", "cls")],
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            start_new_session=True
        )
