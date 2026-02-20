# api.py
# ─────────────────────────────────────────────
# FastAPI REST API
#
# Endpoints:
#   GET  /health    → liveness check
#   POST /refine    → improve a prompt
#   GET  /history   → retrieve past prompts
#
# DB is called only here — agents never touch it.
# session_id tracks users across requests.
# ─────────────────────────────────────────────
# api.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Any, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import logging

from graph.workflow import workflow
from state import AgentState
from langchain_core.messages import HumanMessage
from database import save_request, save_agent_logs, save_history, get_history

logger = logging.getLogger(__name__)

# ── Schemas ───────────────────────────────────

class RefineRequest(BaseModel):
    prompt: str = Field(..., min_length=5, max_length=2000)
    session_id: Optional[str] = Field(default="default")


class RefineResponse(BaseModel):
    original_prompt: str
    improved_prompt: str
    breakdown:       dict[str, Any]
    session_id:      str


# ── App ───────────────────────────────────────

app = FastAPI(
    title="PromptForge",
    description="Multi-agent prompt improvement system",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GRAPH_TIMEOUT = 120  # seconds before we give up


# ── Routes ────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


@app.post("/refine", response_model=RefineResponse)
def refine(req: RefineRequest):
    logger.info(f"[api] /refine session={req.session_id} prompt='{req.prompt[:60]}...'")

    try:
        initial_state = AgentState(
            raw_prompt=req.prompt,
            intent_result={},
            context_result={},
            domain_result={},
            improved_prompt="",
            final_response={},
            messages=[HumanMessage(content=req.prompt)]
        )

        # ── Run graph with timeout ────────────
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(workflow.invoke, initial_state)
            try:
                final_state = future.result(timeout=GRAPH_TIMEOUT)
            except TimeoutError:
                logger.error("[api] graph timed out")
                raise HTTPException(status_code=504, detail="Request timed out")

        # ── Save to Supabase ──────────────────
        request_id = save_request(
            raw_prompt=final_state["raw_prompt"],
            improved_prompt=final_state.get("improved_prompt", ""),
            session_id=req.session_id
        )

        if request_id:
            save_agent_logs(request_id, {
                "intent_agent":  final_state.get("intent_result", {}),
                "context_agent": final_state.get("context_result", {}),
                "domain_agent":  final_state.get("domain_result", {}),
            })

        save_history(
            raw_prompt=final_state["raw_prompt"],
            improved_prompt=final_state.get("improved_prompt", ""),
            session_id=req.session_id
        )

        logger.info(f"[api] /refine complete session={req.session_id}")

        return RefineResponse(
            original_prompt=final_state["raw_prompt"],
            improved_prompt=final_state.get("improved_prompt", ""),
            breakdown={
                "intent":  final_state.get("intent_result", {}),
                "context": final_state.get("context_result", {}),
                "domain":  final_state.get("domain_result", {}),
            },
            session_id=req.session_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[api] unhandled error in /refine")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history")
def history(
    session_id: Optional[str] = Query(default=None),
    limit: int = Query(default=10, ge=1, le=100)
):
    logger.info(f"[api] /history session={session_id} limit={limit}")
    data = get_history(session_id=session_id, limit=limit)
    return {"count": len(data), "history": data}