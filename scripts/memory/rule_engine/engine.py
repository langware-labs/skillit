"""Main rule evaluation engine for file-based rules."""

from __future__ import annotations

import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from log import skill_log
from .activation_rule import ActivationRule, ActivationRuleHeader
from .rule_loader import (
    discover_rules,
    get_rules_dir,
    get_user_rules_dir,
    get_project_rules_dir,
    get_system_rules_dir,
)
from .trigger_executor import execute_all_triggers, TriggerResult
from .action_executor import execute_actions, format_hook_output
from .index_manager import IndexManager


class RulesPackage:
    """A collection of activation rules from one or more directories.

    RulesPackage manages rule discovery, CRUD operations, and batch execution.
    Project rules override user rules with the same name.
    """

    def __init__(
        self,
        path: Path | None = None,
        source: str = "user",
        rules: list[ActivationRule] | None = None,
    ):
        """Initialize a RulesPackage.

        Args:
            path: Path to the rules folder. None means no folder.
            source: Source identifier for folder rules.
            rules: Optional additional rules (not from folder).
        """
        self._path = path
        self._source = source
        self._additional_rules: list[ActivationRule] = rules or []

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def path(self) -> Path | None:
        """Path to the rules directory, or None."""
        return self._path

    @property
    def source(self) -> str:
        """Source identifier for this package."""
        return self._source

    @property
    def folder_rules(self) -> list[ActivationRule]:
        """Live list of rules loaded from the folder path."""
        if not self._path or not self._path.exists():
            return []
        rules = []
        for rule_dir in self._path.iterdir():
            if not rule_dir.is_dir():
                continue
            if not (rule_dir / "trigger.py").exists():
                continue
            rule = ActivationRule.from_md(rule_dir)
            rule.source = self._source
            rules.append(rule)
        rules.sort(key=lambda r: r.name)
        return rules

    @property
    def additional_rules(self) -> list[ActivationRule]:
        """Rules added programmatically (not from folder)."""
        return list(self._additional_rules)

    @property
    def rules(self) -> list[ActivationRule]:
        """All rules (additional + folder). Folder (project) overrides additional (system/user) by name."""
        by_name: dict[str, ActivationRule] = {}
        for r in self._additional_rules:
            by_name[r.name] = r
        for r in self.folder_rules:
            by_name[r.name] = r
        return sorted(by_name.values(), key=lambda r: r.name)

    @property
    def _rules_by_name(self) -> dict[str, ActivationRule]:
        """Live name-to-rule lookup derived from rules."""
        return {r.name: r for r in self.rules}

    def __len__(self) -> int:
        return len(self.rules)

    def __iter__(self) -> Iterator[ActivationRule]:
        return iter(self.rules)

    def __contains__(self, name: str) -> bool:
        return name in self._rules_by_name

    # -------------------------------------------------------------------------
    # CRUD Operations
    # -------------------------------------------------------------------------

    def add_rule(self, rule: ActivationRule) -> None:
        """Add a rule to the additional rules list.

        Args:
            rule: The ActivationRule to add.

        Raises:
            ValueError: If a rule with the same name already exists.
        """
        if rule.name in self._rules_by_name:
            raise ValueError(f"Rule '{rule.name}' already exists in package")
        self._additional_rules.append(rule)
        skill_log(f"Added rule '{rule.name}' to package")

    def remove_rule(self, name: str) -> bool:
        """Remove a rule from the additional rules list by name.

        Args:
            name: Name of the rule to remove.

        Returns:
            True if rule was removed, False if not found.
        """
        for rule in self._additional_rules:
            if rule.name == name:
                self._additional_rules.remove(rule)
                skill_log(f"Removed rule '{name}' from package")
                return True
        return False

    def update_rule(self, name: str, **updates: Any) -> bool:
        """Update a rule's header fields.

        Args:
            name: Name of the rule to update.
            **updates: Header fields to update (if_condition, then_action, etc.)

        Returns:
            True if rule was updated, False if not found.
        """
        rule = self._rules_by_name.get(name)
        if not rule:
            return False

        for key, value in updates.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
            else:
                skill_log(f"Unknown rule attribute: {key}")

        skill_log(f"Updated rule '{name}'")
        return True

    def get(self, name: str) -> ActivationRule | None:
        """Get a rule by name.

        Args:
            name: Name of the rule.

        Returns:
            The ActivationRule, or None if not found.
        """
        return self._rules_by_name.get(name)

    # -------------------------------------------------------------------------
    # Class Methods
    # -------------------------------------------------------------------------

    @classmethod
    def from_folder(cls, path: Path, source: str = "user") -> "RulesPackage":
        """Create a RulesPackage backed by a directory.

        Rules are loaded live from the folder via the folder_rules property.

        Args:
            path: Path to the rules directory.
            source: Source identifier for rules in this package.

        Returns:
            RulesPackage backed by the given folder.
        """
        return cls(path=path, source=source)

    @classmethod
    def from_multiple_folders(
        cls,
        system_path: Path | None = None,
        user_path: Path | None = None,
        project_path: Path | None = None,
    ) -> "RulesPackage":
        """Create a RulesPackage merging system, user and project directories.

        Project folder is the live folder (folder_rules). System and user rules
        are loaded into additional_rules. Precedence: project > user > system
        (project overrides user, user overrides system by name).

        Args:
            system_path: Path to system rules directory (ships with skillit). None to skip.
            user_path: Path to user rules directory. None to skip.
            project_path: Path to project rules directory (live folder).

        Returns:
            RulesPackage with project as folder and system+user as additional.
        """
        additional_rules: list[ActivationRule] = []

        # Load system rules first (lowest precedence in additional)
        if system_path and system_path.exists():
            for rule_dir in system_path.iterdir():
                if not rule_dir.is_dir():
                    continue
                if not (rule_dir / "trigger.py").exists():
                    continue
                rule = ActivationRule.from_md(rule_dir)
                rule.source = "system"
                additional_rules.append(rule)

        # Load user rules (overrides system by name within additional)
        user_by_name: dict[str, ActivationRule] = {}
        if user_path and user_path.exists():
            for rule_dir in user_path.iterdir():
                if not rule_dir.is_dir():
                    continue
                if not (rule_dir / "trigger.py").exists():
                    continue
                rule = ActivationRule.from_md(rule_dir)
                rule.source = "user"
                user_by_name[rule.name] = rule

        # Merge: user overrides system by name
        merged: dict[str, ActivationRule] = {r.name: r for r in additional_rules}
        merged.update(user_by_name)
        additional_rules = list(merged.values())

        return cls(path=project_path, source="project", rules=additional_rules)

    # -------------------------------------------------------------------------
    # Instance Methods
    # -------------------------------------------------------------------------

    def to_folder(self, path: Path | None = None) -> None:
        """Save all rules to a directory.

        Args:
            path: Target directory. If None, uses self.path.
        """
        target_path = path or self._path
        target_path.mkdir(parents=True, exist_ok=True)

        all_rules = self.rules
        for rule in all_rules:
            rule_dir = target_path / rule.name
            rule_dir.mkdir(exist_ok=True)

            # Write rule.md
            rule_md = rule_dir / "rule.md"
            rule_md.write_text(rule.to_md(), encoding="utf-8")

        # Write index
        self._write_index(target_path)
        skill_log(f"Saved {len(all_rules)} rules to {target_path}")

    def run(
        self,
        hooks_data: dict[str, Any],
        transcript: list[dict[str, Any]] | None = None,
        timeout: float = 5.0,
    ) -> dict[str, Any]:
        """Execute all rules and aggregate results.

        Args:
            hooks_data: Current hook event data.
            transcript: Optional list of transcript entries.
            timeout: Maximum execution time per rule.

        Returns:
            Combined hook JSON output dict.
        """
        all_rules = self.rules
        if not all_rules:
            return {}

        # Get hook event type for proper output formatting
        hook_event = (
            hooks_data.get("hookEvent")
            or hooks_data.get("hook_event")
            or hooks_data.get("event")
            or ""
        )

        # Execute all triggers
        trigger_results: list[TriggerResult] = []
        for rule in all_rules:
            result = rule.run(hooks_data, transcript, timeout)
            if result.error:
                skill_log(f"[{result.rule_name}] Error: {result.error}")
            elif result.trigger:
                skill_log(f"[{result.rule_name}] Triggered: {result.reason}")
                trigger_results.append(result)

        if not trigger_results:
            skill_log("No rules triggered")
            return {}

        # Log triggered rules
        triggered_names = [r.rule_name for r in trigger_results]
        skill_log(f"Triggered rules: {triggered_names}")

        # Aggregate results
        return self._aggregate_results(trigger_results, hook_event, hooks_data, transcript)

    def _aggregate_results(
        self,
        trigger_results: list[TriggerResult],
        hook_event: str,
        hooks_data: dict[str, Any],
        transcript: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Aggregate trigger results into hook output.

        Args:
            trigger_results: List of triggered rule results.
            hook_event: The hook event type.
            hooks_data: Hook event data.
            transcript: Transcript entries.

        Returns:
            Combined hook JSON output dict.
        """
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

    def _write_index(self, path: Path) -> None:
        """Write index.md file to the rules directory.

        Args:
            path: Target directory.
        """
        manager = IndexManager(path)
        rules_data = []

        for rule in self.rules:
            rules_data.append({
                "name": rule.name,
                "trigger_summary": rule.if_condition,
                "hook_events": ", ".join(rule.hook_events) if rule.hook_events else "",
                "actions": ", ".join(rule.actions) if rule.actions else "",
                "created": rule.created or datetime.now().strftime("%Y-%m-%d"),
                "if_condition": rule.if_condition,
                "then_action": rule.then_action,
                "source": rule.source,
            })

        manager.save_index(rules_data)

    @property
    def rules_index(self) -> str:
        """Return a plain-text index of all rules (name + description)."""
        all_rules = self.rules
        if not all_rules:
            return "(no rules)"
        lines = []
        for rule in all_rules:
            desc = rule.description or rule.if_condition or ""
            lines.append(f"- {rule.name}: {desc}")
        return "\n".join(lines)

    def get_summary(self) -> list[dict[str, str]]:
        """Get a summary of all rules.

        Returns:
            List of dicts with rule name, source, and path.
        """
        return [
            {
                "name": r.name,
                "source": r.source,
                "path": str(r.path),
            }
            for r in self.rules
        ]

    def find_similar(self, pattern: str, threshold: float = 0.7) -> str | None:
        """Find a rule with a similar trigger pattern.

        Args:
            pattern: The trigger pattern to match against.
            threshold: Similarity threshold (0-1).

        Returns:
            Name of similar rule if found, None otherwise.
        """
        pattern_lower = pattern.lower()
        pattern_words = set(pattern_lower.split())

        for rule in self.rules:
            rule_trigger = rule.if_condition.lower()
            rule_words = set(rule_trigger.split())

            if not rule_words or not pattern_words:
                continue

            overlap = len(pattern_words & rule_words)
            total = len(pattern_words | rule_words)
            similarity = overlap / total if total > 0 else 0

            if similarity >= threshold:
                skill_log(f"Found similar rule: {rule.name} (similarity: {similarity:.2f})")
                return rule.name

        return None


# =============================================================================
# Backward Compatibility: RuleEngine
# =============================================================================


class RuleEngine:
    """Main engine for evaluating file-based rules.

    .. deprecated::
        Use RulesPackage instead. This class is kept for backward compatibility.
    """

    def __init__(self, project_dir: str | None = None):
        """Initialize the rule engine.

        Args:
            project_dir: Optional project directory path for project-specific rules.
        """
        self.project_dir = project_dir
        self._rules_cache: list[dict[str, Any]] | None = None
        self._package: RulesPackage | None = None

    def _get_package(self) -> RulesPackage:
        """Get or create the underlying RulesPackage."""
        if self._package is None:
            project_path = get_project_rules_dir(self.project_dir) if self.project_dir else None
            self._package = RulesPackage.from_multiple_folders(
                system_path=get_system_rules_dir(),
                user_path=get_user_rules_dir(),
                project_path=project_path,
            )
        return self._package

    def discover_rules(self, force_refresh: bool = False) -> list[dict[str, Any]]:
        """Discover all available rules.

        Args:
            force_refresh: If True, bypass cache and re-discover rules.

        Returns:
            List of rule metadata dicts.
        """
        if self._rules_cache is None or force_refresh:
            if force_refresh:
                self._package = None
            package = self._get_package()
            self._rules_cache = [
                {
                    "name": r.name,
                    "path": r.path,
                    "source": r.source,
                }
                for r in package.rules
            ]
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
        package = self._get_package()
        return package.run(hooks_data, transcript, timeout)

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
        package = self._get_package()
        rule = package.get(rule_name)
        if not rule:
            skill_log(f"Rule not found: {rule_name}")
            return None

        result = rule.run(hooks_data, transcript)
        return result if result.trigger else None

    def get_rules_summary(self) -> list[dict[str, str]]:
        """Get a summary of all rules for logging/debugging.

        Returns:
            List of dicts with rule name, source, and path.
        """
        package = self._get_package()
        return package.get_summary()

    def load_rule(self, rule: "ActivationRule") -> None:
        """Load a rule into this engine's package.

        Copies the rule to the project rules directory and adds it to the package.

        Args:
            rule: ActivationRule to load.
        """
        import shutil

        package = self._get_package()

        # Determine target directory - always construct the path, don't rely on get_project_rules_dir
        # which returns None if the directory doesn't exist yet
        if self.project_dir:
            rules_base = Path(self.project_dir) / ".flow" / "skill_rules"
        else:
            rules_base = get_user_rules_dir()

        target_dir = rules_base / rule.name

        # Ensure parent directory exists
        target_dir.parent.mkdir(parents=True, exist_ok=True)

        # Copy rule files
        if target_dir.exists():
            shutil.rmtree(target_dir)
        shutil.copytree(rule.path, target_dir)

        # Reload rule from new location and add to package
        new_rule = ActivationRule.from_md(target_dir)
        new_rule.source = "project" if self.project_dir else "user"

        # Add to package (or replace if exists)
        if rule.name in package:
            package.remove_rule(rule.name)
        package.add_rule(new_rule)

        # Invalidate cache
        self._rules_cache = None


def create_rule_engine(project_dir: str | None = None) -> RuleEngine:
    """Create a rule engine instance.

    .. deprecated::
        Use RulesPackage.from_multiple_folders() instead.

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

    .. deprecated::
        Use RulesPackage.from_multiple_folders().run() instead.

    Args:
        hooks_data: Current hook event data.
        transcript: Optional list of transcript entries.
        project_dir: Optional project directory path.

    Returns:
        Combined hook JSON output dict.
    """
    engine = create_rule_engine(project_dir)
    return engine.evaluate_rules(hooks_data, transcript)
