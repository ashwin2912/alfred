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
        # Check if user already has pending request
        existing = self.team_service.data_service.get_pending_onboarding_by_discord_id(
            interaction.user.id
        )

        if existing:
            await interaction.response.send_message(
                f"⚠️ You already have a pending onboarding request (ID: {existing.id}).\n"
                "Please wait for admin approval.",
                ephemeral=True,
            )
            return

        # Check if user is already onboarded
        member = self.team_service.get_member_by_discord_id(interaction.user.id)
        if member:
            await interaction.response.send_message(
                "✅ You're already onboarded! Use `/setup` to view your profile.",
                ephemeral=True,
            )
            return

        # Show modal
        modal = OnboardingModal(self.team_service)
        await interaction.response.send_modal(modal)


class TeamRoleSelectionModal(discord.ui.Modal, title="Assign Team & Role"):
    """Modal for admin to select team and role during approval."""

    team = discord.ui.TextInput(
        label="Team",
        placeholder="Engineering, Product, or Business",
        required=True,
        max_length=100,
    )

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
        team_service: TeamMemberService,
        docs_service,
        original_message,
    ):
        super().__init__()
        self.request_id = request_id
        self.user_id = user_id
        self.team_service = team_service
        self.docs_service = docs_service
        self.original_message = original_message

    async def on_submit(self, interaction: discord.Interaction):
        """Handle team/role assignment and complete approval."""
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

            # Create Google Doc profile
            doc_url = None
            if self.docs_service.is_available():
                try:
                    member_data = {
                        "name": pending.name,
                        "email": pending.email,
                        "phone": pending.phone or "Not provided",
                        "team": self.team.value,
                        "role": self.role.value or "To be assigned",
                        "bio": pending.bio,
                    }
                    doc_url = self.docs_service.create_team_member_profile(member_data)
                    logger.info(f"Created Google Doc profile: {doc_url}")
                except Exception as e:
                    logger.error(f"Error creating Google Doc: {e}")

            # Update the approval message
            original_embed = self.original_message.embeds[0]
            original_embed.color = discord.Color.green()
            original_embed.title = f"✅ Approved by {interaction.user.name}"
            original_embed.add_field(
                name="Assigned Team", value=self.team.value, inline=True
            )
            if self.role.value:
                original_embed.add_field(
                    name="Assigned Role", value=self.role.value, inline=True
                )
            if doc_url:
                original_embed.add_field(
                    name="📄 Profile Created",
                    value=f"[View Document]({doc_url})",
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
                name="1️⃣ Create Supabase User",
                value=f"Email: `{pending.email}`\nCreate in Supabase dashboard",
                inline=False,
            )

            admin_checklist.add_field(
                name="2️⃣ Add to ClickUp",
                value=(
                    f"Email: `{pending.email}`\n"
                    f"Team: {self.team.value}\n"
                    f"Role: {self.role.value if self.role.value else 'TBD'}\n"
                    f"⚠️ **ACTION REQUIRED:** Add this user to ClickUp workspace manually"
                ),
                inline=False,
            )

            # Assign Discord roles based on team
            role_assigned = False
            try:
                guild = interaction.guild
                member = guild.get_member(self.user_id)
                if member:
                    # Try to find and assign role based on team name
                    team_role = discord.utils.get(guild.roles, name=self.team.value)
                    if team_role:
                        await member.add_roles(team_role)
                        role_assigned = True
                        logger.info(f"Assigned {self.team.value} role to {member.name}")
                    else:
                        logger.warning(f"Role '{self.team.value}' not found in guild")
            except Exception as e:
                logger.error(f"Error assigning Discord role: {e}")

            # Add Discord role status to checklist
            if role_assigned:
                admin_checklist.add_field(
                    name="3️⃣ Discord Roles",
                    value=f"✅ Assigned {self.team.value} role",
                    inline=False,
                )
            else:
                admin_checklist.add_field(
                    name="3️⃣ Discord Roles",
                    value=f"⚠️ Could not find '{self.team.value}' role - assign manually",
                    inline=False,
                )

            # Add Google Docs status to checklist
            if doc_url:
                admin_checklist.add_field(
                    name="4️⃣ Google Doc Profile",
                    value=f"✅ Created: [View Document]({doc_url})",
                    inline=False,
                )
            else:
                admin_checklist.add_field(
                    name="4️⃣ Create Google Doc Profile",
                    value="⚠️ Google Docs not configured - create manually",
                    inline=False,
                )

            await interaction.followup.send(embed=admin_checklist, ephemeral=True)

            # Notify the user
            try:
                discord_user = await interaction.client.fetch_user(self.user_id)
                user_embed = discord.Embed(
                    title="🎉 Welcome to the Team!",
                    description="Your onboarding request has been approved!",
                    color=discord.Color.green(),
                )

                user_embed.add_field(
                    name="Your Assignment",
                    value=f"**Team:** {self.team.value}\n**Role:** {self.role.value if self.role.value else 'To be assigned'}",
                    inline=False,
                )

                next_steps = (
                    "1. You'll receive login credentials via email\n"
                    "2. You'll be added to ClickUp\n"
                )

                if role_assigned:
                    next_steps += (
                        f"3. ✅ You've been assigned the {self.team.value} role\n"
                    )
                else:
                    next_steps += "3. You'll get team role access soon\n"

                next_steps += "4. Use `/setup` in #alfred to view your profile"

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

    @discord.ui.button(label="✅ Approve & Assign", style=discord.ButtonStyle.green)
    async def approve(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Show modal to assign team and role."""
        try:
            logger.info(f"Approve button clicked by {interaction.user}")
            modal = TeamRoleSelectionModal(
                self.request_id,
                self.user_id,
                self.team_service,
                self.docs_service,
                interaction.message,
            )
            await interaction.response.send_modal(modal)
            logger.info(f"Modal sent successfully")
        except Exception as e:
            logger.error(f"Error in approve button: {e}", exc_info=True)
            await interaction.response.send_message(
                f"❌ Error: {str(e)}", ephemeral=True
            )

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
