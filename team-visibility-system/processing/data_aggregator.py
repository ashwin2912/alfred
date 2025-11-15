from collections import defaultdict
from typing import Any, Dict, List

from clients.models.task import ClickUpTask


class DataAggregator:
    """Aggregates and organizes ClickUp tasks by person, project, and other dimensions."""

    def __init__(self, tasks: List[ClickUpTask]):
        """
        Initialize aggregator with tasks.

        Args:
            tasks: List of ClickUpTask objects to aggregate
        """
        self.tasks = tasks

    def group_by_person(self) -> Dict[str, List[ClickUpTask]]:
        """
        Group tasks by assignee.

        Returns:
            Dict mapping person name to their tasks
        """
        by_person = defaultdict(list)

        for task in self.tasks:
            if task.assignees:
                for assignee in task.assignees:
                    by_person[assignee].append(task)
            else:
                by_person["Unassigned"].append(task)

        return dict(by_person)

    def group_by_status(self) -> Dict[str, List[ClickUpTask]]:
        """
        Group tasks by status.

        Returns:
            Dict mapping status to tasks
        """
        by_status = defaultdict(list)

        for task in self.tasks:
            status = task.status or "unknown"
            by_status[status].append(task)

        return dict(by_status)

    def group_by_priority(self) -> Dict[str, List[ClickUpTask]]:
        """
        Group tasks by priority.

        Returns:
            Dict mapping priority to tasks
        """
        by_priority = defaultdict(list)

        for task in self.tasks:
            priority = task.priority or "None"
            by_priority[priority].append(task)

        return dict(by_priority)

    def get_person_summary(self, person: str) -> Dict[str, Any]:
        """
        Get detailed summary for a specific person.

        Args:
            person: Person's username

        Returns:
            Dict containing task counts, status breakdown, blockers, etc.
        """
        person_tasks = [t for t in self.tasks if person in t.assignees]

        if not person_tasks:
            return {
                "person": person,
                "total_tasks": 0,
                "by_status": {},
                "blockers": [],
                "overdue": [],
                "high_priority": [],
            }

        by_status = defaultdict(list)
        blockers = []
        overdue = []
        high_priority = []

        for task in person_tasks:
            # Group by status
            by_status[task.status].append(task)

            # Identify special cases
            if task.has_blockers:
                blockers.append(task)
            if task.is_overdue:
                overdue.append(task)
            if task.priority and task.priority.lower() in ["urgent", "high", "1"]:
                high_priority.append(task)

        return {
            "person": person,
            "total_tasks": len(person_tasks),
            "by_status": {status: len(tasks) for status, tasks in by_status.items()},
            "blockers": blockers,
            "overdue": overdue,
            "high_priority": high_priority,
            "tasks": person_tasks,
        }

    def get_team_summary(self) -> Dict[str, Any]:
        """
        Get overall team summary.

        Returns:
            Dict containing team-wide statistics
        """
        by_person = self.group_by_person()
        by_status = self.group_by_status()

        all_blockers = [t for t in self.tasks if t.has_blockers]
        all_overdue = [t for t in self.tasks if t.is_overdue]
        high_priority = [
            t
            for t in self.tasks
            if t.priority and t.priority.lower() in ["urgent", "high", "1"]
        ]

        # Calculate comment activity
        tasks_with_comments = [t for t in self.tasks if t.comment_count > 0]
        total_comments = sum(t.comment_count for t in self.tasks)

        return {
            "total_tasks": len(self.tasks),
            "by_person": {person: len(tasks) for person, tasks in by_person.items()},
            "by_status": {status: len(tasks) for status, tasks in by_status.items()},
            "blockers": {"count": len(all_blockers), "tasks": all_blockers},
            "overdue": {"count": len(all_overdue), "tasks": all_overdue},
            "high_priority": {"count": len(high_priority), "tasks": high_priority},
            "comment_activity": {
                "tasks_with_comments": len(tasks_with_comments),
                "total_comments": total_comments,
            },
            "active_people": list(by_person.keys()),
        }

    def get_all_people(self) -> List[str]:
        """
        Get list of all people with assigned tasks.

        Returns:
            List of usernames
        """
        people = set()
        for task in self.tasks:
            people.update(task.assignees)
        return sorted(list(people))
