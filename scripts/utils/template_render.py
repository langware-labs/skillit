"""Simple template renderer with basic Handlebars-like syntax.

Supports:
  {{variable}}             - Simple variable substitution
  {{object.key}}           - Dot-notation access
  {{#if var}}...{{/if}}    - Conditional blocks
  {{#unless var}}...{{/unless}} - Inverse conditional blocks
  {{#each list}}...{{/each}}   - Iteration ({{this}} for value, {{@index}} for index)
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

_VAR_RE = re.compile(r"\{\{(?!#|/|@)([a-zA-Z_][\w.]*)\}\}")
_EACH_RE = re.compile(
    r"\{\{#each\s+([\w.]+)\}\}(.*?)\{\{/each\}\}", re.DOTALL
)
_IF_RE = re.compile(
    r"\{\{#if\s+([\w.]+)\}\}(.*?)\{\{/if\}\}", re.DOTALL
)
_UNLESS_RE = re.compile(
    r"\{\{#unless\s+([\w.]+)\}\}(.*?)\{\{/unless\}\}", re.DOTALL
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve(name: str, context: dict[str, Any]) -> Any:
    """Resolve a dotted name against a context dict."""
    parts = name.split(".")
    value: Any = context
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part)
        else:
            return None
        if value is None:
            return None
    return value


def _is_truthy(value: Any) -> bool:
    """Handlebars-style truthiness (empty list / None / False / '' are falsy)."""
    if value is None:
        return False
    if isinstance(value, (list, dict, str)) and len(value) == 0:
        return False
    return bool(value)


# ---------------------------------------------------------------------------
# Core renderer
# ---------------------------------------------------------------------------

def _render_string(template: str, context: dict[str, Any]) -> str:
    """Render a template string against a context dict."""

    # {{#each list}}...{{/each}}
    def _replace_each(m: re.Match) -> str:
        key = m.group(1)
        body = m.group(2)
        items = _resolve(key, context)
        if not isinstance(items, list):
            return ""
        parts: list[str] = []
        for idx, item in enumerate(items):
            chunk = body
            if isinstance(item, dict):
                # nested render with item fields available
                child_ctx = {**context, **item, "this": item, "@index": idx}
                chunk = _render_string(chunk, child_ctx)
            else:
                chunk = chunk.replace("{{this}}", str(item))
                chunk = chunk.replace("{{@index}}", str(idx))
                chunk = _render_string(chunk, {**context, "this": item, "@index": idx})
            parts.append(chunk)
        return "".join(parts)

    template = _EACH_RE.sub(_replace_each, template)

    # {{#if var}}...{{/if}}
    def _replace_if(m: re.Match) -> str:
        key = m.group(1)
        body = m.group(2)
        if _is_truthy(_resolve(key, context)):
            return _render_string(body, context)
        return ""

    template = _IF_RE.sub(_replace_if, template)

    # {{#unless var}}...{{/unless}}
    def _replace_unless(m: re.Match) -> str:
        key = m.group(1)
        body = m.group(2)
        if not _is_truthy(_resolve(key, context)):
            return _render_string(body, context)
        return ""

    template = _UNLESS_RE.sub(_replace_unless, template)

    # {{variable}} / {{object.key}}
    def _replace_var(m: re.Match) -> str:
        val = _resolve(m.group(1), context)
        if val is None:
            return ""
        return str(val)

    template = _VAR_RE.sub(_replace_var, template)

    return template


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def render(template: str | Path, context: dict[str, Any]) -> str:
    """Render a template with the given context.

    Args:
        template: A template string **or** a Path / path-string to a template file.
        context: Dict of variables available inside the template.

    Returns:
        The rendered string.
    """
    # Determine if template is a file path
    if isinstance(template, Path):
        template = template.read_text(encoding="utf-8")
    elif isinstance(template, str):
        path = Path(template)
        if path.is_file():
            template = path.read_text(encoding="utf-8")

    return _render_string(template, context)
