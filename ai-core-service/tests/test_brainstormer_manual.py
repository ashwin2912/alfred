"""Manual test script for ProjectBrainstormer.

Run this to verify the AI brainstorming service works correctly.

Usage:
    python -m tests.test_brainstormer_manual
"""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai.project_brainstormer import ProjectBrainstormer


def test_simple_analysis():
    """Test analyzing a simple project idea."""
    print("=" * 80)
    print("TEST 1: Simple Project Analysis")
    print("=" * 80)

    brainstormer = ProjectBrainstormer()

    project_idea = "Build a dashboard to monitor team task completion in ClickUp"

    print(f"\n📝 Project Idea: {project_idea}\n")

    analysis = brainstormer.analyze_project_idea(project_idea)

    print("\n✅ Analysis Complete!\n")
    print(json.dumps(analysis, indent=2))

    # Verify structure
    assert "title" in analysis, "Missing 'title' in analysis"
    assert "goals" in analysis, "Missing 'goals' in analysis"
    assert "scope" in analysis, "Missing 'scope' in analysis"
    assert "risks" in analysis, "Missing 'risks' in analysis"

    print("\n✅ All required fields present!")

    return analysis


def test_milestone_generation():
    """Test generating milestones from analysis."""
    print("\n" + "=" * 80)
    print("TEST 2: Milestone Generation")
    print("=" * 80)

    brainstormer = ProjectBrainstormer()

    # Simple analysis for testing
    project_analysis = {
        "title": "Task Completion Dashboard",
        "summary": "Build a real-time dashboard showing team task metrics",
        "goals": [
            "Visualize task completion rates",
            "Track team performance over time",
        ],
        "estimated_duration": "3 weeks",
    }

    print(f"\n📊 Generating milestones for: {project_analysis['title']}\n")

    milestones = brainstormer.generate_milestones(project_analysis)

    print(f"\n✅ Generated {len(milestones)} milestones:\n")

    for i, milestone in enumerate(milestones, 1):
        print(f"{i}. {milestone['name']}")
        print(f"   Duration: {milestone.get('duration', 'N/A')}")
        print(f"   Deliverables: {len(milestone.get('deliverables', []))}")
        print()

    assert len(milestones) >= 3, "Should generate at least 3 milestones"
    assert all("name" in m for m in milestones), "All milestones need names"

    print("✅ Milestone generation successful!")

    return milestones


def test_task_generation():
    """Test generating tasks for a milestone."""
    print("\n" + "=" * 80)
    print("TEST 3: Task Generation")
    print("=" * 80)

    brainstormer = ProjectBrainstormer()

    milestone = {
        "name": "Backend Development",
        "description": "Build API endpoints and database",
        "duration": "1 week",
    }

    project_context = {
        "title": "Task Dashboard",
        "technical_requirements": ["Python", "FastAPI", "PostgreSQL"],
    }

    print(f"\n📋 Generating tasks for: {milestone['name']}\n")

    tasks = brainstormer.generate_tasks_for_milestone(milestone, project_context)

    print(f"\n✅ Generated {len(tasks)} tasks:\n")

    for i, task in enumerate(tasks, 1):
        print(f"{i}. {task['name']}")
        print(f"   Hours: {task.get('estimated_hours', 'N/A')}")
        print(f"   Priority: {task.get('priority', 'N/A')}")
        print(f"   Skills: {', '.join(task.get('required_skills', []))}")
        print()

    assert len(tasks) >= 3, "Should generate at least 3 tasks"
    assert all("name" in t for t in tasks), "All tasks need names"
    assert all("required_skills" in t for t in tasks), "All tasks need skills"

    print("✅ Task generation successful!")

    return tasks


def test_complete_plan():
    """Test generating a complete project plan."""
    print("\n" + "=" * 80)
    print("TEST 4: Complete Project Plan")
    print("=" * 80)

    brainstormer = ProjectBrainstormer()

    project_idea = """
    Build a monitoring system that tracks GitHub activity and creates daily reports.
    It should analyze commits, pull requests, and issues, then send summaries to Slack.
    """

    print(f"\n📝 Project Idea: {project_idea.strip()}\n")

    plan = brainstormer.generate_complete_plan(project_idea)

    print("\n" + "=" * 80)
    print("COMPLETE PLAN GENERATED")
    print("=" * 80)

    print("\n📊 Project Analysis:")
    print(f"   Title: {plan['analysis']['title']}")
    print(f"   Duration: {plan['analysis']['estimated_duration']}")
    print(f"   Team: {plan['analysis']['team_size']}")

    print(f"\n🎯 Milestones: {len(plan['milestones'])}")
    for milestone in plan["milestones"]:
        print(f"   • {milestone['name']} ({len(milestone['tasks'])} tasks)")

    print(f"\n📈 Summary:")
    print(f"   Total Tasks: {plan['summary']['total_tasks']}")
    print(f"   Total Hours: {plan['summary']['total_estimated_hours']}")

    print(f"\n🔍 Refinement Assessment:")
    print(f"   {plan['refinement']['overall_assessment']}")

    if plan["refinement"].get("concerns"):
        print(f"\n⚠️  Concerns: {len(plan['refinement']['concerns'])}")
        for concern in plan["refinement"]["concerns"][:2]:
            print(f"   • {concern['issue']}")

    # Save to file for inspection
    output_file = Path(__file__).parent / "test_output_plan.json"
    with open(output_file, "w") as f:
        json.dump(plan, f, indent=2)

    print(f"\n💾 Full plan saved to: {output_file}")

    assert plan["summary"]["total_tasks"] > 0, "Should generate tasks"
    assert plan["summary"]["total_milestones"] > 0, "Should generate milestones"

    print("\n✅ Complete plan generation successful!")

    return plan


def main():
    """Run all tests."""
    print("\n🧪 TESTING PROJECT BRAINSTORMER")
    print("=" * 80)

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("\nSet it in your .env file or export it:")
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        sys.exit(1)

    print("✅ ANTHROPIC_API_KEY found")

    try:
        # Run tests
        test_simple_analysis()
        test_milestone_generation()
        test_task_generation()
        test_complete_plan()

        print("\n" + "=" * 80)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 80)
        print("\nThe AI brainstorming service is working correctly.")
        print("You can now integrate it with the Discord bot.")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
