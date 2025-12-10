"""Data models for authentication service."""

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """Model for creating a new user."""

    email: EmailStr
    password: Optional[str] = None  # If None, will generate temporary password
    role: str = "member"
    metadata: Dict = {}


class User(BaseModel):
    """User model."""

    id: str
    email: EmailStr
    role: str
    metadata: Dict = {}
    created_at: datetime
    email_confirmed_at: Optional[datetime] = None
    last_sign_in_at: Optional[datetime] = None


class UserSession(BaseModel):
    """User session model."""

    access_token: str
    refresh_token: str
    expires_at: int
    expires_in: int
    token_type: str = "bearer"
    user: User


class UserUpdate(BaseModel):
    """Model for updating user information."""

    email: Optional[EmailStr] = None
    password: Optional[str] = None
    metadata: Optional[Dict] = None
    role: Optional[str] = None
