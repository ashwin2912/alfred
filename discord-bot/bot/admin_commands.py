"""Discord admin commands for managing project lists and team configuration."""

import logging
from typing import Optional

import discord
from discord import app_commands

logger = logging.getLogger(__name__)


class AdminCommands:
    """
    Discord admin commands for project and team management.

    Only accessible to Team Leads and above.
    """

    def __init__(self, bot, team_service):
        """
        Initialize admin commands.

        Args:
            bot: Discord bot instance
            team_service: TeamMemberService instance
        """
        self.bot = bot
        self.team_service = team_service

        logger.info("AdminCommands initialized")

    def register_commands(self, tree: app_commands.CommandTree):
        """
        Register commands with the bot's command tree.

        Args:
            tree: Discord command tree
        """
        tree.add_command(self._add_project_list_command())
        tree.add_command(self._list_project_lists_command())
        tree.add_command(self._remove_project_list_command())
        logger.info("Admin commands registered")

    async def _check_admin_access(
        self, interaction: discord.Interaction
    ) -> tuple[bool, Optional[str]]:
        """
        Check if user has admin access (Team Lead or above).

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

        # Check for Team Lead roles
        admin_roles = [
            "Engineering Team Lead",
            "Product Team Lead",
            "Business Team Lead",
            "Team Lead",
            "Manager",
            "Director",
            "Executive",
        ]

        user_roles = [role.name for role in member.roles]
        # Check exact role matches or roles ending with " Manager" (team-specific managers)
        has_access = any(role in user_roles for role in admin_roles) or any(
            role.endswith(" Manager") for role in user_roles
        )

        if not has_access:
            return False, "This command requires Team Lead role or higher."

        return True, None

    def _add_project_list_command(self) -> app_commands.Command:
        """Create the /add-project-list command."""

        @app_commands.command(
            name="add-project-list",
            description="[Admin] Add a ClickUp list to your team's project tracking",
        )
        @app_commands.describe(
            list_id="ClickUp list ID - Find it in your ClickUp list URL: .../list/[THIS_NUMBER]",
            list_name="Name of the list (e.g., 'Q1 Projects', 'Sprint Backlog')",
            description="Optional description of this list",
        )
        async def add_project_list(
            interaction: discord.Interaction,
            list_id: str,
            list_name: str,
            description: Optional[str] = None,
        ):
            """
            Add a ClickUp list to track for a team.

            Only tasks from configured lists will be shown in /my-tasks
            for team members.
            """
            await interaction.response.defer(ephemeral=True)

            # Send helpful guide if user seems confused
            if not list_id or list_id.lower() in ["help", "how", "where", "?"]:
                guide_embed = discord.Embed(
                    title="📖 How to Find Your ClickUp List ID",
                    description="Follow these steps to find the List ID:",
                    color=discord.Color.blue(),
                )
                guide_embed.add_field(
                    name="Step 1: Open Your List in ClickUp",
                    value="Navigate to the list you want to track in ClickUp",
                    inline=False,
                )
                guide_embed.add_field(
                    name="Step 2: Look at the URL",
                    value=(
                        "The URL will look like:\n"
                        "`https://app.clickup.com/12345/v/li/901234567`\n\n"
                        "The List ID is the number after `/li/`: **901234567**"
                    ),
                    inline=False,
                )
                guide_embed.add_field(
                    name="Step 3: Copy the List ID",
                    value="Copy just the numeric List ID (e.g., `901234567`)",
                    inline=False,
                )
                guide_embed.add_field(
                    name="Step 4: Run the Command",
                    value=(
                        "Run this command in your team channel:\n"
                        '`/add-project-list list_id:901234567 list_name:"My List"`'
                    ),
                    inline=False,
                )
                guide_embed.set_footer(
                    text="💡 Must be run in a team channel (e.g., #engineering-general)"
                )
                await interaction.followup.send(embed=guide_embed, ephemeral=True)
                return

            try:
                # Check admin access
                has_access, error_msg = await self._check_admin_access(interaction)
                if not has_access:
                    error_embed = discord.Embed(
                        title="❌ Access Denied",
                        description=error_msg,
                        color=discord.Color.red(),
                    )
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                    return

                # Infer team from channel
                channel = interaction.channel
                team = None

                if channel:
                    # Try to match channel to team
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
                            team = t
                            break

                if not team:
                    error_embed = discord.Embed(
                        title="❌ Not a Team Channel",
                        description="This command must be run in a team channel (e.g., #engineering-general or #engineering-standups)",
                        color=discord.Color.red(),
                    )
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                    return

                team_name = team["name"]
                team_id = team["id"]

                logger.info(
                    f"Add project list called by {interaction.user} for team {team_name}"
                )

                # Add the list
                try:
                    result = self.team_service.data_service.add_clickup_list(
                        clickup_list_id=list_id,
                        list_name=list_name,
                        team_id=team_id,
                        description=description,
                    )

                    success_embed = discord.Embed(
                        title="✅ Project List Added",
                        description=f"Successfully added ClickUp list to **{team_name}** team",
                        color=discord.Color.green(),
                    )

                    success_embed.add_field(
                        name="List Name", value=list_name, inline=True
                    )
                    success_embed.add_field(
                        name="List ID", value=f"`{list_id}`", inline=True
                    )
                    success_embed.add_field(name="Team", value=team_name, inline=True)

                    if description:
                        success_embed.add_field(
                            name="Description", value=description, inline=False
                        )

                    success_embed.add_field(
                        name="📝 Note",
                        value=f"Team members will now only see tasks from configured project lists in `/my-tasks`",
                        inline=False,
                    )

                    await interaction.followup.send(embed=success_embed, ephemeral=True)
                    logger.info(
                        f"Added list {list_id} ({list_name}) to team {team_name}"
                    )

                except Exception as e:
                    error_embed = discord.Embed(
                        title="❌ Failed to Add List",
                        description=f"Error: {str(e)}\n\nThis list may already be added.",
                        color=discord.Color.red(),
                    )
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                    logger.error(f"Error adding list: {e}")

            except Exception as e:
                logger.error(f"Error in add-project-list command: {e}", exc_info=True)
                error_embed = discord.Embed(
                    title="❌ Error",
                    description=f"Failed to add project list: {str(e)}",
                    color=discord.Color.red(),
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)

        return add_project_list

    def _list_project_lists_command(self) -> app_commands.Command:
        """Create the /list-project-lists command."""

        @app_commands.command(
            name="list-project-lists",
            description="[Admin] View all configured ClickUp lists for a team",
        )
        @app_commands.describe(
            team_name="Team name (Engineering, Product, Business) - leave empty for all teams"
        )
        async def list_project_lists(
            interaction: discord.Interaction, team_name: Optional[str] = None
        ):
            """
            List all configured project lists for a team.
            """
            await interaction.response.defer(ephemeral=True)

            try:
                # Check admin access
                has_access, error_msg = await self._check_admin_access(interaction)
                if not has_access:
                    error_embed = discord.Embed(
                        title="❌ Access Denied",
                        description=error_msg,
                        color=discord.Color.red(),
                    )
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                    return

                logger.info(
                    f"List project lists called by {interaction.user} for team {team_name}"
                )

                if team_name:
                    # Get lists for specific team
                    lists = (
                        self.team_service.data_service.get_team_clickup_lists_by_name(
                            team_name
                        )
                    )

                    if not lists:
                        info_embed = discord.Embed(
                            title=f"📋 {team_name} Project Lists",
                            description=f"No project lists configured for **{team_name}** team.\n\n"
                            "Use `/add-project-list` to add lists.",
                            color=discord.Color.blue(),
                        )
                        await interaction.followup.send(
                            embed=info_embed, ephemeral=True
                        )
                        return

                    embed = discord.Embed(
                        title=f"📋 {team_name} Project Lists ({len(lists)})",
                        description=f"Configured ClickUp lists for **{team_name}** team",
                        color=discord.Color.blue(),
                    )

                    for lst in lists:
                        field_value = f"**ID:** `{lst['clickup_list_id']}`\n"
                        if lst.get("description"):
                            field_value += f"{lst['description']}\n"
                        field_value += f"**Status:** {'✅ Active' if lst['is_active'] else '⏸️ Inactive'}"

                        embed.add_field(
                            name=lst["list_name"], value=field_value, inline=False
                        )

                else:
                    # Get all teams and their lists
                    teams_response = (
                        self.team_service.data_service.client.table("teams")
                        .select("id, name")
                        .execute()
                    )

                    if not teams_response.data:
                        info_embed = discord.Embed(
                            title="📋 Project Lists",
                            description="No teams found.",
                            color=discord.Color.blue(),
                        )
                        await interaction.followup.send(
                            embed=info_embed, ephemeral=True
                        )
                        return

                    embed = discord.Embed(
                        title="📋 All Project Lists",
                        description="Configured ClickUp lists by team",
                        color=discord.Color.blue(),
                    )

                    for team in teams_response.data:
                        lists = self.team_service.data_service.get_team_clickup_lists_by_name(
                            team["name"]
                        )

                        if lists:
                            list_items = [
                                f"• `{lst['clickup_list_id']}` - {lst['list_name']}"
                                for lst in lists
                            ]
                            field_value = "\n".join(list_items)
                            embed.add_field(
                                name=f"{team['name']} ({len(lists)} lists)",
                                value=field_value,
                                inline=False,
                            )

                await interaction.followup.send(embed=embed, ephemeral=True)
                logger.info("Project lists displayed successfully")

            except Exception as e:
                logger.error(f"Error in list-project-lists command: {e}", exc_info=True)
                error_embed = discord.Embed(
                    title="❌ Error",
                    description=f"Failed to fetch project lists: {str(e)}",
                    color=discord.Color.red(),
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)

        return list_project_lists

    def _remove_project_list_command(self) -> app_commands.Command:
        """Create the /remove-project-list command."""

        @app_commands.command(
            name="remove-project-list",
            description="[Admin] Remove a ClickUp list from team tracking",
        )
        @app_commands.describe(list_id="ClickUp list ID to remove")
        async def remove_project_list(interaction: discord.Interaction, list_id: str):
            """
            Remove (deactivate) a ClickUp list from team tracking.

            This will hide tasks from this list in /my-tasks.
            """
            await interaction.response.defer(ephemeral=True)

            try:
                # Check admin access
                has_access, error_msg = await self._check_admin_access(interaction)
                if not has_access:
                    error_embed = discord.Embed(
                        title="❌ Access Denied",
                        description=error_msg,
                        color=discord.Color.red(),
                    )
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                    return

                logger.info(
                    f"Remove project list called by {interaction.user} for list {list_id}"
                )

                # Deactivate the list
                success = self.team_service.data_service.deactivate_clickup_list(
                    list_id
                )

                if success:
                    success_embed = discord.Embed(
                        title="✅ Project List Removed",
                        description=f"List `{list_id}` has been deactivated.\n\n"
                        "Team members will no longer see tasks from this list in `/my-tasks`.",
                        color=discord.Color.green(),
                    )
                    await interaction.followup.send(embed=success_embed, ephemeral=True)
                    logger.info(f"Deactivated list {list_id}")
                else:
                    error_embed = discord.Embed(
                        title="❌ List Not Found",
                        description=f"Could not find list with ID: `{list_id}`\n\n"
                        "Use `/list-project-lists` to see configured lists.",
                        color=discord.Color.red(),
                    )
                    await interaction.followup.send(embed=error_embed, ephemeral=True)

            except Exception as e:
                logger.error(
                    f"Error in remove-project-list command: {e}", exc_info=True
                )
                error_embed = discord.Embed(
                    title="❌ Error",
                    description=f"Failed to remove project list: {str(e)}",
                    color=discord.Color.red(),
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)

        return remove_project_list
