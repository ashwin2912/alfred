#!/usr/bin/env python3
"""
Initialize Google Drive folder structure for teams.

This script:
1. Creates Team Management folder for all member profiles
2. Creates folder structure for each team in the database
3. Updates team records with Drive folder/sheet IDs

Run this once to set up the folder structure for existing teams.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Add shared-services to path
shared_services_path = parent_dir.parent / "shared-services"
sys.path.insert(0, str(shared_services_path))
sys.path.insert(0, str(shared_services_path / "data-service"))
sys.path.insert(0, str(shared_services_path / "docs-service"))

from data_service.models import TeamUpdate
from dotenv import load_dotenv

from bot.services import DocsService, TeamMemberService

# Load environment variables
load_dotenv()


def main():
    """Initialize team folder structure."""
    print("🚀 Starting team folder initialization...\n")

    # Initialize services
    docs_service = DocsService()
    team_service = TeamMemberService()

    if not docs_service.is_available():
        print("❌ Error: Google Docs service is not available")
        print("Please check your GOOGLE_CREDENTIALS_PATH environment variable")
        return 1

    # Create Team Management folder
    print("📁 Creating Team Management folder...")
    team_mgmt_folder = docs_service.get_team_management_folder()
    if team_mgmt_folder:
        print(f"✅ Team Management folder created: {team_mgmt_folder}\n")
    else:
        print("❌ Failed to create Team Management folder\n")
        return 1

    # Get all teams from database
    print("📋 Fetching teams from database...")
    try:
        teams = team_service.data_service.list_teams()
        print(f"Found {len(teams)} teams\n")
    except Exception as e:
        print(f"❌ Error fetching teams: {e}")
        return 1

    # Initialize folder structure for each team
    for team in teams:
        print(f"🔧 Processing team: {team.name}")

        # Skip if team already has folder structure
        if team.roster_sheet_id:
            print(
                f"  ⏭️  Team already has folder structure (roster: {team.roster_sheet_id})"
            )
            continue

        try:
            # Create team folder structure
            print(f"  📁 Creating folder structure...")
            result = docs_service.create_team_folder_structure(team.name)

            if result:
                print(f"  ✅ Created folder: {result['folder_id']}")
                print(f"  ✅ Created overview doc: {result['overview_doc_url']}")
                print(f"  ✅ Created roster sheet: {result['roster_sheet_url']}")

                # Update team record in database
                update = TeamUpdate(
                    drive_folder_id=result["folder_id"],
                    overview_doc_id=result["overview_doc_id"],
                    overview_doc_url=result["overview_doc_url"],
                    roster_sheet_id=result["roster_sheet_id"],
                    roster_sheet_url=result["roster_sheet_url"],
                )

                team_service.data_service.update_team(team.id, update)
                print(f"  ✅ Updated team record in database\n")
            else:
                print(f"  ❌ Failed to create folder structure\n")
        except Exception as e:
            print(f"  ❌ Error: {e}\n")

    print("🎉 Team folder initialization complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
