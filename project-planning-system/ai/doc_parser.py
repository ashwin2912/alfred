"""Parse project planning documents for ClickUp publishing."""

import json
from typing import Any, Dict, List, Optional


class ProjectDocParser:
    """
    Parse project planning documents into ClickUp-ready task structure.

    Supports parsing from:
    1. Stored JSON structure (ai_analysis field from database)
    2. Google Doc content (future enhancement)
    """

    def parse_from_json(self, ai_analysis: str) -> Dict[str, Any]:
        """
        Parse stored JSON breakdown into task structure.

        Args:
            ai_analysis: JSON string from project_brainstorms.ai_analysis

        Returns:
            Dict with:
                - title: Project title
                - phases: List of phases with tasks
                - total_tasks: Total number of tasks
                - total_hours: Total estimated hours

        Example:
            >>> parser = ProjectDocParser()
            >>> result = parser.parse_from_json(json_string)
            >>> print(result['total_tasks'])
            19
        """
        try:
            breakdown = json.loads(ai_analysis)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in ai_analysis: {e}")

        # Validate structure
        if "phases" not in breakdown:
            raise ValueError("Missing 'phases' in breakdown structure")

        # Calculate totals
        total_tasks = sum(
            len(phase.get("subtasks", [])) for phase in breakdown["phases"]
        )
        total_hours = sum(
            task.get("estimated_hours", 0)
            for phase in breakdown["phases"]
            for task in phase.get("subtasks", [])
        )

        return {
            "title": breakdown.get("title", "Untitled Project"),
            "overview": breakdown.get("overview", ""),
            "objectives": breakdown.get("objectives", []),
            "phases": breakdown.get("phases", []),
            "team_suggestions": breakdown.get("team_suggestions", []),
            "success_criteria": breakdown.get("success_criteria", []),
            "total_tasks": total_tasks,
            "total_hours": total_hours,
        }

    def extract_clickup_tasks(
        self, parsed_project: Dict[str, Any], use_phase_folders: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Extract tasks in ClickUp-ready format.

        Args:
            parsed_project: Output from parse_from_json()
            use_phase_folders: If True, include folder names for organization

        Returns:
            List of task dicts ready for ClickUp API, each containing:
                - name: Task name
                - description: Task description
                - estimated_hours: Time estimate
                - required_skills: List of skills needed
                - priority: Priority level (1=urgent, 2=high, 3=normal, 4=low)
                - phase_name: Phase this task belongs to (for folder grouping)
                - tags: List of tags

        Example:
            >>> tasks = parser.extract_clickup_tasks(parsed_project)
            >>> print(tasks[0]['name'])
            'Gather dashboard requirements'
        """
        clickup_tasks = []

        for phase in parsed_project["phases"]:
            phase_name = phase["name"]

            for subtask in phase.get("subtasks", []):
                # Map priority if exists, default to normal
                priority_map = {"urgent": 1, "high": 2, "normal": 3, "low": 4}
                priority = priority_map.get(
                    subtask.get("priority", "normal").lower(), 3
                )

                task = {
                    "name": subtask["name"],
                    "description": self._format_task_description(subtask, phase_name),
                    "estimated_hours": subtask.get("estimated_hours", 0),
                    "required_skills": subtask.get("required_skills", []),
                    "priority": priority,
                    "phase_name": phase_name,
                    "tags": ["AI-Generated", phase_name],
                }

                clickup_tasks.append(task)

        return clickup_tasks

    def _format_task_description(self, subtask: Dict[str, Any], phase_name: str) -> str:
        """
        Format a rich task description for ClickUp.

        Args:
            subtask: Task dict from breakdown
            phase_name: Name of the phase

        Returns:
            Formatted markdown description
        """
        parts = []

        # Main description
        parts.append(subtask.get("description", ""))
        parts.append("")

        # Metadata
        parts.append("---")
        parts.append("")
        parts.append(f"**Phase:** {phase_name}")
        parts.append(f"**Estimated Hours:** {subtask.get('estimated_hours', 0)}")

        if subtask.get("required_skills"):
            parts.append(
                f"**Required Skills:** {', '.join(subtask['required_skills'])}"
            )

        parts.append("")
        parts.append("*Generated by Alfred AI Project Planning*")

        return "\n".join(parts)

    def group_tasks_by_phase(
        self, tasks: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group tasks by phase for organized creation.

        Args:
            tasks: List of tasks from extract_clickup_tasks()

        Returns:
            Dict mapping phase_name -> list of tasks

        Example:
            >>> grouped = parser.group_tasks_by_phase(tasks)
            >>> for phase, phase_tasks in grouped.items():
            ...     print(f"{phase}: {len(phase_tasks)} tasks")
        """
        grouped = {}

        for task in tasks:
            phase_name = task["phase_name"]
            if phase_name not in grouped:
                grouped[phase_name] = []
            grouped[phase_name].append(task)

        return grouped
