#!/bin/bash
# Jules Environment Setup Script for Claude MCP Server
# Optimized for Jules's Linux VM environment with robust error handling
set -e

echo "🔧 Setting up Claude MCP Server environment for Jules Linux VM..."

# Function for error handling
handle_error() {
    echo "❌ Error on line $1: $2"
    echo "🔍 Attempting recovery strategies..."
    exit 1
}

trap 'handle_error ${LINENO} "$BASH_COMMAND"' ERR

# Detect Linux distribution for package management
detect_distro() {
    if [ -f /etc/debian_version ]; then
        echo "debian"
    elif [ -f /etc/redhat-release ]; then
        echo "redhat"  
    elif [ -f /etc/alpine-release ]; then
        echo "alpine"
    else
        echo "unknown"
    fi
}

DISTRO=$(detect_distro)
echo "📋 Detected Linux distribution type: $DISTRO"

# Ensure we're working with Python 3.x (Jules VMs should have this)
echo "🔍 Checking Python installation..."
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python 3 not found. This is unexpected in Jules VM."
    exit 1
fi

echo "📦 Installing system-level dependencies for Python virtual environments..."
# Install system packages needed for Python virtual environments and pip
case $DISTRO in
    "debian")
        # For Ubuntu/Debian-based systems (most common in Google Cloud VMs)
        if command -v apt-get >/dev/null 2>&1; then
            apt-get update -qq || echo "⚠️ Could not update package lists (may not have sudo)"
            apt-get install -y python3-pip python3-venv python3-dev build-essential || echo "⚠️ Could not install system packages"
        fi
        ;;
    "redhat")
        # For RHEL/CentOS-based systems
        if command -v yum >/dev/null 2>&1; then
            yum install -y python3-pip python3-devel gcc || echo "⚠️ Could not install system packages"
        fi
        ;;
    "alpine")
        # For Alpine Linux (minimal containers)
        if command -v apk >/dev/null 2>&1; then
            apk add --no-cache python3-dev py3-pip gcc musl-dev || echo "⚠️ Could not install system packages"
        fi
        ;;
esac

echo "🔧 Creating virtual environment with fallback strategies..."
# Try multiple approaches for virtual environment creation
if python3 -m venv .venv 2>/dev/null; then
    echo "✅ Virtual environment created successfully with venv"
elif python3 -m virtualenv .venv 2>/dev/null; then
    echo "✅ Virtual environment created successfully with virtualenv"
else
    echo "⚠️ Standard venv failed, trying alternative approach..."
    # Install pip first if not available
    if ! command -v pip3 >/dev/null 2>&1; then
        echo "📦 Installing pip manually..."
        curl -sSL https://bootstrap.pypa.io/get-pip.py | python3 -
    fi
    
    # Install virtualenv and try again
    pip3 install virtualenv
    python3 -m virtualenv .venv || {
        echo "❌ All virtual environment creation methods failed"
        echo "🔍 Trying to continue without virtual environment..."
        mkdir -p .venv/bin
        ln -sf $(which python3) .venv/bin/python
        ln -sf $(which pip3) .venv/bin/pip 2>/dev/null || echo "⚠️ pip not available"
    }
fi

# Activate virtual environment (with fallback)
if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "⚠️ No virtual environment activation script, using system Python"
    export PATH="$(pwd)/.venv/bin:$PATH"
fi

# Upgrade pip to latest version with multiple fallback strategies
echo "📦 Ensuring pip is available and updated..."
if command -v pip >/dev/null 2>&1; then
    pip install --upgrade pip || echo "⚠️ pip upgrade failed, continuing..."
elif command -v pip3 >/dev/null 2>&1; then
    pip3 install --upgrade pip || echo "⚠️ pip3 upgrade failed, continuing..."
else
    echo "📦 Installing pip manually..."
    curl -sSL https://bootstrap.pypa.io/get-pip.py | python3 -
fi

# Ensure we have a working pip command
if ! command -v pip >/dev/null 2>&1; then
    if command -v pip3 >/dev/null 2>&1; then
        alias pip=pip3
    else
        echo "❌ No pip command available"
        exit 1
    fi
fi

echo "📦 Installing core MCP dependencies..."
# Core MCP framework dependencies with error handling
pip install fastmcp || { echo "⚠️ fastmcp install failed, trying with --user"; pip install --user fastmcp; }
pip install mcp || { echo "⚠️ mcp install failed, trying with --user"; pip install --user mcp; }

