#!/usr/bin/env python3
"""
Reset database for testing.

This script:
1. Deletes all records from pending_onboarding
2. Deletes all records from team_members
3. Optionally keeps your admin account

Run this to start fresh for testing.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Add shared-services to path
shared_services_path = parent_dir.parent / "shared-services"
sys.path.insert(0, str(shared_services_path))
sys.path.insert(0, str(shared_services_path / "data-service"))

from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()


def main():
    """Reset database tables."""
    print("⚠️  WARNING: This will delete all data from:")
    print("   - pending_onboarding")
    print("   - team_members")
    print()

    confirm = input("Are you sure you want to continue? (type 'yes' to confirm): ")
    if confirm.lower() != "yes":
        print("❌ Cancelled")
        return 1

    # Get admin Discord ID to preserve
    print()
    preserve_admin = input(
        "Enter admin Discord ID to preserve (or press Enter to delete all): "
    )

    # Initialize Supabase
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL or SUPABASE_SERVICE_KEY not found in .env")
        return 1

    supabase = create_client(supabase_url, supabase_key)

    print()
    print("🗑️  Deleting records...")

    # Delete pending_onboarding records
    try:
        if preserve_admin:
            result = (
                supabase.table("pending_onboarding")
                .delete()
                .neq("discord_id", int(preserve_admin))
                .execute()
            )
        else:
            result = (
                supabase.table("pending_onboarding")
                .delete()
                .neq("id", "00000000-0000-0000-0000-000000000000")
                .execute()
            )
        print(f"✅ Deleted pending_onboarding records")
    except Exception as e:
        print(f"⚠️  Error deleting pending_onboarding: {e}")

    # Delete team_members records
    try:
        if preserve_admin:
            result = (
                supabase.table("team_members")
                .delete()
                .neq("discord_id", int(preserve_admin))
                .execute()
            )
        else:
            result = (
                supabase.table("team_members")
                .delete()
                .neq("id", "00000000-0000-0000-0000-000000000000")
                .execute()
            )
        print(f"✅ Deleted team_members records")
    except Exception as e:
        print(f"⚠️  Error deleting team_members: {e}")

    print()
    print("🎉 Database reset complete!")

    if preserve_admin:
        print(f"ℹ️  Preserved admin account with Discord ID: {preserve_admin}")
    else:
        print("⚠️  All records deleted. You'll need to recreate your admin account:")
        print("   python scripts/create_admin.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
