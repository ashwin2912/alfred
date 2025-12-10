"""Document templates for common use cases."""

from typing import Any, Dict


class TeamMemberProfileTemplate:
    """Template for team member profile documents."""

    @staticmethod
    def generate(data: Dict[str, Any]) -> str:
        """
        Generate team member profile content.

        Args:
            data: Dictionary with member information

        Returns:
            Formatted markdown content
        """
        name = data.get("name", "Unknown")
        email = data.get("email", "")
        role = data.get("role", "Team Member")
        bio = data.get("bio", "")
        timezone = data.get("timezone", "UTC")
        availability = data.get("availability", "40 hours/week")
        skills = data.get("skills", [])
        preferred_tasks = data.get("preferred_tasks", [])
        links = data.get("links", {})

        content = f"""# {name}

## Contact Information
- **Email:** {email}
- **Role:** {role}
- **Timezone:** {timezone}

## About
{bio if bio else "No bio provided."}

## Availability
**Hours per week:** {availability}

## Skills & Expertise
"""

        if skills:
            for skill in skills:
                skill_name = skill.get("name", "Unknown")
                skill_level = skill.get("experience_level", "Not specified")
                skill_years = skill.get("years_of_experience", "")

                content += f"\n### {skill_name}\n"
                content += f"- **Proficiency:** {skill_level}\n"
                if skill_years:
                    content += f"- **Experience:** {skill_years} years\n"
        else:
            content += "\nNo skills listed.\n"

        content += "\n## Preferred Task Types\n"
        if preferred_tasks:
            for task_type in preferred_tasks:
                content += f"- {task_type}\n"
        else:
            content += "Not specified.\n"

        content += "\n## Links\n"
        if links:
            if links.get("github"):
                content += f"- **GitHub:** {links['github']}\n"
            if links.get("linkedin"):
                content += f"- **LinkedIn:** {links['linkedin']}\n"
            if links.get("portfolio"):
                content += f"- **Portfolio:** {links['portfolio']}\n"
        else:
            content += "No links provided.\n"

        content += f"\n\n---\n*Last updated: {data.get('updated_at', 'Unknown')}*\n"

        return content

    @staticmethod
    def get_schema() -> Dict[str, Any]:
        """
        Get the expected data schema for this template.

        Returns:
            Dictionary describing the expected fields
        """
        return {
            "name": {"type": "string", "required": True},
            "email": {"type": "string", "required": True},
            "role": {"type": "string", "required": True},
            "bio": {"type": "string", "required": False},
            "timezone": {"type": "string", "required": False},
            "availability": {"type": "string", "required": False},
            "skills": {
                "type": "list",
                "required": False,
                "items": {
                    "name": {"type": "string"},
                    "experience_level": {"type": "string"},
                    "years_of_experience": {"type": "number"},
                },
            },
            "preferred_tasks": {"type": "list", "required": False},
            "links": {
                "type": "dict",
                "required": False,
                "fields": {
                    "github": {"type": "string"},
                    "linkedin": {"type": "string"},
                    "portfolio": {"type": "string"},
                },
            },
        }


class MeetingNotesTemplate:
    """Template for meeting notes."""

    @staticmethod
    def generate(data: Dict[str, Any]) -> str:
        """Generate meeting notes content."""
        title = data.get("title", "Meeting Notes")
        date = data.get("date", "")
        attendees = data.get("attendees", [])
        agenda = data.get("agenda", [])
        notes = data.get("notes", "")
        action_items = data.get("action_items", [])

        content = f"""# {title}

**Date:** {date}

## Attendees
"""
        for attendee in attendees:
            content += f"- {attendee}\n"

        content += "\n## Agenda\n"
        for i, item in enumerate(agenda, 1):
            content += f"{i}. {item}\n"

        content += f"\n## Notes\n{notes}\n"

        content += "\n## Action Items\n"
        for item in action_items:
            assignee = item.get("assignee", "Unassigned")
            task = item.get("task", "")
            due = item.get("due_date", "")
            content += f"- [ ] **{assignee}:** {task}"
            if due:
                content += f" (Due: {due})"
            content += "\n"

        return content


class ProjectDocumentationTemplate:
    """Template for project documentation."""

    @staticmethod
    def generate(data: Dict[str, Any]) -> str:
        """Generate project documentation content."""
        project_name = data.get("project_name", "Project")
        description = data.get("description", "")
        goals = data.get("goals", [])
        tech_stack = data.get("tech_stack", [])
        team = data.get("team", [])
        timeline = data.get("timeline", "")

        content = f"""# {project_name}

## Overview
{description}

## Goals
"""
        for i, goal in enumerate(goals, 1):
            content += f"{i}. {goal}\n"

        content += "\n## Tech Stack\n"
        for tech in tech_stack:
            content += f"- {tech}\n"

        content += "\n## Team\n"
        for member in team:
            content += f"- {member}\n"

        content += f"\n## Timeline\n{timeline}\n"

        return content
