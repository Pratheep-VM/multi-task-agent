from app.tools.research_tools import search_knowledge_base
from app.tools.coder_tools import calculate_math
from app.tools.website_api_tools import (
    create_task,
    list_tasks,
    modify_task,
    remove_task,
)

RESEARCH_TOOLS = [search_knowledge_base]
CODER_TOOLS = [calculate_math]
WEBSITE_TOOLS = [list_tasks, create_task, modify_task, remove_task]
ALL_TOOLS = RESEARCH_TOOLS + CODER_TOOLS + WEBSITE_TOOLS

__all__ = [
    "search_knowledge_base",
    "calculate_math",
    "list_tasks",
    "create_task",
    "modify_task",
    "remove_task",
    "RESEARCH_TOOLS",
    "CODER_TOOLS",
    "WEBSITE_TOOLS",
    "ALL_TOOLS",
]