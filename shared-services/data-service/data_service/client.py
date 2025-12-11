"""Data service client - handles all database operations."""

import os
import secrets
import string
from typing import List, Optional, Tuple
from uuid import UUID

from supabase import Client, create_client

from .models import (
    OnboardingApproval,
    PendingOnboarding,
    PendingOnboardingCreate,
    Role,
    Team,
    TeamMember,
    TeamMemberCreate,
    TeamMembership,
    TeamMemberUpdate,
    TeamUpdate,
)


class DataService:
    """
    Data service for Alfred system.

    Currently uses Supabase, but designed to be database-agnostic
    for easy migration to self-hosted PostgreSQL later.
    """

    def __init__(self, supabase_url: str, supabase_service_key: str):
        """
        Initialize data service.

        Args:
            supabase_url: Supabase project URL
            supabase_service_key: Service role key (for admin operations)
        """
        self.client: Client = create_client(supabase_url, supabase_service_key)
        self.supabase_url = supabase_url
        self.supabase_service_key = supabase_service_key

    # Team Members CRUD

    def create_team_member(self, member: TeamMemberCreate) -> TeamMember:
        """
        Create a new team member.

        Args:
            member: Team member data

        Returns:
            Created team member with database fields

        Raises:
            Exception if creation fails
        """
        try:
            # Convert Pydantic model to dict for Supabase
            member_data = member.model_dump(mode="json")

            # Convert UUID to string for Supabase
            member_data["user_id"] = str(member_data["user_id"])

            # Convert skills list to JSON
            member_data["skills"] = [skill for skill in member_data["skills"]]

            response = self.client.table("team_members").insert(member_data).execute()

            if not response.data:
                raise Exception("No data returned from insert")

            return TeamMember(**response.data[0])

        except Exception as e:
            raise Exception(f"Failed to create team member: {str(e)}")

    def get_team_member(self, member_id: UUID) -> Optional[TeamMember]:
        """
        Get team member by ID.

        Args:
            member_id: Team member UUID

        Returns:
            Team member if found, None otherwise
        """
        try:
            response = (
                self.client.table("team_members")
                .select("*")
                .eq("id", str(member_id))
                .execute()
            )

            if response.data:
                return TeamMember(**response.data[0])
            return None

        except Exception as e:
            raise Exception(f"Failed to get team member: {str(e)}")

    def get_team_member_by_user_id(self, user_id: UUID) -> Optional[TeamMember]:
        """
        Get team member by Supabase auth user ID.

        Args:
            user_id: Supabase auth user UUID

        Returns:
            Team member if found, None otherwise
        """
        try:
            response = (
                self.client.table("team_members")
                .select("*")
                .eq("user_id", str(user_id))
                .execute()
            )

            if response.data:
                return TeamMember(**response.data[0])
            return None

        except Exception as e:
            raise Exception(f"Failed to get team member by user_id: {str(e)}")

    def get_team_member_by_email(self, email: str) -> Optional[TeamMember]:
        """
        Get team member by email.

        Args:
            email: Team member email

        Returns:
            Team member if found, None otherwise
        """
        try:
            response = (
                self.client.table("team_members")
                .select("*")
                .eq("email", email)
                .execute()
            )

            if response.data:
                return TeamMember(**response.data[0])
            return None

        except Exception as e:
            raise Exception(f"Failed to get team member by email: {str(e)}")

    def get_team_member_by_discord(self, discord_username: str) -> Optional[TeamMember]:
        """
        Get team member by Discord username.

        This is the key lookup for the Discord bot.

        Args:
            discord_username: Discord username

        Returns:
            Team member if found, None otherwise
        """
        try:
            response = (
                self.client.table("team_members")
                .select("*")
                .eq("discord_username", discord_username)
                .execute()
            )

            if response.data:
                return TeamMember(**response.data[0])
            return None

        except Exception as e:
            raise Exception(f"Failed to get team member by discord: {str(e)}")

    def list_team_members(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[TeamMember]:
        """
        List all team members.

        Args:
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of team members
        """
        try:
            response = (
                self.client.table("team_members")
                .select("*")
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )

            return [TeamMember(**member) for member in response.data]

        except Exception as e:
            raise Exception(f"Failed to list team members: {str(e)}")

    def update_team_member(
        self,
        member_id: UUID,
        updates: TeamMemberUpdate,
    ) -> TeamMember:
        """
        Update team member.

        Args:
            member_id: Team member UUID
            updates: Fields to update

        Returns:
            Updated team member

        Raises:
            Exception if update fails
        """
        try:
            # Only include fields that are not None
            update_data = updates.model_dump(exclude_none=True, mode="json")

            if not update_data:
                raise ValueError("No fields to update")

            response = (
                self.client.table("team_members")
                .update(update_data)
                .eq("id", str(member_id))
                .execute()
            )

            if not response.data:
                raise Exception("Team member not found")

            return TeamMember(**response.data[0])

        except Exception as e:
            raise Exception(f"Failed to update team member: {str(e)}")

    def delete_team_member(self, member_id: UUID) -> bool:
        """
        Delete team member.

        Args:
            member_id: Team member UUID

        Returns:
            True if deleted successfully

        Raises:
            Exception if deletion fails
        """
        try:
            response = (
                self.client.table("team_members")
                .delete()
                .eq("id", str(member_id))
                .execute()
            )

            return True

        except Exception as e:
            raise Exception(f"Failed to delete team member: {str(e)}")

    # Utility methods for Discord bot

    def get_members_with_skill(self, skill_name: str) -> List[TeamMember]:
        """
        Get team members who have a specific skill.

        Args:
            skill_name: Name of the skill

        Returns:
            List of team members with that skill
        """
        try:
            # Note: This uses JSONB query - may need adjustment for PostgreSQL
            response = (
                self.client.table("team_members")
                .select("*")
                .contains("skills", [{"name": skill_name}])
                .execute()
            )

            return [TeamMember(**member) for member in response.data]

        except Exception as e:
            # Fallback: fetch all and filter in Python
            all_members = self.list_team_members(limit=1000)
            return [
                member
                for member in all_members
                if any(
                    skill.name.lower() == skill_name.lower() for skill in member.skills
                )
            ]

    def get_available_members(self, min_hours: int = 10) -> List[TeamMember]:
        """
        Get team members with availability above threshold.

        Args:
            min_hours: Minimum availability hours

        Returns:
            List of available team members
        """
        try:
            response = (
                self.client.table("team_members")
                .select("*")
                .gte("availability_hours", min_hours)
                .execute()
            )

            return [TeamMember(**member) for member in response.data]

        except Exception as e:
            raise Exception(f"Failed to get available members: {str(e)}")

    def get_team_member_by_discord_id(self, discord_id: int) -> Optional[TeamMember]:
        """
        Get team member by Discord ID.

        Args:
            discord_id: Discord user ID (snowflake)

        Returns:
            Team member if found, None otherwise
        """
        try:
            response = (
                self.client.table("team_members")
                .select("*")
                .eq("discord_id", discord_id)
                .execute()
            )

            if response.data:
                return TeamMember(**response.data[0])
            return None

        except Exception as e:
            raise Exception(f"Failed to get team member by discord_id: {str(e)}")

    # Pending Onboarding CRUD

    def create_pending_onboarding(
        self, onboarding: PendingOnboardingCreate
    ) -> PendingOnboarding:
        """
        Create a pending onboarding request.

        Args:
            onboarding: Onboarding request data

        Returns:
            Created pending onboarding request

        Raises:
            Exception if creation fails
        """
        try:
            onboarding_data = onboarding.model_dump(mode="json")

            response = (
                self.client.table("pending_onboarding")
                .insert(onboarding_data)
                .execute()
            )

            if not response.data:
                raise Exception("No data returned from insert")

            return PendingOnboarding(**response.data[0])

        except Exception as e:
            raise Exception(f"Failed to create pending onboarding: {str(e)}")

    def get_pending_onboarding(self, request_id: UUID) -> Optional[PendingOnboarding]:
        """
        Get pending onboarding request by ID.

        Args:
            request_id: Onboarding request UUID

        Returns:
            Pending onboarding if found, None otherwise
        """
        try:
            response = (
                self.client.table("pending_onboarding")
                .select("*")
                .eq("id", str(request_id))
                .execute()
            )

            if response.data:
                return PendingOnboarding(**response.data[0])
            return None

        except Exception as e:
            raise Exception(f"Failed to get pending onboarding: {str(e)}")

    def get_pending_onboarding_by_discord_id(
        self, discord_id: int
    ) -> Optional[PendingOnboarding]:
        """
        Get pending onboarding request by Discord ID.

        Args:
            discord_id: Discord user ID

        Returns:
            Pending onboarding if found, None otherwise
        """
        try:
            response = (
                self.client.table("pending_onboarding")
                .select("*")
                .eq("discord_id", discord_id)
                .eq("status", "pending")
                .execute()
            )

            if response.data:
                return PendingOnboarding(**response.data[0])
            return None

        except Exception as e:
            raise Exception(f"Failed to get pending onboarding by discord_id: {str(e)}")

    def list_pending_onboarding(
        self, status: str = "pending", limit: int = 50
    ) -> List[PendingOnboarding]:
        """
        List pending onboarding requests.

        Args:
            status: Filter by status (pending, approved, rejected)
            limit: Maximum number of results

        Returns:
            List of pending onboarding requests
        """
        try:
            response = (
                self.client.table("pending_onboarding")
                .select("*")
                .eq("status", status)
                .order("submitted_at", desc=True)
                .limit(limit)
                .execute()
            )

            return [PendingOnboarding(**req) for req in response.data]

        except Exception as e:
            raise Exception(f"Failed to list pending onboarding: {str(e)}")

    def approve_onboarding(
        self, approval: OnboardingApproval, reviewed_by: UUID
    ) -> PendingOnboarding:
        """
        Approve or reject an onboarding request.

        Args:
            approval: Approval data with request_id and decision
            reviewed_by: UUID of the reviewer

        Returns:
            Updated pending onboarding request

        Raises:
            Exception if update fails
        """
        try:
            import datetime

            update_data = {
                "status": "approved" if approval.approved else "rejected",
                "reviewed_at": datetime.datetime.utcnow().isoformat(),
                "reviewed_by": str(reviewed_by),
            }

            if not approval.approved and approval.rejection_reason:
                update_data["rejection_reason"] = approval.rejection_reason

            response = (
                self.client.table("pending_onboarding")
                .update(update_data)
                .eq("id", str(approval.request_id))
                .execute()
            )

            if not response.data:
                raise Exception("Onboarding request not found")

            return PendingOnboarding(**response.data[0])

        except Exception as e:
            raise Exception(f"Failed to approve onboarding: {str(e)}")

    # Teams CRUD

    def list_teams(self) -> List[Team]:
        """List all teams."""
        try:
            response = self.client.table("teams").select("*").execute()
            return [Team(**team) for team in response.data]
        except Exception as e:
            raise Exception(f"Failed to list teams: {str(e)}")

    def get_team_by_name(self, name: str) -> Optional[Team]:
        """Get team by name."""
        try:
            response = self.client.table("teams").select("*").eq("name", name).execute()

            if response.data:
                return Team(**response.data[0])
            return None

        except Exception as e:
            raise Exception(f"Failed to get team: {str(e)}")

    def update_team(self, team_id: UUID, updates: TeamUpdate) -> Team:
        """Update team information."""
        try:
            # Filter out None values
            update_data = {
                k: v for k, v in updates.model_dump().items() if v is not None
            }

            if not update_data:
                raise ValueError("No updates provided")

            response = (
                self.client.table("teams")
                .update(update_data)
                .eq("id", str(team_id))
                .execute()
            )

            if not response.data:
                raise Exception("Team not found")

            return Team(**response.data[0])

        except Exception as e:
            raise Exception(f"Failed to update team: {str(e)}")

    # Roles CRUD

    def list_roles(self) -> List[Role]:
        """List all roles."""
        try:
            response = self.client.table("roles").select("*").order("level").execute()
            return [Role(**role) for role in response.data]
        except Exception as e:
            raise Exception(f"Failed to list roles: {str(e)}")

    def get_role_by_name(self, name: str) -> Optional[Role]:
        """Get role by name."""
        try:
            response = self.client.table("roles").select("*").eq("name", name).execute()

            if response.data:
                return Role(**response.data[0])
            return None

        except Exception as e:
            raise Exception(f"Failed to get role: {str(e)}")

    def get_role_by_level(self, level: int) -> List[Role]:
        """Get roles by hierarchy level."""
        try:
            response = (
                self.client.table("roles").select("*").eq("level", level).execute()
            )
            return [Role(**role) for role in response.data]
        except Exception as e:
            raise Exception(f"Failed to get roles by level: {str(e)}")

    # Supabase Auth User Management

    def create_supabase_user(self, email: str, name: str) -> Tuple[UUID, str]:
        """
        Create a Supabase auth user with auto-generated password.

        Args:
            email: User's email
            name: User's full name (for metadata)

        Returns:
            Tuple of (user_id, temporary_password)

        Raises:
            Exception if user creation fails
        """
        try:
            import requests

            # Generate a secure random password
            password = self._generate_password()

            # Create user using Supabase Admin API
            url = f"{self.supabase_url}/auth/v1/admin/users"
            headers = {
                "apikey": self.supabase_service_key,
                "Authorization": f"Bearer {self.supabase_service_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "email": email,
                "password": password,
                "email_confirm": True,  # Auto-confirm email
                "user_metadata": {"full_name": name},
            }

            response = requests.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                user_data = response.json()
                user_id = UUID(user_data["id"])
                return user_id, password
            else:
                error_msg = response.json().get("msg", response.text)
                raise Exception(f"Supabase API error: {error_msg}")

        except Exception as e:
            raise Exception(f"Failed to create Supabase user: {str(e)}")

    def _generate_password(self, length: int = 16) -> str:
        """Generate a secure random password."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        return password


def create_data_service(
    supabase_url: Optional[str] = None,
    supabase_service_key: Optional[str] = None,
) -> DataService:
    """
    Factory function to create DataService from environment variables.

    Args:
        supabase_url: Optional Supabase URL (uses env var if not provided)
        supabase_service_key: Optional service key (uses env var if not provided)

    Returns:
        Configured DataService instance
    """
    supabase_url = supabase_url or os.getenv("SUPABASE_URL")
    supabase_service_key = supabase_service_key or os.getenv("SUPABASE_SERVICE_KEY")

    if not supabase_url:
        raise ValueError("SUPABASE_URL not provided")
    if not supabase_service_key:
        raise ValueError("SUPABASE_SERVICE_KEY not provided")

    return DataService(supabase_url, supabase_service_key)
