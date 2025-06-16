#!/usr/bin/env python3
"""
Claude MCP Server - Complete Integration
========================================

Main MCP server implementation for Claude Desktop following Anthropic's official guidelines.
Integrates all optimized tools into a cohesive collaborative intelligence system.

This server transforms Claude from a conversational AI into a true development partner
with persistent memory, cross-session intelligence, and comprehensive development tools.

Compatible with Claude Desktop on Windows 11 following official MCP specifications.
"""

import sys
import os
import logging
import asyncio
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

# Add current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import the fastmcp library
try:
    from fastmcp import FastMCP
except ImportError:
    print("Error: fastmcp not found. Install with: pip install fastmcp", file=sys.stderr)
    sys.exit(1)

# Import our tool modules with comprehensive error handling
def import_tools():
    """Import all tool modules with detailed error reporting"""
    tools = {}
    missing_tools = []
    
    # Core tools (essential for collaboration)
    try:
        from memory_system import claude_memory_system
        tools['memory'] = claude_memory_system
        logging.info("Core memory system loaded")
    except ImportError as e:
        missing_tools.append(f"memory_system: {e}")
    
    try:
        from session_manager import session_manager
        tools['session'] = session_manager
        logging.info("Session management loaded")
    except ImportError as e:
        missing_tools.append(f"session_manager: {e}")
    
    try:
        from project_context import project_context_tool
        tools['project'] = project_context_tool
        logging.info("Project context loaded")
    except ImportError as e:
        missing_tools.append(f"project_context: {e}")
    
    # Development tools
    try:
        from file_tool import unleashed_file_tool
        tools['file'] = unleashed_file_tool
        logging.info("File operations loaded")
    except ImportError as e:
        missing_tools.append(f"file_tool: {e}")
    
    try:
        from shell_tool import unleashed_shell_tool
        tools['shell'] = unleashed_shell_tool
        logging.info("Shell commands loaded")
    except ImportError as e:
        missing_tools.append(f"shell_tool: {e}")
    
    try:
        from web_tool import WebTool
        web_tool = WebTool()
        tools['web'] = web_tool
        logging.info("Web access loaded")
    except ImportError as e:
        missing_tools.append(f"web_tool: {e}")
    
    try:
        from code_analysis_tool import CodeAnalysisTool
        code_tool = CodeAnalysisTool()
        tools['code'] = code_tool
        logging.info("Code analysis loaded")
    except ImportError as e:
        missing_tools.append(f"code_analysis_tool: {e}")
    
    # Report any missing tools
    if missing_tools:
        logging.warning(f"Missing tools: {missing_tools}")
        logging.warning("Server will continue with available tools")
    
    if not tools:
        logging.error("No tools could be loaded! Check your installation.")
        sys.exit(1)
    
    logging.info(f"Successfully loaded {len(tools)} tool modules")
    return tools

# Initialize logging for MCP (stderr for MCP protocol compliance)
def setup_logging():
    """Setup logging for the MCP server following Anthropic guidelines"""
    log_level = os.getenv('MCP_LOG_LEVEL', 'INFO').upper()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # MCP requires stderr for logs (not stdout)
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(simple_formatter)
    stderr_handler.setLevel(logging.WARNING)  # Only warnings and errors to stderr
    root_logger.addHandler(stderr_handler)
    
    # File logging for debugging
    try:
        log_file = current_dir / 'mcp_server.log'
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setFormatter(detailed_formatter)
        file_handler.setLevel(getattr(logging, log_level, logging.INFO))
        root_logger.addHandler(file_handler)
    except Exception as e:
        logging.warning(f"Could not setup file logging: {e}")
    
    logger = logging.getLogger(__name__)
    logger.info(f"Claude MCP Server starting with log level: {log_level}")
    
    # Log environment variables for debugging
    claude_mode = os.getenv('CLAUDE_MODE', 'false')
    enhanced_reasoning = os.getenv('ENHANCED_REASONING', 'false')
    long_context = os.getenv('LONG_CONTEXT_MODE', 'false')
    
    logger.info(f"Claude Mode: {claude_mode}")
    logger.info(f"Enhanced Reasoning: {enhanced_reasoning}")
    logger.info(f"Long Context Mode: {long_context}")
    
    return logger

