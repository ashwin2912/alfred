from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel


class Comment(BaseModel):
    """Represents a comment on a ClickUp task."""

    id: str
    comment_text: str
    user: str
    date: Optional[int] = None  # Unix timestamp

    @property
    def date_readable(self) -> Optional[str]:
        """Convert Unix timestamp to readable date."""
        if self.date:
            return datetime.fromtimestamp(self.date / 1000).strftime("%Y-%m-%d %H:%M")
        return None


class HistoryEvent(BaseModel):
    """Represents a status change or history event for a task."""

    id: str
    type: str  # e.g., "statusUpdated", "assigneeAdded", etc.
    field: Optional[str] = None
    before: Optional[str] = None
    after: Optional[str] = None
    user: str
    date: Optional[int] = None  # Unix timestamp

    @property
    def date_readable(self) -> Optional[str]:
        """Convert Unix timestamp to readable date."""
        if self.date:
            return datetime.fromtimestamp(self.date / 1000).strftime("%Y-%m-%d %H:%M")
        return None


class ClickUpTask(BaseModel):
    """Enhanced ClickUp task model with comments and history."""

    id: str
    name: str
    status: Optional[str] = "unknown"
    assignees: List[str] = []
    due_date: Optional[str] = None
    priority: Optional[str] = "None"
    tags: List[str] = []
    description: str = "No description provided."
    url: Optional[str] = None
    custom_fields: Dict[str, Union[str, List[str]]] = {}

    # New fields for enhanced tracking
    comments: List[Comment] = []
    history: List[HistoryEvent] = []
    date_created: Optional[int] = None
    date_updated: Optional[int] = None
    time_estimate: Optional[int] = None  # in milliseconds
    time_spent: Optional[int] = None  # in milliseconds

    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if self.due_date:
            try:
                due = int(self.due_date)
                return due < int(datetime.now().timestamp() * 1000)
            except (ValueError, TypeError):
                return False
        return False

    @property
    def has_blockers(self) -> bool:
        """Check if task appears to be blocked."""
        # Check status
        if self.status and "block" in self.status.lower():
            return True
        # Check tags
        if any("block" in tag.lower() for tag in self.tags):
            return True
        return False

    @property
    def comment_count(self) -> int:
        """Return number of comments."""
        return len(self.comments)
