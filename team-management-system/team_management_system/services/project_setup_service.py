"""Service for setting up complete projects in ClickUp from templates."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from team_management_system.models.project_template import (
    MilestoneTemplate,
    ProjectTemplate,
    TaskPriority,
    TaskTemplate,
)
from team_management_system.services.clickup_team_service import ClickUpTeamService


class ProjectSetupService:
    """Service for creating projects from templates in ClickUp."""

    def __init__(self, clickup_service: ClickUpTeamService):
        """
        Initialize project setup service.

        Args:
            clickup_service: Configured ClickUp team service
        """
        self.clickup = clickup_service
        self.task_id_map: Dict[str, str] = {}  # Map task names to ClickUp IDs

    def _get_priority_number(self, priority: TaskPriority) -> int:
        """Convert TaskPriority enum to ClickUp priority number."""
        priority_map = {
            TaskPriority.URGENT: 1,
            TaskPriority.HIGH: 2,
            TaskPriority.NORMAL: 3,
            TaskPriority.LOW: 4,
        }
        return priority_map.get(priority, 3)

    def create_task_from_template(
        self,
        task_template: TaskTemplate,
        list_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
    ) -> Dict:
        """
        Create a single task in ClickUp from a template.

        Args:
            task_template: Task template to create
            list_id: ClickUp list ID (uses default if not provided)
            start_date: Project start date for calculating due dates

        Returns:
            Created task dict from ClickUp
        """
        # Build description with all details
        description = self._build_task_description(task_template)

        # Calculate due date based on week number
        due_date = None
        if start_date and task_template.week:
            due_date_dt = start_date + timedelta(weeks=task_template.week - 1, days=6)
            due_date = int(due_date_dt.timestamp() * 1000)

        # Convert estimated hours to milliseconds
        time_estimate = None
        if task_template.estimated_hours > 0:
            time_estimate = int(task_template.estimated_hours * 60 * 60 * 1000)

        # Build tags
        tags = task_template.tags.copy()
        if task_template.phase:
            tags.append(task_template.phase.value)
        if task_template.week:
            tags.append(f"week-{task_template.week}")
        if task_template.assignee_role:
            tags.append(f"role:{task_template.assignee_role}")

        # Add skill tags
        for skill in task_template.required_skills:
            tags.append(f"skill:{skill}")

        # Create the task
        created_task = self.clickup.create_task(
            name=task_template.name,
            description=description,
            priority=self._get_priority_number(task_template.priority),
            due_date=due_date,
            time_estimate=time_estimate,
            tags=tags,
            list_id=list_id,
        )

        # Store task ID for dependency tracking
        self.task_id_map[task_template.name] = created_task["id"]

        # Create subtasks if any
        if task_template.subtasks:
            self._create_subtasks(created_task["id"], task_template.subtasks)

        return created_task

    def _build_task_description(self, task_template: TaskTemplate) -> str:
        """Build detailed task description from template."""
        lines = [task_template.description, ""]

        if task_template.required_skills:
            lines.append("**Required Skills:**")
            lines.extend(f"- {skill}" for skill in task_template.required_skills)
            lines.append("")

        if task_template.estimated_hours:
            lines.append(f"**Estimated Time:** {task_template.estimated_hours} hours")
            lines.append("")

        if task_template.dependencies:
            lines.append("**Dependencies:**")
            lines.extend(f"- {dep}" for dep in task_template.dependencies)
            lines.append("")

        if task_template.subtasks:
            lines.append("**Subtasks:**")
            lines.extend(f"- [ ] {subtask}" for subtask in task_template.subtasks)
            lines.append("")

        if task_template.assignee_role:
            lines.append(f"**Best suited for:** {task_template.assignee_role}")

        return "\n".join(lines)

    def _create_subtasks(self, parent_task_id: str, subtasks: List[str]) -> List[Dict]:
        """
        Create subtasks as checklist items.

        Args:
            parent_task_id: Parent task ID
            subtasks: List of subtask names

        Returns:
            List of created subtask dicts
        """
        # ClickUp uses checklists for subtasks
        # We'll add them as checklist items in the description
        # Or create them as actual subtasks if you prefer
        created_subtasks = []

        for subtask_name in subtasks:
            # Create as a separate task with parent relationship
            # Note: ClickUp API v2 doesn't have direct parent-child
            # We'll create them as tasks with a tag indicating the parent
            try:
                subtask = self.clickup.create_task(
                    name=f"  ↳ {subtask_name}",  # Indent to show relationship
                    description=f"Subtask of: {parent_task_id}",
                    tags=["subtask", f"parent:{parent_task_id}"],
                )
                created_subtasks.append(subtask)
            except Exception as e:
                print(f"⚠️  Failed to create subtask '{subtask_name}': {e}")

        return created_subtasks

    def create_milestone(
        self,
        milestone_template: MilestoneTemplate,
        list_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
    ) -> Dict:
        """
        Create all tasks for a milestone.

        Args:
            milestone_template: Milestone template
            list_id: ClickUp list ID
            start_date: Project start date

        Returns:
            Dict with milestone info and created tasks
        """
        print(f"\n📍 Creating milestone: {milestone_template.name}")
        print(f"   {milestone_template.description}")
        print(f"   Tasks: {len(milestone_template.tasks)}\n")

        created_tasks = []
        failed_tasks = []

        for i, task_template in enumerate(milestone_template.tasks, 1):
            try:
                print(
                    f"   [{i}/{len(milestone_template.tasks)}] Creating: {task_template.name}"
                )
                task = self.create_task_from_template(
                    task_template, list_id, start_date
                )
                created_tasks.append(task)
                print(f"       ✅ Created (ID: {task['id']})")
            except Exception as e:
                print(f"       ❌ Failed: {e}")
                failed_tasks.append({"task": task_template.name, "error": str(e)})

        # Add dependencies after all tasks are created
        self._add_task_dependencies(milestone_template.tasks)

        return {
            "milestone": milestone_template.name,
            "phase": milestone_template.phase.value,
            "created": len(created_tasks),
            "failed": len(failed_tasks),
            "tasks": created_tasks,
            "errors": failed_tasks,
        }

    def _add_task_dependencies(self, tasks: List[TaskTemplate]):
        """
        Add dependencies between tasks using ClickUp task relationships.

        Args:
            tasks: List of task templates with dependencies
        """
        for task_template in tasks:
            if not task_template.dependencies:
                continue

            task_id = self.task_id_map.get(task_template.name)
            if not task_id:
                continue

            for dependency_name in task_template.dependencies:
                dependency_id = self.task_id_map.get(dependency_name)
                if dependency_id:
                    try:
                        # Add a comment noting the dependency
                        # ClickUp API v2 task relationships are limited
                        # We'll document it in comments
                        comment = f"⚠️ Depends on: #{dependency_id} ({dependency_name})"
                        self.clickup.add_task_comment(task_id, comment)
                    except Exception as e:
                        print(f"⚠️  Failed to add dependency comment: {e}")

    def create_project_from_template(
        self,
        project_template: ProjectTemplate,
        list_id: Optional[str] = None,
        create_separate_lists: bool = False,
    ) -> Dict:
        """
        Create a complete project from template.

        Args:
            project_template: Complete project template
            list_id: ClickUp list ID for all tasks
            create_separate_lists: If True, create a list per milestone (requires folder ID)

        Returns:
            Dict with project creation summary
        """
        print("=" * 70)
        print(f"🚀 Creating Project: {project_template.name}")
        print("=" * 70)
        print(f"\nDescription: {project_template.description}")
        print(f"Milestones: {len(project_template.milestones)}")
        print(f"Total Tasks: {len(project_template.get_all_tasks())}")
        print(
            f"Total Estimated Hours: {project_template.get_total_estimated_hours():.1f}"
        )
        print()

        start_date = project_template.start_date or datetime.now()

        milestone_results = []

        for milestone_template in project_template.milestones:
            result = self.create_milestone(milestone_template, list_id, start_date)
            milestone_results.append(result)

        # Calculate summary
        total_created = sum(r["created"] for r in milestone_results)
        total_failed = sum(r["failed"] for r in milestone_results)

        print("\n" + "=" * 70)
        print("✅ Project Creation Complete!")
        print("=" * 70)
        print(f"\nTotal Tasks Created: {total_created}")
        print(f"Failed Tasks: {total_failed}")
        print(f"\nMilestone Summary:")
        for result in milestone_results:
            status = "✅" if result["failed"] == 0 else "⚠️"
            print(
                f"  {status} {result['milestone']}: {result['created']} created, {result['failed']} failed"
            )

        if total_failed > 0:
            print(f"\n⚠️  {total_failed} tasks failed to create. Check errors above.")

        return {
            "project": project_template.name,
            "total_tasks": len(project_template.get_all_tasks()),
            "created": total_created,
            "failed": total_failed,
            "milestones": milestone_results,
            "start_date": start_date.isoformat(),
        }

    def get_project_summary(self, project_template: ProjectTemplate) -> str:
        """
        Get a formatted summary of the project template.

        Args:
            project_template: Project template to summarize

        Returns:
            Formatted summary string
        """
        lines = [
            f"# {project_template.name}",
            "",
            project_template.description,
            "",
            "## Project Overview",
            "",
            f"- **Total Milestones:** {len(project_template.milestones)}",
            f"- **Total Tasks:** {len(project_template.get_all_tasks())}",
            f"- **Estimated Hours:** {project_template.get_total_estimated_hours():.1f}",
            f"- **Estimated Weeks:** {max(t.week for t in project_template.get_all_tasks() if t.week) if any(t.week for t in project_template.get_all_tasks()) else 'TBD'}",
            "",
            "## Milestones",
            "",
        ]

        for milestone in project_template.milestones:
            lines.append(f"### {milestone.name}")
            lines.append(f"**Phase:** {milestone.phase.value}")
            lines.append(f"**Tasks:** {len(milestone.tasks)}")
            lines.append(f"**Duration:** {milestone.estimated_duration_days} days")
            lines.append("")

            for task in milestone.tasks:
                lines.append(f"- [ ] {task.name} ({task.estimated_hours}h)")
                if task.required_skills:
                    lines.append(f"  - Skills: {', '.join(task.required_skills)}")

            lines.append("")

        return "\n".join(lines)


def create_project_setup_service(
    clickup_service: ClickUpTeamService,
) -> ProjectSetupService:
    """
    Factory function to create ProjectSetupService.

    Args:
        clickup_service: Configured ClickUp team service

    Returns:
        ProjectSetupService instance
    """
    return ProjectSetupService(clickup_service)
