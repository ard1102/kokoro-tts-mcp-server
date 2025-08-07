# Kokoro TTS MCP Server - Windows PowerShell Installation Script
# Compatible with Windows PowerShell 5.1+ and PowerShell Core 7+

param(
    [string]$DockerHubUsername = "your-username",
    [string]$Tag = "latest",
    [switch]$SkipHealthCheck,
    [switch]$Verbose
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Configuration
$ImageName = "kokoro-tts-mcp"
$ComposeFile = "docker-compose.public.yml"
$GitHubRawUrl = "https://raw.githubusercontent.com/$DockerHubUsername/$ImageName/main"

# Colors for output (if supported)
$SupportsColor = $Host.UI.RawUI.ForegroundColor -ne $null
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    
    if ($SupportsColor) {
        $OriginalColor = $Host.UI.RawUI.ForegroundColor
        switch ($Color) {
            "Red" { $Host.UI.RawUI.ForegroundColor = "Red" }
            "Green" { $Host.UI.RawUI.ForegroundColor = "Green" }
            "Yellow" { $Host.UI.RawUI.ForegroundColor = "Yellow" }
            "Blue" { $Host.UI.RawUI.ForegroundColor = "Blue" }
            "Cyan" { $Host.UI.RawUI.ForegroundColor = "Cyan" }
            "Magenta" { $Host.UI.RawUI.ForegroundColor = "Magenta" }
        }
        Write-Host $Message
        $Host.UI.RawUI.ForegroundColor = $OriginalColor
    } else {
        Write-Host $Message
    }
}

Write-ColorOutput "🚀 Kokoro TTS MCP Server Installation" "Blue"
Write-ColorOutput "======================================" "Blue"
Write-Host ""

