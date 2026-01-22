"""
Skillit - JSON Key-Value Storage
Provides a simple key-value store backed by a JSON file.
"""
import json
from pathlib import Path
from typing import Any, Optional


class JsonKeyVal:
    """A simple key-value store backed by a JSON file."""

    def __init__(self, file_path: Path | str) -> None:
        """Initialize the store with a file path."""
        self.file_path = Path(file_path)
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Create the JSON file with empty object if it doesn't exist."""
        if not self.file_path.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self._write_data({})

    def _read_data(self) -> dict:
        """Read and return the JSON data from file."""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _write_data(self, data: dict) -> None:
        """Write data to the JSON file."""
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value by key, returning default if not found."""
        data = self._read_data()
        return data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a key-value pair."""
        data = self._read_data()
        data[key] = value
        self._write_data(data)

    def delete(self, key: str) -> bool:
        """Delete a key. Returns True if key existed, False otherwise."""
        data = self._read_data()
        if key in data:
            del data[key]
            self._write_data(data)
            return True
        return False

    def exists(self, key: str) -> bool:
        """Check if a key exists."""
        data = self._read_data()
        return key in data

    def keys(self) -> list[str]:
        """Return all keys."""
        return list(self._read_data().keys())

    def clear(self) -> None:
        """Clear all data."""
        self._write_data({})
