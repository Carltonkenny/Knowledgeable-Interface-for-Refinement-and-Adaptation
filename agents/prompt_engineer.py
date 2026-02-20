# agents/prompt_engineer.py
# ─────────────────────────────────────────────
# Prompt Engineer Agent
#
# Job: Takes everything the swarm found out and
#      rewrites the original prompt into a much
#      better, clearer, more effective version.
#
# Input:  raw_prompt + intent + context + domain
# Output: improved_prompt written to AgentState
# ─────────────────────────────────────────────

import json
import re
from langchain_core.messages import SystemMessage, HumanMessage
from config import get_llm
from state import AgentState

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
}

The improved_prompt should feel like it was written by someone who deeply understands both the domain AND prompt engineering — not a generic template.
"""


def prompt_engineer_agent(state: AgentState) -> dict:
    """
    Uses swarm analysis to rewrite the original prompt.
    This is the final agent before the Supervisor returns
    the result to the user.
    """
    llm = get_llm()

    # Package all swarm results for the LLM to use
    analysis = f"""
Original prompt: {state['raw_prompt']}

Intent analysis: {json.dumps(state.get('intent_result', {}), indent=2)}

Context analysis: {json.dumps(state.get('context_result', {}), indent=2)}

Domain analysis: {json.dumps(state.get('domain_result', {}), indent=2)}

Now rewrite the prompt based on all this information.
"""

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=analysis)
    ]

    response = llm.invoke(messages)

    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', response.content, re.DOTALL)
        result = json.loads(match.group()) if match else {
            "improved_prompt": response.content,
            "changes_made": [],
            "confidence_score": 0.0
        }

    return {"improved_prompt": result.get("improved_prompt", "")}