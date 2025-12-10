# Team Management System

ClickUp-based team management system with AI-powered skill matching, task assignment, and project setup automation.

## 🚀 Quick Start with UV

```bash
# Preview the project that will be created
uv run setup-project --preview

# Create all 32 tasks in ClickUp
uv run setup-project

# Run interactive examples
uv run team-example
```

## Features

### 1. **Project Setup Automation**
- 📋 Create complete project structures in ClickUp from templates
- ✅ 32 pre-built tasks for Team Onboarding & Management System
- 🏷️ Automatic tagging by phase, week, skills, and roles
- 📅 Auto-calculated due dates based on project timeline
- 📝 Detailed task descriptions with subtasks and dependencies

### 2. **Smart Team Management**
- 👥 Team member profiles with skills and availability
- 🎯 AI-powered skill matching for task assignment
- 📊 Workload tracking and availability calculation
- 🔍 Find team members by skills

### 3. **Task Assignment**
- 🤖 Smart assignment recommendations based on skills + availability
- ⚖️ Weighted scoring (60% skills, 40% availability)
- 📈 Top N candidate suggestions
- 🔄 Sync with ClickUp for real-time updates

## Installation

### Prerequisites
- Python 3.9+
- [UV](https://github.com/astral-sh/uv) package manager
- ClickUp account with API access

### Setup

1. **Install UV** (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Configure ClickUp credentials**:
```bash
cd team-management-system
cp .env.example .env
```

Edit `.env` with your credentials:
```bash
CLICKUP_API_TOKEN=pk_your_token_here
CLICKUP_WORKSPACE_ID=your_workspace_id
CLICKUP_LIST_ID=your_default_list_id
```

**Finding your credentials:**
- **API Token**: ClickUp Settings → Apps → Generate API Token
- **Workspace ID**: ClickUp Settings → Workspace → Check URL
- **List ID**: Open any list in ClickUp → Copy ID from URL

## Usage

### Create Project in ClickUp

The main feature - create a complete project structure with all tasks:

```bash
# Preview what will be created (32 tasks across 5 milestones)
uv run setup-project --preview

# Create the project with confirmation prompt
uv run setup-project

# Create without confirmation (for automation)
uv run setup-project --yes

# Set custom start date
uv run setup-project --start-date 2025-01-15

# Export project plan to markdown
uv run setup-project --export my_project_plan.md --preview

# Use specific ClickUp list
uv run setup-project --list-id 123456789
```

**What gets created:**
- **Phase 1: MVP** (15 tasks, Weeks 1-2)
  - Database setup, onboarding form, Google Docs, Slack bot
- **Phase 2: Intelligence** (10 tasks, Weeks 3-4)
  - AI skill parsing, smart assignment, NLU chatbot
- **Phase 3: Reporting** (7 tasks, Week 5+)
  - Automated reports, team dashboard, alerts

### Team Management Examples

```bash
# Run interactive examples
uv run team-example

# Options:
# 1. Create team members with skills
# 2. Match skills to tasks
# 3. Create task in ClickUp with auto-assignment
# 4. Check user workload
```

### Programmatic Usage

```python
from team_management_system.models import (
    TeamMember,
    Skill,
    ExperienceLevel,
    TeamMemberRole,
    TaskRequirement,
)
from team_management_system.services import create_clickup_team_service

# Create team member
alice = TeamMember(
    name="Alice Smith",
    email="alice@example.com",
    role=TeamMemberRole.DEVELOPER,
    skills=[
        Skill(name="Python", experience_level=ExperienceLevel.EXPERT),
        Skill(name="FastAPI", experience_level=ExperienceLevel.ADVANCED),
    ],
    hours_per_week=40,
)

# Create task requirement
task = TaskRequirement(
    task_name="Build REST API",
    task_description="Create user authentication API",
    required_skills=["Python", "FastAPI"],
    estimated_hours=20,
    priority="high",
)

# Get skill match score
score = alice.get_skill_score(task.required_skills)
print(f"Alice matches this task at {score}%")

# Create in ClickUp with auto-assignment
service = create_clickup_team_service()
result = service.create_and_assign_task(
    requirement=task,
    team_members=[alice],
    auto_assign=True
)
print(f"Task assigned to: {result['assigned_to']}")
```

## Project Structure

```
team-management-system/
├── team_management_system/
│   ├── models/
│   │   ├── team_member.py          # Team member, skill models
│   │   └── project_template.py     # Project template models
│   ├── services/
│   │   ├── clickup_team_service.py # ClickUp integration
│   │   └── project_setup_service.py # Project setup automation
│   ├── examples/
│   │   ├── clickup_team_example.py # Usage examples
│   │   └── setup_project_example.py # Simple setup script
│   ├── scripts/
│   │   └── setup_project_in_clickup.py # Advanced CLI
│   └── cli.py                       # UV command entry points
├── pyproject.toml                   # UV project config
├── QUICKSTART.md                    # UV quick start guide
├── PROJECT_SETUP_GUIDE.md          # Detailed setup guide
└── README.md                        # This file
```

## Architecture

### Models

**TeamMember**
- Name, email, role, timezone
- Skills with experience levels
- Availability (hours/week)
- Current workload tracking
- Methods: `has_skill()`, `get_skill_score()`, `get_availability_hours()`

**Skill**
- Skill name
- Experience level (beginner, intermediate, advanced, expert)
- Years of experience

**TaskRequirement**
- Task details (name, description, priority)
- Required skills
- Estimated hours
- Due date

**ProjectTemplate**
- Complete project structure
- Milestones with tasks
- Phase organization
- Auto-calculated estimates

### Services

**ClickUpTeamService**
- Create/assign tasks
- Calculate workload
- Find users by email
- Smart assignment recommendations
- Task status updates

**ProjectSetupService**
- Create projects from templates
- Batch task creation
- Dependency tracking
- Progress reporting

## How Skill Matching Works

The system uses a weighted scoring algorithm:

1. **Skill Score (60%)**: Match required skills with member's skills
   - Expert: 100% contribution
   - Advanced: 75% contribution
   - Intermediate: 50% contribution
   - Beginner: 25% contribution

2. **Availability Score (40%)**: Based on available hours
   - Full availability: 100%
   - Partial: Proportional score
   - None: 0%

3. **Overall Score**: `(skill_score × 0.6) + (availability_score × 0.4)`

**Example:**
```python
# Alice has Python (expert) and FastAPI (advanced)
# Task requires: Python, FastAPI, API
# Skill match: (100% + 75% + 0%) / 3 = 58.3%
# Available: 40 of 20 needed hours = 100%
# Overall: (58.3 × 0.6) + (100 × 0.4) = 75%
```

## Task Structure in ClickUp

Each created task includes:

- ✅ **Name**: Clear, descriptive title
- ✅ **Description**: Full requirements with subtasks
- ✅ **Required Skills**: Tagged (e.g., `skill:Python`)
- ✅ **Estimated Hours**: Time estimate
- ✅ **Priority**: High, Normal, or Low
- ✅ **Due Date**: Auto-calculated from week number
- ✅ **Tags**: Phase, week, role, skills
- ✅ **Subtasks**: Detailed checklist
- ✅ **Dependencies**: Noted in comments
- ✅ **Assignee Role**: Suggested role

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `CLICKUP_API_TOKEN` | ClickUp API token | Yes |
| `CLICKUP_WORKSPACE_ID` | Workspace/team ID | Yes |
| `CLICKUP_LIST_ID` | Default list ID | Yes |

## Creating Custom Templates

```python
from team_management_system.models import (
    ProjectTemplate,
    MilestoneTemplate,
    TaskTemplate,
    TaskPriority,
    ProjectPhase,
)

# Define tasks
task = TaskTemplate(
    name="Setup backend API",
    description="Create FastAPI backend",
    priority=TaskPriority.HIGH,
    estimated_hours=20,
    required_skills=["Python", "FastAPI"],
    tags=["backend"],
    week=1,
    subtasks=[
        "Set up FastAPI project",
        "Create authentication endpoints",
        "Add database models",
    ],
)

# Create milestone
milestone = MilestoneTemplate(
    name="Backend Setup",
    description="Initial backend infrastructure",
    phase=ProjectPhase.PHASE_1,
    tasks=[task],
    estimated_duration_days=7,
)

# Create project
project = ProjectTemplate(
    name="My Project",
    description="Custom project",
    milestones=[milestone],
)

# Deploy to ClickUp
from team_management_system.services import (
    create_clickup_team_service,
    create_project_setup_service,
)

clickup_service = create_clickup_team_service()
setup_service = create_project_setup_service(clickup_service)
result = setup_service.create_project_from_template(project)
```

## Integration with Main Agent (Future)

This system is designed to be used by the main Alfred agent:

1. **Agent receives project requirements** from user
2. **Generates or loads project template** based on requirements
3. **Calls `setup_service.create_project_from_template()`**
4. **All tasks created** with proper structure and metadata
5. **Team members auto-assigned** based on skill matching
6. **Project ready to execute** immediately

## Next Steps

This is Phase 1 of the full Team Onboarding & Management System. See the complete roadmap in [`TEAM_ONBOARDING_SYSTEM.md`](../TEAM_ONBOARDING_SYSTEM.md).

**Next phases:**
1. **Database Layer**: Persistent storage with SQLite/PostgreSQL
2. **Onboarding Service**: Web form for team member signup
3. **Google Docs Integration**: Auto-generate profiles and reports
4. **Chatbot Interface**: Slack/Discord bot for task management
5. **Progress Tracking**: Automated reporting and analytics

## Troubleshooting

### "CLICKUP_API_TOKEN not provided"
Create a `.env` file with your ClickUp credentials.

### "ClickUp API error: 401"
Your API token is invalid or expired. Generate a new one.

### "ClickUp API error: 404"
Check that your workspace ID and list ID are correct.

### Tasks not appearing
- Verify your list ID is correct
- Check API token has write permissions
- Review console output for specific errors

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - UV quick start guide
- **[PROJECT_SETUP_GUIDE.md](PROJECT_SETUP_GUIDE.md)** - Detailed setup documentation
- **[TEAM_ONBOARDING_SYSTEM.md](../TEAM_ONBOARDING_SYSTEM.md)** - Full architecture plan

## License

Part of the Alfred project - Digital butler for distributed teams.

## Contributing

This is part of the Alfred ecosystem. See the main repository for contribution guidelines.
