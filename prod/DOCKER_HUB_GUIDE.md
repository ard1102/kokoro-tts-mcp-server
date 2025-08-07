# Docker Hub Deployment Guide

🐳 **Complete guide for publishing Kokoro TTS MCP Server to Docker Hub**

## 📋 Prerequisites

1. **Docker Hub Account**: Create account at [hub.docker.com](https://hub.docker.com)
2. **Docker Desktop**: Installed and running on your system
3. **Git** (optional): For version control

## 🚀 Quick Deployment Steps

### Step 1: Login to Docker Hub

```bash
docker login
# Enter your Docker Hub username and password
```

### Step 2: Build and Tag the Image

```bash
# Replace 'your-username' with your actual Docker Hub username
docker build -t your-username/kokoro-tts-mcp:latest .
docker tag your-username/kokoro-tts-mcp:latest your-username/kokoro-tts-mcp:v1.0.0
```

### Step 3: Push to Docker Hub

```bash
docker push your-username/kokoro-tts-mcp:latest
docker push your-username/kokoro-tts-mcp:v1.0.0
```

### Step 4: Verify Deployment

```bash
# Test pulling and running your published image
docker pull your-username/kokoro-tts-mcp:latest
docker run -d -p 3000:3000 --name kokoro-tts your-username/kokoro-tts-mcp:latest

# Test the health endpoint
curl http://localhost:3000/health
```

## 🛠️ Automated Deployment

### Using the Deployment Scripts

**For Linux/Mac:**
```bash
# Make the script executable
chmod +x deploy.sh

# Set your Docker Hub username
export DOCKER_USERNAME=your-username

# Run the deployment
./deploy.sh
```

**For Windows:**
```cmd
# Set your Docker Hub username
set DOCKER_USERNAME=your-username

# Run the deployment
deploy.bat
```

### Using Docker Compose

```bash
# Edit docker-compose.yml and uncomment the image line
# Replace 'your-dockerhub-username' with your actual username

# Then run:
docker-compose up -d
```

## 📦 Repository Setup on Docker Hub

### Creating the Repository

1. Go to [Docker Hub](https://hub.docker.com)
2. Click "Create Repository"
3. Repository name: `kokoro-tts-mcp`
4. Description: "Production-ready Kokoro TTS MCP Server for AI assistants"
5. Visibility: Public (recommended) or Private
6. Click "Create"

### Repository Configuration

**Recommended settings:**
- **Short Description**: "Text-to-Speech MCP Server for AI Assistants"
- **Full Description**: Copy from the README.md
- **Tags**: 
  - `latest` (always points to the newest stable version)
  - `v1.0.0` (specific version tags)
  - `stable` (alias for latest stable)

## 🔄 Continuous Deployment

### GitHub Actions (Optional)

Create `.github/workflows/docker-publish.yml`:

```yaml
name: Docker Publish

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: docker.io
  IMAGE_NAME: your-username/kokoro-tts-mcp

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
    - name: Checkout repository
      uses: actions/checkout@v3

    - name: Log in to Docker Hub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: ${{ env.IMAGE_NAME }}

    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: ./prod
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
```

## 📊 Usage Analytics

### Monitoring Your Image

- **Docker Hub Stats**: View pulls, stars, and usage on your repository page
- **Docker Scout**: Automatic vulnerability scanning
- **Usage Logs**: Monitor container logs for usage patterns

### Popular Tags Strategy

```bash
# Version-specific tags
docker tag your-username/kokoro-tts-mcp:latest your-username/kokoro-tts-mcp:v1.0.0
docker tag your-username/kokoro-tts-mcp:latest your-username/kokoro-tts-mcp:stable

# Platform-specific tags (if needed)
docker tag your-username/kokoro-tts-mcp:latest your-username/kokoro-tts-mcp:linux-amd64
```

## 🔧 Maintenance

### Regular Updates

1. **Security Updates**: Rebuild monthly for base image updates
2. **Feature Updates**: Tag with new version numbers
3. **Documentation**: Keep README.md updated with new features

### Version Management

```bash
# For major updates
docker tag your-username/kokoro-tts-mcp:latest your-username/kokoro-tts-mcp:v2.0.0

# For minor updates
docker tag your-username/kokoro-tts-mcp:latest your-username/kokoro-tts-mcp:v1.1.0

# For patches
docker tag your-username/kokoro-tts-mcp:latest your-username/kokoro-tts-mcp:v1.0.1
```

## 🎯 User Instructions

### For End Users

Once published, users can deploy your MCP server with:

```bash
# Simple deployment
docker run -d -p 3000:3000 --name kokoro-tts your-username/kokoro-tts-mcp:latest

# With persistent storage
docker run -d -p 3000:3000 -v ./audio:/app/output --name kokoro-tts your-username/kokoro-tts-mcp:latest

# Using docker-compose
wget https://raw.githubusercontent.com/ard1102/kokoro-tts-mcp-server/main/prod/docker-compose.yml
docker-compose up -d
```

### Integration Examples

Provide users with integration examples:

```bash
# Health check
curl http://localhost:3000/health

# Generate speech
curl -X POST http://localhost:3000/v1/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "generate_speech",
    "arguments": {
      "text": "Hello from Docker Hub!",
      "voice": "af_bella"
    }
  }'
```

## 🛡️ Security Best Practices

1. **Regular Updates**: Keep base images updated
2. **Vulnerability Scanning**: Use Docker Scout
3. **Secrets Management**: Never include API keys in images
4. **Non-root User**: Already configured in Dockerfile
5. **Minimal Dependencies**: Only include necessary packages

## 📞 Support

### Troubleshooting

- **Build Failures**: Check Docker daemon and disk space
- **Push Failures**: Verify Docker Hub login and repository permissions
- **Runtime Issues**: Check container logs with `docker logs container-name`

### Getting Help

1. Check the main README.md for common issues
2. Review Docker Hub repository issues
3. Check container logs for specific errors
4. Verify network connectivity and port availability

---

**🎉 Congratulations! Your Kokoro TTS MCP Server is now ready for global deployment!**