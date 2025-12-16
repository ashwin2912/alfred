"""Data models for Alfred system."""

from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class ExperienceLevel(str, Enum):
    """Experience level for skills."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class MemberStatus(str, Enum):
    """Team member status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class OnboardingStatus(str, Enum):
    """Onboarding request status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Skill(BaseModel):
    """Skill model."""

    name: str
    experience_level: ExperienceLevel
    years_of_experience: Optional[float] = None


class TeamMemberBase(BaseModel):
    """Base team member model with common fields - simplified schema."""

    email: EmailStr
    name: str
    phone: Optional[str] = None
    discord_username: Optional[str] = None
    discord_id: Optional[int] = None
    clickup_api_token: Optional[str] = None
    clickup_user_id: Optional[str] = None
    bio: Optional[str] = None
    role: Optional[str] = None
    team: Optional[str] = None
    manager_id: Optional[UUID] = None
    status: MemberStatus = MemberStatus.ACTIVE
    start_date: Optional[date] = None
    profile_doc_id: Optional[str] = None
    profile_url: Optional[str] = None


class TeamMemberCreate(TeamMemberBase):
    """Create team member model."""

    user_id: UUID  # Supabase auth user ID


class TeamMemberUpdate(BaseModel):
    """Update team member model - all fields optional."""

    name: Optional[str] = None
    discord_username: Optional[str] = None
    clickup_user_id: Optional[str] = None
    clickup_api_token: Optional[str] = None
    bio: Optional[str] = None
    role: Optional[str] = None
    team: Optional[str] = None
    profile_doc_id: Optional[str] = None
    profile_url: Optional[str] = None


class TeamMember(TeamMemberBase):
    """Full team member model with database fields."""

    id: UUID
    user_id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic config."""

        from_attributes = True  # Allows creation from ORM models


# Team and Role Models


class RoleBase(BaseModel):
    """Base role model."""

    name: str
    level: int = Field(ge=1, le=5)
    description: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)
    discord_role_id: Optional[int] = None


class Role(RoleBase):
    """Full role model with database fields."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TeamBase(BaseModel):
    """Base team model."""

    name: str
    description: Optional[str] = None
    team_lead_id: Optional[UUID] = None
    parent_team_id: Optional[UUID] = None
    discord_role_id: Optional[int] = None
    discord_manager_role_id: Optional[int] = None


class TeamCreate(TeamBase):
    """Create team model."""

    pass


class TeamUpdate(BaseModel):
    """Update team model - all fields optional."""

    name: Optional[str] = None
    description: Optional[str] = None
    team_lead_id: Optional[UUID] = None
    parent_team_id: Optional[UUID] = None
    discord_role_id: Optional[int] = None
    drive_folder_id: Optional[str] = None
    overview_doc_id: Optional[str] = None
    overview_doc_url: Optional[str] = None
    roster_sheet_id: Optional[str] = None
    roster_sheet_url: Optional[str] = None


class Team(TeamBase):
    """Full team model with database fields."""

    id: UUID
    drive_folder_id: Optional[str] = None
    overview_doc_id: Optional[str] = None
    overview_doc_url: Optional[str] = None
    roster_sheet_id: Optional[str] = None
    roster_sheet_url: Optional[str] = None
    discord_general_channel_id: Optional[int] = None
    discord_standup_channel_id: Optional[int] = None
    clickup_workspace_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TeamMembershipBase(BaseModel):
    """Base team membership model."""

    team_id: UUID
    member_id: UUID
    role_id: Optional[UUID] = None
    is_active: bool = True


class TeamMembership(TeamMembershipBase):
    """Full team membership model."""

    id: UUID
    joined_at: datetime
    left_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Onboarding Models


class PendingOnboardingCreate(BaseModel):
    """Create pending onboarding request."""

    discord_id: int
    discord_username: str
    name: str
    email: EmailStr
    phone: Optional[str] = None
    role: Optional[str] = None
    team: Optional[str] = None
    bio: Optional[str] = None
    timezone: Optional[str] = "UTC"
    skills: List[Skill] = Field(default_factory=list)


class PendingOnboarding(PendingOnboardingCreate):
    """Full pending onboarding model."""

    id: UUID
    status: OnboardingStatus = OnboardingStatus.PENDING
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[UUID] = None
    rejection_reason: Optional[str] = None

    class Config:
        from_attributes = True


class OnboardingApproval(BaseModel):
    """Approval/rejection data."""

    request_id: UUID
    approved: bool
    rejection_reason: Optional[str] = None
