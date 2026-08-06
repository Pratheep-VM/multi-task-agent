import os
import sqlite3
from typing import Annotated, Sequence
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt import ToolNode, tools_condition  # <--- Tool Handlers

from app.models.llm import get_llm
from app.tools.agent_tools import ALL_TOOLS              # <--- Import Tools

# 1. Define Agent State
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

# 2. System Prompt instructing the agent on tool usage
SYSTEM_PROMPT = SystemMessage(
    content=(
        "You are Pradeep's AI, a high-performance personal assistant with access to tools. "
        "If the user asks about private project details, codenames, or launch dates, "
        "use the 'search_knowledge_base' tool to find the answer before responding."
    )
)

# 3. Node Function: Call LLM with Bound Tools
def call_model(state: AgentState) -> dict:
    llm = get_llm()
    # Bind tools to the LLM so it knows what capabilities it possesses
    llm_with_tools = llm.bind_tools(ALL_TOOLS)
    
    messages = [SYSTEM_PROMPT] + list(state["messages"])
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

# 4. Construct Graph Architecture
builder = StateGraph(AgentState)

# Add Nodes
builder.add_node("agent", call_model)
builder.add_node("tools", ToolNode(ALL_TOOLS))  # <--- Automatically executes tool calls!

# Define Edges
builder.add_edge(START, "agent")

# Add Conditional Edge: Agent ──► ToolNode (if tool needed) OR ──► END (if text ready)
builder.add_conditional_edges("agent", tools_condition)

# Edge: Tool Output ──► Loop back to Agent
builder.add_edge("tools", "agent")

# 5. Persistent Memory Database
os.makedirs("data", exist_ok=True)
db_path = os.path.join("data", "memory.db")
conn = sqlite3.connect(db_path, check_same_thread=False)
checkpointer = SqliteSaver(conn)

# 6. Compile Graph
basic_agent = builder.compile(checkpointer=checkpointer)