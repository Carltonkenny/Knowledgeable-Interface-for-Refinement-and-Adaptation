# agents/domain.py
# ─────────────────────────────────────────────
# Domain Identifier Agent
#
# Job: Classify what field/domain the prompt belongs to.
# Input: raw_prompt from AgentState
# Output: domain_result dict written to AgentState
# ─────────────────────────────────────────────

import json
import re
from langchain_core.messages import SystemMessage, HumanMessage
from config import get_llm
from state import AgentState

SYSTEM_PROMPT = """You are a Domain Identifier.
Your job is to classify what domain or field a user's prompt belongs to.

Always respond with ONLY this JSON, no extra text:
{
  "primary_domain": "the main field e.g. software engineering, writing, math",
  "sub_domain": "more specific area e.g. Python scripting, creative writing",
  "relevant_patterns": ["prompt patterns that apply e.g. code generation, explanation"],
  "complexity": "simple or moderate or complex"
}"""


def domain_agent(state: AgentState) -> dict:
    """
    Identifies the domain and complexity of the raw prompt.
    """
    llm = get_llm()

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Identify the domain of this prompt: {state['raw_prompt']}")
    ]

    response = llm.invoke(messages)

    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', response.content, re.DOTALL)
        result = json.loads(match.group()) if match else {}

    return {"domain_result": result}