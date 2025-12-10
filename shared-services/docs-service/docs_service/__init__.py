"""Google Docs documentation service for Alfred."""

from .google_docs_client import GoogleDocsService, create_docs_service
from .models import Document, DocumentCreate, DocumentUpdate
from .templates import TeamMemberProfileTemplate

__all__ = [
    "GoogleDocsService",
    "create_docs_service",
    "Document",
    "DocumentCreate",
    "DocumentUpdate",
    "TeamMemberProfileTemplate",
]
