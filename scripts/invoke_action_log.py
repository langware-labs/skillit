#!/usr/bin/env python3
"""Temp script to test _notify_rules_executed with mock data."""

import sys
import os

# Ensure scripts/ is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from memory.rule_engine.action_executor import _notify_rules_executed

mock_actions = [
    {"rule": "session-context-init", "action": "add_context"},
    {"rule": "jira-helper", "action": "add_context"},
    {"rule": "security-gate", "action": "block"},
]

print("Sending rules_executed notification with mock data...")
_notify_rules_executed("UserPromptSubmit", mock_actions)
print("Done. Check FlowPad for the event.")
