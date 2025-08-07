# Kokoro TTS MCP Server

🎯 **Production-ready Kokoro Text-to-Speech MCP Server with Docker Hub deployment**

## 🚀 Quick Start

### One-Command Installation

**Linux/macOS:**
```bash
curl -fsSL https://raw.githubusercontent.com/ard1102/kokoro-tts-mcp-server/main/scripts/install.sh | bash
```

**Windows (PowerShell):**
```powershell
iwr -useb https://raw.githubusercontent.com/ard1102/kokoro-tts-mcp-server/main/scripts/install.ps1 | iex
```

### Direct Docker Hub Deployment

```bash
# Download and start the complete stack
wget https://raw.githubusercontent.com/ard1102/kokoro-tts-mcp-server/main/docker-compose.public.yml
DOCKER_HUB_USERNAME=ard1102 docker compose -f docker-compose.public.yml up -d
```

## ✨ Features

- 🐳 **Docker Hub Ready**: Pre-built multi-platform images
- 🔄 **One-Command Setup**: Install and configure in 30 seconds
- 🎛️ **MCP Integration**: Copy-paste configuration for IDEs
- 🌐 **Multi-Platform**: Linux, macOS, Windows support
- 🔧 **Production Ready**: Health checks, logging, auto-restart
- 📦 **Complete Stack**: Includes Kokoro FastAPI + MCP Server

## 🎯 MCP Configuration

After installation, add this to your MCP-compatible IDE:

### Stdio Mode (Recommended)
```json
{
  "mcpServers": {
    "kokoro-tts": {
      "command": "docker",
      "args": ["exec", "-i", "kokoro-tts-mcp", "python", "/app/kokoro_tts_mcp.py"]
    }
  }
}
```

### HTTP Mode
```json
{
  "mcpServers": {
    "kokoro-tts": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch", "http://localhost:3000"]
    }
  }
}
```

## 🛠️ Development

```bash
# Clone and setup
git clone https://github.com/ard1102/kokoro-tts-mcp-server.git
cd kokoro-tts-mcp-server
docker compose up -d
```

## 📚 Documentation

- [Quick Start Guide](docs/QUICK_START.md)
- [Docker Hub Deployment Plan](DOCKER_HUB_DEPLOYMENT_PLAN.md)
- [Implementation Checklist](IMPLEMENTATION_CHECKLIST.md)

## 🔧 Management Commands

```bash
# Check status
docker compose ps

# View logs
docker compose logs -f

# Stop services
docker compose down

# Update to latest
docker compose pull && docker compose up -d
```

## 🌟 Service URLs

- **Kokoro FastAPI**: http://localhost:8000
- **MCP Server**: http://localhost:3000
- **Health Check**: http://localhost:3000/health

---

**Ready to generate speech in 30 seconds!** 🎤✨