# Function to check if command exists
function Test-CommandExists {
    param([string]$Command)
    
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Function to test URL accessibility
function Test-UrlAccessible {
    param([string]$Url)
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method Head -TimeoutSec 10 -ErrorAction Stop
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

# Check prerequisites
Write-ColorOutput "📋 Checking prerequisites..." "Yellow"

# Check PowerShell version
$PSVersion = $PSVersionTable.PSVersion
if ($PSVersion.Major -lt 5) {
    Write-ColorOutput "❌ PowerShell 5.0+ is required. Current version: $PSVersion" "Red"
    Write-ColorOutput "Please upgrade PowerShell: https://docs.microsoft.com/en-us/powershell/scripting/install/installing-powershell" "Yellow"
    exit 1
}

Write-ColorOutput "✅ PowerShell version: $PSVersion" "Green"

# Check Docker
if (-not (Test-CommandExists "docker")) {
    Write-ColorOutput "❌ Docker not found!" "Red"
    Write-ColorOutput "Please install Docker Desktop for Windows:" "Yellow"
    Write-ColorOutput "  - Download: https://www.docker.com/products/docker-desktop" "Yellow"
    Write-ColorOutput "  - Or use Chocolatey: choco install docker-desktop" "Yellow"
    Write-ColorOutput "  - Or use winget: winget install Docker.DockerDesktop" "Yellow"
    exit 1
}

# Check Docker Compose
$ComposeCmd = $null
if (Test-CommandExists "docker") {
    try {
        docker compose version | Out-Null
        $ComposeCmd = "docker compose"
    } catch {
        if (Test-CommandExists "docker-compose") {
            $ComposeCmd = "docker-compose"
        } else {
            Write-ColorOutput "❌ Docker Compose not found!" "Red"
            Write-ColorOutput "Docker Compose is required. It should be included with Docker Desktop." "Yellow"
            Write-ColorOutput "Please reinstall Docker Desktop or install Docker Compose separately." "Yellow"
            exit 1
        }
    }
}

Write-ColorOutput "✅ Docker found: $(docker --version)" "Green"
Write-ColorOutput "✅ Docker Compose found: $($ComposeCmd --version)" "Green"

# Check if Docker daemon is running
try {
    docker info | Out-Null
    Write-ColorOutput "✅ Docker daemon is running" "Green"
} catch {
    Write-ColorOutput "❌ Docker daemon is not running!" "Red"
    Write-ColorOutput "Please start Docker Desktop and try again." "Yellow"
    Write-ColorOutput "You can start Docker Desktop from the Start menu or system tray." "Yellow"
    exit 1
}

Write-Host ""

# Download docker-compose file
Write-ColorOutput "📥 Downloading configuration..." "Yellow"

$ComposeUrl = "$GitHubRawUrl/$ComposeFile"
try {
    if ($Verbose) {
        Write-Host "Downloading from: $ComposeUrl"
    }
    
    Invoke-WebRequest -Uri $ComposeUrl -OutFile $ComposeFile -ErrorAction Stop
    
    if (-not (Test-Path $ComposeFile)) {
        throw "File not created"
    }
    
    Write-ColorOutput "✅ Configuration downloaded" "Green"
} catch {
    Write-ColorOutput "❌ Failed to download $ComposeFile" "Red"
    Write-ColorOutput "Error: $($_.Exception.Message)" "Red"
    Write-ColorOutput "Please check your internet connection and try again." "Yellow"
    Write-ColorOutput "Manual download URL: $ComposeUrl" "Yellow"
    exit 1
}

# Set environment variables
$env:DOCKERHUB_USERNAME = $DockerHubUsername
$env:TAG = $Tag

# Pull and start services
Write-ColorOutput "🐳 Starting Kokoro TTS MCP Server..." "Yellow"
Write-ColorOutput "This may take a few minutes on first run..." "Yellow"
Write-Host ""

# Pull images first to show progress
Write-ColorOutput "📦 Pulling Docker images..." "Yellow"
try {
    if ($ComposeCmd -eq "docker compose") {
        docker compose -f $ComposeFile pull
    } else {
        docker-compose -f $ComposeFile pull
    }
} catch {
    Write-ColorOutput "❌ Failed to pull Docker images" "Red"
    Write-ColorOutput "Error: $($_.Exception.Message)" "Red"
    exit 1
}

# Start services
Write-ColorOutput "🚀 Starting services..." "Yellow"
try {
    if ($ComposeCmd -eq "docker compose") {
        docker compose -f $ComposeFile up -d
    } else {
        docker-compose -f $ComposeFile up -d
    }
} catch {
    Write-ColorOutput "❌ Failed to start services" "Red"
    Write-ColorOutput "Error: $($_.Exception.Message)" "Red"
    
    Write-ColorOutput "Checking logs..." "Yellow"
    if ($ComposeCmd -eq "docker compose") {
        docker compose -f $ComposeFile logs
    } else {
        docker-compose -f $ComposeFile logs
    }
    exit 1
}

# Wait for services to be ready
Write-ColorOutput "⏳ Waiting for services to start..." "Yellow"
Start-Sleep -Seconds 10

# Check service status
Write-ColorOutput "🔍 Checking service status..." "Yellow"
try {
    if ($ComposeCmd -eq "docker compose") {
        $status = docker compose -f $ComposeFile ps
    } else {
        $status = docker-compose -f $ComposeFile ps
    }
    
    if ($status -match "Up") {
        Write-ColorOutput "✅ Services are running!" "Green"
    } else {
        Write-ColorOutput "❌ Some services failed to start" "Red"
        Write-ColorOutput "Service status:" "Yellow"
        Write-Host $status
        
        Write-ColorOutput "Checking logs..." "Yellow"
        if ($ComposeCmd -eq "docker compose") {
            docker compose -f $ComposeFile logs
        } else {
            docker-compose -f $ComposeFile logs
        }
        exit 1
    }
} catch {
    Write-ColorOutput "❌ Failed to check service status" "Red"
    Write-ColorOutput "Error: $($_.Exception.Message)" "Red"
    exit 1
}

# Health check
if (-not $SkipHealthCheck) {
    Write-ColorOutput "🏥 Performing health checks..." "Yellow"
    Start-Sleep -Seconds 5
    
    # Check Kokoro FastAPI
    if (Test-UrlAccessible "http://localhost:8880/health") {
        Write-ColorOutput "✅ Kokoro FastAPI is healthy" "Green"
    } else {
        Write-ColorOutput "⚠️  Kokoro FastAPI health check failed (may still be starting)" "Yellow"
    }
    
    # Check MCP Server
    if (Test-UrlAccessible "http://localhost:3000/health") {
        Write-ColorOutput "✅ MCP Server is healthy" "Green"
    } else {
        Write-ColorOutput "⚠️  MCP Server health check failed (may still be starting)" "Yellow"
    }
}

Write-Host ""
Write-ColorOutput "🎉 Installation completed successfully!" "Green"
Write-ColorOutput "====================================" "Green"
Write-Host ""
Write-ColorOutput "📋 Next Steps:" "Blue"
Write-Host "1. Add this MCP configuration to your IDE:"
Write-Host ""
Write-ColorOutput "   For stdio mode (recommended):" "Yellow"
Write-Host '   {'
Write-Host '     "mcpServers": {'
Write-Host '       "kokoro-tts": {'
Write-Host '         "command": "docker",'
Write-Host '         "args": ["exec", "kokoro-tts-mcp", "python", "start_mcp_server.py", "--mode", "stdio"],'
Write-Host '         "env": {'
Write-Host '           "KOKORO_BASE_URL": "http://localhost:8880"'
Write-Host '         }'
Write-Host '       }'
Write-Host '     }'
Write-Host '   }'
Write-Host ""
Write-ColorOutput "   For HTTP mode (alternative):" "Yellow"
Write-Host '   {'
Write-Host '     "mcpServers": {'
Write-Host '       "kokoro-tts": {'
Write-Host '         "command": "curl",'
Write-Host '         "args": ["-X", "POST", "http://localhost:3000/mcp"]'
Write-Host '       }'
Write-Host '     }'
Write-Host '   }'
Write-Host ""
Write-ColorOutput "🔧 Management Commands:" "Blue"
Write-Host "  - View status:    $ComposeCmd -f $ComposeFile ps"
Write-Host "  - View logs:      $ComposeCmd -f $ComposeFile logs -f"
Write-Host "  - Stop services:  $ComposeCmd -f $ComposeFile down"
Write-Host "  - Update:         $ComposeCmd -f $ComposeFile pull; $ComposeCmd -f $ComposeFile up -d"
Write-Host ""
Write-ColorOutput "🌐 Service URLs:" "Blue"
Write-Host "  - MCP Server:     http://localhost:3000"
Write-Host "  - Kokoro API:     http://localhost:8880"
Write-Host ""
Write-ColorOutput "Happy voice generation! 🎤✨" "Green"

# Optional: Open browser to health check URLs
if ($env:OPEN_BROWSER -eq "true") {
    Write-ColorOutput "🌐 Opening health check URLs in browser..." "Cyan"
    Start-Process "http://localhost:3000/health"
    Start-Process "http://localhost:8880/health"
}