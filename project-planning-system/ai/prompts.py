"""Prompts for AI project planning."""


def get_simple_project_breakdown_prompt(project_idea: str) -> str:
    """
    Simple prompt for project breakdown.

    Returns plain text breakdown that can be directly pasted in Google Docs.
    """
    return f"""You are an expert project manager. A team lead has come to you with a project idea and needs help breaking it down into actionable tasks.

Project Idea:
{project_idea}

Please provide:
1. A brief project overview (2-3 sentences)
2. Key milestones/phases
3. Specific tasks for each phase
4. Suggested team members or skills needed

{{
    "title": "Clear project title (5-8 words)",
    "overview": "Brief project overview explaining what will be built and why (2-3 sentences)",
    "objectives": [
        "Primary objective 1",
        "Primary objective 2",
        "Primary objective 3"
    ],
    "phases": [
        {{
            "name": "Phase 1: Planning & Design",
            "description": "Brief description of what happens in this phase",
            "estimated_duration": "1 week",
            "subtasks": [
                {{
                    "name": "Define project requirements",
                    "description": "Gather and document detailed requirements",
                    "estimated_hours": 4,
                    "required_skills": ["Product Management", "Technical Writing"]
                }},
                {{
                    "name": "Create system architecture diagram",
                    "description": "Design high-level system architecture",
                    "estimated_hours": 6,
                    "required_skills": ["System Design", "Architecture"]
                }}
            ]
        }},
        {{
            "name": "Phase 2: Development",
            "description": "Build core features",
            "estimated_duration": "2-3 weeks",
            "subtasks": [
                {{
                    "name": "Setup development environment",
                    "description": "Initialize repository, configure tools",
                    "estimated_hours": 3,
                    "required_skills": ["DevOps", "Git"]
                }}
            ]
        }}
    ],
    "team_suggestions": [
        {{
            "role": "Backend Developer",
            "skills": ["Python", "API Development"],
            "time_commitment": "Full-time for 3 weeks"
        }},
        {{
            "role": "Frontend Developer",
            "skills": ["React", "UI/UX"],
            "time_commitment": "Full-time for 2 weeks"
        }}
    ],
    "success_criteria": [
        "Measurable success criterion 1",
        "Measurable success criterion 2"
    ]
}}

IMPORTANT Guidelines:
- Create 3-5 phases maximum (keep it high-level)
- Each phase should have 3-8 subtasks
- Each subtask: 2-12 hours (not too granular)
- Be specific but concise
- Focus on structure the team lead can easily review and modify

Example Structure to Follow:

{{
    "title": "Team Task Dashboard",
    "overview": "Build a real-time dashboard that displays task completion metrics for all teams. This will help managers track progress and identify bottlenecks quickly.",
    "objectives": [
        "Provide real-time visibility into team task status",
        "Enable filtering by team, project, and time period",
        "Generate weekly progress reports automatically"
    ],
    "phases": [
        {{
            "name": "Phase 1: Planning & Setup",
            "description": "Define requirements and setup project infrastructure",
            "estimated_duration": "3-4 days",
            "subtasks": [
                {{
                    "name": "Gather dashboard requirements",
                    "description": "Interview team leads to understand needed metrics and features",
                    "estimated_hours": 4,
                    "required_skills": ["Product Management", "Requirements Analysis"]
                }},
                {{
                    "name": "Design data model",
                    "description": "Define database schema for task tracking and aggregations",
                    "estimated_hours": 6,
                    "required_skills": ["Database Design", "SQL"]
                }},
                {{
                    "name": "Create UI wireframes",
                    "description": "Design dashboard layout and key components",
                    "estimated_hours": 5,
                    "required_skills": ["UI/UX Design", "Figma"]
                }}
            ]
        }},
        {{
            "name": "Phase 2: Backend Development",
            "description": "Build API and data processing logic",
            "estimated_duration": "1 week",
            "subtasks": [
                {{
                    "name": "Implement ClickUp API integration",
                    "description": "Fetch tasks and track status changes via ClickUp webhooks",
                    "estimated_hours": 8,
                    "required_skills": ["Python", "REST APIs", "ClickUp API"]
                }},
                {{
                    "name": "Build aggregation endpoints",
                    "description": "Create API endpoints for task metrics and statistics",
                    "estimated_hours": 10,
                    "required_skills": ["Python", "FastAPI", "SQL"]
                }}
            ]
        }},
        {{
            "name": "Phase 3: Frontend Development",
            "description": "Build dashboard UI components",
            "estimated_duration": "1 week",
            "subtasks": [
                {{
                    "name": "Setup React project",
                    "description": "Initialize React app with routing and state management",
                    "estimated_hours": 4,
                    "required_skills": ["React", "TypeScript"]
                }},
                {{
                    "name": "Build task metrics components",
                    "description": "Create charts and tables for displaying task data",
                    "estimated_hours": 12,
                    "required_skills": ["React", "Chart.js", "CSS"]
                }}
            ]
        }},
        {{
            "name": "Phase 4: Testing & Deployment",
            "description": "Test functionality and deploy to production",
            "estimated_duration": "3-4 days",
            "subtasks": [
                {{
                    "name": "Write integration tests",
                    "description": "Test API endpoints and data flows",
                    "estimated_hours": 6,
                    "required_skills": ["Python", "Pytest", "Testing"]
                }},
                {{
                    "name": "Deploy to production",
                    "description": "Setup hosting, CI/CD, and monitoring",
                    "estimated_hours": 5,
                    "required_skills": ["DevOps", "Docker", "GCP/AWS"]
                }}
            ]
        }}
    ],
    "team_suggestions": [
        {{
            "role": "Full-Stack Developer",
            "skills": ["Python", "React", "API Development"],
            "time_commitment": "Full-time for 2-3 weeks"
        }},
        {{
            "role": "UI/UX Designer",
            "skills": ["Figma", "Dashboard Design", "Data Visualization"],
            "time_commitment": "Part-time (10-15 hours total)"
        }}
    ],
    "success_criteria": [
        "Dashboard loads task data within 2 seconds",
        "Shows real-time updates when tasks are completed",
        "Generates accurate weekly reports for all teams",
        "Positive feedback from at least 3 team leads"
    ]
}}"""


