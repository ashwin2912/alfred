"""
AI module for team visibility system.

Provides AI-powered summarization and analysis using Claude.
"""

from ai.prompts import (
    get_blocker_analysis_prompt,
    get_daily_standup_prompt,
    get_decision_extraction_prompt,
    get_person_summary_prompt,
    get_project_summary_prompt,
    get_team_summary_prompt,
)
from ai.task_summarizer import TaskSummarizer

__all__ = [
    "TaskSummarizer",
    "get_person_summary_prompt",
    "get_team_summary_prompt",
    "get_blocker_analysis_prompt",
    "get_project_summary_prompt",
    "get_daily_standup_prompt",
    "get_decision_extraction_prompt",
]
