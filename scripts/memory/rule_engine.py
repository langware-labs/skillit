"""Main rule evaluation engine for file-based rules."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from log import skill_log
from .rule_loader import discover_rules, get_rules_dir
from .trigger_executor import execute_all_triggers, TriggerResult
from .action_executor import execute_actions, format_hook_output


class RuleEngine:
    """Main engine for evaluating file-based rules."""

    def __init__(self, project_dir: str | None = None):
        """Initialize the rule engine.

        Args:
            project_dir: Optional project directory path for project-specific rules.
        """
        self.project_dir = project_dir
        self._rules_cache: list[dict[str, Any]] | None = None

    def discover_rules(self, force_refresh: bool = False) -> list[dict[str, Any]]:
        """Discover all available rules.

        Args:
            force_refresh: If True, bypass cache and re-discover rules.

        Returns:
            List of rule metadata dicts.
        """
        if self._rules_cache is None or force_refresh:
            self._rules_cache = discover_rules(self.project_dir)
            skill_log(f"Discovered {len(self._rules_cache)} rules")
        return self._rules_cache

    def evaluate_rules(
        self,
        hooks_data: dict[str, Any],
        transcript: list[dict[str, Any]] | None = None,
        timeout: float = 5.0,
    ) -> dict[str, Any]:
        """Evaluate all rules against the current hook event.

        Args:
            hooks_data: Current hook event data.
            transcript: Optional list of transcript entries.
            timeout: Maximum execution time per trigger.

        Returns:
            Combined hook JSON output dict.
        """
        rules = self.discover_rules()
        if not rules:
            return {}

        # Get hook event type for proper output formatting
        hook_event = (
            hooks_data.get("hookEvent")
            or hooks_data.get("hook_event")
            or hooks_data.get("event")
            or ""
        )

        # Execute all triggers
        trigger_results = execute_all_triggers(
            rules=rules,
            hooks_data=hooks_data,
            transcript=transcript or [],
            timeout=timeout,
        )

        if not trigger_results:
            skill_log("No rules triggered")
            return {}

        # Log triggered rules
        triggered_names = [r.rule_name for r in trigger_results]
        skill_log(f"Triggered rules: {triggered_names}")

        # Execute actions and build output
        output = execute_actions(
            trigger_results=trigger_results,
            hook_event=hook_event,
            hooks_data=hooks_data,
            transcript=transcript or [],
        )

        # Handle exit code
        exit_code = output.pop("_exit_code", None)
        chain_requests = output.pop("_chain_requests", None)

        # Format output for hook event type
        formatted = format_hook_output(output, hook_event)

        # Store metadata for caller
        formatted["_triggered_rules"] = [r.to_dict() for r in trigger_results]
        if exit_code is not None:
            formatted["_exit_code"] = exit_code
        if chain_requests:
            formatted["_chain_requests"] = chain_requests

        return formatted

    def evaluate_single_rule(
        self,
        rule_name: str,
        hooks_data: dict[str, Any],
        transcript: list[dict[str, Any]] | None = None,
    ) -> TriggerResult | None:
        """Evaluate a single rule by name.

        Args:
            rule_name: Name of the rule to evaluate.
            hooks_data: Current hook event data.
            transcript: Optional list of transcript entries.

        Returns:
            TriggerResult if the rule triggered, None otherwise.
        """
        rules = self.discover_rules()

        # Find the rule by name
        rule = next((r for r in rules if r["name"] == rule_name), None)
        if not rule:
            skill_log(f"Rule not found: {rule_name}")
            return None

        results = execute_all_triggers(
            rules=[rule],
            hooks_data=hooks_data,
            transcript=transcript or [],
        )

        return results[0] if results else None

    def get_rules_summary(self) -> list[dict[str, str]]:
        """Get a summary of all rules for logging/debugging.

        Returns:
            List of dicts with rule name, source, and path.
        """
        rules = self.discover_rules()
        return [
            {
                "name": r["name"],
                "source": r["source"],
                "path": str(r["path"]),
            }
            for r in rules
        ]


def create_rule_engine(project_dir: str | None = None) -> RuleEngine:
    """Create a rule engine instance.

    Args:
        project_dir: Optional project directory path.

    Returns:
        Configured RuleEngine instance.
    """
    return RuleEngine(project_dir=project_dir)


def evaluate_hooks_with_rules(
    hooks_data: dict[str, Any],
    transcript: list[dict[str, Any]] | None = None,
    project_dir: str | None = None,
) -> dict[str, Any]:
    """Convenience function to evaluate rules against hook data.

    Args:
        hooks_data: Current hook event data.
        transcript: Optional list of transcript entries.
        project_dir: Optional project directory path.

    Returns:
        Combined hook JSON output dict.
    """
    engine = create_rule_engine(project_dir)
    return engine.evaluate_rules(hooks_data, transcript)
