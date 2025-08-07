@echo off
REM Kokoro TTS MCP Server - Docker Hub Deployment Script (Windows)
REM This script builds and pushes the Docker image to Docker Hub

setlocal enabledelayedexpansion

REM Configuration
set IMAGE_NAME=kokoro-tts-mcp
if "%DOCKER_USERNAME%"=="" set DOCKER_USERNAME=your-dockerhub-username
if "%VERSION%"=="" set VERSION=1.0.0

echo.
echo 🚀 Kokoro TTS MCP Server - Docker Deployment
echo ==========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker and try again.
    pause
    exit /b 1
)

echo 📦 Building Docker image...
docker build -t %DOCKER_USERNAME%/%IMAGE_NAME%:latest .
if errorlevel 1 (
    echo ❌ Docker build failed!
    pause
    exit /b 1
)

docker tag %DOCKER_USERNAME%/%IMAGE_NAME%:latest %DOCKER_USERNAME%/%IMAGE_NAME%:v%VERSION%

echo.
echo 🧪 Testing the complete deployment with Kokoro FastAPI...
REM Start Kokoro FastAPI first
echo Starting Kokoro FastAPI TTS engine...
for /f "tokens=*" %%i in ('docker run -d -p 8881:8880 ghcr.io/remsky/kokoro-fastapi-cpu:latest') do set KOKORO_CONTAINER=%%i

REM Wait for Kokoro to start
echo Waiting for Kokoro FastAPI to initialize...
timeout /t 15 /nobreak >nul

REM Test the MCP server with Kokoro dependency
echo Starting MCP server...
for /f "tokens=*" %%i in ('docker run -d -p 3001:3000 -e KOKORO_API_URL=http://host.docker.internal:8881 %DOCKER_USERNAME%/%IMAGE_NAME%:latest') do set CONTAINER_ID=%%i

REM Wait for MCP server to start
timeout /t 10 /nobreak >nul

REM Check if both containers are running
docker ps | findstr %CONTAINER_ID% >nul
if errorlevel 1 (
    echo ❌ MCP Server test failed!
    docker logs %CONTAINER_ID%
    docker stop %KOKORO_CONTAINER% %CONTAINER_ID% >nul 2>&1
    docker rm %KOKORO_CONTAINER% %CONTAINER_ID% >nul 2>&1
    pause
    exit /b 1
) else (
    echo ✅ Complete deployment test passed!
    docker stop %KOKORO_CONTAINER% %CONTAINER_ID% >nul
    docker rm %KOKORO_CONTAINER% %CONTAINER_ID% >nul
)

echo.
echo 📤 Pushing to Docker Hub...
echo ⚠️  Make sure you're logged in to Docker Hub: docker login
echo.
pause

docker push %DOCKER_USERNAME%/%IMAGE_NAME%:latest
if errorlevel 1 (
    echo ❌ Failed to push latest tag!
    pause
    exit /b 1
)

docker push %DOCKER_USERNAME%/%IMAGE_NAME%:v%VERSION%
if errorlevel 1 (
    echo ❌ Failed to push version tag!
    pause
    exit /b 1
)

echo.
echo 🎉 Deployment completed successfully!
echo.
echo Your image is now available at:
echo   docker pull %DOCKER_USERNAME%/%IMAGE_NAME%:latest
echo   docker pull %DOCKER_USERNAME%/%IMAGE_NAME%:v%VERSION%
echo.
echo 🚀 To deploy the complete system (RECOMMENDED):
echo   1. Download docker-compose.yml from your repository
echo   2. Update the image name in docker-compose.yml to: %DOCKER_USERNAME%/%IMAGE_NAME%:latest
echo   3. Run: docker compose up -d
echo.
echo 🔧 Manual deployment (Advanced):
echo   docker run -d -p 8880:8880 --name kokoro-fastapi ghcr.io/remsky/kokoro-fastapi-cpu:latest
echo   docker run -d -p 3000:3000 --link kokoro-fastapi -e KOKORO_API_URL=http://kokoro-fastapi:8880 --name kokoro-tts %DOCKER_USERNAME%/%IMAGE_NAME%:latest
echo.
echo ✨ Happy deploying!
echo.
pause