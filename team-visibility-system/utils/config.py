import os

from dotenv import load_dotenv


class Config:
    """Configuration management for Team Visibility System."""

    def __init__(self):
        """Load configuration from environment variables."""
        load_dotenv()

        # ClickUp Configuration
        self.clickup_api_token = os.getenv("CLICKUP_API_TOKEN", "").strip()
        self.clickup_list_id = os.getenv("CLICKUP_LIST_ID", "").strip()

        # Google Drive Configuration
        self.gdrive_credentials_path = os.getenv("GDRIVE_CREDENTIALS_PATH", "").strip()
        self.weekly_goals_doc_id = os.getenv("WEEKLY_GOALS_DOC_ID", "").strip()

        # Validate required config
        if not self.clickup_api_token:
            raise ValueError("CLICKUP_API_TOKEN is required in .env file")
        if not self.clickup_list_id:
            raise ValueError("CLICKUP_LIST_ID is required in .env file")
        if not self.gdrive_credentials_path:
            raise ValueError("GDRIVE_CREDENTIALS_PATH is required in .env file")
        if not self.weekly_goals_doc_id:
            raise ValueError("WEEKLY_GOALS_DOC_ID is required in .env file")

    def validate(self) -> bool:
        """Validate that all required configuration is present."""
        return bool(
            self.clickup_api_token
            and self.clickup_list_id
            and self.gdrive_credentials_path
            and self.weekly_goals_doc_id
        )


# Singleton instance
config = Config()
