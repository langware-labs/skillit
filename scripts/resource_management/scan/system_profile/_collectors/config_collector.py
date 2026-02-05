"""Config collector - hooks, MCP servers, commands, agents, skills."""

import hashlib
import sys
from pathlib import Path

# Add parent directory to path for standalone execution
sys.path.insert(0, str(Path(__file__).parent.parent))

from _collectors.project_collector import (
    get_project_cwd,
)
from settings import (
    get_legacy_settings,
)
from utils import (
    CLAUDE_HOME,
    HOME,
    get_file_mtime,
    load_json,
)

try:
    from flowpad.hub.core.resource_management.agent.claude import (
        AgentResource,
        CommandResource,
        HookResource,
        McpServerResource,
        SkillResource,
    )

    _RESOURCE_MGMT_AVAILABLE = True
except Exception:
    _RESOURCE_MGMT_AVAILABLE = False


def _fs_entities_to_items(entities: list) -> list[dict]:
    items: list[dict] = []
    for entity in entities:
        try:
            items.append(entity.model_dump(mode="json"))
        except Exception:
            continue
    return items


def _merge_items(primary: list[dict], secondary: list[dict]) -> list[dict]:
    seen = {item.get("id") for item in primary if item.get("id") is not None}
    for item in secondary:
        item_id = item.get("id")
        if item_id is None or item_id not in seen:
            primary.append(item)
            if item_id is not None:
                seen.add(item_id)
    return primary


def get_hooks_from_settings(settings: dict, scope: str, source_file: str) -> list[dict]:
    """Extract hooks from a settings dict."""
    hooks = []
    if not settings or "hooks" not in settings:
        return hooks

    for event_type, hook_list in settings["hooks"].items():
        if isinstance(hook_list, list):
            for hook_entry in hook_list:
                matcher = hook_entry.get("matcher", "*")
                for h in hook_entry.get("hooks", []):
                    command = h.get("command", "")
                    hook_type = h.get("type", "command")
                    matcher_hash = hashlib.md5(f"{matcher}:{command}".encode()).hexdigest()[:8]
                    hooks.append(
                        {
                            "id": f"{scope}:{event_type}:{matcher_hash}",
                            "type": "hook",
                            "name": f"{event_type} ({matcher})",
                            "scope": scope,
                            "source_file": source_file,
                            "modified_at": get_file_mtime(Path(source_file)),
                            "event_type": event_type,
                            "matcher": matcher,
                            "command": command,
                            "hook_type": hook_type,
                        }
                    )
    return hooks


def get_hooks_from_folder(folder: Path, scope: str) -> list[dict]:
    """Get hooks from settings files in a folder."""
    hooks = []
    settings_path = folder / "settings.json"
    if settings_path.exists():
        data = load_json(settings_path)
        if data:
            hooks.extend(get_hooks_from_settings(data, scope, str(settings_path)))

    local_path = folder / "settings.local.json"
    if local_path.exists():
        data = load_json(local_path)
        if data:
            hooks.extend(get_hooks_from_settings(data, "local", str(local_path)))
    return hooks


def get_all_hooks() -> list[dict]:
    """Get all hooks from user and all projects."""
    all_hooks: list[dict] = []

    if _RESOURCE_MGMT_AVAILABLE:
        all_hooks.extend(_fs_entities_to_items(HookResource.get_all()))

    _merge_items(all_hooks, get_hooks_from_folder(CLAUDE_HOME, "user"))

    legacy_path = HOME / ".claude.json"
    if legacy_path.exists():
        data = load_json(legacy_path)
        if data:
            _merge_items(all_hooks, get_hooks_from_settings(data, "legacy", str(legacy_path)))

    projects_dir = CLAUDE_HOME / "projects"
    if projects_dir.exists():
        for project_dir in projects_dir.iterdir():
            if not project_dir.is_dir():
                continue
            cwd = get_project_cwd(project_dir)
            if not cwd:
                continue
            project_path = Path(cwd)
            if not project_path.exists():
                continue

            _merge_items(all_hooks, get_hooks_from_folder(project_path / ".claude", "project"))

    return all_hooks


