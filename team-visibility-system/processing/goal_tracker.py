from typing import Any, Dict, List

from clients.models.task import ClickUpTask


class GoalTracker:
    """Maps ClickUp tasks to weekly goals using tags."""

    def __init__(self, goals: List[Dict[str, Any]], tasks: List[ClickUpTask]):
        """
        Initialize goal tracker.

        Args:
            goals: List of parsed goals from Google Doc
            tasks: List of ClickUpTask objects
        """
        self.goals = goals
        self.tasks = tasks

    def map_tasks_to_goals(self) -> Dict[str, Any]:
        """
        Map tasks to goals based on tags.

        Returns:
            Dict mapping each goal to its tasks and progress
        """
        goal_mapping = []

        for i, goal in enumerate(self.goals):
            goal_title = goal.get("title", f"Goal {i + 1}")

            # Extract potential tags from goal title
            # Look for tags like "Stage 1", "stage-1", etc.
            goal_tags = self._extract_tags_from_goal(goal)

            # Find tasks matching these tags
            matched_tasks = self._find_matching_tasks(goal_tags)

            # Calculate progress
            total_tasks = len(matched_tasks)
            completed_tasks = len(
                [t for t in matched_tasks if self._is_task_complete(t)]
            )
            in_progress_tasks = len(
                [t for t in matched_tasks if self._is_task_in_progress(t)]
            )
            blocked_tasks = len([t for t in matched_tasks if t.has_blockers])

            goal_mapping.append(
                {
                    "goal": goal,
                    "goal_title": goal_title,
                    "matched_tags": goal_tags,
                    "tasks": matched_tasks,
                    "progress": {
                        "total": total_tasks,
                        "completed": completed_tasks,
                        "in_progress": in_progress_tasks,
                        "blocked": blocked_tasks,
                        "not_started": total_tasks
                        - completed_tasks
                        - in_progress_tasks,
                        "completion_percentage": (completed_tasks / total_tasks * 100)
                        if total_tasks > 0
                        else 0,
                    },
                }
            )

        return {
            "goal_mappings": goal_mapping,
            "unmapped_tasks": self._find_unmapped_tasks(goal_mapping),
        }

    def _extract_tags_from_goal(self, goal: Dict[str, Any]) -> List[str]:
        """
        Extract potential ClickUp tags from goal text.

        Args:
            goal: Goal dict

        Returns:
            List of potential tag strings
        """
        tags = set()

        # Look in title and deliverables
        text = goal.get("title", "").lower()

        # Common patterns
        # "Stage 1" -> ["stage-1", "stage1"]
        import re

        # Pattern: "Stage X" or "Phase X"
        stage_matches = re.findall(r"stage\s*(\d+)", text)
        for match in stage_matches:
            tags.add(f"stage-{match}")
            tags.add(f"stage{match}")

        phase_matches = re.findall(r"phase\s*(\d+)", text)
        for match in phase_matches:
            tags.add(f"phase-{match}")
            tags.add(f"phase{match}")

        # Look for explicit tags in backticks or with #
        backtick_tags = re.findall(r"`([a-z0-9-]+)`", text)
        tags.update(backtick_tags)

        hashtags = re.findall(r"#([a-z0-9-]+)", text)
        tags.update(hashtags)

        # Look for key project names
        if "team visibility" in text or "visibility system" in text:
            tags.add("team-visibility")

        if "code review" in text:
            tags.add("code-review")

        return list(tags)

    def _find_matching_tasks(self, goal_tags: List[str]) -> List[ClickUpTask]:
        """
        Find tasks that match any of the goal tags.

        Args:
            goal_tags: List of tag strings to match

        Returns:
            List of matching tasks
        """
        if not goal_tags:
            return []

        matched_tasks = []

        for task in self.tasks:
            # Check if task has any matching tags
            task_tags_lower = [tag.lower() for tag in task.tags]

            for goal_tag in goal_tags:
                if goal_tag.lower() in task_tags_lower:
                    matched_tasks.append(task)
                    break

        return matched_tasks

    def _is_task_complete(self, task: ClickUpTask) -> bool:
        """Check if a task is completed."""
        if not task.status:
            return False

        status_lower = task.status.lower()
        return any(
            keyword in status_lower
            for keyword in ["complete", "done", "closed", "finished"]
        )

    def _is_task_in_progress(self, task: ClickUpTask) -> bool:
        """Check if a task is in progress."""
        if not task.status:
            return False

        status_lower = task.status.lower()
        return any(
            keyword in status_lower
            for keyword in ["in progress", "active", "working", "started"]
        )

    def _find_unmapped_tasks(
        self, goal_mapping: List[Dict[str, Any]]
    ) -> List[ClickUpTask]:
        """
        Find tasks that don't map to any goal.

        Args:
            goal_mapping: List of goal mappings

        Returns:
            List of unmapped tasks
        """
        mapped_task_ids = set()

        for mapping in goal_mapping:
            for task in mapping["tasks"]:
                mapped_task_ids.add(task.id)

        unmapped = [task for task in self.tasks if task.id not in mapped_task_ids]
        return unmapped

    def get_progress_summary(self) -> Dict[str, Any]:
        """
        Get overall progress summary across all goals.

        Returns:
            Dict with summary statistics
        """
        mapping = self.map_tasks_to_goals()

        total_goals = len(mapping["goal_mappings"])
        completed_goals = len(
            [
                g
                for g in mapping["goal_mappings"]
                if g["progress"]["completion_percentage"] == 100
            ]
        )

        total_tasks = sum(g["progress"]["total"] for g in mapping["goal_mappings"])
        completed_tasks = sum(
            g["progress"]["completed"] for g in mapping["goal_mappings"]
        )
        blocked_tasks = sum(g["progress"]["blocked"] for g in mapping["goal_mappings"])

        return {
            "total_goals": total_goals,
            "completed_goals": completed_goals,
            "goals_in_progress": total_goals - completed_goals,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "blocked_tasks": blocked_tasks,
            "overall_completion": (completed_tasks / total_tasks * 100)
            if total_tasks > 0
            else 0,
            "unmapped_tasks_count": len(mapping["unmapped_tasks"]),
        }
