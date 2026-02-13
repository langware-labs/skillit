"""Storage layout types for resource records."""

from enum import Enum


class StorageLayout(str, Enum):
    """How a single record is persisted on disk."""

    FILE = "file"          # standalone <type>-@<uid>.json file
    LIST_ITEM = "list_item" # line inside a JSONL file
    FOLDER = "folder"      # <type>-@<uid>/ directory with record.json inside
