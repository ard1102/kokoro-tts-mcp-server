#!/usr/bin/env python3
"""
Kokoro TTS MCP Server

A Model Context Protocol (MCP) server that provides text-to-speech capabilities
using the Kokoro-FastAPI model deployed at localhost:8880.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
import requests
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
from pydantic import AnyUrl
import mcp.types as types
from enhanced_audio_handler import AudioHandler
from wav_header_fixer import validate_and_fix_wav_header, validate_wav_integrity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kokoro-tts-mcp")

# Server configuration - support both local and containerized deployment
KOKORO_BASE_URL = os.getenv("KOKORO_API_URL", os.getenv("KOKORO_BASE_URL", "http://localhost:8880"))
server = Server("kokoro-tts")

# Create output directory for containerized environment
OUTPUT_DIR = "/app/output" if os.path.exists("/app") else "./output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Initialize audio handler
audio_handler = AudioHandler(OUTPUT_DIR)

class KokoroTTSClient:
    """Client for interacting with Kokoro-FastAPI TTS service."""
    
    def __init__(self, base_url: str = KOKORO_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def get_available_voices(self) -> Dict[str, Any]:
        """Get list of available voices from the TTS service."""
        try:
            response = self.session.get(f"{self.base_url}/v1/audio/voices")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to get voices: {e}")
            raise
    
    def generate_speech(self, text: str, voice: str = "af_bella", 
                       response_format: str = "wav", speed: float = 1.0) -> bytes:
        """Generate speech from text using the TTS service."""
        try:
            payload = {
                "model": "kokoro",
                "input": text,
                "voice": voice,
                "response_format": response_format,
                "speed": speed
            }
            
            logger.info(f"Sending payload to Kokoro-FastAPI: {payload}")
            
            response = self.session.post(
                f"{self.base_url}/v1/audio/speech",
                json=payload
            )
            response.raise_for_status()
            
            # Get raw audio data
            audio_data = response.content
            
            # Fix WAV header corruption if format is WAV
            if response_format.lower() == "wav":
                logger.info("Validating and fixing WAV header...")
                
                # Validate the audio data
                validation = validate_wav_integrity(audio_data)
                if not validation['valid']:
                    logger.warning(f"WAV validation issues: {validation['errors']} {validation['warnings']}")
                
                # Fix any header corruption
                audio_data = validate_and_fix_wav_header(audio_data)
                
                # Re-validate after fix
                post_fix_validation = validate_wav_integrity(audio_data)
                if post_fix_validation['valid']:
                    logger.info("✅ WAV header validation passed after fix")
                else:
                    logger.warning(f"⚠️ WAV still has issues after fix: {post_fix_validation['errors']}")
            
            return audio_data
            
        except requests.RequestException as e:
            logger.error(f"Failed to generate speech: {e}")
            raise
    
    def check_service_health(self) -> Dict[str, Any]:
        """Check if the TTS service is running and healthy."""
        try:
            response = self.session.get(f"{self.base_url}/docs")
            if response.status_code == 200:
                return {"status": "healthy", "service": "Kokoro-FastAPI"}
            else:
                return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
        except requests.RequestException as e:
            return {"status": "unreachable", "error": str(e)}

# Initialize TTS client
tts_client = KokoroTTSClient()

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools."""
    return [
        Tool(
            name="generate_speech",
            description="Generate speech audio from text using Kokoro TTS model",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to convert to speech"
                    },
                    "voice": {
                        "type": "string",
                        "description": "Voice to use (e.g., 'af_bella', 'af_sky', or combinations like 'af_bella+af_sky')",
                        "default": "af_bella"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["mp3", "wav", "opus", "flac"],
                        "description": "Audio format for the output",
                        "default": "wav"
                    },
                    "speed": {
                        "type": "number",
                        "description": "Speech speed (0.5 to 2.0)",
                        "minimum": 0.5,
                        "maximum": 2.0,
                        "default": 1.0
                    },
                    "output_file": {
                        "type": "string",
                        "description": "Optional output file path to save the audio"
                    },
                    "auto_play": {
                        "type": "boolean",
                        "description": "Automatically play the generated audio (optional, defaults to true)",
                        "default": True
                    }
                },
                "required": ["text"]
            }
        ),
        Tool(
            name="list_voices",
            description="Get list of available voices from Kokoro TTS",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        Tool(
            name="check_tts_status",
            description="Check if the Kokoro TTS service is running and accessible",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        Tool(
            name="play_audio",
            description="Play an audio file using system default player",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Name of the audio file to play (from output directory)"
                    }
                },
                "required": ["filename"]
            }
        ),
        Tool(
            name="list_audio_files",
            description="List all audio files in the output directory",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        Tool(
            name="open_output_folder",
            description="Open the output folder in file explorer",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool calls."""
    
    if name == "generate_speech":
        text = arguments.get("text")
        voice = arguments.get("voice", "af_bella")
        format_type = arguments.get("format", "wav")  # Ensure WAV is the default
        speed = arguments.get("speed", 1.0)
        output_file = arguments.get("output_file")
        auto_play = arguments.get("auto_play", True)
        
        # Force WAV format if not explicitly specified
        if "format" not in arguments:
            format_type = "wav"
        
        logger.info(f"Received arguments: {arguments}")
        logger.info(f"Format type extracted: {format_type}")
        logger.info(f"Final format being sent to API: {format_type}")
        
        if not text:
            return [types.TextContent(type="text", text="Error: Text is required for speech generation")]
        
        try:
            # Generate speech
            audio_data = tts_client.generate_speech(
                text=text,
                voice=voice,
                response_format=format_type,
                speed=speed
            )
            
            # ALWAYS save files with timestamped names for consistency
            saved_file_path = None
            try:
                # Generate timestamped filename if not provided
                if output_file:
                    # Use provided filename but ensure it's in output directory
                    if not os.path.isabs(output_file):
                        saved_file_path = os.path.join(OUTPUT_DIR, output_file)
                    else:
                        saved_file_path = output_file
                else:
                    # Generate automatic timestamped filename
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    # Clean text for filename (first 30 chars, safe characters only)
                    safe_text = "".join(c for c in text[:30] if c.isalnum() or c in (' ', '-', '_')).strip()
                    safe_text = safe_text.replace(' ', '_')
                    if not safe_text:
                        safe_text = "speech"
                    
                    filename = f"{timestamp}_{safe_text}_{voice}.{format_type}"
                    saved_file_path = os.path.join(OUTPUT_DIR, filename)
                
                # Ensure output directory exists
                os.makedirs(OUTPUT_DIR, exist_ok=True)
                if saved_file_path != OUTPUT_DIR:  # Don't try to create parent if it's the same as output dir
                    os.makedirs(os.path.dirname(saved_file_path), exist_ok=True)
                
                # Save the audio file with proper error handling
                with open(saved_file_path, "wb") as f:
                    f.write(audio_data)
                
                # Verify file was saved successfully
                if not os.path.exists(saved_file_path) or os.path.getsize(saved_file_path) == 0:
                    raise Exception(f"File was not saved properly: {saved_file_path}")
                
                logger.info(f"✅ Audio file saved successfully: {saved_file_path}")
                
            except Exception as save_error:
                logger.error(f"❌ Failed to save audio file: {save_error}")
                # Continue with playback even if save failed
                saved_file_path = None
            
            # Handle auto-play
            auto_play_message = ""
            playback_file = saved_file_path
            
            if auto_play:
                try:
                    # If we don't have a saved file, create a temporary one for playback
                    if not playback_file:
                        import tempfile
                        with tempfile.NamedTemporaryFile(suffix=f".{format_type}", delete=False) as temp_file:
                            temp_file.write(audio_data)
                            playback_file = temp_file.name
                        
                        # Schedule cleanup for temp file
                        import threading
                        def delayed_cleanup():
                            import time
                            time.sleep(5)  # Wait 5 seconds before cleanup
                            try:
                                os.unlink(playback_file)
                                logger.info(f"🗑️ Cleaned up temporary file: {playback_file}")
                            except Exception as cleanup_error:
                                logger.warning(f"Could not clean up temp file: {cleanup_error}")
                        threading.Thread(target=delayed_cleanup, daemon=True).start()
                    
                    # Attempt playback
                    play_result = audio_handler.play_audio_file(playback_file)
                    if play_result.get("success"):
                        auto_play_message = f"\n🔊 Audio is now playing with {play_result.get('method', 'unknown method')}."
                        logger.info(f"✅ Audio playback started: {play_result.get('method')}")
                    else:
                        auto_play_message = f"\n❌ Auto-play failed: {play_result.get('error', 'Unknown error')}"
                        logger.error(f"❌ Audio playback failed: {play_result.get('error')}")
                        
                except Exception as play_error:
                    auto_play_message = f"\n❌ Auto-play failed: {str(play_error)}"
                    logger.error(f"❌ Audio playback exception: {play_error}")
            
            # Prepare response message
            if saved_file_path:
                response_text = (
                    f"✅ Speech generated and saved successfully!\n"
                    f"📁 File: {os.path.basename(saved_file_path)}\n"
                    f"📍 Location: {saved_file_path}\n"
                    f"💬 Text: {text[:100]}{'...' if len(text) > 100 else ''}\n"
                    f"🎭 Voice: {voice}\n"
                    f"🎵 Format: {format_type}\n"
                    f"⚡ Speed: {speed}\n"
                    f"📊 File size: {len(audio_data):,} bytes{auto_play_message}"
                )
            else:
                response_text = (
                    f"⚠️ Speech generated but file save failed!\n"
                    f"💬 Text: {text[:100]}{'...' if len(text) > 100 else ''}\n"
                    f"🎭 Voice: {voice}\n"
                    f"🎵 Format: {format_type}\n"
                    f"⚡ Speed: {speed}\n"
                    f"📊 Audio size: {len(audio_data):,} bytes{auto_play_message}\n"
                    f"💡 Try checking output directory permissions or disk space."
                )
            
            # Always return text content with file info
            results = [types.TextContent(type="text", text=response_text)]
            
            # If no file was saved, also return embedded resource as fallback
            if not saved_file_path:
                import base64
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                results.append(types.EmbeddedResource(
                    type="resource",
                    resource=types.BlobResourceContents(
                        uri=f"data:audio/{format_type};base64,{audio_base64}",
                        mimeType=f"audio/{format_type}",
                        blob=audio_base64
                    )
                ))
            
            return results
                
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error generating speech: {str(e)}")]
    
    elif name == "list_voices":
        try:
            voices_data = tts_client.get_available_voices()
            return [types.TextContent(
                type="text",
                text=f"Available voices:\n{json.dumps(voices_data, indent=2)}"
            )]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error getting voices: {str(e)}")]
    
    elif name == "check_tts_status":
        try:
            status = tts_client.check_service_health()
            return [types.TextContent(
                type="text",
                text=f"TTS Service Status:\n{json.dumps(status, indent=2)}"
            )]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error checking status: {str(e)}")]
    
    elif name == "play_audio":
         filename = arguments.get("filename")
         if not filename:
             return [types.TextContent(type="text", text="Error: Filename is required")]
         
         try:
             # Construct full path if only filename is provided
             if not os.path.isabs(filename):
                 file_path = os.path.join(OUTPUT_DIR, filename)
             else:
                 file_path = filename
                 
             result = audio_handler.play_audio_file(file_path)
             if result.get("success"):
                 return [types.TextContent(
                     type="text",
                     text=f"Playing audio file: {filename}"
                 )]
             else:
                 return [types.TextContent(
                     type="text",
                     text=f"Error playing audio: {result.get('error', 'Unknown error')}"
                 )]
         except Exception as e:
             return [types.TextContent(type="text", text=f"Error playing audio: {str(e)}")]
    
    elif name == "list_audio_files":
         try:
             result = audio_handler.list_audio_files()
             if result.get("success") and result.get("files"):
                 files = result["files"]
                 file_list = "\n".join([f"- {f['filename']} ({f['size_kb']} KB)" for f in files])
                 return [types.TextContent(
                     type="text",
                     text=f"Audio files in output directory ({result['count']} files):\n{file_list}"
                 )]
             else:
                 return [types.TextContent(
                     type="text",
                     text="No audio files found in output directory"
                 )]
         except Exception as e:
             return [types.TextContent(type="text", text=f"Error listing audio files: {str(e)}")]
    
    elif name == "open_output_folder":
        try:
            result = audio_handler.open_output_folder()
            if result.get("success"):
                return [types.TextContent(
                    type="text",
                    text=f"Opened output folder: {OUTPUT_DIR}"
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text=f"Error opening folder: {result.get('error', 'Unknown error')}"
                )]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error opening folder: {str(e)}")]
    
    else:
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

async def main():
    """Main function to run the MCP server."""
    # Import here to avoid issues with event loop
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="kokoro-tts",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())