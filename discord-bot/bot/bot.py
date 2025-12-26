"""Discord bot for team management and ClickUp integration."""

import logging
import os

import discord
from discord import app_commands
from discord.ext import commands

from bot.admin_commands import AdminCommands
from bot.config import DISCORD_BOT_TOKEN, DISCORD_GUILD_ID
from bot.onboarding import OnboardingView
from bot.project_planning import ProjectPlanningCommands
from bot.services import (
    ClickUpService,
    DiscordTeamService,
    DocsService,
    TeamMemberService,
)
from bot.task_management import TaskManagementCommands
from bot.team_management_commands import TeamManagementCommands

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TeamBot(commands.Bot):
    """Main bot class for team management."""

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(command_prefix="!", intents=intents, help_command=None)

        self.team_service = TeamMemberService()
        self.docs_service = DocsService()
        self.discord_team_service = DiscordTeamService()
        self.guild_id = int(DISCORD_GUILD_ID) if DISCORD_GUILD_ID else None
        self.admin_channel_id = (
            int(os.getenv("DISCORD_ADMIN_CHANNEL_ID"))
            if os.getenv("DISCORD_ADMIN_CHANNEL_ID")
            else None
        )
        self.alfred_channel_id = (
            int(os.getenv("DISCORD_ALFRED_CHANNEL_ID"))
            if os.getenv("DISCORD_ALFRED_CHANNEL_ID")
            else None
        )

        # Initialize project planning commands
        self.project_planning = ProjectPlanningCommands(
            self, self.team_service, self.docs_service
        )

        # Initialize task management commands
        self.task_management = TaskManagementCommands(self, self.team_service)

        # Initialize admin commands
        self.admin_commands = AdminCommands(self, self.team_service)

        # Initialize team management commands
        self.team_management = TeamManagementCommands(
            self, self.team_service, self.docs_service, self.discord_team_service
        )

    async def setup_hook(self):
        """Called when the bot is starting up."""
        # Register project planning commands
        self.project_planning.register_commands(self.tree)

        # Register task management commands
        self.task_management.register_commands(self.tree)

        # Register admin commands
        self.admin_commands.register_commands(self.tree)

        # Register team management commands
        self.team_management.register_commands(self.tree)

        # Register debug command
        self.tree.add_command(self._debug_perms_command())

        # Sync commands globally (enables DMs)
        await self.tree.sync()
        logger.info("Synced commands globally (DMs enabled)")

        # Also sync to specific guild for faster updates during development
        if self.guild_id:
            guild = discord.Object(id=self.guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logger.info(f"Synced commands to guild {self.guild_id}")

    def _debug_perms_command(self) -> app_commands.Command:
        """Create debug permissions command."""

        @app_commands.command(
            name="debug-perms",
            description="Debug: Check your permissions in this channel",
        )
        async def debug_perms(interaction: discord.Interaction):
            """Show user's permissions in current channel."""

            if not interaction.guild or not interaction.channel:
                await interaction.response.send_message(
                    "Must be in a guild channel", ephemeral=True
                )
                return

            member = interaction.guild.get_member(interaction.user.id)
            if not member:
                await interaction.response.send_message(
                    "Member not found", ephemeral=True
                )
                return

            permissions = interaction.channel.permissions_for(member)

            embed = discord.Embed(
                title="🔍 Permission Debug", color=discord.Color.blue()
            )

            embed.add_field(
                name="Channel", value=f"#{interaction.channel.name}", inline=False
            )

            embed.add_field(
                name="Channel Name (lowercase)",
                value=interaction.channel.name.lower(),
                inline=False,
            )

            embed.add_field(
                name="Manage Channels",
                value="✅ Yes" if permissions.manage_channels else "❌ No",
                inline=True,
            )

            embed.add_field(
                name="Administrator",
                value="✅ Yes" if permissions.administrator else "❌ No",
                inline=True,
            )

            # Show all roles
            roles = [role.name for role in member.roles if role.name != "@everyone"]
            embed.add_field(
                name="Your Roles",
                value=", ".join(roles) if roles else "None",
                inline=False,
            )

            # Check team detection
            channel_name = interaction.channel.name.lower()
            team_mappings = {
                "engineering": "Engineering",
                "product": "Product",
                "business": "Business",
            }

            detected_team = None
            for keyword, team in team_mappings.items():
                if keyword in channel_name:
                    detected_team = team
                    break

            embed.add_field(
                name="Detected Team",
                value=detected_team if detected_team else "❌ No team detected",
                inline=False,
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        return debug_perms

    async def on_ready(self):
        """Called when the bot has successfully connected."""
        logger.info(f"{self.user} has connected to Discord!")
        logger.info(f"Bot is in {len(self.guilds)} guilds")

    async def on_member_join(self, member: discord.Member):
        """Welcome new members in #alfred channel."""
        logger.info(f"New member joined: {member} ({member.id})")

        # Don't welcome bots
        if member.bot:
            return

        # Get alfred channel
        alfred_channel = (
            self.get_channel(self.alfred_channel_id) if self.alfred_channel_id else None
        )
        if not alfred_channel:
            logger.error("Alfred channel not configured!")
            return

        # Check if user is already onboarded
        existing_member = self.team_service.get_member_by_discord_id(member.id)
        if existing_member:
            # User is returning or already set up
            await alfred_channel.send(
                f"👋 Welcome back, {member.mention}! Your profile is already set up. Use `/setup` to view your details.",
                delete_after=30,
            )
            return

        # Check if they have a pending onboarding request
        pending = self.team_service.data_service.get_pending_onboarding_by_discord_id(
            member.id
        )
        if pending:
            await alfred_channel.send(
                f"👋 Welcome, {member.mention}! You already have an onboarding request pending approval. An admin will review it soon!",
                delete_after=30,
            )
            return

        # Send welcome message in alfred channel
        embed = discord.Embed(
            title="👋 Welcome to the Team!",
            description=(
                f"Hi {member.mention}! We're excited to have you join us.\n\n"
                f"**About Us:**\n"
                f"We're a collaborative team focused on building great things together. "
                f"This is Alfred, your AI assistant who will help you get started and stay productive.\n\n"
                f"**Let's get you onboarded!**"
            ),
            color=discord.Color.blue(),
        )

        embed.add_field(
            name="🚀 Start Your Onboarding",
            value=(
                f"Run this command to begin:\n\n"
                f"`/start-onboarding`\n\n"
                f"_(All your responses will be private - only you can see them!)_"
            ),
            inline=False,
        )

        embed.add_field(
            name="📝 What You'll Provide",
            value=(
                "• Your full name\n"
                "• Work email\n"
                "• Phone number\n"
                "• Brief bio with your skills & experience"
            ),
            inline=False,
        )

        embed.add_field(
            name="⏱️ What Happens Next",
            value=(
                "1. You submit your info\n"
                "2. Admin reviews and approves\n"
                "3. You get assigned to your team(s)\n"
                "4. You get access to team channels & resources\n"
                "5. You can set up ClickUp and other integrations"
            ),
            inline=False,
        )

        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="Ready to start? Run /start-onboarding above ⬆️")

        await alfred_channel.send(content=member.mention, embed=embed)
        logger.info(f"Sent welcome message in #alfred for {member}")


# Create bot instance
bot = TeamBot()


@bot.tree.command(
    name="start-onboarding",
    description="Start your onboarding process - provide your info for admin approval",
)
async def start_onboarding(interaction: discord.Interaction):
    """Start the onboarding flow with a modal form."""
    # Check if user is already onboarded
    existing_member = bot.team_service.get_member_by_discord_id(interaction.user.id)
    if existing_member:
        await interaction.response.send_message(
            "✅ You're already onboarded! Use `/setup` to view your profile.",
            ephemeral=True,
        )
        return

    # Allow resubmission - old pending request will be replaced in OnboardingModal
    # Show onboarding modal
    from bot.onboarding import OnboardingModal

    modal = OnboardingModal(bot.team_service, bot.docs_service)
    await interaction.response.send_modal(modal)


@bot.tree.command(
    name="setup", description="Check your onboarding status and get setup instructions"
)
async def setup(interaction: discord.Interaction):
    """Check if user profile exists and provide setup instructions."""
    await interaction.response.defer(ephemeral=True)

    discord_username = f"{interaction.user.name}#{interaction.user.discriminator}"
    if interaction.user.discriminator == "0":
        # New username format (no discriminator)
        discord_username = interaction.user.name

    logger.info(f"Setup command called by {discord_username}")

    # Check if user exists in database
    member = bot.team_service.get_member_by_discord(discord_username)

    if not member:
        embed = discord.Embed(
            title="❌ Profile Not Found",
            description=(
                f"I couldn't find a profile for **{discord_username}**.\n\n"
                "**Next Steps:**\n"
                "1. Make sure you've completed the onboarding process\n"
                "2. Verify your Discord username matches what you provided during onboarding\n"
                "3. Contact an admin if you need help"
            ),
            color=discord.Color.red(),
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    # User exists - check ClickUp setup status
    has_clickup = member.clickup_api_token is not None

    embed = discord.Embed(
        title="✅ Profile Found",
        description=f"Welcome, **{member.name}**!",
        color=discord.Color.green(),
    )

    embed.add_field(name="📧 Email", value=member.email, inline=False)

    if member.bio:
        embed.add_field(
            name="📝 Bio",
            value=member.bio[:100] + "..." if len(member.bio) > 100 else member.bio,
            inline=False,
        )

    if has_clickup:
        embed.add_field(
            name="✅ ClickUp Integration",
            value="Your ClickUp account is connected! Use `/my-tasks` to view your tasks.",
            inline=False,
        )
    else:
        embed.add_field(
            name="⚠️ ClickUp Integration",
            value=(
                "Not set up yet.\n\n"
                "**To connect ClickUp:**\n"
                "1. Get your ClickUp API token from [ClickUp Settings](https://app.clickup.com/settings/apps)\n"
                "2. Use `/setup-clickup <your_token>` to save it"
            ),
            inline=False,
        )

    if member.profile_url:
        embed.add_field(
            name="📄 Profile Document",
            value=f"[View your profile]({member.profile_url})",
            inline=False,
        )

    await interaction.followup.send(embed=embed, ephemeral=True)


@bot.tree.command(
    name="setup-clickup",
    description="Connect your ClickUp account to view and manage tasks",
)
@app_commands.describe(
    token="Your ClickUp API token (Get it: app.clickup.com/settings/apps → Apps → API Token → Generate/Copy)"
)
async def setup_clickup(interaction: discord.Interaction, token: str):
    """Save and validate ClickUp API token."""
    await interaction.response.defer(ephemeral=True)

    # Send helpful guide if user seems confused
    if not token or token.lower() in ["help", "how", "where", "?"]:
        guide_embed = discord.Embed(
            title="📖 How to Get Your ClickUp API Token",
            description="Follow these steps to connect your ClickUp account:",
            color=discord.Color.blue(),
        )
        guide_embed.add_field(
            name="Step 1: Open ClickUp Settings",
            value="Go to [ClickUp Settings](https://app.clickup.com/settings/apps)",
            inline=False,
        )
        guide_embed.add_field(
            name="Step 2: Navigate to API Token",
            value="Click on **'Apps'** in the left sidebar, then **'API Token'**",
            inline=False,
        )
        guide_embed.add_field(
            name="Step 3: Generate or Copy Token",
            value="Click **'Generate'** to create a new token, or **'Copy'** if you already have one",
            inline=False,
        )
        guide_embed.add_field(
            name="Step 4: Run the Command",
            value="Run `/setup-clickup <paste_your_token_here>`",
            inline=False,
        )
        guide_embed.set_footer(text="🔒 Your token is stored securely and never shared")
        await interaction.followup.send(embed=guide_embed, ephemeral=True)
        return

    discord_username = f"{interaction.user.name}#{interaction.user.discriminator}"
    if interaction.user.discriminator == "0":
        discord_username = interaction.user.name

    logger.info(f"Setup ClickUp command called by {discord_username}")

    # Check if user exists
    member = bot.team_service.get_member_by_discord(discord_username)

    if not member:
        embed = discord.Embed(
            title="❌ Profile Not Found",
            description=(
                "You need to complete the onboarding process first.\n"
                "Use `/setup` to check your status."
            ),
            color=discord.Color.red(),
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    # Validate the token
    clickup_service = ClickUpService(token)
    is_valid, error_message = await clickup_service.validate_token()

    if not is_valid:
        embed = discord.Embed(
            title="❌ Invalid Token",
            description=f"Failed to validate your ClickUp token:\n{error_message}",
            color=discord.Color.red(),
        )
        embed.add_field(
            name="How to get your token",
            value=(
                "1. Go to [ClickUp Settings](https://app.clickup.com/settings/apps)\n"
                "2. Click 'Generate' under API Token\n"
                "3. Copy the token and try again"
            ),
            inline=False,
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    # Get user info from ClickUp
    user_info = await clickup_service.get_user_info()

    # Save the token
    updated_member = bot.team_service.update_clickup_token(discord_username, token)

    if not updated_member:
        embed = discord.Embed(
            title="❌ Error",
            description="Failed to save your ClickUp token. Please try again.",
            color=discord.Color.red(),
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    embed = discord.Embed(
        title="✅ ClickUp Connected",
        description="Your ClickUp API token has been saved successfully!",
        color=discord.Color.green(),
    )

    if user_info:
        embed.add_field(
            name="Connected as",
            value=f"{user_info.get('username', 'Unknown')}",
            inline=False,
        )

    embed.add_field(
        name="Next Steps",
        value=(
            "• Use `/my-tasks <list_id>` to view your tasks\n"
            "• Your token is stored securely and never shown again\n"
            "• You can update it anytime by running this command again"
        ),
        inline=False,
    )

    await interaction.followup.send(embed=embed, ephemeral=True)


@bot.tree.command(name="my-tasks", description="View all your assigned ClickUp tasks")
async def my_tasks(interaction: discord.Interaction):
    """Fetch and display user's ClickUp tasks across all teams and lists."""
    await interaction.response.defer(ephemeral=True)

    discord_username = f"{interaction.user.name}#{interaction.user.discriminator}"
    if interaction.user.discriminator == "0":
        discord_username = interaction.user.name

    logger.info(f"My tasks command called by {discord_username}")

    # Get user profile
    member = bot.team_service.get_member_by_discord(discord_username)

    if not member:
        embed = discord.Embed(
            title="❌ Profile Not Found",
            description="Use `/setup` to check your onboarding status.",
            color=discord.Color.red(),
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    if not member.clickup_api_token:
        embed = discord.Embed(
            title="❌ ClickUp Not Connected",
            description="You need to connect your ClickUp account first.\nUse `/setup-clickup <token>` to get started.",
            color=discord.Color.red(),
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    # Get team based on channel context to filter by project lists
    # If run in a team channel, only show tasks from that team's configured lists
    list_ids = None
    channel_team = None

    # Check if current channel is a team channel
    if interaction.channel:
        teams = bot.team_service.data_service.list_teams()
        for team in teams:
            if (
                team.discord_general_channel_id == interaction.channel.id
                or team.discord_standup_channel_id == interaction.channel.id
            ):
                channel_team = team
                break

    # Filter by channel's team if in team channel, otherwise use user's team
    if channel_team:
        list_ids = bot.team_service.data_service.get_team_list_ids(channel_team.id)
        if list_ids:
            logger.info(
                f"Filtering tasks for {discord_username} by {len(list_ids)} project lists for channel team {channel_team.name}"
            )
    elif member.team:
        list_ids = bot.team_service.data_service.get_team_list_ids_by_name(member.team)
        if list_ids:
            logger.info(
                f"Filtering tasks for {discord_username} by {len(list_ids)} project lists for user team {member.team}"
            )

    # Fetch tasks from task-service
    import os

    from bot.clients.task_client import TaskServiceClient

    task_client = TaskServiceClient(
        base_url=os.getenv("TASK_SERVICE_URL", "http://localhost:8002")
    )

    result = await task_client.get_user_tasks(str(interaction.user.id))
    tasks = result.get("tasks", []) if result else []

    if not tasks:
        embed = discord.Embed(
            title="📋 No Tasks Found",
            description="You don't have any tasks assigned across your teams.",
            color=discord.Color.blue(),
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    # Create embed with tasks
    description = "All tasks assigned to you"
    if channel_team and list_ids:
        description += f" from **{channel_team.name}** team lists"
    elif list_ids:
        description += f" from **{member.team}** team lists"
    else:
        description += " across all your ClickUp teams"

    embed = discord.Embed(
        title=f"📋 Your Tasks ({len(tasks)})",
        description=description,
        color=discord.Color.blue(),
    )

    for task in tasks[:10]:  # Limit to 10 tasks to avoid hitting embed limits
        task_id = task.get("id", "")
        status = task.get("status", {}).get("status", "Unknown")
        priority = task.get("priority")
        due_date = task.get("due_date")

        field_value = f"**ID:** `{task_id}`\n**Status:** {status}\n"

        if priority:
            priority_emoji = {"1": "🔴", "2": "🟡", "3": "🔵", "4": "⚪"}.get(
                str(priority.get("id", "")), ""
            )
            field_value += (
                f"**Priority:** {priority_emoji} {priority.get('priority', 'None')}\n"
            )

        if due_date:
            import datetime

            due_timestamp = int(due_date) // 1000
            due = datetime.datetime.fromtimestamp(due_timestamp)
            field_value += f"**Due:** {due.strftime('%Y-%m-%d')}\n"

        task_url = task.get("url")
        if task_url:
            field_value += f"[View Task]({task_url})"

        # Add helpful hint for first task
        if tasks.index(task) == 0:
            field_value += f"\n\n💡 Use `/task-info {task_id}` for details"

        embed.add_field(
            name=task.get("name", "Untitled")[:256],
            value=field_value[:1024],
            inline=False,
        )

    if len(tasks) > 10:
        embed.set_footer(text=f"Showing 10 of {len(tasks)} tasks")

    await interaction.followup.send(embed=embed, ephemeral=True)


@bot.tree.command(
    name="resend-approval",
    description="[Admin] Resend approval notification for a pending request",
)
@app_commands.describe(request_id="The UUID of the pending onboarding request")
async def resend_approval(interaction: discord.Interaction, request_id: str):
    """Resend admin approval notification."""
    await interaction.response.defer(ephemeral=True)

    try:
        from uuid import UUID

        from bot.onboarding import ApprovalView

        req_uuid = UUID(request_id)

        # Get pending request
        pending = bot.team_service.data_service.get_pending_onboarding(req_uuid)

        if not pending:
            await interaction.followup.send(
                f"❌ No pending request found with ID: {request_id}", ephemeral=True
            )
            return

        if pending.status.value != "pending":
            await interaction.followup.send(
                f"⚠️ Request is {pending.status.value}, not pending", ephemeral=True
            )
            return

        # Get admin channel
        if not bot.admin_channel_id:
            await interaction.followup.send(
                "❌ Admin channel not configured", ephemeral=True
            )
            return

        admin_channel = bot.get_channel(bot.admin_channel_id)
        if not admin_channel:
            await interaction.followup.send(
                "❌ Could not find admin channel", ephemeral=True
            )
            return

        # Get Discord user
        discord_user = await bot.fetch_user(pending.discord_id)

        # Create embed
        embed = discord.Embed(
            title="🆕 New Onboarding Request",
            description=f"**{discord_user.mention}** wants to join the team!",
            color=discord.Color.blue(),
        )

        embed.add_field(name="Discord User", value=str(discord_user), inline=False)
        embed.add_field(name="Name", value=pending.name, inline=True)
        embed.add_field(name="Email", value=pending.email, inline=True)

        if pending.phone:
            embed.add_field(name="Phone", value=pending.phone, inline=True)

        embed.add_field(name="Bio & Experience", value=pending.bio[:1024], inline=False)
        embed.set_thumbnail(url=discord_user.display_avatar.url)
        embed.set_footer(text=f"Request ID: {req_uuid}")

        # Create view
        view = ApprovalView(
            req_uuid, pending.discord_id, bot.team_service, bot.docs_service
        )

        # Send
        message = await admin_channel.send(embed=embed, view=view)

        await interaction.followup.send(
            f"✅ Resent approval notification\nJump to: {message.jump_url}",
            ephemeral=True,
        )

    except Exception as e:
        logger.error(f"Error resending approval: {e}", exc_info=True)
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)


@bot.tree.command(
    name="help", description="Show available commands and how to use the bot"
)
async def help_command(interaction: discord.Interaction):
    """Display role-based help information."""

    # Check if user is onboarded
    member = bot.team_service.get_member_by_discord_id(interaction.user.id)
    is_admin = (
        interaction.user.guild_permissions.administrator if interaction.guild else False
    )

    embed = discord.Embed(
        title="🤖 Alfred Bot - Command Guide",
        description="Commands available to you based on your role:",
        color=discord.Color.blue(),
    )

    # Commands for everyone (including non-onboarded)
    if not member:
        embed.add_field(
            name="🚀 Getting Started",
            value=(
                "**`/start-onboarding`**\n"
                "Begin your onboarding process. You'll provide your name, email, "
                "phone, and a brief bio. An admin will review and approve you.\n"
            ),
            inline=False,
        )
        embed.add_field(
            name="ℹ️ General Commands",
            value=("**`/help`** - Show this help message\n"),
            inline=False,
        )
        embed.set_footer(
            text="👆 Start with /start-onboarding to get access to more features!"
        )
    else:
        # Onboarded member commands
        embed.add_field(
            name="👤 Your Profile",
            value=(
                "**`/setup`**\n"
                "View your profile, team assignments, and onboarding status\n"
            ),
            inline=False,
        )

        embed.add_field(
            name="📋 ClickUp Integration",
            value=(
                "**`/setup-clickup`**\n"
                "Connect your ClickUp account to view and manage tasks\n"
                "📌 **How to get your API token:**\n"
                "1. Go to [ClickUp Settings](https://app.clickup.com/settings/apps)\n"
                "2. Click 'Apps' → 'API Token'\n"
                "3. Click 'Generate' or copy existing token\n"
                "4. Run `/setup-clickup` and paste your token\n\n"
                "**`/my-tasks`**\n"
                "View all tasks assigned to you across teams\n\n"
                "**`/task-info <task_id>`**\n"
                "Get detailed info about a task including comments\n\n"
                "**`/task-comment <task_id> <comment>`**\n"
                "Add a comment/update to a ClickUp task\n"
            ),
            inline=False,
        )

        embed.add_field(
            name="🎨 Project Planning (AI)",
            value=(
                "**`/brainstorm <idea>`**\n"
                "Generate an AI-powered project plan from your idea\n\n"
                "**`/my-projects`**\n"
                "List all your brainstorming sessions\n"
            ),
            inline=False,
        )

    # Admin-only commands
    if is_admin:
        embed.add_field(
            name="⚙️ Admin Commands",
            value=(
                "**`/create-team <name> <description> <lead>`**\n"
                "Create a new team with Discord roles, channels, and Drive folder\n\n"
                "**`/assign-lead <team> <member>`**\n"
                "Assign a team lead to a team\n\n"
                "**`/add-list-id <team>`**\n"
                "Track ClickUp lists for team task filtering\n"
                "📌 **How to get List ID:**\n"
                "1. Open your list in ClickUp\n"
                "2. Look at the URL: `https://app.clickup.com/.../list/[LIST_ID]`\n"
                "3. Copy the LIST_ID number\n"
                "4. Run `/add-list-id` and paste it\n\n"
                "**`/resend-approval <request_id>`**\n"
                "Resend an approval prompt for pending onboarding\n"
            ),
            inline=False,
        )

    embed.add_field(
        name="💡 Tips",
        value=(
            "• All commands work in DMs or server channels\n"
            "• Responses are private (ephemeral) by default\n"
            "• Type `/` to see all available commands with autocomplete\n"
        ),
        inline=False,
    )

    if member:
        embed.set_footer(
            text=f"Logged in as: {member.name} | Need help? Ask in #admin-notifications"
        )
    else:
        embed.set_footer(text="Not onboarded yet? Run /start-onboarding to begin!")

    await interaction.response.send_message(embed=embed, ephemeral=True)


def main():
    """Run the bot."""
    try:
        logger.info("Starting bot...")
        bot.run(DISCORD_BOT_TOKEN)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise


if __name__ == "__main__":
    main()
