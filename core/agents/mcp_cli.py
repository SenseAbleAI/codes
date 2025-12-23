"""Simple CLI to exercise the MCP orchestrator locally.

Usage examples:
  python -m core.agents.mcp_cli detector_agent "Some sample text"
  python -m core.agents.mcp_cli rewrite_agent "Text to rewrite"
"""

from __future__ import annotations

import argparse
import json
import logging
from typing import Any

from core.agents.mcp import MCPOrchestrator

logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser("mcp-cli")
    parser.add_argument("agent", help="agent module key (e.g. detector_agent)")
    parser.add_argument("input", help="input text or JSON payload")
    parser.add_argument("--json", action="store_true", help="treat input as JSON")
    parser.add_argument("--prefer-remote", action="store_true", help="prefer remote Copilot when available")
    args = parser.parse_args()

    orch = MCPOrchestrator()
    payload: Any = args.input
    if args.json:
        try:
            payload = json.loads(args.input)
        except Exception:
            logger.error("Failed to parse JSON input")
            return 2

    try:
        # If payload is a dict, expand as kwargs; otherwise pass as single arg
        if isinstance(payload, dict):
            out = orch.run(args.agent, **payload, prefer_remote=args.prefer_remote)
        else:
            out = orch.run(args.agent, payload, prefer_remote=args.prefer_remote)
        print(json.dumps({"ok": True, "result": out}, default=str, indent=2))
        return 0
    except Exception as exc:
        logger.exception("MCP call failed: %s", exc)
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
