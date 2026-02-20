# agents/intent.py
# ─────────────────────────────────────────────
# First agent in the swarm — analyzes WHAT the user wants to accomplish.
# Goes beyond literal words to extract the real goal and emotional intent.
#
# Input:  state['raw_prompt'] (user's original prompt)
# Output: state['intent_result'] with fields:
#   - primary_intent   → The deep actual goal (e.g., "create emotionally engaging narrative")
#   - secondary_intents → Supporting goals that matter
#   - goal_clarity     → "low" | "medium" | "high"
#   - missing_info     → Specific details that would make the prompt better
#
# Example transformation:
#   "write a story" → primary_intent: "create an emotionally engaging narrative that resonates"
#   "fix my code"   → primary_intent: "understand why code fails and learn to prevent it"
#
# Uses parse_json_response() from utils.py — handles malformed LLM JSON output.
# ─────────────────────────────────────────────

import logging
from langchain_core.messages import SystemMessage, HumanMessage
from config import get_fast_llm
from state import AgentState
from utils import parse_json_response

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert Intent Analyzer specializing in understanding what people truly want to accomplish.

Go beyond the literal words — extract the real goal, emotional intent, and success criteria.

Always respond with ONLY this JSON:
{
  "primary_intent": "the deep actual goal, not just surface request",
  "secondary_intents": ["supporting goals that matter"],
  "goal_clarity": "low or medium or high",
  "missing_info": ["specific missing details that would make this prompt significantly better"]
}

Think deeply:
- "write a story" → primary_intent: "create an emotionally engaging narrative that resonates with readers"
- "fix my code" → primary_intent: "understand why code fails and learn to prevent it"
- "help me with python" → primary_intent: "build confidence and competence in Python programming"
"""


def intent_agent(state: AgentState) -> dict:
    logger.info("[intent] analyzing prompt intent")

    llm = get_fast_llm()
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Analyze this prompt: {state['raw_prompt']}")
    ]

    response = llm.invoke(messages)
    result = parse_json_response(response.content, agent_name="intent")

    logger.info(f"[intent] clarity={result.get('goal_clarity', 'unknown')}")
    return {"intent_result": result}