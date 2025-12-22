from fastapi import APIRouter
from api.schemas.rewrite import RewriteResponse
from demo.loader import load_demo_example

router = APIRouter()

@router.get("/{persona_id}", response_model=RewriteResponse)
def demo_run(persona_id: str):
    return load_demo_example(persona_id)