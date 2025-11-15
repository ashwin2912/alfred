from typing import Any, Dict, List

from clients.models.task import ClickUpTask


class BlockerDetector:
    """Detects and analyzes blockers in tasks."""

    # Keywords that indicate blockers in task names, descriptions, or comments
    BLOCKER_KEYWORDS = [
        "blocked",
        "blocker",
        "waiting on",
        "waiting for",
        "stuck",
        "dependency",
        "blocked by",
        "needs review",
        "pending approval",
        "on hold",
    ]

    def __init__(self, tasks: List[ClickUpTask]):
        """
        Initialize blocker detector.

        Args:
            tasks: List of ClickUpTask objects to analyze
        """
        self.tasks = tasks

    def detect_all_blockers(self) -> List[Dict[str, Any]]:
        """
        Detect all blockers across tasks.

        Returns:
            List of dicts containing blocker information
        """
        blockers = []

        for task in self.tasks:
            blocker_info = self.analyze_task(task)
            if blocker_info["is_blocked"]:
                blockers.append(blocker_info)

        return blockers

    def analyze_task(self, task: ClickUpTask) -> Dict[str, Any]:
        """
        Analyze a single task for blocker indicators.

        Args:
            task: ClickUpTask to analyze

        Returns:
            Dict with blocker analysis
        """
        reasons = []

        # Check 1: Status contains "block"
        if task.status and "block" in task.status.lower():
            reasons.append(f"Status is '{task.status}'")

        # Check 2: Tags contain blocker keywords
        for tag in task.tags:
            if any(keyword in tag.lower() for keyword in self.BLOCKER_KEYWORDS):
                reasons.append(f"Tag: '{tag}'")

        # Check 3: Task name contains blocker keywords
        if any(keyword in task.name.lower() for keyword in self.BLOCKER_KEYWORDS):
            reasons.append("Task name contains blocker keyword")

        # Check 4: Description contains blocker keywords
        if any(
            keyword in task.description.lower() for keyword in self.BLOCKER_KEYWORDS
        ):
            reasons.append("Description mentions blocker")

        # Check 5: Overdue with no recent activity
        if task.is_overdue:
            reasons.append("Task is overdue")

        # Check 6: High comment count (might indicate issues)
        if task.comment_count > 5:
            reasons.append(f"High comment activity ({task.comment_count} comments)")

        # Check 7: Custom fields indicating blockers
        for field_name, field_value in task.custom_fields.items():
            if "block" in field_name.lower():
                reasons.append(f"Custom field '{field_name}': {field_value}")

        return {
            "task": task,
            "is_blocked": len(reasons) > 0,
            "blocker_reasons": reasons,
            "severity": self._calculate_severity(reasons, task),
        }

    def _calculate_severity(self, reasons: List[str], task: ClickUpTask) -> str:
        """
        Calculate blocker severity.

        Args:
            reasons: List of blocker reasons
            task: The task being analyzed

        Returns:
            Severity level: 'critical', 'high', 'medium', 'low'
        """
        severity_score = 0

        # More reasons = higher severity
        severity_score += len(reasons)

        # High priority tasks get extra weight
        if task.priority and task.priority.lower() in ["urgent", "high", "1"]:
            severity_score += 3

        # Overdue adds weight
        if task.is_overdue:
            severity_score += 2

        # Multiple assignees might indicate coordination issues
        if len(task.assignees) > 2:
            severity_score += 1

        # Determine severity
        if severity_score >= 6:
            return "critical"
        elif severity_score >= 4:
            return "high"
        elif severity_score >= 2:
            return "medium"
        else:
            return "low"

    def get_blockers_by_person(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get blockers grouped by person.

        Returns:
            Dict mapping person to their blocked tasks
        """
        all_blockers = self.detect_all_blockers()

        by_person = {}
        for blocker in all_blockers:
            task = blocker["task"]
            if task.assignees:
                for assignee in task.assignees:
                    if assignee not in by_person:
                        by_person[assignee] = []
                    by_person[assignee].append(blocker)
            else:
                if "Unassigned" not in by_person:
                    by_person["Unassigned"] = []
                by_person["Unassigned"].append(blocker)

        return by_person

    def get_critical_blockers(self) -> List[Dict[str, Any]]:
        """
        Get only critical severity blockers.

        Returns:
            List of critical blocker dicts
        """
        all_blockers = self.detect_all_blockers()
        return [b for b in all_blockers if b["severity"] in ["critical", "high"]]

    def get_blocker_summary(self) -> Dict[str, Any]:
        """
        Get summary of all blockers.

        Returns:
            Dict with blocker statistics
        """
        all_blockers = self.detect_all_blockers()

        by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for blocker in all_blockers:
            by_severity[blocker["severity"]] += 1

        return {
            "total_blockers": len(all_blockers),
            "by_severity": by_severity,
            "critical_blockers": self.get_critical_blockers(),
            "all_blockers": all_blockers,
        }
