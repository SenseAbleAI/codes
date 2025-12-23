"""Minimal MCP (Model Context Protocol) orchestrator for local agents.

This module provides a lightweight orchestrator that discovers agent
implementations under `core.agents.*`, instantiates them on demand, and
routes calls either to the local agent `run()` method or to the remote
Azure Copilot helper as a fallback or when configured.

The goal is to offer a single integration point so higher-level code or
external MCP servers can dispatch tasks to named agents uniformly.
"""

from __future__ import annotations

import importlib
import json
import logging
from typing import Any, Dict

from core.agents.utils.azure_copilot import AzureCopilotClient
from config import get_config

logger = logging.getLogger(__name__)


def _to_class_name(module_name: str) -> str:
    # e.g. detector_agent -> DetectorAgent
    parts = module_name.split("_")
    return "".join(p.capitalize() for p in parts)


class MCPOrchestrator:
    def __init__(self, agents_config: Dict[str, Any] | None = None):
        self._agents: Dict[str, Any] = {}
        self._instances: Dict[str, Any] = {}
        self._client = AzureCopilotClient()
        cfg = agents_config or get_config("agents", redacted=True)
        # agents.yaml contains mapping under key `agents` (matching repo layout)
        self._specs = cfg.get("agents") if isinstance(cfg, dict) else cfg

    def register_agent(self, name: str, module_path: str) -> None:
        self._agents[name] = module_path

    def _discover_agent_module(self, agent_key: str) -> str:
        # default module path under core.agents
        if agent_key in self._agents:
            return self._agents[agent_key]
        return f"core.agents.{agent_key}"

    def _instantiate(self, agent_key: str):
        if agent_key in self._instances:
            return self._instances[agent_key]
        module_path = self._discover_agent_module(agent_key)
        try:
            module = importlib.import_module(module_path)
            class_name = _to_class_name(agent_key)
            agent_cls = getattr(module, class_name)
            inst = agent_cls()
            self._instances[agent_key] = inst
            return inst
        except Exception as exc:
            logger.debug("Failed to import/instantiate %s: %s", module_path, exc)
            raise

    def run(self, agent_key: str, *args, prefer_remote: bool = False, **kwargs) -> Any:
        """Run an agent by key.

        - If `prefer_remote` is True and the AzureCopilotClient is available,
          the orchestrator will attempt a remote call first.
        - Otherwise it calls the local agent implementation `run()` method.
        """
        # If remote is preferred and available, try calling remote task
        task_name = agent_key
        if prefer_remote and self._client.available():
            logger.debug("Calling remote agent for %s", agent_key)
            # build a conservative payload
            payload = {"args": args, "kwargs": kwargs}
            resp = self._client.call_agent(task=task_name, input_text=json.dumps(payload), context={})
            if resp.get("ok"):
                return resp.get("result")
            # fall through to local

        # Local dispatch
        inst = self._instantiate(agent_key)
        if not hasattr(inst, "run"):
            raise AttributeError(f"Agent {agent_key} has no run() method")
        return inst.run(*args, **kwargs)


__all__ = ["MCPOrchestrator"]
