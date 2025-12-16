"""Discord commands for ClickUp task management."""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

import discord
from discord import app_commands

logger = logging.getLogger(__name__)


class TaskManagementCommands:
    """
    Discord commands for task management.

    Handles task details viewing and commenting with hooks for future rate limiting.
    """

    def __init__(self, bot, team_service):
        """
        Initialize task management commands.

        Args:
            bot: Discord bot instance
            team_service: TeamMemberService instance
        """
        self.bot = bot
        self.team_service = team_service

        # Future: Add rate limiting here
        # self.rate_limiter = RateLimiter(max_calls=100, period=3600)  # 100 calls/hour

        logger.info("TaskManagementCommands initialized")

    def register_commands(self, tree: app_commands.CommandTree):
        """
        Register commands with the bot's command tree.

        Args:
            tree: Discord command tree
        """
        tree.add_command(self._task_info_command())
        tree.add_command(self._task_comment_command())
        logger.info("Task management commands registered")

    async def _check_rate_limit(self, user_id: int) -> tuple[bool, Optional[str]]:
        """
        Check if user has exceeded rate limits.

        Args:
            user_id: Discord user ID

        Returns:
            tuple: (is_allowed, error_message)
        """
        # Future: Implement actual rate limiting
        # For now, always allow
        return True, None

        # Future implementation:
        # if not self.rate_limiter.check_limit(user_id):
        #     remaining_time = self.rate_limiter.get_reset_time(user_id)
        #     return False, f"Rate limit exceeded. Try again in {remaining_time} seconds."
        # return True, None

    def _format_task_embed(self, task: dict, comments: list[dict]) -> discord.Embed:
        """
        Format a task and its comments into a Discord embed.

        Args:
            task: Task dictionary from ClickUp API
            comments: List of comment dictionaries

        Returns:
            Discord embed with formatted task information
        """
        # Extract task details
        task_name = task.get("name", "Untitled Task")
        task_id = task.get("id", "")
        description = task.get("description", "No description")
        status = task.get("status", {}).get("status", "Unknown")
        priority = task.get("priority")
        due_date = task.get("due_date")
        assignees = task.get("assignees", [])
        tags = task.get("tags", [])
        time_estimate = task.get("time_estimate")
        task_url = task.get("url", "")

        # Create embed
        embed = discord.Embed(
            title=f"📋 {task_name}",
            description=description[:500] + ("..." if len(description) > 500 else ""),
            color=discord.Color.blue(),
            url=task_url if task_url else None,
        )

        # Add status
        status_emoji = {
            "to do": "📝",
            "in progress": "🔄",
            "review": "👀",
            "done": "✅",
            "closed": "🔒",
        }
        status_lower = status.lower()
        emoji = status_emoji.get(status_lower, "📌")
        embed.add_field(name="Status", value=f"{emoji} {status}", inline=True)

        # Add priority
        if priority:
            priority_emoji = {"1": "🔴", "2": "🟡", "3": "🔵", "4": "⚪"}.get(
                str(priority.get("id", "")), "⚪"
            )
            priority_text = priority.get("priority", "None")
            embed.add_field(
                name="Priority", value=f"{priority_emoji} {priority_text}", inline=True
            )

        # Add due date
        if due_date:
            try:
                due_timestamp = int(due_date) // 1000
                due = datetime.fromtimestamp(due_timestamp)
                due_str = due.strftime("%Y-%m-%d %H:%M")

                # Check if overdue
                now = datetime.now()
                if due < now:
                    due_str = f"⚠️ {due_str} (Overdue)"

                embed.add_field(name="Due Date", value=due_str, inline=True)
            except Exception:
                pass

        # Add assignees
        if assignees:
            assignee_names = [a.get("username", "Unknown") for a in assignees]
            embed.add_field(
                name="Assignees",
                value=", ".join(assignee_names[:3])
                + ("..." if len(assignee_names) > 3 else ""),
                inline=True,
            )

        # Add time estimate
        if time_estimate:
            hours = time_estimate // 3600000  # Convert ms to hours
            minutes = (time_estimate % 3600000) // 60000
            if hours > 0:
                estimate_str = f"{hours}h {minutes}m"
            else:
                estimate_str = f"{minutes}m"
            embed.add_field(name="Estimate", value=estimate_str, inline=True)

        # Add tags
        if tags:
            tag_names = [t.get("name", "") for t in tags]
            embed.add_field(
                name="Tags",
                value=", ".join(tag_names[:5]) + ("..." if len(tag_names) > 5 else ""),
                inline=True,
            )

        # Add comments section
        if comments:
            comments_text = ""
            # Show last 3 comments
            for comment in comments[-3:]:
                commenter = comment.get("user", {}).get("username", "Unknown")
                text = comment.get("comment_text", "")
                date = comment.get("date")

                if date:
                    try:
                        date_timestamp = int(date) // 1000
                        date_obj = datetime.fromtimestamp(date_timestamp)
                        date_str = date_obj.strftime("%m/%d %H:%M")
                    except Exception:
                        date_str = ""
                else:
                    date_str = ""

                # Truncate long comments
                if len(text) > 100:
                    text = text[:100] + "..."

                comments_text += f"**{commenter}** {date_str}\n{text}\n\n"

            if len(comments) > 3:
                comments_text += f"_...and {len(comments) - 3} more comments_"

            embed.add_field(
                name=f"💬 Recent Comments ({len(comments)} total)",
                value=comments_text[:1024],
                inline=False,
            )
        else:
            embed.add_field(
                name="💬 Comments",
                value="_No comments yet_",
                inline=False,
            )

        # Add footer with task ID
        embed.set_footer(text=f"Task ID: {task_id}")

        return embed

    def _task_info_command(self) -> app_commands.Command:
        """Create the /task-info command."""

        @app_commands.command(
            name="task-info",
            description="View detailed information about a ClickUp task with comments",
        )
        @app_commands.describe(
            task_id="The ClickUp task ID (you can copy from task URL or /my-tasks)"
        )
        async def task_info(interaction: discord.Interaction, task_id: str):
            """
            Display detailed information about a specific task.

            Shows:
            - Task description and status
            - Priority, due date, assignees
            - Time estimates and tags
            - Recent comments (last 3)
            - Link to view in ClickUp
            """
            await interaction.response.defer(ephemeral=True)

            try:
                logger.info(
                    f"Task info command called by {interaction.user} for task {task_id}"
                )

                # Check rate limit
                is_allowed, error_msg = await self._check_rate_limit(
                    interaction.user.id
                )
                if not is_allowed:
                    error_embed = discord.Embed(
                        title="⚠️ Rate Limit Exceeded",
                        description=error_msg,
                        color=discord.Color.orange(),
                    )
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                    return

                # Get user's Discord username
                discord_username = (
                    f"{interaction.user.name}#{interaction.user.discriminator}"
                )
                if interaction.user.discriminator == "0":
                    discord_username = interaction.user.name

                # Get user profile
                member = self.team_service.get_member_by_discord(discord_username)

                if not member:
                    error_embed = discord.Embed(
                        title="❌ Profile Not Found",
                        description="Use `/setup` to check your onboarding status.",
                        color=discord.Color.red(),
                    )
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                    return

                if not member.clickup_api_token:
                    error_embed = discord.Embed(
                        title="❌ ClickUp Not Connected",
                        description="You need to connect your ClickUp account first.\nUse `/setup-clickup <token>` to get started.",
                        color=discord.Color.red(),
                    )
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                    return

                # Import ClickUpService here to avoid circular imports
                from bot.services import ClickUpService

                clickup_service = ClickUpService(member.clickup_api_token)

                # Fetch task details
                logger.info(f"Fetching task details for {task_id}")
                task = await clickup_service.get_task_details(task_id)

                if not task:
                    error_embed = discord.Embed(
                        title="❌ Task Not Found",
                        description=f"Could not find task with ID: `{task_id}`\n\n"
                        "Make sure:\n"
                        "• The task ID is correct\n"
                        "• You have access to this task\n"
                        "• The task exists in ClickUp",
                        color=discord.Color.red(),
                    )
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                    return

                # Fetch comments
                logger.info(f"Fetching comments for task {task_id}")
                comments = await clickup_service.get_task_comments(task_id)

                # Create and send embed
                embed = self._format_task_embed(task, comments)
                await interaction.followup.send(embed=embed, ephemeral=True)

                logger.info(f"Task info displayed successfully for {task_id}")

            except Exception as e:
                logger.error(f"Error in task-info command: {e}", exc_info=True)
                error_embed = discord.Embed(
                    title="❌ Error",
                    description=f"Failed to fetch task information: {str(e)}",
                    color=discord.Color.red(),
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)

        return task_info

    def _task_comment_command(self) -> app_commands.Command:
        """Create the /task-comment command."""

        @app_commands.command(
            name="task-comment",
            description="Add a comment/update to a ClickUp task",
        )
        @app_commands.describe(
            task_id="The ClickUp task ID",
            comment="Your comment or update about the task",
        )
        async def task_comment(
            interaction: discord.Interaction, task_id: str, comment: str
        ):
            """
            Post a comment to a ClickUp task.

            Use this to:
            - Update task progress
            - Ask questions or clarify requirements
            - Share status updates with the team
            - Document blockers or issues
            """
            await interaction.response.defer(ephemeral=True)

            try:
                logger.info(
                    f"Task comment command called by {interaction.user} for task {task_id}"
                )

                # Check rate limit
                is_allowed, error_msg = await self._check_rate_limit(
                    interaction.user.id
                )
                if not is_allowed:
                    error_embed = discord.Embed(
                        title="⚠️ Rate Limit Exceeded",
                        description=error_msg,
                        color=discord.Color.orange(),
                    )
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                    return

                # Get user's Discord username
                discord_username = (
                    f"{interaction.user.name}#{interaction.user.discriminator}"
                )
                if interaction.user.discriminator == "0":
                    discord_username = interaction.user.name

                # Get user profile
                member = self.team_service.get_member_by_discord(discord_username)

                if not member:
                    error_embed = discord.Embed(
                        title="❌ Profile Not Found",
                        description="Use `/setup` to check your onboarding status.",
                        color=discord.Color.red(),
                    )
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                    return

                if not member.clickup_api_token:
                    error_embed = discord.Embed(
                        title="❌ ClickUp Not Connected",
                        description="You need to connect your ClickUp account first.\nUse `/setup-clickup <token>` to get started.",
                        color=discord.Color.red(),
                    )
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                    return

                # Import ClickUpService here to avoid circular imports
                from bot.services import ClickUpService

                clickup_service = ClickUpService(member.clickup_api_token)

                # Add Discord context to comment
                discord_tag = f"\n\n_Posted from Discord by {interaction.user.mention}_"
                full_comment = comment + discord_tag

                # Post comment
                logger.info(f"Posting comment to task {task_id}")
                result = await clickup_service.post_task_comment(task_id, full_comment)

                if not result:
                    error_embed = discord.Embed(
                        title="❌ Failed to Post Comment",
                        description=f"Could not post comment to task `{task_id}`\n\n"
                        "Make sure:\n"
                        "• The task ID is correct\n"
                        "• You have permission to comment on this task\n"
                        "• The task exists in ClickUp",
                        color=discord.Color.red(),
                    )
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                    return

                # Success response
                success_embed = discord.Embed(
                    title="✅ Comment Posted",
                    description=f"Your comment has been added to the task!",
                    color=discord.Color.green(),
                )

                success_embed.add_field(
                    name="Task ID",
                    value=f"`{task_id}`",
                    inline=False,
                )

                success_embed.add_field(
                    name="Your Comment",
                    value=comment[:500] + ("..." if len(comment) > 500 else ""),
                    inline=False,
                )

                # Get task details to show link
                task = await clickup_service.get_task_details(task_id)
                if task and task.get("url"):
                    success_embed.add_field(
                        name="View Task",
                        value=f"[Open in ClickUp]({task['url']})",
                        inline=False,
                    )

                await interaction.followup.send(embed=success_embed, ephemeral=True)

                logger.info(f"Comment posted successfully to task {task_id}")

            except Exception as e:
                logger.error(f"Error in task-comment command: {e}", exc_info=True)
                error_embed = discord.Embed(
                    title="❌ Error",
                    description=f"Failed to post comment: {str(e)}",
                    color=discord.Color.red(),
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)

        return task_comment
