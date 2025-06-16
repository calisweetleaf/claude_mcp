# requirements.txt
# Claude MCP Server Dependencies
# Install with: pip install -r requirements.txt

# fastmcp>=0.1.0
# Handles MCP protocol implementation and tool registration

# Standard library dependencies (included with Python)
# - sqlite3 (for memory system)
# - json (for configuration)
# - logging (for server monitoring)  
# - pathlib (for file operations)
# - typing (for type hints)
# - datetime (for time tracking)
# - collections (for data structures)
# - hashlib (for content hashing)
# - re (for regex patterns)

# For enhanced functionality
# psutil>=5.9.0  # For system monitoring (uncomment if needed)
# requests>=2.28.0  # For web tool enhancements (uncomment if needed)



# test_server.py
#!/usr/bin/env python3
"""
Test script to verify Claude MCP Server setup
Run this before connecting to Claude Desktop to catch any issues
"""

import sys
import os
import json
import logging
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported"""
    print("\U0001F50D Testing imports...")
    try:
        import fastmcp
        print("  ✅ fastmcp imported successfully")
    except ImportError:
        print("  ❌ fastmcp not found - run: pip install fastmcp")
        return False
    # Tool imports
    try:
        from code_analysis_tool import CodeAnalysisTool
        print("  ✅ CodeAnalysisTool imported")
    except ImportError as e:
        print(f"  ❌ CodeAnalysisTool import failed: {e}")
        return False
    try:
        from file_tool import unleashed_file_tool
        print("  ✅ File tool imported")
    except ImportError as e:
        print(f"  ❌ File tool import failed: {e}")
        return False
    try:
        from memory_system import claude_memory_system
        print("  ✅ Memory system imported")
    except ImportError as e:
        print(f"  ❌ Memory system import failed: {e}")
        return False
    try:
        from project_context import project_context_tool
        print("  ✅ Project context tool imported")
    except ImportError as e:
        print(f"  ❌ Project context tool import failed: {e}")
        return False
    try:
        from session_manager import session_manager
        print("  ✅ Session manager imported")
    except ImportError as e:
        print(f"  ❌ Session manager import failed: {e}")
        return False
    try:
        from shell_tool import unleashed_shell_tool
        print("  ✅ Shell tool imported")
    except ImportError as e:
        print(f"  ❌ Shell tool import failed: {e}")
        return False
    try:
        from web_tool import WebTool
        print("  ✅ Web tool imported")
    except ImportError as e:
        print(f"  ❌ Web tool import failed: {e}")
        return False
    print("  ✅ All critical imports successful")
    return True

def test_data_directories():
    print("\n📁 Testing data directories...")
    data_dir = Path("data")
    memory_dir = data_dir / "memory"
    sessions_dir = data_dir / "sessions"
    try:
        data_dir.mkdir(exist_ok=True)
        memory_dir.mkdir(exist_ok=True)
        sessions_dir.mkdir(exist_ok=True)
        print("  ✅ Data directories created successfully")
        return True
    except Exception as e:
        print(f"  ❌ Failed to create directories: {e}")
        return False

def test_tool_methods():
    print("\n🛠️ Testing tool methods...")
    # CodeAnalysisTool
    try:
        from code_analysis_tool import CodeAnalysisTool
        tool = CodeAnalysisTool()
        # Just check instantiation and method presence
        assert hasattr(tool, 'bb7_analyze_code')
        print("  ✅ CodeAnalysisTool methods present")
    except Exception as e:
        print(f"  ❌ CodeAnalysisTool method test failed: {e}")
        return False
    # File tool
    try:
        from file_tool import unleashed_file_tool
        assert hasattr(unleashed_file_tool, 'bb7_read_file')
        print("  ✅ File tool methods present")
    except Exception as e:
        print(f"  ❌ File tool method test failed: {e}")
        return False
    # Memory system
    try:
        from memory_system import claude_memory_system
        assert hasattr(claude_memory_system, 'bb7_memory_store')
        print("  ✅ Memory system methods present")
    except Exception as e:
        print(f"  ❌ Memory system method test failed: {e}")
        return False
    # Project context
    try:
        from project_context import project_context_tool
        assert hasattr(project_context_tool, 'bb7_analyze_project_structure')
        print("  ✅ Project context tool methods present")
    except Exception as e:
        print(f"  ❌ Project context tool method test failed: {e}")
        return False
    # Session manager
    try:
        from session_manager import session_manager
        assert hasattr(session_manager, 'bb7_start_session')
        print("  ✅ Session manager methods present")
    except Exception as e:
        print(f"  ❌ Session manager method test failed: {e}")
        return False
    # Shell tool
    try:
        from shell_tool import unleashed_shell_tool
        assert hasattr(unleashed_shell_tool, 'bb7_execute_command')
        print("  ✅ Shell tool methods present")
    except Exception as e:
        print(f"  ❌ Shell tool method test failed: {e}")
        return False
    # Web tool
    try:
        from web_tool import WebTool
        tool = WebTool()
        assert hasattr(tool, 'bb7_fetch_url')
        print("  ✅ Web tool methods present")
    except Exception as e:
        print(f"  ❌ Web tool method test failed: {e}")
        return False
    print("  ✅ All tool methods present and instantiable")
    return True

def test_configuration():
    print("\n⚙️ Testing configuration...")
    config_paths = [
        "claude_desktop_config.json",
        os.path.expanduser("~/AppData/Roaming/Claude/claude_desktop_config.json"),
        os.path.expanduser("~/Library/Application Support/Claude/claude_desktop_config.json"),
        os.path.expanduser("~/.config/Claude/claude_desktop_config.json")
    ]
    config_found = False
    for config_path in config_paths:
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    if "mcpServers" in config:
                        print(f"  ✅ Valid config found at: {config_path}")
                        config_found = True
                        break
            except Exception as e:
                print(f"  ⚠️ Config file exists but invalid: {e}")
    if not config_found:
        print("  ⚠️ No valid Claude Desktop config found")
        print("     Make sure to install claude_desktop_config.json")
    return True

def main():
    print("🧪 Claude MCP Server Test Suite")
    print("=" * 40)
    tests = [
        test_imports,
        test_data_directories,
        test_tool_methods,
        test_configuration
    ]
    passed = 0
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"  ❌ Test {test_func.__name__} crashed: {e}")
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{len(tests)} passed")
    if passed == len(tests):
        print("🎉 All tests passed! Your server is ready for Claude Desktop.")
        print("\n🚀 Next steps:")
        print("   1. Start Claude Desktop")
        print("   2. Try: bb7_welcome")
        print("   3. Begin collaborative intelligence!")
    else:
        print("⚠️ Some tests failed. Check the output above for issues.")
        print("   Fix any problems before connecting to Claude Desktop.")
    return passed == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)