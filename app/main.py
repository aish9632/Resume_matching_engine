from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.pipeline.matching_pipeline import run_match

app = FastAPI(
    title="Explainable Resume–Job Matching Engine",
    description="Evidence-aware hybrid candidate-job matching with explainable requirement-level reasoning.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MatchRequest(BaseModel):
    candidate_id: str
    job_id: str


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "resume-matching-engine",
        "version": "1.0.0",
    }


@app.post("/matches")
def create_match(request: MatchRequest):
    try:
        result = run_match(request.candidate_id, request.job_id)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Matching failed: {exc}",
        )


@app.get("/")
def root():
    return {
        "service": "Explainable Resume–Job Matching Engine",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "version": "1.0.0",
    }
