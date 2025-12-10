"""Script to create the Team Onboarding & Management System project in ClickUp."""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from team_management_system.models.project_template import (
    create_team_onboarding_project_template,
)
from team_management_system.services.clickup_team_service import (
    create_clickup_team_service,
)
from team_management_system.services.project_setup_service import (
    create_project_setup_service,
)


def print_project_summary(template):
    """Print a preview of the project that will be created."""
    print("\n" + "=" * 70)
    print("PROJECT PREVIEW")
    print("=" * 70)
    print()
    print(f"Project: {template.name}")
    print(f"Description: {template.description}")
    print()
    print(f"Total Milestones: {len(template.milestones)}")
    print(f"Total Tasks: {len(template.get_all_tasks())}")
    print(f"Estimated Hours: {template.get_total_estimated_hours():.1f}")
    print()

    for milestone in template.milestones:
        print(f"\n📍 {milestone.name}")
        print(f"   Phase: {milestone.phase.value}")
        print(f"   Tasks: {len(milestone.tasks)}")
        print(f"   Duration: {milestone.estimated_duration_days} days")

        task_list = []
        for task in milestone.tasks[:3]:  # Show first 3 tasks
            task_list.append(f"      - {task.name} ({task.estimated_hours}h)")

        if task_list:
            print("   Sample tasks:")
            print("\n".join(task_list))

        if len(milestone.tasks) > 3:
            print(f"      ... and {len(milestone.tasks) - 3} more tasks")

    print("\n" + "=" * 70)


def confirm_creation():
    """Ask user to confirm project creation."""
    response = input("\n⚠️  This will create all tasks in ClickUp. Continue? (yes/no): ")
    return response.lower() in ["yes", "y"]


def main():
    """Main script to set up the project in ClickUp."""
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
        "--preview-only",
        action="store_true",
        help="Only show preview without creating tasks",
    )
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Skip confirmation prompt",
    )
    parser.add_argument(
        "--export-summary",
        help="Export project summary to markdown file",
        default=None,
    )

    args = parser.parse_args()

    print("=" * 70)
    print("Team Onboarding & Management System - ClickUp Setup")
    print("=" * 70)

    # Create project template
    print("\n📋 Loading project template...")
    template = create_team_onboarding_project_template()

    # Set start date
    if args.start_date:
        try:
            template.start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
        except ValueError:
            print(f"❌ Invalid date format: {args.start_date}")
            print("   Use format: YYYY-MM-DD")
            return 1
    else:
        template.start_date = datetime.now()

    print(f"✅ Project template loaded: {template.name}")

    # Show preview
    print_project_summary(template)

    # Export summary if requested
    if args.export_summary:
        try:
            setup_service = create_project_setup_service(
                None
            )  # Don't need ClickUp for summary
            summary = setup_service.get_project_summary(template)

            with open(args.export_summary, "w") as f:
                f.write(summary)

            print(f"\n✅ Project summary exported to: {args.export_summary}")
        except Exception as e:
            print(f"\n❌ Failed to export summary: {e}")

    # Exit if preview only
    if args.preview_only:
        print("\n👀 Preview mode - no tasks created")
        return 0

    # Confirm creation
    if not args.no_confirm and not confirm_creation():
        print("\n❌ Project creation cancelled")
        return 0

    # Initialize ClickUp service
    print("\n🔌 Connecting to ClickUp...")
    try:
        clickup_service = create_clickup_team_service()
        if args.list_id:
            clickup_service.list_id = args.list_id
        print(f"✅ Connected to ClickUp workspace")
        print(f"   List ID: {clickup_service.list_id}")
    except ValueError as e:
        print(f"\n❌ Failed to connect to ClickUp: {e}")
        print("\nMake sure you have set the following environment variables:")
        print("  - CLICKUP_API_TOKEN")
        print("  - CLICKUP_WORKSPACE_ID")
        print("  - CLICKUP_LIST_ID")
        return 1

    # Create project setup service
    setup_service = create_project_setup_service(clickup_service)

    # Create project in ClickUp
    print("\n🚀 Creating project in ClickUp...")
    try:
        result = setup_service.create_project_from_template(
            template,
            list_id=args.list_id,
        )

        # Print final summary
        print("\n" + "=" * 70)
        print("🎉 PROJECT SETUP COMPLETE!")
        print("=" * 70)
        print(f"\nCreated: {result['created']} tasks")
        print(f"Failed: {result['failed']} tasks")
        print(f"Start Date: {result['start_date'][:10]}")
        print()

        if result["failed"] == 0:
            print("✅ All tasks created successfully!")
            print(f"\n🔗 View your tasks in ClickUp: https://app.clickup.com/")
        else:
            print(
                f"⚠️  {result['failed']} tasks failed. Check the logs above for details."
            )

        print("\n" + "=" * 70)
        return 0

    except Exception as e:
        print(f"\n❌ Error creating project: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
