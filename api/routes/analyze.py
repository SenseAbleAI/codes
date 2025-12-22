from fastapi import APIRouter, Depends
from api.schemas.detection import AnalyzeRequest, AnalyzeResponse
from api.dependencies import get_user_fingerprint
from core.detector import detect_sensory_spans
from core.difficulty import score_difficulty

router = APIRouter()

@router.post("/", response_model=AnalyzeResponse)
def analyze_text(payload: AnalyzeRequest, fingerprint=Depends(get_user_fingerprint)):
    spans = detect_sensory_spans(payload.text, payload.language)
    scores = score_difficulty(spans, fingerprint)
    return AnalyzeResponse(sensory_spans=spans, difficulty_scores=scores)