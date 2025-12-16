"""Google Docs service - reusable documentation creator for Alfred."""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .models import Document, DocumentCreate, DocumentSearchResult, DocumentUpdate
from .templates import TeamMemberProfileTemplate


class GoogleDocsService:
    """
    Google Docs documentation service.

    Provides document creation, reading, updating, and organization capabilities
    that can be used by any Alfred component or agent.
    """

    # Scopes for full access to Google Docs, Drive, and Sheets
    SCOPES = [
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/spreadsheets",
    ]

    def __init__(
        self,
        credentials_path: str,
        default_folder_id: Optional[str] = None,
        delegated_user_email: Optional[str] = None,
    ):
        """
        Initialize Google Docs service.

        Args:
            credentials_path: Path to service account credentials JSON file
            default_folder_id: Optional default Google Drive folder ID for documents
            delegated_user_email: Optional email to impersonate (for Workspace domain-wide delegation)
        """
        self.credentials_path = credentials_path
        self.default_folder_id = default_folder_id
        self.delegated_user_email = delegated_user_email
        self.docs_service = None
        self.drive_service = None
        self.sheets_service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Google APIs using service account or OAuth."""
        try:
            # Check if using OAuth (token.pickle) or service account
            if self.credentials_path.endswith(".pickle"):
                # OAuth flow
                import pickle

                from google.auth.transport.requests import Request

                with open(self.credentials_path, "rb") as token:
                    credentials = pickle.load(token)

                # Refresh token if expired
                if credentials.expired and credentials.refresh_token:
                    credentials.refresh(Request())
                    # Save refreshed token
                    with open(self.credentials_path, "wb") as token:
                        pickle.dump(credentials, token)
            else:
                # Service account
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path, scopes=self.SCOPES
                )

                # If delegated user email provided (for Workspace domain-wide delegation)
                if self.delegated_user_email:
                    credentials = credentials.with_subject(self.delegated_user_email)

            self.docs_service = build("docs", "v1", credentials=credentials)
            self.drive_service = build("drive", "v3", credentials=credentials)
            self.sheets_service = build("sheets", "v4", credentials=credentials)
        except Exception as e:
            raise Exception(f"Failed to authenticate with Google: {str(e)}")

    def create_document(
        self,
        title: str,
        content: Optional[str] = None,
        folder_id: Optional[str] = None,
    ) -> Document:
        """
        Create a new Google Doc.

        Args:
            title: Document title
            content: Optional initial content (markdown will be converted)
            folder_id: Optional folder ID (uses default if not provided)

        Returns:
            Document object with ID and URL

        Raises:
            Exception if creation fails
        """
        try:
            # Create document
            doc = self.docs_service.documents().create(body={"title": title}).execute()
            doc_id = doc.get("documentId")

            # Add content if provided
            if content:
                self._write_content(doc_id, content)

            # Move to folder if specified
            target_folder = folder_id or self.default_folder_id
            if target_folder:
                self._move_to_folder(doc_id, target_folder)

            # Get document metadata
            doc_metadata = (
                self.drive_service.files()
                .get(fileId=doc_id, fields="id,name,webViewLink,createdTime,modifiedTime")
                .execute()
            )

            return Document(
                id=doc_id,
                title=doc_metadata["name"],
                url=doc_metadata["webViewLink"],
                created_time=doc_metadata.get("createdTime"),
                modified_time=doc_metadata.get("modifiedTime"),
            )

        except HttpError as e:
            raise Exception(f"Failed to create document: {str(e)}")

    def create_from_template(
        self,
        template_name: str,
        data: Dict[str, Any],
        folder_id: Optional[str] = None,
    ) -> Document:
        """
        Create a document from a template.

        Args:
            template_name: Template name (e.g., "team_member_profile")
            data: Data to populate the template
            folder_id: Optional folder ID

        Returns:
            Document object

        Raises:
            Exception if creation fails or template not found
        """
        # Get template content
        if template_name == "team_member_profile":
            content = TeamMemberProfileTemplate.generate(data)
            title = f"{data.get('name', 'Profile')} - Team Profile"
        else:
            raise ValueError(f"Unknown template: {template_name}")

        return self.create_document(title, content, folder_id)

    def read_document(self, document_id: str) -> Dict[str, Any]:
        """
        Read a Google Doc and return its content.

        Args:
            document_id: Document ID

        Returns:
            Dict containing document metadata and content

        Raises:
            Exception if read fails
        """
        try:
            document = self.docs_service.documents().get(documentId=document_id).execute()
            return document
        except HttpError as e:
            raise Exception(f"Failed to read document {document_id}: {str(e)}")

    def get_document_text(self, document_id: str) -> str:
        """
        Extract plain text from a document.

        Args:
            document_id: Document ID

        Returns:
            Plain text content

        Raises:
            Exception if extraction fails
        """
        try:
            doc = self.read_document(document_id)
            text_parts = []

            content = doc.get("body", {}).get("content", [])
            for element in content:
                if "paragraph" in element:
                    paragraph = element["paragraph"]
                    for text_run in paragraph.get("elements", []):
                        if "textRun" in text_run:
                            text_parts.append(text_run["textRun"]["content"])

            return "".join(text_parts)

        except Exception as e:
            raise Exception(f"Failed to extract text: {str(e)}")

    def update_document(
        self,
        document_id: str,
        updates: DocumentUpdate,
    ) -> Document:
        """
        Update a document.

        Args:
            document_id: Document ID
            updates: DocumentUpdate with fields to update

        Returns:
            Updated Document object

        Raises:
            Exception if update fails
        """
        try:
            # Update title if provided
            if updates.title:
                self.drive_service.files().update(
                    fileId=document_id, body={"name": updates.title}
                ).execute()

            # Replace content if provided
            if updates.content:
                self._replace_content(document_id, updates.content)

            # Append content if provided
            if updates.append_content:
                self._append_content(document_id, updates.append_content)

            # Get updated metadata
            doc_metadata = (
                self.drive_service.files()
                .get(fileId=document_id, fields="id,name,webViewLink,createdTime,modifiedTime")
                .execute()
            )

            return Document(
                id=document_id,
                title=doc_metadata["name"],
                url=doc_metadata["webViewLink"],
                created_time=doc_metadata.get("createdTime"),
                modified_time=doc_metadata.get("modifiedTime"),
            )

        except HttpError as e:
            raise Exception(f"Failed to update document: {str(e)}")

    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document (moves to trash).

        Args:
            document_id: Document ID

        Returns:
            True if successful

        Raises:
            Exception if deletion fails
        """
        try:
            self.drive_service.files().delete(fileId=document_id).execute()
            return True
        except HttpError as e:
            raise Exception(f"Failed to delete document: {str(e)}")

    def search_documents(
        self,
        query: str,
        folder_id: Optional[str] = None,
        max_results: int = 10,
    ) -> DocumentSearchResult:
        """
        Search for documents.

        Args:
            query: Search query
            folder_id: Optional folder to search in
            max_results: Maximum number of results

        Returns:
            DocumentSearchResult with matching documents

        Raises:
            Exception if search fails
        """
        try:
            # Build search query
            search_query = (
                f"name contains '{query}' and mimeType='application/vnd.google-apps.document'"
            )

            if folder_id:
                search_query += f" and '{folder_id}' in parents"

            # Search
            results = (
                self.drive_service.files()
                .list(
                    q=search_query,
                    pageSize=max_results,
                    fields="files(id,name,webViewLink,createdTime,modifiedTime)",
                )
                .execute()
            )

            files = results.get("files", [])

            documents = [
                Document(
                    id=file["id"],
                    title=file["name"],
                    url=file["webViewLink"],
                    created_time=file.get("createdTime"),
                    modified_time=file.get("modifiedTime"),
                )
                for file in files
            ]

            return DocumentSearchResult(documents=documents, total=len(documents))

        except HttpError as e:
            raise Exception(f"Failed to search documents: {str(e)}")

    def list_documents_in_folder(
        self,
        folder_id: Optional[str] = None,
        max_results: int = 50,
    ) -> List[Document]:
        """
        List all documents in a folder.

        Args:
            folder_id: Folder ID (uses default if not provided)
            max_results: Maximum number of results

        Returns:
            List of Document objects

        Raises:
            Exception if listing fails
        """
        target_folder = folder_id or self.default_folder_id
        if not target_folder:
            raise ValueError("No folder ID provided")

        try:
            query = f"'{target_folder}' in parents and mimeType='application/vnd.google-apps.document' and trashed=false"

            results = (
                self.drive_service.files()
                .list(
                    q=query,
                    pageSize=max_results,
                    fields="files(id,name,webViewLink,createdTime,modifiedTime)",
                    orderBy="modifiedTime desc",
                )
                .execute()
            )

            files = results.get("files", [])

            return [
                Document(
                    id=file["id"],
                    title=file["name"],
                    url=file["webViewLink"],
                    created_time=file.get("createdTime"),
                    modified_time=file.get("modifiedTime"),
                )
                for file in files
            ]

        except HttpError as e:
            raise Exception(f"Failed to list documents: {str(e)}")

    def create_folder(
        self,
        folder_name: str,
        parent_folder_id: Optional[str] = None,
    ) -> str:
        """
        Create a new Google Drive folder.

        Args:
            folder_name: Name of the folder
            parent_folder_id: Optional parent folder ID (uses default if not provided)

        Returns:
            Folder ID

        Raises:
            Exception if creation fails
        """
        try:
            folder_metadata = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
            }

            # Set parent folder
            parent_id = parent_folder_id or self.default_folder_id
            if parent_id:
                folder_metadata["parents"] = [parent_id]

            folder = self.drive_service.files().create(body=folder_metadata, fields="id").execute()

            return folder.get("id")

        except HttpError as e:
            raise Exception(f"Failed to create folder: {str(e)}")

    def get_or_create_folder(
        self,
        folder_name: str,
        parent_folder_id: Optional[str] = None,
    ) -> str:
        """
        Get folder ID if exists, otherwise create it.

        Args:
            folder_name: Name of the folder
            parent_folder_id: Optional parent folder ID (uses default if not provided)

        Returns:
            Folder ID

        Raises:
            Exception if operation fails
        """
        try:
            parent_id = parent_folder_id or self.default_folder_id

            # Search for existing folder
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            if parent_id:
                query += f" and '{parent_id}' in parents"

            results = (
                self.drive_service.files()
                .list(q=query, fields="files(id, name)", pageSize=1)
                .execute()
            )

            files = results.get("files", [])

            if files:
                return files[0]["id"]
            else:
                return self.create_folder(folder_name, parent_id)

        except HttpError as e:
            raise Exception(f"Failed to get or create folder: {str(e)}")

    def create_spreadsheet(
        self,
        title: str,
        folder_id: Optional[str] = None,
        headers: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """
        Create a new Google Sheet.

        Args:
            title: Spreadsheet title
            folder_id: Optional folder ID (uses default if not provided)
            headers: Optional list of header values for first row

        Returns:
            Dict with spreadsheet_id and url

        Raises:
            Exception if creation fails
        """
        try:
            # Create spreadsheet
            spreadsheet = {"properties": {"title": title}}

            sheet = (
                self.sheets_service.spreadsheets()
                .create(body=spreadsheet, fields="spreadsheetId,spreadsheetUrl")
                .execute()
            )

            sheet_id = sheet.get("spreadsheetId")
            sheet_url = sheet.get("spreadsheetUrl")

            # Add headers if provided
            if headers:
                self._write_sheet_headers(sheet_id, headers)

            # Move to folder if specified
            target_folder = folder_id or self.default_folder_id
            if target_folder:
                self._move_to_folder(sheet_id, target_folder)

            return {
                "spreadsheet_id": sheet_id,
                "url": sheet_url,
            }

        except HttpError as e:
            raise Exception(f"Failed to create spreadsheet: {str(e)}")

    def append_to_sheet(
        self,
        spreadsheet_id: str,
        values: List[List[Any]],
        sheet_name: str = "Sheet1",
    ) -> bool:
        """
        Append rows to a Google Sheet.

        Args:
            spreadsheet_id: Spreadsheet ID
            values: List of rows to append (each row is a list of values)
            sheet_name: Sheet name (default: "Sheet1")

        Returns:
            True if successful

        Raises:
            Exception if append fails
        """
        try:
            range_name = f"{sheet_name}!A:Z"

            body = {"values": values}

            self.sheets_service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body=body,
            ).execute()

            return True

        except HttpError as e:
            raise Exception(f"Failed to append to sheet: {str(e)}")

    def update_sheet_row(
        self,
        spreadsheet_id: str,
        row_index: int,
        values: List[Any],
        sheet_name: str = "Sheet1",
    ) -> bool:
        """
        Update a specific row in a Google Sheet.

        Args:
            spreadsheet_id: Spreadsheet ID
            row_index: Row number (1-indexed)
            values: List of values for the row
            sheet_name: Sheet name (default: "Sheet1")

        Returns:
            True if successful

        Raises:
            Exception if update fails
        """
        try:
            range_name = f"{sheet_name}!A{row_index}:Z{row_index}"

            body = {"values": [values]}

            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                body=body,
            ).execute()

            return True

        except HttpError as e:
            raise Exception(f"Failed to update sheet row: {str(e)}")

    def create_team_folder_structure(
        self,
        team_name: str,
    ) -> Dict[str, str]:
        """
        Create folder structure for a team.

        Creates:
        - Team folder (e.g., "Engineering")
        - Team Overview document
        - Active Team Members spreadsheet

        Args:
            team_name: Name of the team (e.g., "Engineering", "Product", "Business")

        Returns:
            Dict with folder_id, overview_doc_id, overview_doc_url, roster_sheet_id, roster_sheet_url

        Raises:
            Exception if creation fails
        """
        try:
            # Create team folder
            team_folder_id = self.get_or_create_folder(team_name)

            # Create Team Overview document
            overview_content = f"""# {team_name} Team

## Team Introduction
Welcome to the {team_name} team!

## Team Responsibilities
[Add team responsibilities here]

## Milestones
[Add team milestones here]

## Resources
- Active Team Members: [Link will be in the same folder]
"""
            overview_doc = self.create_document(
                title=f"{team_name} - Team Overview",
                content=overview_content,
                folder_id=team_folder_id,
            )

            # Create Active Team Members spreadsheet
            roster_headers = [
                "Name",
                "Discord Username",
                "Email",
                "Role",
                "Join Date",
                "Profile Link",
            ]

            roster_sheet = self.create_spreadsheet(
                title=f"{team_name} - Active Team Members",
                folder_id=team_folder_id,
                headers=roster_headers,
            )

            return {
                "folder_id": team_folder_id,
                "overview_doc_id": overview_doc.id,
                "overview_doc_url": overview_doc.url,
                "roster_sheet_id": roster_sheet["spreadsheet_id"],
                "roster_sheet_url": roster_sheet["url"],
            }

        except Exception as e:
            raise Exception(f"Failed to create team folder structure: {str(e)}")

    def add_member_to_roster(
        self,
        spreadsheet_id: str,
        member_name: str,
        discord_username: str,
        email: str,
        role: str,
        profile_url: str,
        join_date: Optional[str] = None,
    ) -> bool:
        """
        Add a team member to the roster spreadsheet.

        Args:
            spreadsheet_id: Roster spreadsheet ID
            member_name: Member's full name
            discord_username: Discord username
            email: Email address
            role: Role/title
            profile_url: Link to member's profile document
            join_date: Join date (defaults to today)

        Returns:
            True if successful

        Raises:
            Exception if append fails
        """
        if not join_date:
            join_date = datetime.now().strftime("%Y-%m-%d")

        values = [
            [
                member_name,
                discord_username,
                email,
                role,
                join_date,
                profile_url,
            ]
        ]

        return self.append_to_sheet(spreadsheet_id, values)

    def share_document(
        self,
        document_id: str,
        email: str,
        role: str = "writer",
        send_notification: bool = False,
    ) -> bool:
        """
        Share a document with a user by email.

        Args:
            document_id: Document or file ID
            email: Email address to share with
            role: Permission role - "reader", "writer", "commenter" (default: "writer")
            send_notification: Whether to send email notification (default: False)

        Returns:
            True if successful

        Raises:
            Exception if sharing fails
        """
        try:
            permission = {
                "type": "user",
                "role": role,
                "emailAddress": email,
            }

            self.drive_service.permissions().create(
                fileId=document_id,
                body=permission,
                sendNotificationEmail=send_notification,
                fields="id",
            ).execute()

            return True

        except HttpError as e:
            raise Exception(f"Failed to share document with {email}: {str(e)}")

    def share_document_with_multiple_users(
        self,
        document_id: str,
        emails: List[str],
        role: str = "writer",
        send_notification: bool = False,
    ) -> Dict[str, bool]:
        """
        Share a document with multiple users.

        Args:
            document_id: Document or file ID
            emails: List of email addresses to share with
            role: Permission role - "reader", "writer", "commenter" (default: "writer")
            send_notification: Whether to send email notifications (default: False)

        Returns:
            Dict mapping email to success status

        Example:
            >>> results = service.share_document_with_multiple_users(
            ...     doc_id,
            ...     ["user1@example.com", "user2@example.com"],
            ...     role="writer"
            ... )
            >>> print(results)
            {"user1@example.com": True, "user2@example.com": True}
        """
        results = {}

        for email in emails:
            try:
                self.share_document(document_id, email, role, send_notification)
                results[email] = True
            except Exception as e:
                print(f"Failed to share with {email}: {e}")
                results[email] = False

        return results

    def remove_user_access(
        self,
        document_id: str,
        email: str,
    ) -> bool:
        """
        Remove a user's access to a document.

        Args:
            document_id: Document or file ID
            email: Email address to remove

        Returns:
            True if successful

        Raises:
            Exception if removal fails
        """
        try:
            # List permissions to find the permission ID for this email
            permissions = (
                self.drive_service.permissions()
                .list(fileId=document_id, fields="permissions(id,emailAddress)")
                .execute()
            )

            # Find permission ID for this email
            permission_id = None
            for perm in permissions.get("permissions", []):
                if perm.get("emailAddress") == email:
                    permission_id = perm.get("id")
                    break

            if not permission_id:
                raise Exception(f"No permission found for {email}")

            # Delete the permission
            self.drive_service.permissions().delete(
                fileId=document_id, permissionId=permission_id
            ).execute()

            return True

        except HttpError as e:
            raise Exception(f"Failed to remove access for {email}: {str(e)}")

    def _write_sheet_headers(self, spreadsheet_id: str, headers: List[str]):
        """Write headers to first row of a sheet."""
        range_name = "Sheet1!A1:Z1"

        body = {"values": [headers]}

        self.sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="USER_ENTERED",
            body=body,
        ).execute()

    def _write_content(self, document_id: str, content: str):
        """Write content to a document."""
        requests = [{"insertText": {"location": {"index": 1}, "text": content}}]

        self.docs_service.documents().batchUpdate(
            documentId=document_id, body={"requests": requests}
        ).execute()

    def _replace_content(self, document_id: str, content: str):
        """Replace all content in a document."""
        # Get document to find end index
        doc = self.read_document(document_id)
        end_index = doc.get("body", {}).get("content", [{}])[-1].get("endIndex", 1)

        requests = [
            {"deleteContentRange": {"range": {"startIndex": 1, "endIndex": end_index - 1}}},
            {"insertText": {"location": {"index": 1}, "text": content}},
        ]

        self.docs_service.documents().batchUpdate(
            documentId=document_id, body={"requests": requests}
        ).execute()

    def _append_content(self, document_id: str, content: str):
        """Append content to end of document."""
        doc = self.read_document(document_id)
        end_index = doc.get("body", {}).get("content", [{}])[-1].get("endIndex", 1)

        requests = [{"insertText": {"location": {"index": end_index - 1}, "text": "\n" + content}}]

        self.docs_service.documents().batchUpdate(
            documentId=document_id, body={"requests": requests}
        ).execute()

    def _move_to_folder(self, document_id: str, folder_id: str):
        """Move document to a folder."""
        # Get current parents
        file = self.drive_service.files().get(fileId=document_id, fields="parents").execute()

        previous_parents = ",".join(file.get("parents", []))

        # Move to new folder
        self.drive_service.files().update(
            fileId=document_id,
            addParents=folder_id,
            removeParents=previous_parents,
            fields="id,parents",
        ).execute()


def create_docs_service(
    credentials_path: Optional[str] = None,
    default_folder_id: Optional[str] = None,
    delegated_user_email: Optional[str] = None,
) -> GoogleDocsService:
    """
    Factory function to create GoogleDocsService from environment variables.

    Args:
        credentials_path: Optional path to credentials (uses env var if not provided)
        default_folder_id: Optional default folder ID (uses env var if not provided)
        delegated_user_email: Optional user email to impersonate (uses env var if not provided)

    Returns:
        Configured GoogleDocsService instance
    """
    credentials_path = credentials_path or os.getenv("GOOGLE_CREDENTIALS_PATH")
    default_folder_id = default_folder_id or os.getenv("GOOGLE_DRIVE_FOLDER_ID")
    delegated_user_email = delegated_user_email or os.getenv("GOOGLE_DELEGATED_USER_EMAIL")

    if not credentials_path:
        raise ValueError("GOOGLE_CREDENTIALS_PATH not provided")

    return GoogleDocsService(credentials_path, default_folder_id, delegated_user_email)
