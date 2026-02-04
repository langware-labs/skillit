"""Unit tests for trigger loading and execution across all Claude hook types."""

import json
import pytest
from pathlib import Path

from memory import ActivationRule, TriggerResult, Action
from memory.types.hooks import HookEventType

# Import hook_data_factory fixture from test_utils
from tests.test_utils.hook_data_factory import hook_data_factory  # noqa: F401


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_rule_path() -> Path:
    """Path to the test_rule sample rule directory."""
    return Path(__file__).parent / "sample_rules" / "test_rule"


@pytest.fixture
def sample_rule(sample_rule_path: Path) -> ActivationRule:
    """Load ActivationRule from the sample rule directory."""
    return ActivationRule.from_md(sample_rule_path)


@pytest.fixture
def sample_transcript() -> list[dict]:
    """Load sample transcript from resources/transcript.jsonl."""
    transcript_path = Path(__file__).parent / "resources" / "transcript.jsonl"
    entries = []
    with open(transcript_path) as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_load_rule_from_folder(sample_rule: ActivationRule):
    """Verify ActivationRule.from_md() loads rule correctly from folder."""
    assert sample_rule is not None
    assert sample_rule.name == "test_rule"
    assert sample_rule.is_valid()
    assert "test_keyword" in sample_rule.if_condition.lower()
    assert "add_context" in sample_rule.actions
    assert "block" in sample_rule.actions


def test_run_with_user_prompt_submit(
    sample_rule: ActivationRule,
    sample_transcript: list[dict],
    hook_data_factory,
):
    """Test UserPromptSubmit hook triggers add_context action."""
    hook_data = hook_data_factory(HookEventType.USER_PROMPT_SUBMIT)

    result = sample_rule.run(hook_data, sample_transcript)

    assert isinstance(result, TriggerResult)
    assert result.trigger is True
    assert "test_keyword" in result.reason.lower() or "userpromptsubmit" in result.reason.lower()
    assert len(result.actions) >= 1
    assert result.actions[0].type == "add_context"
    assert "content" in result.actions[0].params


def test_run_with_pre_tool_use(
    sample_rule: ActivationRule,
    sample_transcript: list[dict],
    hook_data_factory,
):
    """Test PreToolUse hook with Bash command triggers correctly."""
    hook_data = hook_data_factory(HookEventType.PRE_TOOL_USE)

    result = sample_rule.run(hook_data, sample_transcript)

    assert isinstance(result, TriggerResult)
    assert result.trigger is True
    assert len(result.actions) >= 1
    assert result.actions[0].type == "add_context"


def test_run_with_pre_tool_use_block(
    sample_rule: ActivationRule,
    sample_transcript: list[dict],
    hook_data_factory,
):
    """Test PreToolUse with dangerous command triggers block action."""
    hook_data = hook_data_factory(HookEventType.PRE_TOOL_USE, dangerous=True)

    result = sample_rule.run(hook_data, sample_transcript)

    assert isinstance(result, TriggerResult)
    assert result.trigger is True
    assert len(result.actions) >= 1
    assert result.actions[0].type == "block"
    assert "reason" in result.actions[0].params


def test_run_with_post_tool_use(
    sample_rule: ActivationRule,
    sample_transcript: list[dict],
    hook_data_factory,
):
    """Test PostToolUse hook processing."""
    hook_data = hook_data_factory(HookEventType.POST_TOOL_USE)

    result = sample_rule.run(hook_data, sample_transcript)

    assert isinstance(result, TriggerResult)
    assert result.trigger is True
    assert len(result.actions) >= 1


def test_run_with_session_start(
    sample_rule: ActivationRule,
    sample_transcript: list[dict],
    hook_data_factory,
):
    """Test SessionStart hook."""
    hook_data = hook_data_factory(HookEventType.SESSION_START)

    result = sample_rule.run(hook_data, sample_transcript)

    assert isinstance(result, TriggerResult)
    assert result.trigger is True


def test_run_with_stop(
    sample_rule: ActivationRule,
    sample_transcript: list[dict],
    hook_data_factory,
):
    """Test Stop hook."""
    hook_data = hook_data_factory(HookEventType.STOP)

    result = sample_rule.run(hook_data, sample_transcript)

    assert isinstance(result, TriggerResult)
    # Stop hook may or may not trigger depending on implementation
    # The key is that it runs without error


def test_run_with_notification(
    sample_rule: ActivationRule,
    sample_transcript: list[dict],
    hook_data_factory,
):
    """Test Notification hook."""
    hook_data = hook_data_factory(HookEventType.NOTIFICATION)

    result = sample_rule.run(hook_data, sample_transcript)

    assert isinstance(result, TriggerResult)
    assert result.trigger is True


