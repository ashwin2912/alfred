FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy shared services first (dependency)
COPY ../shared-services /app/shared-services

# Copy bot requirements and install
COPY discord-bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install shared services
RUN pip install -e /app/shared-services/data-service

# Copy bot code
COPY discord-bot/bot /app/bot
COPY discord-bot/run.sh .
RUN chmod +x run.sh

# Create credentials directory
RUN mkdir -p /app/credentials

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Run bot
CMD ["python", "-m", "bot.bot"]
