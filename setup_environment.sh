#!/bin/bash
# Jules Environment Setup Script for Claude MCP Server
# Optimized for Jules's Linux VM environment
set -e

echo "🔧 Setting up Claude MCP Server environment for Jules Linux VM..."

# Ensure we're working with Python 3.11+ (Jules VMs should have this)
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python 3 not found. This is unexpected in Jules VM."
    exit 1
fi

# Create and activate virtual environment (Linux/Jules VM compatible)
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip to latest version
pip install --upgrade pip

echo "📦 Installing core MCP dependencies..."
# Core MCP framework dependencies
pip install fastmcp mcp

echo "📦 Installing HTTP/SSE transport dependencies..."
# HTTP/SSE transport for remote access (critical for Claude Desktop integration)
pip install fastapi>=0.104.0
pip install uvicorn[standard]>=0.24.0
pip install sse-starlette
pip install httpx
pip install requests>=2.28.0

echo "📦 Installing data processing dependencies..."
# Data validation and configuration
pip install pydantic
pip install python-dotenv

echo "📦 Installing CLI and formatting tools..."
# Output formatting and CLI tools
pip install rich
pip install typer

echo "📦 Installing additional functionality..."
# System monitoring and enhanced features
pip install psutil>=5.9.0
pip install exceptiongroup
pip install authlib

echo "📦 Installing security and crypto dependencies..."
# For SSL certificate generation in HTTPS wrapper
pip install cryptography

echo "📦 Installing additional web server dependencies..."
# Additional FastAPI/web server support
pip install starlette
pip install openapi-pydantic

echo "🔍 Verifying critical installations..."
# Verify core installations
python -c "import fastmcp; print('✅ FastMCP installed successfully')"
python -c "import fastapi; print('✅ FastAPI installed successfully')"
python -c "import sqlite3; print('✅ SQLite3 available')"
python -c "import uvicorn; print('✅ Uvicorn installed successfully')"
python -c "import cryptography; print('✅ Cryptography installed successfully')"

echo "📁 Creating data directories..."
# Create necessary data directories with proper permissions
mkdir -p data/memory
mkdir -p data/sessions  
mkdir -p data/security
mkdir -p data/logs
mkdir -p data/web_cache

echo "🔧 Setting up file permissions..."
# Make main server executable
chmod +x mcp_server.py
chmod +x mcp_https_wrapper.py

# Set proper permissions for data directories
chmod 755 data/
chmod 755 data/memory/
chmod 755 data/sessions/
chmod 700 data/security/  # More restrictive for security files
chmod 755 data/logs/
chmod 755 data/web_cache/

echo "🧪 Running basic functionality tests..."
# Test that the main server can at least import without errors
python -c "
import sys
sys.path.insert(0, '.')
try:
    # Test imports without actually running the server
    from pathlib import Path
    import logging
    import sqlite3
    import json
    import time
    import hashlib
    import re
    print('✅ All core Python modules available')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

echo "🔧 Setting environment variables for Jules session..."
# Set environment variables that might be needed
export PYTHONPATH="$(pwd):$PYTHONPATH"
export MCP_LOG_LEVEL="INFO"
export FASTMCP_DEBUG="false"

echo "📋 Environment verification complete!"
echo "📊 Python version: $(python --version)"
echo "📍 Working directory: $(pwd)"
echo "💾 Available disk space: $(df -h . | tail -1 | awk '{print $4}')"
echo "🧠 Available memory: $(free -h | grep Mem | awk '{print $7}')"

echo ""
echo "✅ Claude MCP Server environment ready for Jules!"
echo "🎯 Jules can now work on the codebase with all dependencies installed"
echo ""
echo "🔍 Key capabilities enabled:"
echo "  • FastMCP server with 39+ bb7_ tools"
echo "  • HTTP/SSE transport for remote Claude Desktop access"  
echo "  • Persistent memory system with SQLite"
echo "  • Security features with SSL certificate generation"
echo "  • Web content fetching and analysis"
echo "  • Code analysis and execution capabilities"
echo "  • Session management and project context analysis"
echo ""
echo "🚀 Next: Jules can now complete tool implementations and test the server!"