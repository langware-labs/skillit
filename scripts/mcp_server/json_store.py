"""Simple JSON-based key-value store."""
import json
from pathlib import Path
from typing import Any, Optional


class jsonKeyVal:
    """A simple JSON-based key-value store that persists to disk."""

    def __init__(self, json_path: str | Path):
        """Initialize the key-value store.

        Args:
            json_path: Path to the JSON file for storage.
        """
        self.json_path = Path(json_path)
        self._data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Load data from the JSON file if it exists."""
        if self.json_path.exists():
            try:
                with open(self.json_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                # If file is corrupted or unreadable, start with empty dict
                self._data = {}
        else:
            # Ensure parent directory exists
            self.json_path.parent.mkdir(parents=True, exist_ok=True)
            self._save()

    def _save(self) -> None:
        """Save data to the JSON file."""
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value by key.

        Args:
            key: The key to retrieve.
            default: Default value if key doesn't exist.

        Returns:
            The value associated with the key, or default if not found.
        """
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a key-value pair.

        Args:
            key: The key to set.
            value: The value to store.
        """
        self._data[key] = value
        self._save()

    def delete(self, key: str) -> bool:
        """Delete a key-value pair.

        Args:
            key: The key to delete.

        Returns:
            True if the key existed and was deleted, False otherwise.
        """
        if key in self._data:
            del self._data[key]
            self._save()
            return True
        return False

    def has(self, key: str) -> bool:
        """Check if a key exists.

        Args:
            key: The key to check.

        Returns:
            True if the key exists, False otherwise.
        """
        return key in self._data

    def keys(self) -> list[str]:
        """Get all keys in the store.

        Returns:
            List of all keys.
        """
        return list(self._data.keys())

    def values(self) -> list[Any]:
        """Get all values in the store.

        Returns:
            List of all values.
        """
        return list(self._data.values())

    def items(self) -> list[tuple[str, Any]]:
        """Get all key-value pairs.

        Returns:
            List of (key, value) tuples.
        """
        return list(self._data.items())

    def clear(self) -> None:
        """Clear all data from the store."""
        self._data = {}
        self._save()

    def __len__(self) -> int:
        """Get the number of items in the store."""
        return len(self._data)

    def __contains__(self, key: str) -> bool:
        """Check if a key exists using 'in' operator."""
        return key in self._data

    def __getitem__(self, key: str) -> Any:
        """Get a value using dictionary-style access."""
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Set a value using dictionary-style access."""
        self.set(key, value)

    def __delitem__(self, key: str) -> None:
        """Delete a key using dictionary-style access."""
        if key not in self._data:
            raise KeyError(key)
        self.delete(key)
