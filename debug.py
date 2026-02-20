# debug.py
from graph.workflow import workflow
from state import AgentState
from langchain_core.messages import HumanMessage

state = AgentState(
    raw_prompt="write me a python script",
    intent_result={},
    context_result={},
    domain_result={},
    improved_prompt="",
    final_response={},
    messages=[HumanMessage(content="write me a python script")]
)

result = workflow.invoke(state)
print(result)