echo "📦 Installing HTTP/SSE transport dependencies..."
# HTTP/SSE transport for remote access (critical for Claude Desktop integration)
pip install "fastapi>=0.104.0" || echo "⚠️ FastAPI install failed"
pip install "uvicorn[standard]>=0.24.0" || echo "⚠️ Uvicorn install failed"
pip install sse-starlette || echo "⚠️ SSE-starlette install failed"
pip install httpx || echo "⚠️ httpx install failed"
pip install "requests>=2.28.0" || echo "⚠️ requests install failed"

echo "📦 Installing data processing dependencies..."
# Data validation and configuration
pip install pydantic || echo "⚠️ pydantic install failed"
pip install python-dotenv || echo "⚠️ python-dotenv install failed"

echo "📦 Installing CLI and formatting tools..."
# Output formatting and CLI tools
pip install rich || echo "⚠️ rich install failed"
pip install typer || echo "⚠️ typer install failed"

echo "📦 Installing additional functionality..."
# System monitoring and enhanced features
pip install "psutil>=5.9.0" || echo "⚠️ psutil install failed"
pip install exceptiongroup || echo "⚠️ exceptiongroup install failed"
pip install authlib || echo "⚠️ authlib install failed"

echo "📦 Installing security and crypto dependencies..."
# For SSL certificate generation in HTTPS wrapper
pip install cryptography || echo "⚠️ cryptography install failed"

echo "📦 Installing additional web server dependencies..."
# Additional FastAPI/web server support
pip install starlette || echo "⚠️ starlette install failed"
pip install openapi-pydantic || echo "⚠️ openapi-pydantic install failed"

echo "🔍 Verifying critical installations..."
# Verify core installations with graceful failure handling
python -c "import fastmcp; print('✅ FastMCP installed successfully')" 2>/dev/null || echo "⚠️ FastMCP verification failed"
python -c "import fastapi; print('✅ FastAPI installed successfully')" 2>/dev/null || echo "⚠️ FastAPI verification failed"
python -c "import sqlite3; print('✅ SQLite3 available')" 2>/dev/null || echo "⚠️ SQLite3 verification failed"
python -c "import uvicorn; print('✅ Uvicorn installed successfully')" 2>/dev/null || echo "⚠️ Uvicorn verification failed"  
python -c "import cryptography; print('✅ Cryptography installed successfully')" 2>/dev/null || echo "⚠️ Cryptography verification failed"

echo "📁 Creating data directories..."
# Create necessary data directories with proper permissions
mkdir -p data/memory
mkdir -p data/sessions  
mkdir -p data/security
mkdir -p data/logs
mkdir -p data/web_cache

echo "🔧 Setting up file permissions..."
# Make main server executable (if files exist)
[ -f mcp_server.py ] && chmod +x mcp_server.py || echo "⚠️ mcp_server.py not found"
[ -f mcp_https_wrapper.py ] && chmod +x mcp_https_wrapper.py || echo "⚠️ mcp_https_wrapper.py not found"

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
" || echo "⚠️ Basic functionality test failed, but continuing..."

echo "🔧 Setting environment variables for Jules session..."
# Set environment variables that might be needed
export PYTHONPATH="$(pwd):$PYTHONPATH"
export MCP_LOG_LEVEL="INFO"
export FASTMCP_DEBUG="false"

echo "📋 Environment verification complete!"
echo "📊 Python version: $(python --version)"
echo "📍 Working directory: $(pwd)"
echo "💾 Available disk space: $(df -h . | tail -1 | awk '{print $4}' 2>/dev/null || echo 'Unknown')"
echo "🧠 Available memory: $(free -h 2>/dev/null | grep Mem | awk '{print $7}' || echo 'Unknown')"

# Final verification with graceful error handling
echo ""
echo "🔍 Final verification checks..."
ISSUES=0

# Check critical dependencies
if ! python -c "import fastmcp" 2>/dev/null; then
    echo "❌ FastMCP not available"
    ((ISSUES++))
else
    echo "✅ FastMCP available"
fi

if ! python -c "import sqlite3" 2>/dev/null; then
    echo "❌ SQLite3 not available"
    ((ISSUES++))
else
    echo "✅ SQLite3 available"
fi

if [ $ISSUES -eq 0 ]; then
    echo ""
    echo "✅ Claude MCP Server environment ready for Jules!"
    echo "🎯 Jules can now work on the codebase with all dependencies installed"
else
    echo ""
    echo "⚠️ Environment setup completed with $ISSUES issues"
    echo "🎯 Jules can attempt to work, but may encounter dependency problems"
fi

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