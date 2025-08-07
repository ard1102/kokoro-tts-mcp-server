#!/bin/bash
# Kokoro TTS MCP Server - Universal Installation Script
# Compatible with Linux, macOS, and Windows (Git Bash/WSL)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKERHUB_USERNAME="your-username"  # Replace with actual username
IMAGE_NAME="kokoro-tts-mcp"
COMPOSE_FILE="docker-compose.public.yml"
GITHUB_RAW_URL="https://raw.githubusercontent.com/${DOCKERHUB_USERNAME}/${IMAGE_NAME}/main"

echo -e "${BLUE}🚀 Kokoro TTS MCP Server Installation${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

# Check Docker
if ! command_exists docker; then
    echo -e "${RED}❌ Docker not found!${NC}"
    echo -e "${YELLOW}Please install Docker first:${NC}"
    
    OS=$(detect_os)
    case $OS in
        "linux")
            echo "  - Ubuntu/Debian: sudo apt-get install docker.io"
            echo "  - CentOS/RHEL: sudo yum install docker"
            echo "  - Or visit: https://docs.docker.com/engine/install/"
            ;;
        "macos")
            echo "  - Download Docker Desktop: https://www.docker.com/products/docker-desktop"
            echo "  - Or use Homebrew: brew install --cask docker"
            ;;
        "windows")
            echo "  - Download Docker Desktop: https://www.docker.com/products/docker-desktop"
            echo "  - Or use Chocolatey: choco install docker-desktop"
            ;;
        *)
            echo "  - Visit: https://docs.docker.com/get-docker/"
            ;;
    esac
    exit 1
fi

# Check Docker Compose
if ! command_exists "docker compose" && ! command_exists docker-compose; then
    echo -e "${RED}❌ Docker Compose not found!${NC}"
    echo -e "${YELLOW}Docker Compose is required. Please install it:${NC}"
    echo "  - Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

# Determine compose command
if command_exists "docker compose"; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

echo -e "${GREEN}✅ Docker found: $(docker --version)${NC}"
echo -e "${GREEN}✅ Docker Compose found: $(${COMPOSE_CMD} --version)${NC}"

# Check if Docker daemon is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker daemon is not running!${NC}"
    echo -e "${YELLOW}Please start Docker and try again.${NC}"
    
    OS=$(detect_os)
    case $OS in
        "linux")
            echo "  - sudo systemctl start docker"
            echo "  - sudo service docker start"
            ;;
        "macos"|"windows")
            echo "  - Start Docker Desktop application"
            ;;
    esac
    exit 1
fi

echo -e "${GREEN}✅ Docker daemon is running${NC}"
echo ""

# Download docker-compose file
echo -e "${YELLOW}📥 Downloading configuration...${NC}"

if command_exists curl; then
    curl -fsSL "${GITHUB_RAW_URL}/${COMPOSE_FILE}" -o "${COMPOSE_FILE}"
elif command_exists wget; then
    wget -q "${GITHUB_RAW_URL}/${COMPOSE_FILE}" -O "${COMPOSE_FILE}"
else
    echo -e "${RED}❌ Neither curl nor wget found!${NC}"
    echo -e "${YELLOW}Please install curl or wget, or manually download:${NC}"
    echo "  ${GITHUB_RAW_URL}/${COMPOSE_FILE}"
    exit 1
fi

if [[ ! -f "${COMPOSE_FILE}" ]]; then
    echo -e "${RED}❌ Failed to download ${COMPOSE_FILE}${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Configuration downloaded${NC}"

# Set Docker Hub username in environment
export DOCKERHUB_USERNAME="${DOCKERHUB_USERNAME}"

# Pull and start services
echo -e "${YELLOW}🐳 Starting Kokoro TTS MCP Server...${NC}"
echo "This may take a few minutes on first run..."
echo ""

# Pull images first to show progress
echo -e "${YELLOW}📦 Pulling Docker images...${NC}"
${COMPOSE_CMD} -f "${COMPOSE_FILE}" pull

# Start services
echo -e "${YELLOW}🚀 Starting services...${NC}"
${COMPOSE_CMD} -f "${COMPOSE_FILE}" up -d

# Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to start...${NC}"
sleep 10

# Check service status
echo -e "${YELLOW}🔍 Checking service status...${NC}"
if ${COMPOSE_CMD} -f "${COMPOSE_FILE}" ps | grep -q "Up"; then
    echo -e "${GREEN}✅ Services are running!${NC}"
else
    echo -e "${RED}❌ Some services failed to start${NC}"
    echo -e "${YELLOW}Checking logs...${NC}"
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" logs
    exit 1
fi

# Health check
echo -e "${YELLOW}🏥 Performing health checks...${NC}"
sleep 5

# Check Kokoro FastAPI
if command_exists curl; then
    if curl -f http://localhost:8880/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Kokoro FastAPI is healthy${NC}"
    else
        echo -e "${YELLOW}⚠️  Kokoro FastAPI health check failed (may still be starting)${NC}"
    fi
    
    # Check MCP Server
    if curl -f http://localhost:3000/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ MCP Server is healthy${NC}"
    else
        echo -e "${YELLOW}⚠️  MCP Server health check failed (may still be starting)${NC}"
    fi
fi

echo ""
echo -e "${GREEN}🎉 Installation completed successfully!${NC}"
echo -e "${GREEN}====================================${NC}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "1. Add this MCP configuration to your IDE:"
echo ""
echo -e "${YELLOW}   For stdio mode (recommended):${NC}"
echo '   {'
echo '     "mcpServers": {'
echo '       "kokoro-tts": {'
echo '         "command": "docker",'
echo '         "args": ["exec", "kokoro-tts-mcp", "python", "start_mcp_server.py", "--mode", "stdio"],'
echo '         "env": {'
echo '           "KOKORO_BASE_URL": "http://localhost:8880"'
echo '         }'
echo '       }'
echo '     }'
echo '   }'
echo ""
echo -e "${YELLOW}   For HTTP mode (alternative):${NC}"
echo '   {'
echo '     "mcpServers": {'
echo '       "kokoro-tts": {'
echo '         "command": "curl",'
echo '         "args": ["-X", "POST", "http://localhost:3000/mcp"]'
echo '       }'
echo '     }'
echo '   }'
echo ""
echo -e "${BLUE}🔧 Management Commands:${NC}"
echo "  - View status:    ${COMPOSE_CMD} -f ${COMPOSE_FILE} ps"
echo "  - View logs:      ${COMPOSE_CMD} -f ${COMPOSE_FILE} logs -f"
echo "  - Stop services:  ${COMPOSE_CMD} -f ${COMPOSE_FILE} down"
echo "  - Update:         ${COMPOSE_CMD} -f ${COMPOSE_FILE} pull && ${COMPOSE_CMD} -f ${COMPOSE_FILE} up -d"
echo ""
echo -e "${BLUE}🌐 Service URLs:${NC}"
echo "  - MCP Server:     http://localhost:3000"
echo "  - Kokoro API:     http://localhost:8880"
echo ""
echo -e "${GREEN}Happy voice generation! 🎤✨${NC}"