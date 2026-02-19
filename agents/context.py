# agents/context.py
# ─────────────────────────────────────────────
# Context Extractor Agent
#
# Job: Understand WHO is asking and their constraints.
# Input: raw_prompt from AgentState
# Output: context_result dict written to AgentState
# ─────────────────────────────────────────────

import json
import re
from langchain_core.messages import SystemMessage, HumanMessage
from config import get_llm
from state import AgentState

SYSTEM_PROMPT = """You are a Context Extractor.
Your job is to analyze a user's prompt and extract context about the user.

Always respond with ONLY this JSON, no extra text:
{
  "skill_level": "beginner or intermediate or expert",
  "tone": "casual or formal or technical",
  "constraints": ["any limitations or requirements mentioned"],
  "implicit_preferences": ["preferences implied but not stated"]
}"""


def context_agent(state: AgentState) -> dict:
    """
    Extracts user context from the raw prompt.
    """
    llm = get_llm()

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Extract context from this prompt: {state['raw_prompt']}")
    ]

    response = llm.invoke(messages)

    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', response.content, re.DOTALL)
        result = json.loads(match.group()) if match else {}

    return {"context_result": result}