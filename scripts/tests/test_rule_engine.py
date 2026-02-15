"""Tests for the file-based rule engine system."""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from memory import (
    # Rule loader
    discover_rules,
    get_user_rules_dir,
    get_project_rules_dir,
    ensure_rules_dir,
    load_rule_metadata,
    # Trigger executor
    TriggerResult,
    Action,
    # Action executor
    ActionExecutor,
    execute_actions,
    format_hook_output,
    # Rule engine
    RuleEngine,
    create_rule_engine,
    evaluate_hooks_with_rules,
    # New classes
    ActivationRule,
    RulesPackage,
    # Regex utils
    contains,
    regex_match,
    word_boundary_match,
    matches_any,
    # Field extractor
    get_user_prompt,
    get_bash_command,
    get_tool_info,
    get_hook_event,
    # Index manager
    IndexManager,
)

# Also import from submodules to verify those paths work
from memory.rule_engine.trigger_executor import _convert_actions_to_result
from memory.rule_engine.rule_loader import _is_valid_rule_dir


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

    def test_convert_actions_to_result_none(self):
        """Test that None returns a non-triggered result."""
        result = _convert_actions_to_result(None, "test_rule")
        assert result.trigger is False
        assert result.rule_name == "test_rule"

    def test_convert_actions_to_result_single_action(self):
        """Test that a single Action returns a triggered result."""
        action = Action(type="add_context", params={"content": "test"})
        result = _convert_actions_to_result(action, "test_rule")
        assert result.trigger is True
        assert len(result.actions) == 1
        assert result.actions[0].type == "add_context"

    def test_convert_actions_to_result_list(self):
        """Test that a list of Actions returns a triggered result."""
        actions = [
            Action(type="block", params={"reason": "blocked"}),
            Action(type="add_context", params={"content": "test1"}),
        ]
        result = _convert_actions_to_result(actions, "test_rule")
        assert result.trigger is True
        assert len(result.actions) == 2
        assert result.reason == "blocked"  # First action with reason


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


def _make_rule_dir(parent: Path, name: str, record: dict | None = None) -> Path:
    """Helper: create a rule directory with record.json and trigger.py."""
    rule_dir = parent / name
    rule_dir.mkdir(parents=True, exist_ok=True)
    (rule_dir / "trigger.py").write_text("# empty trigger")
    rec = {"name": name, "type": "rule", **(record or {})}
    (rule_dir / "record.json").write_text(json.dumps(rec), encoding="utf-8")
    return rule_dir


