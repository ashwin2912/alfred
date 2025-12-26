"""AI-powered project brainstorming and planning service."""

import json
import os
from typing import Any, Dict, List, Optional

from anthropic import Anthropic
from dotenv import load_dotenv

from .prompts import (
    get_milestone_generation_prompt,
    get_project_analysis_prompt,
    get_project_refinement_prompt,
    get_simple_project_breakdown_prompt,
    get_task_generation_prompt,
)

load_dotenv()


class ProjectBrainstormer:
    """
    AI-powered project brainstorming service using Claude.

    Generates comprehensive project plans from high-level ideas:
    1. Analyzes project idea (goals, scope, risks)
    2. Generates logical milestones
    3. Creates specific tasks for each milestone
    4. Refines and validates the complete plan
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the brainstormer with Anthropic API.

        Args:
            api_key: Anthropic API key (uses ANTHROPIC_API_KEY env var if not provided)
        """
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable or api_key parameter required"
            )

        self.client = Anthropic(api_key=api_key)
        # Use Claude Haiku 4.5 - cheapest and fastest option
        self.model = "claude-haiku-4-5-20251001"

    def generate_simple_breakdown(self, project_idea: str) -> Dict[str, Any]:
        """
        Generate a simple, high-level breakdown of a project idea.

        This method creates a structured project plan that's easy for team leads
        to review and modify. Returns JSON that will be formatted into a Google Doc.

        Args:
            project_idea: Free-form description of the project

        Returns:
            Dict containing:
                - title: Project title
                - overview: Brief project overview (2-3 sentences)
                - objectives: List of primary objectives
                - phases: List of project phases, each containing:
                    * name: Phase name
                    * description: What happens in this phase
                    * estimated_duration: Time estimate
                    * subtasks: List of subtasks with name, description, hours, skills
                - team_suggestions: Recommended roles and skills
                - success_criteria: List of measurable success criteria

        Example:
            >>> brainstormer = ProjectBrainstormer()
            >>> breakdown = brainstormer.generate_simple_breakdown(
            ...     "Build a dashboard to monitor team task completion"
            ... )
            >>> print(breakdown['title'])
            'Team Task Dashboard'
            >>> print(f"{len(breakdown['phases'])} phases")
            4 phases
        """
        prompt = get_simple_project_breakdown_prompt(project_idea)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}],
        )

        # Extract and return structured JSON
        content = response.content[0].text
        breakdown = self._extract_json(content)

        return breakdown

    def analyze_project_idea(self, project_idea: str) -> Dict[str, Any]:
        """
        Analyze a raw project idea and extract structured information.

        Args:
            project_idea: Free-form description of the project

        Returns:
            Dict containing:
                - title: Project title
                - summary: Executive summary
                - goals: List of project goals
                - scope: Dict with in_scope and out_of_scope items
                - target_users: Target audience
                - success_metrics: How to measure success
                - technical_requirements: Required technologies/skills
                - risks: List of potential risks with mitigation
                - estimated_duration: Timeline estimate
                - team_size: Recommended team composition

        Example:
            >>> brainstormer = ProjectBrainstormer()
            >>> analysis = brainstormer.analyze_project_idea(
            ...     "Build a dashboard to monitor team task completion"
            ... )
            >>> print(analysis['title'])
            'Team Task Completion Dashboard'
        """
        prompt = get_project_analysis_prompt(project_idea)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}],
        )

        # Extract JSON from response
        content = response.content[0].text
        analysis = self._extract_json(content)

        return analysis

    def generate_milestones(
        self, project_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate project milestones based on project analysis.

        Args:
            project_analysis: Output from analyze_project_idea()

        Returns:
            List of milestone dicts, each containing:
                - name: Milestone name
                - description: What will be accomplished
                - duration: Estimated duration
                - order: Sequence number
                - deliverables: List of concrete deliverables
                - dependencies: List of prerequisite milestones

        Example:
            >>> milestones = brainstormer.generate_milestones(analysis)
            >>> print(milestones[0]['name'])
            'Design & Planning Phase'
        """
        prompt = get_milestone_generation_prompt(project_analysis)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.content[0].text
        result = self._extract_json(content)

        return result.get("milestones", [])

    def generate_tasks_for_milestone(
        self, milestone: Dict[str, Any], project_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate specific tasks for a milestone.

        Args:
            milestone: Milestone dict from generate_milestones()
            project_context: Original project analysis for context

        Returns:
            List of task dicts, each containing:
                - name: Task name
                - description: Detailed description
                - estimated_hours: Time estimate
                - priority: high/medium/low
                - required_skills: List of required skills
                - dependencies: List of prerequisite tasks
                - deliverable: Expected output

        Example:
            >>> tasks = brainstormer.generate_tasks_for_milestone(
            ...     milestones[0], analysis
            ... )
            >>> print(tasks[0]['name'])
            'Create database schema for user profiles'
        """
        prompt = get_task_generation_prompt(milestone, project_context)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.content[0].text
        result = self._extract_json(content)

        return result.get("tasks", [])

    def generate_complete_plan(self, project_idea: str) -> Dict[str, Any]:
        """
        Generate a complete project plan from a raw idea.

        This is the main entry point that orchestrates the entire planning process:
        1. Analyze the project idea
        2. Generate milestones
        3. Generate tasks for each milestone
        4. Refine and validate the plan

        Args:
            project_idea: Free-form description of the project

        Returns:
            Complete project plan dict containing:
                - analysis: Project analysis (goals, scope, risks, etc.)
                - milestones: List of milestones with tasks
                - refinement: Quality review and suggestions
                - summary: Quick stats (total tasks, duration, team size)

        Example:
            >>> plan = brainstormer.generate_complete_plan(
            ...     "Build an API to sync data between ClickUp and Slack"
            ... )
            >>> print(f"Generated {plan['summary']['total_tasks']} tasks")
            Generated 24 tasks
        """
        print("🧠 Analyzing project idea...")
        analysis = self.analyze_project_idea(project_idea)

        print(f"✅ Project: {analysis.get('title', 'Untitled')}")
        print(f"📊 Estimated duration: {analysis.get('estimated_duration', 'Unknown')}")

        print("\n🎯 Generating milestones...")
        milestones = self.generate_milestones(analysis)
        print(f"✅ Created {len(milestones)} milestones")

        print("\n📋 Generating tasks for each milestone...")
        all_tasks = []
        for i, milestone in enumerate(milestones, 1):
            print(f"  {i}. {milestone['name']}...")
            tasks = self.generate_tasks_for_milestone(milestone, analysis)
            milestone["tasks"] = tasks
            all_tasks.extend(tasks)
            print(f"     ✅ {len(tasks)} tasks")

        print(f"\n✅ Total tasks generated: {len(all_tasks)}")

        print("\n🔍 Refining plan...")
        refinement = self.refine_plan(analysis, milestones, all_tasks)

        # Calculate summary stats
        total_hours = sum(task.get("estimated_hours", 0) for task in all_tasks)

        summary = {
            "total_milestones": len(milestones),
            "total_tasks": len(all_tasks),
            "total_estimated_hours": total_hours,
            "estimated_duration": analysis.get("estimated_duration"),
            "team_size": analysis.get("team_size"),
        }

        print(f"\n📦 Plan Summary:")
        print(f"   - {summary['total_milestones']} milestones")
        print(f"   - {summary['total_tasks']} tasks")
        print(f"   - {summary['total_estimated_hours']} estimated hours")
        print(f"   - Duration: {summary['estimated_duration']}")
        print(f"   - Team: {summary['team_size']}")

        return {
            "analysis": analysis,
            "milestones": milestones,
            "refinement": refinement,
            "summary": summary,
        }

    def refine_plan(
        self,
        analysis: Dict[str, Any],
        milestones: List[Dict[str, Any]],
        all_tasks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Review and refine the complete project plan.

        Args:
            analysis: Project analysis
            milestones: Generated milestones
            all_tasks: All generated tasks

        Returns:
            Refinement dict containing:
                - overall_assessment: Quality assessment
                - strengths: What's good about the plan
                - concerns: Issues and recommendations
                - missing_items: What might be missing
                - timeline_assessment: Is timeline realistic?
                - resource_assessment: Does team size match workload?
                - suggestions: Specific improvements
        """
        prompt = get_project_refinement_prompt(analysis, milestones, all_tasks)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=0.5,  # Lower temperature for more consistent review
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.content[0].text
        refinement = self._extract_json(content)

        return refinement

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        Extract JSON from Claude's response.

        Claude sometimes wraps JSON in markdown code blocks, so we handle that.
        """
        # Try to find JSON in markdown code block
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            json_str = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            json_str = text[start:end].strip()
        else:
            json_str = text.strip()

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse JSON from Claude response: {e}\n\nResponse: {text}"
            )
