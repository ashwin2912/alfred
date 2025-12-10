"""Data models for Google Docs service."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class Document(BaseModel):
    """Google Docs document model."""

    id: str
    title: str
    url: str
    created_time: Optional[datetime] = None
    modified_time: Optional[datetime] = None
    metadata: Dict[str, Any] = {}


class DocumentCreate(BaseModel):
    """Model for creating a new document."""

    title: str
    content: Optional[str] = None
    folder_id: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None


class DocumentUpdate(BaseModel):
    """Model for updating a document."""

    title: Optional[str] = None
    content: Optional[str] = None
    append_content: Optional[str] = None


class DocumentSearchResult(BaseModel):
    """Search result for documents."""

    documents: List[Document]
    total: int
