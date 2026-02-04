"""End-to-end test for jira_context rule integration with Claude."""

import subprocess
import pytest


class TestJiraContextE2E:
    """End-to-end tests for jira context injection."""

    def test_jira_prompt_suggests_acli(self):
        """
        Test that when asking about jira, Claude suggests using acli.

        This test runs:
            claude -p "how would you check my jira status?"

        And expects the response to contain "acli" because the jira_context
        rule should inject context about using acli for jira operations.
        """
        result = subprocess.run(
            ["claude", "-p", "how would you check my jira status?"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        response = result.stdout.lower()

        # The jira_context rule should have injected context about acli,
        # so Claude's response should mention acli
        assert "acli" in response, (
            f"Expected 'acli' in response but got:\n{result.stdout[:500]}"
        )
