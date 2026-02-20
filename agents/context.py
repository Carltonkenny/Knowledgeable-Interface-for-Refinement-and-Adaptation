# agents/context.py
# ─────────────────────────────────────────────
# Second agent in the swarm — analyzes WHO is asking and their constraints.
# Reads between the lines to identify skill level, tone, and implicit preferences.
#
# Input:  state['raw_prompt'] (user's original prompt)
# Output: state['context_result'] with fields:
#   - skill_level          → "beginner" | "intermediate" | "expert"
#   - tone                 → "casual" | "formal" | "technical" | "creative"
#   - constraints          → Real limitations mentioned or strongly implied
#   - implicit_preferences → What the person values based on how they wrote the prompt
#
# Key insight: Word choice reveals expertise.
#   - "thing" vs "module" vs "microservice" → signals different skill levels
#   - Specificity signals clarity of thinking
#   - "Write a 300-word opening scene with atmosphere" → expert, creative, values craft
#
# Uses parse_json_response() from utils.py — handles malformed LLM JSON output.
# ─────────────────────────────────────────────
import logging
from langchain_core.messages import SystemMessage, HumanMessage
from config import get_fast_llm
from state import AgentState
from utils import parse_json_response

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert Context Extractor who reads between the lines.

Identify not just what is stated but what the person reveals about themselves through word choice, specificity, and framing.

Always respond with ONLY this JSON:
{
  "skill_level": "beginner or intermediate or expert",
  "tone": "casual or formal or technical or creative",
  "constraints": ["real limitations mentioned or strongly implied"],
  "implicit_preferences": ["what this person clearly values based on how they wrote the prompt"]
}

Think deeply:
- Word choice reveals expertise — "thing" vs "module" vs "microservice"
- Specificity reveals clarity of thinking
- Length reveals how much they know about what they want
- "Write a 300-word opening scene with atmosphere and tension" → expert, creative, values craft over speed
"""

def context_agent(state: AgentState) -> dict:
    logger.info("[context] extracting user context")

    llm = get_fast_llm()
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Extract context from: {state['raw_prompt']}")
    ]

    response = llm.invoke(messages)
    result = parse_json_response(response.content, agent_name="context")

    logger.info(f"[context] skill={result.get('skill_level', 'unknown')}")
    return {"context_result": result}