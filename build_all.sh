#!/bin/bash
echo "🏗️ Building all BTL services..."

echo "🖥️ Building Backoffice..."
docker build backoffice/ -t tcc-backoffice:latest --no-cache

echo "🎨 Building Frontend..."
docker build frontend/ -t tcc-frontend:latest --no-cache

echo "🔄 Restarting all services..."
docker compose restart backoffice frontend

echo "✅ All services built and restarted!"

