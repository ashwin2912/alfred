from datetime import datetime, timedelta
from typing import List, Optional

import requests
from clients.models.task import ClickUpTask, Comment, HistoryEvent


class ClickUpClient:
    """Enhanced ClickUp API client for fetching tasks, comments, and history."""

    BASE_URL = "https://api.clickup.com/api/v2"

    def __init__(self, api_token: str):
        """
        Initialize ClickUp client.

        Args:
            api_token: ClickUp API token
        """
        self.api_token = api_token
        self.headers = {"Authorization": api_token, "Accept": "application/json"}

    def _make_request(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """
        Make a GET request to ClickUp API.

        Args:
            endpoint: API endpoint (e.g., "/list/123/task")
            params: Optional query parameters

        Returns:
            JSON response as dict

        Raises:
            Exception if request fails
        """
        url = f"{self.BASE_URL}{endpoint}"
        response = requests.get(url, headers=self.headers, params=params)

        if response.status_code != 200:
            raise Exception(
                f"ClickUp API error: {response.status_code} - {response.text}"
            )

        return response.json()

    def fetch_tasks(
        self, list_id: str, include_closed: bool = False, page: int = 0
    ) -> List[ClickUpTask]:
        """
        Fetch tasks from a ClickUp list.

        Args:
            list_id: ClickUp list ID
            include_closed: Whether to include closed tasks
            page: Page number for pagination

        Returns:
            List of ClickUpTask objects
        """
        endpoint = f"/list/{list_id}/task"
        params = {"page": page, "include_closed": str(include_closed).lower()}

        data = self._make_request(endpoint, params)
        raw_tasks = data.get("tasks", [])

        tasks: List[ClickUpTask] = []
        for task_data in raw_tasks:
            try:
                task = self._parse_task(task_data)
                tasks.append(task)
            except Exception as e:
                print(f"⚠️ Failed to parse task {task_data.get('id')}: {str(e)}")
                continue

        return tasks

    def _parse_task(self, task_data: dict) -> ClickUpTask:
        """Parse raw task data into ClickUpTask model."""
        assignees = [a["username"] for a in task_data.get("assignees", [])]
        tags = [t["name"] for t in task_data.get("tags", [])]
        priority = (
            task_data.get("priority", {}).get("priority")
            if task_data.get("priority")
            else None
        )
        description = (
            task_data.get("description")
            or task_data.get("text_content")
            or "No description provided."
        )

        # Parse custom fields
        custom_fields = {}
        for field in task_data.get("custom_fields", []):
            name = field.get("name", "unknown")
            if field["type"] == "users":
                value = (
                    [u["username"] for u in field.get("value", [])]
                    if isinstance(field.get("value"), list)
                    else []
                )
            else:
                value = field.get("value") or "None"
            custom_fields[name] = value

        return ClickUpTask(
            id=task_data["id"],
            name=task_data["name"],
            status=task_data.get("status", {}).get("status", "unknown"),
            assignees=assignees,
            due_date=task_data.get("due_date"),
            priority=priority,
            tags=tags,
            description=description,
            url=task_data.get("url"),
            custom_fields=custom_fields,
            date_created=task_data.get("date_created"),
            date_updated=task_data.get("date_updated"),
            time_estimate=task_data.get("time_estimate"),
            time_spent=task_data.get("time_spent"),
            comments=[],  # Will be populated by fetch_task_comments
            history=[],  # Will be populated by fetch_task_history
        )

    def fetch_task_comments(self, task_id: str) -> List[Comment]:
        """
        Fetch comments for a specific task.

        Args:
            task_id: ClickUp task ID

        Returns:
            List of Comment objects
        """
        endpoint = f"/task/{task_id}/comment"

        try:
            data = self._make_request(endpoint)
            raw_comments = data.get("comments", [])

            comments: List[Comment] = []
            for comment_data in raw_comments:
                try:
                    comment = Comment(
                        id=comment_data["id"],
                        comment_text=comment_data.get("comment_text", ""),
                        user=comment_data.get("user", {}).get("username", "Unknown"),
                        date=comment_data.get("date"),
                    )
                    comments.append(comment)
                except Exception as e:
                    print(f"⚠️ Failed to parse comment: {str(e)}")
                    continue

            return comments
        except Exception as e:
            print(f"⚠️ Failed to fetch comments for task {task_id}: {str(e)}")
            return []

    def fetch_task_history(self, task_id: str) -> List[HistoryEvent]:
        """
        Fetch history/activity for a specific task.

        Args:
            task_id: ClickUp task ID

        Returns:
            List of HistoryEvent objects
        """
        # Note: ClickUp API doesn't have a direct history endpoint
        # We'll use the task endpoint which includes some history data
        # For full history, you might need webhooks or the Activity endpoint
        # This is a simplified version

        # Placeholder - ClickUp's history API is limited
        # You may need to track changes via webhooks in production
        return []

    def fetch_tasks_with_details(
        self, list_id: str, include_closed: bool = False
    ) -> List[ClickUpTask]:
        """
        Fetch tasks with all details (comments and history).

        Args:
            list_id: ClickUp list ID
            include_closed: Whether to include closed tasks

        Returns:
            List of ClickUpTask objects with comments and history populated
        """
        tasks = self.fetch_tasks(list_id, include_closed)

        for task in tasks:
            # Fetch comments for each task
            task.comments = self.fetch_task_comments(task.id)
            # Fetch history for each task
            task.history = self.fetch_task_history(task.id)

        return tasks

    def fetch_recent_activity(self, list_id: str, hours: int = 24) -> List[ClickUpTask]:
        """
        Fetch tasks with recent activity (updated in last N hours).

        Args:
            list_id: ClickUp list ID
            hours: Number of hours to look back

        Returns:
            List of ClickUpTask objects updated recently
        """
        all_tasks = self.fetch_tasks_with_details(list_id, include_closed=False)

        cutoff_time = int((datetime.now() - timedelta(hours=hours)).timestamp() * 1000)

        recent_tasks = [
            task
            for task in all_tasks
            if task.date_updated and int(task.date_updated) >= cutoff_time
        ]

        return recent_tasks
