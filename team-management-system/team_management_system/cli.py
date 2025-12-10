"""CLI entry points for team management system."""

import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from team_management_system.models import create_team_onboarding_project_template
from team_management_system.services import (
    create_clickup_team_service,
    create_project_setup_service,
)

# Load environment variables from .env file
load_dotenv()


def setup_project():
    """
    CLI command to set up the Team Onboarding project in ClickUp.

    Usage:
        uv run setup-project
        uv run setup-project --preview
        uv run setup-project --start-date 2025-01-15
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Create Team Onboarding & Management System project in ClickUp"
    )
    parser.add_argument(
        "--list-id",
        help="ClickUp list ID (overrides env var)",
        default=None,
    )
    parser.add_argument(
        "--start-date",
        help="Project start date (YYYY-MM-DD)",
        default=None,
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Only show preview without creating tasks",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompt",
    )
    parser.add_argument(
        "--export",
        help="Export project summary to markdown file",
        default=None,
    )

    args = parser.parse_args()

    print("=" * 70)
    print("Team Onboarding & Management System - ClickUp Setup")
    print("=" * 70)

    # Load template
    print("\n📋 Loading project template...")
    template = create_team_onboarding_project_template()

    # Set start date
    if args.start_date:
        try:
            template.start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
        except ValueError:
            print(f"❌ Invalid date format: {args.start_date}")
            print("   Use format: YYYY-MM-DD")
            sys.exit(1)
    else:
        template.start_date = datetime.now()

    print(f"✅ Loaded: {template.name}")
    print(f"   Milestones: {len(template.milestones)}")
    print(f"   Total Tasks: {len(template.get_all_tasks())}")
    print(f"   Estimated Hours: {template.get_total_estimated_hours():.1f}")

    # Show preview
    print("\n📊 Project Overview:")
    for milestone in template.milestones:
        print(f"\n   📍 {milestone.name}")
        print(f"      Phase: {milestone.phase.value}")
        print(f"      Tasks: {len(milestone.tasks)}")
        print(f"      Duration: {milestone.estimated_duration_days} days")

    # Export summary if requested
    if args.export:
        try:
            setup_service = create_project_setup_service(None)
            summary = setup_service.get_project_summary(template)

            with open(args.export, "w") as f:
                f.write(summary)

            print(f"\n✅ Project summary exported to: {args.export}")
        except Exception as e:
            print(f"\n❌ Failed to export summary: {e}")

    # Exit if preview only
    if args.preview:
        print("\n👀 Preview mode - no tasks created")
        sys.exit(0)

    # Confirm
    if not args.yes:
        print("\n⚠️  This will create all tasks in ClickUp.")
        response = input("   Continue? (yes/no): ")
        if response.lower() not in ["yes", "y"]:
            print("\n❌ Cancelled")
            sys.exit(0)

    # Connect to ClickUp
    print("\n🔌 Connecting to ClickUp...")
    try:
        clickup_service = create_clickup_team_service()
        if args.list_id:
            clickup_service.list_id = args.list_id
        print(f"✅ Connected")
        print(f"   List ID: {clickup_service.list_id}")
    except ValueError as e:
        print(f"\n❌ Error: {e}")
        print("\nSet these environment variables:")
        print("  CLICKUP_API_TOKEN")
        print("  CLICKUP_WORKSPACE_ID")
        print("  CLICKUP_LIST_ID")
        sys.exit(1)

    # Create project
    print("\n🚀 Creating project in ClickUp...")
    setup_service = create_project_setup_service(clickup_service)

    try:
        result = setup_service.create_project_from_template(template, list_id=args.list_id)

        print("\n" + "=" * 70)
        print("🎉 SETUP COMPLETE!")
        print("=" * 70)
        print(f"\nCreated: {result['created']} tasks")
        if result["failed"] > 0:
            print(f"Failed: {result['failed']} tasks")
        print(f"\n🔗 View in ClickUp: https://app.clickup.com/")

        sys.exit(0 if result["failed"] == 0 else 1)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


def run_example():
    """
    Run the team management system examples.

    Usage:
        uv run team-example
    """
    print("=" * 70)
    print("Team Management System - Examples")
    print("=" * 70)
    print()
    print("Available examples:")
    print("  1. Create team members with skills")
    print("  2. Match skills to tasks")
    print("  3. Create task in ClickUp with auto-assignment")
    print("  4. Check user workload")
    print()

    choice = input("Select example (1-4) or 'all': ").strip()

    # Import the example functions
    from team_management_system.examples.clickup_team_example import (
        example_1_create_team_members,
        example_2_skill_matching,
        example_3_create_task_in_clickup,
        example_4_get_user_workload,
    )

    if choice == "all":
        team_members = example_1_create_team_members()
        example_2_skill_matching(team_members)
        example_3_create_task_in_clickup(team_members)
        example_4_get_user_workload()
    elif choice == "1":
        example_1_create_team_members()
    elif choice == "2":
        team_members = example_1_create_team_members()
        example_2_skill_matching(team_members)
    elif choice == "3":
        team_members = example_1_create_team_members()
        example_3_create_task_in_clickup(team_members)
    elif choice == "4":
        example_4_get_user_workload()
    else:
        print("Invalid choice")
        sys.exit(1)


if __name__ == "__main__":
    # Default to setup_project if run directly
    setup_project()
