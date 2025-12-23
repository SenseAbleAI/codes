"""Azure Copilot helper (safe, credential-free defaults).

This module provides a thin client wrapper for calling an Azure-hosted Copilot
style agent. It intentionally reads credentials from environment variables and
never stores secrets in code. If credentials are not present it exposes a
`available()` method that returns False so callers can fall back to a local
implementation.

Environment variables used (no defaults provided):
 - `AZURE_COPILOT_ENDPOINT` : HTTP(S) endpoint for the Copilot agent
 - `AZURE_COPILOT_API_KEY`  : API key or bearer token
 - `AZURE_COPILOT_DEPLOYMENT`: optional deployment or model id

The exact request/response schema depends on the Copilot deployment. This
helper sends a JSON payload with `task`, `input`, and `context` fields and
returns the raw JSON response or a structured fallback.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class AzureCopilotClient:
    """Minimal client for calling an Azure Copilot agent.

    This client is intentionally conservative: it only attempts a network
    request if the endpoint and api key environment variables are present.
    Callers should always check `available()` before using it in production.
    """

    def __init__(self):
        self.endpoint = os.environ.get("AZURE_COPILOT_ENDPOINT")
        self.api_key = os.environ.get("AZURE_COPILOT_API_KEY")
        self.deployment = os.environ.get("AZURE_COPILOT_DEPLOYMENT")

    def available(self) -> bool:
        return bool(self.endpoint and self.api_key)

    def call_agent(self, task: str, input_text: str, context: Optional[Dict[str, Any]] = None, timeout: int = 20) -> Dict[str, Any]:
        """Call the remote Copilot agent and return parsed JSON result.

        Args:
            task: short identifier of the agent task (e.g., 'rewrite', 'explain')
            input_text: primary input text
            context: optional dict with extra structured context
            timeout: request timeout in seconds

        Returns:
            dict with keys: `ok` (bool), `status` (int), `result` (any), `error` (str)
        """
        if not self.available():
            return {"ok": False, "status": 0, "result": None, "error": "credentials_missing"}

        payload = {"task": task, "input": input_text, "context": context or {}}

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        # If a deployment id is supplied, pass it as a header (some deployments use this)
        if self.deployment:
            headers["X-Deployment-Id"] = self.deployment

        try:
            # Import requests lazily so module import doesn't fail when requests is not installed.
            import requests  # type: ignore

            resp = requests.post(self.endpoint, headers=headers, data=json.dumps(payload), timeout=timeout)
            status = getattr(resp, "status_code", 0)
            try:
                body = resp.json()
            except Exception:
                body = {"raw": resp.text}

            if 200 <= status < 300:
                return {"ok": True, "status": status, "result": body, "error": None}
            else:
                logger.warning("Copilot request failed status=%s body=%s", status, body)
                return {"ok": False, "status": status, "result": body, "error": f"status_{status}"}
        except Exception as exc:
            logger.exception("Copilot call failed: %s", exc)
            return {"ok": False, "status": 0, "result": None, "error": str(exc)}


def mock_agent_response(task: str, input_text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Return a conservative local response used when no remote agent is available.

    This keeps the system usable in offline or demo mode.
    """
    # Simple, safe local heuristics for demo purposes
    if task == "detect":
        return {"ok": True, "status": 200, "result": {"spans": []}, "error": None}
    if task == "rewrite":
        # echo input as fallback
        return {"ok": True, "status": 200, "result": {"rewrites": [input_text]}, "error": None}
    if task == "metaphor_retrieval":
        return {"ok": True, "status": 200, "result": {"metaphors": [f"{input_text} like a memory"]}, "error": None}
    return {"ok": True, "status": 200, "result": {"text": input_text}, "error": None}


__all__ = ["AzureCopilotClient", "mock_agent_response"]
