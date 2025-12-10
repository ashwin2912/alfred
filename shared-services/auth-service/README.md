# Auth Service

Supabase authentication service for Alfred - reusable across all components.

## Features

- 🔐 User authentication (sign in/out)
- 👤 User management (create, update, delete)
- 🔑 Temporary password generation
- 📧 Email invitations via Supabase
- 🏷️ Role-based access (member, admin, etc.)
- 📝 User metadata management
- 🤖 Agent-friendly API

## Installation

```bash
cd shared-services/auth-service
uv pip install -e .
```

## Configuration

Set environment variables:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key  # For admin operations
```

## Usage

### Create Auth Service

```python
from auth_service import create_auth_service

# Uses environment variables
auth = create_auth_service()

# Or provide credentials directly
auth = create_auth_service(
    supabase_url="https://project.supabase.co",
    supabase_key="anon-key",
    service_role_key="service-key"
)
```

### Admin Operations

```python
# Create a new user
result = auth.create_user(
    email="alice@example.com",
    role="developer",
    metadata={"department": "engineering"},
    send_email=True  # Sends Supabase invitation email
)

print(f"User created: {result['user_id']}")
print(f"Temp password: {result['temporary_password']}")

# Update user metadata
auth.update_user_metadata(
    user_id="uuid",
    metadata={"onboarding_complete": True, "profile_doc_id": "doc-123"}
)

# List all users
users = auth.list_users(page=1, per_page=50)
for user in users:
    print(f"{user.email} - {user.role}")

# Delete user
auth.delete_user(user_id="uuid")
```

### User Operations

```python
# Sign in
session = auth.sign_in(
    email="alice@example.com",
    password="temp-password"
)

print(f"Access token: {session.access_token}")
print(f"User: {session.user.email}")

# Get current user
user = auth.get_user(access_token=session.access_token)
print(f"User metadata: {user.metadata}")

# Sign out
auth.sign_out(access_token=session.access_token)
```

## Agent Usage

Agents can use this service for any authentication needs:

```python
from auth_service import create_auth_service

auth = create_auth_service()

# Agent creates a user
result = auth.create_user(
    email="new.member@company.com",
    role="member",
    metadata={"invited_by": "agent"}
)

# Agent sends notification
print(f"✅ User created: {result['email']}")
print(f"📧 Credentials sent to user")
print(f"🔑 Temp password: {result['temporary_password']}")
```

## Models

### User
- `id`: User UUID
- `email`: Email address
- `role`: User role (member, admin, etc.)
- `metadata`: Custom metadata dict
- `created_at`: Creation timestamp
- `email_confirmed_at`: Email confirmation timestamp
- `last_sign_in_at`: Last sign in timestamp

### UserSession
- `access_token`: JWT access token
- `refresh_token`: JWT refresh token
- `expires_at`: Token expiration timestamp
- `expires_in`: Seconds until expiration
- `user`: User object

## Error Handling

All methods raise `Exception` with descriptive messages:

```python
try:
    auth.create_user(email="invalid-email")
except Exception as e:
    print(f"Error: {e}")
```

## Security Notes

- **Service role key** is required for admin operations (create, update, delete users)
- **Anon key** is sufficient for user sign in/out operations
- Store service role key securely - it has full database access
- Use HTTPS in production
- Supabase handles password hashing automatically

## Supabase Setup

1. Create a project at https://supabase.com
2. Go to Settings → API
3. Copy your:
   - Project URL (`SUPABASE_URL`)
   - Anon/public key (`SUPABASE_KEY`)
   - Service role key (`SUPABASE_SERVICE_KEY`)

4. Configure email templates in Authentication → Email Templates

## Integration Examples

### With FastAPI
```python
from fastapi import Depends, HTTPException
from auth_service import create_auth_service

auth = create_auth_service()

async def get_current_user(token: str = Header(...)):
    try:
        return auth.get_user(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### With Streamlit
```python
import streamlit as st
from auth_service import create_auth_service

auth = create_auth_service()

email = st.text_input("Email")
password = st.text_input("Password", type="password")

if st.button("Sign In"):
    try:
        session = auth.sign_in(email, password)
        st.session_state["token"] = session.access_token
        st.success("Signed in!")
    except Exception as e:
        st.error(f"Failed: {e}")
```

## License

Part of Alfred - Digital butler for distributed teams.
