from fastapi import APIRouter
from api.schemas.profile import ProfileRequest, ProfileResponse
from config.personalization import initialize_fingerprint

router = APIRouter()

@router.post("/create", response_model=ProfileResponse)
def create_profile(payload: ProfileRequest):
    fingerprint = initialize_fingerprint(payload)
    return ProfileResponse(fingerprint=fingerprint)