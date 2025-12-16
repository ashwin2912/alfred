"""Script to create an admin account with complete setup (bypasses onboarding)."""

import os
import sys
from pathlib import Path
from uuid import uuid4

# Load environment variables from .env
from dotenv import load_dotenv

# Load .env from discord-bot directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Add shared-services to path
shared_services_path = Path(__file__).parent.parent.parent / "shared-services"
sys.path.insert(0, str(shared_services_path))

# Add docs-service to path
docs_service_path = shared_services_path / "docs-service"
sys.path.insert(0, str(docs_service_path))

from data_service import create_data_service

try:
    from docs_service.google_docs_client import GoogleDocsService

    DOCS_AVAILABLE = True
except ImportError:
    DOCS_AVAILABLE = False
    print("⚠️  Google Docs service not available - will skip profile creation")


def create_admin():
    """Create an admin account with complete setup."""
    # Get user info
    print("🔧 Creating Admin Account (Bypass Onboarding)\n")

    discord_id = input("Enter Discord ID: ").strip()
    discord_username = input("Enter Discord username: ").strip()
    name = input("Enter full name: ").strip()
    email = input("Enter email: ").strip()
    phone = input("Enter phone (optional, press Enter to skip): ").strip() or None
    bio = (
        input("Enter bio (optional, press Enter to skip): ").strip() or "Admin account"
    )

    # Convert discord_id to int
    try:
        discord_id = int(discord_id)
    except ValueError:
        print("❌ Invalid Discord ID. Must be a number.")
        return

    # Create data service
    data_service = create_data_service()

    # Check if user already exists
    existing = data_service.get_team_member_by_discord_id(discord_id)
    if existing:
        print(f"\n⚠️  Account already exists: {existing.name} ({existing.email})")
        print(f"   ID: {existing.id}")
        print(f"   Role: {existing.role}")
        overwrite = (
            input("\nDo you want to delete and recreate? (yes/no): ").strip().lower()
        )
        if overwrite == "yes":
            # Delete from team_memberships first (foreign key constraint)
            try:
                data_service.client.table("team_memberships").delete().eq(
                    "member_id", str(existing.id)
                ).execute()
                print(f"✅ Deleted team memberships")
            except:
                pass

            # Delete from team_members
            data_service.client.table("team_members").delete().eq(
                "id", str(existing.id)
            ).execute()
            print(f"✅ Deleted existing account")
        else:
            print("❌ Cancelled")
            return

    print("\n📝 Creating resources...")

    # Step 1: Create Supabase auth user
    print("1️⃣  Creating Supabase auth user...")
    supabase_user_id = None
    temp_password = None

    try:
        supabase_user_id, temp_password = data_service.create_supabase_user(
            email=email, name=name
        )
        print(f"   ✅ Supabase user created")
        print(f"   📧 Email: {email}")
        print(f"   🔑 Temp password: {temp_password}")
    except Exception as e:
        print(f"   ⚠️  Supabase user creation failed: {e}")
        print(f"   ℹ️  Using temporary UUID instead")
        supabase_user_id = uuid4()

    # Step 2: Create Google Doc profile (if available)
    doc_id = None
    doc_url = None

    if DOCS_AVAILABLE:
        print("\n2️⃣  Creating Google Doc profile...")
        try:
            docs_service = GoogleDocsService()

            member_data = {
                "name": name,
                "email": email,
                "phone": phone or "Not provided",
                "team": "Unassigned",
                "role": "Manager",
                "bio": bio,
            }

            # Create profile in main Team Management folder
            profile_result = docs_service.create_team_member_profile(member_data, None)

            if profile_result:
                doc_id = profile_result["doc_id"]
                doc_url = profile_result["url"]
                print(f"   ✅ Google Doc profile created")
                print(f"   📄 {doc_url}")
        except Exception as e:
            print(f"   ⚠️  Google Doc creation failed: {e}")
    else:
        print("\n2️⃣  Skipping Google Doc profile (service not available)")

    # Step 3: Add to main roster spreadsheet (if available)
    if DOCS_AVAILABLE and doc_url:
        print("\n3️⃣  Adding to main roster...")
        try:
            main_roster_id = os.getenv("GOOGLE_MAIN_ROSTER_SHEET_ID")

            if main_roster_id:
                docs_service.add_member_to_roster(
                    roster_sheet_id=main_roster_id,
                    member_name=name,
                    discord_username=discord_username,
                    email=email,
                    role="Manager",
                    profile_url=doc_url,
                )
                print(f"   ✅ Added to main roster")
            else:
                print(f"   ⚠️  GOOGLE_MAIN_ROSTER_SHEET_ID not set in .env")
        except Exception as e:
            print(f"   ⚠️  Roster update failed: {e}")
    else:
        print("\n3️⃣  Skipping main roster (no profile URL)")

    # Step 4: Create team_members record using direct SQL (bypass Pydantic validation)
    print("\n4️⃣  Creating database record...")

    try:
        insert_data = {
            "user_id": str(supabase_user_id),
            "discord_id": discord_id,
            "discord_username": discord_username,
            "name": name,
            "email": email,
            "phone": phone,
            "bio": bio,
            "role": "Manager",
            "status": "active",
            "profile_doc_id": doc_id,
            "profile_url": doc_url,
        }

        # Remove None values
        insert_data = {k: v for k, v in insert_data.items() if v is not None}

        response = (
            data_service.client.table("team_members").insert(insert_data).execute()
        )

        if response.data:
            admin = response.data[0]
            print(f"   ✅ Database record created")

            print(f"\n{'=' * 60}")
            print(f"✅ ADMIN ACCOUNT CREATED SUCCESSFULLY!")
            print(f"{'=' * 60}")
            print(f"\n📋 Account Details:")
            print(f"   ID: {admin['id']}")
            print(f"   Name: {admin['name']}")
            print(f"   Email: {admin['email']}")
            print(f"   Discord: {admin['discord_username']} ({admin['discord_id']})")
            print(f"   Role: {admin['role']}")

            if doc_url:
                print(f"\n📄 Profile: {doc_url}")

            if temp_password:
                print(f"\n🔑 Login Credentials:")
                print(f"   Email: {email}")
                print(f"   Temp Password: {temp_password}")
                print(f"   ⚠️  Please change password after first login")

            print(f"\n🎉 You can now:")
            print(f"   • Approve onboarding requests")
            print(f"   • Create teams with /create-team")
            print(f"   • Add members with /add-to-team")
            print(f"   • Generate reports with /team-report")

        else:
            print(f"   ❌ No data returned from insert")

    except Exception as e:
        print(f"\n❌ Error creating database record: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    create_admin()
