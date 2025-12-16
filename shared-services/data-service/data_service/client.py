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
            member_data = member.model_dump(mode="json", exclude_none=True)

            # Convert UUID to string for Supabase
            member_data["user_id"] = str(member_data["user_id"])

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

    # DEPRECATED: Skills and availability_hours fields removed from schema
    # def get_members_with_skill(self, skill_name: str) -> List[TeamMember]:
    #     """Get team members who have a specific skill."""
    #     # This method is disabled because 'skills' field was removed from team_members table
    #     raise NotImplementedError("Skills field has been removed from the schema")

    # def get_available_members(self, min_hours: int = 10) -> List[TeamMember]:
    #     """Get team members with availability above threshold."""
    #     # This method is disabled because 'availability_hours' field was removed from team_members table
    #     raise NotImplementedError("Availability hours field has been removed from the schema")

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

    # ClickUp Lists Management

    def add_clickup_list(
        self,
        clickup_list_id: str,
        list_name: str,
        team_id: UUID,
        description: Optional[str] = None,
        clickup_folder_id: Optional[str] = None,
        clickup_space_id: Optional[str] = None,
    ) -> dict:
        """
        Add a ClickUp list to track for a team.

        Args:
            clickup_list_id: ClickUp list ID from API
            list_name: Name of the list
            team_id: UUID of the team this list belongs to
            description: Optional description of the list
            clickup_folder_id: Optional ClickUp folder ID
            clickup_space_id: Optional ClickUp space ID

        Returns:
            Created clickup_lists record
        """
        try:
            # Build insert data with only non-None values to avoid schema cache issues
            insert_data = {
                "clickup_list_id": clickup_list_id,
                "list_name": list_name,
                "team_id": str(team_id),
                "is_active": True,
            }

            if description is not None:
                insert_data["description"] = description

            response = self.client.table("clickup_lists").insert(insert_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            raise Exception(f"Failed to add ClickUp list: {str(e)}")

    def get_team_clickup_lists(self, team_id: UUID) -> List[dict]:
        """
        Get all active ClickUp lists for a team.

        Args:
            team_id: UUID of the team

        Returns:
            List of clickup_lists records
        """
        try:
            response = (
                self.client.table("clickup_lists")
                .select("*")
                .eq("team_id", str(team_id))
                .eq("is_active", True)
                .order("list_name")
                .execute()
            )
            return response.data if response.data else []
        except Exception:
            return []

    def get_team_clickup_lists_by_name(self, team_name: str) -> List[dict]:
        """
        Get all active ClickUp lists for a team by team name.

        Args:
            team_name: Name of the team (e.g., "Engineering", "Product")

        Returns:
            List of clickup_lists records with list IDs
        """
        try:
            # First get the team
            team_response = (
                self.client.table("teams").select("id").eq("name", team_name).execute()
            )

            if not team_response.data:
                return []

            team_id = team_response.data[0]["id"]

            # Then get lists for that team
            response = (
                self.client.table("clickup_lists")
                .select("*")
                .eq("team_id", team_id)
                .eq("is_active", True)
                .order("list_name")
                .execute()
            )
            return response.data if response.data else []
        except Exception:
            return []

    def get_team_list_ids(self, team_id: UUID) -> List[str]:
        """
        Get all active ClickUp list IDs for a team (for filtering tasks).

        Args:
            team_id: UUID of the team

        Returns:
            List of ClickUp list ID strings
        """
        lists = self.get_team_clickup_lists(team_id)
        return [lst["clickup_list_id"] for lst in lists]

    def get_team_list_ids_by_name(self, team_name: str) -> List[str]:
        """
        Get all active ClickUp list IDs for a team by name.

        Args:
            team_name: Name of the team

        Returns:
            List of ClickUp list ID strings
        """
        lists = self.get_team_clickup_lists_by_name(team_name)
        return [lst["clickup_list_id"] for lst in lists]

    def deactivate_clickup_list(self, clickup_list_id: str) -> bool:
        """
        Deactivate a ClickUp list (soft delete).

        Args:
            clickup_list_id: ClickUp list ID to deactivate

        Returns:
            True if successful, False otherwise
        """
        try:
            response = (
                self.client.table("clickup_lists")
                .update({"is_active": False})
                .eq("clickup_list_id", clickup_list_id)
                .execute()
            )
            return len(response.data) > 0 if response.data else False
        except Exception:
            return False

    def reactivate_clickup_list(self, clickup_list_id: str) -> bool:
        """
        Reactivate a ClickUp list.

        Args:
            clickup_list_id: ClickUp list ID to reactivate

        Returns:
            True if successful, False otherwise
        """
        try:
            response = (
                self.client.table("clickup_lists")
                .update({"is_active": True})
                .eq("clickup_list_id", clickup_list_id)
                .execute()
            )
            return len(response.data) > 0 if response.data else False
        except Exception:
            return False

    # Team Management Methods

    def create_team(
        self,
        name: str,
        team_lead_id: UUID,
        description: Optional[str] = None,
        drive_folder_id: Optional[str] = None,
        overview_doc_id: Optional[str] = None,
        overview_doc_url: Optional[str] = None,
        roster_sheet_id: Optional[str] = None,
        roster_sheet_url: Optional[str] = None,
        discord_role_id: Optional[int] = None,
        discord_manager_role_id: Optional[int] = None,
        discord_general_channel_id: Optional[int] = None,
        discord_standup_channel_id: Optional[int] = None,
    ) -> Team:
        """
        Create a new team with all integration IDs.

        Args:
            name: Team name
            team_lead_id: UUID of the team lead (REQUIRED - migration 011 constraint)
            description: Team description
            drive_folder_id: Google Drive folder ID
            overview_doc_id: Team overview document ID
            overview_doc_url: Team overview document URL
            roster_sheet_id: Team roster spreadsheet ID
            roster_sheet_url: Team roster spreadsheet URL
            discord_role_id: Discord role ID for this team
            discord_manager_role_id: Discord manager role ID for team leads
            discord_general_channel_id: Discord general channel ID
            discord_standup_channel_id: Discord standup channel ID

        Returns:
            Created team

        Raises:
            Exception if creation fails
        """
        try:
            team_data = {
                "name": name,
                "team_lead_id": str(team_lead_id),
                "description": description,
                "drive_folder_id": drive_folder_id,
                "overview_doc_id": overview_doc_id,
                "overview_doc_url": overview_doc_url,
                "roster_sheet_id": roster_sheet_id,
                "roster_sheet_url": roster_sheet_url,
                "discord_role_id": discord_role_id,
                "discord_manager_role_id": discord_manager_role_id,
                "discord_general_channel_id": discord_general_channel_id,
                "discord_standup_channel_id": discord_standup_channel_id,
            }

            # Remove None values
            team_data = {k: v for k, v in team_data.items() if v is not None}

            response = self.client.table("teams").insert(team_data).execute()

            if not response.data:
                raise Exception("No data returned from insert")

            return Team(**response.data[0])

        except Exception as e:
            raise Exception(f"Failed to create team: {str(e)}")

    def update_team_discord_ids(
        self,
        team_id: UUID,
        role_id: Optional[int] = None,
        general_channel_id: Optional[int] = None,
        standup_channel_id: Optional[int] = None,
    ) -> Team:
        """
        Update Discord integration IDs for a team.

        Args:
            team_id: Team UUID
            role_id: Discord role ID
            general_channel_id: Discord general channel ID
            standup_channel_id: Discord standup channel ID

        Returns:
            Updated team

        Raises:
            Exception if update fails
        """
        try:
            update_data = {}
            if role_id is not None:
                update_data["discord_role_id"] = role_id
            if general_channel_id is not None:
                update_data["discord_general_channel_id"] = general_channel_id
            if standup_channel_id is not None:
                update_data["discord_standup_channel_id"] = standup_channel_id

            if not update_data:
                raise ValueError("No Discord IDs provided")

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
            raise Exception(f"Failed to update team Discord IDs: {str(e)}")

    def update_team_clickup_workspace(
        self,
        team_id: UUID,
        workspace_id: Optional[str] = None,
        space_id: Optional[str] = None,
        workspace_name: Optional[str] = None,
    ) -> Team:
        """
        Update ClickUp workspace information for a team.

        Args:
            team_id: Team UUID
            workspace_id: ClickUp workspace ID (optional)
            space_id: ClickUp space ID (optional)
            workspace_name: Workspace name for display (optional)

        Returns:
            Updated team

        Raises:
            Exception if update fails
        """
        try:
            update_data = {}
            if workspace_id is not None:
                update_data["clickup_workspace_id"] = workspace_id
            if space_id is not None:
                update_data["clickup_space_id"] = space_id
            if workspace_name is not None:
                update_data["clickup_workspace_name"] = workspace_name

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
            raise Exception(f"Failed to update team ClickUp workspace: {str(e)}")

    def add_member_to_team(
        self, member_id: UUID, team_id: UUID, role: Optional[str] = None
    ) -> TeamMembership:
        """
        Add a member to a team (creates team_memberships record).

        Args:
            member_id: Team member UUID
            team_id: Team UUID
            role: Role within the team (optional, e.g., "Senior Engineer")

        Returns:
            Created team membership

        Raises:
            Exception if creation fails
        """
        try:
            membership_data = {
                "member_id": str(member_id),
                "team_id": str(team_id),
                "role": role,
                "is_active": True,
            }

            response = (
                self.client.table("team_memberships").insert(membership_data).execute()
            )

            if not response.data:
                raise Exception("No data returned from insert")

            return TeamMembership(**response.data[0])

        except Exception as e:
            raise Exception(f"Failed to add member to team: {str(e)}")

    def remove_member_from_team(self, member_id: UUID, team_id: UUID) -> bool:
        """
        Remove a member from a team (soft delete).

        Args:
            member_id: Team member UUID
            team_id: Team UUID

        Returns:
            True if successful, False otherwise
        """
        try:
            response = (
                self.client.table("team_memberships")
                .update({"is_active": False})
                .eq("member_id", str(member_id))
                .eq("team_id", str(team_id))
                .execute()
            )
            return len(response.data) > 0 if response.data else False
        except Exception:
            return False

    def get_team_members(
        self, team_id: UUID, active_only: bool = True
    ) -> List[TeamMember]:
        """
        Get all members of a team.

        Args:
            team_id: Team UUID
            active_only: Whether to only return active memberships (default True)

        Returns:
            List of team members
        """
        try:
            # Use the database function we created in the migration
            query = self.client.rpc(
                "get_team_member_list", {"team_id_param": str(team_id)}
            )

            response = query.execute()

            if not response.data:
                return []

            # Convert to TeamMember objects
            members = []
            for row in response.data:
                # Fetch full member data
                member = self.get_team_member(UUID(row["member_id"]))
                if member:
                    members.append(member)

            return members

        except Exception as e:
            raise Exception(f"Failed to get team members: {str(e)}")

    def get_member_teams(self, member_id: UUID) -> List[Team]:
        """
        Get all teams a member belongs to.

        Args:
            member_id: Team member UUID

        Returns:
            List of teams
        """
        try:
            # Use the database function we created in the migration
            query = self.client.rpc(
                "get_member_teams", {"member_id_param": str(member_id)}
            )

            response = query.execute()

            if not response.data:
                return []

            # Convert to Team objects
            teams = []
            for row in response.data:
                team = self.get_team_by_name(row["team_name"])
                if team:
                    teams.append(team)

            return teams

        except Exception as e:
            raise Exception(f"Failed to get member teams: {str(e)}")


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
