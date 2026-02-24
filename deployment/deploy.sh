#!/bin/bash
# =============================================================
# KKL FMS - Deploy Script
# Owner: Nir Avutbul (nirab96Developer)
# =============================================================

set -e

# Configuration
APP_DIR="/opt/kkl-fms"
COMPOSE_FILE="docker-compose.yml"

echo "============================================="
echo "🚀 Deploying KKL FMS Backend"
echo "============================================="

# Navigate to app directory
cd $APP_DIR/app_backend

# Pull latest changes (if running manually)
if [ "$1" != "--no-pull" ]; then
    echo "📥 Pulling latest code..."
    git pull origin main
fi

# Build and deploy
echo "🐳 Building Docker images..."
docker-compose -f $COMPOSE_FILE build --no-cache

echo "🔄 Stopping old containers..."
docker-compose -f $COMPOSE_FILE down

echo "▶️ Starting new containers..."
docker-compose -f $COMPOSE_FILE up -d

# Wait for backend to be ready
echo "⏳ Waiting for backend to start..."
sleep 10

# Health check
echo "🏥 Running health check..."
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "000")

if [ "$HEALTH_STATUS" = "200" ]; then
    echo "✅ Health check passed!"
else
    echo "⚠️ Health check returned: $HEALTH_STATUS"
    echo "Checking container logs..."
    docker-compose -f $COMPOSE_FILE logs --tail=50 backend
fi

# Run migrations (if needed)
echo "📊 Running database migrations..."
docker-compose -f $COMPOSE_FILE exec -T backend alembic upgrade head || echo "No migrations needed"

echo ""
echo "============================================="
echo "✅ Deployment Complete!"
echo "============================================="
echo "🌐 Backend URL: http://YOUR_SERVER_IP:8000"
echo "📋 API Docs: http://YOUR_SERVER_IP:8000/docs"
echo "============================================="

# Show running containers
docker-compose -f $COMPOSE_FILE ps
