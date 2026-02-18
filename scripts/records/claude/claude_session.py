"""ClaudeSessionFsRecord — represents a Claude Code chat session.

Source: ~/.claude/projects/<encoded-path>/<session-id>.jsonl
Each line is a JSON entry with a shared envelope (sessionId, cwd, version,
gitBranch, slug, timestamp, uuid) plus a type-specific payload.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, Self

from fs_store import FsRecord, RecordType


@dataclass
class ClaudeSessionFsRecord(FsRecord):
    """A single Claude Code chat session.

    Mapped from the JSONL transcript at
    ``~/.claude/projects/<project>/<session-id>.jsonl``.
    """

    session_id: str = ""
    project_path: str = ""
    cwd: str = ""
    version: str = ""
    git_branch: str = ""
    slug: str = ""
    model: str | None = None
    message_count: int = 0
    user_message_count: int = 0
    assistant_message_count: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cost_usd: float = 0.0
    duration_ms: int = 0
    tools_used: list[str] = field(default_factory=list)
    has_plan: bool = False
    jsonl_path: str = ""

    def __post_init__(self):
        if not self.type:
            self.type = RecordType.SESSION
        if self.session_id:
            self.id = self.session_id
            if not self.name:
                self.name = self.slug or self.session_id

    EXCLUDED_ENTRY_TYPES: ClassVar[list[str]] = ["file-history-snapshot", "progress"]

    @property
    def filtered_entries(self) -> list:
        """Return transcript entries with noisy types excluded.

        Uses ``EXCLUDED_ENTRY_TYPES`` as a blocklist.
        """
        return [
            e for e in self.transcript_entries
            if e.entry_type not in self.EXCLUDED_ENTRY_TYPES
        ]

    @property
    def transcript_entries(self) -> list:
        """Lazily load transcript entries from the JSONL file.

        Returns a list of transcript entry records (base or type-specific).
        """
        from .transcript_records import create_transcript_entry

        path = self.jsonl_path or (self.source_file or "")
        if not path or not Path(path).is_file():
            return []
        entries = []
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    raw = json.loads(line)
                except json.JSONDecodeError:
                    continue
                entries.append(create_transcript_entry(raw))
        return entries

    @property
    def summary_log(self) -> str:
        """Newline-joined one-line summaries of filtered transcript entries."""
        return "\n".join(
            f"[{i:4d}]  {e.summary}" for i, e in enumerate(self.filtered_entries, 1)
        )

    @classmethod
    def from_jsonl(cls, path: str | Path) -> Self:
        """Build a session record by parsing a transcript JSONL file.

        Populates envelope fields from the first entry that carries them
        and aggregates message counts and token usage across all entries.
        """
        path = Path(path)
        session_id = ""
        cwd = ""
        version = ""
        git_branch = ""
        slug = ""
        model: str | None = None

        message_count = 0
        user_count = 0
        assistant_count = 0
        input_tokens = 0
        output_tokens = 0
        cache_read = 0
        cache_creation = 0
        duration_ms = 0
        tools: set[str] = set()
        has_plan = False

        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    raw = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Envelope fields — take from first entry that has them
                if not session_id and raw.get("sessionId"):
                    session_id = raw["sessionId"]
                if not cwd and raw.get("cwd"):
                    cwd = raw["cwd"]
                if not version and raw.get("version"):
                    version = raw["version"]
                if not git_branch and raw.get("gitBranch"):
                    git_branch = raw["gitBranch"]
                if not slug and raw.get("slug"):
                    slug = raw["slug"]

                entry_type = raw.get("type", "")

                if entry_type == "user":
                    message_count += 1
                    user_count += 1
                    if raw.get("planContent"):
                        has_plan = True

                elif entry_type == "assistant":
                    message_count += 1
                    assistant_count += 1
                    msg = raw.get("message") or {}
                    if not model and msg.get("model"):
                        model = msg["model"]
                    usage = msg.get("usage") or {}
                    input_tokens += usage.get("input_tokens", 0)
                    output_tokens += usage.get("output_tokens", 0)
                    cache_read += usage.get("cache_read_input_tokens", 0)
                    cache_creation += usage.get(
                        "cache_creation_input_tokens", 0
                    )
                    # Collect tool names from content blocks
                    for block in msg.get("content") or []:
                        if isinstance(block, dict) and block.get("type") == "tool_use":
                            tools.add(block.get("name", ""))

                elif entry_type == "system" and raw.get("subtype") == "turn_duration":
                    duration_ms += raw.get("durationMs", 0)

        return cls(
            session_id=session_id,
            cwd=cwd,
            version=version,
            git_branch=git_branch,
            slug=slug,
            model=model,
            message_count=message_count,
            user_message_count=user_count,
            assistant_message_count=assistant_count,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_input_tokens=cache_read,
            cache_creation_input_tokens=cache_creation,
            duration_ms=duration_ms,
            tools_used=sorted(tools),
            has_plan=has_plan,
            jsonl_path=str(path),
            source_file=str(path),
        )