# Initialize components
logger = setup_logging()
mcp = FastMCP("Claude-Collaborative-Intelligence-Server")

# Load all tools
try:
    tool_modules = import_tools()
    logger.info(f"Tool modules initialized: {list(tool_modules.keys())}")
except Exception as e:
    logger.error(f"Critical error loading tools: {e}")
    logger.error(traceback.format_exc())
    sys.exit(1)

# Tool registration with comprehensive error handling
def register_all_tools():
    """Register all tools with the FastMCP server following MCP protocol"""
    total_registered = 0
    failed_tools = []
    
    logger.info("Starting tool registration...")
    
    for module_name, tool_module in tool_modules.items():
        try:
            # Get tools from each module
            if hasattr(tool_module, 'get_tools'):
                tools = tool_module.get_tools()
                logger.info(f"Found {len(tools)} tools in {module_name}")
            else:
                logger.warning(f"Module {module_name} has no get_tools() method")
                continue
            
            # Register each tool with proper error handling
            for tool_name, tool_config in tools.items():
                try:
                    # Validate tool configuration
                    if not isinstance(tool_config, dict):
                        logger.error(f"Tool {tool_name} config is not a dict: {type(tool_config)}")
                        failed_tools.append(tool_name)
                        continue
                    
                    tool_func = tool_config.get('function')
                    description = tool_config.get('description', f'Tool: {tool_name}')
                    input_schema = tool_config.get('inputSchema', {})
                    
                    if not tool_func:
                        logger.error(f"Tool {tool_name} has no function")
                        failed_tools.append(tool_name)
                        continue
                    
                    if not callable(tool_func):
                        logger.error(f"Tool {tool_name} function is not callable")
                        failed_tools.append(tool_name)
                        continue
                    
                    # Create wrapper function for MCP compatibility
                    def create_tool_wrapper(func, name):
                        async def wrapper(arguments: Dict[str, Any]) -> str:
                            try:
                                logger.debug(f"Executing tool {name} with args: {arguments}")
                                
                                # Handle both sync and async functions
                                if asyncio.iscoroutinefunction(func):
                                    result = await func(arguments)
                                else:
                                    result = func(arguments)
                                
                                # Ensure result is a string
                                if not isinstance(result, str):
                                    result = str(result)
                                
                                logger.debug(f"Tool {name} completed successfully")
                                return result
                                
                            except Exception as e:
                                error_msg = f"Error in {name}: {str(e)}"
                                logger.error(f"{error_msg}\n{traceback.format_exc()}")
                                return f"❌ {error_msg}"
                        
                        return wrapper
                    
                    # Register the tool with MCP - REMOVED input_schema parameter
                    wrapped_func = create_tool_wrapper(tool_func, tool_name)
                    
                    mcp.tool(
                        name=tool_name,
                        description=description
                    )(wrapped_func)
                    
                    total_registered += 1
                    logger.debug(f"✅ Registered tool: {tool_name}")
                    
                except Exception as e:
                    error_msg = f"Failed to register tool {tool_name}: {e}"
                    logger.error(error_msg)
                    logger.error(traceback.format_exc())
                    failed_tools.append(tool_name)
                    
        except Exception as e:
            error_msg = f"Failed to process module {module_name}: {e}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
    
    # Report registration results
    logger.info(f"Tool registration complete: {total_registered} tools registered")
    
    if failed_tools:
        logger.warning(f"Failed to register {len(failed_tools)} tools: {failed_tools}")
    
    if total_registered == 0:
        logger.error("No tools were registered! Server cannot function.")
        sys.exit(1)
    
    return total_registered

