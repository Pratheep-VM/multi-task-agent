import os
import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

from app.agents.supervisor import MultiAgentState, supervisor_node
from app.agents.research_agent import research_node
from app.agents.coder_agent import coder_node
from app.agents.website_api_agent import website_api_node

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
        END: END,
    },
)

builder.add_edge("ResearchAgent", "Supervisor")
builder.add_edge("CoderAgent", "Supervisor")
builder.add_edge("WebsiteApiAgent", "Supervisor")

os.makedirs("data", exist_ok=True)
conn = sqlite3.connect(
    os.path.join("data", "memory.db"),
    timeout=30.0,
    check_same_thread=False,
)
conn.execute("PRAGMA journal_mode=WAL;")
checkpointer = SqliteSaver(conn)

multi_agent_system = builder.compile(checkpointer=checkpointer)