def get_mcp_servers_from_file(mcp_path: Path, scope: str) -> list[dict]:
    """Get MCP servers from a specific file."""
    servers = []
    data = load_json(mcp_path)
    if data and "mcpServers" in data:
        for name, config in data["mcpServers"].items():
            servers.append(
                {
                    "id": f"{mcp_path}:{name}",
                    "type": "mcp_server",
                    "name": name,
                    "scope": scope,
                    "source_file": str(mcp_path),
                    "modified_at": get_file_mtime(mcp_path),
                    "command": config.get("command", ""),
                    "args": config.get("args", []),
                    "env": config.get("env", {}),
                }
            )
    return servers


def get_mcp_servers_from_folder(folder: Path, scope: str) -> list[dict]:
    """Get MCP servers from mcp.json or .mcp.json in a folder."""
    servers = []
    for filename in ["mcp.json", ".mcp.json"]:
        mcp_path = folder / filename
        if mcp_path.exists():
            servers.extend(get_mcp_servers_from_file(mcp_path, scope))
    return servers


def get_mcp_servers() -> list[dict]:
    """Get all MCP server configurations from user and all projects."""
    servers: list[dict] = []
    seen_names = set()

    if _RESOURCE_MGMT_AVAILABLE:
        for server in _fs_entities_to_items(McpServerResource.get_all()):
            servers.append(server)
            if server.get("name"):
                seen_names.add(server["name"])

    for server in get_mcp_servers_from_file(HOME / ".mcp.json", "user"):
        servers.append(server)
        seen_names.add(server["name"])

    for server in get_mcp_servers_from_folder(CLAUDE_HOME, "user"):
        if server["name"] not in seen_names:
            servers.append(server)
            seen_names.add(server["name"])

    legacy_settings = get_legacy_settings()
    if legacy_settings and "mcpServers" in legacy_settings:
        for name, config in legacy_settings.get("mcpServers", {}).items():
            if name in seen_names:
                continue
            seen_names.add(name)
            servers.append(
                {
                    "id": f"{HOME / '.claude.json'}:{name}",
                    "type": "mcp_server",
                    "name": name,
                    "scope": "user",
                    "source_file": str(HOME / ".claude.json"),
                    "modified_at": get_file_mtime(HOME / ".claude.json"),
                    "command": config.get("command", ""),
                    "args": config.get("args", []),
                    "env": config.get("env", {}),
                }
            )

    projects_dir = CLAUDE_HOME / "projects"
    if projects_dir.exists():
        for project_dir in projects_dir.iterdir():
            if not project_dir.is_dir():
                continue
            cwd = get_project_cwd(project_dir)
            if not cwd:
                continue
            project_path = Path(cwd)
            if not project_path.exists():
                continue

            for server in get_mcp_servers_from_file(project_path / ".mcp.json", "project"):
                if server["name"] not in seen_names:
                    servers.append(server)
                    seen_names.add(server["name"])

            for server in get_mcp_servers_from_folder(project_path / ".claude", "project"):
                if server["name"] not in seen_names:
                    servers.append(server)
                    seen_names.add(server["name"])

    return servers


def get_commands_from_folder(folder: Path, scope: str) -> list[dict]:
    """Get commands from a specific folder."""
    commands = []
    commands_dir = folder / "commands"
    if commands_dir.exists():
        for f in commands_dir.glob("*.md"):
            commands.append(
                {
                    "id": f"{scope}:{f.stem}:{folder}",
                    "type": "command",
                    "name": f.stem,
                    "scope": scope,
                    "source_file": str(f),
                    "path": str(f),
                    "modified_at": get_file_mtime(f),
                }
            )
    return commands


