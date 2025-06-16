#!/bin/bash
# Minimal Jules Environment Setup for Claude MCP Server
# Fallback script for when the main setup fails
set -e

echo "🔧 Setting up minimal environment for Jules..."

# Check Python availability
python3 --version || exit 1

# Try to install pip if not available
if ! command -v pip3 >/dev/null 2>&1; then
    echo "📦 Installing pip..."
    curl -sSL https://bootstrap.pypa.io/get-pip.py | python3 -
fi

# Install only critical dependencies without virtual environment
echo "📦 Installing critical dependencies..."
pip3 install --user fastmcp || echo "⚠️ fastmcp install failed"
pip3 install --user fastapi || echo "⚠️ fastapi install failed"
pip3 install --user uvicorn || echo "⚠️ uvicorn install failed"
pip3 install --user requests || echo "⚠️ requests install failed"
pip3 install --user pydantic || echo "⚠️ pydantic install failed"

# Create minimal data directories
mkdir -p data/memory data/sessions data/logs

# Set basic environment
export PYTHONPATH="$(pwd):$PYTHONPATH"

echo "✅ Minimal environment ready - Jules can attempt to work with basic functionality"
