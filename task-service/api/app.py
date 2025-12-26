"""FastAPI application for task service."""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(
    0, str(Path(__file__).parent.parent.parent / "shared-services" / "data-service")
)

from data_service.client import create_data_service
from services.clickup_client import ClickUpClient

from .models import (
    AddCommentRequest,
    AddCommentResponse,
    HealthResponse,
    TaskCommentsResponse,
    TaskResponse,
    UserTasksResponse,
)

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Alfred Task Service",
    description="Platform-agnostic task management service",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

data_service = None


@app.on_event("startup")
async def startup_event():
    global data_service
    logger.info("Initializing Task Service...")
    data_service = create_data_service()
    logger.info("✓ Database service initialized")
    logger.info("🚀 Task Service ready!")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy")


@app.get("/tasks/user/{discord_user_id}", response_model=UserTasksResponse)
async def get_user_tasks(discord_user_id: str):
    """Get all tasks for a user."""
    # Get user from database
    result = (
        data_service.client.table("team_members")
        .select("*")
        .eq("discord_id", discord_user_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")

    member = result.data[0]
    clickup_token = member.get("clickup_api_token")

    if not clickup_token:
        raise HTTPException(status_code=400, detail="ClickUp token not configured")

    # Get user's team lists
    team_name = member.get("team")
    list_ids = None
    if team_name:
        lists_result = (
            data_service.client.table("project_lists")
            .select("clickup_list_id")
            .eq("team_name", team_name)
            .execute()
        )
        if lists_result.data:
            list_ids = [item["clickup_list_id"] for item in lists_result.data]

    # Fetch tasks from ClickUp
    client = ClickUpClient(clickup_token)
    tasks = await client.get_user_tasks(list_ids=list_ids)

    return UserTasksResponse(
        tasks=[TaskResponse(**task) for task in tasks], total_count=len(tasks)
    )


@app.get("/tasks/{task_id}")
async def get_task_details(task_id: str, authorization: str = Header(...)):
    """Get details for a specific task."""
    client = ClickUpClient(authorization)
    task = await client.get_task_details(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


@app.get("/tasks/{task_id}/comments", response_model=TaskCommentsResponse)
async def get_task_comments(task_id: str, authorization: str = Header(...)):
    """Get comments for a task."""
    client = ClickUpClient(authorization)
    comments = await client.get_task_comments(task_id)

    return TaskCommentsResponse(comments=comments)


@app.post("/tasks/{task_id}/comment", response_model=AddCommentResponse)
async def add_task_comment(
    task_id: str, request: AddCommentRequest, authorization: str = Header(...)
):
    """Add a comment to a task."""
    client = ClickUpClient(authorization)
    result = await client.add_task_comment(task_id, request.comment_text)

    if result:
        return AddCommentResponse(success=True, comment_id=result.get("id"))
    else:
        return AddCommentResponse(success=False, error="Failed to add comment")
