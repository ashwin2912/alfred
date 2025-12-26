"""Discord commands for AI-powered project planning (HTTP client)."""

import logging
import os
from typing import Any, Dict, Optional

import discord
import httpx
from discord import app_commands

logger = logging.getLogger(__name__)


class ProjectPlanningCommands:
    """
    Discord commands for project planning.

    Makes HTTP requests to the AI Core Service.
    """

    def __init__(self, bot, team_service, docs_service):
        """
        Initialize project planning commands.

        Args:
            bot: Discord bot instance
            team_service: TeamMemberService instance
            docs_service: DocsService instance
        """
        self.bot = bot
        self.team_service = team_service
        self.docs_service = docs_service

        # Get AI Core Service URL from env
        self.api_url = os.getenv("AI_CORE_SERVICE_URL", "http://localhost:8001")
        self.planning_folder_id = os.getenv("GOOGLE_DRIVE_PROJECT_PLANNING_FOLDER_ID")

        # HTTP client for API calls
        self.http_client = httpx.AsyncClient(
            timeout=120.0
        )  # 2 min timeout for AI processing

        logger.info(f"ProjectPlanningCommands initialized (API: {self.api_url})")

    def register_commands(self, tree: app_commands.CommandTree):
        """
        Register commands with the bot's command tree.

        Args:
            tree: Discord command tree
        """
        tree.add_command(self._brainstorm_command())
        tree.add_command(self._my_projects_command())
        tree.add_command(self._publish_project_command())
        logger.info("Project planning commands registered")

    async def _check_channel_manager_access(
        self, interaction: discord.Interaction
    ) -> Optional[Dict[str, Any]]:
        """
        Check if user can manage the current channel and get team info.

        Command must be run in a team channel, and user must have Manage Channels permission.

        Returns dict with team_name, role_name, folder_id if authorized, None otherwise.
        """
        if not interaction.guild or not interaction.channel:
            return None

        member = interaction.guild.get_member(interaction.user.id)
        if not member:
            return None

        # Check if user has Manage Channels permission in current channel
        permissions = interaction.channel.permissions_for(member)
        if not permissions.manage_channels:
            return None

        # Get all teams from database
        try:
            teams_response = (
                self.team_service.data_service.client.table("teams")
                .select("name, drive_folder_id")
                .execute()
            )

            if not teams_response.data:
                return None

            # Get channel name to match against team names
            channel_name = interaction.channel.name.lower()

            # Find matching team by checking if team name appears in channel name
            team_name = None
            team_folder_id = None

            for team in teams_response.data:
                team_name_lower = team["name"].lower()
                if team_name_lower in channel_name:
                    team_name = team["name"]
                    team_folder_id = team.get("drive_folder_id")
                    break

            if not team_name or not team_folder_id:
                return None

            return {
                "team_name": team_name,
                "role_name": f"{team_name} Manager",
                "folder_id": team_folder_id,
            }

        except Exception as e:
            logger.error(f"Error fetching teams from database: {e}")
            return None

    def _brainstorm_command(self) -> app_commands.Command:
        """Create the /brainstorm command."""

        @app_commands.command(
            name="brainstorm",
            description="[Team Channel Manager] Generate an AI-powered project plan from your idea",
        )
        @app_commands.describe(
            project_idea="Describe your project idea (be as detailed as possible)"
        )
        async def brainstorm(interaction: discord.Interaction, project_idea: str):
            """
            Generate a complete project plan from a project idea.

            The AI will analyze your idea and create:
            - Project goals and scope
            - Milestones and timeline
            - Detailed tasks with skill requirements
            - Risk assessment
            - A formatted Google Doc with the full plan

            **Access:** Must be run in a team channel with Manage Channels permission
            **Document Location:** Your team's Google Drive folder
            """
            await interaction.response.defer(ephemeral=True)

            try:
                logger.info(
                    f"Brainstorm command called by {interaction.user} in {interaction.channel.name}"
                )

                # Check if user can manage current channel (team permission)
                team_info = await self._check_channel_manager_access(interaction)
                if not team_info:
                    error_embed = discord.Embed(
                        title="❌ Access Denied",
                        description=(
                            "This command requires:\n\n"
                            "1. Run in a team channel (#engineering-*, #product-*, #business-*)\n"
                            "2. You must have **Manage Channels** permission in this channel\n\n"
                            "Only team managers can create project plans."
                        ),
                        color=discord.Color.red(),
                    )
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                    return

                team_name = team_info["team_name"]
                role_name = team_info["role_name"]
                folder_id = team_info["folder_id"]

                logger.info(
                    f"Access granted: {role_name} for {team_name} team (folder: {folder_id})"
                )

                # Create initial embed
                embed = discord.Embed(
                    title="🧠 AI Project Brainstorming",
                    description=f"Analyzing your project idea for **{team_name}** team...",
                    color=discord.Color.blue(),
                )
                embed.add_field(
                    name="Your Idea",
                    value=project_idea[:1000]
                    + ("..." if len(project_idea) > 1000 else ""),
                    inline=False,
                )
                embed.add_field(
                    name="Team", value=f"{team_name} ({role_name})", inline=True
                )
                embed.add_field(
                    name="Document Location",
                    value=f"{team_name} Team Folder",
                    inline=True,
                )

                await interaction.followup.send(embed=embed, ephemeral=True)

                # Call planning API with team context
                logger.info("Calling project planning API...")
                response = await self.http_client.post(
                    f"{self.api_url}/brainstorm",
                    json={
                        "project_idea": project_idea,
                        "discord_user_id": interaction.user.id,
                        "discord_username": str(interaction.user),
                        "google_drive_folder_id": folder_id,  # Use team's folder
                        "team_name": team_name,
                        "role_name": role_name,
                    },
                )

                response.raise_for_status()
                result = response.json()

                # Create success embed
                success_embed = discord.Embed(
                    title=f"✅ {result['title']}",
                    description=f"Your project breakdown is ready for the **{team_name}** team!",
                    color=discord.Color.green(),
                )

                success_embed.add_field(
                    name="📄 Your Project Breakdown",
                    value=f"[Open in Google Docs]({result['doc_url']})\n*Saved in {team_name} Team Folder*",
                    inline=False,
                )

                success_embed.add_field(
                    name="🎯 Next Steps",
                    value=(
                        f"1. **Review** the breakdown in Google Docs\n"
                        f"2. **Edit** the tasks and milestones as needed\n"
                        f"3. **Keep the format** - it will be parsed to create ClickUp tasks\n"
                        f"4. When ready, use a command to publish tasks to ClickUp (coming soon)"
                    ),
                    inline=False,
                )

                success_embed.set_footer(
                    text=f"Project ID: {result['brainstorm_id']} | Team: {team_name}"
                )

                await interaction.edit_original_response(embed=success_embed)

                logger.info(
                    f"Project brainstorm created successfully: {result['brainstorm_id']} for {team_name}"
                )

            except httpx.HTTPStatusError as e:
                logger.error(f"API error: {e.response.status_code} - {e.response.text}")
                error_embed = discord.Embed(
                    title="❌ API Error",
                    description=f"Failed to generate project plan: {e.response.status_code}\n{e.response.text[:500]}",
                    color=discord.Color.red(),
                )
                await interaction.edit_original_response(embed=error_embed)

            except Exception as e:
                logger.error(f"Error in brainstorm command: {e}", exc_info=True)
                error_embed = discord.Embed(
                    title="❌ Error",
                    description=f"Failed to generate project plan: {str(e)}",
                    color=discord.Color.red(),
                )
                await interaction.edit_original_response(embed=error_embed)

        return brainstorm

    def _my_projects_command(self) -> app_commands.Command:
        """Create the /my-projects command."""

        @app_commands.command(
            name="my-projects", description="List all your project brainstorms"
        )
        async def my_projects(interaction: discord.Interaction):
            """List all project brainstorms created by the user."""
            await interaction.response.defer(ephemeral=True)

            try:
                logger.info(f"My projects command called by {interaction.user}")

                # Call planning API
                response = await self.http_client.get(
                    f"{self.api_url}/projects/{interaction.user.id}"
                )

                response.raise_for_status()
                result = response.json()

                projects = result["projects"]

                if not projects:
                    embed = discord.Embed(
                        title="📋 Your Projects",
                        description="You haven't created any project plans yet.\n\nUse `/brainstorm <your idea>` to get started!",
                        color=discord.Color.blue(),
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return

                # Create embed with projects
                embed = discord.Embed(
                    title=f"📋 Your Projects ({len(projects)})",
                    description="Here are all your project brainstorms:",
                    color=discord.Color.blue(),
                )

                for project in projects[:10]:  # Limit to 10 to avoid embed limits
                    field_value = ""

                    # Team
                    if project.get("team_name"):
                        field_value += f"**Team:** {project['team_name']}\n"

                    # Doc link
                    if project.get("doc_url"):
                        field_value += f"[View Breakdown]({project['doc_url']})\n"

                    # ClickUp status
                    if project.get("clickup_list_id"):
                        field_value += f"✅ Published to ClickUp\n"
                    else:
                        field_value += f"📝 Draft - Not yet published\n"

                    # Created date
                    field_value += (
                        f"**Created:** {project.get('created_at', 'Unknown')[:10]}\n"
                    )
                    field_value += f"**ID:** `{project.get('id')}`"

                    embed.add_field(
                        name=project.get("title", "Untitled Project"),
                        value=field_value,
                        inline=False,
                    )

                if len(projects) > 10:
                    embed.set_footer(text=f"Showing 10 of {len(projects)} projects")

                await interaction.followup.send(embed=embed, ephemeral=True)

            except httpx.HTTPStatusError as e:
                logger.error(f"API error: {e.response.status_code} - {e.response.text}")
                error_embed = discord.Embed(
                    title="❌ API Error",
                    description=f"Failed to fetch projects: {e.response.status_code}",
                    color=discord.Color.red(),
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)

            except Exception as e:
                logger.error(f"Error in my-projects command: {e}", exc_info=True)
                error_embed = discord.Embed(
                    title="❌ Error",
                    description=f"Failed to fetch your projects: {str(e)}",
                    color=discord.Color.red(),
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)

        return my_projects

    def _publish_project_command(self) -> app_commands.Command:
        """Create the /publish-project command."""

        @app_commands.command(
            name="publish-project",
            description="[Team Channel Manager] Publish project plan to ClickUp",
        )
        @app_commands.describe(
            project_id="Project ID from /my-projects",
            clickup_list_id="(Optional) ClickUp List ID - leave blank to choose from team lists",
        )
        async def publish_project(
            interaction: discord.Interaction,
            project_id: str,
            clickup_list_id: str = None,
        ):
            """
            Publish an AI-generated project plan to ClickUp.

            Parses the Google Doc and creates tasks automatically.
            If multiple ClickUp lists are configured for your team, you'll be prompted to choose one.
            """
            await interaction.response.defer(ephemeral=True)

            try:
                logger.info(
                    f"Publish project command called by {interaction.user} for project {project_id}"
                )

                # Check if user can manage current channel (team permission)
                team_info = await self._check_channel_manager_access(interaction)
                if not team_info:
                    error_embed = discord.Embed(
                        title="❌ Access Denied",
                        description=(
                            "This command requires:\n\n"
                            "1. Run in a team channel\n"
                            "2. You must have **Manage Channels** permission\n\n"
                            "Only team managers can publish projects."
                        ),
                        color=discord.Color.red(),
                    )
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                    return

                team_name = team_info["team_name"]

                # Get team member to fetch ClickUp token
                member = self.team_service.get_member_by_discord_id(interaction.user.id)
                if not member or not member.clickup_api_token:
                    error_embed = discord.Embed(
                        title="❌ ClickUp Not Connected",
                        description=(
                            "You need to connect your ClickUp account first.\n\n"
                            "Use `/setup-clickup <your_api_token>` to connect."
                        ),
                        color=discord.Color.red(),
                    )
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                    return

                # If no list_id provided, fetch team's configured lists
                if not clickup_list_id:
                    team_lists = (
                        self.team_service.data_service.client.table("clickup_lists")
                        .select("clickup_list_id, list_name")
                        .eq(
                            "team_id",
                            (
                                self.team_service.data_service.client.table("teams")
                                .select("id")
                                .eq("name", team_name)
                                .execute()
                            ).data[0]["id"],
                        )
                        .eq("is_active", True)
                        .execute()
                    )

                    if not team_lists.data:
                        error_embed = discord.Embed(
                            title="❌ No ClickUp Lists Configured",
                            description=(
                                f"No ClickUp lists are configured for {team_name} team.\n\n"
                                f"Ask an admin to configure lists with `/add-project-list`\n"
                                f"Or provide a list ID: `/publish-project {project_id} <list_id>`"
                            ),
                            color=discord.Color.red(),
                        )
                        await interaction.followup.send(
                            embed=error_embed, ephemeral=True
                        )
                        return

                    # If multiple lists, let user choose
                    if len(team_lists.data) > 1:
                        # TODO: Show selection UI
                        list_options = "\n".join(
                            [
                                f"• {lst['list_name']} (`{lst['clickup_list_id']}`)"
                                for lst in team_lists.data
                            ]
                        )
                        error_embed = discord.Embed(
                            title="📋 Multiple Lists Available",
                            description=(
                                f"Your team has multiple ClickUp lists:\n\n"
                                f"{list_options}\n\n"
                                f"Please run the command again with a specific list:\n"
                                f"`/publish-project {project_id} <list_id>`"
                            ),
                            color=discord.Color.blue(),
                        )
                        await interaction.followup.send(
                            embed=error_embed, ephemeral=True
                        )
                        return

                    # Use the single configured list
                    clickup_list_id = team_lists.data[0]["clickup_list_id"]

                # Call planning API to publish
                logger.info(
                    f"Publishing project {project_id} to ClickUp list {clickup_list_id}"
                )

                response = await self.http_client.post(
                    f"{self.api_url}/publish-project",
                    json={
                        "brainstorm_id": project_id,
                        "clickup_list_id": clickup_list_id,
                        "clickup_api_token": member.clickup_api_token,
                        "team_name": team_name,
                    },
                    timeout=120.0,  # Publishing can take time
                )

                response.raise_for_status()
                result = response.json()

                # Success embed
                success_embed = discord.Embed(
                    title="✅ Project Published to ClickUp",
                    description=f"Successfully created tasks in ClickUp!",
                    color=discord.Color.green(),
                )
                success_embed.add_field(
                    name="Tasks Created",
                    value=result.get("tasks_created", 0),
                    inline=True,
                )
                success_embed.add_field(
                    name="Tasks Assigned",
                    value=result.get("tasks_assigned", 0),
                    inline=True,
                )
                if result.get("clickup_list_url"):
                    success_embed.add_field(
                        name="View in ClickUp",
                        value=f"[Open List]({result['clickup_list_url']})",
                        inline=False,
                    )

                await interaction.followup.send(embed=success_embed, ephemeral=True)

            except httpx.HTTPStatusError as e:
                logger.error(f"API error: {e.response.status_code} - {e.response.text}")
                error_embed = discord.Embed(
                    title="❌ API Error",
                    description=f"Failed to publish project: {e.response.text}",
                    color=discord.Color.red(),
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)

            except Exception as e:
                logger.error(f"Error in publish-project command: {e}", exc_info=True)
                error_embed = discord.Embed(
                    title="❌ Error",
                    description=f"Failed to publish project: {str(e)}",
                    color=discord.Color.red(),
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)

        return publish_project
