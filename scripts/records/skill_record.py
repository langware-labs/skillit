"""SkillitSkill — a typed record for skills managed by skillit."""

from __future__ import annotations

import re
import shutil
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


def _load_skill_yaml_from_dir(skill_dir: Path) -> dict[str, Any]:
    yaml_sources = [skill_dir / "skill.yaml", skill_dir / "skill.yml"]
    for source in yaml_sources:
        if source.exists():
            return _yaml_load(source.read_text(encoding="utf-8"))

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return {}

    frontmatter = _extract_frontmatter(skill_md.read_text(encoding="utf-8"))
    if not frontmatter:
        return {}
    return _yaml_load(frontmatter)


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
        return _load_skill_yaml_from_dir(record_dir)

    @classmethod
    def init_record(
        cls,
        path_or_data: str | Path | dict[str, Any],
        path: str | Path | None = None,
        indent: int = 2,
    ) -> SkillRecord:
        """Initialize or load a skill record.

        Adds skill-aware bootstrap behavior: when loading from a folder that has
        no ``record.json`` but has skill metadata (e.g. ``SKILL.md`` frontmatter),
        create ``record.json`` from that metadata.
        """
        if isinstance(path_or_data, dict):
            return super().init_record(path_or_data, path, indent=indent)  # type: ignore[return-value]

        p = Path(path_or_data)
        record_file = p / "record.json" if p.is_dir() else p
        if record_file.exists():
            return super().init_record(path_or_data, path, indent=indent)  # type: ignore[return-value]

        if not p.is_dir():
            return super().init_record(path_or_data, path, indent=indent)  # type: ignore[return-value]

        yaml_fields = _load_skill_yaml_from_dir(p)
        yaml_name = yaml_fields.get("name")
        if isinstance(yaml_name, str) and yaml_name.strip():
            skill_name = yaml_name.strip()
        else:
            skill_name = p.name.split("-@", 1)[-1] if "-@" in p.name else p.name

        data: dict[str, Any] = {
            "id": skill_name,
            "name": skill_name,
            "status": "active",
        }
        if isinstance(yaml_fields.get("description"), str):
            data["description"] = yaml_fields["description"]
        if yaml_fields:
            data["metadata"] = yaml_fields
        return super().init_record(data, p, indent=indent)  # type: ignore[return-value]

    @classmethod
    def load_record(cls, path: str | Path) -> SkillRecord:
        """Backward-compatible alias for loading by path."""
        return cls.init_record(path)

    def copy_to_claude_user_home(self) -> Path:
        """Copy this skill folder into ~/.claude/skills/<skill-name>/."""
        destination_root = Path.home() / ".claude" / "skills"
        return self.copy_to(destination_root)

    def copy_to_project(self, project_dir: str | Path) -> Path:
        """Copy this skill folder into <project>/.claude/skills/<skill-name>/."""
        destination_root = Path(project_dir) / ".claude" / "skills"
        return self.copy_to(destination_root)

    def copy_to(self, destination_root: Path) -> Path:
        """Copy this skill folder into <destination_root>/<skill-name>/."""
        source_dir = self.record_dir
        if source_dir is None:
            raise ValueError("Skill record has no source directory")
        if not (source_dir / "SKILL.md").exists():
            raise FileNotFoundError(f"Missing SKILL.md in {source_dir}")

        yaml_name = self.yaml_fields.get("name")
        if isinstance(yaml_name, str) and yaml_name.strip():
            skill_name = yaml_name.strip()
        else:
            skill_name = self.name or self.id or source_dir.name

        destination_root.mkdir(parents=True, exist_ok=True)
        destination = destination_root / skill_name

        if destination.exists():
            shutil.rmtree(destination)

        shutil.copytree(
            source_dir,
            destination,
            ignore=shutil.ignore_patterns("record.json"),
        )
        return destination

    def __getattr__(self, item: str) -> Any:
        yaml_data = self.yaml_fields
        if item in yaml_data:
            return yaml_data[item]
        raise AttributeError(f"{self.__class__.__name__!s} has no attribute {item!r}")
