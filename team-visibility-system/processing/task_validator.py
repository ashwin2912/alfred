from typing import Any, Dict, List, Set

from clients.models.task import ClickUpTask


class TaskValidator:
    """Validates tasks for missing critical information."""

    # Required fields and their validation criteria
    REQUIRED_FIELDS = {
        "description": "Task should have a description",
        "assignees": "Task should have at least one assignee",
        "due_date": "Task should have a deadline",
        "status": "Task should have a status",
    }

    def __init__(self, tasks: List[ClickUpTask]):
        """
        Initialize validator with tasks.

        Args:
            tasks: List of ClickUpTask objects to validate
        """
        self.tasks = tasks

    def validate_task(self, task: ClickUpTask) -> Dict[str, Any]:
        """
        Validate a single task for missing information.

        Args:
            task: ClickUpTask to validate

        Returns:
            Dict with validation results
        """
        missing_fields = []

        # Check description
        if not task.description or task.description == "No description provided.":
            missing_fields.append("description")

        # Check assignees
        if not task.assignees or len(task.assignees) == 0:
            missing_fields.append("assignees")

        # Check due_date
        if not task.due_date:
            missing_fields.append("due_date")

        # Check status
        if not task.status or task.status == "unknown":
            missing_fields.append("status")

        return {
            "task": task,
            "is_valid": len(missing_fields) == 0,
            "missing_fields": missing_fields,
            "completeness_score": self._calculate_completeness(task, missing_fields),
        }

    def _calculate_completeness(
        self, task: ClickUpTask, missing_fields: List[str]
    ) -> float:
        """
        Calculate task completeness as a percentage.

        Args:
            task: The task being validated
            missing_fields: List of missing field names

        Returns:
            Completeness score (0.0 to 1.0)
        """
        total_fields = len(self.REQUIRED_FIELDS)
        missing_count = len(missing_fields)

        # Bonus points for having additional useful info
        bonus = 0
        if task.priority and task.priority != "None":
            bonus += 0.1
        if task.tags and len(task.tags) > 0:
            bonus += 0.1
        if task.comment_count > 0:
            bonus += 0.1

        base_score = (total_fields - missing_count) / total_fields
        return min(1.0, base_score + bonus)

    def validate_all_tasks(self) -> List[Dict[str, Any]]:
        """
        Validate all tasks.

        Returns:
            List of validation results
        """
        return [self.validate_task(task) for task in self.tasks]

    def get_incomplete_tasks(self) -> List[Dict[str, Any]]:
        """
        Get all tasks that are missing critical information.

        Returns:
            List of validation results for incomplete tasks
        """
        all_validations = self.validate_all_tasks()
        return [v for v in all_validations if not v["is_valid"]]

    def get_tasks_missing_field(self, field: str) -> List[ClickUpTask]:
        """
        Get tasks missing a specific field.

        Args:
            field: Field name (description, assignees, due_date, status)

        Returns:
            List of tasks missing that field
        """
        incomplete = self.get_incomplete_tasks()
        return [v["task"] for v in incomplete if field in v["missing_fields"]]

    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get summary of validation results.

        Returns:
            Dict with validation statistics
        """
        all_validations = self.validate_all_tasks()
        incomplete = [v for v in all_validations if not v["is_valid"]]

        # Count missing fields
        missing_field_counts = {
            "description": 0,
            "assignees": 0,
            "due_date": 0,
            "status": 0,
        }

        for validation in incomplete:
            for field in validation["missing_fields"]:
                missing_field_counts[field] += 1

        # Calculate average completeness
        avg_completeness = (
            sum(v["completeness_score"] for v in all_validations) / len(all_validations)
            if all_validations
            else 0
        )

        # Group by completeness level
        by_completeness = {
            "complete": [],  # 100%
            "mostly_complete": [],  # 75-99%
            "partially_complete": [],  # 50-74%
            "incomplete": [],  # < 50%
        }

        for validation in all_validations:
            score = validation["completeness_score"]
            task = validation["task"]

            if score >= 1.0:
                by_completeness["complete"].append(task)
            elif score >= 0.75:
                by_completeness["mostly_complete"].append(task)
            elif score >= 0.5:
                by_completeness["partially_complete"].append(task)
            else:
                by_completeness["incomplete"].append(task)

        return {
            "total_tasks": len(all_validations),
            "valid_tasks": len(all_validations) - len(incomplete),
            "incomplete_tasks": len(incomplete),
            "missing_field_counts": missing_field_counts,
            "average_completeness": avg_completeness,
            "by_completeness_level": {
                "complete": len(by_completeness["complete"]),
                "mostly_complete": len(by_completeness["mostly_complete"]),
                "partially_complete": len(by_completeness["partially_complete"]),
                "incomplete": len(by_completeness["incomplete"]),
            },
            "incomplete_task_details": incomplete,
        }

    def get_tasks_by_person_validation(self) -> Dict[str, Dict[str, Any]]:
        """
        Get validation summary grouped by person.

        Returns:
            Dict mapping person to their validation summary
        """
        by_person = {}

        all_validations = self.validate_all_tasks()

        for validation in all_validations:
            task = validation["task"]

            if task.assignees:
                for assignee in task.assignees:
                    if assignee not in by_person:
                        by_person[assignee] = {
                            "total_tasks": 0,
                            "incomplete_tasks": 0,
                            "incomplete_details": [],
                        }

                    by_person[assignee]["total_tasks"] += 1

                    if not validation["is_valid"]:
                        by_person[assignee]["incomplete_tasks"] += 1
                        by_person[assignee]["incomplete_details"].append(validation)
            else:
                if "Unassigned" not in by_person:
                    by_person["Unassigned"] = {
                        "total_tasks": 0,
                        "incomplete_tasks": 0,
                        "incomplete_details": [],
                    }

                by_person["Unassigned"]["total_tasks"] += 1

                if not validation["is_valid"]:
                    by_person["Unassigned"]["incomplete_tasks"] += 1
                    by_person["Unassigned"]["incomplete_details"].append(validation)

        return by_person

    def get_critical_missing_info(self) -> List[Dict[str, Any]]:
        """
        Get tasks with critical missing information (missing 2+ fields).

        Returns:
            List of validation results for critically incomplete tasks
        """
        incomplete = self.get_incomplete_tasks()
        return [v for v in incomplete if len(v["missing_fields"]) >= 2]
