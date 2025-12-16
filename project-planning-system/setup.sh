#!/bin/bash

# Setup script for Project Planning API (first time)

set -e

echo "🔧 Setting up Project Planning API..."

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed"
    echo "Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Create virtual environment with uv
echo "📦 Creating virtual environment with uv..."
uv venv

# Install dependencies
echo "📦 Installing dependencies..."
source .venv/bin/activate
uv pip install -e .

# Copy .env.example if .env doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys:"
    echo "   - ANTHROPIC_API_KEY"
    echo "   - GOOGLE_CREDENTIALS_PATH"
    echo "   - SUPABASE_URL"
    echo "   - SUPABASE_SERVICE_KEY"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your API keys"
echo "  2. Run: ./run.sh"
