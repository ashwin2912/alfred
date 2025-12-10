"""ClickUp service for team member management and task assignment."""

import os
from typing import Dict, List, Optional

import requests
from team_management_system.models.team_member import (
    AssignmentScore,
    TaskRequirement,
    TeamMember,
)


class ClickUpTeamService:
    """Service for managing team members and assignments in ClickUp."""

    BASE_URL = "https://api.clickup.com/api/v2"

    def __init__(self, api_token: str, workspace_id: str, list_id: str):
        """
        Initialize ClickUp team service.

        Args:
            api_token: ClickUp API token
            workspace_id: ClickUp workspace/team ID
            list_id: Default list ID for team tasks
        """
        self.api_token = api_token
        self.workspace_id = workspace_id
        self.list_id = list_id
        self.headers = {"Authorization": api_token, "Content-Type": "application/json"}

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None,
    ) -> dict:
        """
        Make a request to ClickUp API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            params: Optional query parameters
            json_data: Optional JSON body

        Returns:
            JSON response as dict

        Raises:
            Exception if request fails
        """
        url = f"{self.BASE_URL}{endpoint}"
        response = requests.request(
            method, url, headers=self.headers, params=params, json=json_data
        )

        if response.status_code not in (200, 201):
            raise Exception(
                f"ClickUp API error: {response.status_code} - {response.text}"
            )

        return response.json() if response.text else {}

    def get_workspace_members(self) -> List[Dict]:
        """
        Get all members in the workspace.

        Returns:
            List of workspace members with their details
        """
        endpoint = f"/team/{self.workspace_id}"
        data = self._make_request("GET", endpoint)
        return data.get("team", {}).get("members", [])

    def find_user_by_email(self, email: str) -> Optional[Dict]:
        """
        Find a ClickUp user by email.

        Args:
            email: Email address to search for

        Returns:
            User dict if found, None otherwise
        """
        members = self.get_workspace_members()
        for member in members:
            user = member.get("user", {})
            if user.get("email", "").lower() == email.lower():
                return user
        return None

    def invite_member(self, email: str, admin: bool = False) -> Dict:
        """
        Invite a new member to the workspace.

        Args:
            email: Email address to invite
            admin: Whether to make them an admin

        Returns:
            Invitation response dict
        """
        endpoint = f"/team/{self.workspace_id}/user"
        json_data = {"email": email, "admin": admin}

        return self._make_request("POST", endpoint, json_data=json_data)

    def create_task(
        self,
        name: str,
        description: str,
        assignees: Optional[List[int]] = None,
        priority: Optional[int] = None,
        due_date: Optional[int] = None,
        time_estimate: Optional[int] = None,
        tags: Optional[List[str]] = None,
        custom_fields: Optional[List[Dict]] = None,
        list_id: Optional[str] = None,
    ) -> Dict:
        """
        Create a new task in ClickUp.

        Args:
            name: Task name
            description: Task description
            assignees: List of user IDs to assign
            priority: Priority (1=urgent, 2=high, 3=normal, 4=low)
            due_date: Due date as Unix timestamp in milliseconds
            time_estimate: Time estimate in milliseconds
            tags: List of tag names
            custom_fields: List of custom field objects
            list_id: List ID (uses default if not provided)

        Returns:
            Created task dict
        """
        target_list_id = list_id or self.list_id
        endpoint = f"/list/{target_list_id}/task"

        json_data = {
            "name": name,
            "description": description,
        }

        if assignees:
            json_data["assignees"] = assignees

        if priority:
            json_data["priority"] = priority

        if due_date:
            json_data["due_date"] = due_date

        if time_estimate:
            json_data["time_estimate"] = time_estimate

        if tags:
            json_data["tags"] = tags

        if custom_fields:
            json_data["custom_fields"] = custom_fields

        return self._make_request("POST", endpoint, json_data=json_data)

    def assign_task_to_user(self, task_id: str, user_id: int) -> Dict:
        """
        Assign a task to a user.

        Args:
            task_id: ClickUp task ID
            user_id: ClickUp user ID

        Returns:
            Updated task dict
        """
        endpoint = f"/task/{task_id}"

        # Get current task to preserve other assignees
        current_task = self._make_request("GET", endpoint)
        current_assignees = [a["id"] for a in current_task.get("assignees", [])]

        # Add new assignee if not already assigned
        if user_id not in current_assignees:
            current_assignees.append(user_id)

        json_data = {"assignees": {"add": [user_id]}}

        return self._make_request("PUT", endpoint, json_data=json_data)

    def unassign_task_from_user(self, task_id: str, user_id: int) -> Dict:
        """
        Unassign a task from a user.

        Args:
            task_id: ClickUp task ID
            user_id: ClickUp user ID

        Returns:
            Updated task dict
        """
        endpoint = f"/task/{task_id}"
        json_data = {"assignees": {"rem": [user_id]}}

        return self._make_request("PUT", endpoint, json_data=json_data)

    def get_user_tasks(self, user_id: int, list_id: Optional[str] = None) -> List[Dict]:
        """
        Get all tasks assigned to a specific user.

        Args:
            user_id: ClickUp user ID
            list_id: Optional list ID (uses default if not provided)

        Returns:
            List of tasks assigned to the user
        """
        target_list_id = list_id or self.list_id
        endpoint = f"/list/{target_list_id}/task"

        params = {"assignees[]": user_id}

        data = self._make_request("GET", endpoint, params=params)
        return data.get("tasks", [])

    def calculate_user_workload(self, user_id: int) -> float:
        """
        Calculate total estimated workload for a user in hours.

        Args:
            user_id: ClickUp user ID

        Returns:
            Total estimated hours
        """
        tasks = self.get_user_tasks(user_id)

        total_ms = 0
        for task in tasks:
            # Only count open tasks
            status = task.get("status", {}).get("status", "").lower()
            if status not in ["closed", "complete", "done"]:
                time_estimate = task.get("time_estimate")
                if time_estimate:
                    total_ms += time_estimate

        # Convert milliseconds to hours
        return total_ms / (1000 * 60 * 60)

    def create_task_from_requirement(
        self,
        requirement: TaskRequirement,
        assignee_email: Optional[str] = None,
    ) -> Dict:
        """
        Create a task from a TaskRequirement object.

        Args:
            requirement: TaskRequirement with task details
            assignee_email: Optional email of assignee

        Returns:
            Created task dict
        """
        # Find assignee user ID if email provided
        assignees = None
        if assignee_email:
            user = self.find_user_by_email(assignee_email)
            if user:
                assignees = [user["id"]]

        # Convert priority string to ClickUp priority number
        priority_map = {
            "urgent": 1,
            "high": 2,
            "normal": 3,
            "low": 4,
        }
        priority = None
        if requirement.priority:
            priority = priority_map.get(requirement.priority.lower(), 3)

        # Convert due date to Unix timestamp in milliseconds
        due_date = None
        if requirement.due_date:
            due_date = int(requirement.due_date.timestamp() * 1000)

        # Convert hours to milliseconds
        time_estimate = int(requirement.estimated_hours * 60 * 60 * 1000)

        # Create tags from required skills
        tags = [f"skill:{skill}" for skill in requirement.required_skills]

        return self.create_task(
            name=requirement.task_name,
            description=requirement.task_description,
            assignees=assignees,
            priority=priority,
            due_date=due_date,
            time_estimate=time_estimate,
            tags=tags,
        )

    def assign_task_to_best_match(
        self,
        requirement: TaskRequirement,
        team_members: List[TeamMember],
        top_n: int = 3,
    ) -> List[AssignmentScore]:
        """
        Find the best team members for a task and return ranked suggestions.

        Args:
            requirement: Task requirements
            team_members: List of team members to consider
            top_n: Number of top suggestions to return

        Returns:
            List of AssignmentScore objects, ranked by overall score
        """
        scores = []

        for member in team_members:
            if not member.is_active:
                continue

            score = AssignmentScore.calculate(member, requirement)
            scores.append(score)

        # Sort by overall score (descending)
        scores.sort(key=lambda x: x.overall_score, reverse=True)

        return scores[:top_n]

    def create_and_assign_task(
        self,
        requirement: TaskRequirement,
        team_members: List[TeamMember],
        auto_assign: bool = True,
    ) -> Dict:
        """
        Create a task and optionally auto-assign to best match.

        Args:
            requirement: Task requirements
            team_members: List of team members to consider
            auto_assign: Whether to automatically assign to best match

        Returns:
            Dict with 'task' and 'suggestions' keys
        """
        # Get assignment suggestions
        suggestions = self.assign_task_to_best_match(requirement, team_members)

        # Create task
        assignee_email = None
        if auto_assign and suggestions:
            best_match = suggestions[0]
            assignee_email = best_match.member.email

        task = self.create_task_from_requirement(requirement, assignee_email)

        return {
            "task": task,
            "suggestions": suggestions,
            "assigned_to": assignee_email if auto_assign else None,
        }

    def add_task_comment(self, task_id: str, comment_text: str) -> Dict:
        """
        Add a comment to a task.

        Args:
            task_id: ClickUp task ID
            comment_text: Comment text

        Returns:
            Created comment dict
        """
        endpoint = f"/task/{task_id}/comment"
        json_data = {"comment_text": comment_text}

        return self._make_request("POST", endpoint, json_data=json_data)

    def update_task_status(self, task_id: str, status: str) -> Dict:
        """
        Update task status.

        Args:
            task_id: ClickUp task ID
            status: Status name (must exist in ClickUp)

        Returns:
            Updated task dict
        """
        endpoint = f"/task/{task_id}"
        json_data = {"status": status}

        return self._make_request("PUT", endpoint, json_data=json_data)

    def get_list_statuses(self, list_id: Optional[str] = None) -> List[Dict]:
        """
        Get available statuses for a list.

        Args:
            list_id: List ID (uses default if not provided)

        Returns:
            List of status dicts
        """
        target_list_id = list_id or self.list_id
        endpoint = f"/list/{target_list_id}"

        data = self._make_request("GET", endpoint)
        return data.get("statuses", [])


def create_clickup_team_service(
    api_token: Optional[str] = None,
    workspace_id: Optional[str] = None,
    list_id: Optional[str] = None,
) -> ClickUpTeamService:
    """
    Factory function to create ClickUpTeamService from environment variables.

    Args:
        api_token: Optional ClickUp API token (uses env var if not provided)
        workspace_id: Optional workspace ID (uses env var if not provided)
        list_id: Optional list ID (uses env var if not provided)

    Returns:
        Configured ClickUpTeamService instance
    """
    api_token = api_token or os.getenv("CLICKUP_API_TOKEN")
    workspace_id = workspace_id or os.getenv("CLICKUP_WORKSPACE_ID")
    list_id = list_id or os.getenv("CLICKUP_LIST_ID")

    if not api_token:
        raise ValueError("CLICKUP_API_TOKEN not provided")
    if not workspace_id:
        raise ValueError("CLICKUP_WORKSPACE_ID not provided")
    if not list_id:
        raise ValueError("CLICKUP_LIST_ID not provided")

    return ClickUpTeamService(api_token, workspace_id, list_id)
