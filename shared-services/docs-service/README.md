# Docs Service

Google Docs documentation service for Alfred - reusable knowledge base creator.

## Features

- 📝 Create documents from templates or plain content
- 📖 Read and extract document content
- ✏️ Update existing documents
- 🗂️ Organize documents in folders
- 🔍 Search documents
- 📋 Pre-built templates (team profiles, meeting notes, project docs)
- 🤖 Agent-friendly API

## Installation

```bash
cd shared-services/docs-service
uv pip install -e .
```

## Configuration

Set environment variables:

```bash
GOOGLE_CREDENTIALS_PATH=./creds/service-account.json
GOOGLE_DRIVE_FOLDER_ID=your-default-folder-id  # Optional
```

## Usage

### Create Docs Service

```python
from docs_service import create_docs_service

# Uses environment variables
docs = create_docs_service()

# Or provide credentials directly
docs = create_docs_service(
    credentials_path="./creds/service-account.json",
    default_folder_id="folder-id"
)
```

### Create Documents

```python
# Create from template
doc = docs.create_from_template(
    template_name="team_member_profile",
    data={
        "name": "Alice Smith",
        "email": "alice@example.com",
        "role": "Senior Developer",
        "bio": "Full-stack developer with 5 years experience",
        "timezone": "America/New_York",
        "availability": "40 hours/week",
        "skills": [
            {"name": "Python", "experience_level": "Expert", "years_of_experience": 5},
            {"name": "FastAPI", "experience_level": "Advanced", "years_of_experience": 3},
        ],
        "preferred_tasks": ["backend", "api", "database"],
        "links": {
            "github": "https://github.com/alice",
            "linkedin": "https://linkedin.com/in/alice"
        }
    },
    folder_id="team-profiles-folder"
)

print(f"Created: {doc.url}")

# Create blank document
doc = docs.create_document(
    title="Meeting Notes",
    content="# Meeting Notes\n\nDate: 2025-01-15\n",
    folder_id="meetings-folder"
)
```

### Read Documents

```python
# Read full document structure
doc_data = docs.read_document(document_id="doc-123")

# Extract plain text
text = docs.get_document_text(document_id="doc-123")
print(text)
```

### Update Documents

```python
from docs_service import DocumentUpdate

# Update title and replace content
docs.update_document(
    document_id="doc-123",
    updates=DocumentUpdate(
        title="Updated Title",
        content="New content here"
    )
)

# Append content
docs.update_document(
    document_id="doc-123",
    updates=DocumentUpdate(
        append_content="\n\n## New Section\n\nAdditional info..."
    )
)
```

### Search and List

```python
# Search documents
results = docs.search_documents(
    query="Alice",
    folder_id="team-profiles-folder",
    max_results=10
)

for doc in results.documents:
    print(f"{doc.title}: {doc.url}")

# List all documents in folder
documents = docs.list_documents_in_folder(
    folder_id="team-profiles-folder",
    max_results=50
)
```

### Delete Documents

```python
# Delete (move to trash)
docs.delete_document(document_id="doc-123")
```

## Templates

### Team Member Profile

```python
doc = docs.create_from_template(
    template_name="team_member_profile",
    data={
        "name": "Alice Smith",
        "email": "alice@example.com",
        "role": "Developer",
        "bio": "...",
        "skills": [...],
        "preferred_tasks": [...],
        "links": {...}
    }
)
```

Output format:
```
# Alice Smith

## Contact Information
- Email: alice@example.com
- Role: Developer
- Timezone: America/New_York

## About
[Bio content]

## Skills & Expertise
### Python
- Proficiency: Expert
- Experience: 5 years

## Preferred Task Types
- backend
- api

## Links
- GitHub: https://github.com/alice
```

## Agent Usage

Agents can use this service to create any documentation:

```python
from docs_service import create_docs_service

docs = create_docs_service()

# Agent documents a team member
doc = docs.create_from_template(
    template_name="team_member_profile",
    data=member_data,
    folder_id="team-profiles"
)

# Agent responds
print(f"✅ Profile created: {doc.url}")
print(f"📄 Document ID: {doc.id}")
```

## Google Cloud Setup

1. **Create Service Account:**
   - Go to Google Cloud Console
   - Create new service account
   - Download JSON key file

2. **Enable APIs:**
   - Google Docs API
   - Google Drive API

3. **Grant Permissions:**
   - Share your Google Drive folder with the service account email
   - Give "Editor" access

4. **Set Environment Variable:**
   ```bash
   GOOGLE_CREDENTIALS_PATH=./path/to/service-account.json
   ```

## Error Handling

All methods raise `Exception` with descriptive messages:

```python
try:
    doc = docs.create_document(title="Test")
except Exception as e:
    print(f"Error: {e}")
```

## Integration Examples

### With FastAPI
```python
from fastapi import Depends
from docs_service import create_docs_service

docs = create_docs_service()

@app.post("/profiles")
async def create_profile(data: dict):
    doc = docs.create_from_template("team_member_profile", data)
    return {"document_url": doc.url}
```

### With Streamlit
```python
import streamlit as st
from docs_service import create_docs_service

docs = create_docs_service()

if st.button("Create Profile"):
    doc = docs.create_from_template("team_member_profile", form_data)
    st.success(f"Created: {doc.url}")
```

## License

Part of Alfred - Digital butler for distributed teams.
