#!/bin/bash
# Production deployment script for Alfred

set -e

echo "🚀 Starting Alfred deployment..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "Please copy .env.example to .env and configure it"
    exit 1
fi

# Pull latest changes if git repo
if [ -d .git ]; then
    echo "📥 Pulling latest changes..."
    # Discard local changes and pull (preserve credentials)
    git fetch origin
    git reset --hard origin/main
    git clean -fd -e credentials -e .env
fi

# Build and start services
echo "📦 Building Docker images..."
docker compose build --no-cache

echo "🔄 Stopping old containers..."
docker compose down

echo "🚀 Starting services..."
docker compose up -d

echo "⏳ Waiting for services to be healthy..."
sleep 15

# Check health with retries
echo "🏥 Checking service health..."
MAX_RETRIES=5
RETRY_DELAY=5

for i in $(seq 1 $MAX_RETRIES); do
    if curl -f http://localhost:8001/health > /dev/null 2>&1; then
        echo "✅ AI Core Service is healthy"
        break
    else
        if [ $i -eq $MAX_RETRIES ]; then
            echo "❌ AI Core Service failed health check"
            docker compose logs ai-core-service
            exit 1
        fi
        echo "⏳ Waiting for AI Core Service... (attempt $i/$MAX_RETRIES)"
        sleep $RETRY_DELAY
    fi
done

for i in $(seq 1 $MAX_RETRIES); do
    if curl -f http://localhost:8002/health > /dev/null 2>&1; then
        echo "✅ Task Service is healthy"
        break
    else
        if [ $i -eq $MAX_RETRIES ]; then
            echo "❌ Task Service failed health check"
            docker compose logs task-service
            exit 1
        fi
        echo "⏳ Waiting for Task Service... (attempt $i/$MAX_RETRIES)"
        sleep $RETRY_DELAY
    fi
done

# Check Discord bot
if docker compose ps discord-bot | grep -q "Up"; then
    echo "✅ Discord Bot is running"
else
    echo "❌ Discord Bot failed to start"
    docker compose logs discord-bot
    exit 1
fi

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Service URLs:"
echo "  - AI Core Service: http://localhost:8001"
echo "  - Task Service: http://localhost:8002"
echo ""
echo "📝 Useful commands:"
echo "  - View logs: docker compose logs -f"
echo "  - Stop services: docker compose down"
echo "  - Restart: docker compose restart"
echo "  - View status: docker compose ps"
