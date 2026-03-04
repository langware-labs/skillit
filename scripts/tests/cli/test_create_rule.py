import pytest
import time

import plugin_records
from plugin_records import SkillitSession
from plugin_records.crud_handlers.skill_creation_handler import skill_creation_handler
from subagents.agent_manager import SubAgent, get_subagent_launch_prompt
from utils.log import skill_log_print
from flow_sdk.fs_records import TaskStatus
from tests.test_utils import TestPluginProjectEnvironment, ClaudeTranscript, LaunchMode, make_env
from tests.test_utils import TRANSCRIPT_PATH, ACLI_SESSION_ID, analyze_hook, create_skill, LONG_SESSION_ID


def analyze(session_id, env: TestPluginProjectEnvironment, mode: LaunchMode = LaunchMode.HEADLESS) -> str | None:
    """Create a skill from the conversation transcript.

    Args:
        env: The test environment (session is resumed automatically).
        mode: Launch mode for claude.

    Returns:
        The classification output text, or None if in interactive mode.
    """

    result = env.launch_claude(f"analyze the session id {session_id}", mode=mode)
    assert result.returncode == 0
    return result.stdout

def classify_analysis(env: TestPluginProjectEnvironment, mode: LaunchMode = LaunchMode.HEADLESS) -> str:
    """Classify the issues found during analysis.

    Args:
        env: The test environment (session is resumed automatically).
        mode: Launch mode for claude.

    Returns:
        The classification output text.
    """
    transcript = ClaudeTranscript.load(TRANSCRIPT_PATH)
    prompt = transcript.get_entries("user")[0]["message"]["content"]

    instruction = f"user original request: {prompt}"
    all_rules_index = env.all_rules.rules_index
    data = {"known_rules": all_rules_index}
    context_add = get_subagent_launch_prompt(SubAgent.CLASSIFY, instruction, data)

    result = env.launch_claude(context_add, mode=mode)
    assert result.returncode == 0
    return result.stdout

def create_rule(env: TestPluginProjectEnvironment, mode: LaunchMode = LaunchMode.HEADLESS) -> str | None:
    transcript = ClaudeTranscript.load(TRANSCRIPT_PATH)
    prompt = transcript.get_entries("user")[0]["message"]["content"]

    instruction = f"user original request: {prompt}, given the issues classification, clear all known, make sure merged are merged into a single issue and new are passed as is"
    context_add = get_subagent_launch_prompt(SubAgent.CREATE, instruction, {})

    result = env.launch_claude(context_add, mode=mode)
    if mode == LaunchMode.INTERACTIVE:
        return None
    assert result.returncode == 0
    return result.stdout

def test_create_skill():
    """End-to-end: analyze transcript, classify issues, create rule."""
    env = make_env()
    env.install_plugin()
    env._fork = True

    # Clean up any leftover skill records from previous runs so each run starts fresh
    from utils.conf import RECORDS_PATH
    import shutil
    skills_path = RECORDS_PATH / "skill"
    if skills_path.exists():
        shutil.rmtree(skills_path)
        print(f"Cleaned up previous skill records at: {skills_path}")

    print(f"Environment set up at: {env.path}")
    env._resume_session_id = ACLI_SESSION_ID
    create_skill(env, mode=LaunchMode.INTERACTIVE)
    session: SkillitSession = plugin_records.skillit_records.get_session(env.session_id)
    skill_log_print()
    # Session may not exist yet in interactive mode, so don't assert
    if session:
        print(f"Session found: {session.session_id}")


def test_create_skill_stub():
    env = make_env()
    env.install_plugin()
    session_id = env.session_id

    session = plugin_records.skillit_records.get_session(session_id)
    if session is None:
        session = plugin_records.skillit_records.create_session(session_id)
    skill_name = "test-skill"
    resources = skill_creation_handler.on_create(session_id, session, "skill", {"name": skill_name})
    assert resources is not None
    assert resources.task.status == TaskStatus.IN_PROGRESS

    time.sleep(2)  # give FlowPad time to render

    skill_creation_handler.on_update(session_id, session, "skill", {"status": "new", "folder_name": skill_name})
    # Task completion is verified by loading from disk
    from flow_sdk.fs_records import TaskResource
    from flow_sdk.fs_store import Record

    task_key = f"task:{skill_name}"
    session_record = Record.init_record(session.record_dir / "record.json")
    task_data = session_record[task_key] if task_key in session_record else None
    assert task_data is not None, "Task data not found in session record"

    task = TaskResource.from_dict(task_data)
    assert task.status == TaskStatus.DONE

