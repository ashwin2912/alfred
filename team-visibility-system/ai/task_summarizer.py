import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_anthropic import ChatAnthropic

from clients.models.task import ClickUpTask

load_dotenv()


class TaskSummarizer:
    """Manages task summarization workflow using LangChain and Claude."""

    def __init__(self):
        """Initialize the task summarizer with Claude LLM."""
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")

        self.llm = ChatAnthropic(
            model="claude-3-haiku-20240307", anthropic_api_key=anthropic_api_key
        )

    def summarize_person(self, person: str, person_data: Dict[str, Any]) -> str:
        """
        Generate a person-level summary.

        Args:
            person: Person's username
            person_data: Dict containing person's tasks and statistics

        Returns:
            AI-generated summary as markdown string
        """
        from ai.prompts import get_person_summary_prompt

        prompt = get_person_summary_prompt()
        chain = prompt | self.llm

        result = chain.invoke({"person": person, "person_data": str(person_data)})
        return result.content

    def summarize_team(self, team_data: Dict[str, Any]) -> str:
        """
        Generate a team-level summary.

        Args:
            team_data: Dict containing team-wide statistics

        Returns:
            AI-generated summary as markdown string
        """
        from ai.prompts import get_team_summary_prompt

        prompt = get_team_summary_prompt()
        chain = prompt | self.llm

        result = chain.invoke({"team_data": str(team_data)})
        return result.content

    def analyze_blockers(self, blocker_data: List[Dict[str, Any]]) -> str:
        """
        Generate blocker analysis and recommendations.

        Args:
            blocker_data: List of blocker dicts from BlockerDetector

        Returns:
            AI-generated blocker analysis as markdown string
        """
        from ai.prompts import get_blocker_analysis_prompt

        prompt = get_blocker_analysis_prompt()
        chain = prompt | self.llm

        result = chain.invoke({"blocker_data": str(blocker_data)})
        return result.content

    def summarize_project(
        self, project_name: str, project_tasks: List[ClickUpTask]
    ) -> str:
        """
        Generate a project-level summary.

        Args:
            project_name: Name of the project/list/folder
            project_tasks: List of tasks in the project

        Returns:
            AI-generated project summary as markdown string
        """
        from ai.prompts import get_project_summary_prompt

        # Convert tasks to serializable format
        tasks_data = [
            {
                "id": task.id,
                "name": task.name,
                "status": task.status,
                "assignees": task.assignees,
                "priority": task.priority,
                "tags": task.tags,
                "is_overdue": task.is_overdue,
                "has_blockers": task.has_blockers,
                "comment_count": task.comment_count,
            }
            for task in project_tasks
        ]

        prompt = get_project_summary_prompt()
        chain = prompt | self.llm

        result = chain.invoke(
            {"project_name": project_name, "project_data": str(tasks_data)}
        )
        return result.content

    def generate_daily_standup(self, person: str, person_data: Dict[str, Any]) -> str:
        """
        Generate a daily standup-style summary for a person.

        Args:
            person: Person's username
            person_data: Dict containing person's tasks and statistics

        Returns:
            AI-generated standup summary
        """
        from ai.prompts import get_daily_standup_prompt

        prompt = get_daily_standup_prompt()
        chain = prompt | self.llm

        result = chain.invoke({"person": person, "person_data": str(person_data)})
        return result.content

    def extract_decisions(self, tasks: List[ClickUpTask]) -> str:
        """
        Extract key decisions from task comments and descriptions.

        Args:
            tasks: List of tasks to analyze

        Returns:
            AI-generated summary of key decisions
        """
        from ai.prompts import get_decision_extraction_prompt

        # Focus on tasks with comments
        tasks_with_activity = [t for t in tasks if t.comment_count > 0 or t.description]

        tasks_data = [
            {
                "name": task.name,
                "description": task.description,
                "comments": [
                    {"user": c.user, "text": c.comment_text, "date": c.date_readable}
                    for c in task.comments
                ],
            }
            for task in tasks_with_activity
        ]

        prompt = get_decision_extraction_prompt()
        chain = prompt | self.llm

        result = chain.invoke({"tasks_data": str(tasks_data)})
        return result.content
