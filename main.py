"""
FastAPI Server for OnCall Memory: Incident Response Agent.
Serves REST API and single-page dashboard UI.
"""

import time
import logging
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backend.incident_engine import (
    generate_without_memory,
    generate_with_memory,
    record_feedback
)
from backend.memory_client import memory_manager
from backend.sample_data import SAMPLE_INCIDENTS, DEMO_SCENARIOS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("main")

app = FastAPI(
    title="OnCall Memory - Incident Response Agent",
    description="Agentic incident response that remembers past production incidents using Hindsight memory.",
    version="1.0.0"
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# Pydantic Schemas
class AnalyzeRequest(BaseModel):
    alert: str = Field(..., description="Alert title or summary")
    logs: str = Field(..., description="Error stack traces or raw log output")
    service: Optional[str] = Field("checkout-service", description="Target service name")


class FeedbackRequest(BaseModel):
    alert: str
    logs: str
    service: str = "checkout-service"
    fix_status: str = Field(..., description="'SUCCESS' or 'FAILED'")
    solution_notes: str = Field(..., description="What actually fixed it or why it failed")
    suggested_root_cause: Optional[str] = ""


class ReflectRequest(BaseModel):
    query: Optional[str] = "What patterns keep causing our incidents and what should we fix permanently?"


# Routes
@app.get("/")
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="UI index.html not found")
    return FileResponse(index_file)


@app.get("/api/samples")
async def get_samples():
    """Provides sample incidents and guided demo scenarios."""
    return {
        "samples": SAMPLE_INCIDENTS,
        "scenarios": DEMO_SCENARIOS
    }


@app.get("/api/memories/stats")
async def get_memory_stats():
    """Returns live stats on the Hindsight memory bank."""
    return await memory_manager.aget_memory_stats()


@app.get("/api/memories/list")
async def get_memories_list(limit: int = 40):
    """Returns list of all retained incident memories in the live bank."""
    items = await memory_manager.alist_all_memories(limit=limit)
    return {
        "bank_id": memory_manager.bank_id,
        "items": items
    }


@app.post("/api/analyze")
async def analyze_incident(req: AnalyzeRequest):
    """
    Executes the side-by-side incident analysis:
    - Left: Without Memory (Plain Groq LLM, generic textbook advice)
    - Right: With Hindsight Memory (Recalls past incidents from Hindsight Cloud, cites root causes, warns against failed fixes)
    """
    start_time = time.time()

    # 1. Plain LLM without memory
    t0 = time.time()
    without_memory_res = await generate_without_memory(req.alert, req.logs)
    latency_without = round((time.time() - t0) * 1000, 1)
    without_memory_res["latency_ms"] = latency_without

    # 2. Hindsight Memory + Groq LLM
    t1 = time.time()
    with_memory_res = await generate_with_memory(req.alert, req.logs)
    latency_with = round((time.time() - t1) * 1000, 1)
    with_memory_res["latency_ms"] = latency_with

    total_latency = round((time.time() - start_time) * 1000, 1)

    return {
        "status": "success",
        "total_latency_ms": total_latency,
        "without_memory": without_memory_res,
        "with_memory": with_memory_res,
        "memory_bank": memory_manager.bank_id
    }


@app.post("/api/feedback")
async def submit_feedback(req: FeedbackRequest):
    """
    On-call engineer feedback loop:
    Retains the resolution (success or failure) back into live Hindsight Cloud.
    """
    if req.fix_status.upper() not in ["SUCCESS", "FAILED"]:
        raise HTTPException(status_code=400, detail="fix_status must be SUCCESS or FAILED")

    result = await record_feedback(
        alert=req.alert,
        logs=req.logs,
        service=req.service,
        fix_status=req.fix_status,
        solution_notes=req.solution_notes,
        suggested_root_cause=req.suggested_root_cause or ""
    )
    return result


@app.post("/api/insights")
async def get_insights(req: ReflectRequest):
    """
    Uses live Hindsight Reflect to analyze systemic recurring patterns
    and propose permanent architectural remediations.
    """
    query = req.query or "What patterns keep causing our incidents and what should we fix permanently?"
    return await memory_manager.areflect_insights(query=query)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
