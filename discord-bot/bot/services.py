"""Services for interacting with data and external APIs."""

import os
import sys
from pathlib import Path
from typing import Optional

import httpx

# Add shared-services to path
shared_services_path = Path(__file__).parent.parent.parent / "shared-services"
sys.path.insert(0, str(shared_services_path))

# Add docs-service to path
docs_service_path = shared_services_path / "docs-service"
sys.path.insert(0, str(docs_service_path))

from data_service import DataService, create_data_service
from data_service.models import TeamMember, TeamMemberUpdate

# Import Google Docs service
try:
    from docs_service.google_docs_client import GoogleDocsService
except ImportError as e:
    print(f"Warning: Could not import GoogleDocsService: {e}")
    GoogleDocsService = None


class TeamMemberService:
    """Service for managing team member data."""

    def __init__(self):
        self.data_service: DataService = create_data_service()

    def get_member_by_discord(self, discord_username: str) -> Optional[TeamMember]:
        """Get team member by Discord username."""
        return self.data_service.get_team_member_by_discord(discord_username)

    def get_member_by_discord_id(self, discord_id: int) -> Optional[TeamMember]:
        """Get team member by Discord ID."""
        return self.data_service.get_team_member_by_discord_id(discord_id)

    def update_clickup_token(
        self, discord_username: str, clickup_token: str
    ) -> Optional[TeamMember]:
        """Update ClickUp API token for a team member."""
        member = self.get_member_by_discord(discord_username)
        if not member:
            return None

        update = TeamMemberUpdate(clickup_api_token=clickup_token)
        return self.data_service.update_team_member(member.id, update)


