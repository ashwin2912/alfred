"""Prompt templates for AI-powered task summarization."""

from langchain.prompts import PromptTemplate


def get_person_summary_prompt() -> PromptTemplate:
    """
    Returns prompt template for person-level summary.

    Generates a comprehensive summary of an individual's work.
    """
    template = """
You are an AI assistant helping generate daily work summaries for a software development team.

Analyze the following task data for **{person}** and create a concise, actionable summary.

**Person Data:**
{person_data}

**Instructions:**
Generate a summary with the following sections:

## {person}'s Summary

### Overview
- Total tasks assigned
- Task distribution by status
- Overall progress assessment

### Active Work
- List current in-progress tasks
- Highlight high-priority items
- Note any tasks nearing due dates

### Blockers & Risks
- Identify blocked tasks with reasons
- Flag overdue tasks
- Note tasks with high comment activity (may indicate issues)

### Recommendations
- Suggest priorities for today
- Identify tasks that need attention
- Recommend any tasks to escalate or discuss

**Format:** Use clear markdown formatting with bullet points. Be specific and actionable.
"""

    return PromptTemplate(template=template, input_variables=["person", "person_data"])


def get_team_summary_prompt() -> PromptTemplate:
    """
    Returns prompt template for team-level summary.

    Generates a high-level overview of the entire team's work.
    """
    template = """
You are an AI assistant helping generate team-wide visibility reports for a team.

Analyze the following team data and create an executive summary.

**Team Data:**
{team_data}

**Instructions:**
Generate a comprehensive team summary with the following sections:

## Team Summary

### Overview
- Total active tasks across the team
- Task distribution by status
- Overall team velocity and progress

### Team Member Activity
- List all active team members
- Show task distribution per person
- Highlight top contributors

### Critical Items
- Identify high-priority tasks
- List all blockers affecting the team
- Flag overdue tasks requiring immediate attention

### Communication & Collaboration
- Identify tasks with high comment activity
- Note tasks with multiple assignees (collaboration points)
- Highlight areas needing discussion

### Key Insights
- What's going well?
- What needs attention?
- Any patterns or trends to note?

### Recommendations
- Priorities for the team today
- Suggested actions to unblock progress
- Areas for team discussion

**Format:** Use clear markdown formatting. Be concise but comprehensive. Focus on actionable insights.
"""

    return PromptTemplate(template=template, input_variables=["team_data"])


def get_blocker_analysis_prompt() -> PromptTemplate:
    """
    Returns prompt template for blocker analysis.

    Focuses specifically on blocked tasks and provides recommendations.
    """
    template = """
You are an AI assistant helping identify and resolve project blockers for a team.

Analyze the following blocker data and provide actionable recommendations.

**Blocker Data:**
{blocker_data}

**Instructions:**
Generate a blocker analysis report with the following sections:

## Blocker Analysis

### Summary
- Total number of blocked tasks
- Breakdown by severity (critical, high, medium, low)
- Most common blocker types

### Critical Blockers
- List all critical and high-severity blockers
- Explain why each is critical
- Identify who is affected

### Root Causes
- Identify common patterns in blockers
- Are there systemic issues?
- Are certain people or projects more affected?

### Impact Assessment
- Which blockers are blocking multiple people?
- Which blockers affect high-priority work?
- Estimated impact on team velocity

### Recommended Actions
For each critical blocker, suggest:
- Immediate action to take
- Who should be involved
- Timeline for resolution

### Prevention Strategies
- How to prevent similar blockers in the future
- Process improvements to consider
- Early warning signs to watch for

**Format:** Use clear markdown formatting. Prioritize by impact. Be specific and actionable.
"""

    return PromptTemplate(template=template, input_variables=["blocker_data"])


def get_project_summary_prompt() -> PromptTemplate:
    """
    Returns prompt template for project-level summary.

    Generates a summary for a specific project/list/folder.
    """
    template = """
You are an AI assistant helping track project progress for a software development team.

Analyze the following project data and create a project status summary.

**Project:** {project_name}

**Project Data:**
{project_data}

**Instructions:**
Generate a project summary with the following sections:

## Project: {project_name}

### Overview
- Total tasks in project
- Task breakdown by status
- Project health assessment (on track / at risk / blocked)

### Progress Summary
- What's been completed recently?
- What's currently in progress?
- What's upcoming?

### Team Involvement
- Who's working on this project?
- Task distribution among team members
- Any resource constraints?

### Risks & Blockers
- Identify blocked tasks
- Flag overdue items
- Note high-priority tasks at risk

### Key Milestones
- Important tasks to track
- Dependencies to be aware of
- Critical path items

### Recommendations
- What should be prioritized?
- Any tasks that need reassignment?
- Suggested next steps

**Format:** Use clear markdown formatting. Focus on project health and actionable next steps.
"""

    return PromptTemplate(
        template=template, input_variables=["project_name", "project_data"]
    )


def get_daily_standup_prompt() -> PromptTemplate:
    """
    Returns prompt template for daily standup summary.

    Generates a quick standup-style summary (Yesterday/Today/Blockers).
    """
    template = """
You are an AI assistant helping team members prepare for daily standup meetings.

Generate a concise standup summary for **{person}** based on their task data.

**Person Data:**
{person_data}

**Instructions:**
Generate a standup-style summary in this format:

## Daily Standup - {person}

### What I worked on (Recently Updated)
- List tasks that were recently updated or completed
- Focus on actual progress made

### What I'm working on today (In Progress)
- List current in-progress tasks
- Prioritize by importance/urgency

### Blockers
- List any blocked tasks
- Explain what's blocking each task
- Specify what help is needed

### Focus for Today
- Recommend 2-3 key tasks to prioritize
- Explain why these are important

**Format:** Keep it brief and conversational - this should take <2 minutes to read in a standup. Use bullet points.
"""

    return PromptTemplate(template=template, input_variables=["person", "person_data"])


def get_decision_extraction_prompt() -> PromptTemplate:
    """
    Returns prompt template for extracting key decisions from tasks.

    Analyzes comments and descriptions to find important decisions.
    """
    template = """
You are an AI assistant helping track important decisions made during project work.

Analyze the following task data and extract key decisions that were made.

**Task Data:**
{tasks_data}

**Instructions:**
Extract and summarize key decisions from task comments and descriptions.

## Key Decisions

For each decision identified:

### Decision: [Brief title]
- **Context:** What was the situation/problem?
- **Decision Made:** What was decided?
- **Rationale:** Why was this decision made?
- **Task:** [Link task name where decision was discussed]
- **Participants:** Who was involved in the decision?
- **Date:** When was this decided?

**Focus on:**
- Technical architecture decisions
- Feature scope decisions
- Priority/timeline changes
- Process changes
- Trade-offs or alternatives considered

**Ignore:**
- Minor implementation details
- Routine status updates
- General discussion without conclusions

**Format:** Use clear markdown formatting. Only include significant decisions that affect the project or team.
"""

    return PromptTemplate(template=template, input_variables=["tasks_data"])
