from typing import Any, Dict, List

from clients.clickup_client import ClickUpClient
from clients.gdrive_client import GoogleDriveClient
from clients.models.task import ClickUpTask
from processing.blocker_detector import BlockerDetector
from processing.data_aggregator import DataAggregator
from processing.goal_tracker import GoalTracker
from processing.task_validator import TaskValidator


class WeeklyContext:
    """Aggregates all context needed for weekly summaries: ClickUp + Google Drive."""

    def __init__(
        self,
        clickup_client: ClickUpClient,
        gdrive_client: GoogleDriveClient,
        clickup_list_id: str,
        weekly_goals_doc_id: str,
    ):
        """
        Initialize weekly context aggregator.

        Args:
            clickup_client: Initialized ClickUp client
            gdrive_client: Initialized Google Drive client
            clickup_list_id: ClickUp list ID to fetch tasks from
            weekly_goals_doc_id: Google Doc ID containing weekly goals
        """
        self.clickup_client = clickup_client
        self.gdrive_client = gdrive_client
        self.clickup_list_id = clickup_list_id
        self.weekly_goals_doc_id = weekly_goals_doc_id

        # Data holders
        self.tasks = []
        self.goals = None
        self.aggregator = None
        self.blocker_detector = None
        self.validator = None
        self.goal_tracker = None

    def fetch_all_data(self) -> Dict[str, Any]:
        """
        Fetch all data from ClickUp and Google Drive.

        Returns:
            Dict containing all fetched data
        """
        # Fetch ClickUp tasks
        self.tasks = self.clickup_client.fetch_tasks_with_details(
            self.clickup_list_id, include_closed=False
        )

        # Fetch Google Doc goals
        self.goals = self.gdrive_client.parse_weekly_goals(self.weekly_goals_doc_id)

        # Initialize processors
        self.aggregator = DataAggregator(self.tasks)
        self.blocker_detector = BlockerDetector(self.tasks)
        self.validator = TaskValidator(self.tasks)
        self.goal_tracker = GoalTracker(self.goals["goals"], self.tasks)

        return {"tasks": self.tasks, "goals": self.goals, "task_count": len(self.tasks)}

    def get_complete_context(self) -> Dict[str, Any]:
        """
        Get complete weekly context combining all data sources.

        Returns:
            Comprehensive dict with all context for AI summarization
        """
        if not self.tasks or not self.goals:
            raise ValueError("Must call fetch_all_data() first")

        # Get all summaries
        team_summary = self.aggregator.get_team_summary()
        blocker_summary = self.blocker_detector.get_blocker_summary()
        validation_summary = self.validator.get_validation_summary()
        goal_mapping = self.goal_tracker.map_tasks_to_goals()
        progress_summary = self.goal_tracker.get_progress_summary()

        return {
            "week_title": self.goals["title"],
            "google_doc_id": self.weekly_goals_doc_id,
            # Goals from Google Doc
            "weekly_goals": {
                "goals": self.goals["goals"],
                "risks": self.goals["risks"],
                "full_text": self.goals["full_text"],
            },
            # Goal progress tracking
            "goal_progress": {
                "mappings": goal_mapping["goal_mappings"],
                "unmapped_tasks": goal_mapping["unmapped_tasks"],
                "summary": progress_summary,
            },
            # ClickUp task summaries
            "team_summary": team_summary,
            "blocker_summary": blocker_summary,
            "validation_summary": validation_summary,
            # Raw data
            "all_tasks": self.tasks,
        }

    def get_goal_progress_text(self) -> str:
        """
        Get human-readable text summarizing goal progress.

        Returns:
            Formatted text string
        """
        if not self.goal_tracker:
            raise ValueError("Must call fetch_all_data() first")

        mapping = self.goal_tracker.map_tasks_to_goals()
        lines = []

        lines.append(f"Week: {self.goals['title']}")
        lines.append("=" * 60)
        lines.append("")

        for i, goal_map in enumerate(mapping["goal_mappings"], 1):
            goal_title = goal_map["goal_title"]
            progress = goal_map["progress"]

            lines.append(f"{i}. {goal_title}")
            lines.append(
                f"   Progress: {progress['completed']}/{progress['total']} tasks complete ({progress['completion_percentage']:.0f}%)"
            )
            lines.append(
                f"   Status: {progress['in_progress']} in progress, {progress['blocked']} blocked, {progress['not_started']} not started"
            )

            # Show task details
            if goal_map["tasks"]:
                lines.append(f"   Tasks:")
                for task in goal_map["tasks"]:
                    status_icon = (
                        "✅"
                        if self.goal_tracker._is_task_complete(task)
                        else "🔄"
                        if self.goal_tracker._is_task_in_progress(task)
                        else "⚪"
                    )
                    lines.append(f"     {status_icon} {task.name} [{task.status}]")

            lines.append("")

        # Show unmapped tasks
        if mapping["unmapped_tasks"]:
            lines.append("⚠️  Tasks not mapped to any goal:")
            for task in mapping["unmapped_tasks"]:
                lines.append(f"  - {task.name} (tags: {', '.join(task.tags)})")
            lines.append("")

        return "\n".join(lines)

    def get_summary_for_ai(self) -> str:
        """
        Get formatted text optimized for AI summarization.

        Returns:
            Text string containing all context in AI-friendly format
        """
        context = self.get_complete_context()

        lines = []

        # Weekly goals section
        lines.append("=== WEEKLY GOALS (From Google Doc) ===")
        lines.append(context["weekly_goals"]["full_text"])
        lines.append("")

        # Progress section
        lines.append("=== PROGRESS TOWARD GOALS ===")
        progress = context["goal_progress"]["summary"]
        lines.append(
            f"Goals: {progress['completed_goals']}/{progress['total_goals']} complete"
        )
        lines.append(
            f"Tasks: {progress['completed_tasks']}/{progress['total_tasks']} complete ({progress['overall_completion']:.0f}%)"
        )
        lines.append(f"Blocked: {progress['blocked_tasks']} tasks")
        lines.append(
            f"Unmapped: {progress['unmapped_tasks_count']} tasks not linked to goals"
        )
        lines.append("")

        # Detailed goal mapping
        for goal_map in context["goal_progress"]["mappings"]:
            lines.append(f"Goal: {goal_map['goal_title']}")
            prog = goal_map["progress"]
            lines.append(
                f"  {prog['completed']}/{prog['total']} complete, {prog['in_progress']} in progress, {prog['blocked']} blocked"
            )

            # List tasks
            for task in goal_map["tasks"]:
                lines.append(
                    f"  - [{task.status}] {task.name} (assigned: {', '.join(task.assignees)})"
                )
            lines.append("")

        # Blockers
        if context["blocker_summary"]["total_blockers"] > 0:
            lines.append("=== BLOCKERS ===")
            for blocker in context["blocker_summary"]["critical_blockers"]:
                task = blocker["task"]
                lines.append(f"- {task.name} [{blocker['severity']}]")
                lines.append(f"  Reasons: {', '.join(blocker['blocker_reasons'])}")
            lines.append("")

        # Incomplete tasks
        if context["validation_summary"]["incomplete_tasks"] > 0:
            lines.append("=== INCOMPLETE TASK INFO ===")
            lines.append(
                f"{context['validation_summary']['incomplete_tasks']} tasks missing critical information"
            )
            for field, count in context["validation_summary"][
                "missing_field_counts"
            ].items():
                if count > 0:
                    lines.append(f"  - {count} tasks missing {field}")
            lines.append("")

        return "\n".join(lines)
