#!/usr/bin/env python3
"""Launcher for flow-sdk-mcp. Runs a stub MCP server if flowpad is not installed."""
import json, shutil, subprocess, sys

_MSG = "flowpad is not installed. Install with: pip install flowpad — then restart Claude Code."
_notified = False


def _send(msg):
    sys.stdout.buffer.write(json.dumps(msg).encode() + b"\n")
    sys.stdout.buffer.flush()


def _respond(id, result):
    _send({"jsonrpc": "2.0", "id": id, "result": result})


def _read():
    for line in sys.stdin.buffer:
        text = line.decode().strip()
        if not text:
            continue
        if text.lower().startswith("content-length:"):
            length = int(text.split(":", 1)[1])
            while sys.stdin.buffer.readline().strip():
                pass
            return json.loads(sys.stdin.buffer.read(length))
        return json.loads(text)
    raise EOFError


def _stub():
    global _notified
    tool = {"name": "flow_ping", "description": _MSG, "inputSchema": {"type": "object"}}
    while True:
        try:
            msg = _read()
        except (EOFError, ValueError):
            break
        method, id = msg.get("method", ""), msg.get("id")
        if method == "initialize":
            _respond(id, {"protocolVersion": "2024-11-05",
                          "capabilities": {"tools": {}, "logging": {}},
                          "serverInfo": {"name": "flow_sdk_stub", "version": "0.0.0"}})
        elif method == "notifications/initialized":
            _send({"jsonrpc": "2.0", "method": "notifications/message",
                   "params": {"level": "warning", "data": _MSG}})
        elif method == "tools/list":
            _respond(id, {"tools": [tool]})
        elif method == "tools/call":
            text = "[flowpad not installed]" if _notified else _MSG
            _notified = True
            _respond(id, {"content": [{"type": "text", "text": text}], "isError": True})


if __name__ == "__main__":
    exe = shutil.which("flow-sdk-mcp")
    if exe:
        raise SystemExit(subprocess.call([exe] + sys.argv[1:]))
    _stub()
