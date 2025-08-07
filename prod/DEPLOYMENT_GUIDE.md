# 🚀 Kokoro TTS MCP Server - Simple Deployment Guide

**For Non-Technical Users**

This guide will help you deploy the Kokoro TTS MCP Server in just a few simple steps, even if you're not familiar with technical details.

## 📋 Prerequisites

Before you start, make sure you have:

1. **Docker Desktop** installed on your computer
   - Download from: https://www.docker.com/products/docker-desktop/
   - Install and make sure it's running (you'll see a whale icon in your system tray)

2. **Git** (optional, for downloading the code)
   - Download from: https://git-scm.com/downloads

## 🎯 Quick Start (Recommended)

### Step 1: Download the Code

**Option A: Using Git (if you have it)**
```bash
git clone https://github.com/ard1102/kokoro-tts-mcp-server.git
cd kokoro-tts-mcp-server/prod
```

**Option B: Download ZIP**
1. Go to the GitHub repository
2. Click the green "Code" button
3. Select "Download ZIP"
4. Extract the ZIP file
5. Open the `prod` folder

### Step 2: Start the Services

1. **Open Terminal/Command Prompt**
   - Windows: Press `Win + R`, type `cmd`, press Enter
   - Mac: Press `Cmd + Space`, type "Terminal", press Enter
   - Linux: Press `Ctrl + Alt + T`

2. **Navigate to the prod folder**
   ```bash
   cd path/to/your/downloaded/folder/prod
   ```

3. **Start the services**
   ```bash
   docker compose up -d
   ```

4. **Wait for completion**
   - The first time will take 5-10 minutes (downloading required components)
   - You'll see progress messages
   - When complete, you'll see "✅ Container kokoro-fastapi started" and "✅ Container kokoro-tts-mcp started"

### Step 3: Verify Everything Works

1. **Check if services are running**
   ```bash
   docker ps
   ```
   You should see two containers: `kokoro-fastapi` and `kokoro-tts-mcp`

2. **Test the services**
   - Open your web browser
   - Go to: http://localhost:3000/health
   - You should see: `{"status":"healthy","service":"kokoro-tts-mcp"}`

## 🎉 Success!

Your Kokoro TTS MCP Server is now running! Here's what you have:

- **MCP Server**: Running on http://localhost:3000
- **TTS Engine**: Running on http://localhost:8880
- **Available Tools**: Speech generation, voice listing, audio playback

## 🛠️ Managing Your Deployment

### To Stop the Services
```bash
docker compose down
```

### To Restart the Services
```bash
docker compose up -d
```

### To Update to Latest Version
```bash
docker compose pull
docker compose up -d
```

### To View Logs (if something goes wrong)
```bash
docker compose logs
```

## 🆘 Troubleshooting

### Problem: "Docker is not running"
**Solution**: Start Docker Desktop and wait for it to fully load

### Problem: "Port already in use"
**Solution**: Stop other services using ports 3000 or 8880, or change the ports in `docker-compose.yml`

### Problem: "Download is very slow"
**Solution**: This is normal for the first run. The Kokoro TTS model is large (~2GB). Subsequent starts will be much faster.

### Problem: "Container keeps restarting"
**Solution**: Check logs with `docker compose logs` and ensure you have enough disk space (at least 5GB free)

## 📞 Getting Help

If you encounter issues:

1. Check the logs: `docker compose logs`
2. Restart everything: `docker compose down && docker compose up -d`
3. Check our GitHub Issues page
4. Contact support with your log output

## 🔧 Advanced Options

### Custom Configuration

You can modify `docker-compose.yml` to:
- Change ports (if 3000 or 8880 are already used)
- Enable audio file persistence
- Add custom environment variables

### Using Your Own Docker Image

If you've built your own image:
1. Edit `docker-compose.yml`
2. Replace `build: .` with `image: your-dockerhub-username/kokoro-tts-mcp:latest`
3. Run `docker compose up -d`

---

**That's it! You now have a fully functional Kokoro TTS MCP Server running on your machine.** 🎊