def get_commands() -> list[dict]:
    """Get all custom commands (global and from all projects)."""
    commands: list[dict] = []
    seen = set()

    if _RESOURCE_MGMT_AVAILABLE:
        for cmd in _fs_entities_to_items(CommandResource.get_all()):
            commands.append(cmd)
            if cmd.get("name"):
                seen.add(cmd["name"])

    for cmd in get_commands_from_folder(CLAUDE_HOME, "global"):
        commands.append(cmd)
        seen.add(cmd["name"])

    projects_dir = CLAUDE_HOME / "projects"
    if projects_dir.exists():
        for project_dir in projects_dir.iterdir():
            if not project_dir.is_dir():
                continue
            cwd = get_project_cwd(project_dir)
            if not cwd:
                continue
            project_path = Path(cwd)
            if not project_path.exists():
                continue

            for cmd in get_commands_from_folder(project_path / ".claude", "project"):
                if cmd["name"] not in seen:
                    commands.append(cmd)
                    seen.add(cmd["name"])

    return commands


def get_agents_from_folder(folder: Path, scope: str) -> list[dict]:
    """Get agents from a specific folder."""
    agents = []
    agents_dir = folder / "agents"
    if agents_dir.exists():
        for f in agents_dir.glob("*.md"):
            agents.append(
                {
                    "id": f"{scope}:{f.stem}:{folder}",
                    "type": "agent",
                    "name": f.stem,
                    "scope": scope,
                    "source_file": str(f),
                    "path": str(f),
                    "modified_at": get_file_mtime(f),
                }
            )
    return agents


def get_agents() -> list[dict]:
    """Get all custom agents (global and from all projects)."""
    agents: list[dict] = []
    seen = set()

    if _RESOURCE_MGMT_AVAILABLE:
        for agent in _fs_entities_to_items(AgentResource.get_all()):
            agents.append(agent)
            if agent.get("name"):
                seen.add(agent["name"])

    for agent in get_agents_from_folder(CLAUDE_HOME, "global"):
        agents.append(agent)
        seen.add(agent["name"])

    projects_dir = CLAUDE_HOME / "projects"
    if projects_dir.exists():
        for project_dir in projects_dir.iterdir():
            if not project_dir.is_dir():
                continue
            cwd = get_project_cwd(project_dir)
            if not cwd:
                continue
            project_path = Path(cwd)
            if not project_path.exists():
                continue

            for agent in get_agents_from_folder(project_path / ".claude", "project"):
                if agent["name"] not in seen:
                    agents.append(agent)
                    seen.add(agent["name"])

    return agents


def get_skills_from_folder(folder: Path, scope: str) -> list[dict]:
    """Get skills from a specific folder."""
    skills = []
    skills_dir = folder / "skills"
    if skills_dir.exists():
        for item in skills_dir.iterdir():
            skills.append(
                {
                    "id": f"skill:{item.name}:{folder}",
                    "type": "skill",
                    "name": item.name,
                    "scope": scope,
                    "source_file": str(item),
                    "path": str(item),
                    "modified_at": get_file_mtime(item),
                    "usage_count": 0,
                }
            )
    return skills


def get_skills() -> list[dict]:
    """Get installed skills (global and from all projects)."""
    skills: list[dict] = []
    seen = set()

    if _RESOURCE_MGMT_AVAILABLE:
        for skill in _fs_entities_to_items(SkillResource.get_all()):
            skills.append(skill)
            if skill.get("name"):
                seen.add(skill["name"])

    for skill in get_skills_from_folder(CLAUDE_HOME, "user"):
        skills.append(skill)
        seen.add(skill["name"])

    projects_dir = CLAUDE_HOME / "projects"
    if projects_dir.exists():
        for project_dir in projects_dir.iterdir():
            if not project_dir.is_dir():
                continue
            cwd = get_project_cwd(project_dir)
            if not cwd:
                continue
            project_path = Path(cwd)
            if not project_path.exists():
                continue

            for skill in get_skills_from_folder(project_path / ".claude", "project"):
                if skill["name"] not in seen:
                    skills.append(skill)
                    seen.add(skill["name"])

    legacy = get_legacy_settings()
    if legacy and "skillUsage" in legacy:
        usage_map = {name: stats.get("usageCount", 0) for name, stats in legacy["skillUsage"].items()}
        for skill in skills:
            skill["usage_count"] = usage_map.get(skill["name"], 0)

    return skills
