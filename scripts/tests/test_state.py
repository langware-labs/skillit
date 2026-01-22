"""Tests for JsonKeyVal, global_state, and main module."""
import time
from pathlib import Path
import tempfile

import pytest

from json_key_val import JsonKeyVal
from global_state import (
    global_state,
    is_within_cooldown,
    update_invocation_time,
    COOLDOWN_SECONDS,
)
from main import find_matching_modifier


class TestJsonKeyVal:
    """Tests for JsonKeyVal class."""

    @pytest.fixture
    def temp_store(self, tmp_path):
        """Create a temporary JsonKeyVal store."""
        return JsonKeyVal(tmp_path / "test.json")

    def test_get_default_value_int(self, temp_store):
        """Get with default int returns the default."""
        assert temp_store.get("nonexistent", 0) == 0

    def test_get_default_value_string(self, temp_store):
        """Get with default string returns the default."""
        assert temp_store.get("nonexistent", "default_str") == "default_str"

    def test_get_default_none(self, temp_store):
        """Get without default returns None."""
        assert temp_store.get("nonexistent") is None

    def test_set_and_get(self, temp_store):
        """Set and get a value."""
        temp_store.set("test_key", "test_value")
        assert temp_store.get("test_key") == "test_value"

    def test_set_and_get_timestamp(self, temp_store):
        """Set and get a timestamp value."""
        now = time.time()
        temp_store.set("timestamp", now)
        assert temp_store.get("timestamp") == now

    def test_delete_existing_key(self, temp_store):
        """Delete an existing key returns True."""
        temp_store.set("key", "value")
        assert temp_store.delete("key") is True
        assert temp_store.get("key") is None

    def test_delete_nonexistent_key(self, temp_store):
        """Delete a nonexistent key returns False."""
        assert temp_store.delete("nonexistent") is False

    def test_exists_true(self, temp_store):
        """Exists returns True for existing key."""
        temp_store.set("key", "value")
        assert temp_store.exists("key") is True

    def test_exists_false(self, temp_store):
        """Exists returns False for nonexistent key."""
        assert temp_store.exists("nonexistent") is False

    def test_keys(self, temp_store):
        """Keys returns all keys."""
        temp_store.set("a", 1)
        temp_store.set("b", 2)
        assert sorted(temp_store.keys()) == ["a", "b"]

    def test_clear(self, temp_store):
        """Clear removes all data."""
        temp_store.set("a", 1)
        temp_store.set("b", 2)
        temp_store.clear()
        assert temp_store.keys() == []


class TestCooldown:
    """Tests for cooldown functionality."""

    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Clean up global state before and after each test."""
        global_state.delete("last_invocation_time")
        yield
        global_state.delete("last_invocation_time")

    def test_no_previous_invocation_not_in_cooldown(self):
        """Without previous invocation, not within cooldown."""
        assert is_within_cooldown() is False

    def test_recent_invocation_in_cooldown(self):
        """After update, within cooldown."""
        update_invocation_time()
        assert is_within_cooldown() is True

    def test_default_zero_gives_large_elapsed(self):
        """Default 0 gives elapsed time since epoch (not in cooldown)."""
        last = global_state.get("last_invocation_time", 0)
        elapsed = time.time() - last
        assert elapsed > COOLDOWN_SECONDS

    def test_cooldown_seconds_is_positive(self):
        """COOLDOWN_SECONDS is a positive number."""
        assert COOLDOWN_SECONDS > 0


class TestFindMatchingModifier:
    """Tests for find_matching_modifier function."""

    def test_skillit_keyword_matches(self):
        """'skillit' keyword matches and returns handler."""
        handler, keyword = find_matching_modifier("skillit do something")
        assert handler is not None
        assert keyword == "skillit"

    def test_skillit_test_keyword_matches(self):
        """'skillit:test' keyword matches before 'skillit'."""
        handler, keyword = find_matching_modifier("skillit:test something")
        assert handler is not None
        assert keyword == "skillit:test"

    def test_no_keyword_returns_none(self):
        """No matching keyword returns (None, None)."""
        handler, keyword = find_matching_modifier("hello world")
        assert handler is None
        assert keyword is None

    def test_keyword_in_path_does_not_match(self):
        """Keyword inside a file path should NOT match."""
        handler, keyword = find_matching_modifier(
            "run /path/to/skillit/file.txt"
        )
        assert handler is None
        assert keyword is None

    def test_keyword_in_windows_path_does_not_match(self):
        """Keyword inside a Windows file path should NOT match."""
        handler, keyword = find_matching_modifier(
            r"run C:\path\skillit\file.txt"
        )
        assert handler is None
        assert keyword is None

    def test_keyword_case_insensitive(self):
        """Keyword matching is case insensitive."""
        handler, keyword = find_matching_modifier("SKILLIT do something")
        assert handler is not None

    def test_keyword_at_start_of_prompt(self):
        """Keyword at start of prompt matches."""
        handler, keyword = find_matching_modifier("skillit")
        assert handler is not None

    def test_keyword_at_end_of_prompt(self):
        """Keyword at end of prompt matches."""
        handler, keyword = find_matching_modifier("run skillit")
        assert handler is not None

    def test_keyword_not_preceded_by_slash(self):
        """Keyword preceded by slash does not match."""
        handler, keyword = find_matching_modifier("/skillit")
        assert handler is None

    def test_keyword_not_followed_by_slash(self):
        """Keyword followed by slash does not match."""
        handler, keyword = find_matching_modifier("skillit/")
        assert handler is None
