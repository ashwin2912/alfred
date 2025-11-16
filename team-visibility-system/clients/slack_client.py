"""Slack client for sending team visibility reports."""

import os
from typing import List, Optional

import requests


class SlackClient:
    """Client for sending messages to Slack via webhooks or API."""

    def __init__(
        self, webhook_url: Optional[str] = None, bot_token: Optional[str] = None
    ):
        """
        Initialize Slack client.

        Args:
            webhook_url: Slack incoming webhook URL (for simple messaging)
            bot_token: Slack bot token (for advanced API features)
        """
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        self.bot_token = bot_token or os.getenv("SLACK_BOT_TOKEN")

        if not self.webhook_url and not self.bot_token:
            raise ValueError(
                "Either SLACK_WEBHOOK_URL or SLACK_BOT_TOKEN must be provided"
            )

    def send_webhook_message(
        self, text: str, blocks: Optional[List[dict]] = None
    ) -> bool:
        """
        Send a message using webhook.

        Args:
            text: Plain text message (fallback)
            blocks: Optional Slack Block Kit blocks for rich formatting

        Returns:
            True if successful, False otherwise
        """
        if not self.webhook_url:
            raise ValueError("SLACK_WEBHOOK_URL not configured")

        payload = {"text": text}
        if blocks:
            payload["blocks"] = blocks

        try:
            response = requests.post(self.webhook_url, json=payload)
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending Slack webhook: {e}")
            return False

    def send_message(
        self, channel: str, text: str, blocks: Optional[List[dict]] = None
    ) -> bool:
        """
        Send a message to a specific channel using Bot API.

        Args:
            channel: Channel ID or name (e.g., "#general" or "C1234567890")
            text: Plain text message (fallback)
            blocks: Optional Slack Block Kit blocks for rich formatting

        Returns:
            True if successful, False otherwise
        """
        if not self.bot_token:
            raise ValueError("SLACK_BOT_TOKEN not configured")

        url = "https://slack.com/api/chat.postMessage"
        headers = {
            "Authorization": f"Bearer {self.bot_token}",
            "Content-Type": "application/json",
        }

        # Remove # prefix if present - Slack API doesn't need it
        if channel.startswith("#"):
            channel = channel[1:]

        payload = {"channel": channel, "text": text}
        if blocks:
            payload["blocks"] = blocks

        try:
            response = requests.post(url, headers=headers, json=payload)
            data = response.json()

            if not data.get("ok", False):
                error = data.get("error", "Unknown error")
                print(f"Slack API error: {error}")
                if error == "channel_not_found":
                    print(
                        f"Channel '{channel}' not found. Make sure the bot is added to the channel."
                    )
                elif error == "not_in_channel":
                    print(
                        f"Bot needs to be invited to '{channel}'. Add the bot to the channel first."
                    )
                elif error == "invalid_auth":
                    print("Invalid bot token. Check your SLACK_BOT_TOKEN.")
                return False

            return True
        except Exception as e:
            print(f"Error sending Slack message: {e}")
            return False

    def upload_file(
        self, channel: str, file_path: str, title: Optional[str] = None
    ) -> bool:
        """
        Upload a file to Slack channel.

        Args:
            channel: Channel ID or name
            file_path: Path to file to upload
            title: Optional title for the file

        Returns:
            True if successful, False otherwise
        """
        if not self.bot_token:
            raise ValueError("SLACK_BOT_TOKEN not configured")

        url = "https://slack.com/api/files.upload"
        headers = {"Authorization": f"Bearer {self.bot_token}"}

        try:
            with open(file_path, "rb") as f:
                files = {"file": f}
                data = {"channels": channel}
                if title:
                    data["title"] = title

                response = requests.post(url, headers=headers, data=data, files=files)
                result = response.json()
                return result.get("ok", False)
        except Exception as e:
            print(f"Error uploading file to Slack: {e}")
            return False

    def format_report_as_blocks(
        self, report_title: str, report_content: str, report_type: str = "daily"
    ) -> List[dict]:
        """
        Format a report as Slack Block Kit blocks for rich display.

        Args:
            report_title: Title of the report
            report_content: Markdown content of the report
            report_type: Type of report (daily/weekly)

        Returns:
            List of Slack block objects
        """
        emoji = "📊" if report_type == "daily" else "📈"

        # Split content into sections (assuming markdown headers)
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"{emoji} {report_title}"},
            },
            {"type": "divider"},
        ]

        # Convert markdown to Slack mrkdwn format and split into sections
        # Slack has a limit of 3000 chars per text block
        sections = self._split_markdown_into_sections(report_content)

        for section in sections:
            blocks.append(
                {"type": "section", "text": {"type": "mrkdwn", "text": section}}
            )

        blocks.append({"type": "divider"})
        blocks.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"_Generated by Alfred Team Visibility System_ • {report_type.capitalize()} Report",
                    }
                ],
            }
        )

        return blocks

    def _split_markdown_into_sections(
        self, content: str, max_length: int = 2900
    ) -> List[str]:
        """
        Split markdown content into sections that fit Slack's block size limits.

        Args:
            content: Markdown content
            max_length: Max characters per section

        Returns:
            List of content sections
        """
        sections = []
        current_section = ""

        lines = content.split("\n")

        for line in lines:
            # Check if adding this line would exceed the limit
            if len(current_section) + len(line) + 1 > max_length:
                if current_section:
                    sections.append(current_section.strip())
                current_section = line + "\n"
            else:
                current_section += line + "\n"

        # Add the last section
        if current_section:
            sections.append(current_section.strip())

        return sections

    def send_daily_report(
        self, report_content: str, channel: Optional[str] = None
    ) -> bool:
        """
        Send a daily report to Slack.

        Args:
            report_content: Markdown-formatted report content
            channel: Optional channel override (uses webhook if not provided)

        Returns:
            True if successful
        """
        title = "Daily Team Report"
        blocks = self.format_report_as_blocks(title, report_content, "daily")

        if channel and self.bot_token:
            return self.send_message(channel, title, blocks)
        elif self.webhook_url:
            return self.send_webhook_message(title, blocks)
        else:
            raise ValueError("No valid Slack configuration found")

    def send_weekly_report(
        self, report_content: str, channel: Optional[str] = None
    ) -> bool:
        """
        Send a weekly report to Slack.

        Args:
            report_content: Markdown-formatted report content
            channel: Optional channel override (uses webhook if not provided)

        Returns:
            True if successful
        """
        title = "Weekly Team Report"
        blocks = self.format_report_as_blocks(title, report_content, "weekly")

        if channel and self.bot_token:
            return self.send_message(channel, title, blocks)
        elif self.webhook_url:
            return self.send_webhook_message(title, blocks)
        else:
            raise ValueError("No valid Slack configuration found")
