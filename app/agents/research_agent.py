from langchain_core.messages import SystemMessage
from langgraph.prebuilt import ToolNode

from app.models.llm import get_llm
from app.tools.agent_tools import RESEARCH_TOOLS


def research_node(state):
    llm = get_llm()
    llm_with_tools = llm.bind_tools(RESEARCH_TOOLS)

    prompt = SystemMessage(content="You are the Research Specialist Agent. Use 'search_knowledge_base' for project files, codenames, launch dates and confidential documents.")

    messages = [prompt] + list(state["messages"])[-10:]
    response = llm_with_tools.invoke(messages)

    if response.tool_calls:
        try:
            tool_node = ToolNode(RESEARCH_TOOLS)
            tool_result = tool_node.invoke({"messages": [response]})
            final_response = llm.invoke(messages + [response] + tool_result["messages"])
            return {"messages": [response] + tool_result["messages"] + [final_response]}
        except Exception:
            return {"messages": [response]}

    return {"messages": [response]}
