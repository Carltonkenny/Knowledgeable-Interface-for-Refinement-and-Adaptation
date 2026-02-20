# agents/domain.py
# ─────────────────────────────────────────────
# Domain Identifier Agent
#
# Job: Classify what field/domain the prompt belongs to.
# Input: raw_prompt from AgentState
# Output: domain_result dict written to AgentState
# ─────────────────────────────────────────────

# agents/domain.py
import logging
from langchain_core.messages import SystemMessage, HumanMessage
from config import get_llm
from state import AgentState
from utils import parse_json_response

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert Domain Identifier who classifies requests with precision.

Go beyond obvious labels — identify the specific craft, discipline, and patterns that apply.

Always respond with ONLY this JSON:
{
  "primary_domain": "precise field name",
  "sub_domain": "specific discipline within that field",
  "relevant_patterns": ["the prompt engineering patterns that will make this better"],
  "complexity": "simple or moderate or complex"
}

Relevant patterns to consider:
- role_assignment: give the AI a specific expert persona
- output_format: specify exactly how the response should look
- constraints: add quality guardrails
- examples: include what good looks like
- chain_of_thought: ask for reasoning steps
- tone_matching: match the creative/technical register

Example:
- sci-fi mystery story → primary_domain: creative writing, patterns: [role_assignment, tone_matching, output_format, constraints]
"""


def domain_agent(state: AgentState) -> dict:
    logger.info("[domain] identifying domain")

    llm = get_llm()
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Identify the domain of: {state['raw_prompt']}")
    ]

    response = llm.invoke(messages)
    result = parse_json_response(response.content, agent_name="domain")

    logger.info(f"[domain] domain={result.get('primary_domain', 'unknown')}")
    return {"domain_result": result}