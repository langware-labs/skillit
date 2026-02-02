"""Resource management library entry point."""

from .agent.claude import AgentResource, CommandResource, HookResource, McpServerResource, SkillResource
from .api import ApiResource, Scope
from .fs import FsEntity, FsRecord, FsStorage, ScopeResolver, type_registry
from .scan import get_resource_summary, list_projects_fast, scan_full, scan_item, scan_project, scan_resources

__all__ = [
    "ApiResource",
    "Scope",
    "FsEntity",
    "FsRecord",
    "FsStorage",
    "ScopeResolver",
    "HookResource",
    "McpServerResource",
    "CommandResource",
    "AgentResource",
    "SkillResource",
    "type_registry",
    "scan_full",
    "scan_item",
    "scan_resources",
    "scan_project",
    "list_projects_fast",
    "get_resource_summary",
]
