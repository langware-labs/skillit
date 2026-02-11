from tests.test_utils import TestPluginProjectEnvironment, LaunchMode


def test_create_task():
    """End-to-end: analyze transcript, classify issues, create rule."""
    env = TestPluginProjectEnvironment()
    task_flow_xml = """<flow-task data-type='object'> {"title":"hello task", "description":"some desc""} </flow-task>"""
    instruction = f"""
    use the skillit mcp and send the following :
{task_flow_xml}
"""
    mode = LaunchMode.INTERACTIVE
    result = env.launch_claude(instruction, mode=mode)
    if mode == LaunchMode.INTERACTIVE:
        return None
    assert result.returncode == 0
    return result.stdout
    print("=== Rule Creation ===")
    print(rule_output)

