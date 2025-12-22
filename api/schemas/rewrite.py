from pydantic import BaseModel
from typing import List

class RewriteRequest(BaseModel):
    text: str
    language: str
    culture: str

class RewriteResponse(BaseModel):
    original: str
    alternatives: List[str]
    strategy: str