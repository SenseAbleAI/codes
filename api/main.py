from fastapi import FastAPI
from api.routes import health, profile, analyze, rewrite, refine, demo

app = FastAPI(title="SenseAble API", version="1.0")

app.include_router(health.router, prefix="/health")
app.include_router(profile.router, prefix="/profile")
app.include_router(analyze.router, prefix="/analyze")
app.include_router(rewrite.router, prefix="/rewrite")
app.include_router(refine.router, prefix="/refine")
app.include_router(demo.router, prefix="/demo")