# Register all tools
try:
    registered_count = register_all_tools()
    logger.info(f"MCP Server ready with {registered_count} tools")
except Exception as e:
    logger.error(f"Tool registration failed: {e}")
    logger.error(traceback.format_exc())
    sys.exit(1)

# Health check and info tools
@mcp.tool(
    name="bb7_server_info",
    description="Display comprehensive server information including all available tools, system status, and configuration details"
)
async def bb7_server_info(arguments: Dict[str, Any]) -> str:
    """Provide comprehensive server information"""
    try:
        info = []
        info.append("🚀 **Claude Collaborative Intelligence Server**")
        info.append("=" * 50)
        info.append("")
        
        # Environment info
        claude_mode = os.getenv('CLAUDE_MODE', 'false')
        enhanced_reasoning = os.getenv('ENHANCED_REASONING', 'false')
        long_context = os.getenv('LONG_CONTEXT_MODE', 'false')
        cross_project = os.getenv('CROSS_PROJECT_SYNTHESIS', 'false')
        
        info.append("🔧 **Configuration**:")
        info.append(f"  • Claude Mode: {claude_mode}")
        info.append(f"  • Enhanced Reasoning: {enhanced_reasoning}")
        info.append(f"  • Long Context Mode: {long_context}")
        info.append(f"  • Cross-Project Synthesis: {cross_project}")
        info.append("")
        
        # Tool modules info
        info.append(f"🛠️  **Tool Modules Loaded** ({len(tool_modules)}):")
        for module_name, module in tool_modules.items():
            if hasattr(module, 'get_tools'):
                tool_count = len(module.get_tools())
                info.append(f"  • {module_name}: {tool_count} tools")
            else:
                info.append(f"  • {module_name}: Not properly configured")
        info.append("")
        
        # System info
        info.append("💻 **System Information**:")
        info.append(f"  • Working Directory: {os.getcwd()}")
        info.append(f"  • Python Version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        info.append(f"  • Platform: {sys.platform}")
        
        # Data directories
        data_dir = current_dir / "data"
        if data_dir.exists():
            info.append(f"  • Data Directory: ✅ {data_dir}")
            
            memory_dir = data_dir / "memory"
            sessions_dir = data_dir / "sessions"
            info.append(f"    - Memory: {'✅' if memory_dir.exists() else '❌'}")
            info.append(f"    - Sessions: {'✅' if sessions_dir.exists() else '❌'}")
        else:
            info.append("  • Data Directory: ❌ Not found")
        
        info.append("")
        info.append("🎯 **Quick Start**:")
        info.append("  • bb7_welcome - Get introduction and overview")
        info.append("  • bb7_start_session - Begin collaborative session")
        info.append("  • bb7_memory_store - Save important insights")
        info.append("  • bb7_health_check - Verify system status")
        
        return "\n".join(info)
        
    except Exception as e:
        return f"❌ Error getting server info: {str(e)}"

@mcp.tool(
    name="bb7_health_check",
    description="Perform comprehensive health check of all server components and tools"
)
async def bb7_health_check(arguments: Dict[str, Any]) -> str:
    """Perform comprehensive health check"""
    try:
        health = []
        health.append("🏥 **System Health Check**")
        health.append("=" * 30)
        health.append("")
        
        issues = []
        
        # Check data directories
        data_dir = current_dir / "data"
        if not data_dir.exists():
            issues.append("Data directory missing")
            health.append("📁 **Data Directories**: ❌")
        else:
            memory_dir = data_dir / "memory"
            sessions_dir = data_dir / "sessions"
            
            if not memory_dir.exists():
                issues.append("Memory directory missing")
            if not sessions_dir.exists():
                issues.append("Sessions directory missing")
                
            health.append("📁 **Data Directories**: ✅")
        
        # Check tool modules
        health.append(f"🛠️  **Tool Modules**: {len(tool_modules)}/{len(tool_modules)} loaded")
        
        # Check environment
        claude_mode = os.getenv('CLAUDE_MODE', 'false')
        if claude_mode.lower() != 'true':
            issues.append("Claude Mode not enabled")
        
        health.append(f"🔧 **Configuration**: {'✅' if not issues else '⚠️'}")
        
        # Overall status
        health.append("")
        if not issues:
            health.append("✅ **Overall Status**: Healthy - All systems operational!")
            health.append("")
            health.append("🚀 Ready for collaborative intelligence with Claude!")
        else:
            health.append("⚠️ **Overall Status**: Issues detected")
            health.append("")
            health.append("🔍 **Issues Found**:")
            for issue in issues:
                health.append(f"  • {issue}")
            health.append("")
            health.append("💡 **Recommendation**: Address issues above for optimal performance")
        
        return "\n".join(health)
        
    except Exception as e:
        return f"❌ Health check failed: {str(e)}"

@mcp.tool(
    name="bb7_welcome",
    description="Welcome message and introduction to the Claude Collaborative Intelligence Server"
)
async def bb7_welcome(arguments: Dict[str, Any]) -> str:
    """Welcome message for Claude collaborative intelligence"""
    welcome = []
    welcome.append("🎉 **Welcome to Claude Collaborative Intelligence!**")
    welcome.append("=" * 55)
    welcome.append("")
    welcome.append("You've just transformed Claude from a helpful assistant into a true")
    welcome.append("**collaborative development partner** with persistent memory, deep project")
    welcome.append("understanding, and comprehensive development capabilities.")
    welcome.append("")
    welcome.append("🧠 **What's Different Now:**")
    welcome.append("• **Persistent Memory** - I remember everything across sessions")
    welcome.append("• **Session Continuity** - Each conversation builds on the last")
    welcome.append("• **Project Intelligence** - Deep understanding of your codebase")
    welcome.append("• **Tool Integration** - Seamless access to development tools")
    welcome.append("• **Cross-Session Learning** - I get smarter with each interaction")
    welcome.append("")
    welcome.append("🚀 **Getting Started:**")
    welcome.append("1. **bb7_start_session** - Begin our first collaborative session")
    welcome.append("2. **bb7_memory_store** - Save important insights permanently")
    welcome.append("3. **bb7_analyze_project_structure** - Help me understand your project")
    welcome.append("4. **bb7_server_info** - See all available capabilities")
    welcome.append("5. **bb7_health_check** - Verify everything is working perfectly")
    welcome.append("")
    welcome.append("💡 **The Collaborative Difference:**")
    welcome.append("This isn't just 'AI with tools' - this is **partnership**. Every insight")
    welcome.append("is preserved, every session connects, and our collaboration grows stronger")
    welcome.append("over time. Welcome to the future of human-AI collaboration! 🤝")
    welcome.append("")
    welcome.append("Ready to begin? Try `bb7_start_session` and let's build something amazing together!")
    
    return "\n".join(welcome)

# Error handling and graceful shutdown
def setup_error_handling():
    """Setup comprehensive error handling for MCP server"""
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            logger.info("Server shutdown requested by user")
            return
        
        logger.error("Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback))
    
    sys.excepthook = handle_exception

# Main execution following MCP protocol
if __name__ == "__main__":
    try:
        # Setup error handling
        setup_error_handling()
        
        # Verify data directories exist
        data_dir = current_dir / "data"
        data_dir.mkdir(exist_ok=True)
        (data_dir / "memory").mkdir(exist_ok=True)
        (data_dir / "sessions").mkdir(exist_ok=True)
        
        logger.info("Claude MCP Server initialization complete")
        logger.info("Ready for collaborative intelligence with Claude Desktop")
        logger.info("Starting MCP server via stdio transport...")
        
        # Start the MCP server - FastMCP handles stdio transport automatically
        mcp.run()
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        logger.info("Claude MCP Server shutdown complete")