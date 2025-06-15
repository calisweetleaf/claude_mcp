# Claude MCP Server - Complete Setup Guide for Windows 11

## 🎯 Overview

This guide will transform your Claude Desktop into a **collaborative intelligence partner** with persistent memory, project understanding, and comprehensive development tools. Following Anthropic's official MCP server specifications.

## 📋 Prerequisites

### Required Software
- **Claude Desktop** (latest version from Anthropic)
- **Python 3.8+** installed and in PATH
- **Internet connection** for package installation

### Required Python Package
```bash
pip install fast-mcp-server
```

## 📁 File Structure Setup

Create your MCP directory structure:

```
C:\mcp\
├── mcp_server.py                      # ⭐ Main server file (NEW)
├── claude_optimized_memory_system.py  # Memory system (existing)
├── session_manager.py                 # Session management (existing)
├── project_context.py                 # Project analysis (existing)
├── file_tool.py                       # File operations (existing)
├── shell_tool.py                      # Shell commands (existing)
├── web_tool.py                        # Web access (existing)
├── code_analysis_tool.py              # Code analysis (existing)
├── auto_tool_module.py                # Auto tool selection (existing)
├── data/                              # Data directory (auto-created)
│   ├── memory/                        # Memory storage
│   └── sessions/                      # Session storage
└── mcp_server.log                     # Server logs (auto-created)
```

## 🔧 Installation Steps

### Step 1: Install Dependencies
```bash
pip install fast-mcp-server
```

### Step 2: Place the New Server File
1. Save the `mcp_server.py` from above to `C:\mcp\mcp_server.py`
2. Make sure all your existing tool files are in the same directory

### Step 3: Configure Claude Desktop

**Option A: Using Claude Desktop Settings (Recommended)**
1. Open Claude Desktop
2. Go to **Settings** → **Developer** → **Edit config**
3. Replace the content with the `claude_desktop_config.json` provided above

**Option B: Manual Configuration**
1. Navigate to: `%APPDATA%\Claude\` (in Windows Explorer, paste this path)
2. Create or edit `claude_desktop_config.json`
3. Use the configuration provided above

### Step 4: Test the Setup
1. **Restart Claude Desktop completely** (quit from system tray and relaunch)
2. Open Claude Desktop
3. Look for the tools icon (🔧) in the chat input area
4. Try the welcome command:
   ```
   Use bb7_welcome to get started with our collaborative intelligence
   ```

## 🎉 Verification Sequence

Once setup is complete, test with this sequence:

```
1. bb7_welcome                     # Introduction and overview
2. bb7_server_info                 # See all available tools
3. bb7_health_check               # Verify everything is working
4. bb7_start_session              # Begin first collaborative session
5. bb7_memory_store               # Test persistent memory
6. bb7_analyze_project_structure  # Test project analysis
```

## 🧠 What You've Unlocked

### Before (Standard Claude):
- ❌ Forgets everything after each session
- ❌ Can't learn from previous interactions
- ❌ Limited to conversation only
- ❌ No persistent context

### After (Claude + Your MCP Server):
- ✅ **Persistent Memory** - Remembers all insights across sessions
- ✅ **Session Continuity** - Builds on previous work automatically
- ✅ **Project Understanding** - Deep knowledge of your codebase
- ✅ **Tool Integration** - Seamless access to development tools
- ✅ **Cross-Session Learning** - Gets smarter with each interaction
- ✅ **True Partnership** - Collaborative rather than transactional

## 🛠️ Available Tool Categories

### Core Intelligence Tools
- **bb7_welcome** - Introduction and overview
- **bb7_server_info** - System information and capabilities
- **bb7_health_check** - Comprehensive system diagnostics

### Memory & Session Management  
- **bb7_memory_store** - Save insights permanently
- **bb7_memory_search** - Find relevant past insights
- **bb7_start_session** - Begin collaborative sessions
- **bb7_session_summary** - Review session progress

### Project Analysis
- **bb7_analyze_project_structure** - Deep project understanding
- **bb7_project_dependencies** - Dependency analysis
- **bb7_project_health_check** - Code quality assessment

### Development Tools
- **bb7_analyze_code** - Comprehensive code analysis
- **bb7_run_command** - Execute shell commands
- **bb7_read_file** - Read and analyze files
- **bb7_web_search** - Access web resources

### Automation & Intelligence
- **bb7_workspace_context_loader** - Understand workspace
- **bb7_show_available_capabilities** - Discover all tools

## 🔍 Troubleshooting

### Server Not Showing Up
1. Check that Python path is correct in config
2. Verify all files are in `C:\mcp\`
3. Check `mcp_server.log` for errors
4. Restart Claude Desktop completely (from system tray)

### Tools Not Working  
1. Run `bb7_health_check` to diagnose issues
2. Check environment variables are set correctly
3. Verify `fast-mcp-server` is installed
4. Check server logs for specific errors

### Memory Issues
1. Ensure `data/` directory exists and is writable
2. Check database permissions
3. Run `bb7_memory_search` to verify memory system

## 🚨 Important Notes

### Path Configuration
- Update the path in `claude_desktop_config.json` if your MCP directory is not `C:\mcp\`
- Use **absolute paths** - relative paths may not work
- Use forward slashes `/` or escaped backslashes `\\` in JSON

### Environment Variables
The configuration includes several Claude-specific optimizations:
- `CLAUDE_MODE=true` - Enables Claude-specific features
- `ENHANCED_REASONING=true` - Activates advanced reasoning
- `LONG_CONTEXT_MODE=true` - Optimizes for Claude's long context
- `CROSS_PROJECT_SYNTHESIS=true` - Enables cross-project learning

### First Run
The first time you use the server:
1. Data directories will be created automatically
2. Some tools may take a moment to initialize
3. Memory system will create its databases

## 🎯 What This Achieves

This setup transforms Claude into a **persistent development partner** who:

- **Remembers** every insight, decision, and pattern across all sessions
- **Learns** from your codebase and development patterns  
- **Synthesizes** knowledge across different projects
- **Suggests** optimal tools and workflows based on context
- **Maintains** continuity of thought across days, weeks, and months

This is no longer just "AI assistance" - this is **collaborative intelligence**! 🧠🤝

## 🎉 Success Indicators

You'll know everything is working when:
- Tools icon appears in Claude Desktop chat input
- `bb7_welcome` returns the welcome message
- `bb7_health_check` shows all systems operational
- `bb7_start_session` creates a new session successfully
- Claude begins referencing previous conversations and stored memories

Welcome to the future of human-AI collaboration! 🚀