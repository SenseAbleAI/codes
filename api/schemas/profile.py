from pydantic import BaseModel
from typing import Dict, List

class ProfileRequest(BaseModel):
    impairments: List[str]
    language: str
    culture: str

class ProfileResponse(BaseModel):
    fingerprint: Dict[str, float]