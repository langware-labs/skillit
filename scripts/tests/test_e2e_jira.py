"""Integration test for jira_context rule with main.py hook processor."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent


class TestJiraContextIntegration:
    """Integration tests for jira context injection via main.py."""

    def test_jira_prompt_injects_acli_context(self):
        """
        Test that when asking about jira, the hook injects acli context.

        This test runs main.py directly with a jira-related prompt and
        verifies the output contains the expected acli context.
        """
        input_data = {
            "hookEvent": "UserPromptSubmit",
            "prompt": "how would you check my jira status?",
            "cwd": str(Path.home()),  # Use home dir to find ~/.flow/skill_rules
        }

        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "main.py")],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(SCRIPTS_DIR),
        )

        # main.py should succeed
        assert result.returncode == 0, f"main.py failed: {result.stderr}"

        # Parse the JSON output
        if result.stdout.strip():
            output = json.loads(result.stdout)

            # Should have hookSpecificOutput with additionalContext containing acli
            assert "hookSpecificOutput" in output, (
                f"Expected hookSpecificOutput in output, got: {output}"
            )
            assert "additionalContext" in output["hookSpecificOutput"], (
                f"Expected additionalContext, got: {output['hookSpecificOutput']}"
            )

            context = output["hookSpecificOutput"]["additionalContext"].lower()
            assert "acli" in context, (
                f"Expected 'acli' in additionalContext, got: {context}"
            )
        else:
            pytest.fail(f"No output from main.py. stderr: {result.stderr}")

    def test_non_jira_prompt_no_context(self):
        """Test that non-jira prompts don't inject acli context."""
        input_data = {
            "hookEvent": "UserPromptSubmit",
            "prompt": "help me write a python function",
            "cwd": str(Path.home()),
        }

        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "main.py")],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(SCRIPTS_DIR),
        )

        assert result.returncode == 0, f"main.py failed: {result.stderr}"

        # For non-jira prompts, either no output or output without acli context
        if result.stdout.strip():
            output = json.loads(result.stdout)
            if "hookSpecificOutput" in output:
                context = output["hookSpecificOutput"].get("additionalContext", "")
                # jira_context should not have triggered
                assert "jira_context" not in context.lower() or "acli" not in context.lower(), (
                    f"Unexpected jira context for non-jira prompt: {context}"
                )