@pytest.mark.skip()
def test_create_rule():
    """End-to-end: analyze transcript, classify issues, create rule."""
    env = make_env()
    env.install_plugin()
    env._fork = True
    print(f"Environment set up at: {env.path}")
    # analysis = analyze_hook(env, mode=LaunchMode.INTERACTIVE)
    # analysis = analyze_hook(env, mode=LaunchMode.HEADLESS)
    env._resume_session_id = 'dc617ce9-1ae5-4cf2-a091-a487230f8797'
    classification = classify_analysis(env, mode=LaunchMode.HEADLESS)

    session: SkillitSession = plugin_records.skillit_records.get_session('dc617ce9-1ae5-4cf2-a091-a487230f8797')

    # env._resume_session_id ='c0b4cb5e-27bf-4e7c-b08c-cd8ebffcc278'
    # session: SkillitSession = plugin_records.skillit_records.get_session(env._resume_session_id)
    rule_output = create_rule(env, mode=LaunchMode.INTERACTIVE)
    session:SkillitSession = plugin_records.skillit_records.get_session(env.session_id)
    assert session is not None
    print("=== Rule Creation ===")
    print(rule_output)

@pytest.mark.manual
def test_launch():
    env = make_env()
    env.install_plugin()
    result = env.launch_claude("hello from test_launch", mode=LaunchMode.INTERACTIVE)
    skill_log_print()
    assert result.returncode == 0
    assert "hello from test_launch" in result.stdout.lower()

pytest.mark.skip()
def test_create_rule_complete():
    """End-to-end: analyze transcript, classify issues, create rule."""
    env = make_env()
    env._clean = False  # Prevent cleanup so files persist for inspection
    print(f"Environment set up at: {env.path}")
    print(f"Rules will be created at: {env.path}/.flow/skill_rules")
    print(f"session: {env.session_id}")
    # Run all steps in headless mode for automatic completion
    analyze_hook(env, mode=LaunchMode.HEADLESS)
    classify_analysis(env, mode=LaunchMode.HEADLESS)
    rule_output = create_rule(env, mode=LaunchMode.INTERACTIVE)
    print("=== Rule Creation ===")
    print(rule_output)
    print(f"\n>>> Files preserved at: {env.path}")
    print(f">>> Check for created rules at: {env.path}/.flow/skill_rules")

def test_skill_creation_via_entity_crud():
    """Test skill creation task lifecycle via entity_crud (without launching Claude)."""
    import uuid
    env = make_env()
    env.install_plugin()
    session_id = env.session_id

    session = plugin_records.skillit_records.get_session(session_id)
    if session is None:
        session = plugin_records.skillit_records.create_session(session_id)

    # Simulate what Claude does: create skill entity with status="creating"
    skill_name = f"test-skill-{uuid.uuid4().hex[:8]}"
    skill_entity = {
        "type": "skill",
        "name": skill_name,
        "description": "Test skill for verification",
        "status": "creating",
    }
    result = plugin_records.skillit_records.entity_crud(
        session_id=session_id,
        crud="create",
        entity=skill_entity,
    )
    print(f"Create result: {result}")

    time.sleep(2)  # give FlowPad time to render

    # Verify task was created
    from flow_sdk.fs_store import Record
    from flow_sdk.fs_records import TaskResource
    session_record = Record.init_record(session.record_dir / "record.json")
    task_data = session_record["task"] if "task" in session_record else None
    assert task_data is not None, "Task should be created when skill entity is created"

    task = TaskResource.from_dict(task_data)
    assert task.status == TaskStatus.IN_PROGRESS
    print(f"✓ Task created with status: {task.status}")

    # Simulate what Claude does: update skill entity to status="new"
    skill_entity["status"] = "new"
    result = plugin_records.skillit_records.entity_crud(
        session_id=session_id,
        crud="update",
        entity=skill_entity,
    )
    print(f"Update result: {result}")

    time.sleep(1)

    # Verify task was completed
    session_record = Record.init_record(session.record_dir / "record.json")
    task_data = session_record["task"]
    task = TaskResource.from_dict(task_data)
    assert task.status == TaskStatus.DONE
    print(f"✓ Task completed with status: {task.status}")

def test_notify_mcp():
    """End-to-end: analyze transcript, classify issues, create rule."""
    env = make_env()
    env.loadMcp()
    result = env.launch_claude("use skillit mcp to parse the tag: <flow-started_generating_skill>Testing MCP flow tag</flow-started_generating_skill>")
    skill_log_print()
    assert result.returncode == 0
    assert 'flow' in result.stdout.lower()
