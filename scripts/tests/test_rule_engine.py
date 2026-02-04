"""Tests for the file-based rule engine system."""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from memory.rule_loader import (
    discover_rules,
    get_user_rules_dir,
    get_project_rules_dir,
    ensure_rules_dir,
    load_rule_metadata,
    _is_valid_rule_dir,
)
from memory.trigger_executor import (
    execute_trigger,
    _parse_trigger_output,
    TriggerResult,
    Action,
)
from memory.action_executor import (
    ActionExecutor,
    execute_actions,
    format_hook_output,
)
from memory.rule_engine import (
    RuleEngine,
    create_rule_engine,
    evaluate_hooks_with_rules,
)
from memory.regex_utils import (
    contains,
    regex_match,
    word_boundary_match,
    matches_any,
)
from memory.field_extractor import (
    get_user_prompt,
    get_bash_command,
    get_tool_info,
    get_hook_event,
)
from memory.index_manager import IndexManager


class TestRegexUtils:
    """Tests for regex utility functions."""

    def test_contains_case_insensitive(self):
        assert contains("jira", "Help with JIRA ticket")
        assert contains("JIRA", "help with jira ticket")
        assert not contains("github", "Help with JIRA ticket")

    def test_contains_case_sensitive(self):
        assert contains("JIRA", "Help with JIRA ticket", case_sensitive=True)
        assert not contains("jira", "Help with JIRA ticket", case_sensitive=True)

    def test_regex_match(self):
        assert regex_match(r"rm\s+-rf", "rm -rf /")
        assert not regex_match(r"rm\s+-rf", "rm file.txt")

    def test_word_boundary_match(self):
        assert word_boundary_match("jira", "Help with jira tickets")
        assert not word_boundary_match("jira", "Help with jiratickets")

    def test_matches_any(self):
        patterns = ["jira", "ticket", "issue"]
        assert matches_any(patterns, "Help with my jira")
        assert matches_any(patterns, "Create a ticket")
        assert not matches_any(patterns, "Help with code")


class TestFieldExtractor:
    """Tests for field extraction utilities."""

    def test_get_user_prompt(self):
        input_data = {"hooks_data": {"prompt": "test prompt"}}
        assert get_user_prompt(input_data) == "test prompt"

    def test_get_user_prompt_from_command(self):
        input_data = {"hooks_data": {"command": "test command"}}
        assert get_user_prompt(input_data) == "test command"

    def test_get_bash_command(self):
        input_data = {
            "hooks_data": {
                "tool_name": "Bash",
                "tool_input": {"command": "ls -la"},
            }
        }
        assert get_bash_command(input_data) == "ls -la"

    def test_get_bash_command_not_bash(self):
        input_data = {
            "hooks_data": {
                "tool_name": "Write",
                "tool_input": {"file_path": "/test.txt"},
            }
        }
        assert get_bash_command(input_data) is None

    def test_get_tool_info(self):
        input_data = {
            "hooks_data": {
                "tool_name": "Edit",
                "tool_input": {"file_path": "/test.txt", "old_string": "a", "new_string": "b"},
            }
        }
        tool_name, tool_input = get_tool_info(input_data)
        assert tool_name == "Edit"
        assert tool_input["file_path"] == "/test.txt"

    def test_get_hook_event(self):
        input_data = {"hooks_data": {"hookEvent": "PreToolUse"}}
        assert get_hook_event(input_data) == "PreToolUse"


class TestTriggerExecutor:
    """Tests for trigger execution."""

    def test_parse_trigger_output_success(self):
        stdout = """<trigger-result>
{
  "trigger": true,
  "reason": "Test reason",
  "entry_id": null,
  "actions": [{"type": "add_context", "content": "test"}]
}
</trigger-result>"""
        result = _parse_trigger_output(stdout, "test_rule")
        assert result.trigger is True
        assert result.reason == "Test reason"
        assert len(result.actions) == 1
        assert result.actions[0].type == "add_context"

    def test_parse_trigger_output_no_tags(self):
        stdout = "some random output"
        result = _parse_trigger_output(stdout, "test_rule")
        assert result.trigger is False

    def test_parse_trigger_output_invalid_json(self):
        stdout = "<trigger-result>not valid json</trigger-result>"
        result = _parse_trigger_output(stdout, "test_rule")
        assert result.error is not None


