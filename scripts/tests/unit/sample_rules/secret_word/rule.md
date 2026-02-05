---
name: secret_word
description: Returns a secret number when the user prompt contains '42'
---

## Triggers

- Hook events: UserPromptSubmit
- Condition: prompt contains '42'

## Actions

- `add_context`: Injects the secret number response instruction
