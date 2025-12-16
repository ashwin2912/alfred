"""Discord team management commands for creating and managing teams."""

import logging
from typing import Optional
from uuid import UUID

import discord
from discord import app_commands

logger = logging.getLogger(__name__)


class TeamManagementCommands:
    """
    Discord commands for team creation and management.

    Only accessible to Admin, Manager, Director, and Executive roles.
    """

    def __init__(self, bot, team_service, docs_service, discord_team_service):
        """
        Initialize team management commands.

        Args:
            bot: Discord bot instance
            team_service: TeamMemberService instance
            docs_service: DocsService instance for Google Drive operations
            discord_team_service: DiscordTeamService for Discord role/channel creation
        """
        self.bot = bot
        self.team_service = team_service
        self.docs_service = docs_service
        self.discord_team_service = discord_team_service

        logger.info("TeamManagementCommands initialized")

    def register_commands(self, tree: app_commands.CommandTree):
        """
        Register commands with the bot's command tree.

        Args:
            tree: Discord command tree
        """
        tree.add_command(self._create_team_command())
        tree.add_command(self._add_to_team_command())
        tree.add_command(self._team_report_command())
        logger.info("Team management commands registered")

    async def _check_admin_access(
        self, interaction: discord.Interaction
    ) -> tuple[bool, Optional[str]]:
        """
        Check if user has admin access (Manager or above).

        Args:
            interaction: Discord interaction

        Returns:
            tuple: (has_access, error_message)
        """
        if not interaction.guild:
            return False, "This command can only be used in a server."

        member = interaction.guild.get_member(interaction.user.id)
        if not member:
            return False, "Could not verify your server membership."

        # Check for admin roles
        admin_roles = ["Manager", "Director", "Executive", "Admin"]

        user_roles = [role.name for role in member.roles]
        has_access = any(role in user_roles for role in admin_roles)

        if not has_access:
            return False, "This command requires Manager role or higher."

        return True, None

    def _create_team_command(self) -> app_commands.Command:
        """Create the /create-team command."""

        @app_commands.command(
            name="create-team",
            description="[Admin] Create a new team with Discord roles, channels, and Google Drive folder",
        )
        @app_commands.describe(
            team_name="Name of the team (e.g., Engineering, Product, Business)",
            team_color="Color for the Discord role",
            description="Brief description of the team",
            team_lead="Select the team lead (REQUIRED)",
        )
        @app_commands.choices(
            team_color=[
                app_commands.Choice(name="Blue", value="blue"),
                app_commands.Choice(name="Green", value="green"),
                app_commands.Choice(name="Red", value="red"),
                app_commands.Choice(name="Purple", value="purple"),
                app_commands.Choice(name="Orange", value="orange"),
                app_commands.Choice(name="Yellow", value="yellow"),
                app_commands.Choice(name="Teal", value="teal"),
                app_commands.Choice(name="Pink", value="pink"),
            ]
        )
        async def create_team(
            interaction: discord.Interaction,
            team_name: str,
            team_color: str,
            description: str,
            team_lead: discord.Member,
        ):
            """Create a new team with complete infrastructure."""
            # Check admin access
            has_access, error_msg = await self._check_admin_access(interaction)
            if not has_access:
                await interaction.response.send_message(error_msg, ephemeral=True)
                return

            # Defer response since this will take time
            await interaction.response.defer(ephemeral=True)

            # Verify team lead is in database
            team_lead_member = self.team_service.data_service.get_team_member_by_discord_id(
                team_lead.id
            )
            if not team_lead_member:
                await interaction.followup.send(
                    f"❌ {team_lead.mention} is not onboarded yet. "
                    f"Please have them complete onboarding first using the welcome message.",
                    ephemeral=True,
                )
                return

            try:
                # Step 1: Create Discord roles (team + manager)
                logger.info(f"Creating Discord roles for team: {team_name}")
                (
                    team_role,
                    manager_role,
                ) = await self.discord_team_service.create_team_roles(
                    interaction.guild, team_name, team_color
                )

                if not team_role or not manager_role:
                    await interaction.followup.send(
                        f"❌ Failed to create Discord roles for {team_name}",
                        ephemeral=True,
                    )
                    return

                # Step 2: Create Discord channels
                logger.info(f"Creating Discord channels for team: {team_name}")
                (
                    general_channel,
                    standup_channel,
                ) = await self.discord_team_service.create_team_channels(
                    interaction.guild, team_name, team_role
                )

                if not general_channel:
                    await interaction.followup.send(
                        f"❌ Failed to create Discord channels for {team_name}",
                        ephemeral=True,
                    )
                    return

                # Step 3: Create Google Drive folder structure
                logger.info(f"Creating Google Drive folder for team: {team_name}")
                folder_result = self.docs_service.create_team_folder_structure(
                    team_name
                )

                if not folder_result:
                    await interaction.followup.send(
                        f"⚠️ Team created in Discord, but Google Drive setup failed. Please create manually.",
                        ephemeral=True,
                    )
                    # Continue with partial setup
                    folder_result = {}

                # Step 4: Create team in database with team lead
                logger.info(f"Creating team record in database: {team_name}")
                team = self.team_service.data_service.create_team(
                    name=team_name,
                    team_lead_id=team_lead_member.id,
                    description=description,
                    drive_folder_id=folder_result.get("folder_id"),
                    overview_doc_id=folder_result.get("overview_doc_id"),
                    overview_doc_url=folder_result.get("overview_doc_url"),
                    roster_sheet_id=folder_result.get("roster_sheet_id"),
                    roster_sheet_url=folder_result.get("roster_sheet_url"),
                    discord_role_id=team_role.id,
                    discord_manager_role_id=manager_role.id,
                    discord_general_channel_id=general_channel.id,
                    discord_standup_channel_id=standup_channel.id
                    if standup_channel
                    else None,
                )

                # Step 5: Assign team lead roles and add to team
                logger.info(f"Assigning team lead: {team_lead.name}")
                # Add both team and manager roles to team lead
                await team_lead.add_roles(team_role, manager_role)

                # Add to team
                self.team_service.data_service.add_member_to_team(
                    team_lead_member.id, team.id, role=f"{team_name} Team Lead"
                )

                # Update roster
                if folder_result.get("roster_sheet_id"):
                    self.docs_service.add_member_to_roster(
                        roster_sheet_id=folder_result["roster_sheet_id"],
                        member_name=team_lead_member.name,
                        discord_username=team_lead_member.discord_username or team_lead.name,
                        email=team_lead_member.email,
                        role=f"{team_name} Team Lead",
                        profile_url=team_lead_member.profile_url or "",
                    )

                # Build response
                embed = discord.Embed(
                    title=f"✅ Team Created: {team_name}",
                    description=f"{description}",
                    color=discord.Color.green(),
                )

                # What was created
                created_items = f"• Team Role: {team_role.mention} ({team_color})\n"
                created_items += f"• Manager Role: {manager_role.mention}\n"
                created_items += f"• Channels: {general_channel.mention}"
                if standup_channel:
                    created_items += f", {standup_channel.mention}"
                created_items += "\n"

                if folder_result.get("folder_id"):
                    created_items += f"• Google Drive Folder: [View Folder](https://drive.google.com/drive/folders/{folder_result['folder_id']})\n"
                if folder_result.get("overview_doc_url"):
                    created_items += f"• Team Overview: [View Document]({folder_result['overview_doc_url']})\n"
                if folder_result.get("roster_sheet_url"):
                    created_items += f"• Team Roster: [View Spreadsheet]({folder_result['roster_sheet_url']})\n"

                if team_lead:
                    created_items += f"• Team Lead: {team_lead.mention}\n"

                embed.add_field(
                    name="📋 What Was Created", value=created_items, inline=False
                )

                # Next steps
                next_steps = (
                    "1. Use `/add-to-team` to add members\n"
                    "2. Use `/set-team-space` to connect ClickUp\n"
                    "3. Team lead can use `/brainstorm` for project planning"
                )
                embed.add_field(name="🎯 Next Steps", value=next_steps, inline=False)

                embed.set_footer(text=f"Team ID: {team.id}")

                await interaction.followup.send(embed=embed, ephemeral=True)

                # Post announcement to general channel
                if general_channel:
                    announce_embed = discord.Embed(
                        title=f"🎉 Welcome to {team_name}!",
                        description=f"{description}\n\nThis channel is for general team discussion and updates.",
                        color=discord.Color.blue(),
                    )
                    if team_lead:
                        announce_embed.add_field(
                            name="Team Lead",
                            value=f"{team_lead.mention}",
                            inline=False,
                        )
                    await general_channel.send(embed=announce_embed)

                logger.info(f"Successfully created team: {team_name}")

            except Exception as e:
                logger.error(f"Failed to create team: {str(e)}", exc_info=True)
                await interaction.followup.send(
                    f"❌ Error creating team: {str(e)}", ephemeral=True
                )

        return create_team

    def _add_to_team_command(self) -> app_commands.Command:
        """Create the /add-to-team command."""

        async def team_autocomplete(
            interaction: discord.Interaction,
            current: str,
        ) -> list[app_commands.Choice[str]]:
            """Autocomplete teams from database."""
            try:
                teams = (
                    self.team_service.data_service.client.table("teams")
                    .select("name")
                    .execute()
                )
                team_names = [team["name"] for team in teams.data]

                # Filter based on what user is typing
                if current:
                    team_names = [
                        name for name in team_names if current.lower() in name.lower()
                    ]

                return [
                    app_commands.Choice(name=name, value=name)
                    for name in team_names[:25]  # Discord limit
                ]
            except Exception as e:
                logger.error(f"Error in team autocomplete: {e}")
                return []

        @app_commands.command(
            name="add-to-team",
            description="[Admin] Add a member to a team or promote to team lead",
        )
        @app_commands.describe(
            member="The member to add to the team",
            team_name="Name of the team",
            role="Optional: Role within the team (e.g., Senior Engineer)",
            make_team_lead="Make this person the team lead (gives manager role)",
        )
        @app_commands.autocomplete(team_name=team_autocomplete)
        async def add_to_team(
            interaction: discord.Interaction,
            member: discord.Member,
            team_name: str,
            role: Optional[str] = None,
            make_team_lead: bool = False,
        ):
            """Add a member to a team."""
            # Check admin access
            has_access, error_msg = await self._check_admin_access(interaction)
            if not has_access:
                await interaction.response.send_message(error_msg, ephemeral=True)
                return

            await interaction.response.defer(ephemeral=True)

            try:
                # Get team from database
                team = self.team_service.data_service.get_team_by_name(team_name)
                if not team:
                    await interaction.followup.send(
                        f"❌ Team '{team_name}' not found in database.", ephemeral=True
                    )
                    return

                # Get member from database
                db_member = (
                    self.team_service.data_service.get_team_member_by_discord_id(
                        member.id
                    )
                )
                if not db_member:
                    await interaction.followup.send(
                        f"❌ {member.mention} has not completed onboarding yet. They need to use `/start-onboarding` first.",
                        ephemeral=True,
                    )
                    return

                # Check if already a member and just promoting to team lead
                already_member = False
                try:
                    existing = (
                        self.team_service.data_service.client.table("team_memberships")
                        .select("*")
                        .eq("member_id", str(db_member.id))
                        .eq("team_id", str(team.id))
                        .execute()
                    )
                    already_member = len(existing.data) > 0
                except:
                    pass

                # Add to team in database (or update if already member)
                if not already_member:
                    self.team_service.data_service.add_member_to_team(
                        db_member.id,
                        team.id,
                        role=role or ("Team Lead" if make_team_lead else "Team Member"),
                    )

                # Handle team lead promotion
                is_team_lead = False
                if make_team_lead:
                    # Update team_lead_id in teams table
                    self.team_service.data_service.client.table("teams").update(
                        {"team_lead_id": str(db_member.id)}
                    ).eq("id", str(team.id)).execute()
                    is_team_lead = True

                # Assign Discord roles
                discord_role = None
                manager_role = None
                roles_to_add = []

                if team.discord_role_id:
                    discord_role = interaction.guild.get_role(team.discord_role_id)
                    if discord_role and discord_role not in member.roles:
                        roles_to_add.append(discord_role)

                if make_team_lead and team.discord_manager_role_id:
                    manager_role = interaction.guild.get_role(
                        team.discord_manager_role_id
                    )
                    if manager_role and manager_role not in member.roles:
                        roles_to_add.append(manager_role)

                if roles_to_add:
                    await member.add_roles(*roles_to_add)

                # Update team roster in Google Sheets
                roster_updated = False
                if (
                    team.roster_sheet_id
                    and self.docs_service.is_available()
                    and not already_member
                ):
                    try:
                        final_role = role or (
                            "Team Lead" if make_team_lead else "Team Member"
                        )
                        self.docs_service.add_member_to_roster(
                            roster_sheet_id=team.roster_sheet_id,
                            member_name=db_member.name,
                            discord_username=db_member.discord_username or member.name,
                            email=db_member.email,
                            role=final_role,
                            profile_url=db_member.profile_url or "",
                        )
                        roster_updated = True
                        logger.info(f"Added {db_member.name} to {team_name} roster")
                    except Exception as e:
                        logger.warning(
                            f"Failed to update roster for {team_name}: {str(e)}"
                        )

                # Build response
                if already_member and make_team_lead:
                    title = (
                        f"✅ Promoted {member.display_name} to Team Lead of {team_name}"
                    )
                elif already_member:
                    title = f"✅ Updated {member.display_name} in {team_name}"
                else:
                    title = f"✅ Added {member.display_name} to {team_name}"

                embed = discord.Embed(
                    title=title,
                    color=discord.Color.green(),
                )

                updates = ""
                if discord_role:
                    updates += f"• Team Role: ✅ {discord_role.mention} assigned\n"
                else:
                    updates += "• Team Role: ⚠️ Role not found - assign manually\n"

                if manager_role:
                    updates += f"• Manager Role: ✅ {manager_role.mention} assigned\n"

                if roster_updated:
                    updates += "• Team Roster: ✅ Added to spreadsheet\n"
                elif already_member:
                    updates += "• Team Roster: ℹ️ Already in roster\n"
                else:
                    updates += "• Team Roster: ⚠️ Update failed - check manually\n"

                # Add channel access info
                if team.discord_general_channel_id:
                    general_channel = interaction.guild.get_channel(
                        team.discord_general_channel_id
                    )
                    if general_channel:
                        updates += (
                            f"• Channels: ✅ Can access {general_channel.mention}"
                        )
                        if team.discord_standup_channel_id:
                            standup_channel = interaction.guild.get_channel(
                                team.discord_standup_channel_id
                            )
                            if standup_channel:
                                updates += f", {standup_channel.mention}"
                        updates += "\n"

                embed.add_field(name="📋 Updates", value=updates, inline=False)

                if role:
                    embed.add_field(name="Role", value=role, inline=True)

                await interaction.followup.send(embed=embed, ephemeral=True)

                # Send DM to member
                try:
                    if make_team_lead:
                        dm_embed = discord.Embed(
                            title=f"🎖️ You've been promoted to Team Lead of {team_name}!",
                            description=f"Congratulations! You now have manager permissions for the team.",
                            color=discord.Color.gold(),
                        )
                        dm_embed.add_field(
                            name="Your Responsibilities",
                            value="• Manage team messages and threads\n• Guide team members\n• Coordinate team activities",
                            inline=False,
                        )
                    else:
                        dm_embed = discord.Embed(
                            title=f"🎉 You've been added to {team_name}!",
                            description=f"Welcome to the team! You now have access to team channels and resources.",
                            color=discord.Color.blue(),
                        )

                    if role:
                        dm_embed.add_field(name="Your Role", value=role, inline=False)

                    if team.discord_general_channel_id:
                        general_channel = interaction.guild.get_channel(
                            team.discord_general_channel_id
                        )
                        if general_channel:
                            dm_embed.add_field(
                                name="Team Channel",
                                value=f"Join the conversation in {general_channel.mention}",
                                inline=False,
                            )

                    if db_member.profile_url:
                        dm_embed.add_field(
                            name="Your Profile",
                            value=f"[View your profile document]({db_member.profile_url})",
                            inline=False,
                        )

                    await member.send(embed=dm_embed)
                except discord.Forbidden:
                    logger.warning(f"Could not send DM to {member.name}")

                # Post to team channel
                if team.discord_general_channel_id:
                    general_channel = interaction.guild.get_channel(
                        team.discord_general_channel_id
                    )
                    if general_channel:
                        if make_team_lead:
                            welcome_msg = f"🎖️ {member.mention} has been promoted to Team Lead! Congrats! 🎉"
                        elif already_member:
                            welcome_msg = f"📢 {member.mention}'s role has been updated"
                            if role:
                                welcome_msg += f" to {role}"
                        else:
                            welcome_msg = f"👋 Welcome {member.mention} to the team!"
                            if role:
                                welcome_msg += f" ({role})"
                        await general_channel.send(welcome_msg)

                logger.info(f"Added {member.name} to team {team_name}")

            except Exception as e:
                logger.error(f"Failed to add member to team: {str(e)}", exc_info=True)
                await interaction.followup.send(
                    f"❌ Error adding member to team: {str(e)}", ephemeral=True
                )

        return add_to_team

    def _team_report_command(self) -> app_commands.Command:
        """Create the /team-report command."""

        @app_commands.command(
            name="team-report",
            description="[Team Lead] Generate a report of team's ClickUp tasks",
        )
        async def team_report(interaction: discord.Interaction):
            """Generate a daily report of team's ClickUp board status."""
            await interaction.response.defer(ephemeral=False)

            try:
                # Get the channel this was run in
                channel = interaction.channel

                # Find which team this channel belongs to
                team = None
                if channel.category:
                    # Try to match channel category to team
                    teams_response = (
                        self.team_service.data_service.client.table("teams")
                        .select("*")
                        .execute()
                    )
                    for t in teams_response.data:
                        if (
                            t.get("discord_general_channel_id") == channel.id
                            or t.get("discord_standup_channel_id") == channel.id
                        ):
                            team = (
                                self.team_service.data_service.client.table("teams")
                                .select("*")
                                .eq("id", t["id"])
                                .execute()
                                .data[0]
                            )
                            break

                if not team:
                    await interaction.followup.send(
                        "❌ This command must be run in a team channel (e.g., #engineering-general or #engineering-standups)",
                        ephemeral=True,
                    )
                    return

                # Check if user is team lead or admin
                member = self.team_service.get_member_by_discord_id(interaction.user.id)
                if not member:
                    await interaction.followup.send(
                        "❌ You must be onboarded to use this command.", ephemeral=True
                    )
                    return

                is_team_lead = (
                    str(team.get("team_lead_id")) == str(member.id)
                    if team.get("team_lead_id")
                    else False
                )
                is_admin = (
                    member.role in ["Manager", "Director", "Executive"]
                    if member.role
                    else False
                )

                if not (is_team_lead or is_admin):
                    await interaction.followup.send(
                        "❌ Only the team lead or admins can generate team reports.",
                        ephemeral=True,
                    )
                    return

                # Get configured project lists for this team
                list_ids = self.team_service.data_service.get_team_list_ids_by_name(
                    team["name"]
                )

                if not list_ids:
                    await interaction.followup.send(
                        f"❌ Team '{team['name']}' does not have any ClickUp lists configured.\n"
                        f"Use `/add-project-list` to add lists first.",
                        ephemeral=True,
                    )
                    return

                # Get team members to fetch their tasks
                team_members_response = (
                    self.team_service.data_service.client.table("team_memberships")
                    .select("member_id")
                    .eq("team_id", team["id"])
                    .eq("is_active", True)
                    .execute()
                )

                if not team_members_response.data:
                    await interaction.followup.send(
                        f"⚠️ No active members found in team '{team['name']}'.",
                        ephemeral=True,
                    )
                    return

                # Get any team member's ClickUp token to fetch tasks
                from bot.services import ClickUpService

                clickup_token = None
                for tm in team_members_response.data:
                    member_data = (
                        self.team_service.data_service.client.table("team_members")
                        .select("*")
                        .eq("id", tm["member_id"])
                        .execute()
                        .data
                    )
                    if member_data and member_data[0].get("clickup_api_token"):
                        clickup_token = member_data[0].get("clickup_api_token")
                        break

                if not clickup_token:
                    await interaction.followup.send(
                        f"❌ No team members have configured their ClickUp API tokens.\n"
                        f"Team members need to use `/setup-clickup` first.",
                        ephemeral=True,
                    )
                    return

                # Validate the ClickUp token first
                clickup = ClickUpService(clickup_token)
                is_valid, error_msg = await clickup.validate_token()

                if not is_valid:
                    await interaction.followup.send(
                        f"❌ ClickUp API token is invalid or expired.\n\n"
                        f"Error: {error_msg}\n\n"
                        f"Please update your token using `/setup-clickup <new_token>`",
                        ephemeral=True,
                    )
                    return

                # Fetch all tasks from configured lists
                all_team_tasks = await clickup.get_all_tasks(
                    assigned_only=False,
                    list_ids=list_ids
                )

                logger.info(f"Fetched {len(all_team_tasks)} tasks from {len(list_ids)} lists: {list_ids}")
                logger.info(f"Sample task: {all_team_tasks[0] if all_team_tasks else 'No tasks'}")

                # Build a map of team member IDs for filtering
                team_member_ids = set()
                team_member_names = {}
                for tm in team_members_response.data:
                    member_data = (
                        self.team_service.data_service.client.table("team_members")
                        .select("id, name, clickup_user_id")
                        .eq("id", tm["member_id"])
                        .execute()
                        .data
                    )
                    if member_data:
                        member_obj = member_data[0]
                        clickup_user_id = member_obj.get("clickup_user_id")
                        if clickup_user_id:
                            team_member_ids.add(str(clickup_user_id))
                            team_member_names[str(clickup_user_id)] = member_obj.get(
                                "name"
                            )

                # Track member task counts
                member_task_counts = {}
                for task in all_team_tasks:
                    assignees = task.get("assignees", [])
                    for assignee in assignees:
                        assignee_id = str(assignee.get("id"))
                        if assignee_id in team_member_ids:
                            # Add member info to task
                            task["_member_name"] = team_member_names.get(assignee_id)
                            task["_member_id"] = assignee_id

                            # Count tasks per member
                            member_name = team_member_names.get(assignee_id)
                            member_task_counts[member_name] = (
                                member_task_counts.get(member_name, 0) + 1
                            )
                            break  # Only count each task once even if multiple team members assigned

                # Analyze tasks
                total_tasks = len(all_team_tasks)

                logger.info(f"Total tasks: {total_tasks}, Team member IDs: {team_member_ids}")
                logger.info(f"Member task counts: {member_task_counts}")

                if total_tasks == 0:
                    await interaction.followup.send(
                        f"📊 **{team['name']} Team Report**\n\n"
                        f"No tasks found for this team. Team members may need to configure their ClickUp tokens or be assigned tasks."
                    )
                    return

                # Group by status
                status_counts = {}
                priority_counts = {"urgent": 0, "high": 0, "normal": 0, "low": 0}
                overdue_tasks = []
                due_soon = []  # Due within 3 days

                import datetime

                now = datetime.datetime.now()

                for task in all_team_tasks:
                    # Status
                    status = task.get("status", {}).get("status", "Unknown")
                    status_counts[status] = status_counts.get(status, 0) + 1

                    # Priority
                    priority = task.get("priority")
                    if priority:
                        priority_level = priority.get("priority", "normal").lower()
                        if priority_level in priority_counts:
                            priority_counts[priority_level] += 1

                    # Due dates
                    due_date_str = task.get("due_date")
                    if due_date_str:
                        try:
                            # ClickUp timestamps are in milliseconds
                            due_date = datetime.datetime.fromtimestamp(
                                int(due_date_str) / 1000
                            )

                            if due_date < now:
                                overdue_tasks.append(task)
                            elif (due_date - now).days <= 3:
                                due_soon.append(task)
                        except:
                            pass

                # Build report embed
                embed = discord.Embed(
                    title=f"📊 {team['name']} Team Report",
                    description=f"Daily status report • {datetime.datetime.now().strftime('%B %d, %Y')}",
                    color=discord.Color.blue(),
                )

                # Overview
                overview = f"**Total Tasks:** {total_tasks}\n"
                overview += f"**Active Members:** {len(member_task_counts)}\n"
                if overdue_tasks:
                    overview += f"**⚠️ Overdue:** {len(overdue_tasks)}\n"
                if due_soon:
                    overview += f"**⏰ Due Soon (3 days):** {len(due_soon)}\n"

                embed.add_field(name="📈 Overview", value=overview, inline=False)

                # Status breakdown
                if status_counts:
                    status_text = ""
                    for status, count in sorted(
                        status_counts.items(), key=lambda x: x[1], reverse=True
                    ):
                        status_text += f"• **{status}**: {count}\n"
                    embed.add_field(
                        name="📋 Status Breakdown", value=status_text, inline=True
                    )

                # Priority breakdown
                priority_text = ""
                if priority_counts["urgent"] > 0:
                    priority_text += f"🔴 **Urgent**: {priority_counts['urgent']}\n"
                if priority_counts["high"] > 0:
                    priority_text += f"🟠 **High**: {priority_counts['high']}\n"
                if priority_counts["normal"] > 0:
                    priority_text += f"🟡 **Normal**: {priority_counts['normal']}\n"
                if priority_counts["low"] > 0:
                    priority_text += f"🟢 **Low**: {priority_counts['low']}\n"

                if priority_text:
                    embed.add_field(
                        name="⚡ Priority", value=priority_text, inline=True
                    )

                # Member workload
                if member_task_counts:
                    member_text = ""
                    for member_name, count in sorted(
                        member_task_counts.items(), key=lambda x: x[1], reverse=True
                    )[:5]:
                        member_text += f"• **{member_name}**: {count} tasks\n"
                    if len(member_task_counts) > 5:
                        member_text += (
                            f"• *...and {len(member_task_counts) - 5} more members*\n"
                        )
                    embed.add_field(
                        name="👥 Top Contributors", value=member_text, inline=False
                    )

                # All tasks summary (show top 10)
                if all_team_tasks:
                    tasks_text = ""
                    for task in all_team_tasks[:10]:
                        task_id = task.get("id", "")
                        task_name = task.get("name", "Untitled")[:50]
                        status = task.get("status", {}).get("status", "Unknown")

                        # Get assignee
                        assignees = task.get("assignees", [])
                        assignee_name = "Unassigned"
                        if assignees:
                            assignee_name = assignees[0].get("username", "Unknown")

                        # Priority emoji
                        priority = task.get("priority")
                        priority_emoji = ""
                        if priority:
                            priority_emoji = {"1": "🔴", "2": "🟡", "3": "🔵", "4": "⚪"}.get(
                                str(priority.get("id", "")), ""
                            )

                        task_url = task.get("url", "")
                        if task_url:
                            tasks_text += f"{priority_emoji} [{task_name}]({task_url}) - {status} ({assignee_name})\n"
                        else:
                            tasks_text += f"{priority_emoji} {task_name} - {status} ({assignee_name})\n"

                    if len(all_team_tasks) > 10:
                        tasks_text += f"\n*...and {len(all_team_tasks) - 10} more tasks*"

                    embed.add_field(
                        name="📝 Recent Tasks", value=tasks_text, inline=False
                    )

                # Overdue tasks (show top 5)
                if overdue_tasks:
                    overdue_text = ""
                    for task in overdue_tasks[:5]:
                        task_name = task.get("name", "Unnamed task")[:50]
                        member_name = task.get("_member_name", "Unknown")
                        task_url = task.get("url", "")
                        if task_url:
                            overdue_text += f"• [{task_name}]({task_url}) ({member_name})\n"
                        else:
                            overdue_text += f"• {task_name} ({member_name})\n"
                    if len(overdue_tasks) > 5:
                        overdue_text += f"• *...and {len(overdue_tasks) - 5} more*\n"
                    embed.add_field(
                        name="⚠️ Overdue Tasks", value=overdue_text, inline=False
                    )

                # Due soon (show top 5)
                if due_soon:
                    due_soon_text = ""
                    for task in due_soon[:5]:
                        task_name = task.get("name", "Unnamed task")[:50]
                        member_name = task.get("_member_name", "Unknown")
                        due_date_str = task.get("due_date")
                        due_date = datetime.datetime.fromtimestamp(
                            int(due_date_str) / 1000
                        )
                        days_until = (due_date - now).days
                        task_url = task.get("url", "")
                        if task_url:
                            due_soon_text += f"• [{task_name}]({task_url}) - {days_until}d ({member_name})\n"
                        else:
                            due_soon_text += f"• {task_name} - {days_until}d ({member_name})\n"
                    if len(due_soon) > 5:
                        due_soon_text += f"• *...and {len(due_soon) - 5} more*\n"
                    embed.add_field(
                        name="⏰ Due Soon", value=due_soon_text, inline=False
                    )

                embed.set_footer(
                    text=f"Generated by {interaction.user.name} • Use /team-report to refresh"
                )

                await interaction.followup.send(embed=embed)

                logger.info(
                    f"Generated team report for {team['name']} by {interaction.user.name}"
                )

            except Exception as e:
                logger.error(f"Failed to generate team report: {str(e)}", exc_info=True)
                await interaction.followup.send(
                    f"❌ Error generating team report: {str(e)}", ephemeral=True
                )

        return team_report
