# Skillit 🎯

A powerful Claude Code plugin that enhances your prompts with intelligent keyword-based modifiers. Skillit automatically detects keywords in your prompts and augments them with specialized behaviors to improve Claude's responses.

## Features

- **Keyword-Based Activation**: Automatically triggers specialized behaviors when keywords are detected
- **Extensible Architecture**: Easy to add new modifiers and skills
- **Smart Cooldown System**: Prevents recursive activation with built-in cooldown mechanism
- **Path-Aware Matching**: Won't trigger on keywords in file paths
- **Multiple Skills**: Pre-built skills for analysis and testing workflows
- **Logging Support**: Comprehensive logging for debugging and monitoring

## Prerequisites

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) installed and accessible in your PATH
- Python 3.7+ (for the plugin scripts)
- Git (for cloning the repository)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/langware-labs/skillit.git
   cd skillit
   ```

2. **Run the installer**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

   The installer will:
   - Verify Claude Code CLI is installed
   - Create a local marketplace configuration
   - Register the plugin with Claude Code
   - Install the plugin at user level

3. **Verify installation**
   ```bash
   claude plugin list
   ```

   You should see `skillit` in the list of installed plugins.

## Usage

### Basic Usage

Simply include the `skillit` keyword in your Claude Code prompts:

```bash
claude -p "skillit analyze this codebase"
```

This will activate the analyzer modifier which enhances Claude's ability to understand and analyze code structures.

### Test Mode

Use `skillit:test` to activate testing-focused behavior:

```bash
claude -p "skillit:test check the authentication module"
```

This modifier optimizes Claude for test writing, debugging, and test coverage analysis.

### Available Keywords

| Keyword | Description | Use Case |
|---------|-------------|----------|
| `skillit` | Activates the analyzer modifier | Code analysis, understanding architecture |
| `skillit:test` | Activates the test modifier | Writing tests, debugging test failures |

## Configuration

Skillit uses a configuration file located at `scripts/plugin.json`. The plugin automatically manages state using `global_state.json` to track invocation timing and prevent recursive activation.

### Cooldown Period

By default, Skillit has a 3-second cooldown period to prevent recursive triggering. This is configured in `scripts/global_state.py`.

## Architecture

```
skillit/
├── commands/           # Command definitions
│   └── skillit.md     # Main command specification
├── scripts/           # Core plugin logic
│   ├── main.py        # Entry point and routing
│   ├── modifiers/     # Skill modifier implementations
│   │   ├── analyzer.py
│   │   └── test.py
│   ├── global_state.py
│   ├── log.py
│   └── claude_utils.py
├── hooks/             # Claude Code hooks
├── install.sh         # Installation script
├── uninstall.sh       # Uninstallation script
└── README.md
```

## Adding New Modifiers

1. Create a new file in `scripts/modifiers/`:
   ```python
   def handle_myskill(prompt: str, data: dict):
       """Your skill implementation"""
       # Modify the prompt or add context
       data["prompt"] = f"{prompt} [with your modifications]"
       return data
   ```

2. Import it in `scripts/main.py`:
   ```python
   from modifiers.myskill import handle_myskill
   ```

3. Add it to the `KEYWORD_MAPPINGS`:
   ```python
   KEYWORD_MAPPINGS = [
       ("skillit:myskill", handle_myskill),
       ("skillit:test", handle_test),
       ("skillit", handle_analyze),
   ]
   ```

Note: More specific patterns should come first in the list.

## Development

### Running Tests

```bash
cd scripts
python test.py
```

### Viewing Logs

Logs are written to `skill.log` in the root directory:

```bash
tail -f skill.log
```

### Debugging

To enable verbose logging, modify the `log.py` file or check `skill.log` after each invocation.

## Uninstallation

To completely remove Skillit:

```bash
./uninstall.sh
```

This will:
- Uninstall the plugin from Claude Code
- Optionally remove the marketplace configuration
- Clean up plugin registration

## Troubleshooting

### Plugin Not Triggering

- Verify installation: `claude plugin list`
- Check logs in `skill.log`
- Ensure cooldown period has passed (3 seconds between invocations)

### Claude Code Not Found

Make sure Claude Code CLI is installed and in your PATH:
```bash
which claude
```

If not found, install from: https://docs.anthropic.com/en/docs/claude-code

### Permission Errors

Ensure scripts are executable:
```bash
chmod +x install.sh uninstall.sh scripts/main.py
```

## How It Works

1. **Hook Integration**: Skillit registers a `UserPromptSubmit` hook with Claude Code
2. **Keyword Detection**: When you submit a prompt, the plugin scans for registered keywords
3. **Modifier Activation**: If a keyword matches, the corresponding modifier is invoked
4. **Prompt Enhancement**: The modifier augments your prompt with specialized instructions
5. **Cooldown**: A timestamp is recorded to prevent recursive activation

## Contributing

Contributions are welcome! Please feel free to submit issues, fork the repository, and create pull requests.

### Contribution Guidelines

1. Create a new branch for your feature
2. Add tests for new modifiers
3. Update documentation
4. Submit a pull request with a clear description

## License

MIT License - see LICENSE file for details

## Acknowledgments

Built for the Claude Code ecosystem. Inspired by the need for extensible, keyword-driven prompt enhancement.

## Support

- **Issues**: [GitHub Issues](https://github.com/langware-labs/skillit/issues)
- **Documentation**: [Claude Code Docs](https://docs.anthropic.com/en/docs/claude-code)

---

**Made with ❤️ for the Claude Code community**
