from typing import Any, Dict, Optional

from core.difficulty.zero_shot_scorer import score_sensory_difficulty
from core.agents.utils.azure_copilot import AzureCopilotClient, mock_agent_response


class DifficultyAgent:
    def __init__(self):
        self.client = AzureCopilotClient()

    def run(self, spans: Any, fingerprint: Optional[Dict[str, Any]] = None) -> Any:
        if self.client.available():
            resp = self.client.call_agent(task="score_difficulty", input_text=jsonify_spans(spans), context={"fingerprint": fingerprint})
            if resp.get("ok") and resp.get("result") is not None:
                return resp["result"]
        return score_sensory_difficulty(spans, fingerprint)


def jsonify_spans(spans: Any) -> str:
    try:
        import json

        return json.dumps(spans)
    except Exception:
        return str(spans)