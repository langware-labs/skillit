"""Base resource record for unified resource management."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TypeVar

from pydantic import BaseModel, ConfigDict, Field

from .scope import Scope

T = TypeVar("T", bound="ResourceRecord")


class ResourceRecord(BaseModel):
    """Base record shared by file-system and cloud entities."""

    model_config = ConfigDict(
        from_attributes=True,
        arbitrary_types_allowed=True,
        extra="allow",
        use_enum_values=True,
    )

    # Identity
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str = Field(default="")
    name: str = Field(default="")

    # Audit
    created_at: datetime | None = Field(default=None)
    modified_at: datetime | None = Field(default=None)
    created_by: str | None = Field(default=None)
    updated_by: str | None = Field(default=None)

    # Scope and location
    scope: Scope | str = Field(default=Scope.USER)
    source_file: str | None = Field(default=None)
    path: str | None = Field(default=None)

    # Cloud sync link
    entity_id: str | None = Field(default=None)

    # CRUD
    def save(self: T) -> T: ...

    def delete(self) -> bool: ...

    @classmethod
    def get_by_id(cls: type[T], eid: str, **kwargs) -> T | None: ...

    @classmethod
    def get_all(cls: type[T], **kwargs) -> list[T]: ...

    # Serialization
    def model_dump(self, **kwargs) -> dict: ...
