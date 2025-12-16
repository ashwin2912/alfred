"""Google Doc generator for project plans."""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Add shared-services to path for imports
shared_services_path = (
    Path(__file__).parent.parent.parent / "shared-services" / "docs-service"
)
sys.path.insert(0, str(shared_services_path))

from docs_service.google_docs_client import GoogleDocsService


class ProjectPlanDocGenerator:
    """
    Generates formatted Google Docs for project plans.

    Takes AI-generated project plans and creates well-formatted,
    human-readable Google Docs with proper structure.
    """

    def __init__(self, docs_service: GoogleDocsService):
        """
        Initialize doc generator.

        Args:
            docs_service: Configured GoogleDocsService instance
        """
        self.docs_service = docs_service

    def generate_project_plan_doc(
        self, plan: Dict[str, Any], folder_id: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate a Google Doc from a complete project plan.

        Args:
            plan: Complete project plan from ProjectBrainstormer.generate_complete_plan()
            folder_id: Optional Google Drive folder ID

        Returns:
            Dict with doc_id and doc_url

        Example:
            >>> generator = ProjectPlanDocGenerator(docs_service)
            >>> result = generator.generate_project_plan_doc(plan)
            >>> print(result['doc_url'])
            https://docs.google.com/document/d/...
        """
        analysis = plan["analysis"]
        milestones = plan["milestones"]
        summary = plan["summary"]

        # Generate document content
        content = self._format_project_plan(analysis, milestones, summary)

        # Create the document
        doc = self.docs_service.create_document(
            title=analysis["title"], content=content, folder_id=folder_id
        )

        return {"doc_id": doc.id, "doc_url": doc.url, "title": doc.title}

    def _format_project_plan(
        self, analysis: Dict[str, Any], milestones: list, summary: Dict[str, Any]
    ) -> str:
        """
        Format the project plan as markdown-style text for Google Docs.

        Args:
            analysis: Project analysis dict
            milestones: List of milestones with tasks
            summary: Summary statistics

        Returns:
            Formatted text content
        """
        content = []

        # Header
        content.append(f"# {analysis['title']}\n\n")
        content.append(f"**Generated:** {self._get_current_date()}\n\n")

        # Executive Summary
        content.append("## Executive Summary\n\n")
        content.append(f"{analysis['summary']}\n\n")

        # Quick Stats
        content.append("## Project Overview\n\n")
        content.append(f"**Duration:** {analysis['estimated_duration']}\n")
        content.append(f"**Team Size:** {analysis['team_size']}\n")
        content.append(f"**Total Milestones:** {summary['total_milestones']}\n")
        content.append(f"**Total Tasks:** {summary['total_tasks']}\n")
        content.append(f"**Estimated Hours:** {summary['total_estimated_hours']}\n\n")

        # Goals
        content.append("## Project Goals\n\n")
        for i, goal in enumerate(analysis["goals"], 1):
            content.append(f"{i}. {goal}\n")
        content.append("\n")

        # Scope
        content.append("## Scope\n\n")
        content.append("### In Scope\n\n")
        for item in analysis["scope"]["in_scope"]:
            content.append(f"• {item}\n")
        content.append("\n")

        content.append("### Out of Scope\n\n")
        for item in analysis["scope"]["out_of_scope"]:
            content.append(f"• {item}\n")
        content.append("\n")

        # Target Users
        content.append("## Target Users\n\n")
        content.append(f"{analysis['target_users']}\n\n")

        # Success Metrics
        content.append("## Success Metrics\n\n")
        for metric in analysis["success_metrics"]:
            content.append(f"• {metric}\n")
        content.append("\n")

        # Technical Requirements
        content.append("## Technical Requirements\n\n")
        for req in analysis["technical_requirements"]:
            content.append(f"• {req}\n")
        content.append("\n")

        # Risks
        content.append("## Risks & Mitigation\n\n")
        for risk in analysis["risks"]:
            severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                risk["severity"], "⚪"
            )
            content.append(f"### {severity_emoji} {risk['risk']}\n\n")
            content.append(f"**Severity:** {risk['severity'].title()}\n\n")
            content.append(f"**Mitigation:** {risk['mitigation']}\n\n")

        # Milestones & Tasks
        content.append("## Milestones & Tasks\n\n")
        content.append("---\n\n")

        for i, milestone in enumerate(milestones, 1):
            content.append(f"### Milestone {i}: {milestone['name']}\n\n")
            content.append(f"**Duration:** {milestone['duration']}\n\n")
            content.append(f"**Description:** {milestone['description']}\n\n")

            if milestone.get("deliverables"):
                content.append("**Deliverables:**\n")
                for deliverable in milestone["deliverables"]:
                    content.append(f"• {deliverable}\n")
                content.append("\n")

            if milestone.get("dependencies"):
                content.append("**Dependencies:** ")
                if milestone["dependencies"]:
                    content.append(", ".join(milestone["dependencies"]) + "\n\n")
                else:
                    content.append("None\n\n")

            # Tasks for this milestone
            content.append("#### Tasks\n\n")
            tasks = milestone.get("tasks", [])

            for j, task in enumerate(tasks, 1):
                priority_emoji = {"high": "🔥", "medium": "⚡", "low": "📌"}.get(
                    task["priority"], "•"
                )

                content.append(f"{j}. {priority_emoji} **{task['name']}**\n")
                content.append(f"   - **Description:** {task['description']}\n")
                content.append(f"   - **Estimated Hours:** {task['estimated_hours']}\n")
                content.append(f"   - **Priority:** {task['priority'].title()}\n")
                content.append(
                    f"   - **Required Skills:** {', '.join(task['required_skills'])}\n"
                )

                if task.get("dependencies"):
                    deps = (
                        ", ".join(task["dependencies"])
                        if task["dependencies"]
                        else "None"
                    )
                    content.append(f"   - **Dependencies:** {deps}\n")

                if task.get("deliverable"):
                    content.append(f"   - **Deliverable:** {task['deliverable']}\n")

                content.append(f"   - **Status:** [ ] Not Started\n\n")

            content.append("---\n\n")

        # Next Steps
        content.append("## Next Steps\n\n")
        content.append("1. Review this project plan with the team\n")
        content.append(
            "2. Assign tasks to team members based on skills and availability\n"
        )
        content.append(
            "3. Create tasks in ClickUp using the `/publish-project` command\n"
        )
        content.append("4. Begin execution with Milestone 1\n\n")

        # Footer
        content.append("---\n\n")
        content.append(
            "*This project plan was generated by Alfred's AI Project Planning System.*\n"
        )
        content.append("*Edit this document as needed - it's your plan!*\n")

        return "".join(content)

    def _get_current_date(self) -> str:
        """Get current date in readable format."""
        from datetime import datetime

        return datetime.now().strftime("%B %d, %Y")


def create_doc_generator(docs_service: GoogleDocsService) -> ProjectPlanDocGenerator:
    """
    Factory function to create ProjectPlanDocGenerator.

    Args:
        docs_service: Configured GoogleDocsService instance

    Returns:
        ProjectPlanDocGenerator instance
    """
    return ProjectPlanDocGenerator(docs_service)
