"""Configuration for Discord bot."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Discord settings
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_GUILD_ID = os.getenv("DISCORD_GUILD_ID")

# Supabase settings
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# ClickUp settings
CLICKUP_API_BASE_URL = os.getenv(
    "CLICKUP_API_BASE_URL", "https://api.clickup.com/api/v2"
)

# Validate required settings
if not DISCORD_BOT_TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN is required")
if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL is required")
if not SUPABASE_KEY:
    raise ValueError("SUPABASE_KEY is required")