class DocsService:
    """Service for creating team member documentation."""

    def __init__(self):
        """Initialize Google Docs service if credentials are available."""
        self.docs_service = None
        self._team_management_folder_id = None

        if GoogleDocsService:
            try:
                credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH")
                folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
                delegated_email = os.getenv("GOOGLE_DELEGATED_USER_EMAIL")

                if credentials_path and os.path.exists(credentials_path):
                    self.docs_service = GoogleDocsService(
                        credentials_path=credentials_path,
                        default_folder_id=folder_id,
                        delegated_user_email=delegated_email,
                    )
            except Exception as e:
                print(f"Warning: Could not initialize Google Docs service: {e}")

    def is_available(self) -> bool:
        """Check if Google Docs service is available."""
        return self.docs_service is not None

    def get_team_management_folder(self) -> Optional[str]:
        """
        Get or create the Team Management folder.

        Returns:
            Folder ID of the Team Management folder
        """
        if not self.is_available():
            return None

        if self._team_management_folder_id:
            return self._team_management_folder_id

        try:
            self._team_management_folder_id = self.docs_service.get_or_create_folder(
                "Team Management"
            )
            return self._team_management_folder_id
        except Exception as e:
            print(f"Error creating Team Management folder: {e}")
            return None

    def create_team_member_profile(
        self, member_data: dict, team_name: Optional[str] = None
    ) -> Optional[dict]:
        """
        Create a Google Doc profile for a team member in the Team Management folder.

        Args:
            member_data: Dict with keys: name, email, phone, team, role, bio
            team_name: Optional team name for roster update

        Returns:
            Dict with doc_id and url, or None if failed
        """
        if not self.is_available():
            return None

        try:
            # Get Team Management folder
            folder_id = self.get_team_management_folder()
            if not folder_id:
                print("Warning: Could not get Team Management folder, using default")
                folder_id = None

            doc = self.docs_service.create_from_template(
                "team_member_profile", member_data, folder_id=folder_id
            )
            return {"doc_id": doc.id, "url": doc.url}
        except Exception as e:
            print(f"Error creating Google Doc: {e}")
            return None

    def create_team_folder_structure(self, team_name: str) -> Optional[dict]:
        """
        Create folder structure for a team.

        Returns:
            Dict with folder_id, overview_doc_id, overview_doc_url, roster_sheet_id, roster_sheet_url
        """
        if not self.is_available():
            return None

        try:
            return self.docs_service.create_team_folder_structure(team_name)
        except Exception as e:
            print(f"Error creating team folder structure: {e}")
            return None

    def add_member_to_roster(
        self,
        roster_sheet_id: str,
        member_name: str,
        discord_username: str,
        email: str,
        role: str,
        profile_url: str,
    ) -> bool:
        """
        Add a team member to the roster spreadsheet.

        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            return False

        try:
            return self.docs_service.add_member_to_roster(
                spreadsheet_id=roster_sheet_id,
                member_name=member_name,
                discord_username=discord_username,
                email=email,
                role=role,
                profile_url=profile_url,
            )
        except Exception as e:
            print(f"Error adding member to roster: {e}")
            return False


class ClickUpService:
    """Service for interacting with ClickUp API."""

    def __init__(self, api_token: str):
        self.api_token = api_token
        self.base_url = "https://api.clickup.com/api/v2"
        self.headers = {"Authorization": api_token, "Content-Type": "application/json"}

    async def validate_token(self) -> tuple[bool, Optional[str]]:
        """
        Validate ClickUp API token by making a test request.

        Returns:
            tuple: (is_valid, error_message)
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/user", headers=self.headers, timeout=10.0
                )

                if response.status_code == 200:
                    return True, None
                elif response.status_code == 401:
                    return (
                        False,
                        "Invalid API token. Please check your token and try again.",
                    )
                else:
                    return False, f"Unexpected error: {response.status_code}"
            except httpx.TimeoutException:
                return False, "Request timed out. Please try again."
            except Exception as e:
                return False, f"Error validating token: {str(e)}"

    async def get_user_info(self) -> Optional[dict]:
        """Get authenticated user info from ClickUp."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/user", headers=self.headers, timeout=10.0
                )

                if response.status_code == 200:
                    return response.json().get("user")
                return None
            except Exception:
                return None

    async def get_all_teams(self) -> list[dict]:
        """Get all teams the authenticated user has access to."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/team", headers=self.headers, timeout=10.0
                )

                if response.status_code == 200:
                    return response.json().get("teams", [])
                return []
            except Exception:
                return []

    async def get_all_tasks(self, assigned_only: bool = True) -> list[dict]:
        """
        Get all tasks assigned to the authenticated user across all teams/spaces.

        Args:
            assigned_only: If True, only return tasks assigned to the authenticated user

        Returns:
            List of task dictionaries
        """
        all_tasks = []

        async with httpx.AsyncClient() as client:
            try:
                # Get user info first
                user_info = await self.get_user_info()
                if not user_info:
                    return []

                user_id = user_info.get("id")

                # Get all teams
                teams = await self.get_all_teams()

                for team in teams:
                    team_id = team.get("id")
                    if not team_id:
                        continue

                    # Get tasks for this team using the team endpoint
                    params = {
                        "subtasks": "true",
                        "include_closed": "false",
                    }

                    if assigned_only and user_id:
                        params["assignees[]"] = user_id

                    try:
                        response = await client.get(
                            f"{self.base_url}/team/{team_id}/task",
                            headers=self.headers,
                            params=params,
                            timeout=15.0,
                        )

                        if response.status_code == 200:
                            tasks = response.json().get("tasks", [])
                            all_tasks.extend(tasks)
                    except Exception:
                        continue

                return all_tasks
            except Exception:
                return []

    async def get_tasks(self, list_id: str, assigned_only: bool = True) -> list[dict]:
        """
        Get tasks from a ClickUp list.

        Args:
            list_id: ClickUp list ID
            assigned_only: If True, only return tasks assigned to the authenticated user

        Returns:
            List of task dictionaries
        """
        async with httpx.AsyncClient() as client:
            try:
                params = {}
                if assigned_only:
                    user_info = await self.get_user_info()
                    if user_info:
                        params["assignees[]"] = user_info.get("id")

                response = await client.get(
                    f"{self.base_url}/list/{list_id}/task",
                    headers=self.headers,
                    params=params,
                    timeout=10.0,
                )

                if response.status_code == 200:
                    return response.json().get("tasks", [])
                return []
            except Exception:
                return []
