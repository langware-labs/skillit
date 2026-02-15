from tests.test_utils import TestPluginProjectEnvironment, LaunchMode
from utils.log import skill_log_print, skill_log_clear

EXPECTED_TASK_TITLE = "hello task"


def test_create_task():
    """End-to-end: launch Claude headless, send flow-task XML via MCP, verify in skill log."""
    env = TestPluginProjectEnvironment()
    env.install_plugin()
    env.loadMcp()
    skill_log_clear()

    task_flow_xml = """<flow-task data-type='object'> {"title":"hello task", "description":"some desc"} </flow-task>"""
    instruction = (
        f"use the skillit mcp flow_tag tool and send the following xml exactly as-is:\n"
        f"{task_flow_xml}"
    )
    result = env.launch_claude(instruction, mode=LaunchMode.HEADLESS)
    assert result.returncode == 0

    # Verify MCP flow_tag was called with the task data
    skill_log = result.skill_log
    skill_log_print()
    assert "flow_tag" in skill_log, f"flow_tag not found in skill log: {skill_log}"
    assert "hello task" in skill_log, f"task title not found in skill log: {skill_log}"
