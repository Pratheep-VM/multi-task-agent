import base64
import html
import json
import os

from mudraid import Agent
from langchain_core.tools import tool
from dotenv import load_dotenv
load_dotenv()

website_client = Agent(
    api_key_id=os.getenv("WEBSITE_API_KEY_ID"),
    secret=os.getenv("WEBSITE_API_SECRET"),
    base_url=os.getenv("MUDRAID_BASE_URL", "https://api.staging.mudraid.ai")
)

BASE_URL = "https://pradeepplatform.mudraidtesting.online/api/v1/tasks"


@tool
def list_tasks() -> str:
    """Lists all tasks from the Task Management System."""
    try:
        response = website_client.get(BASE_URL, timeout=10)
        response.raise_for_status()

        auth_header = response.request.headers.get("Authorization", "")
        if "Bearer " in auth_header:
            token = auth_header.split("Bearer ")[1].strip()
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


@tool
def create_task(title: str) -> str:
    """Creates a new task in the Task Management System."""
    try:
        response = website_client.post(BASE_URL, json={"title": title}, timeout=10)
        response.raise_for_status()
        return f"Task Created Successfully:\n{html.escape(response.text)}"
    except Exception as e:
        return f"Error creating task: {str(e)}"


@tool
def modify_task(task_id: str, title: str) -> str:
    """Modifies an existing task by task_id in the Task Management System."""
    try:
        url = f"{BASE_URL}/{task_id}"
        response = website_client.put(url, json={"title": title}, timeout=10)
        response.raise_for_status()
        return f"Task Modified Successfully:\n{html.escape(response.text)}"
    except Exception as e:
        return f"Error modifying task: {str(e)}"


@tool
def remove_task(task_id: str) -> str:
    """Removes a task by task_id from the Task Management System."""
    try:
        url = f"{BASE_URL}/{task_id}"
        response = website_client.delete(url, timeout=10)
        response.raise_for_status()
        return f"Task #{task_id} Removed Successfully:\n{html.escape(response.text)}"
    except Exception as e:
        return f"Error removing task: {str(e)}"
