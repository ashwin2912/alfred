"""Project template models for creating structured projects in ClickUp."""

from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel


class TaskPriority(str, Enum):
    """Task priority levels."""

    URGENT = "urgent"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class TaskStatus(str, Enum):
    """Task status options."""

    TODO = "to do"
    IN_PROGRESS = "in progress"
    BLOCKED = "blocked"
    REVIEW = "in review"
    DONE = "complete"


class ProjectPhase(str, Enum):
    """Project phases."""

    PHASE_1 = "Phase 1: MVP"
    PHASE_2 = "Phase 2: Intelligence"
    PHASE_3 = "Phase 3: Reporting & Automation"


class TaskTemplate(BaseModel):
    """Template for a task to be created."""

    name: str
    description: str
    priority: TaskPriority = TaskPriority.NORMAL
    estimated_hours: float = 0
    tags: List[str] = []
    required_skills: List[str] = []
    dependencies: List[str] = []  # Task names this depends on
    phase: Optional[ProjectPhase] = None
    week: Optional[int] = None  # Week number in project
    assignee_role: Optional[str] = None  # Role that should handle this
    subtasks: List[str] = []  # List of subtask names


class MilestoneTemplate(BaseModel):
    """Template for a project milestone."""

    name: str
    description: str
    phase: ProjectPhase
    tasks: List[TaskTemplate]
    estimated_duration_days: int = 7


class ProjectTemplate(BaseModel):
    """Complete project template with all phases and tasks."""

    name: str
    description: str
    milestones: List[MilestoneTemplate]
    start_date: Optional[datetime] = None

    def get_all_tasks(self) -> List[TaskTemplate]:
        """Get all tasks from all milestones."""
        all_tasks = []
        for milestone in self.milestones:
            all_tasks.extend(milestone.tasks)
        return all_tasks

    def get_tasks_by_phase(self, phase: ProjectPhase) -> List[TaskTemplate]:
        """Get all tasks for a specific phase."""
        tasks = []
        for milestone in self.milestones:
            if milestone.phase == phase:
                tasks.extend(milestone.tasks)
        return tasks

    def get_total_estimated_hours(self) -> float:
        """Calculate total estimated hours for the project."""
        return sum(task.estimated_hours for task in self.get_all_tasks())