def get_project_analysis_prompt(project_idea: str) -> str:
    """
    Generate prompt for analyzing a raw project idea.

    Returns structured analysis with goals, scope, risks, and requirements.
    """
    return f"""You are an expert project manager and software architect. Analyze the following project idea and provide a comprehensive breakdown.

Project Idea:
{project_idea}

Provide your analysis in the following JSON format:
{{
    "title": "Clear, concise project title (5-8 words)",
    "summary": "2-3 sentence executive summary of the project",
    "goals": [
        "Specific, measurable goal 1",
        "Specific, measurable goal 2",
        "..."
    ],
    "scope": {{
        "in_scope": [
            "Feature or requirement that IS part of this project",
            "..."
        ],
        "out_of_scope": [
            "Feature or requirement that is NOT part of this project",
            "..."
        ]
    }},
    "target_users": "Who will use this? Be specific.",
    "success_metrics": [
        "How will we measure success? (e.g., 'API response time < 200ms')",
        "..."
    ],
    "technical_requirements": [
        "Technology or skill needed (e.g., 'Python backend', 'React frontend')",
        "..."
    ],
    "risks": [
        {{
            "risk": "Description of potential risk",
            "severity": "high|medium|low",
            "mitigation": "How to address this risk"
        }}
    ],
    "estimated_duration": "Realistic timeline (e.g., '3-4 weeks', '2 months')",
    "team_size": "Recommended team size (e.g., '2-3 developers, 1 designer')"
}}

Be specific and actionable. If the project idea is vague, make reasonable assumptions and note them."""


def get_milestone_generation_prompt(project_analysis: dict) -> str:
    """
    Generate prompt for creating project milestones.

    Takes the project analysis and generates logical milestones.
    """
    return f"""You are an expert project manager. Based on the project analysis below, create a detailed milestone breakdown.

Project Analysis:
{project_analysis}

Generate 3-6 milestones that logically break down this project. Each milestone should represent a significant deliverable or phase.

Provide your response in the following JSON format:
{{
    "milestones": [
        {{
            "name": "Milestone name (e.g., 'Design & Planning Phase')",
            "description": "What will be accomplished in this milestone",
            "duration": "Estimated duration (e.g., '1 week', '5 days')",
            "order": 1,
            "deliverables": [
                "Concrete deliverable 1",
                "Concrete deliverable 2"
            ],
            "dependencies": [
                "Which previous milestones must be complete? (empty array if none)"
            ]
        }}
    ]
}}

Guidelines:
- Start with discovery/planning milestones
- Include design phase if needed
- Break development into logical chunks
- Include testing and deployment milestones
- Make dependencies clear
- Be realistic with durations"""


def get_task_generation_prompt(milestone: dict, project_context: dict) -> str:
    """
    Generate prompt for creating tasks within a milestone.

    Takes a milestone and project context to generate specific tasks.
    """
    return f"""You are an expert project manager. Generate specific, actionable tasks for the following milestone.

Project Context:
{project_context}

Milestone:
{milestone}

Create 4-8 concrete tasks for this milestone. Each task should be:
- Specific and actionable
- Completable by one person
- Have clear success criteria
- Include estimated hours

Provide your response in the following JSON format:
{{
    "tasks": [
        {{
            "name": "Specific task name (e.g., 'Design database schema for user authentication')",
            "description": "Detailed description of what needs to be done and acceptance criteria",
            "estimated_hours": 8,
            "priority": "high|medium|low",
            "required_skills": [
                "Primary skill needed (e.g., 'Python', 'React', 'UI/UX Design')",
                "Secondary skill if needed"
            ],
            "dependencies": [
                "Task names that must be completed first (empty array if none)"
            ],
            "deliverable": "What will be produced? (e.g., 'SQL migration file', 'Figma mockup')"
        }}
    ]
}}

Guidelines:
- Tasks should be 2-16 hours each (break down if larger)
- Be specific about deliverables
- Include all necessary skills
- Consider realistic dependencies
- Mix priorities based on criticality"""


def get_project_refinement_prompt(
    project_analysis: dict, milestones: list, all_tasks: list
) -> str:
    """
    Generate prompt for refining and validating the complete project plan.

    Reviews the entire plan and suggests improvements.
    """
    return f"""You are an expert project manager reviewing a complete project plan. Analyze for:
- Logical flow and dependencies
- Resource allocation and team capacity
- Risk coverage
- Missing critical tasks
- Unrealistic estimates

Project Analysis:
{project_analysis}

Milestones:
{milestones}

All Tasks:
{all_tasks}

Provide your review in the following JSON format:
{{
    "overall_assessment": "Brief assessment of the plan's quality and feasibility",
    "strengths": [
        "What's good about this plan"
    ],
    "concerns": [
        {{
            "issue": "Description of the concern",
            "severity": "high|medium|low",
            "recommendation": "How to address it"
        }}
    ],
    "missing_items": [
        "Important tasks or milestones that are missing"
    ],
    "timeline_assessment": "Is the timeline realistic? Too aggressive? Too conservative?",
    "resource_assessment": "Does the team size match the workload?",
    "suggestions": [
        "Specific improvement suggestions"
    ]
}}

Be honest and constructive. This review will help improve the plan before execution."""
