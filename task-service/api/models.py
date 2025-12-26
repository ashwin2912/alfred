"""Pydantic models for task service API."""

from typing import List, Optional

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    clickup_configured: bool = True


class TaskResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    status: dict
    priority: Optional[dict] = None
    due_date: Optional[str] = None
    assignees: List[dict] = []
    tags: List[dict] = []
    url: Optional[str] = None


class UserTasksResponse(BaseModel):
    tasks: List[TaskResponse]
    total_count: int


class CommentResponse(BaseModel):
    id: str
    comment_text: str
    user: dict
    date: str


class TaskCommentsResponse(BaseModel):
    comments: List[CommentResponse]


class AddCommentRequest(BaseModel):
    comment_text: str


class AddCommentResponse(BaseModel):
    success: bool
    comment_id: Optional[str] = None
    error: Optional[str] = None
