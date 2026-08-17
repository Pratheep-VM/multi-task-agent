import os
import sqlite3
from typing import Annotated, Sequence
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt import ToolNode

from app.models.llm import get_llm
from app.tools.agent_tools import RESEARCH_TOOLS, CODER_TOOLS, WEBSITE_TOOLS

# 1. State Schema
class MultiAgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next_step: str

# -------------------------------------------------------------------
# NODE 1: SUPERVISOR AGENT 
# -------------------------------------------------------------------
def supervisor_node(state: MultiAgentState) -> dict:
    try:
        messages = list(state["messages"])
        last_message = messages[-1] if messages else None

        # 1. If an agent already provided a final text answer, FINISH
        if isinstance(last_message, AIMessage) and not last_message.tool_calls:
            return {"next_step": "FINISH"}

        # 2. Extract ONLY the last HumanMessage for routing
        last_user_input = ""
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage) and msg.content:
                last_user_input = str(msg.content).lower()
                break

        # LAYER 1: KEYWORD ROUTER
        task_keywords = [
            "task", "tasks", "todo", "api", "http", "endpoint", 
            "list", "create", "add", "delete", "remove", "modify", 
            "update", "meeting", "portal", "system", "management"
        ]
        research_keywords = [
            "launch date", "codename", "project file", "confidential", 
            "secret", "knowledge base", "document", "specifications"
        ]
        math_keywords = [
            "calculate", "math", "plus", "minus", "multiply", 
            "divide", "equation", "power", "algebra"
        ]

        if any(keyword in last_user_input for keyword in task_keywords):
            return {"next_step": "WebsiteApiAgent"}

        if any(keyword in last_user_input for keyword in research_keywords):
            return {"next_step": "ResearchAgent"}

        if any(keyword in last_user_input for keyword in math_keywords):
            return {"next_step": "CoderAgent"}

        # LAYER 2: PURE TEXT LLM CLASSIFIER
        llm = get_llm(temperature=0.0)
        supervisor_prompt = (
            "You are a routing supervisor. Choose EXACTLY ONE destination:\n"
            "- 'WebsiteApiAgent'\n"
            "- 'ResearchAgent'\n"
            "- 'CoderAgent'\n"
            "- 'FINISH'\n\n"
            "Respond with ONLY ONE WORD."
        )
        
        recent_messages = messages[-10:]
        prompt_messages = [SystemMessage(content=supervisor_prompt)] + recent_messages
        response = llm.invoke(prompt_messages)
        route_output = str(response.content).strip().replace("'", "").replace('"', "")
        
        for valid_route in ["WebsiteApiAgent", "ResearchAgent", "CoderAgent"]:
            if valid_route.lower() in route_output.lower():
                return {"next_step": valid_route}
                
        # CONVERSATIONAL CHAT FALLBACK
        conversational_response = llm.invoke(recent_messages)
        return {"next_step": "FINISH", "messages": [conversational_response]}

    except Exception:
        llm = get_llm()
        fallback_response = llm.invoke(list(state["messages"])[-10:])
        return {"next_step": "FINISH", "messages": [fallback_response]}

# -------------------------------------------------------------------
# NODE 2: RESEARCH AGENT
# -------------------------------------------------------------------
def research_node(state: MultiAgentState) -> dict:
    llm = get_llm()
    llm_with_tools = llm.bind_tools(RESEARCH_TOOLS)
    
    prompt = SystemMessage(content="You are the Research Specialist Agent. Use 'search_knowledge_base' for project files, codenames, launch dates and confidential documents.")
    
    messages = [prompt] + list(state["messages"])[-10:]
    response = llm_with_tools.invoke(messages)
    
    if response.tool_calls:
        try:
            tool_node = ToolNode(RESEARCH_TOOLS)
            tool_result = tool_node.invoke({"messages": [response]})
            # Pass tool output back to LLM to generate final response
            final_response = llm.invoke(messages + [response] + tool_result["messages"])
            return {"messages": [response] + tool_result["messages"] + [final_response]}
        except Exception:
            return {"messages": [response]}
            
    return {"messages": [response]}

# -------------------------------------------------------------------
# NODE 3: CODER AGENT
# -------------------------------------------------------------------
def coder_node(state: MultiAgentState) -> dict:
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

# -------------------------------------------------------------------
# NODE 4: WEBSITE API AGENT
# -------------------------------------------------------------------
def website_api_node(state: MultiAgentState) -> dict:
    llm = get_llm()
    llm_with_tools = llm.bind_tools(WEBSITE_TOOLS)
    prompt = SystemMessage(content="You are the Web API Specialist. Use task tools ('create_task', 'list_tasks') to manage tasks.")
    
    messages = [prompt] + list(state["messages"])[-10:]
    response = llm_with_tools.invoke(messages)
    
    if response.tool_calls:
        try:
            tool_node = ToolNode(WEBSITE_TOOLS)
            tool_result = tool_node.invoke({"messages": [response]})
            final_response = llm.invoke(messages + [response] + tool_result["messages"])
            return {"messages": [response] + tool_result["messages"] + [final_response]}
        except Exception:
            return {"messages": [response]}
            
    return {"messages": [response]}

# -------------------------------------------------------------------
# BUILD MULTI-AGENT GRAPH
# -------------------------------------------------------------------
builder = StateGraph(MultiAgentState)

builder.add_node("Supervisor", supervisor_node)
builder.add_node("ResearchAgent", research_node)
builder.add_node("CoderAgent", coder_node)
builder.add_node("WebsiteApiAgent", website_api_node)

builder.add_edge(START, "Supervisor")

def route_supervisor(state: MultiAgentState) -> str:
    next_step = state.get("next_step", "FINISH")
    if next_step == "FINISH":
        return END
    return next_step

builder.add_conditional_edges(
    "Supervisor", 
    route_supervisor, 
    {
        "ResearchAgent": "ResearchAgent", 
        "CoderAgent": "CoderAgent", 
        "WebsiteApiAgent": "WebsiteApiAgent",
        END: END
    }
)

builder.add_edge("ResearchAgent", "Supervisor")
builder.add_edge("CoderAgent", "Supervisor")
builder.add_edge("WebsiteApiAgent", "Supervisor")


os.makedirs("data", exist_ok=True)
conn = sqlite3.connect(
    os.path.join("data", "memory.db"), 
    timeout=30.0,                # Wait up to 30 seconds if DB is busy
    check_same_thread=False
)
conn.execute("PRAGMA journal_mode=WAL;")  # WAL mode allows concurrent reads/writes
checkpointer = SqliteSaver(conn)