from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import assess, documents, quiz
from app.config import settings

app = FastAPI(title="GapGraph API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api", tags=["graph"])
app.include_router(quiz.router, prefix="/api", tags=["quiz"])
app.include_router(assess.router, prefix="/api", tags=["assess"])


@app.get("/api/health")
async def health() -> dict:
    return {
        "ok": True,
        "mock_extraction": settings.mock_extraction,
        "mock_learner": settings.mock_learner,
        "model": settings.claude_model,
    }
