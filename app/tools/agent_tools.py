import os
import ast
import html
import operator
from mudraid import Agent
from langchain_core.tools import tool
from app.services.rag_services import get_vector_store

client = Agent()  # reads MUDRAID_API_KEY_ID and MUDRAID_SECRET from .env automatically

BASE_URL = "https://pradeepplatform.mudraidtesting.online/api/v1/tasks"

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
        return f"Retrieved Private Context:\n{html.escape(context)}"
    except Exception as e:
        return f"Error reading knowledge base: {str(e)}"

# -------------------------------------------------------------------
# MATH TOOL
# -------------------------------------------------------------------
_SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}

def _safe_eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPERATORS:
        return _SAFE_OPERATORS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPERATORS:
        return _SAFE_OPERATORS[type(node.op)](_safe_eval(node.operand))
    raise ValueError(f"Unsafe operation: {type(node).__name__}")

@tool
def calculate_math(expression: str) -> str:
    """Evaluates mathematical expressions safely."""
    try:
        tree = ast.parse(expression, mode="eval")
        result = _safe_eval(tree.body)
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
        response = client.get(BASE_URL, timeout=10)
        response.raise_for_status()
        return f"Tasks:\n{html.escape(response.text)}"
    except Exception as e:
        return f"Error fetching tasks: {str(e)}"

@tool
def create_task(title: str) -> str:
    """Creates a new task in the Task Management System."""
    try:
        response = client.post(BASE_URL, json={"title": title}, timeout=10)
        response.raise_for_status()
        return f"Task Created Successfully:\n{html.escape(response.text)}"
    except Exception as e:
        return f"Error creating task: {str(e)}"

@tool
def modify_task(task_id: str, title: str) -> str:
    """Modifies an existing task by task_id in the Task Management System."""
    try:
        url = f"{BASE_URL}/{task_id}"
        response = client.put(url, json={"title": title}, timeout=10)
        response.raise_for_status()
        return f"Task Modified Successfully:\n{html.escape(response.text)}"
    except Exception as e:
        return f"Error modifying task: {str(e)}"

@tool
def remove_task(task_id: str) -> str:
    """Removes a task by task_id from the Task Management System."""
    try:
        url = f"{BASE_URL}/{task_id}"
        response = client.delete(url, timeout=10)
        response.raise_for_status()
        return f"Task #{task_id} Removed Successfully:\n{html.escape(response.text)}"
    except Exception as e:
        return f"Error removing task: {str(e)}"

import json
import base64
import html
from langchain_core.tools import tool

@tool
def list_tasks() -> str:
    """Lists all tasks from the Task Management System."""
    try:
        response = client.get(BASE_URL)
        
        # --- DEBUG JWT CLAIMS ---
        auth_header = response.request.headers.get("Authorization", "")
        if "Bearer " in auth_header:
            token = auth_header.split("Bearer ")[1].strip()
            # Decode the unencrypted payload (middle part of JWT)
            payload_part = token.split(".")[1]
            padded_b64 = payload_part + "=" * (-len(payload_part) % 4)
            claims = json.loads(base64.b64decode(padded_b64).decode("utf-8"))
            
            print("\n================ MUDRAID JWT DEBUG ================")
            print(f"Audience (Platform): {claims.get('aud')}")
            print(f"Token Scopes:        {claims.get('scopes')}")
            print("===================================================\n")
            
        return f"Tasks:\n{html.escape(response.text)}"
    except Exception as e:
        return f"Error fetching tasks: {str(e)}"

# -------------------------------------------------------------------
# EXPORT TOOLSETS FOR WORKERS
# -------------------------------------------------------------------
RESEARCH_TOOLS = [search_knowledge_base]
CODER_TOOLS = [calculate_math]
WEBSITE_TOOLS = [list_tasks, create_task, modify_task, remove_task]

ALL_TOOLS = RESEARCH_TOOLS + CODER_TOOLS + WEBSITE_TOOLS