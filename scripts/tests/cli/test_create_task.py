import json
import time
import urllib.error
import urllib.request

from flowpad_discovery import read_server_info
from tests.test_utils import TestPluginProjectEnvironment, LaunchMode

TASK_CREATION_TIMEOUT = 120  # seconds
POLL_INTERVAL = 3  # seconds
EXPECTED_TASK_TITLE = "hello task"


def _get_flowpad_base_url() -> str:
    """Return the FlowPad base URL from the server port file."""
    server_info = read_server_info()
    if not server_info:
        raise RuntimeError("FlowPad server not found (no server.json port file)")
    return f"http://localhost:{server_info.port}"


def _flowpad_local_login(base_url: str) -> str:
    """Get a JWT token via local login. Returns the token string."""
    req = urllib.request.Request(
        f"{base_url}/api/v1/login/local",
        data=b"{}",
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        body = json.loads(resp.read())
    token = body.get("data", {}).get("token")
    if not token:
        raise RuntimeError(f"Local login failed, response: {body}")
    return token


def _query_tasks(base_url: str, token: str) -> list[dict]:
    """Query all tasks from FlowPad's graph API."""
    req = urllib.request.Request(
        f"{base_url}/api/v1/graph/task",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = json.loads(resp.read())
    return body.get("data", [])


def _find_task_by_title(tasks: list[dict], title: str) -> dict | None:
    """Find a task by title (case-insensitive)."""
    for task in tasks:
        if (task.get("title") or "").lower() == title.lower():
            return task
    return None


def test_create_task():
    """End-to-end: launch Claude, send flow-task XML via MCP, verify task in FlowPad DB."""
    env = TestPluginProjectEnvironment()
    env.install_plugin()
    env.loadMcp()
    task_flow_xml = """<flow-task data-type='object'> {"title":"hello task", "description":"some desc"} </flow-task>"""
    instruction = f"""
    use the skillit mcp and send the following :
{task_flow_xml}
"""
    mode = LaunchMode.INTERACTIVE
    result = env.launch_claude(instruction, mode=mode)
    if mode == LaunchMode.INTERACTIVE:
        base_url = _get_flowpad_base_url()
        token = _flowpad_local_login(base_url)

        elapsed = 0
        while elapsed < TASK_CREATION_TIMEOUT:
            try:
                tasks = _query_tasks(base_url, token)
                task = _find_task_by_title(tasks, EXPECTED_TASK_TITLE)
                if task:
                    print(f"Task found in FlowPad DB after {elapsed}s: {task.get('title')}")
                    assert task["title"] == EXPECTED_TASK_TITLE
                    return
            except urllib.error.URLError as e:
                print(f"FlowPad API error (will retry): {e}")
            time.sleep(POLL_INTERVAL)
            elapsed += POLL_INTERVAL
        raise AssertionError(
            f"Task '{EXPECTED_TASK_TITLE}' not found in FlowPad DB "
            f"within {TASK_CREATION_TIMEOUT}s"
        )
    assert result.returncode == 0
    return result.stdout
