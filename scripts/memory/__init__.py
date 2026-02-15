"""Memory module for skill rules and transcript replay."""

# Types (from types/)
from .types import (
    HookEvent,
    HookEventType,
)

# Rule engine (from rule_engine/)
from .rule_engine import (
    # Core classes
    ActivationRule,
    ActivationRuleHeader,
    RulesPackage,
    RuleEngine,
    # Trigger/Action system
    Action,
    TriggerResult,
    ActionExecutor,
    ActionResult,
    execute_actions,
    format_hook_output,
    # Factory functions
    create_rule_engine,
    evaluate_hooks_with_rules,
    # Rule loader
    discover_rules,
    ensure_rules_dir,
    get_rules_dir,
    get_system_rules_dir,
    get_user_rules_dir,
    get_project_rules_dir,
    load_rule_metadata,
    # Index manager
    IndexManager,
    get_index_manager,
    # Field extractor
    extract_field,
    get_tool_info,
    get_hook_event,
    get_user_prompt,
    is_tool_match,
    get_bash_command,
    get_file_operation,
    # Regex utilities
    compile_regex,
    regex_match,
    regex_match_ignorecase,
    contains,
    starts_with,
    ends_with,
    matches_any,
    extract_match,
    word_boundary_match,
)

__all__ = [
    # Core types (types/)
    "HookEvent",
    "HookEventType",
    # Rule engine classes (rule_engine/)
    "ActivationRule",
    "ActivationRuleHeader",
    "RulesPackage",
    "RuleEngine",
    # Trigger/Action system
    "Action",
    "TriggerResult",
    "ActionExecutor",
    "ActionResult",
    "execute_actions",
    "format_hook_output",
    # Factory functions
    "create_rule_engine",
    "evaluate_hooks_with_rules",
    # Rule loader
    "discover_rules",
    "ensure_rules_dir",
    "get_rules_dir",
    "get_system_rules_dir",
    "get_user_rules_dir",
    "get_project_rules_dir",
    "load_rule_metadata",
    # Index manager
    "IndexManager",
    "get_index_manager",
    # Field extractor
    "extract_field",
    "get_tool_info",
    "get_hook_event",
    "get_user_prompt",
    "is_tool_match",
    "get_bash_command",
    "get_file_operation",
    # Regex utilities
    "compile_regex",
    "regex_match",
    "regex_match_ignorecase",
    "contains",
    "starts_with",
    "ends_with",
    "matches_any",
    "extract_match",
    "word_boundary_match",
]
