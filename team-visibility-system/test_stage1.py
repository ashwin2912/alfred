#!/usr/bin/env python3
"""
Test script for Stage 1: Verify ClickUp data fetching works correctly.
"""

import sys

sys.path.insert(
    0,
    "/Users/ashwindhanasamy/Documents/cave/experiments/alfred/alfred/team-visibility-system",
)

from clients.clickup_client import ClickUpClient
from utils.config import config
from utils.logger import logger


def test_fetch_tasks():
    """Test basic task fetching."""
    logger.info("=" * 60)
    logger.info("STAGE 1 TEST: Fetching ClickUp Tasks")
    logger.info("=" * 60)

    try:
        # Initialize client
        logger.info(f"Initializing ClickUp client...")
        client = ClickUpClient(config.clickup_api_token)

        # Fetch tasks
        logger.info(f"Fetching tasks from list: {config.clickup_list_id}")
        tasks = client.fetch_tasks(config.clickup_list_id, include_closed=False)

        logger.info(f"\n✅ Successfully fetched {len(tasks)} tasks")

        # Display summary of each task
        logger.info("\n" + "=" * 60)
        logger.info("TASK SUMMARY")
        logger.info("=" * 60)

        for i, task in enumerate(tasks, 1):
            logger.info(f"\n{i}. {task.name}")
            logger.info(f"   ID: {task.id}")
            logger.info(f"   Status: {task.status}")
            logger.info(
                f"   Assignees: {', '.join(task.assignees) if task.assignees else 'Unassigned'}"
            )
            logger.info(f"   Priority: {task.priority}")
            logger.info(f"   Tags: {', '.join(task.tags) if task.tags else 'None'}")
            logger.info(f"   URL: {task.url}")

            if task.has_blockers:
                logger.warning(f"   ⚠️  BLOCKER DETECTED")

            if task.is_overdue:
                logger.warning(f"   ⏰ OVERDUE")

        return tasks

    except Exception as e:
        logger.error(f"❌ Error fetching tasks: {str(e)}")
        raise


def test_fetch_with_details():
    """Test fetching tasks with comments."""
    logger.info("\n" + "=" * 60)
    logger.info("TESTING: Fetch Tasks with Comments")
    logger.info("=" * 60)

    try:
        client = ClickUpClient(config.clickup_api_token)

        # Fetch with details (this will be slower)
        logger.info("Fetching tasks with comments...")
        tasks = client.fetch_tasks_with_details(
            config.clickup_list_id, include_closed=False
        )

        logger.info(f"\n✅ Successfully fetched {len(tasks)} tasks with details")

        # Show comment stats
        total_comments = sum(task.comment_count for task in tasks)
        logger.info(f"Total comments across all tasks: {total_comments}")

        # Show tasks with comments
        tasks_with_comments = [t for t in tasks if t.comment_count > 0]
        if tasks_with_comments:
            logger.info(f"\nTasks with comments ({len(tasks_with_comments)}):")
            for task in tasks_with_comments:
                logger.info(f"  - {task.name}: {task.comment_count} comments")
                for comment in task.comments[:2]:  # Show first 2 comments
                    logger.info(
                        f"      └─ {comment.user} ({comment.date_readable}): {comment.comment_text[:50]}..."
                    )

        return tasks

    except Exception as e:
        logger.error(f"❌ Error fetching task details: {str(e)}")
        raise


def test_recent_activity():
    """Test fetching recent activity."""
    logger.info("\n" + "=" * 60)
    logger.info("TESTING: Fetch Recent Activity (Last 24 Hours)")
    logger.info("=" * 60)

    try:
        client = ClickUpClient(config.clickup_api_token)

        recent_tasks = client.fetch_recent_activity(config.clickup_list_id, hours=24)

        logger.info(f"\n✅ Found {len(recent_tasks)} tasks updated in last 24 hours")

        if recent_tasks:
            logger.info("\nRecent activity:")
            for task in recent_tasks:
                logger.info(f"  - {task.name}")
                logger.info(
                    f"    Status: {task.status}, Assignees: {', '.join(task.assignees)}"
                )
        else:
            logger.info("No tasks updated in the last 24 hours")

        return recent_tasks

    except Exception as e:
        logger.error(f"❌ Error fetching recent activity: {str(e)}")
        raise


if __name__ == "__main__":
    logger.info("Starting Stage 1 Tests...\n")

    try:
        # Test 1: Basic task fetching
        tasks = test_fetch_tasks()

        # Test 2: Fetch with comments (optional, can be slow)
        choice = input(
            "\n\nFetch detailed task info including comments? This may be slow. (y/n): "
        )
        if choice.lower() == "y":
            tasks_with_details = test_fetch_with_details()

        # Test 3: Recent activity
        recent = test_recent_activity()

        logger.info("\n" + "=" * 60)
        logger.info("✅ STAGE 1 TESTS COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"\n❌ STAGE 1 TESTS FAILED: {str(e)}")
        sys.exit(1)
