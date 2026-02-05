"""Scope-to-path resolution for filesystem entities."""

from __future__ import annotations

import os
import platform
from pathlib import Path

from ..api import Scope


class DefaultPathResolver:
    def home(self) -> Path:
        return Path.home()

    def cwd(self) -> Path:
        return Path.cwd()

    def env(self, key: str) -> str | None:
        return os.environ.get(key)


class ScopeResolver:
    """Resolve scope to entity roots.

    Layout (default):
    - user: ~/.claude/flowpad/entities
    - project: {project_root}/.claude/flowpad/entities
    - local: {project_root}/.claude/flowpad/entities.local
    - managed: platform-specific app support
    """

    def __init__(self, path_resolver: DefaultPathResolver | None = None, project_root: Path | None = None) -> None:
        self._resolver = path_resolver or DefaultPathResolver()
        self._project_root = project_root

    @property
    def project_root(self) -> Path:
        if self._project_root:
            return self._project_root
        cwd = self._resolver.cwd()
        for parent in [cwd] + list(cwd.parents):
            if (parent / ".claude").exists():
                return parent
        return cwd

    def _user_root(self) -> Path:
        env_override = self._resolver.env("FLOWPAD_USER_ENTITIES")
        if env_override:
            return Path(env_override)
        return self._resolver.home() / ".claude" / "flowpad" / "entities"

    def _project_root_entities(self) -> Path:
        env_override = self._resolver.env("FLOWPAD_PROJECT_ENTITIES")
        if env_override:
            return Path(env_override)
        return self.project_root / ".claude" / "flowpad" / "entities"

    def _local_root_entities(self) -> Path:
        env_override = self._resolver.env("FLOWPAD_LOCAL_ENTITIES")
        if env_override:
            return Path(env_override)
        return self.project_root / ".claude" / "flowpad" / "entities.local"

    def _managed_root(self) -> Path:
        env_override = self._resolver.env("FLOWPAD_MANAGED_ENTITIES")
        if env_override:
            return Path(env_override)
        system = platform.system().lower()
        if system == "darwin":
            return Path("/Library/Application Support/FlowPad/entities")
        if system == "windows":
            appdata = self._resolver.env("APPDATA") or str(self._resolver.home() / "AppData" / "Roaming")
            return Path(appdata) / "FlowPad" / "entities"
        return Path("/etc/flowpad/entities")

    def root_for_scope(self, scope: Scope | str) -> Path:
        scope_value = scope.value if isinstance(scope, Scope) else scope
        if scope_value in (Scope.USER.value, Scope.GLOBAL.value, Scope.LEGACY.value):
            return self._user_root()
        if scope_value == Scope.PROJECT.value:
            return self._project_root_entities()
        if scope_value == Scope.LOCAL.value:
            return self._local_root_entities()
        if scope_value == Scope.MANAGED.value:
            return self._managed_root()
        return self._user_root()

    def roots_for_scope(self, scope: Scope | str | None = None) -> list[Path]:
        if scope is None:
            return [
                self._user_root(),
                self._project_root_entities(),
                self._local_root_entities(),
                self._managed_root(),
            ]
        return [self.root_for_scope(scope)]

    def entity_dir(self, scope: Scope | str, typeid: str) -> Path:
        return self.root_for_scope(scope) / typeid
