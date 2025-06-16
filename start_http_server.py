#!/usr/bin/env python3
"""
HTTP Server Launcher for Claude MCP Server
==========================================

This script starts the Claude MCP Server in HTTP/SSE mode for remote access.
Use this when Claude Desktop requires an integration URL instead of local stdio.
"""

import sys
import os
import subprocess
import time
from pathlib import Path

def main():
    """Start the MCP server in HTTP mode"""
    
    # Get current directory
    current_dir = Path(__file__).parent
    server_script = current_dir / "mcp_server.py"
    
    if not server_script.exists():
        print("Error: mcp_server.py not found!", file=sys.stderr)
        sys.exit(1)
    
    # Default configuration
    host = os.getenv('MCP_HOST', '0.0.0.0')
    port = int(os.getenv('MCP_PORT', '8000'))
    
    print("Claude MCP Server - HTTP/SSE Mode")
    print("=" * 40)
    print(f"Starting server on {host}:{port}")
    print()
    print("Integration Instructions:")
    print("1. Open Claude Desktop")
    print("2. Go to Settings > Integrations")
    print("3. Click 'Add more' or 'Custom Integration'")
    print(f"4. Enter URL: http://{host}:{port}/mcp/sse")
    print("5. Save and restart Claude Desktop")
    print()
    print("Available endpoints:")
    print(f"  • Server info: http://{host}:{port}/")
    print(f"  • Health check: http://{host}:{port}/health")
    print(f"  • Tools list: http://{host}:{port}/mcp/tools")
    print(f"  • SSE endpoint: http://{host}:{port}/mcp/sse")
    print()
    print("Press Ctrl+C to stop the server")
    print("-" * 40)
    
    try:
        # Start the server
        subprocess.run([
            sys.executable, 
            str(server_script), 
            "--http", 
            "--host", host, 
            "--port", str(port)
        ], check=True)
        
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: Python not found in PATH", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
