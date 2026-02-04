"""Factory for generating hook data for each Claude HookEventType."""

import pytest
from memory.types.hooks import HookEventType


def create_hook_data(
    hook_type: HookEventType,
    trigger_keyword: bool = True,
    dangerous: bool = False,
) -> dict:
    """Create hook data for the specified hook type.

    Args:
        hook_type: The Claude hook event type.
        trigger_keyword: If True, include 'test_keyword' to trigger the rule.
        dangerous: If True, include 'dangerous' for block action testing.

    Returns:
        dict: Hook data matching the specified hook type schema.
    """
    keyword = "test_keyword" if trigger_keyword else "no_match"
    danger_suffix = " dangerous" if dangerous else ""

    base_data = {
        "hookEvent": hook_type.value,
        "session_id": "test-session-123",
        "transcript_path": "/tmp/transcript.json",
        "cwd": "/Users/test/project",
    }

    if hook_type == HookEventType.USER_PROMPT_SUBMIT:
        return {
            **base_data,
            "prompt": f"Please help with {keyword}{danger_suffix}",
        }

    elif hook_type == HookEventType.PRE_TOOL_USE:
        return {
            **base_data,
            "tool_name": "Bash",
            "tool_input": {"command": f"echo {keyword}{danger_suffix}"},
            "tool_use_id": "tool-use-001",
        }

    elif hook_type == HookEventType.POST_TOOL_USE:
        return {
            **base_data,
            "tool_name": "Bash",
            "tool_input": {"command": f"echo {keyword}"},
            "tool_response": {"output": "command output"},
            "tool_use_id": "tool-use-001",
        }

    elif hook_type == HookEventType.SESSION_START:
        return {
            **base_data,
            "source": f"cli_{keyword}" if trigger_keyword else "cli",
        }

    elif hook_type == HookEventType.STOP:
        return {
            **base_data,
            "stop_hook_active": True,
            # Include keyword in raw data for triggering
            "metadata": {"info": keyword} if trigger_keyword else {},
        }

    elif hook_type == HookEventType.NOTIFICATION:
        return {
            **base_data,
            "message": f"Notification: {keyword}" if trigger_keyword else "Info",
            "notification_type": "idle",
        }

    elif hook_type == HookEventType.SUBAGENT_STOP:
        return {
            **base_data,
            "agent_id": "agent-001",
            "agent_type": f"Explore_{keyword}" if trigger_keyword else "Explore",
            "agent_transcript_path": "/tmp/agent_transcript.json",
            "stop_hook_active": True,
        }

    elif hook_type == HookEventType.PRE_COMPACT:
        return {
            **base_data,
            "compact_info": keyword if trigger_keyword else "none",
        }

    elif hook_type == HookEventType.PERMISSION_REQUEST:
        return {
            **base_data,
            "permission_mode": "default",
            "request_info": keyword if trigger_keyword else "none",
        }

    else:
        # Fallback for any new hook types
        return {
            **base_data,
            "data": keyword if trigger_keyword else "none",
        }


@pytest.fixture
def hook_data_factory():
    """Pytest fixture that returns the hook data factory function."""
    return create_hook_data
