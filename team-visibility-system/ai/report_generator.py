"""Report generator for creating daily and weekly team visibility reports."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ai.task_summarizer import TaskSummarizer
from clients.clickup_client import ClickUpClient
from clients.models.task import ClickUpTask
from processing.blocker_detector import BlockerDetector
from processing.data_aggregator import DataAggregator


class ReportGenerator:
    """Generates comprehensive team visibility reports."""

    def __init__(self, clickup_client: ClickUpClient, list_id: str):
        """
        Initialize report generator.

        Args:
            clickup_client: Initialized ClickUpClient
            list_id: ClickUp list ID to generate reports from
        """
        self.clickup_client = clickup_client
        self.list_id = list_id
        self.summarizer = TaskSummarizer()

    def generate_daily_report(self, include_individual_summaries: bool = True) -> str:
        """
        Generate a daily team report.

        Args:
            include_individual_summaries: Whether to include per-person summaries

        Returns:
            Markdown-formatted daily report
        """
        # Fetch tasks updated in last 24 hours
        tasks = self.clickup_client.fetch_recent_activity(self.list_id, hours=24)
        all_tasks = self.clickup_client.fetch_tasks_with_details(
            self.list_id, include_closed=False
        )

        aggregator = DataAggregator(all_tasks)
        detector = BlockerDetector(all_tasks)

        # Build report sections
        report_parts = []

        # Header
        today = datetime.now().strftime("%A, %B %d, %Y")
        report_parts.append(f"# Daily Team Report - {today}\n")

        # Executive Summary
        report_parts.append("## Executive Summary\n")
        team_data = aggregator.get_team_summary()
        report_parts.append(f"- **Total Active Tasks**: {team_data['total_tasks']}\n")
        report_parts.append(
            f"- **Team Members**: {len(team_data['active_people'])} ({', '.join(team_data['active_people'])})\n"
        )
        report_parts.append(f"- **Tasks Updated Today**: {len(tasks)}\n")

        status_summary = ", ".join(
            [f"{count} {status}" for status, count in team_data["by_status"].items()]
        )
        report_parts.append(f"- **Status Distribution**: {status_summary}\n")

        blocker_summary = detector.get_blocker_summary()
        report_parts.append(
            f"- **Active Blockers**: {blocker_summary['total_blockers']} "
            f"({blocker_summary['by_severity']['critical']} critical, "
            f"{blocker_summary['by_severity']['high']} high)\n"
        )

        report_parts.append("\n---\n\n")

        # Recent Activity (tasks updated today)
        if tasks:
            report_parts.append("## Today's Activity\n")
            report_parts.append(f"Tasks updated in the last 24 hours:\n\n")
            for task in tasks[:10]:  # Limit to 10 most recent
                status_emoji = self._get_status_emoji(task.status)
                report_parts.append(
                    f"- {status_emoji} **{task.name}** ({task.status})\n"
                )
                if task.assignees:
                    report_parts.append(
                        f"  - Assigned to: {', '.join(task.assignees)}\n"
                    )
                if task.comment_count > 0:
                    report_parts.append(f"  - {task.comment_count} new comments\n")
            report_parts.append("\n")
        else:
            report_parts.append("## Today's Activity\n")
            report_parts.append("No tasks updated in the last 24 hours.\n\n")

        # Critical Blockers
        critical_blockers = detector.get_critical_blockers()
        if critical_blockers:
            report_parts.append("## 🚨 Critical Blockers\n")
            blocker_analysis = self.summarizer.analyze_blockers(critical_blockers)
            report_parts.append(blocker_analysis)
            report_parts.append("\n")

        # Team Summary (AI-generated)
        report_parts.append("## Team Overview\n")
        team_summary = self.summarizer.summarize_team(team_data)
        report_parts.append(team_summary)
        report_parts.append("\n")

        # Individual Summaries (optional)
        if include_individual_summaries:
            report_parts.append("## Individual Updates\n")
            all_people = aggregator.get_all_people()

            for person in all_people:
                person_data = aggregator.get_person_summary(person)
                if person_data["total_tasks"] > 0:
                    report_parts.append(f"### {person}\n")
                    standup = self.summarizer.generate_daily_standup(
                        person, person_data
                    )
                    report_parts.append(standup)
                    report_parts.append("\n")

        # Footer
        report_parts.append("\n---\n")
        report_parts.append(
            f"_Report generated on {datetime.now().strftime('%Y-%m-%d at %H:%M')}_\n"
        )

        return "".join(report_parts)

    def generate_weekly_report(self) -> str:
        """
        Generate a weekly team report.

        Returns:
            Markdown-formatted weekly report
        """
        # Fetch tasks updated in last 7 days
        recent_tasks = self.clickup_client.fetch_recent_activity(
            self.list_id, hours=168
        )
        all_tasks = self.clickup_client.fetch_tasks_with_details(
            self.list_id, include_closed=True
        )

        aggregator = DataAggregator(all_tasks)
        detector = BlockerDetector(all_tasks)

        # Build report sections
        report_parts = []

        # Header
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        date_range = (
            f"{start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}"
        )
        report_parts.append(f"# Weekly Team Report\n")
        report_parts.append(f"## {date_range}\n\n")

        # Executive Summary
        report_parts.append("## Executive Summary\n")
        team_data = aggregator.get_team_summary()

        # Calculate completed tasks this week
        completed_this_week = [
            t for t in recent_tasks if t.status and "complete" in t.status.lower()
        ]

        report_parts.append(
            f"- **Tasks Completed This Week**: {len(completed_this_week)}\n"
        )
        report_parts.append(f"- **Total Active Tasks**: {team_data['total_tasks']}\n")
        report_parts.append(
            f"- **Team Members Active**: {len(team_data['active_people'])}\n"
        )
        report_parts.append(f"- **Tasks With Activity**: {len(recent_tasks)}\n")

        # Velocity metrics
        total_comments = sum(t.comment_count for t in recent_tasks)
        report_parts.append(
            f"- **Team Engagement**: {total_comments} comments this week\n"
        )

        report_parts.append("\n---\n\n")

        # Accomplishments
        if completed_this_week:
            report_parts.append("## ✅ Accomplishments This Week\n")
            for task in completed_this_week[:15]:  # Top 15
                report_parts.append(f"- **{task.name}**\n")
                if task.assignees:
                    report_parts.append(
                        f"  - Completed by: {', '.join(task.assignees)}\n"
                    )
            report_parts.append("\n")

        # AI-generated team summary
        report_parts.append("## Team Performance Overview\n")
        team_summary = self.summarizer.summarize_team(team_data)
        report_parts.append(team_summary)
        report_parts.append("\n")

        # Blocker Analysis
        blocker_summary = detector.get_blocker_summary()
        if blocker_summary["total_blockers"] > 0:
            report_parts.append("## 🚧 Blockers & Risks\n")
            blocker_analysis = self.summarizer.analyze_blockers(
                blocker_summary["all_blockers"]
            )
            report_parts.append(blocker_analysis)
            report_parts.append("\n")

        # Key Decisions
        tasks_with_comments = [t for t in recent_tasks if t.comment_count > 0]
        if tasks_with_comments:
            report_parts.append("## 💡 Key Decisions This Week\n")
            decisions = self.summarizer.extract_decisions(tasks_with_comments)
            report_parts.append(decisions)
            report_parts.append("\n")

        # Individual Contributions
        report_parts.append("## Individual Contributions\n")
        all_people = aggregator.get_all_people()

        for person in all_people:
            person_data = aggregator.get_person_summary(person)
            if person_data["total_tasks"] > 0:
                report_parts.append(f"### {person}\n")
                person_summary = self.summarizer.summarize_person(person, person_data)
                report_parts.append(person_summary)
                report_parts.append("\n")

        # Looking Ahead
        report_parts.append("## 🔮 Looking Ahead\n")
        high_priority = [
            t
            for t in all_tasks
            if t.priority
            and t.priority.lower() in ["urgent", "high", "1"]
            and t.status
            and "complete" not in t.status.lower()
        ]

        if high_priority:
            report_parts.append(
                f"**{len(high_priority)} high-priority tasks** for next week:\n\n"
            )
            for task in high_priority[:10]:
                report_parts.append(f"- **{task.name}**")
                if task.assignees:
                    report_parts.append(f" ({', '.join(task.assignees)})")
                report_parts.append("\n")
        else:
            report_parts.append("No high-priority tasks pending.\n")

        report_parts.append("\n")

        # Footer
        report_parts.append("\n---\n")
        report_parts.append(
            f"_Weekly report generated on {datetime.now().strftime('%Y-%m-%d at %H:%M')}_\n"
        )

        return "".join(report_parts)

    def _get_status_emoji(self, status: Optional[str]) -> str:
        """Get emoji for task status."""
        if not status:
            return "⚪"

        status_lower = status.lower()
        if "complete" in status_lower or "done" in status_lower:
            return "✅"
        elif "progress" in status_lower or "doing" in status_lower:
            return "🔄"
        elif "review" in status_lower:
            return "👀"
        elif "block" in status_lower:
            return "🚫"
        elif "todo" in status_lower or "to do" in status_lower:
            return "📝"
        else:
            return "⚪"
