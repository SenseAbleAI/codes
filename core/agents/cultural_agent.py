from typing import Any, Dict, Optional

from core.culture.rag import retrieve_cultural_metaphors
from core.agents.utils.azure_copilot import AzureCopilotClient, mock_agent_response


class CulturalAgent:
    def __init__(self):
        self.client = AzureCopilotClient()

    def run(self, span: str, culture: Optional[str] = None) -> Any:
        if self.client.available():
            resp = self.client.call_agent(task="metaphor_retrieval", input_text=span, context={"culture": culture})
            if resp.get("ok") and resp.get("result") is not None:
                return resp["result"]
        return retrieve_cultural_metaphors(span, culture)