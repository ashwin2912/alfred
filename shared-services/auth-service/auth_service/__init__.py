"""Supabase authentication service for Alfred."""

from .models import User, UserCreate, UserSession
from .supabase_client import SupabaseAuthService, create_auth_service

__all__ = [
    "SupabaseAuthService",
    "create_auth_service",
    "User",
    "UserCreate",
    "UserSession",
]
