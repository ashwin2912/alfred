#!/usr/bin/env python3
"""
Interactive setup script for Alfred Discord Bot.

This script:
1. Asks which teams you want to create
2. Creates admin account in database
3. Creates/updates teams in database
4. Creates Discord roles with custom colors
5. Initializes Google Drive folder structure
6. Links everything together

Run this for initial setup or to add new teams.
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


# Default team suggestions
DEFAULT_TEAMS = {
    "Engineering": {
        "description": "Software development and technical infrastructure",
        "color": "blue",
    },
    "Product": {"description": "Product management and design", "color": "green"},
    "Business": {
        "description": "Business development and partnerships",
        "color": "gold",
    },
    "Marketing": {"description": "Marketing and growth initiatives", "color": "purple"},
    "Sales": {"description": "Sales and business development", "color": "orange"},
    "Operations": {
        "description": "Operations and administrative functions",
        "color": "teal",
    },
}

COLOR_MAP = {
    "blue": discord.Color.blue(),
    "green": discord.Color.green(),
    "gold": discord.Color.gold(),
    "purple": discord.Color.purple(),
    "orange": discord.Color.orange(),
    "teal": discord.Color.teal(),
    "red": discord.Color.red(),
    "magenta": discord.Color.magenta(),
    "dark_blue": discord.Color.dark_blue(),
    "dark_green": discord.Color.dark_green(),
}


class SetupBot(commands.Bot):
    """Temporary bot instance for setup."""

    def __init__(self, teams_to_create):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

        self.guild_id = int(os.getenv("DISCORD_GUILD_ID"))
        self.teams_to_create = teams_to_create
        self.setup_complete = False
        self.team_service = TeamMemberService()
        self.docs_service = DocsService()

    async def on_ready(self):
        """Run setup when bot is ready."""
        print(f"\n🤖 Bot logged in as {self.user}")

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
        print("=" * 70)
        print("STEP 1: Create Admin Account")
        print("=" * 70)

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

        # Step 2: Create/update teams in database
        print("\n" + "=" * 70)
        print("STEP 2: Create Teams in Database")
        print("=" * 70)

        from supabase import create_client

        supabase = create_client(
            os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY")
        )

        created_teams = []
        for team_name, team_info in self.teams_to_create.items():
            try:
                # Check if team exists
                existing = (
                    supabase.table("teams").select("*").eq("name", team_name).execute()
                )

                if existing.data:
                    print(f"  ⏭️  Team '{team_name}' already exists in database")
                    created_teams.append(existing.data[0])
                else:
                    # Create team
                    result = (
                        supabase.table("teams")
                        .insert(
                            {
                                "name": team_name,
                                "description": team_info["description"],
                            }
                        )
                        .execute()
                    )
                    print(f"  ✅ Created team '{team_name}' in database")
                    created_teams.append(result.data[0])
            except Exception as e:
                print(f"  ❌ Error creating team '{team_name}': {e}")

        print(f"\n✅ Total teams in database: {len(created_teams)}")

        # Step 3: Create Discord roles
        print("\n" + "=" * 70)
        print("STEP 3: Create Discord Roles (Team + Team Lead)")
        print("=" * 70)

        # Check if bot has Manage Roles permission
        if not guild.me.guild_permissions.manage_roles:
            print("❌ Bot is missing 'Manage Roles' permission!")
            print("   Please give the bot 'Manage Roles' permission in Server Settings")
            print("   Then re-run this script")
            print("\n   Skipping role creation...")
        else:
            for team_name, team_info in self.teams_to_create.items():
                try:
                    # Create base team role
                    existing_role = discord.utils.get(guild.roles, name=team_name)
                    if existing_role:
                        print(f"  ⏭️  Discord role '{team_name}' already exists")
                        role_id = existing_role.id
                    else:
                        color = COLOR_MAP.get(
                            team_info["color"], discord.Color.default()
                        )
                        new_role = await guild.create_role(
                            name=team_name,
                            color=color,
                            mentionable=True,
                            reason="Alfred bot setup",
                        )
                        print(
                            f"  ✅ Created Discord role '{team_name}' ({team_info['color']}, ID: {new_role.id})"
                        )
                        role_id = new_role.id

                    # Update team in database with Discord role ID
                    team = self.team_service.data_service.get_team_by_name(team_name)
                    if team and not team.discord_role_id:
                        update = TeamUpdate(discord_role_id=role_id)
                        self.team_service.data_service.update_team(team.id, update)
                        print(f"     → Updated database with Discord role ID")

                    # Create Team Lead role
                    team_lead_name = f"{team_name} Team Lead"
                    existing_lead_role = discord.utils.get(guild.roles, name=team_lead_name)
                    if existing_lead_role:
                        print(f"  ⏭️  Discord role '{team_lead_name}' already exists")
                    else:
                        # Use same color but make it slightly different (hoisted)
                        color = COLOR_MAP.get(
                            team_info["color"], discord.Color.default()
                        )
                        new_lead_role = await guild.create_role(
                            name=team_lead_name,
                            color=color,
                            mentionable=True,
                            hoist=True,  # Display separately in member list
                            reason="Alfred bot setup - Team Lead role",
                        )
                        print(
                            f"  ✅ Created Discord role '{team_lead_name}' (Team Lead, ID: {new_lead_role.id})"
                        )

                except Exception as e:
                    print(f"  ❌ Error creating roles for '{team_name}': {e}")

        # Step 4: Initialize Google Drive folders
        print("\n" + "=" * 70)
        print("STEP 4: Initialize Google Drive Folders")
        print("=" * 70)

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

            for team_name in self.teams_to_create.keys():
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

        # Summary
        print("\n" + "=" * 70)
        print("SETUP COMPLETE! 🎉")
        print("=" * 70)
        print("\n📋 Summary:")
        print(f"  ✅ Admin account: {admin_member.name} ({admin_member.email})")
        print(f"  ✅ Teams created: {len(created_teams)}")
        print(f"  ✅ Discord roles created")
        if self.docs_service.is_available():
            print(f"  ✅ Google Drive folders initialized")

        print("\n🎨 Teams configured:")
        for team_name, team_info in self.teams_to_create.items():
            print(f"  • {team_name} ({team_info['color']})")

        print("\n🚀 You're ready to test the onboarding flow!")
        print("\nNext steps:")
        print("  1. Start the bot: ./run.sh")
        print("  2. Test onboarding: /start-onboarding")
        print("  3. Approve as admin in #admin-onboarding")
        print()


def get_teams_from_user():
    """Interactive prompt to get teams from user."""
    print("=" * 70)
    print("TEAM CONFIGURATION")
    print("=" * 70)
    print()
    print("Let's configure your teams. You can:")
    print("  1. Use default teams (Engineering, Product, Business, etc.)")
    print("  2. Select from defaults")
    print("  3. Create custom teams")
    print()

    choice = input("Choose option (1/2/3): ").strip()

    if choice == "1":
        print("\n✅ Using all default teams:")
        for name, info in DEFAULT_TEAMS.items():
            print(f"  • {name} ({info['color']}) - {info['description']}")
        return DEFAULT_TEAMS

    elif choice == "2":
        print("\n📋 Available default teams:")
        team_list = list(DEFAULT_TEAMS.keys())
        for i, name in enumerate(team_list, 1):
            info = DEFAULT_TEAMS[name]
            print(f"  {i}. {name} ({info['color']}) - {info['description']}")

        print("\nEnter team numbers to include (comma-separated, e.g., 1,2,3):")
        selected = input("Teams: ").strip()

        teams = {}
        for num in selected.split(","):
            try:
                idx = int(num.strip()) - 1
                if 0 <= idx < len(team_list):
                    team_name = team_list[idx]
                    teams[team_name] = DEFAULT_TEAMS[team_name]
            except ValueError:
                continue

        if teams:
            print(f"\n✅ Selected {len(teams)} teams:")
            for name in teams:
                print(f"  • {name}")
            return teams
        else:
            print("❌ No valid teams selected")
            return None

    elif choice == "3":
        print("\n🎨 Create custom teams")
        print("Available colors:", ", ".join(COLOR_MAP.keys()))
        print()

        teams = {}
        while True:
            name = input("Team name (or press Enter to finish): ").strip()
            if not name:
                break

            description = input(f"Description for {name}: ").strip()
            color = (
                input(f"Color for {name} ({', '.join(list(COLOR_MAP.keys())[:6])}): ")
                .strip()
                .lower()
            )

            if color not in COLOR_MAP:
                color = "blue"
                print(f"  ⚠️  Invalid color, using 'blue'")

            teams[name] = {"description": description or f"{name} team", "color": color}
            print(f"  ✅ Added {name}\n")

        if teams:
            print(f"\n✅ Created {len(teams)} custom teams:")
            for name, info in teams.items():
                print(f"  • {name} ({info['color']}) - {info['description']}")
            return teams
        else:
            print("❌ No teams created")
            return None

    else:
        print("❌ Invalid choice")
        return None


async def main():
    """Main setup function."""
    print("\n" + "=" * 70)
    print(" 🚀 Alfred Bot - Interactive Setup")
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

    # Get teams from user
    teams = get_teams_from_user()
    if not teams:
        print("\n❌ Setup cancelled - no teams configured")
        return 1

    # Confirm
    print(f"\n⚠️  This will create {len(teams)} teams in:")
    print("   • Database (Supabase)")
    print("   • Discord (roles)")
    print("   • Google Drive (folders + rosters)")
    print()
    confirm = input("Continue? (yes/no): ").strip().lower()

    if confirm != "yes":
        print("❌ Setup cancelled")
        return 1

    # Create and run bot
    bot = SetupBot(teams)

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
