import os
import requests
from dotenv import load_dotenv
from typing import List
from langchain.tools import Tool

from models.task import ClickUpTask  # 👈 Import the Pydantic model

load_dotenv()
CLICKUP_API_TOKEN = os.getenv("CLICKUP_API_TOKEN", "").strip()
CLICKUP_LIST_ID = os.getenv("CLICKUP_LIST_ID", "").strip()

def fetch_clickup_tasks() -> List[ClickUpTask]:
    """
    Fetch tasks from ClickUp and parse into Pydantic models.
    """
    if not CLICKUP_API_TOKEN or not CLICKUP_LIST_ID:
        raise ValueError("Missing CLICKUP_API_TOKEN or CLICKUP_LIST_ID in .env")

    url = f"https://api.clickup.com/api/v2/list/{CLICKUP_LIST_ID}/task"
    headers = {
        "Authorization": CLICKUP_API_TOKEN,
        "Accept": "application/json"
    }

    print(f"➡️ Sending GET request to: {url}")
    print(f"🧾 Headers: {headers}")

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"❌ Status: {response.status_code}")
        print(f"❌ Response: {response.text}")
        raise Exception(f"ClickUp API error: {response.status_code} - {response.text}")

    raw_tasks = response.json().get("tasks", [])
    tasks: List[ClickUpTask] = []

    for task in raw_tasks:
        try:
            assignees = [a["username"] for a in task.get("assignees", [])]
            tags = [t["name"] for t in task.get("tags", [])]
            priority = task.get("priority", {}).get("priority") if task.get("priority") else None
            description = (
                task.get("description")
                or task.get("text_content")
                or "No description provided."
            )

            # Parse custom fields
            custom_fields = {}
            for field in task.get("custom_fields", []):
                name = field.get("name", "unknown")
                if field["type"] == "users":
                    value = [u["username"] for u in field.get("value", [])] if isinstance(field.get("value"), list) else []
                else:
                    value = field.get("value") or "None"
                custom_fields[name] = value

            task_obj = ClickUpTask(
                id=task["id"],
                name=task["name"],
                status=task.get("status", {}).get("status", "unknown"),
                assignees=assignees,
                due_date=task.get("due_date"),
                priority=priority,
                tags=tags,
                description=description,
                url=task.get("url"),
                custom_fields=custom_fields
            )
            tasks.append(task_obj)
        except Exception as e:
            print(f"⚠️ Failed to parse task: {task.get('id')} — {str(e)}")
            continue

    return tasks

# Optional LangChain Tool wrapper
clickup_fetcher_tool = Tool(
    name="ClickUp Task Fetcher",
    description="Fetches detailed tasks from a ClickUp list for summarization or analysis.",
    func=lambda _: fetch_clickup_tasks()
)
