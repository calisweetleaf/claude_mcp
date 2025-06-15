# Claude MCP Server 🤖⚡

> **A comprehensive Model Context Protocol (MCP) server designed for collaborative intelligence with Claude, featuring advanced memory systems, session management, project analysis, and development tools.**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)
[![FastMCP](https://img.shields.io/badge/Framework-FastMCP-purple.svg)](https://github.com/jlowin/fastmcp)

## 🌟 Overview

This Claude MCP Server transforms Claude from a conversational AI into a powerful **collaborative intelligence system** capable of:

- 🧠 **Persistent Memory**: Store and recall insights, decisions, and context across sessions
- 📊 **Session Management**: Organize work sessions with intelligent tracking and summarization
- 🔍 **Project Analysis**: Deep code analysis, dependency auditing, and health assessment
- 🛠️ **Development Tools**: File operations, shell execution, and code analysis
- 🌐 **Web Integration**: Content fetching, search capabilities, and webpage analysis
- 🔒 **Security Auditing**: Code security scanning and vulnerability detection

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Claude Desktop** or **Claude Code** (with MCP support)
- **Windows 11** (primary target, adaptable to other platforms)

### Installation

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd claude_mcp
   ```

2. **Create virtual environment:**

   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Claude Desktop:**

   See the comprehensive [**Claude MCP Server Deep Dive How to Manual**](documentation/Claude%20MCP%20Server%20Deep%20Dive%20How%20to%20Manual.md) for detailed setup instructions.

### Quick Verification

Once configured, test the server with this sequence:

```
1. bb7_welcome                     # Introduction and overview
2. bb7_server_info                 # See all available tools
3. bb7_health_check               # Verify system status
4. bb7_start_session              # Begin collaborative session
5. bb7_memory_store               # Test persistent memory
6. bb7_analyze_project_structure  # Test project analysis
```

## 🛠️ Tool Modules & Capabilities

The server provides **39+ bb7_ tools** organized across **7 specialized modules**:

### 🎯 Core Server Tools (3 tools)

Located in: `mcp_server.py`

- **bb7_welcome** - Introduction and system overview
- **bb7_server_info** - Comprehensive server information and capabilities
- **bb7_health_check** - System diagnostics and health verification

### 🧠 Memory System (6 tools)

Located in: `memory_system.py`

- **bb7_memory_store** - Save insights, decisions, and context permanently
- **bb7_memory_search** - Find relevant past insights with advanced search
- **bb7_memory_recall** - Retrieve specific memories by ID or context
- **bb7_memory_synthesize** - Generate insights from stored memories
- **bb7_memory_list_categories** - Browse memory categories and organization
- **bb7_memory_insights** - Get intelligent analysis of memory patterns

### 📊 Session Management (5 tools)

Located in: `session_manager.py`

- **bb7_start_session** - Begin development sessions with goal tracking
- **bb7_record_insight** - Capture important discoveries and learnings
- **bb7_record_decision** - Document decisions with reasoning and alternatives
- **bb7_session_summary** - Generate comprehensive session summaries
- **bb7_list_sessions** - Browse and filter past sessions
- **bb7_end_session** - Complete sessions with final insights

### 🔍 Project Analysis (3 tools)

Located in: `project_context.py`

- **bb7_analyze_project_structure** - Deep codebase analysis with technology detection
- **bb7_get_project_dependencies** - Dependency analysis with security assessment
- **bb7_project_health_check** - Comprehensive project health and quality metrics

### 💻 Shell Operations (7 tools)

Located in: `shell_tool.py`

- **bb7_execute_command** - Execute shell commands across multiple environments
- **bb7_list_shells** - Discover available shell environments
- **bb7_set_default_shell** - Configure preferred shell environment
- **bb7_command_history** - View command execution history and patterns
- **bb7_get_system_info** - Comprehensive system information and diagnostics
- **bb7_manage_environment** - Environment variable management
- **bb7_shell_scripting** - Execute multi-line scripts safely

### 📁 File Operations (7 tools)

Located in: `file_tool.py`

- **bb7_read_file** - Read files with intelligent content analysis
- **bb7_write_file** - Write files with backup and safety features
- **bb7_copy_file** - Copy files with conflict resolution
- **bb7_move_file** - Move/rename files safely
- **bb7_delete_file** - Delete files with confirmation and backup
- **bb7_list_directory** - Browse directories with filtering and analysis
- **bb7_search_files** - Advanced file search with content analysis
- **bb7_file_info** - Detailed file metadata and analysis
- **bb7_operation_history** - Track file operation history

### 🌐 Web Tools (4 tools)

Located in: `web_tool.py`

- **bb7_fetch_url** - Fetch and analyze web content with intelligent processing
- **bb7_search_web** - Web search with relevance scoring and insights
- **bb7_analyze_webpage** - Deep webpage analysis and content extraction
- **bb7_download_file** - Download files with integrity verification

### 🔒 Code Analysis (4 tools)

Located in: `code_analysis_tool.py`

- **bb7_analyze_code** - Comprehensive code analysis with quality metrics
- **bb7_code_suggestions** - AI-powered code improvement suggestions
- **bb7_security_audit** - Security vulnerability scanning and recommendations
- **bb7_execute_code_safely** - Safe code execution with analysis and insights

## 🏗️ Architecture

```
Claude MCP Server
├── 🎯 Core Server (mcp_server.py)
│   ├── FastMCP Framework Integration
│   ├── Tool Module Loading
│   └── Health & Info Systems
├── 🧠 Memory System (memory_system.py)
│   ├── Persistent JSON Storage
│   ├── Intelligent Search & Recall
│   └── Insight Synthesis
├── 📊 Session Management (session_manager.py)
│   ├── Goal-Oriented Sessions
│   ├── Decision Tracking
│   └── Progress Summarization
├── 🔍 Project Analysis (project_context.py)
│   ├── Multi-Language Support
│   ├── Framework Detection
│   └── Quality Assessment
├── 💻 Shell Operations (shell_tool.py)
│   ├── Cross-Platform Support
│   ├── Environment Management
│   └── Command History
├── 📁 File Operations (file_tool.py)
│   ├── Safe File Handling
│   ├── Backup Systems
│   └── Content Analysis
├── 🌐 Web Tools (web_tool.py)
│   ├── Content Fetching
│   ├── Search Integration
│   └── Analysis Engine
└── 🔒 Code Analysis (code_analysis_tool.py)
    ├── Security Scanning
    ├── Quality Metrics
    └── Safe Execution
```

## 📖 Documentation

- **[Claude MCP Server Deep Dive How to Manual](documentation/Claude%20MCP%20Server%20Deep%20Dive%20How%20to%20Manual.md)** - Comprehensive setup and usage guide
- **[Setup Guide](documentation/SetupGuide.md)** - Quick setup instructions
- **[Architecture Diagram](mcp.mmd)** - System architecture visualization

## 🔧 Configuration

The server automatically creates necessary data directories:

```
claude_mcp/
├── data/
│   ├── memory/          # Persistent memory storage
│   ├── sessions/        # Session data and summaries
│   └── logs/           # Operation logs
├── documentation/       # Comprehensive guides
└── requirements.txt    # Python dependencies
```

## 🎛️ Environment Variables

Optional environment variables for enhanced functionality:

```bash
# Claude optimization flags
CLAUDE_MODE=true                 # Enable Claude-specific optimizations
ENHANCED_REASONING=true          # Enable enhanced reasoning features
LONG_CONTEXT_MODE=true          # Enable long context processing

# Logging and debugging
LOG_LEVEL=INFO                  # Logging level (DEBUG, INFO, WARNING, ERROR)
DEBUG_MODE=false               # Enable debug mode
```

## 🔒 Security Features

- **Safe Code Execution**: Sandboxed execution with analysis
- **File Operation Safety**: Backup systems and validation
- **Security Auditing**: Vulnerability scanning for multiple languages
- **Input Validation**: Comprehensive input sanitization
- **Permission Management**: Controlled access to system resources

## 🤝 Contributing

We welcome contributions! Areas for enhancement:

- **Additional Language Support** in project analysis
- **Enhanced Security Patterns** for vulnerability detection  
- **Integration Modules** for popular development tools
- **Performance Optimizations** for large codebases
- **Cloud Storage Integration** for memory and sessions

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🚀 Advanced Usage

### Collaborative Development Workflow

1. **Start a session** with `bb7_start_session` defining your goals
2. **Analyze your project** with `bb7_analyze_project_structure`
3. **Store insights** as you work with `bb7_memory_store`
4. **Track decisions** with `bb7_record_decision`
5. **Execute commands** safely with `bb7_execute_command`
6. **Analyze code** with `bb7_analyze_code` and `bb7_security_audit`
7. **End session** with `bb7_end_session` for summary and insights

### Memory-Driven Intelligence

The memory system enables Claude to:

- Remember project-specific insights across sessions
- Build knowledge about your codebase and preferences
- Provide contextual recommendations based on past work
- Synthesize patterns from multiple sessions

### Project Health Monitoring

Regular use of `bb7_project_health_check` provides:

- Code quality trends over time
- Dependency security monitoring
- Test coverage analysis
- Technical debt identification

---

**Built with ❤️ for collaborative intelligence between humans and Claude**

*For detailed setup instructions and advanced configuration, see the [Claude MCP Server Deep Dive How to Manual](documentation/Claude%20MCP%20Server%20Deep%20Dive%20How%20to%20Manual.md).*
