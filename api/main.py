from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
import logging

from api.routes import health, profile, analyze, rewrite, refine, demo
from core.agents.utils.azure_copilot import AzureCopilotClient


logger = logging.getLogger("api")


app = FastAPI(title="SenseAble API", version="1.0")

# CORS: allow all origins for development; lock this down in production
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
	return JSONResponse(status_code=422, content={"detail": exc.errors(), "body": exc.body})


@app.on_event("startup")
def startup_event():
	# Lightweight readiness hints — do not log secrets
	copilot = AzureCopilotClient()
	logger.info("Startup: Azure Copilot available=%s", copilot.available())


app.include_router(health.router, prefix="/health")
app.include_router(profile.router, prefix="/profile")
app.include_router(analyze.router, prefix="/analyze")
app.include_router(rewrite.router, prefix="/rewrite")
app.include_router(refine.router, prefix="/refine")
app.include_router(demo.router, prefix="/demo")