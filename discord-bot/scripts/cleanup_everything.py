#!/usr/bin/env python3
"""
Cleanup script for Alfred Discord Bot.

This script helps you clean up before running interactive setup:
1. Delete Discord roles
2. Clear team folder references from database
3. Optionally list Google Drive folders to delete manually

Use this to start completely fresh.
"""

import asyncio
import os
import sys
from pathlib import Path

import discord
from discord.ext import commands

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


class CleanupBot(commands.Bot):
    """Temporary bot instance for cleanup."""

    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

        self.guild_id = int(os.getenv("DISCORD_GUILD_ID"))
        self.cleanup_complete = False
        self.team_service = TeamMemberService()

    async def on_ready(self):
        """Run cleanup when bot is ready."""
        print(f"\n🤖 Bot logged in as {self.user}")

        guild = self.get_guild(self.guild_id)
        if not guild:
            print(f"❌ Error: Could not find guild with ID {self.guild_id}")
            await self.close()
            return

        print(f"📍 Found guild: {guild.name}\n")

        try:
            await self.run_cleanup(guild)
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
            import traceback

            traceback.print_exc()
        finally:
            self.cleanup_complete = True
            await self.close()

    async def run_cleanup(self, guild):
        """Run the cleanup process."""

        print("=" * 70)
        print("⚠️  CLEANUP WIZARD")
        print("=" * 70)
        print()
        print("This will help you clean up before fresh setup.")
        print()

        # Step 1: Delete Discord roles
        print("=" * 70)
        print("STEP 1: Delete Discord Roles")
        print("=" * 70)
        print()

        # Get all teams from database
        teams = self.team_service.data_service.list_teams()
        team_names = [team.name for team in teams]

        print(f"Found {len(team_names)} teams in database:")
        for name in team_names:
            print(f"  • {name}")
        print()

        delete_roles = (
            input("Delete Discord roles for these teams? (yes/no): ").strip().lower()
        )

        if delete_roles == "yes":
            if not guild.me.guild_permissions.manage_roles:
                print("❌ Bot is missing 'Manage Roles' permission!")
            else:
                for team_name in team_names:
                    try:
                        role = discord.utils.get(guild.roles, name=team_name)
                        if role:
                            await role.delete(reason="Alfred cleanup")
                            print(f"  ✅ Deleted Discord role: {team_name}")
                        else:
                            print(f"  ⏭️  Role not found: {team_name}")
                    except Exception as e:
                        print(f"  ❌ Error deleting role '{team_name}': {e}")
        else:
            print("⏭️  Skipped Discord role deletion")

        # Step 2: Clear database references
        print("\n" + "=" * 70)
        print("STEP 2: Clear Database References")
        print("=" * 70)
        print()
        print("This will clear Google Drive folder/sheet IDs from teams table.")
        print("(Does NOT delete the actual files in Google Drive)")
        print()

        clear_db = input("Clear database references? (yes/no): ").strip().lower()

        if clear_db == "yes":
            for team in teams:
                try:
                    update = TeamUpdate(
                        drive_folder_id=None,
                        overview_doc_id=None,
                        overview_doc_url=None,
                        roster_sheet_id=None,
                        roster_sheet_url=None,
                        discord_role_id=None,
                    )
                    self.team_service.data_service.update_team(team.id, update)
                    print(f"  ✅ Cleared references for: {team.name}")
                except Exception as e:
                    print(f"  ❌ Error updating team '{team.name}': {e}")
        else:
            print("⏭️  Skipped database cleanup")

        # Step 3: Show Google Drive folders to delete
        print("\n" + "=" * 70)
        print("STEP 3: Google Drive Cleanup (Manual)")
        print("=" * 70)
        print()
        print("📁 Google Drive folders to delete manually:")
        print()
        print("Go to your Google Drive folder:")
        print(
            f"https://drive.google.com/drive/folders/{os.getenv('GOOGLE_DRIVE_FOLDER_ID')}"
        )
        print()
        print("Delete these folders:")
        print("  • Team Management")
        for team_name in team_names:
            print(f"  • {team_name}")
        print()
        print("(You can also delete individual docs/sheets if needed)")
        print()

        # Step 4: Optional - Delete teams from database
        print("=" * 70)
        print("STEP 4: Delete Teams from Database (Optional)")
        print("=" * 70)
        print()
        print("⚠️  WARNING: This will delete team records from database!")
        print("Only do this if you want to completely remove these teams.")
        print()

        delete_teams = input("Delete teams from database? (yes/no): ").strip().lower()

        if delete_teams == "yes":
            from supabase import create_client

            supabase = create_client(
                os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY")
            )

            for team_name in team_names:
                try:
                    supabase.table("teams").delete().eq("name", team_name).execute()
                    print(f"  ✅ Deleted team from database: {team_name}")
                except Exception as e:
                    print(f"  ❌ Error deleting team '{team_name}': {e}")
        else:
            print("⏭️  Skipped team deletion (teams kept in database)")

        # Summary
        print("\n" + "=" * 70)
        print("CLEANUP COMPLETE! 🎉")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Manually delete Google Drive folders (if not done)")
        print("  2. Run: python scripts/interactive_setup.py")
        print("  3. Configure your teams")
        print()


async def main():
    """Main cleanup function."""
    print("\n" + "=" * 70)
    print(" 🗑️  Alfred Bot - Cleanup Wizard")
    print("=" * 70)
    print()

    # Check environment variables
    required_vars = [
        "DISCORD_BOT_TOKEN",
        "DISCORD_GUILD_ID",
        "SUPABASE_URL",
        "SUPABASE_SERVICE_KEY",
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print("❌ Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        return 1

    print("⚠️  WARNING: This will help you clean up existing setup.")
    print()
    confirm = input("Continue with cleanup? (yes/no): ").strip().lower()

    if confirm != "yes":
        print("❌ Cleanup cancelled")
        return 1

    # Create and run bot
    bot = CleanupBot()

    try:
        await bot.start(os.getenv("DISCORD_BOT_TOKEN"))
    except KeyboardInterrupt:
        print("\n❌ Cleanup cancelled by user")
        await bot.close()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
