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

SYSTEM_PROMPT = """You are an expert Prompt Engineer.
You will receive a raw user prompt and a full analysis of it.
Your job is to rewrite the prompt into a significantly better version.

A good prompt:
- Has a clear role/persona for the AI
- Specifies the exact output format needed
- Includes relevant constraints
- Is specific, not vague
- Matches the user's skill level and domain

Always respond with ONLY this JSON, no extra text:
{
  "improved_prompt": "the full rewritten prompt here",
  "changes_made": ["change 1", "change 2", "change 3"],
  "confidence_score": 0.0
}"""


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