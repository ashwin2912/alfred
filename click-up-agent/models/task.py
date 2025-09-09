from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel


class ClickUpTask(BaseModel):
    id: str
    name: str
    status: Optional[str] = "unknown"
    assignees: List[str] = []
    due_date: Optional[str] = None
    priority: Optional[str] = "None"
    tags: List[str] = []
    description: str = "No description provided."
    url: Optional[str]
    custom_fields: Dict[str, Union[str, List[str]]] = {}
