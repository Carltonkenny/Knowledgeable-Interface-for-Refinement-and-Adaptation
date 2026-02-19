# api.py
# ─────────────────────────────────────────────
# FastAPI REST API
#
# Single endpoint:
#   POST /refine  → takes raw prompt, returns improved prompt + breakdown
#
# Schemas (Pydantic) and routes are in one file
# since we only have one endpoint — keeps it simple.
# ─────────────────────────────────────────────

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Any
from graph.workflow import workflow
from state import AgentState
from langchain_core.messages import HumanMessage


# ── Request / Response schemas ────────────────

class RefineRequest(BaseModel):
    prompt: str = Field(
        ...,
        min_length=5,
        max_length=2000,
        examples=["write me a python thing that reads files"]
    )


class RefineResponse(BaseModel):
    original_prompt: str
    improved_prompt: str
    breakdown:       dict[str, Any]


# ── App setup ─────────────────────────────────

app = FastAPI(
    title="PromptForge",
    description="Multi-agent prompt improvement system",
    version="1.0.0"
)

# Allow all origins for dev — tighten in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ────────────────────────────────────

@app.get("/health")
def health():
    """Quick liveness check."""
    return {"status": "ok"}


@app.post("/refine", response_model=RefineResponse)
def refine(req: RefineRequest):
    """
    Takes a raw prompt, runs it through the multi-agent
    swarm, and returns an improved version with full breakdown.
    """
    try:
        # Build initial state
        initial_state = AgentState(
            raw_prompt=req.prompt,
            intent_result={},
            context_result={},
            domain_result={},
            improved_prompt="",
            final_response={},
            messages=[HumanMessage(content=req.prompt)]
        )

        # Run the graph
        final_state = workflow.invoke(initial_state)

        return RefineResponse(
            original_prompt=final_state["raw_prompt"],
            improved_prompt=final_state.get("improved_prompt", ""),
            breakdown={
                "intent":  final_state.get("intent_result", {}),
                "context": final_state.get("context_result", {}),
                "domain":  final_state.get("domain_result", {}),
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))