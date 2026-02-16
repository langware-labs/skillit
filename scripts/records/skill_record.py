"""SkillitSkill — a typed record for skills managed by skillit."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fs_store import FsRecord, RecordType


def _coerce_scalar(value: str) -> Any:
    raw = value.strip()
    if raw.startswith('"') and raw.endswith('"') and len(raw) >= 2:
        return raw[1:-1]
    if raw.startswith("'") and raw.endswith("'") and len(raw) >= 2:
        return raw[1:-1]
    low = raw.lower()
    if low in {"true", "false"}:
        return low == "true"
    if low in {"null", "none", "~"}:
        return None
    if re.fullmatch(r"-?\d+", raw):
        try:
            return int(raw)
        except ValueError:
            return raw
    if re.fullmatch(r"-?\d+\.\d+", raw):
        try:
            return float(raw)
        except ValueError:
            return raw
    return raw


def _parse_simple_yaml_map(text: str) -> dict[str, Any]:
    """Parse a small YAML mapping subset for environments without PyYAML."""
    data: dict[str, Any] = {}
    lines = text.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        i += 1
        if not stripped or stripped.startswith("#") or ":" not in line:
            continue

        key, raw_value = line.split(":", 1)
        key = key.strip()
        value = raw_value.strip()

        if value in {">", "|"}:
            block: list[str] = []
            while i < len(lines):
                next_line = lines[i]
                if re.match(r"^[A-Za-z_][A-Za-z0-9_-]*\s*:", next_line):
                    break
                if next_line.startswith("  "):
                    block.append(next_line[2:])
                    i += 1
                    continue
                if next_line.strip() == "":
                    block.append("")
                    i += 1
                    continue
                break
            block_text = "\n".join(block).strip()
            if value == ">":
                block_text = " ".join(part.strip() for part in block_text.splitlines() if part.strip())
            data[key] = block_text
            continue

        data[key] = _coerce_scalar(value)

    return data


def _yaml_load(text: str) -> dict[str, Any]:
    try:
        import yaml  # type: ignore

        parsed = yaml.safe_load(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    return _parse_simple_yaml_map(text)


def _extract_frontmatter(text: str) -> str | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None

    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i]).strip()
    return None


@dataclass
class SkillRecord(FsRecord):
    """A skill record backed by FsRecord.

    Each skill is stored as
    ``~/.flow/records/skill/skill-@<id>/record.json``
    using the FOLDER storage layout.
    """

    name: str = ""
    description: str = ""
    status: str = "active"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.type:
            self.type = RecordType.SKILL
        if self.name and not self.id:
            self.id = self.name

    @property
    def yaml_fields(self) -> dict[str, Any]:
        """Load YAML metadata from skill.yaml/skill.yml or SKILL.md frontmatter."""
        record_dir = self.record_dir
        if record_dir is None:
            return {}

        yaml_sources = [record_dir / "skill.yaml", record_dir / "skill.yml"]
        for source in yaml_sources:
            if source.exists():
                return _yaml_load(source.read_text(encoding="utf-8"))

        skill_md = record_dir / "SKILL.md"
        if not skill_md.exists():
            return {}

        frontmatter = _extract_frontmatter(skill_md.read_text(encoding="utf-8"))
        if not frontmatter:
            return {}
        return _yaml_load(frontmatter)

    def __getattr__(self, item: str) -> Any:
        yaml_data = self.yaml_fields
        if item in yaml_data:
            return yaml_data[item]
        raise AttributeError(f"{self.__class__.__name__!s} has no attribute {item!r}")
