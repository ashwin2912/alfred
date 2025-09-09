import os
import requests
from dotenv import load_dotenv

load_dotenv()
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

def post_to_slack(message: str) -> None:
    if not SLACK_WEBHOOK_URL:
        raise ValueError("Missing SLACK_WEBHOOK_URL in .env")

    payload = {
        "text": message
    }

    response = requests.post(SLACK_WEBHOOK_URL, json=payload)

    if response.status_code != 200:
        raise Exception(f"Slack webhook failed: {response.status_code} - {response.text}")
