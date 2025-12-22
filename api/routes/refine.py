from fastapi import APIRouter
from api.schemas.refinement import RefinementRequest, RefinementResponse
from core.preferences import update_fingerprint

router = APIRouter()

@router.post("/", response_model=RefinementResponse)
def refine(payload: RefinementRequest):
    updated = update_fingerprint(payload.fingerprint, payload.feedback)
    return RefinementResponse(updated_fingerprint=updated)