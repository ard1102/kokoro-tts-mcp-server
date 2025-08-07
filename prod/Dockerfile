# Kokoro TTS MCP Server - Production Docker Image
# Multi-stage build for optimized image size and security

# Build stage
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    pkg-config \
    libportaudio2 \
    portaudio19-dev \
    libasound2-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies to user directory
RUN pip install --user --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Set build arguments for labels
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=latest

# Add comprehensive metadata labels
LABEL org.opencontainers.image.title="Kokoro TTS MCP Server" \
      org.opencontainers.image.description="MCP Server for Kokoro Text-to-Speech with Docker support" \
      org.opencontainers.image.version="$VERSION" \
      org.opencontainers.image.created="$BUILD_DATE" \
      org.opencontainers.image.revision="$VCS_REF" \
      org.opencontainers.image.vendor="Open Source" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.url="https://github.com/ard1102/kokoro-tts-mcp-server" \
      org.opencontainers.image.source="https://github.com/ard1102/kokoro-tts-mcp-server" \
      org.opencontainers.image.documentation="https://github.com/ard1102/kokoro-tts-mcp-server/blob/main/README.md" \
      maintainer="ard1102 <131929269+ard1102@users.noreply.github.com>"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libportaudio2 \
    libasound2 \
    alsa-utils \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy pre-built dependencies from builder stage
COPY --from=builder /root/.local /home/mcp/.local

# Copy application files
COPY --chown=mcp:mcp . .

# Create non-root user for security
RUN groupadd -r mcp && useradd -r -g mcp -d /app -s /bin/bash mcp

# Create necessary directories
RUN mkdir -p /app/audio_output /app/logs && \
    chown -R mcp:mcp /app

# Set comprehensive environment variables
ENV PATH=/home/mcp/.local/bin:$PATH \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    KOKORO_BASE_URL=http://localhost:8880 \
    MCP_MODE=stdio \
    AUDIO_OUTPUT_DIR=/app/audio_output \
    LOG_LEVEL=INFO

# Switch to non-root user
USER mcp

# Expose port
EXPOSE 3000

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Create volume for audio output
VOLUME ["/app/audio_output"]

# Default command - run in HTTP mode for containerized deployment
CMD ["python", "start_mcp_server.py", "--mode", "http", "--host", "0.0.0.0", "--port", "3000"]

# Build instructions:
# docker build -t kokoro-tts-mcp:latest \
#   --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
#   --build-arg VCS_REF=$(git rev-parse --short HEAD) \
#   --build-arg VERSION=$(git describe --tags --always) \
#   -f prod/Dockerfile .

# Multi-platform build:
# docker buildx build --platform linux/amd64,linux/arm64 \
#   -t ard1102/kokoro-tts-mcp:latest \
#   --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
#   --build-arg VCS_REF=$(git rev-parse --short HEAD) \
#   --build-arg VERSION=$(git describe --tags --always) \
#   -f prod/Dockerfile . --push