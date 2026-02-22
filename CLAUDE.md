# Skillit - Claude Code Plugin

## SDK Dependency

This project depends on the **flow-sdk** (`flow_sdk` Python package), which lives in the `flow-cli` repo.

- Git: https://github.com/langware-labs/flow-cli.git
- The SDK code is under `flow-cli/flow-sdk/python/flow_sdk/`

The SDK provides:
- `flow_sdk.fs_store` — File-system record store (FsRecord, FsRecordRef, ResourceRecord, type registry, sync protocol, storage layout)
- `flow_sdk.fs_records` — Record types (SkillRecord, TaskResource, ClaudeRootFsRecord, relationships, artifacts, agentic processes, and Claude-specific records)

### Install the SDK (editable / dev mode)

```bash
git clone https://github.com/langware-labs/flow-cli.git
uv pip install -e <path-to-flow-cli>
```

For example, if cloned to `~/dev/flow-cli`:
```bash
uv pip install -e ~/dev/flow-cli
```

This installs the `flowpad` package (which includes `flow_sdk`) in editable mode so local changes to flow-cli are immediately available.

### Running tests

```bash
uv run pytest scripts/tests/
```
