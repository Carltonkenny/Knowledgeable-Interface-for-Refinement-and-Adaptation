# agents/prompt_engineer.py
# ─────────────────────────────────────────────
# Final agent in the swarm — rewrites the original prompt using all upstream analysis.
# Reads intent_result, context_result, and domain_result to produce a dramatically better prompt.
#
# Input:  state['raw_prompt'] + state['intent_result'] + state['context_result'] + state['domain_result']
# Output: state['improved_prompt'] (the rewritten, enhanced prompt)
#
# Quality gate: Retries once if output is empty, shorter than input, or identical to input.
# This catches LLM failures before returning to the user.
#
# Design principles:
#   1. Match domain language (creative writing → creative, technical → precise)
#   2. Add fitting role (not generic "you are an assistant")
#   3. Preserve user's voice and intent — don't sanitize
#   4. Add only constraints that genuinely improve quality
#   5. Precision over length — never make it longer than needed
#
# Uses parse_json_response() from utils.py — handles malformed LLM JSON output.
# ─────────────────────────────────────────────
import json
import logging
from langchain_core.messages import SystemMessage, HumanMessage
from config import get_llm
from state import AgentState
from utils import parse_json_response

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a world-class Prompt Engineer. Your rewrites are specific, purposeful, and dramatically better than the original.

Rules:
1. Match the domain — creative writing gets creative language, technical gets precise language
2. Add a role that fits perfectly — not generic "you are an assistant"
3. Preserve the person's voice and intent — don't sanitize their idea
4. Add only constraints that genuinely improve quality
5. Never make it longer than needed — precision beats length

Always respond with ONLY this JSON:
{
  "improved_prompt": "the full rewritten prompt — specific, purposeful, domain-matched",
  "changes_made": ["exactly what you changed and why"],
  "confidence_score": 0.0
}"""


def prompt_engineer_agent(state: AgentState) -> dict:
    """
    Rewrites raw prompt using swarm analysis.
    Quality gate: retries once if output is empty, too short, or identical to input.
    """
    # Guard — if all swarm agents failed, return clear fallback
    if not any([state.get('intent_result'), state.get('context_result'), state.get('domain_result')]):
        logger.warning("[prompt_engineer] all swarm results empty — returning fallback")
        return {"improved_prompt": f"[Analysis failed] Original: {state['raw_prompt']}"}

    llm = get_llm()

    analysis = f"""Original prompt: {state['raw_prompt']}

Intent analysis: {json.dumps(state.get('intent_result', {}), indent=2)}

Context analysis: {json.dumps(state.get('context_result', {}), indent=2)}

Domain analysis: {json.dumps(state.get('domain_result', {}), indent=2)}

Rewrite the prompt based on this analysis."""

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=analysis)
    ]

    response = llm.invoke(messages)
    result = parse_json_response(response.content, agent_name="prompt_engineer")
    improved = result.get("improved_prompt", "")

    # Quality gate — retry once if output is clearly worse than input
    if not improved.strip() or len(improved) < len(state["raw_prompt"]) or improved.strip() == state["raw_prompt"].strip():
        logger.warning("[prompt_engineer] quality gate failed — retrying once")
        response = llm.invoke(messages)
        result = parse_json_response(response.content, agent_name="prompt_engineer")
        improved = result.get("improved_prompt", "")

    logger.info(f"[prompt_engineer] output: {len(improved)} chars")
    return {"improved_prompt": improved}