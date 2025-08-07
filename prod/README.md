# Production Deployment Guide

This directory contains all the production-ready files for deploying the Kokoro TTS MCP Server.

## Quick Start

### Option 1: Docker Hub (Recommended)
```bash
docker run -d -p 3000:3000 --name kokoro-tts-mcp rockstar837/kokoro-tts-mcp-server:latest
```

### Option 2: Local Build
```bash
docker build -t kokoro-tts-mcp-server .
docker run -d -p 3000:3000 --name kokoro-tts-mcp kokoro-tts-mcp-server
```

## Files Overview

- `Dockerfile` - Production Docker configuration
- `docker-compose.yml` - Docker Compose setup
- `requirements.txt` - Python dependencies
- `start_mcp_server.py` - Main server startup script
- `kokoro_tts_mcp.py` - Core MCP implementation
- `enhanced_audio_handler.py` - Audio processing utilities
- `wav_header_fixer.py` - WAV file header repair utility
- `trae_mcp_config.json` - Trae AI MCP configuration
- `mcp_config_simple.json` - Simple MCP configuration

## Deployment Guides

- `DEPLOYMENT_GUIDE.md` - Complete deployment instructions
- `DOCKER_HUB_GUIDE.md` - Docker Hub deployment guide
- `DOCKER_AUTO_START_GUIDE.md` - Auto-start configuration
- `IDE_MCP_SETUP_GUIDE.md` - IDE integration setup

## Scripts

### Windows
- `start.bat` - Start the server
- `deploy.bat` - Deploy to production
- `check-kokoro.bat` - Health check
- `restart-kokoro.bat` - Restart server
- `configure-trae-mcp.bat` - Configure Trae AI

### Linux/Mac
- `start.sh` - Start the server
- `deploy.sh` - Deploy to production
