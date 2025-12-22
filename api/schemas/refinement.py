from pydantic import BaseModel
from typing import Dict

class RefinementRequest(BaseModel):
    fingerprint: Dict[str, float]
    feedback: str

class RefinementResponse(BaseModel):
    updated_fingerprint: Dict[str, float]