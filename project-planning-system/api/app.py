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

from ai.project_brainstormer import ProjectBrainstormer
from data_service.client import create_data_service
from docs_service.google_docs_client import GoogleDocsService
from services.doc_generator import ProjectPlanDocGenerator

from .models import (
    BrainstormRequest,
    BrainstormResponse,
    HealthResponse,
    ProjectDetailResponse,
    ProjectListItem,
    ProjectListResponse,
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
    1. Generates a plain text breakdown with AI (single call)
    2. Pastes the text directly into a Google Doc
    3. Saves everything to the database

    Team leads can then manually edit the doc before creating ClickUp tasks.

    Returns the project details and Google Doc link.
    """
    if not brainstormer:
        raise HTTPException(status_code=503, detail="AI service not configured")

    if not docs_service:
        raise HTTPException(
            status_code=503, detail="Google Docs service not configured"
        )

    try:
        logger.info(
            f"Brainstorm request from {request.discord_username}: {request.project_idea[:100]}..."
        )

        # Generate simple text breakdown with AI (single call)
        logger.info("Generating project breakdown...")
        breakdown_text = brainstormer.generate_simple_breakdown(request.project_idea)

        # Extract a title from the first few lines for database
        title_line = breakdown_text.split('\n')[0].strip()
        if title_line.startswith('#'):
            title = title_line.lstrip('#').strip()
        else:
            # Fallback: use first 50 chars
            title = request.project_idea[:50] + "..." if len(request.project_idea) > 50 else request.project_idea

        # Create Google Doc with plain text
        logger.info("Creating Google Doc...")
        folder_id = request.google_drive_folder_id or docs_service.default_folder_id
        doc = docs_service.create_document(
            title=title,
            content=breakdown_text,
            folder_id=folder_id
        )

        # Save to database with simplified structure
        logger.info("Saving to database...")
        brainstorm_id = await _save_simple_brainstorm(
            request.discord_user_id,
            request.discord_username,
            request.project_idea,
            title,
            breakdown_text,
            doc,
            request.team_name,
            request.role_name,
        )

        logger.info(f"✓ Brainstorm complete: {brainstorm_id}")

        return BrainstormResponse(
            brainstorm_id=brainstorm_id,
            title=title,
            doc_id=doc.id,
            doc_url=doc.url,
            summary={"note": "Simple breakdown - edit in Google Docs before creating tasks"},
            analysis={"breakdown": breakdown_text},
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


async def _save_simple_brainstorm(
    discord_user_id: int,
    discord_username: str,
    raw_idea: str,
    title: str,
    breakdown_text: str,
    doc: any,  # Document object from docs_service
    team_name: Optional[str] = None,
    role_name: Optional[str] = None,
) -> UUID:
    """Save simple brainstorm to database."""

    # Insert into database with minimal fields
    result = (
        data_service.client.table("project_brainstorms")
        .insert(
            {
                "discord_user_id": discord_user_id,
                "discord_username": discord_username,
                "team_name": team_name,
                "title": title,
                "doc_id": doc.id,
                "doc_url": doc.url,
                # clickup_list_id will be added later when tasks are created
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
