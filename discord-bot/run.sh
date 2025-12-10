#!/bin/bash

# Discord Bot Runner Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Starting Discord Team Bot..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "Error: .env file not found"
    echo "Please copy .env.example to .env and configure it"
    exit 1
fi

# Check if dependencies are installed
if ! uv pip show discord.py > /dev/null 2>&1; then
    echo "Installing dependencies..."
    uv pip install -e .
    uv pip install -e ../shared-services/data-service
fi

# Run the bot
echo "Bot is starting..."
uv run python -m bot.bot
