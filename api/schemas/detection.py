from pydantic import BaseModel
from typing import List, Dict

class AnalyzeRequest(BaseModel):
    text: str
    language: str

class AnalyzeResponse(BaseModel):
    sensory_spans: List[Dict]
    difficulty_scores: List[float]