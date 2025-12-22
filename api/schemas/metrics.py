from pydantic import BaseModel

class MetricScore(BaseModel):
    semantic_similarity: float
    entailment_score: float
    accessibility_gain: float