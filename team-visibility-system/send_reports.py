"""
Main script for generating and sending team visibility reports to Slack.

Usage:
    python send_reports.py daily    # Send daily report
    python send_reports.py weekly   # Send weekly report
    python send_reports.py test     # Send test message
"""

import os
import sys

from dotenv import load_dotenv

from ai.report_generator import ReportGenerator
from clients.clickup_client import ClickUpClient
from clients.slack_client import SlackClient

load_dotenv()


def send_daily_report():
    """Generate and send daily report to Slack."""
    print("=" * 80)
    print("GENERATING DAILY REPORT")
    print("=" * 80 + "\n")

    # Initialize clients
    api_token = os.getenv("CLICKUP_API_TOKEN")
    list_id = os.getenv("CLICKUP_LIST_ID")

    if not api_token or not list_id:
        print("❌ Error: Missing CLICKUP_API_TOKEN or CLICKUP_LIST_ID in .env")
        return False

    print("Initializing ClickUp client...")
    clickup_client = ClickUpClient(api_token)

    print("Initializing Slack client...")
    try:
        slack_client = SlackClient()
    except ValueError as e:
        print(f"❌ Error: {e}")
        print(
            "\nPlease set either SLACK_WEBHOOK_URL or SLACK_BOT_TOKEN in your .env file"
        )
        return False

    print("Generating daily report (this may take a minute)...\n")

    # Generate report
    generator = ReportGenerator(clickup_client, list_id)

    try:
        report_content = generator.generate_daily_report(
            include_individual_summaries=True
        )

        # Show preview
        print("Report Preview:")
        print("-" * 80)
        print(
            report_content[:500] + "..."
            if len(report_content) > 500
            else report_content
        )
        print("-" * 80)
        print(f"\nTotal report length: {len(report_content)} characters\n")

        # Send to Slack
        print("Sending to Slack...")
        channel = os.getenv("SLACK_CHANNEL")
        success = slack_client.send_daily_report(report_content, channel)

        if success:
            print("✅ Daily report sent successfully!")
            return True
        else:
            print("❌ Failed to send report to Slack")
            return False

    except Exception as e:
        print(f"❌ Error generating or sending report: {e}")
        import traceback

        traceback.print_exc()
        return False


def send_weekly_report():
    """Generate and send weekly report to Slack."""
    print("=" * 80)
    print("GENERATING WEEKLY REPORT")
    print("=" * 80 + "\n")

    # Initialize clients
    api_token = os.getenv("CLICKUP_API_TOKEN")
    list_id = os.getenv("CLICKUP_LIST_ID")

    if not api_token or not list_id:
        print("❌ Error: Missing CLICKUP_API_TOKEN or CLICKUP_LIST_ID in .env")
        return False

    print("Initializing ClickUp client...")
    clickup_client = ClickUpClient(api_token)

    print("Initializing Slack client...")
    try:
        slack_client = SlackClient()
    except ValueError as e:
        print(f"❌ Error: {e}")
        print(
            "\nPlease set either SLACK_WEBHOOK_URL or SLACK_BOT_TOKEN in your .env file"
        )
        return False

    print("Generating weekly report (this may take 2-3 minutes)...\n")

    # Generate report
    generator = ReportGenerator(clickup_client, list_id)

    try:
        report_content = generator.generate_weekly_report()

        # Show preview
        print("Report Preview:")
        print("-" * 80)
        print(
            report_content[:500] + "..."
            if len(report_content) > 500
            else report_content
        )
        print("-" * 80)
        print(f"\nTotal report length: {len(report_content)} characters\n")

        # Send to Slack
        print("Sending to Slack...")
        channel = os.getenv("SLACK_CHANNEL")
        success = slack_client.send_weekly_report(report_content, channel)

        if success:
            print("✅ Weekly report sent successfully!")
            return True
        else:
            print("❌ Failed to send report to Slack")
            return False

    except Exception as e:
        print(f"❌ Error generating or sending report: {e}")
        import traceback

        traceback.print_exc()
        return False


def send_test_message():
    """Send a test message to Slack to verify configuration."""
    print("=" * 80)
    print("SENDING TEST MESSAGE")
    print("=" * 80 + "\n")

    try:
        slack_client = SlackClient()
    except ValueError as e:
        print(f"❌ Error: {e}")
        print(
            "\nPlease set either SLACK_WEBHOOK_URL or SLACK_BOT_TOKEN in your .env file"
        )
        return False

    test_message = """
# Test Message from Alfred Team Visibility System

This is a test message to verify your Slack integration is working correctly.

## System Status
✅ Slack client initialized
✅ Connection successful

If you see this message, your Slack integration is configured correctly!

---
_Test message sent from send_reports.py_
"""

    print("Sending test message to Slack...")

    channel = os.getenv("SLACK_CHANNEL")

    # Try to send using the appropriate method
    try:
        if channel and os.getenv("SLACK_BOT_TOKEN"):
            success = slack_client.send_message(channel, test_message)
        else:
            success = slack_client.send_webhook_message(test_message)

        if success:
            print("✅ Test message sent successfully!")
            print(
                f"\nCheck your Slack channel{f' ({channel})' if channel else ''} to verify."
            )
            return True
        else:
            print("❌ Failed to send test message")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python send_reports.py [daily|weekly|test]")
        print("\nCommands:")
        print("  daily   - Generate and send daily team report")
        print("  weekly  - Generate and send weekly team report")
        print("  test    - Send a test message to verify Slack configuration")
        sys.exit(1)

    command = sys.argv[1].lower()

    # Check for required environment variables
    if command != "test":
        missing_vars = []
        if not os.getenv("ANTHROPIC_API_KEY"):
            missing_vars.append("ANTHROPIC_API_KEY")
        if not os.getenv("CLICKUP_API_TOKEN"):
            missing_vars.append("CLICKUP_API_TOKEN")
        if not os.getenv("CLICKUP_LIST_ID"):
            missing_vars.append("CLICKUP_LIST_ID")

        if missing_vars:
            print(
                f"❌ Missing required environment variables: {', '.join(missing_vars)}"
            )
            print("\nPlease add them to your .env file")
            sys.exit(1)

    if command == "daily":
        success = send_daily_report()
    elif command == "weekly":
        success = send_weekly_report()
    elif command == "test":
        success = send_test_message()
    else:
        print(f"Unknown command: {command}")
        print("Valid commands: daily, weekly, test")
        sys.exit(1)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
