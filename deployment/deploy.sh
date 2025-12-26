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

# Build and start services
echo "📦 Building Docker images..."
docker-compose build

echo "🔄 Starting services..."
docker-compose up -d

echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check health
echo "🏥 Checking service health..."
curl -f http://localhost:8001/health && echo "✅ AI Core Service is healthy"
curl -f http://localhost:8002/health && echo "✅ Task Service is healthy"

echo "✅ Deployment complete!"
echo ""
echo "📊 Service URLs:"
echo "  - AI Core Service: http://localhost:8001"
echo "  - Task Service: http://localhost:8002"
echo ""
echo "📝 View logs: docker-compose logs -f"
echo "🛑 Stop services: docker-compose down"
