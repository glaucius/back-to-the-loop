#!/bin/bash
echo "🎨 Building BTL Frontend..."
docker build frontend/ -t tcc-frontend:latest
echo "🔄 Restarting frontend service..."
docker compose restart frontend
echo "✅ Frontend build completed!"

