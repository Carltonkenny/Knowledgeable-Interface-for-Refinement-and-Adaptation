# agents/intent.py
# ─────────────────────────────────────────────
# Intent Analyzer Agent
#
# Job: Figure out what the user ACTUALLY wants.
# Input: raw_prompt from AgentState
# Output: intent_result dict written to AgentState
#
# Sends one prompt to Mistral, parses JSON back.
# ─────────────────────────────────────────────

import json
from langchain_core.messages import SystemMessage, HumanMessage
from config import get_llm
from state import AgentState

# What we tell Mistral to be
SYSTEM_PROMPT = """You are an Intent Analyzer. 
Your job is to analyze a user's prompt and extract their true intent.

Always respond with ONLY this JSON, no extra text:
{
  "primary_intent": "the main thing they want to accomplish",
  "secondary_intents": ["other goals detected"],
  "goal_clarity": "low or medium or high",
  "missing_info": ["what info is missing to fulfill this properly"]
}"""


def intent_agent(state: AgentState) -> dict:
    """
    Analyzes the raw prompt and returns intent breakdown.
    LangGraph calls this function and merges the returned
    dict into the shared AgentState automatically.
    """
    llm = get_llm()

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Analyze this prompt: {state['raw_prompt']}")
    ]

    response = llm.invoke(messages)

    # Parse Mistral's response as JSON
    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        # Fallback if Mistral adds extra text around the JSON
        import re
        match = re.search(r'\{.*\}', response.content, re.DOTALL)
        result = json.loads(match.group()) if match else {}

    return {"intent_result": result}