"""Test Google Docs integration for Discord bot."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add shared-services to path
shared_services_path = Path(__file__).parent.parent / "shared-services"
docs_service_path = shared_services_path / "docs-service"
data_service_path = shared_services_path / "data-service"
sys.path.insert(0, str(shared_services_path))
sys.path.insert(0, str(docs_service_path))
sys.path.insert(0, str(data_service_path))

print("=" * 60)
print("Testing Google Docs Integration for Discord Bot")
print("=" * 60)
print()

# Check environment variables
creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH")
folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
delegated_email = os.getenv("GOOGLE_DELEGATED_USER_EMAIL")

print(f"Credentials Path: {creds_path}")
print(f"Folder ID: {folder_id}")
print(f"Delegated Email: {delegated_email}")
print()

if not creds_path or not os.path.exists(creds_path):
    print("❌ GOOGLE_CREDENTIALS_PATH not set or file doesn't exist")
    exit(1)

if not folder_id:
    print("❌ GOOGLE_DRIVE_FOLDER_ID not set")
    exit(1)

# Test DocsService
print("📋 Step 1: Testing DocsService initialization...")
try:
    from bot.services import DocsService

    docs_service = DocsService()

    if docs_service.is_available():
        print("✅ DocsService initialized successfully!")
    else:
        print("❌ DocsService not available")
        exit(1)
except Exception as e:
    print(f"❌ DocsService initialization failed: {e}")
    import traceback

    traceback.print_exc()
    exit(1)

print()
print("📋 Step 2: Testing profile creation...")
try:
    test_member_data = {
        "name": "Test User (Discord Bot)",
        "email": "test@example.com",
        "phone": "+1 (555) 123-4567",
        "team": "Engineering",
        "role": "Software Engineer",
        "bio": "This is a test profile created by the Discord bot. You can safely delete this.",
    }

    doc_url = docs_service.create_team_member_profile(test_member_data)

    if doc_url:
        print(f"✅ Test profile created successfully!")
        print(f"   URL: {doc_url}")
    else:
        print("❌ Profile creation returned None")
        exit(1)
except Exception as e:
    print(f"❌ Profile creation failed: {e}")
    import traceback

    traceback.print_exc()
    exit(1)

print()
print("=" * 60)
print("✅ All tests passed! Discord bot Google Docs integration is working!")
print("=" * 60)
print()
print("Next steps:")
print("1. Delete the test document if you want")
print("2. Run the Discord bot - it will create profiles on approval")
print("3. Make sure Discord roles match team names (Engineering, Product, Business)")
