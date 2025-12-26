"""ClickUp API client service."""

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class ClickUpClient:
    """Client for interacting with ClickUp API."""

    def __init__(self, api_token: str):
        self.api_token = api_token
        self.base_url = "https://api.clickup.com/api/v2"
        self.headers = {"Authorization": api_token, "Content-Type": "application/json"}

    async def validate_token(self) -> tuple[bool, Optional[str]]:
        """Validate ClickUp API token."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/user", headers=self.headers, timeout=10.0
                )

                if response.status_code == 200:
                    return True, None
                elif response.status_code == 401:
                    return False, "Invalid API token"
                else:
                    return False, f"Unexpected error: {response.status_code}"
            except Exception as e:
                return False, f"Error: {str(e)}"

    async def get_user_info(self) -> Optional[dict]:
        """Get authenticated user info."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/user", headers=self.headers, timeout=10.0
                )
                if response.status_code == 200:
                    return response.json().get("user")
                return None
            except Exception:
                return None

    async def get_user_tasks(
        self, user_id: Optional[str] = None, list_ids: Optional[list[str]] = None
    ) -> list[dict]:
        """Get tasks for user, optionally filtered by list IDs."""
        all_tasks = []
        async with httpx.AsyncClient() as client:
            try:
                if not user_id:
                    user_info = await self.get_user_info()
                    if not user_info:
                        return []
                    user_id = user_info.get("id")

                if list_ids:
                    for list_id in list_ids:
                        params = {
                            "subtasks": "true",
                            "include_closed": "false",
                            "assignees[]": user_id,
                        }
                        response = await client.get(
                            f"{self.base_url}/list/{list_id}/task",
                            headers=self.headers,
                            params=params,
                            timeout=15.0,
                        )
                        if response.status_code == 200:
                            all_tasks.extend(response.json().get("tasks", []))
                else:
                    teams = await self._get_teams(client)
                    for team in teams:
                        params = {
                            "subtasks": "true",
                            "include_closed": "false",
                            "assignees[]": user_id,
                        }
                        response = await client.get(
                            f"{self.base_url}/team/{team['id']}/task",
                            headers=self.headers,
                            params=params,
                            timeout=15.0,
                        )
                        if response.status_code == 200:
                            all_tasks.extend(response.json().get("tasks", []))

                return all_tasks
            except Exception as e:
                logger.error(f"Error fetching tasks: {e}")
                return []

    async def get_task_details(self, task_id: str) -> Optional[dict]:
        """Get details for a specific task."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/task/{task_id}",
                    headers=self.headers,
                    timeout=10.0,
                )
                if response.status_code == 200:
                    return response.json()
                return None
            except Exception as e:
                logger.error(f"Error fetching task {task_id}: {e}")
                return None

    async def get_task_comments(self, task_id: str) -> list[dict]:
        """Get comments for a task."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/task/{task_id}/comment",
                    headers=self.headers,
                    timeout=10.0,
                )
                if response.status_code == 200:
                    return response.json().get("comments", [])
                return []
            except Exception as e:
                logger.error(f"Error fetching comments for task {task_id}: {e}")
                return []

    async def add_task_comment(self, task_id: str, comment_text: str) -> Optional[dict]:
        """Add a comment to a task."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/task/{task_id}/comment",
                    headers=self.headers,
                    json={"comment_text": comment_text},
                    timeout=10.0,
                )
                if response.status_code == 200:
                    return response.json()
                return None
            except Exception as e:
                logger.error(f"Error adding comment to task {task_id}: {e}")
                return None

    async def _get_teams(self, client: httpx.AsyncClient) -> list[dict]:
        """Helper to get all teams."""
        try:
            response = await client.get(
                f"{self.base_url}/team", headers=self.headers, timeout=10.0
            )
            if response.status_code == 200:
                return response.json().get("teams", [])
            return []
        except Exception:
            return []
