"""Sync protocol types for resource notifications."""

from enum import StrEnum


class SyncOperation(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class RefType(StrEnum):
    DATA = "data"
    PATH = "path"
