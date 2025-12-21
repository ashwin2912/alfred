"""FastAPI application for project planning service."""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional
from uuid import UUID

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(
    0, str(Path(__file__).parent.parent.parent / "shared-services" / "docs-service")
)
sys.path.insert(
    0, str(Path(__file__).parent.parent.parent / "shared-services" / "data-service")
)

from data_service.client import create_data_service
from docs_service.google_docs_client import GoogleDocsService

from ai.project_brainstormer import ProjectBrainstormer
from services.clickup_publisher import ClickUpPublisher
from services.doc_generator import ProjectPlanDocGenerator

from .models import (
    BrainstormRequest,
    BrainstormResponse,
    HealthResponse,
    ProjectDetailResponse,
    ProjectListItem,
    ProjectListResponse,
    PublishProjectRequest,
    PublishProjectResponse,
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Alfred Project Planning API",
    description="AI-powered project planning and brainstorming service",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services on startup
brainstormer: Optional[ProjectBrainstormer] = None
doc_generator: Optional[ProjectPlanDocGenerator] = None
docs_service: Optional[GoogleDocsService] = None
data_service = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global brainstormer, doc_generator, docs_service, data_service

    logger.info("Initializing Project Planning API...")

    try:
        # Initialize AI brainstormer
        brainstormer = ProjectBrainstormer()
        logger.info("✓ AI Brainstormer initialized")

        # Initialize Google Docs service
        credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH")
        default_folder_id = os.getenv("GOOGLE_DRIVE_PROJECT_PLANNING_FOLDER_ID")
        delegated_user = os.getenv("GOOGLE_DELEGATED_USER_EMAIL")

        if credentials_path:
            docs_service = GoogleDocsService(
                credentials_path=credentials_path,
                default_folder_id=default_folder_id,
                delegated_user_email=delegated_user,
            )
            doc_generator = ProjectPlanDocGenerator(docs_service)
            logger.info("✓ Google Docs service initialized")
        else:
            logger.warning(
                "⚠ Google Docs not configured (GOOGLE_CREDENTIALS_PATH missing)"
            )

        # Initialize data service
        data_service = create_data_service()
        logger.info("✓ Database service initialized")

        logger.info("🚀 Project Planning API ready!")

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}", exc_info=True)
        raise


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        anthropic_configured=brainstormer is not None,
        google_docs_configured=docs_service is not None,
        database_configured=data_service is not None,
    )


@app.post("/brainstorm", response_model=BrainstormResponse)
async def brainstorm_project(request: BrainstormRequest):
    """
    Generate a simple project breakdown from an idea.

    This endpoint:
    1. Generates a structured breakdown with AI (single call)
    2. Formats it into a clean Google Doc template
    3. Saves everything to the database

    Team leads can then review/edit the doc before publishing to ClickUp.

    Returns the project details and Google Doc link.
    """
    if not brainstormer:
        raise HTTPException(status_code=503, detail="AI service not configured")

    if not doc_generator:
        raise HTTPException(
            status_code=503, detail="Google Docs service not configured"
        )

    try:
        logger.info(
            f"Brainstorm request from {request.discord_username}: {request.project_idea[:100]}..."
        )

        # Generate structured breakdown with AI (single call, ~10-30 seconds)
        logger.info("Generating project breakdown...")
        breakdown = brainstormer.generate_simple_breakdown(request.project_idea)

        # Create formatted Google Doc
        logger.info("Creating Google Doc...")
        folder_id = request.google_drive_folder_id or docs_service.default_folder_id
        doc_result = doc_generator.generate_simple_breakdown_doc(
            breakdown, folder_id=folder_id
        )

        # Calculate summary stats
        total_tasks = sum(len(phase["subtasks"]) for phase in breakdown["phases"])

        # Save to database
        logger.info("Saving to database...")
        brainstorm_id = await _save_structured_brainstorm(
            request.discord_user_id,
            request.discord_username,
            request.project_idea,
            breakdown,
            doc_result,
            request.team_name,
            request.role_name,
        )

        logger.info(f"✓ Brainstorm complete: {brainstorm_id}")

        return BrainstormResponse(
            brainstorm_id=brainstorm_id,
            title=breakdown["title"],
            doc_id=doc_result["doc_id"],
            doc_url=doc_result["doc_url"],
            summary={
                "total_phases": len(breakdown["phases"]),
                "total_tasks": total_tasks,
                "note": "Review and edit the Google Doc, then use /publish-project to create tasks in ClickUp",
            },
            analysis=breakdown,
        )

    except Exception as e:
        logger.error(f"Brainstorm failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Brainstorm failed: {str(e)}")


@app.get("/projects/{discord_user_id}", response_model=ProjectListResponse)
async def list_user_projects(discord_user_id: int):
    """List all projects for a Discord user."""
    if not data_service:
        raise HTTPException(status_code=503, detail="Database service not configured")

    try:
        logger.info(f"Listing projects for user {discord_user_id}")

        # Query database
        result = (
            data_service.client.table("project_brainstorms")
            .select("*")
            .eq("discord_user_id", discord_user_id)
            .order("created_at", desc=True)
            .execute()
        )

        projects = [
            ProjectListItem(
                id=UUID(item["id"]),
                title=item["title"],
                team_name=item.get("team_name"),
                doc_url=item.get("doc_url"),
                clickup_list_id=item.get("clickup_list_id"),
                created_at=item["created_at"],
            )
            for item in result.data
        ]

        return ProjectListResponse(projects=projects, total=len(projects))

    except Exception as e:
        logger.error(f"Failed to list projects: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to list projects: {str(e)}"
        )


