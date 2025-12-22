from fastapi import APIRouter, Depends
from api.schemas.rewrite import RewriteRequest, RewriteResponse
from api.dependencies import get_user_fingerprint
from core.pipeline import run_rewrite_pipeline

router = APIRouter()

@router.post("/", response_model=RewriteResponse)
def rewrite_text(payload: RewriteRequest, fingerprint=Depends(get_user_fingerprint)):
    result = run_rewrite_pipeline(payload.text, payload.language, payload.culture, fingerprint)
    return RewriteResponse(**result)