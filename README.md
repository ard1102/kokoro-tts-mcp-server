# 🎤 Kokoro TTS MCP Server

> **Make Your AI Agents Speak! 🗣️ Transform text into natural speech instantly**

**Give your AI assistants a voice!** Let them announce completed tasks, provide audio feedback, and communicate naturally using the **FREE** Hugging Face Kokoro TTS model wrapped in a powerful MCP server. Perfect for developers, researchers, and AI enthusiasts who want their agents to speak!

[![Docker Hub](https://img.shields.io/docker/pulls/rockstar837/kokoro-tts-mcp-server?style=flat-square&logo=docker)](https://hub.docker.com/r/rockstar837/kokoro-tts-mcp-server)
[![GitHub Actions](https://img.shields.io/github/actions/workflow/status/ard1102/kokoro-tts-mcp/docker-publish.yml?style=flat-square&logo=github)](https://github.com/ard1102/kokoro-tts-mcp/actions)
[![License](https://img.shields.io/github/license/ard1102/kokoro-tts-mcp?style=flat-square)](LICENSE)
[![Version](https://img.shields.io/github/v/release/ard1102/kokoro-tts-mcp?style=flat-square)](https://github.com/ard1102/kokoro-tts-mcp/releases)

## ✨ Why Choose Kokoro TTS MCP?

- **🆓 Completely FREE**: Uses open-source Hugging Face Kokoro model - no API costs!
- **🎯 AI Agent Integration**: Perfect for making your AI assistants announce task completions
- **⚡ 2-Step Setup**: Pull Docker image → Copy MCP config → Done!
- **🔌 Universal Compatibility**: Works with any MCP-compatible IDE (Claude, Cursor, etc.)
- **🎵 Natural Voices**: High-quality speech synthesis with multiple voice options
- **🐳 Docker Ready**: Pre-built image on Docker Hub - no complex setup required
- **🔧 Flexible Deployment**: Supports both stdio and HTTP modes for any workflow
- **🌍 Cross-Platform**: Works on Windows, macOS, and Linux

## 🚀 2-Step Setup (Under 1 Minute!)

### Step 1: Pull & Run Docker Image

```bash
docker pull rockstar837/kokoro-tts-mcp-server:latest
docker run -p 3000:3000 rockstar837/kokoro-tts-mcp-server:latest
```

### Step 2: Add MCP Configuration

Copy this configuration to your IDE's MCP settings file:

**For Docker Deployment (HTTP Mode):**
```json
{
  "mcpServers": {
    "kokoro-tts": {
      "command": "python",
      "args": ["-c", "import requests; import sys; import json; response = requests.post('http://localhost:3000/mcp', json={'method': sys.argv[1] if len(sys.argv) > 1 else 'list_tools', 'params': {}}); print(response.text)"],
      "env": {
        "KOKORO_BASE_URL": "http://localhost:3000"
      }
    }
  }
}
```

**For Local Development (STDIO Mode):**
```json
{
  "mcpServers": {
    "kokoro-tts": {
      "command": "python",
      "args": ["start_mcp_server.py", "--mode", "stdio"],
      "cwd": "${workspaceFolder}/prod",
      "env": {
        "KOKORO_BASE_URL": "http://localhost:8880",
        "PYTHONPATH": "${workspaceFolder}/prod"
      }
    }
  }
}
```

### 🎉 That's it! Your AI can now speak!

Test it by asking your AI assistant: *"Generate speech saying 'Hello, I can speak now!'"*

---

## 🛠️ For Developers: Building & Contributing

**Want to build from source or make changes?** Clone the repository and follow these instructions:

```bash
# Clone the repository
git clone https://github.com/ard1102/kokoro-tts-mcp.git
cd kokoro-tts-mcp

# Option 1: Quick local development
./start.bat          # Windows
./start.sh           # Mac/Linux

# Option 2: Build your own Docker image
docker build -f prod/Dockerfile -t my-kokoro-tts .
docker run -p 3000:3000 my-kokoro-tts

# Option 3: Development with hot reload
pip install -r requirements.txt
python start_mcp_server.py --mode http --port 3000
```

**Project Structure:**
- `/prod/` - Production-ready files and Docker configuration
- `/scripts/` - Installation and setup scripts
- `start_mcp_server.py` - Main server entry point
- `kokoro_tts_mcp.py` - Core MCP server implementation

---

## 📋 Deployment Options

### 🐳 Docker Deployment (Recommended)

For a complete containerized setup with both Kokoro TTS and MCP server:

```bash
# Quick start with Docker Compose
docker-compose up -d

# Verify deployment
curl http://localhost:8880/web  # Kokoro TTS web interface
curl http://localhost:3000/health  # MCP server health check
```

**Benefits of Docker deployment:**
- Isolated environment
- Easy scaling and management
- Consistent deployment across systems
- Built-in networking between services

See [Docker Deployment Guide](docker-deployment-guide.md) for detailed instructions.

### 🖥️ Local Installation

#### Prerequisites

1. **Kokoro-FastAPI Service**: You should have the Kokoro-FastAPI service running at `localhost:8880`. Based on the [Kokoro-FastAPI documentation](https://github.com/remsky/Kokoro-FastAPI), you can start it with:
   ```bash
   docker run -p 8880:8880 ghcr.io/remsky/kokoro-fastapi-cpu:latest
   # or for GPU:
   docker run --gpus all -p 8880:8880 ghcr.io/remsky/kokoro-fastapi-gpu:latest
   ```

2. **Python 3.8+**: Required for running the MCP server

## Local Installation

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Verify your Kokoro TTS service is running:
   - Open http://localhost:8880/web in your browser
   - Check the API docs at http://localhost:8880/docs

## Configuration

### For Docker Deployment

The Docker image comes pre-configured and ready to use. Simply run:

```bash
docker run -p 3000:3000 rockstar837/kokoro-tts-mcp-server:latest
```

### For Local Development

Configure your environment variables in `.env` file:

```env
KOKORO_BASE_URL=http://localhost:8880
MCP_MODE=stdio
AUDIO_OUTPUT_DIR=./output
LOG_LEVEL=INFO
```

## Available Tools

Once configured, your AI assistant will have access to these TTS tools:

- **`generate_speech`**: Convert text to speech with voice selection
- **`list_voices`**: Get available voice options
- **`play_audio`**: Play generated audio files
- **`check_tts_status`**: Verify TTS service health

## Example Usage

Ask your AI assistant:

- *"Generate speech saying 'Task completed successfully' using the bella voice"*
- *"What voices are available for text-to-speech?"*
- *"Create an audio announcement for project completion"*
- *"Play the last generated audio file"*

## Troubleshooting

### Common Issues

1. **Connection refused**: Ensure Docker container is running on port 3000
2. **No audio output**: Check your system's audio settings and permissions
3. **Voice not found**: Use `list_voices` to see available options
4. **MCP not detected**: Verify your IDE's MCP configuration path

### Debug Mode

Run with debug logging:

```bash
docker run -p 3000:3000 -e LOG_LEVEL=DEBUG rockstar837/kokoro-tts-mcp-server:latest
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Kokoro TTS](https://huggingface.co/kokoro) - The amazing open-source TTS model
- [Kokoro-FastAPI](https://github.com/remsky/Kokoro-FastAPI) - FastAPI wrapper for Kokoro
- [Model Context Protocol](https://modelcontextprotocol.io/) - The protocol that makes this integration possible

---

**🎤 Ready to give your AI a voice? Start with the 2-step setup above!**