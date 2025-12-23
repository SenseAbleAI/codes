from typing import Any, Dict, Optional

from core.agents.utils.azure_copilot import AzureCopilotClient, mock_agent_response


class RefinementAgent:
    def __init__(self):
        self.client = AzureCopilotClient()

    def run(self, fingerprint: Dict[str, Any], feedback: Dict[str, Any]) -> Dict[str, Any]:
        if self.client.available():
            resp = self.client.call_agent(task="refine", input_text=jsonify(fingerprint), context={"feedback": feedback})
            if resp.get("ok") and isinstance(resp.get("result"), dict):
                return resp["result"]
        # Local conservative merge
        merged = dict(fingerprint)
        merged.update(feedback)
        return merged


def jsonify(obj: Any) -> str:
    try:
        import json

        return json.dumps(obj)
    except Exception:
        return str(obj)