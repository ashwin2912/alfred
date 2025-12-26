"""HTTP client for task service."""

import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class TaskServiceClient:
    """Client for communicating with task service."""

    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_user_tasks(self, discord_user_id: str) -> Optional[Dict[str, Any]]:
        """Get all tasks for a user."""
        try:
            response = await self.client.get(
                f"{self.base_url}/tasks/user/{discord_user_id}"
            )
            if response.status_code == 200:
                return response.json()
            logger.error(f"Failed to get user tasks: {response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Error calling task service: {e}")
            return None

    async def get_task_details(
        self, task_id: str, clickup_token: str
    ) -> Optional[Dict[str, Any]]:
        """Get details for a specific task."""
        try:
            response = await self.client.get(
                f"{self.base_url}/tasks/{task_id}",
                headers={"Authorization": clickup_token},
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error getting task details: {e}")
            return None

    async def get_task_comments(
        self, task_id: str, clickup_token: str
    ) -> List[Dict[str, Any]]:
        """Get comments for a task."""
        try:
            response = await self.client.get(
                f"{self.base_url}/tasks/{task_id}/comments",
                headers={"Authorization": clickup_token},
            )
            if response.status_code == 200:
                return response.json().get("comments", [])
            return []
        except Exception as e:
            logger.error(f"Error getting task comments: {e}")
            return []

    async def add_task_comment(
        self, task_id: str, comment_text: str, clickup_token: str
    ) -> bool:
        """Add a comment to a task."""
        try:
            response = await self.client.post(
                f"{self.base_url}/tasks/{task_id}/comment",
                json={"comment_text": comment_text},
                headers={"Authorization": clickup_token},
            )
            if response.status_code == 200:
                result = response.json()
                return result.get("success", False)
            return False
        except Exception as e:
            logger.error(f"Error adding task comment: {e}")
            return False

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
