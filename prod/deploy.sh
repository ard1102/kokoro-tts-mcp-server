#!/bin/bash
# Kokoro TTS MCP Server - Docker Hub Deployment Script
# This script builds and pushes the Docker image to Docker Hub

set -e  # Exit on any error

# Configuration
IMAGE_NAME="kokoro-tts-mcp"
DOCKER_USERNAME="${DOCKER_USERNAME:-your-dockerhub-username}"
VERSION="${VERSION:-1.0.0}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Kokoro TTS MCP Server - Docker Deployment${NC}"
echo "=========================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Check if logged into Docker Hub
if ! docker info | grep -q "Username"; then
    echo -e "${YELLOW}⚠️  You may need to login to Docker Hub first:${NC}"
    echo "   docker login"
    echo ""
fi

echo -e "${GREEN}📦 Building Docker image...${NC}"
docker build -t ${DOCKER_USERNAME}/${IMAGE_NAME}:latest .
docker tag ${DOCKER_USERNAME}/${IMAGE_NAME}:latest ${DOCKER_USERNAME}/${IMAGE_NAME}:v${VERSION}

echo -e "${GREEN}🧪 Testing the complete deployment with Kokoro FastAPI...${NC}"
# Start Kokoro FastAPI first
echo "Starting Kokoro FastAPI TTS engine..."
KOKORO_CONTAINER=$(docker run -d -p 8881:8880 ghcr.io/remsky/kokoro-fastapi-cpu:latest)

# Wait for Kokoro to start
echo "Waiting for Kokoro FastAPI to initialize..."
sleep 15

# Test the MCP server with Kokoro dependency
echo "Starting MCP server..."
CONTAINER_ID=$(docker run -d -p 3001:3000 -e KOKORO_API_URL=http://host.docker.internal:8881 ${DOCKER_USERNAME}/${IMAGE_NAME}:latest)
sleep 10

# Check if both containers are running
if docker ps | grep -q ${CONTAINER_ID}; then
    echo -e "${GREEN}✅ Complete deployment test passed!${NC}"
    docker stop ${KOKORO_CONTAINER} ${CONTAINER_ID} > /dev/null
    docker rm ${KOKORO_CONTAINER} ${CONTAINER_ID} > /dev/null
else
    echo -e "${RED}❌ MCP Server test failed!${NC}"
    docker logs ${CONTAINER_ID}
    docker stop ${KOKORO_CONTAINER} ${CONTAINER_ID} > /dev/null 2>&1
    docker rm ${KOKORO_CONTAINER} ${CONTAINER_ID} > /dev/null 2>&1
    exit 1
fi

echo -e "${GREEN}📤 Pushing to Docker Hub...${NC}"
docker push ${DOCKER_USERNAME}/${IMAGE_NAME}:latest
docker push ${DOCKER_USERNAME}/${IMAGE_NAME}:v${VERSION}

echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo ""
echo "Your image is now available at:"
echo "  docker pull ${DOCKER_USERNAME}/${IMAGE_NAME}:latest"
echo "  docker pull ${DOCKER_USERNAME}/${IMAGE_NAME}:v${VERSION}"
echo ""
echo -e "${GREEN}🚀 To deploy the complete system (RECOMMENDED):${NC}"
echo "  1. Download docker-compose.yml from your repository"
echo "  2. Update the image name in docker-compose.yml to: ${DOCKER_USERNAME}/${IMAGE_NAME}:latest"
echo "  3. Run: docker compose up -d"
echo ""
echo -e "${YELLOW}🔧 Manual deployment (Advanced):${NC}"
echo "  docker run -d -p 8880:8880 --name kokoro-fastapi ghcr.io/remsky/kokoro-fastapi-cpu:latest"
echo "  docker run -d -p 3000:3000 --link kokoro-fastapi -e KOKORO_API_URL=http://kokoro-fastapi:8880 --name kokoro-tts ${DOCKER_USERNAME}/${IMAGE_NAME}:latest"
echo ""
echo -e "${GREEN}✨ Happy deploying!${NC}"