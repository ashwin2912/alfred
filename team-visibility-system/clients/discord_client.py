"""Discord client for sending team visibility reports."""

import os
from typing import List, Optional

import requests


class DiscordClient:
    """Client for sending messages to Discord via webhooks or Bot API."""

    def __init__(
        self, webhook_url: Optional[str] = None, bot_token: Optional[str] = None
    ):
        """
        Initialize Discord client.

        Args:
            webhook_url: Discord incoming webhook URL (for simple messaging)
            bot_token: Discord bot token (for advanced API features)
        """
        self.webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
        self.bot_token = bot_token or os.getenv("DISCORD_BOT_TOKEN")

        if not self.webhook_url and not self.bot_token:
            raise ValueError(
                "Either DISCORD_WEBHOOK_URL or DISCORD_BOT_TOKEN must be provided"
            )

    def send_webhook_message(
        self,
        content: str,
        embeds: Optional[List[dict]] = None,
        username: Optional[str] = None,
    ) -> bool:
        """
        Send a message using webhook.

        Args:
            content: Plain text message
            embeds: Optional Discord embeds for rich formatting
            username: Optional username override for webhook

        Returns:
            True if successful, False otherwise
        """
        if not self.webhook_url:
            raise ValueError("DISCORD_WEBHOOK_URL not configured")

        payload = {"content": content}
        if embeds:
            payload["embeds"] = embeds
        if username:
            payload["username"] = username

        try:
            response = requests.post(self.webhook_url, json=payload)
            # Discord returns 204 No Content on success
            return response.status_code in (200, 204)
        except Exception as e:
            print(f"Error sending Discord webhook: {e}")
            return False

    def send_message(
        self, channel_id: str, content: str, embeds: Optional[List[dict]] = None
    ) -> bool:
        """
        Send a message to a specific channel using Bot API.

        Args:
            channel_id: Discord channel ID (numeric string)
            content: Plain text message
            embeds: Optional Discord embeds for rich formatting

        Returns:
            True if successful, False otherwise
        """
        if not self.bot_token:
            raise ValueError("DISCORD_BOT_TOKEN not configured")

        url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        headers = {
            "Authorization": f"Bot {self.bot_token}",
            "Content-Type": "application/json",
        }

        payload = {"content": content}
        if embeds:
            payload["embeds"] = embeds

        try:
            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                return True

            data = response.json()
            error_code = data.get("code", 0)
            error_message = data.get("message", "Unknown error")
            print(f"Discord API error: {error_message} (code: {error_code})")

            if error_code == 10003:
                print(f"Channel '{channel_id}' not found.")
            elif error_code == 50001:
                print(f"Bot lacks access to channel '{channel_id}'.")
            elif error_code == 50013:
                print(f"Bot lacks permission to send messages in '{channel_id}'.")
            elif error_code == 0 and response.status_code == 401:
                print("Invalid bot token. Check your DISCORD_BOT_TOKEN.")

            return False
        except Exception as e:
            print(f"Error sending Discord message: {e}")
            return False

    def upload_file(
        self, channel_id: str, file_path: str, content: Optional[str] = None
    ) -> bool:
        """
        Upload a file to Discord channel.

        Args:
            channel_id: Discord channel ID
            file_path: Path to file to upload
            content: Optional message content to accompany the file

        Returns:
            True if successful, False otherwise
        """
        if not self.bot_token:
            raise ValueError("DISCORD_BOT_TOKEN not configured")

        url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        headers = {"Authorization": f"Bot {self.bot_token}"}

        try:
            with open(file_path, "rb") as f:
                files = {"file": f}
                data = {}
                if content:
                    data["content"] = content

                response = requests.post(url, headers=headers, data=data, files=files)
                return response.status_code == 200
        except Exception as e:
            print(f"Error uploading file to Discord: {e}")
            return False

    def format_report_as_embeds(
        self, report_title: str, report_content: str, report_type: str = "daily"
    ) -> List[dict]:
        """
        Format a report as Discord embeds for rich display.

        Args:
            report_title: Title of the report
            report_content: Markdown content of the report
            report_type: Type of report (daily/weekly)

        Returns:
            List of Discord embed objects
        """
        # Discord embed color (blue for daily, green for weekly)
        color = 0x3498DB if report_type == "daily" else 0x2ECC71
        emoji = "📊" if report_type == "daily" else "📈"

        # Split content into sections that fit Discord's embed limits
        # Discord has a limit of 4096 chars per embed description
        sections = self._split_markdown_into_sections(report_content, max_length=4000)

        embeds = []

        # First embed with title
        first_embed = {
            "title": f"{emoji} {report_title}",
            "color": color,
            "description": sections[0] if sections else "",
            "footer": {
                "text": f"Generated by Alfred Team Visibility System • {report_type.capitalize()} Report"
            },
        }
        embeds.append(first_embed)

        # Additional embeds for overflow content
        for i, section in enumerate(sections[1:], start=2):
            embed = {
                "color": color,
                "description": section,
            }
            # Add footer only to last embed
            if i == len(sections):
                embed["footer"] = {
                    "text": f"Generated by Alfred Team Visibility System • {report_type.capitalize()} Report"
                }
            embeds.append(embed)

        return embeds

    def _split_markdown_into_sections(
        self, content: str, max_length: int = 4000
    ) -> List[str]:
        """
        Split markdown content into sections that fit Discord's embed size limits.

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

        return sections if sections else [""]

    def send_daily_report(
        self, report_content: str, channel_id: Optional[str] = None
    ) -> bool:
        """
        Send a daily report to Discord.

        Args:
            report_content: Markdown-formatted report content
            channel_id: Optional channel ID override (uses webhook if not provided)

        Returns:
            True if successful
        """
        title = "Daily Team Report"
        embeds = self.format_report_as_embeds(title, report_content, "daily")

        if channel_id and self.bot_token:
            return self.send_message(channel_id, "", embeds)
        elif self.webhook_url:
            return self.send_webhook_message("", embeds)
        else:
            raise ValueError("No valid Discord configuration found")

    def send_weekly_report(
        self, report_content: str, channel_id: Optional[str] = None
    ) -> bool:
        """
        Send a weekly report to Discord.

        Args:
            report_content: Markdown-formatted report content
            channel_id: Optional channel ID override (uses webhook if not provided)

        Returns:
            True if successful
        """
        title = "Weekly Team Report"
        embeds = self.format_report_as_embeds(title, report_content, "weekly")

        if channel_id and self.bot_token:
            return self.send_message(channel_id, "", embeds)
        elif self.webhook_url:
            return self.send_webhook_message("", embeds)
        else:
            raise ValueError("No valid Discord configuration found")
