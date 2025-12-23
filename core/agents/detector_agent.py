from typing import Any, Dict, Optional

from core.detection.sensory_detector import detect_sensory_spans
from core.agents.utils.azure_copilot import AzureCopilotClient, mock_agent_response


class DetectorAgent:
    def __init__(self):
        self.client = AzureCopilotClient()

    def run(self, text: str, language: Optional[str] = None) -> Any:
        # Prefer remote agent when available, otherwise fall back to local detector
        if self.client.available():
            resp = self.client.call_agent(task="detect", input_text=text, context={"language": language})
            if resp.get("ok") and resp.get("result") is not None:
                return resp["result"]
        # Local fallback
        return detect_sensory_spans(text, language)
