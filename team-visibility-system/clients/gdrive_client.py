import os
from typing import Any, Dict, List, Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleDriveClient:
    """Client for reading Google Docs containing weekly goals and deliverables."""

    # Scopes required for read-only access to Google Docs
    SCOPES = ["https://www.googleapis.com/auth/documents.readonly"]

    def __init__(self, credentials_path: str):
        """
        Initialize Google Drive client.

        Args:
            credentials_path: Path to service account credentials JSON file
        """
        self.credentials_path = credentials_path
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Google Drive API using service account."""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path, scopes=self.SCOPES
            )
            self.service = build("docs", "v1", credentials=credentials)
        except Exception as e:
            raise Exception(f"Failed to authenticate with Google Drive: {str(e)}")

    def read_document(self, document_id: str) -> Dict[str, Any]:
        """
        Read a Google Doc and return its content.

        Args:
            document_id: The Google Doc ID from the URL

        Returns:
            Dict containing document metadata and content
        """
        try:
            document = self.service.documents().get(documentId=document_id).execute()
            return document
        except HttpError as e:
            raise Exception(f"Failed to read document {document_id}: {str(e)}")

    def extract_text_from_document(self, document: Dict[str, Any]) -> str:
        """
        Extract plain text from Google Doc structure.

        Args:
            document: Document dict from read_document()

        Returns:
            Plain text content of the document
        """
        text_parts = []

        content = document.get("body", {}).get("content", [])

        for element in content:
            if "paragraph" in element:
                paragraph = element["paragraph"]
                for text_run in paragraph.get("elements", []):
                    if "textRun" in text_run:
                        text_parts.append(text_run["textRun"]["content"])

        return "".join(text_parts)

    def parse_weekly_goals(self, document_id: str) -> Dict[str, Any]:
        """
        Parse a weekly goals document into structured data.

        Args:
            document_id: The Google Doc ID

        Returns:
            Dict with parsed goals, deliverables, and risks
        """
        document = self.read_document(document_id)
        text = self.extract_text_from_document(document)

        # Parse the document structure
        parsed = {
            "title": document.get("title", "Untitled"),
            "document_id": document_id,
            "full_text": text,
            "goals": [],
            "deliverables": [],
            "risks": [],
        }

        # Simple parsing logic - split by sections
        lines = text.strip().split("\n")
        current_section = None
        current_goal = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detect sections
            if "WEEKLY GOALS" in line.upper() or "GOALS" == line.upper():
                current_section = "goals"
                continue
            elif "DELIVERABLES" in line.upper():
                current_section = "deliverables"
                continue
            elif "RISKS" in line.upper() or "BLOCKERS" in line.upper():
                current_section = "risks"
                continue
            elif "SUCCESS CRITERIA" in line.upper():
                current_section = "success_criteria"
                continue

            # Parse goals (numbered items like "1. Goal name")
            if current_section == "goals" and line[0].isdigit() and ". " in line:
                # New goal
                goal_text = line.split(". ", 1)[1] if ". " in line else line
                current_goal = {
                    "title": goal_text,
                    "deliverables": [],
                    "success_criteria": [],
                }
                parsed["goals"].append(current_goal)

            # Parse deliverables
            elif current_section == "deliverables" and line.startswith("-"):
                deliverable = line.lstrip("- ").strip()
                if current_goal is not None:
                    current_goal["deliverables"].append(deliverable)
                else:
                    parsed["deliverables"].append(deliverable)

            # Parse success criteria
            elif current_section == "success_criteria" and line.startswith("-"):
                criteria = line.lstrip("- ").strip()
                if current_goal is not None:
                    current_goal["success_criteria"].append(criteria)

            # Parse risks
            elif current_section == "risks" and line.startswith("-"):
                risk = line.lstrip("- ").strip()
                parsed["risks"].append(risk)

        return parsed

    def get_document_title(self, document_id: str) -> str:
        """
        Get the title of a Google Doc.

        Args:
            document_id: The Google Doc ID

        Returns:
            Document title
        """
        document = self.read_document(document_id)
        return document.get("title", "Untitled")

    def extract_tags_from_goals(self, parsed_goals: Dict[str, Any]) -> List[str]:
        """
        Extract ClickUp tags mentioned in the goals.

        Looks for tags in format: `tag-name` or #tag-name

        Args:
            parsed_goals: Parsed goals dict from parse_weekly_goals()

        Returns:
            List of tag names
        """
        tags = set()
        text = parsed_goals["full_text"]

        # Find tags in backticks
        import re

        backtick_tags = re.findall(r"`([a-z0-9-]+)`", text)
        tags.update(backtick_tags)

        # Find hashtags
        hashtags = re.findall(r"#([a-z0-9-]+)", text.lower())
        tags.update(hashtags)

        return list(tags)
