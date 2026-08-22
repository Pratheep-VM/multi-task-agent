import os
from typing import Annotated, Sequence
from dotenv import load_dotenv
load_dotenv()

from mudraid import Agent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from app.models.llm import get_llm

supervisor_client = Agent(
    api_key_id=os.getenv("SUPERVISOR_KEY_ID"),
    secret=os.getenv("SUPERVISOR_SECRET"),
    base_url=os.getenv("MUDRAID_BASE_URL", "https://api.staging.mudraid.ai")
)


class MultiAgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next_step: str


def supervisor_node(state: MultiAgentState) -> dict:
    try:
        messages = list(state["messages"])
        last_message = messages[-1] if messages else None

        if isinstance(last_message, AIMessage) and not last_message.tool_calls:
            return {"next_step": "FINISH"}

        last_user_input = ""
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage) and msg.content:
                last_user_input = str(msg.content).lower()
                break

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

        conversational_response = llm.invoke(recent_messages)
        return {"next_step": "FINISH", "messages": [conversational_response]}

    except Exception:
        llm = get_llm()
        fallback_response = llm.invoke(list(state["messages"])[-10:])
        return {"next_step": "FINISH", "messages": [fallback_response]}
