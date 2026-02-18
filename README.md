# Skillit 🎯

[![Version](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Flangware-labs%2Fskillit%2Fmain%2F.claude-plugin%2Fplugin.json&query=%24.version&label=version&color=blue)](https://github.com/langware-labs/skillit)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-Plugin-blueviolet)](https://docs.anthropic.com/en/docs/claude-code)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/langware-labs/skillit/pulls)

A Claude Code plugin that automatically learns from your sessions. Skillit analyzes conversations to identify mistakes, inefficiencies, and automation opportunities, then creates reusable skills to prevent them from recurring.

## Features

- **Session Analysis**: Identifies mistakes, misunderstandings, inefficiencies, and automation opportunities in Claude Code sessions
- **Skill Creation**: Automatically generates activation rules to prevent recurring issues
- **Agent-Based Architecture**: Specialized agents run as background tasks for non-blocking workflows
- **Hook Integration**: Monitors sessions

## Prerequisites

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) installed and accessible in your PATH
- Python 3.7+ (for the plugin scripts)
- Git (for cloning the repository)

## Installation

### Quick Install (from GitHub)

```bash
# Add the skillit marketplace
claude plugin marketplace add langware-labs/skillit

# Install the plugin
claude plugin install skillit@flowpad-ai
```

### Verify Installation

```bash
claude plugin list
```

You should see `skillit` in the list of installed plugins.

### Auto-Update

- `claude /plugin` to open the plugin manager
- Navigate to `Marketplaces`
- Select `flowpad-ai` marketplace
- Choose `Enable auto-update`

### Manual Update

```bash
claude plugin marketplace update flowpad-ai
claude plugin update skillit@flowpad-ai
```

### Alternative: Local Development Install

If you want to develop or modify the plugin:

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

### Commands

| Command | Description |
|---------|-------------|
| `/skillit:create-skill` | Launches the skill creator agent to analyze the conversation and create activation rules |
| `/skillit:analyze` | Launches the analyzer agent to identify issues and automation opportunities |

### Create Skill

Run `/skillit:create-skill` in a Claude Code session to analyze the current conversation and generate skills that prevent recurring issues:

```
/skillit:create-skill
```

### Analyze Session

Run `/skillit:analyze` to review a session for mistakes, misunderstandings, inefficiencies, or automation opportunities:

```
/skillit:analyze
```

Both commands launch their respective agents as background tasks, so you can continue working while they run.

## Architecture

```
skillit/
├── agents/              # Built agent definitions (generated from templates)
├── commands/            # Slash command definitions
│   ├── create-skill.md  # /skillit:create-skill command
│   └── analyze.md       # /skillit:analyze command
├── templates/           # Agent templates (source of truth)
│   ├── skillit-creator.md
│   ├── skillit-analyzer.md
│   ├── skillit-classifier.md
│   └── skillit-agent.md
├── hooks/               # Claude Code hooks (SessionStart, UserPromptSubmit)
├── scripts/             # Build system and utilities
│   └── utils/           # Plugin manager, build tools
├── .claude-plugin/      # Plugin metadata and marketplace config
├── install.sh           # Installation script
├── uninstall.sh         # Uninstallation script
└── README.md
```

### Agents

| Agent | Role |
|-------|------|
| `skillit-analyzer` | Analyzes conversations to identify issues and opportunities |
| `skillit-creator` | Creates activation rules/skills from identified issues |

## Development

### Building

The build step renders agent templates (with version injection) into the `agents/` directory:

```bash
cd scripts
python utils/build.py
```

### Deploying

Bump the patch version, build, commit, and push:

```bash
cd scripts
python -c "from utils.plugin_manager import SkillitPluginManager; SkillitPluginManager().patch()"
python utils/build.py
```

Then commit and push the changes.

## Uninstallation

To completely remove Skillit:

```bash
./uninstall.sh
```

This will:
- Uninstall the plugin from Claude Code
- Optionally remove the marketplace configuration
- Clean up plugin registration

## How It Works

1. **Hooks**: Skillit registers `SessionStart` and `UserPromptSubmit` hooks that run on each session/prompt
2. **Commands**: Slash commands (`/skillit:analyze`, `/skillit:create-skill`) launch specialized agents as background tasks
3. **Analysis**: The analyzer agent reviews conversation transcripts and identifies issues
4. **Classification**: Issues are classified as new or known against existing rules
5. **Skill Creation**: New activation rules are generated and saved to prevent recurring issues

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
