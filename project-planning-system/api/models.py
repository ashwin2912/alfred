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
    team_name: Optional[str] = Field(
        None, description="Team name (e.g., Engineering, Product)"
    )
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


class PublishProjectRequest(BaseModel):
    """Request to publish a project to ClickUp."""

    brainstorm_id: str = Field(..., description="Project brainstorm UUID")
    clickup_list_id: str = Field(..., description="ClickUp list ID to create tasks in")
    clickup_api_token: str = Field(..., description="User's ClickUp API token")
    team_name: str = Field(..., description="Team name for assignment logic")


class PublishProjectResponse(BaseModel):
    """Response from publishing a project."""

    brainstorm_id: UUID = Field(..., description="Project ID")
    tasks_created: int = Field(..., description="Number of tasks created")
    tasks_assigned: int = Field(
        ..., description="Number of tasks assigned to team members"
    )
    clickup_list_url: str = Field(..., description="URL to view tasks in ClickUp")
    errors: List[str] = Field(
        default_factory=list, description="Any errors encountered"
    )
