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

    Makes HTTP requests to the Project Planning API service.
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

        # Get planning API URL from env
        self.api_url = os.getenv("PROJECT_PLANNING_API_URL", "http://localhost:8001")
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
        logger.info("Project planning commands registered")

    async def _check_team_lead_access(
        self, interaction: discord.Interaction
    ) -> Optional[Dict[str, Any]]:
        """
        Check if user has Team Lead role and get their team info.

        Returns dict with team_name, role_name, folder_id if authorized, None otherwise.
        """
        if not interaction.guild:
            return None

        member = interaction.guild.get_member(interaction.user.id)
        if not member:
            return None

        # Define team lead role patterns
        team_lead_roles = {
            "Engineering Team Lead": "Engineering",
            "Product Team Lead": "Product",
            "Business Team Lead": "Business",
            "Engineering": "Engineering",  # Fallback to just team name
            "Product": "Product",
            "Business": "Business",
        }

        # Check user's roles
        for role in member.roles:
            if role.name in team_lead_roles:
                team_name = team_lead_roles[role.name]

                # Get team folder from database
                try:
                    team = (
                        self.team_service.data_service.client.table("teams")
                        .select("drive_folder_id, name")
                        .eq("name", team_name)
                        .execute()
                    )

                    if team.data and team.data[0].get("drive_folder_id"):
                        return {
                            "team_name": team_name,
                            "role_name": role.name,
                            "folder_id": team.data[0]["drive_folder_id"],
                        }
                except Exception as e:
                    logger.error(f"Error fetching team folder: {e}")

        return None

    def _brainstorm_command(self) -> app_commands.Command:
        """Create the /brainstorm command."""

        @app_commands.command(
            name="brainstorm",
            description="[Team Lead only] Generate an AI-powered project plan from your idea",
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

            **Access:** Team Lead role required
            **Document Location:** Your team's Google Drive folder
            """
            await interaction.response.defer(ephemeral=True)

            try:
                logger.info(f"Brainstorm command called by {interaction.user}")

                # Check if user has Team Lead role
                team_info = await self._check_team_lead_access(interaction)
                if not team_info:
                    error_embed = discord.Embed(
                        title="❌ Access Denied",
                        description=(
                            "This command is only available to Team Leads.\n\n"
                            "**Required roles:**\n"
                            "• Engineering Team Lead\n"
                            "• Product Team Lead\n"
                            "• Business Team Lead"
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
                    field_value += f"**Created:** {project.get('created_at', 'Unknown')[:10]}\n"
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
