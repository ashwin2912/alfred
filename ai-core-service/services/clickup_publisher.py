"""ClickUp publisher service for creating tasks from project plans."""

import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class ClickUpPublisher:
    """
    Service to publish project plans to ClickUp.

    Takes a parsed project breakdown and creates tasks in ClickUp.
    """

    def __init__(self, api_token: str):
        """
        Initialize ClickUp publisher.

        Args:
            api_token: ClickUp API token
        """
        self.api_token = api_token
        self.base_url = "https://api.clickup.com/api/v2"
        self.headers = {"Authorization": api_token, "Content-Type": "application/json"}

    async def publish_project(
        self, breakdown: Dict[str, Any], clickup_list_id: str
    ) -> Dict[str, Any]:
        """
        Publish a project breakdown to ClickUp.

        Args:
            breakdown: Parsed project breakdown (ai_analysis JSON)
            clickup_list_id: ClickUp list ID to create tasks in

        Returns:
            Dict with:
                - tasks_created: Number of tasks created
                - task_ids: List of created task IDs
                - errors: List of any errors encountered
        """
        tasks_created = 0
        task_ids = []
        errors = []
        project_title = breakdown.get("title", "Project")

        logger.info(
            f"Publishing {len(breakdown.get('phases', []))} phases to ClickUp list {clickup_list_id}"
        )

        async with httpx.AsyncClient() as client:
            for phase_num, phase in enumerate(breakdown.get("phases", []), 1):
                phase_name = phase["name"]
                phase_description = phase.get("description", "")

                logger.info(f"Processing phase {phase_num}: {phase_name}")

                # Create Phase as parent task
                try:
                    phase_task_data = {
                        "name": phase_name,
                        "description": phase_description,
                        "tags": [{"name": project_title}],
                    }

                    phase_response = await client.post(
                        f"{self.base_url}/list/{clickup_list_id}/task",
                        headers=self.headers,
                        json=phase_task_data,
                        timeout=15.0,
                    )

                    if phase_response.status_code != 200:
                        error_msg = f"Failed to create phase '{phase_name}': {phase_response.status_code}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        continue  # Skip subtasks if phase creation failed

                    phase_result = phase_response.json()
                    phase_task_id = phase_result["id"]
                    task_ids.append(phase_task_id)
                    tasks_created += 1
                    logger.info(
                        f"Created phase task: {phase_name} (ID: {phase_task_id})"
                    )

                    # Create subtasks under this phase
                    for subtask in phase.get("subtasks", []):
                        try:
                            subtask_data = {
                                "name": subtask["name"],
                                "description": self._format_subtask_description(
                                    subtask, project_title
                                ),
                                "parent": phase_task_id,  # Link to parent phase
                                "tags": [{"name": project_title}],
                            }

                            subtask_response = await client.post(
                                f"{self.base_url}/list/{clickup_list_id}/task",
                                headers=self.headers,
                                json=subtask_data,
                                timeout=15.0,
                            )

                            if subtask_response.status_code == 200:
                                subtask_result = subtask_response.json()
                                task_ids.append(subtask_result["id"])
                                tasks_created += 1
                                logger.info(
                                    f"Created subtask: {subtask['name']} (ID: {subtask_result['id']})"
                                )
                            else:
                                error_msg = f"Failed to create subtask '{subtask['name']}': {subtask_response.status_code}"
                                logger.error(error_msg)
                                errors.append(error_msg)

                        except Exception as e:
                            error_msg = (
                                f"Error creating subtask '{subtask['name']}': {str(e)}"
                            )
                            logger.error(error_msg, exc_info=True)
                            errors.append(error_msg)

                except Exception as e:
                    error_msg = f"Error creating phase '{phase_name}': {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    errors.append(error_msg)

        return {"tasks_created": tasks_created, "task_ids": task_ids, "errors": errors}

    def _format_subtask_description(
        self, subtask: Dict[str, Any], project_title: str
    ) -> str:
        """
        Format a subtask description for ClickUp.

        Args:
            subtask: Subtask data from breakdown
            project_title: Title of the project

        Returns:
            Formatted markdown description
        """
        parts = []

        # Main description
        parts.append(subtask.get("description", ""))
        parts.append("")

        # Metadata section
        parts.append("---")
        parts.append("")
        parts.append(f"**Project:** {project_title}")

        if subtask.get("required_skills"):
            parts.append(
                f"**Required Skills:** {', '.join(subtask['required_skills'])}"
            )

        parts.append("")
        parts.append("*Generated by Alfred AI Project Planning*")

        return "\n".join(parts)

    async def get_list_url(self, clickup_list_id: str) -> Optional[str]:
        """
        Get the URL for a ClickUp list.

        Args:
            clickup_list_id: ClickUp list ID

        Returns:
            URL to view the list in ClickUp, or None if failed
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/list/{clickup_list_id}",
                    headers=self.headers,
                    timeout=10.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    # ClickUp list URL format
                    return f"https://app.clickup.com/t/{clickup_list_id}"

                return None

            except Exception as e:
                logger.error(f"Error fetching list URL: {e}")
                return None