@app.get("/projects/detail/{brainstorm_id}", response_model=ProjectDetailResponse)
async def get_project_detail(brainstorm_id: UUID):
    """Get detailed information about a specific project."""
    if not data_service:
        raise HTTPException(status_code=503, detail="Database service not configured")

    try:
        logger.info(f"Getting project detail: {brainstorm_id}")

        result = (
            data_service.client.table("project_brainstorms")
            .select("*")
            .eq("id", str(brainstorm_id))
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Project not found")

        item = result.data[0]

        return ProjectDetailResponse(
            id=UUID(item["id"]),
            title=item["title"],
            team_name=item.get("team_name"),
            doc_id=item.get("doc_id"),
            doc_url=item.get("doc_url"),
            clickup_list_id=item.get("clickup_list_id"),
            created_at=item["created_at"],
            updated_at=item["updated_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project detail: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get project: {str(e)}")


@app.post("/publish-project", response_model=PublishProjectResponse)
async def publish_project(request: PublishProjectRequest):
    """
    Publish a project plan to ClickUp.

    Takes a brainstorm ID, parses the stored breakdown, and creates tasks in ClickUp.
    """
    if not data_service:
        raise HTTPException(status_code=503, detail="Database service not configured")

    try:
        logger.info(
            f"Publishing project {request.brainstorm_id} to ClickUp list {request.clickup_list_id}"
        )

        # Fetch project from database
        result = (
            data_service.client.table("project_brainstorms")
            .select("*")
            .eq("id", request.brainstorm_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Project not found")

        project = result.data[0]

        # Parse ai_analysis
        if not project.get("ai_analysis"):
            raise HTTPException(
                status_code=400,
                detail="Project has no AI analysis data. It may have been created with an older version.",
            )

        breakdown = json.loads(project["ai_analysis"])

        # Create ClickUp publisher
        publisher = ClickUpPublisher(request.clickup_api_token)

        # Publish to ClickUp
        logger.info("Creating tasks in ClickUp...")
        publish_result = await publisher.publish_project(
            breakdown=breakdown, clickup_list_id=request.clickup_list_id
        )

        tasks_created = publish_result["tasks_created"]
        errors = publish_result["errors"]

        logger.info(f"Created {tasks_created} tasks in ClickUp")

        if errors:
            logger.warning(f"Encountered {len(errors)} errors during publishing")

        # Update database with clickup_list_id
        data_service.client.table("project_brainstorms").update(
            {"clickup_list_id": request.clickup_list_id, "status": "published"}
        ).eq("id", request.brainstorm_id).execute()

        # Get list URL
        list_url = await publisher.get_list_url(request.clickup_list_id)
        if not list_url:
            list_url = f"https://app.clickup.com/t/{request.clickup_list_id}"

        return PublishProjectResponse(
            brainstorm_id=UUID(request.brainstorm_id),
            tasks_created=tasks_created,
            tasks_assigned=0,  # No auto-assignment
            clickup_list_url=list_url,
            errors=errors,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to publish project: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to publish project: {str(e)}"
        )


async def _save_structured_brainstorm(
    discord_user_id: int,
    discord_username: str,
    raw_idea: str,
    breakdown: dict,
    doc_result: dict,
    team_name: Optional[str] = None,
    role_name: Optional[str] = None,
) -> UUID:
    """Save structured brainstorm to database."""

    # Insert into database with structured breakdown
    result = (
        data_service.client.table("project_brainstorms")
        .insert(
            {
                "discord_user_id": discord_user_id,
                "discord_username": discord_username,
                "team_name": team_name,
                "title": breakdown["title"],
                "doc_id": doc_result["doc_id"],
                "doc_url": doc_result["doc_url"],
                "ai_analysis": json.dumps(breakdown),  # Store structured breakdown
                "raw_idea": raw_idea,
                "status": "draft",
                # clickup_list_id will be added later when published
            }
        )
        .execute()
    )

    return UUID(result.data[0]["id"])


async def _save_brainstorm(
    discord_user_id: int,
    discord_username: str,
    raw_idea: str,
    plan: dict,
    doc_result: dict,
    team_name: Optional[str] = None,
    role_name: Optional[str] = None,
) -> UUID:
    """Save brainstorm to database (legacy complex approach - kept for reference)."""

    # Get team member if exists
    try:
        member = data_service.get_team_member_by_discord_id(discord_user_id)
        created_by = str(member.user_id) if member else None
    except:
        created_by = None

    # Insert into database
    result = (
        data_service.client.table("project_brainstorms")
        .insert(
            {
                "discord_user_id": discord_user_id,
                "discord_username": discord_username,
                "created_by": created_by,
                "title": plan["analysis"]["title"],
                "raw_idea": raw_idea,
                "ai_analysis": json.dumps(plan),
                "doc_id": doc_result["doc_id"],
                "doc_url": doc_result["doc_url"],
                "team_name": team_name,
                "role_name": role_name,
                "status": "draft",
            }
        )
        .execute()
    )

    return UUID(result.data[0]["id"])


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
