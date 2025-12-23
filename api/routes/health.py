from fastapi import APIRouter
from core.agents.utils.azure_copilot import AzureCopilotClient

router = APIRouter()


@router.get("/live")
def liveness():
    return {"status": "alive"}


@router.get("/ready")
def readiness():
    # Basic readiness: check optional external dependencies conservatively
    copilot = AzureCopilotClient()
    features = {"azure_copilot": copilot.available()}
    overall = "ok" if all(features.values()) or not any(features.values()) else "degraded"
    return {"status": overall, "features": features}


@router.get("/")
def health_check():
    return {"status": "ok"}