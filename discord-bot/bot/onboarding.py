"""Discord onboarding system with modals and admin approval."""

import logging
from typing import Optional
from uuid import UUID

import discord
from data_service.models import (
    ExperienceLevel,
    OnboardingApproval,
    PendingOnboardingCreate,
    Skill,
)
from discord import app_commands

from bot.services import TeamMemberService

logger = logging.getLogger(__name__)


class OnboardingModal(discord.ui.Modal, title="Team Onboarding"):
    """Interactive onboarding modal for new members."""

    name = discord.ui.TextInput(
        label="Full Name",
        placeholder="John Doe",
        required=True,
        max_length=255,
    )

    email = discord.ui.TextInput(
        label="Work Email",
        placeholder="john@company.com",
        required=True,
        max_length=255,
    )

    phone = discord.ui.TextInput(
        label="Phone Number",
        placeholder="+1 (555) 123-4567",
        required=False,
        max_length=50,
    )

    bio = discord.ui.TextInput(
        label="Bio: Skills & Experience",
        style=discord.TextStyle.paragraph,
        placeholder="e.g., 5 years Python, worked at Google, skilled in Django, PostgreSQL...",
        required=True,
        max_length=1000,
    )

    def __init__(self, team_service: TeamMemberService, docs_service=None):
        super().__init__()
        self.team_service = team_service
        self.docs_service = docs_service

    async def on_submit(self, interaction: discord.Interaction):
        """Handle form submission."""
        await interaction.response.defer(ephemeral=True)

        try:
            # Check if user already has a pending request
            existing_pending = (
                self.team_service.data_service.get_pending_onboarding_by_discord_id(
                    interaction.user.id
                )
            )

            # Create pending onboarding request
            onboarding_data = PendingOnboardingCreate(
                discord_id=interaction.user.id,
                discord_username=str(interaction.user),
                name=self.name.value,
                email=self.email.value,
                phone=self.phone.value if self.phone.value else None,
                team=None,  # Admin will assign during approval
                bio=self.bio.value,
            )

            # If existing pending request, update it instead of creating new
            if existing_pending and existing_pending.status.value == "pending":
                logger.info(f"Updating existing pending request: {existing_pending.id}")
                # Delete old request and create new one (simpler than update)
                self.team_service.data_service.client.table(
                    "pending_onboarding"
                ).delete().eq("id", str(existing_pending.id)).execute()
                pending = self.team_service.data_service.create_pending_onboarding(
                    onboarding_data
                )
            else:
                # Save to database
                pending = self.team_service.data_service.create_pending_onboarding(
                    onboarding_data
                )

            logger.info(
                f"Onboarding request created: {pending.id} for {interaction.user}"
            )

            # Send confirmation to user
            embed = discord.Embed(
                title="✅ Onboarding Request Submitted",
                description="Thanks for submitting your information!",
                color=discord.Color.green(),
            )

            embed.add_field(name="Name", value=self.name.value, inline=False)
            embed.add_field(name="Email", value=self.email.value, inline=False)
            if self.phone.value:
                embed.add_field(name="Phone", value=self.phone.value, inline=False)

            embed.add_field(
                name="⏳ Next Steps",
                value=(
                    "Your request has been sent to the admins for approval.\n"
                    "You'll receive a DM once it's been reviewed!"
                ),
                inline=False,
            )

            embed.set_footer(text=f"Request ID: {pending.id}")

            await interaction.followup.send(embed=embed, ephemeral=True)

            # Notify admins
            await self.send_admin_notification(interaction, pending.id)

        except Exception as e:
            logger.error(f"Error creating onboarding request: {e}")
            await interaction.followup.send(
                f"❌ Error: {str(e)}\nPlease try again or contact an admin.",
                ephemeral=True,
            )

    async def send_admin_notification(
        self, interaction: discord.Interaction, request_id: UUID
    ):
        """Send notification to admin channel for approval."""
        # Get admin channel (set in bot config)
        admin_channel_id = interaction.client.admin_channel_id
        if not admin_channel_id:
            logger.warning("No admin channel configured")
            return

        admin_channel = interaction.client.get_channel(admin_channel_id)
        if not admin_channel:
            logger.warning(f"Admin channel {admin_channel_id} not found")
            return

        # Create approval embed
        embed = discord.Embed(
            title="🆕 New Onboarding Request",
            description=f"**{interaction.user.mention}** wants to join the team!",
            color=discord.Color.blue(),
        )

        embed.add_field(name="Discord User", value=str(interaction.user), inline=False)
        embed.add_field(name="Name", value=self.name.value, inline=True)
        embed.add_field(name="Email", value=self.email.value, inline=True)

        if self.phone.value:
            embed.add_field(name="Phone", value=self.phone.value, inline=True)

        embed.add_field(
            name="Bio & Experience", value=self.bio.value[:1024], inline=False
        )

        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text=f"Request ID: {request_id}")

        # Add approval buttons
        view = ApprovalView(
            request_id, interaction.user.id, self.team_service, self.docs_service
        )

        await admin_channel.send(embed=embed, view=view)


