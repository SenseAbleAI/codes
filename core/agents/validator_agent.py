from typing import Any, Dict, Optional

from core.generation.constraints import validate_rewrites
from core.agents.utils.azure_copilot import AzureCopilotClient


class ValidatorAgent:
    def __init__(self):
        self.client = AzureCopilotClient()

    def run(self, original: str, rewrites: Any) -> Any:
        if self.client.available():
            resp = self.client.call_agent(task="validate", input_text=original, context={"rewrites": rewrites})
            if resp.get("ok") and resp.get("result") is not None:
                return resp["result"]
        return validate_rewrites(original, rewrites)