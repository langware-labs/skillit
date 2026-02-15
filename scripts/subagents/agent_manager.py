"""Manage skillit subagents and their prompt generation."""

import json
from enum import StrEnum


class SubAgent(StrEnum):
    """Available skillit subagents."""

    ANALYZE = "skillit-analyzer"
    MAIN_AGENT = "skillit-agent"
    CLASSIFY = "skillit-classifier"
    CREATE = "skillit-create"


def get_subagent_launch_prompt(agent: SubAgent, prompt: str, data: dict) -> str:
    data_json = json.dumps(data, indent=2)
    return f"""\nLaunch the "{agent}" subagent with the following context:

**Instruction:**
{prompt}

**Data:**
```json
{data_json}
```

# Important Notes:
- Make sure to include all the context you received : session_id and output directory are crucial for the subagent to function properly.
"""

