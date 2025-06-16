#!/bin/bash
# Jules Environment Setup Script
set -e

echo "🔧 Setting up Claude MCP Server environment for Jules..."

# Python environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows (Jules runs Linux VMs)

# Install core dependencies
pip install --upgrade pip
pip install fastmcp mcp

# HTTP/SSE transport dependencies  
pip install fastapi uvicorn sse-starlette httpx requests

# Data processing
pip install pydantic python-dotenv

# CLI and formatting
pip install rich typer

# Additional functionality
pip install psutil exceptiongroup authlib

# Verify installation
python -c "import fastmcp; print('✅ FastMCP installed successfully')"
python -c "import fastapi; print('✅ FastAPI installed successfully')"

# Create data directories
mkdir -p data/memory data/sessions data/security data/logs

# Set permissions (if needed)
chmod +x mcp_server.py

echo "✅ Environment setup complete - Jules ready to work!"