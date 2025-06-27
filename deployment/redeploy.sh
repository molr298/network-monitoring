#!/bin/bash

echo "🔄 Redeploying Network Monitoring Application..."

# Stop and remove existing containers
echo "📦 Stopping existing containers..."
docker compose down

# Remove any existing volumes (optional - uncomment if you want to start fresh)
# echo "🗑️  Removing existing volumes..."
# docker volume rm network-monitoring_postgres_data network-monitoring_timescale_data 2>/dev/null || true

# Build and start the services
echo "🚀 Starting services with updated configuration..."
docker compose up -d --build

# Wait a moment for services to start
echo "⏳ Waiting for services to initialize..."
sleep 10

# Check service status
echo "📊 Checking service status..."
docker compose ps

echo "✅ Redeployment complete!"
echo ""
echo "🌐 Access your application:"
echo "   - Frontend: http://localhost"
echo "   - Backend API: http://localhost:8000"
echo "   - Zabbix Web: http://localhost:8081 (Admin/zabbix)"
echo "   - TimescaleDB: localhost:5433"
echo ""
echo "📋 To view logs:"
echo "   - Backend: docker compose logs -f backend"
echo "   - Frontend: docker compose logs -f frontend"
echo "   - TimescaleDB: docker compose logs -f timescaledb" 