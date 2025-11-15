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

        # Validate required config
        if not self.clickup_api_token:
            raise ValueError("CLICKUP_API_TOKEN is required in .env file")
        if not self.clickup_list_id:
            raise ValueError("CLICKUP_LIST_ID is required in .env file")

    def validate(self) -> bool:
        """Validate that all required configuration is present."""
        return bool(self.clickup_api_token and self.clickup_list_id)


# Singleton instance
config = Config()
