#!/bin/bash
echo "🎨 Building BTL Backoffice..."
docker build backoffice/ -t tcc-backoffice:latest
echo "🔄 Restarting backoffice service..."
docker compose restart backoffice
echo "✅ backoffice build completed!"

