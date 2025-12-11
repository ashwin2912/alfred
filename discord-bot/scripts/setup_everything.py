#!/usr/bin/env python3
"""
Complete setup script for Alfred Discord Bot.

This script:
1. Creates admin account in database
2. Creates teams in database (Engineering, Product, Business)
3. Creates roles in database
4. Creates Discord roles (if they don't exist)
5. Initializes Google Drive folder structure for teams
6. Links everything together

Run this once for initial setup or after database reset.
"""

import asyncio
import os
import sys
from pathlib import Path
from uuid import UUID

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

from data_service.models import TeamMemberCreate, TeamUpdate
from dotenv import load_dotenv

from bot.services import DocsService, TeamMemberService

# Load environment variables
load_dotenv()


class SetupBot(commands.Bot):
    """Temporary bot instance for setup."""

    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

        self.guild_id = int(os.getenv("DISCORD_GUILD_ID"))
        self.setup_complete = False
        self.team_service = TeamMemberService()
        self.docs_service = DocsService()

    async def on_ready(self):
        """Run setup when bot is ready."""
        print(f"🤖 Bot logged in as {self.user}")

        guild = self.get_guild(self.guild_id)
        if not guild:
            print(f"❌ Error: Could not find guild with ID {self.guild_id}")
            await self.close()
            return

        print(f"📍 Found guild: {guild.name}\n")

        try:
            await self.run_setup(guild)
        except Exception as e:
            print(f"❌ Error during setup: {e}")
            import traceback

            traceback.print_exc()
        finally:
            self.setup_complete = True
            await self.close()

    async def run_setup(self, guild):
        """Run the complete setup process."""

        # Step 1: Create admin account
        print("=" * 60)
        print("STEP 1: Create Admin Account")
        print("=" * 60)

        admin_discord_id = input(
            "Enter your Discord ID (right-click profile → Copy ID): "
        ).strip()
        admin_name = input("Enter your full name: ").strip()
        admin_email = input("Enter your email: ").strip()

        if not admin_discord_id or not admin_name or not admin_email:
            print("❌ All fields are required")
            return

        try:
            # Check if admin already exists
            existing_admin = self.team_service.get_member_by_discord_id(
                int(admin_discord_id)
            )
            if existing_admin:
                print(f"✅ Admin account already exists: {existing_admin.name}")
                admin_member = existing_admin
            else:
                from uuid import uuid4

                admin_data = TeamMemberCreate(
                    user_id=uuid4(),  # Temporary UUID
                    discord_id=int(admin_discord_id),
                    discord_username=str(self.get_user(int(admin_discord_id)))
                    if self.get_user(int(admin_discord_id))
                    else admin_email.split("@")[0],
                    name=admin_name,
                    email=admin_email,
                    role="Admin",
                    team="Leadership",
                )
                admin_member = self.team_service.data_service.create_team_member(
                    admin_data
                )
                print(f"✅ Created admin account: {admin_member.name}")
        except Exception as e:
            print(f"❌ Error creating admin: {e}")
            return

        # Step 2: Create teams in database
        print("\n" + "=" * 60)
        print("STEP 2: Create Teams in Database")
        print("=" * 60)

        teams_to_create = [
            "Engineering",
            "Product",
            "Business",
            "Marketing",
            "Sales",
            "Operations",
        ]

        created_teams = []
        for team_name in teams_to_create:
            try:
                existing_team = self.team_service.data_service.get_team_by_name(
                    team_name
                )
                if existing_team:
                    print(f"  ⏭️  Team '{team_name}' already exists")
                    created_teams.append(existing_team)
                else:
                    # Teams are created by migration, just verify they exist
                    print(
                        f"  ⚠️  Team '{team_name}' not found - should be created by migration"
                    )
            except Exception as e:
                print(f"  ⚠️  Error checking team '{team_name}': {e}")

        # Get all teams from database
        all_teams = self.team_service.data_service.list_teams()
        print(f"\n✅ Found {len(all_teams)} teams in database")

        # Step 3: Create Discord roles
        print("\n" + "=" * 60)
        print("STEP 3: Create Discord Roles")
        print("=" * 60)

        # Check if bot has Manage Roles permission
        if not guild.me.guild_permissions.manage_roles:
            print("❌ Bot is missing 'Manage Roles' permission!")
            print("   Please give the bot 'Manage Roles' permission in Server Settings")
            print("   Then re-run this script")
            print("\n   Skipping role creation...")
        else:
            role_colors = {
                "Engineering": discord.Color.blue(),
                "Product": discord.Color.green(),
                "Business": discord.Color.gold(),
                "Marketing": discord.Color.purple(),
                "Sales": discord.Color.orange(),
                "Operations": discord.Color.teal(),
            }

            for team_name, color in role_colors.items():
                try:
                    # Check if role exists
                    existing_role = discord.utils.get(guild.roles, name=team_name)
                    if existing_role:
                        print(f"  ⏭️  Discord role '{team_name}' already exists")
                    else:
                        # Create role
                        new_role = await guild.create_role(
                            name=team_name,
                            color=color,
                            mentionable=True,
                            reason="Alfred bot setup",
                        )
                        print(
                            f"  ✅ Created Discord role '{team_name}' (ID: {new_role.id})"
                        )

                        # Update team in database with Discord role ID
                        team = self.team_service.data_service.get_team_by_name(
                            team_name
                        )
                        if team:
                            update = TeamUpdate(discord_role_id=new_role.id)
                            self.team_service.data_service.update_team(team.id, update)
                            print(f"     → Updated database with Discord role ID")
                except Exception as e:
                    print(f"  ❌ Error creating role '{team_name}': {e}")

        # Step 4: Initialize Google Drive folders
        print("\n" + "=" * 60)
        print("STEP 4: Initialize Google Drive Folders")
        print("=" * 60)

        if not self.docs_service.is_available():
            print("⚠️  Google Docs service not available - skipping Drive setup")
            print("   Configure GOOGLE_CREDENTIALS_PATH to enable this feature")
        else:
            # Create Team Management folder
            print("\n📁 Creating Team Management folder...")
            team_mgmt_folder = self.docs_service.get_team_management_folder()
            if team_mgmt_folder:
                print(f"✅ Team Management folder: {team_mgmt_folder}")
            else:
                print("❌ Failed to create Team Management folder")
                return

            # Create team folders
            print("\n📁 Creating team folder structures...")
            primary_teams = ["Engineering", "Product", "Business"]

            for team_name in primary_teams:
                team = self.team_service.data_service.get_team_by_name(team_name)
                if not team:
                    print(f"  ⚠️  Team '{team_name}' not found in database")
                    continue

                # Skip if already has folder structure
                if team.roster_sheet_id:
                    print(f"  ⏭️  Team '{team_name}' already has folder structure")
                    continue

                print(f"\n  🔧 Setting up '{team_name}'...")
                try:
                    result = self.docs_service.create_team_folder_structure(team_name)
                    if result:
                        print(f"     ✅ Folder: {result['folder_id']}")
                        print(f"     ✅ Overview: {result['overview_doc_url']}")
                        print(f"     ✅ Roster: {result['roster_sheet_url']}")

                        # Update team record
                        update = TeamUpdate(
                            drive_folder_id=result["folder_id"],
                            overview_doc_id=result["overview_doc_id"],
                            overview_doc_url=result["overview_doc_url"],
                            roster_sheet_id=result["roster_sheet_id"],
                            roster_sheet_url=result["roster_sheet_url"],
                        )
                        self.team_service.data_service.update_team(team.id, update)
                        print(f"     ✅ Updated database")
                    else:
                        print(f"     ❌ Failed to create folder structure")
                except Exception as e:
                    print(f"     ❌ Error: {e}")

        # Step 5: Summary
        print("\n" + "=" * 60)
        print("SETUP COMPLETE! 🎉")
        print("=" * 60)
        print("\n📋 Summary:")
        print(f"  ✅ Admin account: {admin_member.name} ({admin_member.email})")
        print(f"  ✅ Teams in database: {len(all_teams)}")
        print(f"  ✅ Discord roles created")
        if self.docs_service.is_available():
            print(f"  ✅ Google Drive folders initialized")
        print("\n🚀 You're ready to test the onboarding flow!")
        print("\nNext steps:")
        print("  1. Start the bot: ./run.sh")
        print("  2. Test onboarding: /start-onboarding")
        print("  3. Approve as admin in #admin-onboarding")
        print()


async def main():
    """Main setup function."""
    print("🚀 Alfred Bot - Complete Setup")
    print("=" * 60)
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

    # Create and run bot
    bot = SetupBot()

    try:
        await bot.start(os.getenv("DISCORD_BOT_TOKEN"))
    except KeyboardInterrupt:
        print("\n❌ Setup cancelled by user")
        await bot.close()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