class TestActivationRule:
    """Tests for the ActivationRule class."""

    def test_from_json_loads_fields(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rule_dir = _make_rule_dir(Path(tmpdir), "test_rule", {
                "description": "A test rule for testing.",
                "if_condition": "prompt contains 'test'",
                "then_action": "add context with test info",
                "hook_events": ["UserPromptSubmit", "PreToolUse"],
                "actions": ["add_context"],
                "scope": "user",
            })

            rule = ActivationRule.from_json(rule_dir / "record.json")
            rule.path = str(rule_dir)

            assert rule.name == "test_rule"
            assert rule.if_condition == "prompt contains 'test'"
            assert rule.then_action == "add context with test info"
            assert rule.hook_events == ["UserPromptSubmit", "PreToolUse"]
            assert rule.actions == ["add_context"]

    def test_properties_get_set(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rule_dir = _make_rule_dir(Path(tmpdir), "test_rule")

            rule = ActivationRule.from_json(rule_dir / "record.json")
            rule.path = str(rule_dir)

            rule.if_condition = "new condition"
            assert rule.if_condition == "new condition"

            rule.then_action = "new action"
            assert rule.then_action == "new action"

            rule.hook_events = ["PostToolUse"]
            assert rule.hook_events == ["PostToolUse"]

    def test_to_dict(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rule_dir = _make_rule_dir(Path(tmpdir), "dict_test", {
                "if_condition": "test condition",
                "then_action": "test action",
            })

            rule = ActivationRule.from_json(rule_dir / "record.json")
            rule.path = str(rule_dir)
            d = rule.to_dict()

            assert d["name"] == "dict_test"
            assert d["if_condition"] == "test condition"
            assert d["then_action"] == "test action"

    def test_is_valid(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Valid rule (has trigger.py)
            valid_dir = _make_rule_dir(Path(tmpdir), "valid_rule")
            valid_rule = ActivationRule.from_json(valid_dir / "record.json")
            valid_rule.path = str(valid_dir)
            assert valid_rule.is_valid()

            # Invalid rule (no trigger.py)
            invalid_dir = Path(tmpdir) / "invalid_rule"
            invalid_dir.mkdir()
            (invalid_dir / "record.json").write_text(
                json.dumps({"name": "invalid_rule", "type": "rule"}),
                encoding="utf-8",
            )
            invalid_rule = ActivationRule.from_json(invalid_dir / "record.json")
            invalid_rule.path = str(invalid_dir)
            assert not invalid_rule.is_valid()

    def test_run_executes_trigger(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rule_dir = Path(tmpdir) / "run_test"
            rule_dir.mkdir()

            trigger_code = '''
from memory.rule_engine.trigger_executor import Action

def evaluate(hooks_data: dict, transcript: list) -> Action | list[Action] | None:
    prompt = hooks_data.get("prompt", "")

    if "test" in prompt.lower():
        return Action(type="add_context", params={"content": "Test context"})

    return None
'''
            (rule_dir / "trigger.py").write_text(trigger_code)
            (rule_dir / "record.json").write_text(
                json.dumps({"name": "run_test", "type": "rule"}),
                encoding="utf-8",
            )

            rule = ActivationRule.from_json(rule_dir / "record.json")
            rule.path = str(rule_dir)

            # Should trigger
            result = rule.run({"prompt": "this is a test prompt"})
            assert result.trigger is True
            assert len(result.actions) == 1
            assert result.actions[0].type == "add_context"

            # Should not trigger
            result = rule.run({"prompt": "hello world"})
            assert result.trigger is False


class TestRulesPackage:
    """Tests for the RulesPackage class."""

    def test_loads_rules_from_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir)
            _make_rule_dir(rules_dir, "rule_a")
            _make_rule_dir(rules_dir, "rule_b")

            package = RulesPackage.from_folder(rules_dir, source="test")

            assert len(package) == 2
            assert "rule_a" in package
            assert "rule_b" in package

    def test_get_rule_by_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir)
            _make_rule_dir(rules_dir, "my_rule", {"description": "test desc"})

            package = RulesPackage.from_folder(rules_dir, source="test")
            rule = package.get("my_rule")

            assert rule is not None
            assert rule.name == "my_rule"
            assert rule.description == "test desc"
            assert str(rule.scope) == "test"

    def test_run_aggregates_results(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir)
            rule_dir = rules_dir / "aggregate_rule"
            rule_dir.mkdir()

            trigger_code = '''
from memory.rule_engine.trigger_executor import Action

def evaluate(hooks_data: dict, transcript: list) -> Action | list[Action] | None:
    prompt = hooks_data.get("prompt", "")

    if "aggregate" in prompt.lower():
        return Action(type="add_context", params={"content": "Aggregated context"})

    return None
'''
            (rule_dir / "trigger.py").write_text(trigger_code)
            (rule_dir / "record.json").write_text(
                json.dumps({"name": "aggregate_rule", "type": "rule"}),
                encoding="utf-8",
            )

            package = RulesPackage.from_folder(rules_dir, source="test")

            # Should trigger
            result = package.run({"hookEvent": "UserPromptSubmit", "prompt": "test aggregate"})
            assert "hookSpecificOutput" in result
            assert "additionalContext" in result["hookSpecificOutput"]
            assert "Aggregated" in result["hookSpecificOutput"]["additionalContext"]

            # Should not trigger
            result = package.run({"hookEvent": "UserPromptSubmit", "prompt": "no match"})
            assert result == {}

    def test_find_similar(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir)
            _make_rule_dir(rules_dir, "jira_helper", {
                "if_condition": "prompt contains jira ticket",
            })

            package = RulesPackage.from_folder(rules_dir, source="test")

            similar = package.find_similar("jira ticket help", threshold=0.3)
            assert similar == "jira_helper"

            similar = package.find_similar("completely unrelated", threshold=0.7)
            assert similar is None

    def test_get_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir)
            _make_rule_dir(rules_dir, "summary_test")

            package = RulesPackage.from_folder(rules_dir, source="test_source")

            summary = package.get_summary()
            assert len(summary) == 1
            assert summary[0]["name"] == "summary_test"
            assert summary[0]["source"] == "test_source"
            assert summary[0]["path"] != ""

    def test_crud_via_record_list(self):
        """Test create/save/delete via inherited ResourceRecordList methods."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir)
            package = RulesPackage(path=rules_dir, source="test")

            # Create
            rule = ActivationRule(name="new_rule", description="created via CRUD")
            package.create(rule)
            assert "new_rule" in package
            assert len(package) == 1

            # Get
            loaded = package.get("new_rule")
            assert loaded is not None
            assert loaded.description == "created via CRUD"

            # Delete
            deleted = package.delete("new_rule")
            assert deleted is True
            assert "new_rule" not in package
            assert len(package) == 0


class TestRuleEngine:
    """Tests for the main rule engine."""

    def test_create_rule_engine(self):
        engine = create_rule_engine()
        assert isinstance(engine, RuleEngine)

    def test_discover_rules_from_user_dir(self):
        engine = create_rule_engine()
        rules = engine.discover_rules()
        rule_names = [r["name"] for r in rules]
        assert "jira_context" in rule_names

    def test_evaluate_rules_jira_context(self):
        engine = create_rule_engine()
        result = engine.evaluate_rules({
            "hookEvent": "UserPromptSubmit",
            "prompt": "Help me with the jira ticket",
        })
        assert "hookSpecificOutput" in result
        assert "additionalContext" in result["hookSpecificOutput"]
        assert "jira" in result["hookSpecificOutput"]["additionalContext"].lower()

    def test_evaluate_rules_no_match(self):
        engine = create_rule_engine()
        result = engine.evaluate_rules({
            "hookEvent": "UserPromptSubmit",
            "prompt": "Help me with this code",
        })
        assert result == {} or "_triggered_rules" not in result or len(result.get("_triggered_rules", [])) == 0

    def test_evaluate_rules_block_rm_rf(self):
        engine = create_rule_engine()
        result = engine.evaluate_rules({
            "hookEvent": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf /"},
        })
        assert "hookSpecificOutput" in result
        assert result["hookSpecificOutput"].get("permissionDecision") == "deny"