def create_team_onboarding_project_template() -> ProjectTemplate:
    """
    Create the Team Onboarding & Management System project template.

    This template matches the implementation plan from TEAM_ONBOARDING_SYSTEM.md
    """

    # Phase 1: MVP - Week 1
    week1_foundation = MilestoneTemplate(
        name="Week 1: Foundation",
        description="Set up database, onboarding form, Google Docs, and ClickUp integration",
        phase=ProjectPhase.PHASE_1,
        estimated_duration_days=7,
        tasks=[
            # Database Setup
            TaskTemplate(
                name="Design database schema",
                description="Define tables: team_members, skills, availability, task_assignments, progress_logs",
                priority=TaskPriority.HIGH,
                estimated_hours=4,
                tags=["database", "design"],
                required_skills=["SQLAlchemy", "Database Design"],
                week=1,
                assignee_role="developer",
                subtasks=[
                    "Create team_members table",
                    "Create skills table with member_id FK",
                    "Create availability table",
                    "Create task_assignments table",
                    "Create progress_logs table",
                ],
            ),
            TaskTemplate(
                name="Create SQLite database and models",
                description="Set up SQLAlchemy models and create initial database",
                priority=TaskPriority.HIGH,
                estimated_hours=6,
                tags=["database", "backend"],
                required_skills=["Python", "SQLAlchemy"],
                dependencies=["Design database schema"],
                week=1,
                assignee_role="developer",
                subtasks=[
                    "Install SQLAlchemy and dependencies",
                    "Create database.py with connection logic",
                    "Create models.py with all table models",
                    "Write migration script",
                    "Test CRUD operations",
                ],
            ),
            TaskTemplate(
                name="Implement database CRUD operations",
                description="Write basic Create, Read, Update, Delete operations for all models",
                priority=TaskPriority.HIGH,
                estimated_hours=8,
                tags=["database", "backend"],
                required_skills=["Python", "SQLAlchemy"],
                dependencies=["Create SQLite database and models"],
                week=1,
                assignee_role="developer",
                subtasks=[
                    "Create team member CRUD",
                    "Create skills CRUD",
                    "Create availability CRUD",
                    "Add validation and error handling",
                    "Write unit tests for CRUD operations",
                ],
            ),
            # Onboarding Form
            TaskTemplate(
                name="Design onboarding form UI",
                description="Design simple and intuitive onboarding form layout",
                priority=TaskPriority.NORMAL,
                estimated_hours=4,
                tags=["frontend", "design"],
                required_skills=["UI/UX Design", "Streamlit"],
                week=1,
                assignee_role="designer",
                subtasks=[
                    "Sketch form layout",
                    "Define form fields and validation",
                    "Create color scheme and styling",
                ],
            ),
            TaskTemplate(
                name="Build Streamlit onboarding form",
                description="Create web form with fields: name, email, role, skills, experience, availability, timezone",
                priority=TaskPriority.HIGH,
                estimated_hours=10,
                tags=["frontend", "streamlit"],
                required_skills=["Python", "Streamlit"],
                dependencies=["Design onboarding form UI"],
                week=1,
                assignee_role="developer",
                subtasks=[
                    "Set up Streamlit app structure",
                    "Add form fields with validation",
                    "Implement multi-select for skills",
                    "Add experience level selector per skill",
                    "Connect form to database",
                    "Add success/error messages",
                ],
            ),
            # Google Docs Integration
            TaskTemplate(
                name="Create member profile template",
                description="Design Google Doc template for team member profiles",
                priority=TaskPriority.NORMAL,
                estimated_hours=3,
                tags=["documentation", "template"],
                required_skills=["Documentation", "Google Docs"],
                week=1,
                assignee_role="designer",
            ),
            TaskTemplate(
                name="Implement auto-generate profile docs",
                description="Create service to auto-generate Google Doc profiles from onboarding data",
                priority=TaskPriority.HIGH,
                estimated_hours=8,
                tags=["backend", "integration"],
                required_skills=["Python", "Google Docs API"],
                dependencies=["Create member profile template"],
                week=1,
                assignee_role="developer",
                subtasks=[
                    "Extend existing Google Docs client",
                    "Load profile template",
                    "Populate template with member data",
                    "Set up folder structure in Google Drive",
                    "Test profile generation",
                ],
            ),
            # ClickUp Integration
            TaskTemplate(
                name="Add team member custom fields to ClickUp",
                description="Create custom fields in ClickUp for team member skills and availability",
                priority=TaskPriority.NORMAL,
                estimated_hours=4,
                tags=["clickup", "integration"],
                required_skills=["ClickUp API"],
                week=1,
                assignee_role="developer",
                subtasks=[
                    "Create skills custom field",
                    "Create availability custom field",
                    "Create timezone custom field",
                    "Test custom fields in ClickUp",
                ],
            ),
            TaskTemplate(
                name="Implement task assignment to members",
                description="Extend ClickUp service to assign tasks to team members and sync with database",
                priority=TaskPriority.HIGH,
                estimated_hours=6,
                tags=["clickup", "backend"],
                required_skills=["Python", "ClickUp API"],
                dependencies=["Add team member custom fields to ClickUp"],
                week=1,
                assignee_role="developer",
                subtasks=[
                    "Implement find user by email",
                    "Implement assign task function",
                    "Implement unassign task function",
                    "Sync assignments with local database",
                    "Add error handling",
                ],
            ),
        ],
    )

    # Phase 1: MVP - Week 2
    week2_chatbot = MilestoneTemplate(
        name="Week 2: Chatbot & Basic Commands",
        description="Build Slack bot with basic commands for task viewing and progress updates",
        phase=ProjectPhase.PHASE_1,
        estimated_duration_days=7,
        tasks=[
            TaskTemplate(
                name="Set up Slack bot with Bolt SDK",
                description="Initialize Slack bot app and set up event handling",
                priority=TaskPriority.HIGH,
                estimated_hours=6,
                tags=["slack", "chatbot"],
                required_skills=["Python", "Slack Bolt SDK"],
                week=2,
                assignee_role="developer",
                subtasks=[
                    "Create Slack app in workspace",
                    "Install Slack Bolt SDK",
                    "Set up bot authentication",
                    "Configure event subscriptions",
                    "Test basic bot connection",
                ],
            ),
            TaskTemplate(
                name="Implement /help command",
                description="Create help command showing all available bot commands",
                priority=TaskPriority.NORMAL,
                estimated_hours=2,
                tags=["slack", "chatbot"],
                required_skills=["Python", "Slack Bolt SDK"],
                dependencies=["Set up Slack bot with Bolt SDK"],
                week=2,
                assignee_role="developer",
            ),
            TaskTemplate(
                name="Implement /my-tasks command",
                description="Fetch and display user's ClickUp tasks in Slack",
                priority=TaskPriority.HIGH,
                estimated_hours=8,
                tags=["slack", "chatbot", "clickup"],
                required_skills=["Python", "Slack Bolt SDK", "ClickUp API"],
                dependencies=["Set up Slack bot with Bolt SDK"],
                week=2,
                assignee_role="developer",
                subtasks=[
                    "Parse /my-tasks command",
                    "Get user email from Slack",
                    "Fetch tasks from ClickUp for user",
                    "Format tasks with Slack Block Kit",
                    "Handle pagination for many tasks",
                    "Add filters (status, priority)",
                ],
            ),
            TaskTemplate(
                name="Implement /update command for progress",
                description="Allow users to update task progress via Slack",
                priority=TaskPriority.HIGH,
                estimated_hours=10,
                tags=["slack", "chatbot", "clickup"],
                required_skills=["Python", "Slack Bolt SDK", "ClickUp API"],
                dependencies=["Implement /my-tasks command"],
                week=2,
                assignee_role="developer",
                subtasks=[
                    "Parse /update command with task ID and text",
                    "Validate task ID exists",
                    "Add comment to ClickUp task",
                    "Log update in database",
                    "Send confirmation to user",
                    "Handle errors gracefully",
                ],
            ),
            TaskTemplate(
                name="Create message formatters for Slack",
                description="Build reusable formatters for displaying tasks, teams, and reports",
                priority=TaskPriority.NORMAL,
                estimated_hours=5,
                tags=["slack", "ui"],
                required_skills=["Python", "Slack Block Kit"],
                dependencies=["Implement /my-tasks command"],
                week=2,
                assignee_role="developer",
                subtasks=[
                    "Create task card formatter",
                    "Create task list formatter",
                    "Create team member formatter",
                    "Add color coding for priority",
                    "Add emoji indicators for status",
                ],
            ),
            TaskTemplate(
                name="Add progress logging to database",
                description="Store all progress updates in database for reporting",
                priority=TaskPriority.NORMAL,
                estimated_hours=4,
                tags=["backend", "database"],
                required_skills=["Python", "SQLAlchemy"],
                dependencies=["Implement /update command for progress"],
                week=2,
                assignee_role="developer",
            ),
        ],
    )

    # Phase 2: Intelligence - Week 3
    week3_skill_matching = MilestoneTemplate(
        name="Week 3: Skill Matching",
        description="Build AI-powered skill parsing and task assignment recommender",
        phase=ProjectPhase.PHASE_2,
        estimated_duration_days=7,
        tasks=[
            TaskTemplate(
                name="Build Claude AI skill parser",
                description="Use Claude to extract and normalize skills from free-text onboarding",
                priority=TaskPriority.HIGH,
                estimated_hours=10,
                tags=["ai", "backend"],
                required_skills=["Python", "Claude API", "Prompt Engineering"],
                week=3,
                assignee_role="developer",
                subtasks=[
                    "Set up Claude API client",
                    "Design prompts for skill extraction",
                    "Parse skills from free text",
                    "Normalize skill names (e.g., 'JS' -> 'JavaScript')",
                    "Assign confidence scores",
                    "Store parsed skills in database",
                ],
            ),
            TaskTemplate(
                name="Implement availability calculator",
                description="Calculate team member workload and availability from ClickUp",
                priority=TaskPriority.HIGH,
                estimated_hours=8,
                tags=["backend", "clickup"],
                required_skills=["Python", "ClickUp API"],
                week=3,
                assignee_role="developer",
                subtasks=[
                    "Fetch all tasks for a member",
                    "Sum time estimates for open tasks",
                    "Compare with member's hours_per_week",
                    "Calculate availability percentage",
                    "Cache results for performance",
                ],
            ),
            TaskTemplate(
                name="Build skill matching algorithm",
                description="Create algorithm to score and rank team members for tasks",
                priority=TaskPriority.HIGH,
                estimated_hours=12,
                tags=["backend", "algorithm"],
                required_skills=["Python", "Algorithm Design"],
                dependencies=[
                    "Build Claude AI skill parser",
                    "Implement availability calculator",
                ],
                week=3,
                assignee_role="developer",
                subtasks=[
                    "Extract required skills from task description",
                    "Query database for matching members",
                    "Score skill match (0-100)",
                    "Score availability (0-100)",
                    "Calculate weighted overall score",
                    "Return top N ranked suggestions",
                    "Include reasoning for scores",
                ],
            ),
            TaskTemplate(
                name="Create /find-person command",
                description="Chatbot command to find team members with specific skills",
                priority=TaskPriority.NORMAL,
                estimated_hours=6,
                tags=["slack", "chatbot"],
                required_skills=["Python", "Slack Bolt SDK"],
                dependencies=["Build skill matching algorithm"],
                week=3,
                assignee_role="developer",
                subtasks=[
                    "Parse /find-person command with skill query",
                    "Search database for members with skill",
                    "Display ranked results in Slack",
                    "Show availability for each member",
                ],
            ),
            TaskTemplate(
                name="Implement /assign command for PMs",
                description="Allow PMs to assign tasks with AI recommendations",
                priority=TaskPriority.HIGH,
                estimated_hours=8,
                tags=["slack", "chatbot", "ai"],
                required_skills=["Python", "Slack Bolt SDK"],
                dependencies=["Build skill matching algorithm"],
                week=3,
                assignee_role="developer",
                subtasks=[
                    "Parse task requirements from message",
                    "Get AI recommendations",
                    "Show interactive buttons for top 3 matches",
                    "Assign task on button click",
                    "Notify assignee in Slack",
                ],
            ),
        ],
    )

    # Phase 2: Intelligence - Week 4
    week4_nlu = MilestoneTemplate(
        name="Week 4: NLU Chatbot",
        description="Add natural language understanding and weekly goals tracking",
        phase=ProjectPhase.PHASE_2,
        estimated_duration_days=7,
        tasks=[
            TaskTemplate(
                name="Build chatbot NLU with Claude",
                description="Integrate Claude for understanding natural language queries",
                priority=TaskPriority.HIGH,
                estimated_hours=12,
                tags=["ai", "chatbot"],
                required_skills=["Python", "Claude API", "NLP"],
                week=4,
                assignee_role="developer",
                subtasks=[
                    "Design intent classification system",
                    "Extract entities from messages",
                    "Map intents to commands",
                    "Handle conversational context",
                    "Test with various phrasings",
                ],
            ),
            TaskTemplate(
                name="Implement conversational task queries",
                description="Handle queries like 'What tasks do I have this week?'",
                priority=TaskPriority.NORMAL,
                estimated_hours=6,
                tags=["ai", "chatbot"],
                required_skills=["Python", "Claude API"],
                dependencies=["Build chatbot NLU with Claude"],
                week=4,
                assignee_role="developer",
            ),
            TaskTemplate(
                name="Sync weekly goals from Google Docs",
                description="Read weekly goals from Google Docs and store in database",
                priority=TaskPriority.HIGH,
                estimated_hours=8,
                tags=["backend", "integration"],
                required_skills=["Python", "Google Docs API"],
                week=4,
                assignee_role="developer",
                subtasks=[
                    "Parse weekly goals doc format",
                    "Extract goals and deliverables",
                    "Store in database with member mapping",
                    "Set up periodic sync",
                ],
            ),
            TaskTemplate(
                name="Implement /weekly-goals command",
                description="Show team member's weekly goals in Slack",
                priority=TaskPriority.NORMAL,
                estimated_hours=5,
                tags=["slack", "chatbot"],
                required_skills=["Python", "Slack Bolt SDK"],
                dependencies=["Sync weekly goals from Google Docs"],
                week=4,
                assignee_role="developer",
            ),
            TaskTemplate(
                name="Build goal progress tracker",
                description="Track progress of tasks against weekly goals",
                priority=TaskPriority.NORMAL,
                estimated_hours=7,
                tags=["backend", "analytics"],
                required_skills=["Python"],
                dependencies=["Sync weekly goals from Google Docs"],
                week=4,
                assignee_role="developer",
            ),
        ],
    )

    # Phase 3: Reporting & Automation
    week5_reports = MilestoneTemplate(
        name="Week 5+: Reporting & Automation",
        description="Automated reports, team dashboard, and advanced features",
        phase=ProjectPhase.PHASE_3,
        estimated_duration_days=14,
        tasks=[
            TaskTemplate(
                name="Build daily standup report generator",
                description="Generate daily summaries with AI from task updates",
                priority=TaskPriority.HIGH,
                estimated_hours=10,
                tags=["ai", "reporting"],
                required_skills=["Python", "Claude API"],
                week=5,
                assignee_role="developer",
                subtasks=[
                    "Aggregate daily updates from database",
                    "Use Claude to summarize",
                    "Format as Google Doc",
                    "Send to Slack channel",
                    "Schedule daily automation",
                ],
            ),
            TaskTemplate(
                name="Build weekly progress report generator",
                description="Generate weekly team reports with insights",
                priority=TaskPriority.HIGH,
                estimated_hours=10,
                tags=["ai", "reporting"],
                required_skills=["Python", "Claude API"],
                dependencies=["Build daily standup report generator"],
                week=5,
                assignee_role="developer",
                subtasks=[
                    "Aggregate weekly data",
                    "Calculate team metrics",
                    "AI-generated insights",
                    "Save to Google Docs",
                    "Share in Slack",
                ],
            ),
            TaskTemplate(
                name="Create /team-status command",
                description="Show real-time team availability and workload",
                priority=TaskPriority.NORMAL,
                estimated_hours=8,
                tags=["slack", "chatbot"],
                required_skills=["Python", "Slack Bolt SDK"],
                week=5,
                assignee_role="developer",
                subtasks=[
                    "Query all team members",
                    "Calculate availability for each",
                    "Show workload distribution",
                    "Highlight overloaded members",
                    "Display in formatted table",
                ],
            ),
            TaskTemplate(
                name="Implement /availability command",
                description="Allow members to set/update their availability",
                priority=TaskPriority.NORMAL,
                estimated_hours=5,
                tags=["slack", "chatbot"],
                required_skills=["Python", "Slack Bolt SDK"],
                week=5,
                assignee_role="developer",
            ),
            TaskTemplate(
                name="Build task deadline reminder system",
                description="Automated reminders for upcoming task deadlines",
                priority=TaskPriority.NORMAL,
                estimated_hours=8,
                tags=["automation", "slack"],
                required_skills=["Python", "Slack Bolt SDK"],
                week=6,
                assignee_role="developer",
                subtasks=[
                    "Query tasks with upcoming due dates",
                    "Send reminders 1 day before",
                    "Send urgent reminders on due date",
                    "Schedule periodic checks",
                ],
            ),
            TaskTemplate(
                name="Create workload balancing alerts",
                description="Alert PMs when team members are overloaded",
                priority=TaskPriority.NORMAL,
                estimated_hours=6,
                tags=["automation", "analytics"],
                required_skills=["Python"],
                week=6,
                assignee_role="developer",
            ),
            TaskTemplate(
                name="Build team dashboard data API",
                description="Create API endpoints for dashboard metrics",
                priority=TaskPriority.NORMAL,
                estimated_hours=10,
                tags=["backend", "api"],
                required_skills=["FastAPI", "Python"],
                week=6,
                assignee_role="developer",
                subtasks=[
                    "Design dashboard metrics",
                    "Create FastAPI endpoints",
                    "Add caching for performance",
                    "Document API with OpenAPI",
                ],
            ),
        ],
    )

    # Create complete project template
    return ProjectTemplate(
        name="Team Onboarding & Management System",
        description="Complete system for team onboarding, task assignment, and visibility",
        milestones=[
            week1_foundation,
            week2_chatbot,
            week3_skill_matching,
            week4_nlu,
            week5_reports,
        ],
    )