def test_run_with_subagent_stop(
    sample_rule: ActivationRule,
    sample_transcript: list[dict],
    hook_data_factory,
):
    """Test SubagentStop hook."""
    hook_data = hook_data_factory(HookEventType.SUBAGENT_STOP)

    result = sample_rule.run(hook_data, sample_transcript)

    assert isinstance(result, TriggerResult)
    assert result.trigger is True


def test_run_with_pre_compact(
    sample_rule: ActivationRule,
    sample_transcript: list[dict],
    hook_data_factory,
):
    """Test PreCompact hook."""
    hook_data = hook_data_factory(HookEventType.PRE_COMPACT)

    result = sample_rule.run(hook_data, sample_transcript)

    assert isinstance(result, TriggerResult)
    # PreCompact may or may not trigger based on implementation


def test_run_with_permission_request(
    sample_rule: ActivationRule,
    sample_transcript: list[dict],
    hook_data_factory,
):
    """Test PermissionRequest hook."""
    hook_data = hook_data_factory(HookEventType.PERMISSION_REQUEST)

    result = sample_rule.run(hook_data, sample_transcript)

    assert isinstance(result, TriggerResult)
    # PermissionRequest may or may not trigger based on implementation


def test_run_no_trigger(
    sample_rule: ActivationRule,
    sample_transcript: list[dict],
    hook_data_factory,
):
    """Test that non-matching input returns trigger=False."""
    hook_data = hook_data_factory(
        HookEventType.USER_PROMPT_SUBMIT,
        trigger_keyword=False,
    )

    result = sample_rule.run(hook_data, sample_transcript)

    assert isinstance(result, TriggerResult)
    assert result.trigger is False
    assert len(result.actions) == 0


def test_action_validation_add_context(
    sample_rule: ActivationRule,
    sample_transcript: list[dict],
    hook_data_factory,
):
    """Validate add_context action has correct type and params."""
    hook_data = hook_data_factory(HookEventType.USER_PROMPT_SUBMIT)

    result = sample_rule.run(hook_data, sample_transcript)

    assert result.trigger is True
    action = result.actions[0]
    assert isinstance(action, Action)
    assert action.type == "add_context"
    assert "content" in action.params
    assert isinstance(action.params["content"], str)
    assert len(action.params["content"]) > 0


def test_action_validation_block(
    sample_rule: ActivationRule,
    sample_transcript: list[dict],
    hook_data_factory,
):
    """Validate block action has correct type and params."""
    hook_data = hook_data_factory(HookEventType.PRE_TOOL_USE, dangerous=True)

    result = sample_rule.run(hook_data, sample_transcript)

    assert result.trigger is True
    action = result.actions[0]
    assert isinstance(action, Action)
    assert action.type == "block"
    assert "reason" in action.params
    assert isinstance(action.params["reason"], str)


def test_run_with_empty_transcript(
    sample_rule: ActivationRule,
    hook_data_factory,
):
    """Test that rule runs correctly with empty transcript."""
    hook_data = hook_data_factory(HookEventType.USER_PROMPT_SUBMIT)

    result = sample_rule.run(hook_data, transcript=[])

    assert isinstance(result, TriggerResult)
    assert result.trigger is True


def test_run_with_none_transcript(
    sample_rule: ActivationRule,
    hook_data_factory,
):
    """Test that rule runs correctly with None transcript."""
    hook_data = hook_data_factory(HookEventType.USER_PROMPT_SUBMIT)

    result = sample_rule.run(hook_data, transcript=None)

    assert isinstance(result, TriggerResult)
    assert result.trigger is True


def test_trigger_result_to_dict(
    sample_rule: ActivationRule,
    hook_data_factory,
):
    """Test TriggerResult.to_dict() produces valid structure."""
    hook_data = hook_data_factory(HookEventType.USER_PROMPT_SUBMIT)

    result = sample_rule.run(hook_data)
    result_dict = result.to_dict()

    assert isinstance(result_dict, dict)
    assert "trigger" in result_dict
    assert "reason" in result_dict
    assert "actions" in result_dict
    assert isinstance(result_dict["actions"], list)


def test_action_to_dict(
    sample_rule: ActivationRule,
    hook_data_factory,
):
    """Test Action.to_dict() produces valid structure."""
    hook_data = hook_data_factory(HookEventType.USER_PROMPT_SUBMIT)

    result = sample_rule.run(hook_data)
    action = result.actions[0]
    action_dict = action.to_dict()

    assert isinstance(action_dict, dict)
    assert "type" in action_dict
    # Params should be flattened into the dict
    assert action_dict["type"] == "add_context"
