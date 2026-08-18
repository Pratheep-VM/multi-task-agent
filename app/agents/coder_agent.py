from langchain_core.messages import SystemMessage
from langgraph.prebuilt import ToolNode

from app.models.llm import get_llm
from app.tools.agent_tools import CODER_TOOLS


def coder_node(state):
    llm = get_llm()
    llm_with_tools = llm.bind_tools(CODER_TOOLS)
    prompt = SystemMessage(content="You are the Math Specialist. Use 'calculate_math' for calculations.")

    messages = [prompt] + list(state["messages"])[-10:]
    response = llm_with_tools.invoke(messages)

    if response.tool_calls:
        try:
            tool_node = ToolNode(CODER_TOOLS)
            tool_result = tool_node.invoke({"messages": [response]})
            final_response = llm.invoke(messages + [response] + tool_result["messages"])
            return {"messages": [response] + tool_result["messages"] + [final_response]}
        except Exception:
            return {"messages": [response]}

    return {"messages": [response]}