class TestActionExecutor:
    """Tests for action execution."""

    def test_add_context(self):
        executor = ActionExecutor("UserPromptSubmit")
        result = executor.add_context("Test context")
        assert result.success
        assert result.output["hookSpecificOutput"]["additionalContext"] == "Test context"

    def test_block_user_prompt_submit(self):
        executor = ActionExecutor("UserPromptSubmit")
        result = executor.block("Test reason")
        assert result.success
        assert result.output["decision"] == "block"
        assert result.output["reason"] == "Test reason"
        assert result.should_stop

    def test_block_pre_tool_use(self):
        executor = ActionExecutor("PreToolUse")
        result = executor.block("Test reason")
        assert result.success
        assert result.output["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert result.should_stop

    def test_allow(self):
        executor = ActionExecutor("PreToolUse")
        result = executor.allow("Test reason")
        assert result.success
        assert result.output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_modify_input(self):
        executor = ActionExecutor("PreToolUse")
        result = executor.modify_input({"timeout": 60})
        assert result.success
        assert result.output["hookSpecificOutput"]["updatedInput"]["timeout"] == 60


class TestExecuteActions:
    """Tests for combined action execution."""

    def test_combine_contexts(self):
        results = [
            TriggerResult(
                trigger=True,
                reason="Rule 1",
                rule_name="rule1",
                actions=[Action(type="add_context", params={"content": "Context 1"})],
            ),
            TriggerResult(
                trigger=True,
                reason="Rule 2",
                rule_name="rule2",
                actions=[Action(type="add_context", params={"content": "Context 2"})],
            ),
        ]
        output = execute_actions(results, "UserPromptSubmit")
        context = output["hookSpecificOutput"]["additionalContext"]
        assert "rule1" in context
        assert "Context 1" in context
        assert "rule2" in context
        assert "Context 2" in context

    def test_block_takes_priority(self):
        results = [
            TriggerResult(
                trigger=True,
                reason="Rule 1",
                rule_name="rule1",
                actions=[Action(type="add_context", params={"content": "Context"})],
            ),
            TriggerResult(
                trigger=True,
                reason="Rule 2",
                rule_name="rule2",
                actions=[Action(type="block", params={"reason": "Blocked"})],
            ),
        ]
        output = execute_actions(results, "UserPromptSubmit")
        assert output["decision"] == "block"


class TestFormatHookOutput:
    """Tests for hook output formatting."""

    def test_format_pre_tool_use_block(self):
        output = {
            "decision": "block",
            "reason": "Test reason",
        }
        formatted = format_hook_output(output, "PreToolUse")
        assert "decision" not in formatted
        assert formatted["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_format_removes_internal_fields(self):
        output = {
            "_exit_code": 0,
            "_triggered_rules": [],
            "hookSpecificOutput": {"additionalContext": "test"},
        }
        formatted = format_hook_output(output, "UserPromptSubmit")
        assert "_exit_code" not in formatted
        assert "_triggered_rules" not in formatted
        assert "hookSpecificOutput" in formatted


class TestIndexManager:
    """Tests for index.md management."""

    def test_load_empty_index(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir)
            manager = IndexManager(rules_dir)
            index = manager.load_index()
            assert index["rules"] == []

    def test_add_rule(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir)
            manager = IndexManager(rules_dir)
            manager.add_rule("test_rule", {
                "trigger_summary": "Test trigger",
                "hook_events": "UserPromptSubmit",
                "actions": "add_context",
            })
            index = manager.load_index()
            assert len(index["rules"]) == 1
            assert index["rules"][0]["name"] == "test_rule"

    def test_rule_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir)
            manager = IndexManager(rules_dir)
            manager.add_rule("test_rule", {"trigger_summary": "Test"})
            assert manager.rule_exists("test_rule")
            assert not manager.rule_exists("other_rule")

    def test_find_similar_rule(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir)
            manager = IndexManager(rules_dir)
            manager.add_rule("jira_context", {"trigger_summary": "prompt contains jira"})
            # Should find similar
            similar = manager.find_similar_rule("jira prompt", threshold=0.3)
            assert similar == "jira_context"
            # Should not find similar
            not_similar = manager.find_similar_rule("completely different", threshold=0.7)
            assert not_similar is None


class TestRuleEngine:
    """Tests for the main rule engine."""

    def test_create_rule_engine(self):
        engine = create_rule_engine()
        assert isinstance(engine, RuleEngine)

    def test_discover_rules_from_user_dir(self):
        # This tests the actual user rules directory
        engine = create_rule_engine()
        rules = engine.discover_rules()
        # Should find at least the example rules we created
        rule_names = [r["name"] for r in rules]
        assert "jira_context" in rule_names

    def test_evaluate_rules_jira_context(self):
        engine = create_rule_engine()
        result = engine.evaluate_rules({
            "hookEvent": "UserPromptSubmit",
            "prompt": "Help me with the jira ticket",
        })
        # Should have triggered jira_context
        assert "hookSpecificOutput" in result
        assert "additionalContext" in result["hookSpecificOutput"]
        assert "jira" in result["hookSpecificOutput"]["additionalContext"].lower()

    def test_evaluate_rules_no_match(self):
        engine = create_rule_engine()
        result = engine.evaluate_rules({
            "hookEvent": "UserPromptSubmit",
            "prompt": "Help me with this code",
        })
        # Should not have any output (no rules triggered)
        assert result == {} or "_triggered_rules" not in result or len(result.get("_triggered_rules", [])) == 0

    def test_evaluate_rules_block_rm_rf(self):
        engine = create_rule_engine()
        result = engine.evaluate_rules({
            "hookEvent": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf /"},
        })
        # Should have blocked
        assert "hookSpecificOutput" in result
        assert result["hookSpecificOutput"].get("permissionDecision") == "deny"


class TestJiraContextEval:
    """Eval tests for jira_context rule using test case files."""

    def test_jira_status_prompt_adds_acli_context(self):
        """
        Test that 'how would you check my jira status?' triggers the jira_context rule
        and adds acli context to the response.

        This validates the rule trigger mechanism works correctly.
        """
        import json
        from pathlib import Path

        # Load expected output
        eval_dir = Path(__file__).parent / "test_skills" / "jira_acli" / "eval" / "case_jira_status"
        expected_file = eval_dir / "expected.json"
        with open(expected_file) as f:
            expected = json.load(f)

        # Run rule engine with the test prompt
        engine = create_rule_engine()
        result = engine.evaluate_rules({
            "hookEvent": "UserPromptSubmit",
            "prompt": "how would you check my jira status?",
        })

        # Verify the output matches expected
        assert "hookSpecificOutput" in result, "Rule should produce hookSpecificOutput"
        assert "additionalContext" in result["hookSpecificOutput"], "Should have additionalContext"

        # Check that acli is mentioned in the context
        context = result["hookSpecificOutput"]["additionalContext"]
        assert "acli" in context.lower(), f"Context should mention acli, got: {context}"

        # Verify exact match with expected
        assert result["hookSpecificOutput"]["additionalContext"] == expected["hookSpecificOutput"]["additionalContext"], \
            f"Context mismatch.\nExpected: {expected['hookSpecificOutput']['additionalContext']}\nActual: {result['hookSpecificOutput']['additionalContext']}"
