#!/bin/bash

echo "🔧 Fixing API port configuration..."

# Stop the current containers
echo "📦 Stopping current containers..."
docker compose down

# Start with the updated configuration
echo "🚀 Starting with backend port 8000 exposed..."
docker compose up -d

echo "✅ Port fix applied!"
echo ""
echo "🌐 Your application should now be accessible at:"
echo "   - Frontend: http://localhost"
echo "   - Backend API: http://localhost:8000"
echo ""
echo "📋 Check if the frontend can now connect to the backend API" 