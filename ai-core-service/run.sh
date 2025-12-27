#!/bin/bash

# Startup script for Project Planning API

set -e

echo "🚀 Starting Project Planning API..."

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed"
    echo "Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Sync dependencies with uv
echo "📦 Syncing dependencies with uv..."
uv sync

# Check for required environment variables
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  Warning: ANTHROPIC_API_KEY not set"
fi

if [ -z "$GOOGLE_CREDENTIALS_PATH" ]; then
    echo "⚠️  Warning: GOOGLE_CREDENTIALS_PATH not set"
fi

if [ -z "$SUPABASE_URL" ]; then
    echo "⚠️  Warning: SUPABASE_URL not set"
fi

# Start the API server
echo "Starting server on http://0.0.0.0:8001"
uv run python -m api.app
