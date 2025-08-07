#!/usr/bin/env python3
"""
Startup script for Kokoro TTS MCP Server
Supports both stdio and HTTP modes for different deployment scenarios
"""

import asyncio
import argparse
import logging
import sys
from kokoro_tts_mcp import server, InitializationOptions, NotificationOptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kokoro-tts-mcp-startup")

async def run_stdio_server():
    """Run MCP server using stdio (for direct integration with AI clients)."""
    from mcp.server.stdio import stdio_server
    
    logger.info("Starting MCP server in stdio mode...")
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

async def run_http_server(host: str = "0.0.0.0", port: int = 3000):
    """Run MCP server in HTTP mode using FastAPI wrapper"""
    try:
        import uvicorn
        from fastapi import FastAPI, HTTPException
        from fastapi.responses import JSONResponse
        import json
        
        logger.info(f"Starting MCP server in HTTP mode on {host}:{port}...")
        
        app = FastAPI(title="Kokoro TTS MCP Server", version="1.0.0")
        
        @app.get("/health")
        async def health_check():
            return {"status": "healthy", "service": "kokoro-tts-mcp"}
        
        @app.get("/tools")
        async def list_tools():
            """List available MCP tools"""
            try:
                from kokoro_tts_mcp import handle_list_tools
                tools = await handle_list_tools()
                return {"tools": [tool.model_dump() for tool in tools]}
            except Exception as e:
                logger.error(f"Error listing tools: {e}")
                return {"tools": []}
        
        @app.post("/v1/tools/list")
        async def list_tools_v1():
            """List available MCP tools (v1 API)"""
            return await list_tools()
        
        @app.post("/v1/tools/call")
        async def call_tool_v1(request_data: dict):
            """Execute MCP tool (v1 API)"""
            try:
                tool_name = request_data.get("name")
                arguments = request_data.get("arguments", {})
                
                if not tool_name:
                    raise HTTPException(status_code=400, detail="Tool name is required")
                
                # Import the MCP tool handler
                from kokoro_tts_mcp import handle_call_tool
                
                # Call the MCP server's tool handler
                result = await handle_call_tool(tool_name, arguments)
                
                # Convert MCP result to JSON-serializable format
                if result:
                    result_text = ""
                    for item in result:
                        if hasattr(item, 'text'):
                            result_text += item.text
                        elif hasattr(item, 'type') and item.type == "text":
                            result_text += getattr(item, 'text', str(item))
                    return {"content": [{"type": "text", "text": result_text or str(result)}]}
                else:
                    return {"content": [{"type": "text", "text": "Tool executed successfully"}]}
                    
            except Exception as e:
                logger.error(f"Error executing tool: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/tools/{tool_name}")
        async def call_tool(tool_name: str, request_data: dict):
            """Execute MCP tool"""
            try:
                # Import the MCP tool handler
                from kokoro_tts_mcp import handle_call_tool
                
                # Call the MCP server's tool handler
                result = await handle_call_tool(tool_name, request_data)
                
                # Convert MCP result to JSON-serializable format
                if result:
                    result_text = ""
                    for item in result:
                        if hasattr(item, 'text'):
                            result_text += item.text
                        elif hasattr(item, 'type') and item.type == "text":
                            result_text += getattr(item, 'text', str(item))
                    return {"result": result_text or str(result)}
                else:
                    return {"result": "Tool executed successfully"}
                    
            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        config = uvicorn.Config(
            app=app,
            host=host,
            port=port,
            log_level="info"
        )
        
        server_instance = uvicorn.Server(config)
        await server_instance.serve()
        
    except ImportError as e:
        logger.error(f"FastAPI/uvicorn not available: {e}")
        logger.info("Falling back to stdio mode...")
        await run_stdio_server()

def main():
    parser = argparse.ArgumentParser(description="Kokoro TTS MCP Server")
    parser.add_argument(
        "--mode",
        choices=["stdio", "http"],
        default="stdio",
        help="Server mode: stdio for direct integration, http for containerized deployment"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (HTTP mode only)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="Port to bind to (HTTP mode only)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "stdio":
        asyncio.run(run_stdio_server())
    else:
        asyncio.run(run_http_server(args.host, args.port))

if __name__ == "__main__":
    main()