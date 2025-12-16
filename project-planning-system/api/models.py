"""API request/response models."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BrainstormRequest(BaseModel):
    """Request to brainstorm a project."""

    project_idea: str = Field(..., description="Description of the project idea")
    discord_user_id: int = Field(..., description="Discord user ID")
    discord_username: str = Field(..., description="Discord username")
    google_drive_folder_id: Optional[str] = Field(
        None, description="Optional folder for the doc"
    )
    team_name: Optional[str] = Field(None, description="Team name (e.g., Engineering, Product)")
    role_name: Optional[str] = Field(None, description="User's role name")


class BrainstormResponse(BaseModel):
    """Response from brainstorming."""

    brainstorm_id: UUID = Field(..., description="Unique ID for this brainstorm")
    title: str = Field(..., description="Generated project title")
    doc_id: str = Field(..., description="Google Doc ID")
    doc_url: str = Field(..., description="Google Doc URL")
    summary: Dict[str, Any] = Field(..., description="Project summary stats")
    analysis: Dict[str, Any] = Field(..., description="Full AI analysis")


class ProjectListItem(BaseModel):
    """Single project in a list."""

    id: UUID
    title: str
    team_name: Optional[str]
    doc_url: Optional[str]
    clickup_list_id: Optional[str]
    created_at: datetime


class ProjectListResponse(BaseModel):
    """Response for listing projects."""

    projects: List[ProjectListItem]
    total: int


class ProjectDetailResponse(BaseModel):
    """Detailed project information."""

    id: UUID
    title: str
    team_name: Optional[str]
    doc_id: Optional[str]
    doc_url: Optional[str]
    clickup_list_id: Optional[str]
    created_at: datetime
    updated_at: datetime


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    anthropic_configured: bool
    google_docs_configured: bool
    database_configured: bool