class OnboardingView(discord.ui.View):
    """View with button to start onboarding."""

    def __init__(self, team_service: TeamMemberService):
        super().__init__(timeout=None)
        self.team_service = team_service

    @discord.ui.button(label="📋 Start Onboarding", style=discord.ButtonStyle.primary)
    async def start_onboarding(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Open onboarding modal."""
        # Check if user is already onboarded (approved)
        member = self.team_service.get_member_by_discord_id(interaction.user.id)
        if member:
            await interaction.response.send_message(
                "✅ You're already onboarded! Use `/setup` to view your profile.",
                ephemeral=True,
            )
            return

        # Allow resubmission - old pending request will be replaced
        # Show modal
        modal = OnboardingModal(self.team_service)
        await interaction.response.send_modal(modal)


class TeamSelectionView(discord.ui.View):
    """View for selecting team during approval."""

    def __init__(
        self,
        request_id: UUID,
        user_id: int,
        team_service: TeamMemberService,
        docs_service,
        original_message,
    ):
        super().__init__(timeout=300)  # 5 minute timeout
        self.request_id = request_id
        self.user_id = user_id
        self.team_service = team_service
        self.docs_service = docs_service
        self.original_message = original_message
        self.selected_team = None

        # Load teams from database dynamically
        self._setup_team_select()

    def _setup_team_select(self):
        """Setup team select dropdown with teams from database."""
        try:
            # Get all teams from database
            from data_service.client import DataService

            # Query teams table
            teams_response = (
                self.team_service.data_service.client.table("teams")
                .select("name")
                .execute()
            )

            # Build options from database teams
            options = []
            team_emojis = {
                "Engineering": "⚙️",
                "Product": "📱",
                "Business": "💼",
                "Data": "📊",
                "AI": "🤖",
                "Marketing": "📢",
                "Sales": "💰",
            }

            for team in teams_response.data:
                team_name = team["name"]
                emoji = team_emojis.get(team_name, "👥")
                options.append(
                    discord.SelectOption(label=team_name, value=team_name, emoji=emoji)
                )

            # Always add "None" option at the end
            options.append(
                discord.SelectOption(label="None (No Team)", value="None", emoji="➖")
            )

            # Create the select menu
            select = discord.ui.Select(
                placeholder="Select Team (or None)",
                options=options,
                custom_id="team_select",
            )
            select.callback = self.team_select
            self.add_item(select)

        except Exception as e:
            logger.error(f"Error loading teams for dropdown: {e}")
            # Fallback to default teams
            select = discord.ui.Select(
                placeholder="Select Team (or None)",
                options=[
                    discord.SelectOption(
                        label="Engineering", value="Engineering", emoji="⚙️"
                    ),
                    discord.SelectOption(label="Product", value="Product", emoji="📱"),
                    discord.SelectOption(
                        label="Business", value="Business", emoji="💼"
                    ),
                    discord.SelectOption(
                        label="None (No Team)", value="None", emoji="➖"
                    ),
                ],
                custom_id="team_select",
            )
            select.callback = self.team_select
            self.add_item(select)

    async def team_select(self, interaction: discord.Interaction):
        """Handle team selection."""
        # Get the select component
        select = [
            item for item in self.children if isinstance(item, discord.ui.Select)
        ][0]
        self.selected_team = select.values[0]
        logger.info(f"Team selected: {self.selected_team}")

        # Now show role input modal
        modal = RoleInputModal(
            self.request_id,
            self.user_id,
            self.selected_team,
            self.team_service,
            self.docs_service,
            self.original_message,
        )
        await interaction.response.send_modal(modal)


class RoleInputModal(discord.ui.Modal, title="Assign Role"):
    """Modal to input role after team is selected."""

    role = discord.ui.TextInput(
        label="Role (optional)",
        placeholder="e.g., Software Engineer, Product Manager",
        required=False,
        max_length=50,
    )

    def __init__(
        self,
        request_id: UUID,
        user_id: int,
        team: str,
        team_service: TeamMemberService,
        docs_service,
        original_message,
    ):
        super().__init__()
        self.request_id = request_id
        self.user_id = user_id
        self.team = team
        self.team_service = team_service
        self.docs_service = docs_service
        self.original_message = original_message

    async def on_submit(self, interaction: discord.Interaction):
        """Process approval with team and role."""
        # Call the same logic as the old TeamRoleSelectionModal
        # but with self.team and self.role.value
        await self._process_approval(interaction, self.team, self.role.value)

    async def _process_approval(
        self, interaction: discord.Interaction, team: str, role: str
    ):
        """Handle the approval process."""
        await interaction.response.defer(ephemeral=True)

        try:
            logger.info(
                f"Approval submitted by {interaction.user} for request {self.request_id}"
            )

            # Get the pending request
            pending = self.team_service.data_service.get_pending_onboarding(
                self.request_id
            )

            if not pending:
                logger.error(f"Request {self.request_id} not found")
                await interaction.followup.send(
                    "❌ Onboarding request not found.", ephemeral=True
                )
                return

            logger.info(
                f"Found pending request: {pending.name}, status: {pending.status}"
            )

            if pending.status.value != "pending":
                logger.warning(
                    f"Request {self.request_id} already {pending.status.value}"
                )
                await interaction.followup.send(
                    f"⚠️ This request has already been {pending.status.value}.",
                    ephemeral=True,
                )
                return

            # Get admin's team member record
            logger.info(
                f"Looking up admin member for Discord ID: {interaction.user.id}"
            )
            admin_member = self.team_service.get_member_by_discord_id(
                interaction.user.id
            )
            if not admin_member:
                logger.error(f"Admin profile not found for {interaction.user}")
                await interaction.followup.send(
                    "❌ Could not find your admin profile. You need to be onboarded first to approve others.",
                    ephemeral=True,
                )
                return

            logger.info(f"Admin member found: {admin_member.name}")

            # Approve the request in database
            approval = OnboardingApproval(request_id=self.request_id, approved=True)
            self.team_service.data_service.approve_onboarding(approval, admin_member.id)

            # Create Supabase auth user automatically
            from uuid import uuid4

            from data_service.models import TeamMemberCreate

            supabase_user_id = None
            temp_password = None

            try:
                supabase_user_id, temp_password = (
                    self.team_service.data_service.create_supabase_user(
                        email=pending.email, name=pending.name
                    )
                )
                logger.info(f"Created Supabase user: {supabase_user_id}")
            except Exception as e:
                logger.error(f"Error creating Supabase user: {e}")
                # Continue with temporary UUID if Supabase creation fails
                supabase_user_id = uuid4()

            # Create team_members record
            team_member_data = TeamMemberCreate(
                user_id=supabase_user_id,
                discord_id=pending.discord_id,
                discord_username=pending.discord_username,
                name=pending.name,
                email=pending.email,
                phone=pending.phone,
                bio=pending.bio,
            )

            try:
                new_member = self.team_service.data_service.create_team_member(
                    team_member_data
                )
                logger.info(f"Created team_members record: {new_member.id}")
            except Exception as e:
                logger.error(f"Error creating team_members record: {e}")

            # Create Google Doc profile and add to team roster
            doc_url = None
            doc_id = None
            roster_added = False

            # Only create team-specific resources if a team was assigned
            if team != "None" and self.docs_service.is_available():
                try:
                    # Create member profile in Team Management folder
                    member_data = {
                        "name": pending.name,
                        "email": pending.email,
                        "phone": pending.phone or "Not provided",
                        "team": team,
                        "role": role or "To be assigned",
                        "bio": pending.bio,
                    }
                    profile_result = self.docs_service.create_team_member_profile(
                        member_data, team
                    )
                    if profile_result:
                        doc_url = profile_result["url"]
                        doc_id = profile_result["doc_id"]
                        logger.info(f"Created Google Doc profile: {doc_url}")

                        # Get team from database to get roster sheet ID
                        db_team = self.team_service.data_service.get_team_by_name(team)
                        if db_team:
                            # Add member to team via team_memberships table
                            try:
                                self.team_service.data_service.add_member_to_team(
                                    new_member.id, db_team.id, role=role
                                )
                                logger.info(
                                    f"Added {pending.name} to team {team} in database"
                                )
                            except Exception as e:
                                logger.error(f"Error adding to team_memberships: {e}")

                            # Add to team roster spreadsheet
                            if db_team.roster_sheet_id:
                                try:
                                    roster_added = (
                                        self.docs_service.add_member_to_roster(
                                            roster_sheet_id=db_team.roster_sheet_id,
                                            member_name=pending.name,
                                            discord_username=pending.discord_username,
                                            email=pending.email,
                                            role=role or "TBD",
                                            profile_url=doc_url,
                                        )
                                    )
                                    if roster_added:
                                        logger.info(
                                            f"Added {pending.name} to {team} roster"
                                        )
                                except Exception as e:
                                    logger.error(f"Error adding to roster: {e}")
                            else:
                                logger.warning(
                                    f"Team {team} does not have roster_sheet_id set"
                                )
                        else:
                            logger.warning(f"Team {team} not found in database")
                except Exception as e:
                    logger.error(f"Error creating Google Doc: {e}")
            elif team == "None":
                logger.info(
                    f"No team assigned to {pending.name}, skipping team-specific setup"
                )

            # Update the approval message
            original_embed = self.original_message.embeds[0]
            original_embed.color = discord.Color.green()
            original_embed.title = f"✅ Approved by {interaction.user.name}"
            original_embed.add_field(name="Assigned Team", value=team, inline=True)
            if role:
                original_embed.add_field(name="Assigned Role", value=role, inline=True)
            if doc_url:
                profile_status = "✅ Profile created"
                if roster_added:
                    profile_status += " & added to team roster"
                original_embed.add_field(
                    name="📄 " + profile_status,
                    value=f"[View Profile Document]({doc_url})",
                    inline=False,
                )

            await self.original_message.edit(embed=original_embed, view=None)

            # Send admin todo checklist
            admin_checklist = discord.Embed(
                title="📋 Admin Action Items",
                description=f"**For:** {pending.name} ({pending.email})",
                color=discord.Color.blue(),
            )

            admin_checklist.add_field(
                name="1️⃣ Team Member Record",
                value=f"✅ Created in database\nEmail: `{pending.email}`",
                inline=False,
            )

            # Supabase user field
            if temp_password:
                admin_checklist.add_field(
                    name="2️⃣ Supabase User",
                    value=(
                        f"✅ Automatically created\n"
                        f"Email: `{pending.email}`\n"
                        f"Temp Password: `{temp_password}`\n"
                        f"**Send credentials to user securely**"
                    ),
                    inline=False,
                )
            else:
                admin_checklist.add_field(
                    name="2️⃣ Create Supabase User",
                    value=f"⚠️ Auto-creation failed - create manually in Supabase dashboard\nEmail: `{pending.email}`",
                    inline=False,
                )

            admin_checklist.add_field(
                name="3️⃣ Add to ClickUp",
                value=(
                    f"Email: `{pending.email}`\n"
                    f"Team: {team}\n"
                    f"Role: {role if role else 'TBD'}\n"
                    f"⚠️ **ACTION REQUIRED:** Add this user to ClickUp workspace manually"
                ),
                inline=False,
            )

            # Assign Discord roles based on team
            role_assigned = False
            if team != "None":
                try:
                    guild = interaction.guild
                    member = guild.get_member(self.user_id)
                    if member:
                        team_role = discord.utils.get(guild.roles, name=team)
                        if team_role:
                            await member.add_roles(team_role)
                            role_assigned = True
                            logger.info(f"Assigned {team} role to {member.name}")
                        else:
                            logger.warning(f"Role '{team}' not found in guild")
                except Exception as e:
                    logger.error(f"Error assigning Discord role: {e}")

                if role_assigned:
                    admin_checklist.add_field(
                        name="4️⃣ Discord Roles",
                        value=f"✅ Assigned {team} role",
                        inline=False,
                    )
                else:
                    admin_checklist.add_field(
                        name="4️⃣ Discord Roles",
                        value=f"⚠️ Could not find '{team}' role - assign manually",
                        inline=False,
                    )
            else:
                admin_checklist.add_field(
                    name="4️⃣ Discord Roles",
                    value="➖ No team assigned - use `/add-to-team` later",
                    inline=False,
                )

            if doc_url:
                admin_checklist.add_field(
                    name="5️⃣ Google Doc Profile",
                    value=f"✅ Created: [View Document]({doc_url})",
                    inline=False,
                )
            else:
                admin_checklist.add_field(
                    name="5️⃣ Create Google Doc Profile",
                    value="⚠️ Google Docs not configured - create manually",
                    inline=False,
                )

            await interaction.followup.send(embed=admin_checklist, ephemeral=True)

            # Notify the user
            try:
                discord_user = await interaction.client.fetch_user(self.user_id)

                if team != "None":
                    user_embed = discord.Embed(
                        title="🎉 Welcome to the Team!",
                        description="Your onboarding request has been approved!",
                        color=discord.Color.green(),
                    )

                    user_embed.add_field(
                        name="Your Assignment",
                        value=f"**Team:** {team}\n**Role:** {role if role else 'To be assigned'}",
                        inline=False,
                    )

                    next_steps = "1. You'll be added to ClickUp\n"

                    if role_assigned:
                        next_steps += f"2. ✅ You've been assigned the {team} role\n"
                    else:
                        next_steps += "2. You'll get team role access soon\n"

                    next_steps += "3. Use `/setup` in #alfred to view your profile"

                    user_embed.add_field(
                        name="What's Next?",
                        value=next_steps,
                        inline=False,
                    )
                else:
                    # No team assigned
                    user_embed = discord.Embed(
                        title="✅ Onboarding Approved!",
                        description="Your onboarding request has been approved. You'll be assigned to a team soon.",
                        color=discord.Color.green(),
                    )

                    next_steps = (
                        "1. Your account has been created\n"
                        "2. You'll be assigned to a team by an admin\n"
                        "3. Use `/setup` in #alfred to view your profile"
                    )

                    user_embed.add_field(
                        name="What's Next?",
                        value=next_steps,
                        inline=False,
                    )

                user_embed.set_footer(text="Looking forward to working with you! 🚀")

                await discord_user.send(embed=user_embed)
            except Exception as e:
                logger.warning(f"Could not DM user {self.user_id}: {e}")

        except Exception as e:
            logger.error(f"Error approving onboarding: {e}")
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)


class ApprovalView(discord.ui.View):
    """Admin buttons for approving/rejecting onboarding."""

    def __init__(
        self,
        request_id: UUID,
        user_id: int,
        team_service: TeamMemberService,
        docs_service,
    ):
        super().__init__(timeout=None)
        self.request_id = request_id
        self.user_id = user_id
        self.team_service = team_service
        self.docs_service = docs_service

    @discord.ui.button(label="✅ Approve", style=discord.ButtonStyle.green)
    async def approve(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Approve the onboarding request (no team assignment yet)."""
        await interaction.response.defer(ephemeral=True)

        try:
            logger.info(f"Approve button clicked by {interaction.user}")

            # Get the pending request
            pending = self.team_service.data_service.get_pending_onboarding(
                self.request_id
            )
            if not pending:
                await interaction.followup.send(
                    "❌ Onboarding request not found.", ephemeral=True
                )
                return

            if pending.status.value != "pending":
                await interaction.followup.send(
                    f"⚠️ This request has already been {pending.status.value}.",
                    ephemeral=True,
                )
                return

            # Get admin's team member record
            admin_member = self.team_service.get_member_by_discord_id(
                interaction.user.id
            )
            if not admin_member:
                await interaction.followup.send(
                    "❌ Could not find your admin profile. You need to be onboarded first.",
                    ephemeral=True,
                )
                return

            # Approve in database
            import os
            from uuid import uuid4

            from data_service.models import TeamMemberCreate

            approval = OnboardingApproval(request_id=self.request_id, approved=True)
            self.team_service.data_service.approve_onboarding(approval, admin_member.id)

            # Create Supabase auth user
            supabase_user_id = None
            temp_password = None
            try:
                supabase_user_id, temp_password = (
                    self.team_service.data_service.create_supabase_user(
                        email=pending.email, name=pending.name
                    )
                )
                logger.info(f"Created Supabase user: {supabase_user_id}")
            except Exception as e:
                logger.error(f"Error creating Supabase user: {e}")
                supabase_user_id = uuid4()

            # Create team_members record (no team assigned yet)
            team_member_data = TeamMemberCreate(
                user_id=supabase_user_id,
                discord_id=pending.discord_id,
                discord_username=pending.discord_username,
                name=pending.name,
                email=pending.email,
                phone=pending.phone,
                bio=pending.bio,
            )

            new_member = self.team_service.data_service.create_team_member(
                team_member_data
            )
            logger.info(f"Created team_members record: {new_member.id}")

            # Create Google Doc profile in main Team Management folder
            doc_url = None
            doc_id = None
            if self.docs_service.is_available():
                try:
                    member_data = {
                        "name": pending.name,
                        "email": pending.email,
                        "phone": pending.phone or "Not provided",
                        "team": "Unassigned",
                        "role": "To be assigned",
                        "bio": pending.bio or "No bio provided",
                    }
                    profile_result = self.docs_service.create_team_member_profile(
                        member_data, None
                    )
                    if profile_result:
                        doc_url = profile_result["url"]
                        doc_id = profile_result["doc_id"]
                        logger.info(f"Created Google Doc profile: {doc_url}")

                        # Update team_members with profile info
                        self.team_service.data_service.client.table(
                            "team_members"
                        ).update({"profile_doc_id": doc_id, "profile_url": doc_url}).eq(
                            "id", str(new_member.id)
                        ).execute()

                        # Add to main roster spreadsheet
                        main_roster_id = os.getenv("GOOGLE_MAIN_ROSTER_SHEET_ID")
                        if main_roster_id:
                            try:
                                self.docs_service.add_member_to_roster(
                                    roster_sheet_id=main_roster_id,
                                    member_name=pending.name,
                                    discord_username=pending.discord_username,
                                    email=pending.email,
                                    role="To be assigned",
                                    profile_url=doc_url,
                                )
                                logger.info(f"Added {pending.name} to main roster")
                            except Exception as e:
                                logger.error(f"Error adding to main roster: {e}")
                except Exception as e:
                    logger.error(f"Error creating Google Doc: {e}")

            # Update approval message
            original_embed = interaction.message.embeds[0]
            original_embed.color = discord.Color.green()
            original_embed.title = f"✅ Approved by {interaction.user.name}"
            if doc_url:
                original_embed.add_field(
                    name="📄 Profile Created",
                    value=f"[View Profile Document]({doc_url})",
                    inline=False,
                )
            original_embed.add_field(
                name="⏳ Next Step",
                value="Admin should run `/add-to-team` to assign this user to a team",
                inline=False,
            )

            await interaction.message.edit(embed=original_embed, view=None)

            # Send welcome DM to user
            try:
                discord_user = await interaction.client.fetch_user(self.user_id)
                welcome_msg = (
                    f"🎉 **Welcome to the team, {pending.name}!**\n\n"
                    f"Your onboarding request has been approved!\n\n"
                )
                if doc_url:
                    welcome_msg += f"📄 **Your Profile:** {doc_url}\n\n"
                if temp_password:
                    welcome_msg += (
                        f"🔑 **Temporary Password:** `{temp_password}`\n"
                        f"Please change this after your first login.\n\n"
                    )
                welcome_msg += (
                    f"⏳ **Next Steps:**\n"
                    f"An admin will assign you to a team soon. You'll receive another notification when that happens.\n\n"
                    f"In the meantime, feel free to explore the server!"
                )
                await discord_user.send(welcome_msg)
            except Exception as e:
                logger.warning(f"Could not DM user {self.user_id}: {e}")

            await interaction.followup.send(
                "✅ User approved successfully! Use `/add-to-team` to assign them to a team.",
                ephemeral=True,
            )

        except Exception as e:
            logger.error(f"Error in approve button: {e}", exc_info=True)
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

    @discord.ui.button(label="❌ Reject", style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Reject onboarding request."""
        # Show modal for rejection reason
        modal = RejectionModal(self.request_id, self.user_id, self.team_service)
        await interaction.response.send_modal(modal)


class RejectionModal(discord.ui.Modal, title="Reject Onboarding"):
    """Modal to collect rejection reason."""

    reason = discord.ui.TextInput(
        label="Rejection Reason",
        style=discord.TextStyle.paragraph,
        placeholder="Please provide a reason for rejection...",
        required=True,
        max_length=500,
    )

    def __init__(self, request_id: UUID, user_id: int, team_service: TeamMemberService):
        super().__init__()
        self.request_id = request_id
        self.user_id = user_id
        self.team_service = team_service

    async def on_submit(self, interaction: discord.Interaction):
        """Handle rejection."""
        await interaction.response.defer(ephemeral=True)

        try:
            # Get admin's team member record
            admin_member = self.team_service.get_member_by_discord_id(
                interaction.user.id
            )
            if not admin_member:
                await interaction.followup.send(
                    "❌ Could not find your admin profile.", ephemeral=True
                )
                return

            # Reject the request
            approval = OnboardingApproval(
                request_id=self.request_id,
                approved=False,
                rejection_reason=self.reason.value,
            )
            self.team_service.data_service.approve_onboarding(approval, admin_member.id)

            # Update original message
            original_message = await interaction.channel.fetch_message(
                interaction.message.id
            )
            original_embed = original_message.embeds[0]
            original_embed.color = discord.Color.red()
            original_embed.title = "❌ Rejected by " + str(interaction.user)
            original_embed.add_field(name="Reason", value=self.reason.value)

            # Disable buttons
            view = discord.ui.View()
            await original_message.edit(embed=original_embed, view=view)

            await interaction.followup.send("✅ Request rejected.", ephemeral=True)

            # Notify the user
            try:
                discord_user = await interaction.client.fetch_user(self.user_id)
                await discord_user.send(
                    f"❌ **Onboarding Request Update**\n\n"
                    f"Unfortunately, your onboarding request has been declined.\n\n"
                    f"**Reason:** {self.reason.value}\n\n"
                    f"If you have questions, please reach out to an admin."
                )
            except:
                logger.warning(f"Could not DM user {self.user_id}")

        except Exception as e:
            logger.error(f"Error rejecting onboarding: {e}")
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
