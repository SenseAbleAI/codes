from typing import Any, Dict, Optional

from core.generation.rewrite_engine import generate_rewrites
from core.agents.utils.azure_copilot import AzureCopilotClient, mock_agent_response


class RewriteAgent:
    def __init__(self):
        self.client = AzureCopilotClient()

    def run(self, text: str, candidates: Any, fingerprint: Optional[Dict[str, Any]] = None) -> Any:
        if self.client.available():
            context = {"candidates": candidates, "fingerprint": fingerprint}
            resp = self.client.call_agent(task="rewrite", input_text=text, context=context)
            if resp.get("ok") and resp.get("result") is not None:
                return resp["result"]
        return generate_rewrites(text, candidates, fingerprint)