#!/bin/bash

echo "🔧 Fixing Zabbix API connection..."

# Stop the current containers
echo "📦 Stopping current containers..."
docker compose down

# Start with the updated configuration
echo "🚀 Starting with correct Zabbix API URL..."
docker compose up -d

echo "✅ Zabbix API fix applied!"
echo ""
echo "🌐 Your application should now be accessible at:"
echo "   - Frontend: http://localhost"
echo "   - Backend API: http://localhost:8000"
echo "   - Zabbix Web: http://localhost:8081 (Admin/zabbix)"
echo ""
echo "📋 The backend should now be able to connect to Zabbix API"
echo "📋 Check backend logs: docker compose logs -f backend" 