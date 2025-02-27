#!/bin/bash

# Exit immediately if any command fails
set -e

echo "🚀 Stopping and removing all containers, networks, and volumes defined in docker-compose.yml..."
docker compose down -v --remove-orphans

echo "🗑 Removing all stopped containers..."
docker container prune -f

echo "🖼 Removing all Docker images..."
docker rmi -f $(docker images -aq) || echo "No images to remove."

echo "📦 Removing all Docker volumes..."
docker volume prune -f

echo "🧹 Pruning all unused Docker resources (containers, networks, images, build cache)..."
docker system prune -a -f --volumes

echo "✅ Docker environment fully reset!"
