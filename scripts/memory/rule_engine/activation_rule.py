"""ActivationRule class for individual rule management."""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from log import skill_log
from .trigger_executor import TriggerResult, Action, _convert_actions_to_result


@dataclass
class ActivationRuleHeader:
    """Metadata header for an activation rule."""

    name: str
    if_condition: str = ""
    then_action: str = ""
    hook_events: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    source: str = ""
    description: str = ""
    created: str = ""


class ActivationRule:
    """Represents a single activation rule loaded from disk.

    A rule consists of:
    - rule.md: Metadata describing the rule (IF/THEN, hook events, etc.)
    - trigger.py: Python script that evaluates whether the rule triggers
    """

    def __init__(self, path: Path, header: ActivationRuleHeader | None = None):
        """Initialize an ActivationRule.

        Args:
            path: Path to the rule directory containing rule.md and trigger.py.
            header: Optional pre-loaded header. If None, will be loaded from rule.md.
        """
        self._path = path
        self._header = header or ActivationRuleHeader(name=path.name)

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def name(self) -> str:
        """Rule name (directory name)."""
        return self._header.name

    @name.setter
    def name(self, value: str) -> None:
        self._header.name = value

    @property
    def if_condition(self) -> str:
        """IF condition describing when the rule triggers."""
        return self._header.if_condition

    @if_condition.setter
    def if_condition(self, value: str) -> None:
        self._header.if_condition = value

    @property
    def then_action(self) -> str:
        """THEN action describing what happens when triggered."""
        return self._header.then_action

    @then_action.setter
    def then_action(self, value: str) -> None:
        self._header.then_action = value

    @property
    def hook_events(self) -> list[str]:
        """List of hook events this rule responds to."""
        return self._header.hook_events

    @hook_events.setter
    def hook_events(self, value: list[str]) -> None:
        self._header.hook_events = value

    @property
    def actions(self) -> list[str]:
        """List of action types this rule can perform."""
        return self._header.actions

    @actions.setter
    def actions(self, value: list[str]) -> None:
        self._header.actions = value

    @property
    def source(self) -> str:
        """Source identifier (user, project, etc.)."""
        return self._header.source

    @source.setter
    def source(self, value: str) -> None:
        self._header.source = value

    @property
    def description(self) -> str:
        """Human-readable description of the rule."""
        return self._header.description

    @description.setter
    def description(self, value: str) -> None:
        self._header.description = value

    @property
    def created(self) -> str:
        """Creation date of the rule."""
        return self._header.created

    @created.setter
    def created(self, value: str) -> None:
        self._header.created = value

    @property
    def path(self) -> Path:
        """Path to the rule directory."""
        return self._path

    @property
    def header(self) -> ActivationRuleHeader:
        """The rule's header metadata."""
        return self._header

    # -------------------------------------------------------------------------
    # Class Methods
    # -------------------------------------------------------------------------

    @classmethod
    def from_md(cls, path: Path) -> "ActivationRule":
        """Load an ActivationRule from a rule directory.

        Args:
            path: Path to the rule directory containing rule.md.

        Returns:
            ActivationRule instance with parsed header.
        """
        rule_md = path / "rule.md"
        header = ActivationRuleHeader(name=path.name)

        if rule_md.exists():
            header = cls._parse_rule_md(rule_md, path.name)

        return cls(path=path, header=header)

    @classmethod
    def _parse_rule_md(cls, rule_md: Path, rule_name: str) -> ActivationRuleHeader:
        """Parse rule.md file into an ActivationRuleHeader.

        Supports two formats:
        1. YAML front matter (preferred): name/description in YAML, body has Issue/Triggers/Actions
        2. Legacy markdown format with **IF**/**THEN** bullet points

        Args:
            rule_md: Path to the rule.md file.
            rule_name: Name of the rule (directory name).

        Returns:
            Parsed ActivationRuleHeader.
        """
        content = rule_md.read_text(encoding="utf-8")
        header = ActivationRuleHeader(name=rule_name)

        # Check for YAML front matter
        if content.startswith("---"):
            return cls._parse_yaml_format(content, rule_name)

        # Fall back to legacy format
        return cls._parse_legacy_format(content, rule_name)

    @classmethod
    def _parse_yaml_format(cls, content: str, rule_name: str) -> ActivationRuleHeader:
        """Parse rule.md with YAML front matter format."""
        import yaml

        header = ActivationRuleHeader(name=rule_name)

        # Split front matter from body
        parts = content.split("---", 2)
        if len(parts) >= 3:
            yaml_content = parts[1].strip()
            body = parts[2].strip()

            # Parse YAML
            try:
                meta = yaml.safe_load(yaml_content) or {}
                header.name = meta.get("name", rule_name)
                header.description = meta.get("description", "")
            except yaml.YAMLError:
                pass

            # Parse markdown body sections
            current_section: str | None = None
            section_content: list[str] = []

            for line in body.split("\n"):
                line_lower = line.lower().strip()

                if line_lower.startswith("## issue"):
                    if current_section and section_content:
                        cls._store_yaml_section(header, current_section, section_content)
                    current_section = "issue"
                    section_content = []
                elif line_lower.startswith("## trigger"):
                    if current_section and section_content:
                        cls._store_yaml_section(header, current_section, section_content)
                    current_section = "triggers"
                    section_content = []
                elif line_lower.startswith("## action"):
                    if current_section and section_content:
                        cls._store_yaml_section(header, current_section, section_content)
                    current_section = "actions"
                    section_content = []
                elif line_lower.startswith("##"):
                    if current_section and section_content:
                        cls._store_yaml_section(header, current_section, section_content)
                    current_section = None
                    section_content = []
                elif current_section:
                    section_content.append(line)

            if current_section and section_content:
                cls._store_yaml_section(header, current_section, section_content)

        return header

    @classmethod
    def _store_yaml_section(cls, header: ActivationRuleHeader, section: str, content: list[str]) -> None:
        """Store parsed YAML format section into header."""
        text = "\n".join(content).strip()

        if section == "issue":
            # Store issue as the IF condition
            header.if_condition = text
        elif section == "triggers":
            # Parse hook events and conditions from triggers section
            header.then_action = text
            # Extract hook events if mentioned
            for line in content:
                line_lower = line.lower()
                if "hook" in line_lower and ":" in line:
                    events_part = line.split(":", 1)[1].strip()
                    header.hook_events = [e.strip() for e in events_part.split(",") if e.strip()]
        elif section == "actions":
            # Extract action types from actions section
            action_types = []
            for line in content:
                if "add_context" in line.lower():
                    action_types.append("add_context")
                if "block" in line.lower():
                    action_types.append("block")
                if "modify" in line.lower():
                    action_types.append("modify_input")
            header.actions = list(dict.fromkeys(action_types))  # dedupe preserving order

    @classmethod
    def _parse_legacy_format(cls, content: str, rule_name: str) -> ActivationRuleHeader:
        """Parse legacy rule.md format with **IF**/**THEN** bullet points."""
        header = ActivationRuleHeader(name=rule_name)
        lines = content.split("\n")
        current_section: str | None = None
        section_content: list[str] = []

        for line in lines:
            line_lower = line.lower().strip()

            if line_lower.startswith("**if**:") or line_lower.startswith("- **if**:"):
                if current_section and section_content:
                    cls._store_section(header, current_section, section_content)
                current_section = "if_condition"
                content_after = line.split(":", 1)[1].strip() if ":" in line else ""
                section_content = [content_after] if content_after else []
            elif line_lower.startswith("**then**:") or line_lower.startswith("- **then**:"):
                if current_section and section_content:
                    cls._store_section(header, current_section, section_content)
                current_section = "then_action"
                content_after = line.split(":", 1)[1].strip() if ":" in line else ""
                section_content = [content_after] if content_after else []
            elif line_lower.startswith("**hook events**:") or line_lower.startswith("- **hook events**:"):
                if current_section and section_content:
                    cls._store_section(header, current_section, section_content)
                current_section = "hook_events"
                content_after = line.split(":", 1)[1].strip() if ":" in line else ""
                section_content = [content_after] if content_after else []
            elif line_lower.startswith("**actions**:") or line_lower.startswith("- **actions**:"):
                if current_section and section_content:
                    cls._store_section(header, current_section, section_content)
                current_section = "actions"
                content_after = line.split(":", 1)[1].strip() if ":" in line else ""
                section_content = [content_after] if content_after else []
            elif line_lower.startswith("**source**:") or line_lower.startswith("- **source**:"):
                if current_section and section_content:
                    cls._store_section(header, current_section, section_content)
                current_section = "source"
                content_after = line.split(":", 1)[1].strip() if ":" in line else ""
                section_content = [content_after] if content_after else []
            elif line_lower.startswith("**created**:") or line_lower.startswith("- **created**:"):
                if current_section and section_content:
                    cls._store_section(header, current_section, section_content)
                current_section = "created"
                content_after = line.split(":", 1)[1].strip() if ":" in line else ""
                section_content = [content_after] if content_after else []
            elif line_lower.startswith("#"):
                if current_section and section_content:
                    cls._store_section(header, current_section, section_content)
                current_section = None
                section_content = []
                if "description" in line_lower:
                    current_section = "description"
            elif current_section:
                section_content.append(line)

        if current_section and section_content:
            cls._store_section(header, current_section, section_content)

        return header

    @classmethod
    def _store_section(cls, header: ActivationRuleHeader, section: str, content: list[str]) -> None:
        """Store parsed section content into header."""
        text = "\n".join(content).strip()

        if section == "hook_events":
            header.hook_events = [e.strip() for e in text.split(",") if e.strip()]
        elif section == "actions":
            header.actions = [a.strip() for a in text.split(",") if a.strip()]
        elif section == "if_condition":
            header.if_condition = text
        elif section == "then_action":
            header.then_action = text
        elif section == "source":
            header.source = text
        elif section == "description":
            header.description = text
        elif section == "created":
            header.created = text

    # -------------------------------------------------------------------------
    # Instance Methods
    # -------------------------------------------------------------------------

    def to_md(self) -> str:
        """Serialize the rule to markdown format with YAML front matter.

        Returns:
            Markdown string representation of the rule.
        """
        hook_events_str = ", ".join(self._header.hook_events) if self._header.hook_events else ""
        actions_lines = []
        for action in self._header.actions:
            if action == "add_context":
                actions_lines.append("- `add_context`: Injects guidance into Claude's context")
            elif action == "block":
                actions_lines.append("- `block`: Prevents the action with a reason")
            elif action == "modify_input":
                actions_lines.append("- `modify_input`: Changes tool input before execution")
            else:
                actions_lines.append(f"- `{action}`")

        lines = [
            "---",
            f"name: {self._header.name}",
            f"description: {self._header.description}",
            "---",
            "",
            "## Issue",
            "",
            self._header.if_condition or "No issue specified.",
            "",
            "## Triggers",
            "",
            f"- Hook events: {hook_events_str}" if hook_events_str else "- Hook events: All",
            "",
            "## Actions",
            "",
        ]
        lines.extend(actions_lines if actions_lines else ["- None specified"])
        lines.append("")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Convert rule to dictionary representation.

        Returns:
            Dict with rule metadata.
        """
        return {
            "name": self._header.name,
            "if_condition": self._header.if_condition,
            "then_action": self._header.then_action,
            "hook_events": self._header.hook_events,
            "actions": self._header.actions,
            "source": self._header.source,
            "description": self._header.description,
            "created": self._header.created,
            "path": str(self._path),
        }

    def run(
        self,
        hooks_data: dict[str, Any],
        transcript: list[dict[str, Any]] | None = None,
        timeout: float = 5.0,
    ) -> TriggerResult:
        """Execute the rule's trigger.py module.

        Args:
            hooks_data: Current hook event data.
            transcript: Optional list of transcript entries.
            timeout: Maximum execution time in seconds (unused, kept for API compatibility).

        Returns:
            TriggerResult with parsed output or error information.
        """
        trigger_file = self._path / "trigger.py"

        if not trigger_file.exists():
            return TriggerResult(
                rule_name=self.name,
                error=f"trigger.py not found at {trigger_file}",
            )

        try:
            # Import trigger.py as a module
            spec = importlib.util.spec_from_file_location(
                f"trigger_{self.name}",
                trigger_file,
            )
            if spec is None or spec.loader is None:
                return TriggerResult(
                    rule_name=self.name,
                    error=f"Could not load trigger.py from {trigger_file}",
                )

            module = importlib.util.module_from_spec(spec)

            # Add rule_path to sys.path temporarily for relative imports
            original_path = sys.path.copy()
            sys.path.insert(0, str(self._path))
            try:
                spec.loader.exec_module(module)
            finally:
                sys.path = original_path

            # Check for evaluate() function
            if not hasattr(module, "evaluate"):
                return TriggerResult(
                    rule_name=self.name,
                    error=f"trigger.py missing evaluate() function",
                )

            # Call evaluate(hooks_data, transcript)
            result = module.evaluate(hooks_data, transcript or [])

            # Convert Action(s) to TriggerResult
            return _convert_actions_to_result(result, self.name)

        except Exception as e:
            return TriggerResult(
                rule_name=self.name,
                error=f"Error executing trigger.py: {e}",
            )

    def is_valid(self) -> bool:
        """Check if the rule has a valid trigger.py file.

        Returns:
            True if trigger.py exists.
        """
        trigger_file = self._path / "trigger.py"
        return trigger_file.exists()

    def __repr__(self) -> str:
        return f"ActivationRule(name={self.name!r}, path={self._path!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ActivationRule):
            return NotImplemented
        return self.name == other.name and self._path == other._path
