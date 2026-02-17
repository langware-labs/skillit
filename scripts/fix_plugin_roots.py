"""One-time script to expand $CLAUDE_PLUGIN_ROOT in all cached plugin versions."""
from pathlib import Path

base_cache = Path.home() / ".claude" / "plugins" / "cache"
plugin_name = "skillit"
count = 0

for marketplace_dir in base_cache.iterdir():
    if not marketplace_dir.is_dir():
        continue
    plugin_dir = marketplace_dir / plugin_name
    if not plugin_dir.is_dir():
        continue
    for version_dir in plugin_dir.iterdir():
        if not version_dir.is_dir():
            continue
        replacement = str(version_dir).replace("\\", "/")
        marker = "$CLAUDE_PLUGIN_ROOT"
        for pattern in ("**/*.json", "**/*.md"):
            for path in version_dir.glob(pattern):
                try:
                    content = path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue
                if marker in content:
                    path.write_text(content.replace(marker, replacement), encoding="utf-8")
                    print(f"Expanded: {path}")
                    count += 1

print(f"Total expanded: {count}")
