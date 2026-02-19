from config import get_llm
from langchain_core.messages import HumanMessage

llm = get_llm()
response = llm.invoke([HumanMessage(content="Reply with just: API working")])
print(response.content)