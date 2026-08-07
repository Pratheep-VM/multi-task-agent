import os
import math
import mudraid
from langchain_core.tools import tool
from app.services.rag_services import get_vector_store

# 1. Initialize MudraID Client safely
try:
    client = mudraid.Agent()
except Exception:
    client = mudraid.Agent(
        api_key_id=os.getenv("MUDRAID_API_KEY_ID", "test_key"),
        secret=os.getenv("MUDRAID_SECRET", "test_secret")
    )

BASE_URL = "http://13.235.48.164:8011/api/v1/tasks"  

# -------------------------------------------------------------------
# RAG TOOL
# -------------------------------------------------------------------
@tool
def search_knowledge_base(query: str) -> str:
    """Searches Pradeep's confidential project documents, launch dates, codenames, and private files."""
    try:
        vector_store = get_vector_store()
        results = vector_store.similarity_search(query, k=2)
        if not results:
            return "No matching information found in the private knowledge base."
        context = "\n---\n".join([doc.page_content for doc in results])
        return f"Retrieved Private Context:\n{context}"
    except Exception as e:
        return f"Error reading knowledge base: {str(e)}"

# -------------------------------------------------------------------
# MATH TOOL
# -------------------------------------------------------------------
@tool
def calculate_math(expression: str) -> str:
    """Evaluates mathematical expressions using Python."""
    try:
        allowed_names = {"math": math, "abs": abs, "round": round, "pow": pow}
        result = eval(expression, {"__builtins__": None}, allowed_names)
        return f"Math Result: {result}"
    except Exception as e:
        return f"Error evaluating expression: {str(e)}"

# -------------------------------------------------------------------
# TASK MANAGEMENT WEBSITE API TOOLS
# -------------------------------------------------------------------
@tool
def list_tasks() -> str:
    """Lists all tasks from the Task Management System."""
    try:
        response = client.get(BASE_URL)
        return f"Tasks:\n{response.text}"
    except Exception as e:
        return f"Error fetching tasks: {str(e)}"

@tool
def create_task(title: str) -> str:
    """Creates a new task in the Task Management System."""
    try:
        response = client.post(BASE_URL, json={"title": title})
        return f"Task Created:\n{response.text}"
    except Exception as e:
        return f"Error creating task: {str(e)}"

@tool
def modify_task(task_id: str, title: str) -> str:
    """Modifies an existing task by task_id in the Task Management System."""
    try:
        url = f"{BASE_URL}/{task_id}"
        response = client.put(url, json={"title": title})
        return f"Task Modified:\n{response.text}"
    except Exception as e:
        return f"Error modifying task: {str(e)}"

@tool
def remove_task(task_id: str) -> str:
    """Removes a task by task_id from the Task Management System."""
    try:
        url = f"{BASE_URL}/{task_id}"
        response = client.delete(url)
        return f"Task #{task_id} Removed:\n{response.text}"
    except Exception as e:
        return f"Error removing task: {str(e)}"
@tool
def brave_search(query: str) -> str:
    """Searches the internet for current events or general knowledge."""
    return f"Simulated search results for: {query}. (Note: Real web search API not yet connected)."


# -------------------------------------------------------------------
# EXPORT TOOLSETS FOR WORKERS
# -------------------------------------------------------------------
RESEARCH_TOOLS = [search_knowledge_base, brave_search]
CODER_TOOLS = [calculate_math]
WEBSITE_TOOLS = [list_tasks, create_task, modify_task, remove_task]