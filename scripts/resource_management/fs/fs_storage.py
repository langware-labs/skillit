"""Filesystem storage helpers for entities."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from .scope_resolver import ScopeResolver


class FsStorage:
    def __init__(self, resolver: ScopeResolver | None = None) -> None:
        self._resolver = resolver or ScopeResolver()

    @property
    def resolver(self) -> ScopeResolver:
        return self._resolver

    def entity_dir(self, scope: str, typeid: str) -> Path:
        return self._resolver.entity_dir(scope, typeid)

    def entity_json_path(self, entity_dir: Path) -> Path:
        return entity_dir / "entity.json"

    def read(self, entity_dir: Path) -> dict | None:
        json_path = self.entity_json_path(entity_dir)
        if not json_path.exists():
            return None
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            return None

    def write(self, entity_dir: Path, data: dict) -> Path:
        entity_dir.mkdir(parents=True, exist_ok=True)
        json_path = self.entity_json_path(entity_dir)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
        return json_path

    def delete(self, entity_dir: Path) -> bool:
        if not entity_dir.exists():
            return False
        try:
            shutil.rmtree(entity_dir)
            return True
        except OSError:
            return False
