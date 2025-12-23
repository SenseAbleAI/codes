from typing import Any, Dict, Optional

from core.stg.traversal import traverse_stg
from core.agents.utils.azure_copilot import AzureCopilotClient


class STGAgent:
    def __init__(self):
        self.client = AzureCopilotClient()

    def run(self, span: str, fingerprint: Optional[Dict[str, Any]] = None) -> Any:
        if self.client.available():
            resp = self.client.call_agent(task="stg_traverse", input_text=span, context={"fingerprint": fingerprint})
            if resp.get("ok") and resp.get("result") is not None:
                return resp["result"]
        return traverse_stg(span, fingerprint)