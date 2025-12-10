"""Supabase authentication service - reusable across Alfred components."""

import os
import secrets
import string
from typing import Dict, Optional

from supabase import Client, create_client

from .models import User, UserCreate, UserSession, UserUpdate


class SupabaseAuthService:
    """
    Supabase authentication service.

    Provides authentication and user management capabilities that can be used
    by any Alfred component or agent.
    """

    def __init__(
        self, supabase_url: str, supabase_key: str, service_role_key: Optional[str] = None
    ):
        """
        Initialize Supabase auth service.

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase anon/public key
            service_role_key: Optional service role key for admin operations
        """
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.service_role_key = service_role_key

        # Client for user operations
        self.client: Client = create_client(supabase_url, supabase_key)

        # Admin client for privileged operations (if service key provided)
        self.admin_client: Optional[Client] = None
        if service_role_key:
            self.admin_client = create_client(supabase_url, service_role_key)

    def _generate_temp_password(self, length: int = 12) -> str:
        """Generate a secure temporary password."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def create_user(
        self,
        email: str,
        role: str = "member",
        metadata: Optional[Dict] = None,
        password: Optional[str] = None,
        send_email: bool = True,
    ) -> Dict:
        """
        Create a new user (admin operation).

        Args:
            email: User email address
            role: User role (member, admin, etc.)
            metadata: Additional user metadata
            password: Optional password (generates temp password if None)
            send_email: Whether to send invitation email

        Returns:
            Dict with user info and temporary password

        Raises:
            Exception if user creation fails
        """
        if not self.admin_client:
            raise ValueError("Service role key required for creating users")

        # Generate temp password if not provided
        temp_password = password or self._generate_temp_password()

        # Prepare user metadata
        user_metadata = metadata or {}
        user_metadata["role"] = role
        user_metadata["onboarding_complete"] = False

        try:
            # Create user with Supabase admin API
            response = self.admin_client.auth.admin.create_user(
                {
                    "email": email,
                    "password": temp_password,
                    "email_confirm": not send_email,  # Auto-confirm if not sending email
                    "user_metadata": user_metadata,
                }
            )

            return {
                "user_id": response.user.id,
                "email": response.user.email,
                "temporary_password": temp_password,
                "role": role,
                "metadata": user_metadata,
                "invitation_sent": send_email,
            }

        except Exception as e:
            raise Exception(f"Failed to create user: {str(e)}")

    def sign_in(self, email: str, password: str) -> UserSession:
        """
        Sign in a user.

        Args:
            email: User email
            password: User password

        Returns:
            UserSession with tokens and user info

        Raises:
            Exception if sign in fails
        """
        try:
            response = self.client.auth.sign_in_with_password(
                {
                    "email": email,
                    "password": password,
                }
            )

            user = User(
                id=response.user.id,
                email=response.user.email,
                role=response.user.user_metadata.get("role", "member"),
                metadata=response.user.user_metadata,
                created_at=response.user.created_at,
                email_confirmed_at=response.user.email_confirmed_at,
                last_sign_in_at=response.user.last_sign_in_at,
            )

            return UserSession(
                access_token=response.session.access_token,
                refresh_token=response.session.refresh_token,
                expires_at=response.session.expires_at,
                expires_in=response.session.expires_in,
                user=user,
            )

        except Exception as e:
            raise Exception(f"Sign in failed: {str(e)}")

    def sign_out(self, access_token: str) -> bool:
        """
        Sign out a user.

        Args:
            access_token: User's access token

        Returns:
            True if successful

        Raises:
            Exception if sign out fails
        """
        try:
            # Set the session for this request
            self.client.auth.set_session(access_token, "")
            self.client.auth.sign_out()
            return True
        except Exception as e:
            raise Exception(f"Sign out failed: {str(e)}")

    def get_user(self, access_token: str) -> User:
        """
        Get current user from access token.

        Args:
            access_token: User's access token

        Returns:
            User object

        Raises:
            Exception if user retrieval fails
        """
        try:
            # Set the session
            self.client.auth.set_session(access_token, "")

            # Get user
            response = self.client.auth.get_user()

            return User(
                id=response.user.id,
                email=response.user.email,
                role=response.user.user_metadata.get("role", "member"),
                metadata=response.user.user_metadata,
                created_at=response.user.created_at,
                email_confirmed_at=response.user.email_confirmed_at,
                last_sign_in_at=response.user.last_sign_in_at,
            )

        except Exception as e:
            raise Exception(f"Failed to get user: {str(e)}")

    def update_user(
        self,
        user_id: str,
        updates: UserUpdate,
    ) -> User:
        """
        Update user information (admin operation).

        Args:
            user_id: User ID to update
            updates: UserUpdate model with fields to update

        Returns:
            Updated User object

        Raises:
            Exception if update fails
        """
        if not self.admin_client:
            raise ValueError("Service role key required for updating users")

        try:
            # Prepare update data
            update_data = {}

            if updates.email:
                update_data["email"] = updates.email

            if updates.password:
                update_data["password"] = updates.password

            if updates.metadata:
                update_data["user_metadata"] = updates.metadata

            if updates.role:
                if "user_metadata" not in update_data:
                    update_data["user_metadata"] = {}
                update_data["user_metadata"]["role"] = updates.role

            # Update user
            response = self.admin_client.auth.admin.update_user_by_id(user_id, update_data)

            return User(
                id=response.user.id,
                email=response.user.email,
                role=response.user.user_metadata.get("role", "member"),
                metadata=response.user.user_metadata,
                created_at=response.user.created_at,
                email_confirmed_at=response.user.email_confirmed_at,
                last_sign_in_at=response.user.last_sign_in_at,
            )

        except Exception as e:
            raise Exception(f"Failed to update user: {str(e)}")

    def update_user_metadata(
        self,
        user_id: str,
        metadata: Dict,
        merge: bool = True,
    ) -> User:
        """
        Update user metadata (admin operation).

        Args:
            user_id: User ID
            metadata: Metadata to update
            merge: If True, merge with existing metadata; if False, replace

        Returns:
            Updated User object
        """
        if not self.admin_client:
            raise ValueError("Service role key required for updating metadata")

        try:
            # Get current user if merging
            if merge:
                current_user = self.admin_client.auth.admin.get_user_by_id(user_id)
                current_metadata = current_user.user.user_metadata or {}
                metadata = {**current_metadata, **metadata}

            # Update metadata
            response = self.admin_client.auth.admin.update_user_by_id(
                user_id, {"user_metadata": metadata}
            )

            return User(
                id=response.user.id,
                email=response.user.email,
                role=response.user.user_metadata.get("role", "member"),
                metadata=response.user.user_metadata,
                created_at=response.user.created_at,
                email_confirmed_at=response.user.email_confirmed_at,
                last_sign_in_at=response.user.last_sign_in_at,
            )

        except Exception as e:
            raise Exception(f"Failed to update metadata: {str(e)}")

    def delete_user(self, user_id: str) -> bool:
        """
        Delete a user (admin operation).

        Args:
            user_id: User ID to delete

        Returns:
            True if successful

        Raises:
            Exception if deletion fails
        """
        if not self.admin_client:
            raise ValueError("Service role key required for deleting users")

        try:
            self.admin_client.auth.admin.delete_user(user_id)
            return True
        except Exception as e:
            raise Exception(f"Failed to delete user: {str(e)}")

    def list_users(self, page: int = 1, per_page: int = 50) -> list[User]:
        """
        List all users (admin operation).

        Args:
            page: Page number (1-indexed)
            per_page: Users per page

        Returns:
            List of User objects

        Raises:
            Exception if listing fails
        """
        if not self.admin_client:
            raise ValueError("Service role key required for listing users")

        try:
            response = self.admin_client.auth.admin.list_users(page=page, per_page=per_page)

            return [
                User(
                    id=user.id,
                    email=user.email,
                    role=user.user_metadata.get("role", "member"),
                    metadata=user.user_metadata,
                    created_at=user.created_at,
                    email_confirmed_at=user.email_confirmed_at,
                    last_sign_in_at=user.last_sign_in_at,
                )
                for user in response
            ]

        except Exception as e:
            raise Exception(f"Failed to list users: {str(e)}")


def create_auth_service(
    supabase_url: Optional[str] = None,
    supabase_key: Optional[str] = None,
    service_role_key: Optional[str] = None,
) -> SupabaseAuthService:
    """
    Factory function to create SupabaseAuthService from environment variables.

    Args:
        supabase_url: Optional Supabase URL (uses env var if not provided)
        supabase_key: Optional Supabase key (uses env var if not provided)
        service_role_key: Optional service role key (uses env var if not provided)

    Returns:
        Configured SupabaseAuthService instance
    """
    supabase_url = supabase_url or os.getenv("SUPABASE_URL")
    supabase_key = supabase_key or os.getenv("SUPABASE_KEY")
    service_role_key = service_role_key or os.getenv("SUPABASE_SERVICE_KEY")

    if not supabase_url:
        raise ValueError("SUPABASE_URL not provided")
    if not supabase_key:
        raise ValueError("SUPABASE_KEY not provided")

    return SupabaseAuthService(supabase_url, supabase_key, service_role_key)
