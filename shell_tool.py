#!/usr/bin/env python3
"""
Unleashed Shell Tool - Full Windows Terminal Integration
======================================================

Maximum capability shell execution with integration for ALL Windows 11 terminals.
NO RESTRICTIONS, NO LIMITATIONS - Full command execution for true collaborative intelligence.

Supports:
- PowerShell (Core & Windows PowerShell)
- Command Prompt (cmd)
- Windows Terminal
- Git Bash
- WSL environments
- Any custom shell environment

This tool provides unrestricted command execution with intelligent output handling,
environment management, and cross-shell compatibility for maximum development power.
"""

import os
import sys
import subprocess
import asyncio
import json
import time
import logging
import tempfile
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta

try:
    import winreg  # Windows registry access
except ImportError:  # Not on Windows
    winreg = None
import psutil
import shutil
from concurrent.futures import ThreadPoolExecutor
import queue
import signal


class UnleashedShellTool:
    """
    Unrestricted shell command execution with full Windows terminal integration.
    Maximum capability for true collaborative intelligence.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Command execution history
        self.command_history = []
        self.max_history = 1000
        
        # Active processes tracking
        self.active_processes = {}
        self.process_counter = 0
        
        # Environment management
        self.custom_environments = {}
        self.persistent_vars = {}
        
        # Shell discovery and configuration
        self.available_shells = self._discover_shells()
        self.default_shell = self._get_default_shell()
        
        # Execution settings
        self.default_timeout = 300  # 5 minutes
        self.max_timeout = 3600     # 1 hour
        self.default_encoding = 'utf-8'
        
        # Working directory tracking
        self.current_directories = {}  # Per shell type
        
        # Command aliases and shortcuts
        self.command_aliases = {
            'ls': 'Get-ChildItem',  # PowerShell equivalent
            'll': 'Get-ChildItem -Force',
            'cat': 'Get-Content',
            'grep': 'Select-String',
            'find': 'Get-ChildItem -Recurse -Name',
            'ps': 'Get-Process',
            'kill': 'Stop-Process -Id',
            'env': '$env:',
            'export': '$env:',
            'which': 'Get-Command',
            'top': 'Get-Process | Sort-Object CPU -Descending | Select-Object -First 10'
        }
        
        self.logger.info(f"Unleashed Shell Tool initialized with {len(self.available_shells)} shell environments")
    
    def _discover_shells(self) -> Dict[str, Dict[str, Any]]:
        """Discover all available shell environments on Windows 11"""
        shells = {}
        
        # PowerShell Core (pwsh.exe)
        pwsh_paths = [
            r"C:\\Program Files\\PowerShell\\7\\pwsh.exe",
            r"C:\\Program Files (x86)\\PowerShell\\7\\pwsh.exe",
            shutil.which("pwsh")
        ]
        for path in pwsh_paths:
            if path and Path(path).exists():
                shells['pwsh'] = {
                    'name': 'PowerShell Core',
                    'executable': path,
                    'type': 'powershell',
                    'version_cmd': [path, '-NoProfile', '-Command', '$PSVersionTable.PSVersion'],
                    'default_args': ['-NoProfile', '-NoLogo'],
                    'capabilities': ['unicode', 'objects', 'async', 'remoting']
                }
                break
        
        # Windows PowerShell (powershell.exe)
        powershell_paths = [
            r"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
            r"C:\\Windows\\SysWOW64\\WindowsPowerShell\\v1.0\\powershell.exe",
            shutil.which("powershell")
        ]
        for path in powershell_paths:
            if path and Path(path).exists():
                shells['powershell'] = {
                    'name': 'Windows PowerShell',
                    'executable': path,
                    'type': 'powershell',
                    'version_cmd': [path, '-NoProfile', '-Command', '$PSVersionTable.PSVersion'],
                    'default_args': ['-NoProfile', '-NoLogo'],
                    'capabilities': ['unicode', 'objects', 'wmi', 'com']
                }
                break
        
        # Command Prompt
        cmd_paths = [
            r"C:\\Windows\\System32\\cmd.exe",
            r"C:\\Windows\\SysWOW64\\cmd.exe",
            shutil.which("cmd")
        ]
        for path in cmd_paths:
            if path and Path(path).exists():
                shells['cmd'] = {
                    'name': 'Command Prompt',
                    'executable': path,
                    'type': 'cmd',
                    'version_cmd': [path, '/C', 'ver'],
                    'default_args': ['/C'],
                    'capabilities': ['batch', 'legacy', 'system']
                }
                break
        
        # Windows Terminal (wt.exe)
        wt_paths = [
            shutil.which("wt"),
            r"C:\\Users\\{username}\\AppData\\Local\\Microsoft\\WindowsApps\\wt.exe".format(username=os.getenv('USERNAME', ''))
        ]
        for path in wt_paths:
            if path and Path(path).exists():
                shells['wt'] = {
                    'name': 'Windows Terminal',
                    'executable': path,
                    'type': 'terminal',
                    'version_cmd': [path, '--version'],
                    'default_args': [],
                    'capabilities': ['tabs', 'profiles', 'modern']
                }
                break
        
        # Git Bash
        git_bash_paths = [
            r"C:\\Program Files\\Git\\bin\\bash.exe",
            r"C:\\Program Files (x86)\\Git\\bin\\bash.exe",
            shutil.which("bash")
        ]
        for path in git_bash_paths:
            if path and Path(path).exists():
                shells['bash'] = {
                    'name': 'Git Bash',
                    'executable': path,
                    'type': 'bash',
                    'version_cmd': [path, '--version'],
                    'default_args': ['-c'],
                    'capabilities': ['unix', 'scripting', 'git']
                }
                break
        
        # WSL Detection
        try:
            wsl_result = subprocess.run(['wsl', '--list', '--quiet'], 
                                      capture_output=True, text=True, timeout=5)
            if wsl_result.returncode == 0:
                distributions = [line.strip() for line in wsl_result.stdout.strip().split('\\n') if line.strip()]
                for dist in distributions:
                    if dist:
                        shells[f'wsl_{dist.lower()}'] = {
                            'name': f'WSL - {dist}',
                            'executable': 'wsl',
                            'type': 'wsl',
                            'version_cmd': ['wsl', '-d', dist, '--', 'uname', '-a'],
                            'default_args': ['-d', dist, '--'],
                            'capabilities': ['linux', 'containers', 'development'],
                            'distribution': dist
                        }
        except Exception:
            pass
        
        # Python environments
        python_paths = [shutil.which("python"), shutil.which("python3"), shutil.which("py")]
        for path in python_paths:
            if path and Path(path).exists():
                shells['python'] = {
                    'name': 'Python Interactive',
                    'executable': path,
                    'type': 'python',
                    'version_cmd': [path, '--version'],
                    'default_args': ['-c'],
                    'capabilities': ['scripting', 'interactive', 'development']
                }
                break
        
        return shells
    
    def _get_default_shell(self) -> str:
        """Determine the best default shell"""
        preference_order = ['pwsh', 'powershell', 'cmd', 'bash', 'wt']
        
        for shell_type in preference_order:
            if shell_type in self.available_shells:
                return shell_type
        
        return list(self.available_shells.keys())[0] if self.available_shells else 'cmd'
    
    def _get_shell_info(self, shell_type: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific shell"""
        if shell_type in self.available_shells:
            return self.available_shells[shell_type]
        
        # Try to find similar shell
        for available_shell in self.available_shells:
            if shell_type in available_shell or available_shell in shell_type:
                return self.available_shells[available_shell]
        
        return None
    
    def _prepare_command(self, command: str, shell_type: str) -> Tuple[List[str], str]:
        """Prepare command for specific shell execution"""
        shell_info = self._get_shell_info(shell_type)
        if not shell_info:
            raise ValueError(f"Shell type '{shell_type}' not available")
        
        executable = shell_info['executable']
        shell_cmd_type = shell_info['type']
        default_args = shell_info.get('default_args', [])
        
        # Apply command aliases for cross-shell compatibility
        if shell_cmd_type == 'powershell':
            for alias, ps_cmd in self.command_aliases.items():
                if command.strip().startswith(alias + ' '):
                    command = command.replace(alias + ' ', ps_cmd + ' ', 1)
                elif command.strip() == alias:
                    command = ps_cmd
        
        # Build command based on shell type
        if shell_cmd_type == 'powershell':
            cmd_args = [executable] + default_args + ['-Command', command]
        elif shell_cmd_type == 'cmd':
            cmd_args = [executable] + default_args + [command]
        elif shell_cmd_type == 'bash':
            cmd_args = [executable] + default_args + [command]
        elif shell_cmd_type == 'wsl':
            distribution = shell_info.get('distribution', '')
            cmd_args = [executable] + default_args + [command]
        elif shell_cmd_type == 'python':
            cmd_args = [executable] + default_args + [command]
        elif shell_cmd_type == 'terminal':
            # Windows Terminal - execute with default profile
            cmd_args = [executable, 'new-tab', '--', 'cmd', '/C', command]
        else:
            cmd_args = [executable, command]
        
        return cmd_args, shell_cmd_type
    
    def _execute_command_sync(self, cmd_args: List[str], working_dir: str, 
                            timeout: int, env: Dict[str, str]) -> Dict[str, Any]:
        """Execute command synchronously with full output capture"""
        try:
            start_time = time.time()
            
            # Execute process
            process = subprocess.Popen(
                cmd_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                cwd=working_dir,
                env=env,
                text=True,
                encoding=self.default_encoding,
                errors='replace',
                shell=False
            )
            
            # Capture output with timeout
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                return_code = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                return_code = -1
                stderr = f"Command timed out after {timeout} seconds\\n" + (stderr or "")
            
            execution_time = time.time() - start_time
            
            return {
                'stdout': stdout or "",
                'stderr': stderr or "",
                'return_code': return_code,
                'execution_time': execution_time,
                'timed_out': return_code == -1,
                'pid': process.pid
            }
            
        except Exception as e:
            return {
                'stdout': "",
                'stderr': f"Execution error: {str(e)}",
                'return_code': -2,
                'execution_time': 0,
                'timed_out': False,
                'pid': None
            }
    
    def _analyze_output(self, result: Dict[str, Any], command: str, shell_type: str) -> Dict[str, Any]:
        """Analyze command output for intelligent insights"""
        analysis = {
            'success': result['return_code'] == 0,
            'has_output': bool(result['stdout'].strip()),
            'has_errors': bool(result['stderr'].strip()),
            'output_lines': len(result['stdout'].splitlines()),
            'error_lines': len(result['stderr'].splitlines()),
            'output_size': len(result['stdout']),
            'command_type': 'unknown'
        }
        
        # Classify command type
        cmd_lower = command.lower().strip()
        if any(cmd_lower.startswith(x) for x in ['dir', 'ls', 'get-childitem']):
            analysis['command_type'] = 'list_directory'
        elif any(cmd_lower.startswith(x) for x in ['cd ', 'set-location', 'pushd', 'popd']):
            analysis['command_type'] = 'change_directory'
        elif any(cmd_lower.startswith(x) for x in ['type', 'cat', 'get-content']):
            analysis['command_type'] = 'read_file'
        elif any(cmd_lower.startswith(x) for x in ['echo', 'write-output', 'write-host']):
            analysis['command_type'] = 'output_text'
        elif any(cmd_lower.startswith(x) for x in ['ps', 'get-process', 'tasklist']):
            analysis['command_type'] = 'list_processes'
        elif any(cmd_lower.startswith(x) for x in ['kill', 'stop-process', 'taskkill']):
            analysis['command_type'] = 'terminate_process'
        elif any(cmd_lower.startswith(x) for x in ['git ']):
            analysis['command_type'] = 'version_control'
        elif any(cmd_lower.startswith(x) for x in ['npm ', 'pip ', 'dotnet ', 'cargo ']):
            analysis['command_type'] = 'package_manager'
        elif any(cmd_lower.startswith(x) for x in ['python ', 'node ', 'java ', 'dotnet run']):
            analysis['command_type'] = 'script_execution'
        
        # Detect common patterns
        if 'error' in result['stderr'].lower() or 'exception' in result['stderr'].lower():
            analysis['contains_errors'] = True
        
        if 'warning' in result['stderr'].lower():
            analysis['contains_warnings'] = True
        
        if result['return_code'] == 0 and result['stdout']:
            analysis['likely_successful'] = True
        
        return analysis
    
    def _add_to_history(self, command: str, shell_type: str, result: Dict[str, Any], 
                       analysis: Dict[str, Any], working_dir: str):
        """Add command to execution history"""
        entry = {
            'timestamp': time.time(),
            'command': command,
            'shell_type': shell_type,
            'working_dir': working_dir,
            'return_code': result['return_code'],
            'execution_time': result['execution_time'],
            'output_size': len(result['stdout']),
            'error_size': len(result['stderr']),
            'analysis': analysis,
            'success': analysis['success']
        }
        
        self.command_history.append(entry)
        
        # Keep history manageable
        if len(self.command_history) > self.max_history:
            self.command_history = self.command_history[-self.max_history:]
    
    # ===== CORE SHELL OPERATIONS =====
    
    def bb7_execute_command(self, arguments: Dict[str, Any]) -> str:
        """⚡ Execute any command in any available shell with full system access and intelligent analysis"""
        command = arguments.get('command', '')
        shell_type = arguments.get('shell', self.default_shell)
        working_dir = arguments.get('working_dir', '.')
        timeout = arguments.get('timeout', self.default_timeout)
        environment = arguments.get('environment', {})
        capture_output = arguments.get('capture_output', True)
        show_analysis = arguments.get('show_analysis', True)
        
        if not command:
            return "❌ Provide command to execute. Example: {'command': 'Get-Process', 'shell': 'pwsh'}"
        
        try:
            # Validate and prepare
            shell_info = self._get_shell_info(shell_type)
            if not shell_info:
                available = ', '.join(self.available_shells.keys())
                return f"❌ Shell '{shell_type}' not available. Available: {available}"
            
            # Prepare working directory
            work_dir = Path(working_dir).expanduser().resolve()
            if not work_dir.exists():
                return f"❌ Working directory not found: {working_dir}"
            
            # Prepare environment
            env = os.environ.copy()
            env.update(environment)
            env.update(self.persistent_vars)
            
            # Prepare command
            cmd_args, shell_cmd_type = self._prepare_command(command, shell_type)
            
            # Validate timeout
            timeout = min(max(timeout, 1), self.max_timeout)
            
            # Execute command
            result = self._execute_command_sync(cmd_args, str(work_dir), timeout, env)
            
            # Analyze result
            analysis = self._analyze_output(result, command, shell_type)
            
            # Add to history
            self._add_to_history(command, shell_type, result, analysis, str(work_dir))
            
            # Build response
            response = []
            response.append(f"⚡ **Command Executed**: `{command}`\\n")
            response.append(f"**Shell**: {shell_info['name']} ({shell_type})")
            response.append(f"**Directory**: `{work_dir}`")
            response.append(f"**Exit Code**: {result['return_code']}")
            response.append(f"**Execution Time**: {result['execution_time']:.2f}s")
            
            if result['timed_out']:
                response.append(f"⏰ **Timed Out**: Command exceeded {timeout}s limit")
            
            if show_analysis and analysis:
                response.append(f"**Type**: {analysis['command_type']}")
                if analysis.get('likely_successful'):
                    response.append("✅ **Status**: Likely successful")
                elif analysis.get('contains_errors'):
                    response.append("❌ **Status**: Contains errors")
                elif analysis.get('contains_warnings'):
                    response.append("⚠️ **Status**: Contains warnings")
            
            response.append("\\n")
            
            # Output
            if result['stdout']:
                response.append("📤 **Output**:")
                response.append("```")
                response.append(result['stdout'])
                response.append("```")
            
            # Errors
            if result['stderr']:
                response.append("📥 **Error Output**:")
                response.append("```")
                response.append(result['stderr'])
                response.append("```")
            
            if not result['stdout'] and not result['stderr']:
                response.append("✨ **No output produced**")
            
            return "\\n".join(response)
            
        except Exception as e:
            return f"❌ Command execution failed: {str(e)}"
    
    def bb7_list_shells(self, arguments: Dict[str, Any]) -> str:
        """🔧 List all available shell environments with capabilities and versions"""
        show_details = arguments.get('show_details', True)
        test_shells = arguments.get('test_shells', False)
        
        try:
            if not self.available_shells:
                return "❌ No shell environments detected"
            
            response = []
            response.append(f"🔧 **Available Shell Environments** ({len(self.available_shells)} total)\\n")
            response.append(f"**Default Shell**: {self.default_shell} ({self.available_shells[self.default_shell]['name']})\\n")
            
            for shell_type, shell_info in self.available_shells.items():
                is_default = shell_type == self.default_shell
                status_icon = "⭐" if is_default else "🔧"
                
                response.append(f"{status_icon} **{shell_type}** - {shell_info['name']}")
                response.append(f"   📍 Path: `{shell_info['executable']}`")
                response.append(f"   🏷️ Type: {shell_info['type']}")
                
                if show_details:
                    capabilities = shell_info.get('capabilities', [])
                    if capabilities:
                        response.append(f"   ⚡ Capabilities: {', '.join(capabilities)}")
                    
                    # Test shell version if requested
                    if test_shells and 'version_cmd' in shell_info:
                        try:
                            version_result = subprocess.run(
                                shell_info['version_cmd'],
                                capture_output=True,
                                text=True,
                                timeout=10
                            )
                            if version_result.returncode == 0:
                                version_info = version_result.stdout.strip().split('\\n')[0]
                                response.append(f"   📊 Version: {version_info}")
                            else:
                                response.append(f"   ❌ Version check failed")
                        except Exception:
                            response.append(f"   ⚠️ Version check timeout")
                
                response.append("")
            
            # Usage examples
            response.append("💡 **Usage Examples**:")
            response.append("  • PowerShell: `bb7_execute_command({'command': 'Get-Process', 'shell': 'pwsh'})`")
            response.append("  • Command Prompt: `bb7_execute_command({'command': 'dir', 'shell': 'cmd'})`")
            response.append("  • Git Bash: `bb7_execute_command({'command': 'ls -la', 'shell': 'bash'})`")
            if any('wsl' in shell for shell in self.available_shells):
                response.append("  • WSL: `bb7_execute_command({'command': 'uname -a', 'shell': 'wsl_ubuntu'})`")
            
            return "\\n".join(response)
            
        except Exception as e:
            return f"❌ Error listing shells: {str(e)}"
    
    def bb7_set_default_shell(self, arguments: Dict[str, Any]) -> str:
        """🎯 Set the default shell environment for command execution"""
        shell_type = arguments.get('shell', '')
        
        if not shell_type:
            return f"❌ Specify shell type. Available: {', '.join(self.available_shells.keys())}"
        
        if shell_type not in self.available_shells:
            return f"❌ Shell '{shell_type}' not available. Available: {', '.join(self.available_shells.keys())}"
        
        self.default_shell = shell_type
        shell_info = self.available_shells[shell_type]
        
        return f"🎯 **Default shell set**: {shell_info['name']} ({shell_type})"
    
    def bb7_command_history(self, arguments: Dict[str, Any]) -> str:
        """📊 View command execution history with analysis and patterns"""
        limit = arguments.get('limit', 20)
        shell_filter = arguments.get('shell_filter', '')
        show_analysis = arguments.get('show_analysis', True)
        
        try:
            if not self.command_history:
                return "📊 **No command history available yet**"
            
            # Filter history
            history = self.command_history
            if shell_filter:
                history = [cmd for cmd in history if cmd['shell_type'] == shell_filter]
            
            # Get recent commands
            recent_commands = history[-limit:]
            
            response = []
            response.append(f"📊 **Command History** (last {len(recent_commands)} commands)\\n")
            
            if show_analysis:
                # Statistics
                total_commands = len(self.command_history)
                successful_commands = sum(1 for cmd in self.command_history if cmd['success'])
                avg_execution_time = sum(cmd['execution_time'] for cmd in self.command_history) / total_commands
                
                response.append(f"**Statistics**:")
                response.append(f"  • Total Commands: {total_commands:,}")
                response.append(f"  • Success Rate: {(successful_commands/total_commands)*100:.1f}%")
                response.append(f"  • Average Execution Time: {avg_execution_time:.2f}s")
                
                # Shell usage
                shell_usage = {}
                for cmd in self.command_history:
                    shell_usage[cmd['shell_type']] = shell_usage.get(cmd['shell_type'], 0) + 1
                
                if shell_usage:
                    most_used_shell = max(shell_usage, key=lambda x: shell_usage[x])
                    most_used_count = shell_usage[most_used_shell]
                    response.append(f"  • Most Used Shell: {most_used_shell} ({most_used_count} commands)")
                else:
                    response.append(f"  • Most Used Shell: None")
                response.append("\n")
            
            # Recent commands
            response.append("**Recent Commands**:")
            for cmd in reversed(recent_commands):
                timestamp = datetime.fromtimestamp(cmd['timestamp']).strftime("%H:%M:%S")
                status = "✅" if cmd['success'] else "❌"
                shell_type = cmd['shell_type']
                command = cmd['command'][:60] + "..." if len(cmd['command']) > 60 else cmd['command']
                exec_time = cmd['execution_time']
                
                response.append(f"  {timestamp} {status} [{shell_type}] `{command}` ({exec_time:.2f}s)")
            
            return "\\n".join(response)
            
        except Exception as e:
            return f"❌ Error getting command history: {str(e)}"
    
    def bb7_get_system_info(self, arguments: Dict[str, Any]) -> str:
        """💻 Get comprehensive system information and environment details"""
        include_processes = arguments.get('include_processes', False)
        include_network = arguments.get('include_network', False)
        
        try:
            response = []
            response.append("💻 **System Information**\\n")
            
            # Basic system info
            response.append(f"**Operating System**: {os.name}")
            response.append(f"**Platform**: {sys.platform}")
            response.append(f"**Architecture**: {os.environ.get('PROCESSOR_ARCHITECTURE', 'Unknown')}")
            response.append(f"**Computer Name**: {os.environ.get('COMPUTERNAME', 'Unknown')}")
            response.append(f"**Username**: {os.environ.get('USERNAME', 'Unknown')}")
            response.append(f"**User Domain**: {os.environ.get('USERDOMAIN', 'Unknown')}")
            response.append(f"**Current Directory**: `{os.getcwd()}`")
            response.append("")
            
            # Python environment
            response.append(f"**Python Version**: {sys.version}")
            response.append(f"**Python Executable**: `{sys.executable}`")
            response.append("")
            
            # Environment variables (key ones)
            important_vars = ['PATH', 'PYTHONPATH', 'TEMP', 'TMP', 'USERPROFILE', 'PROGRAMFILES', 'WINDIR']
            response.append("**Key Environment Variables**:")
            for var in important_vars:
                value = os.environ.get(var, 'Not set')
                if len(value) > 100:
                    value = value[:100] + "..."
                response.append(f"  • {var}: `{value}`")
            response.append("")
            
            # Available shells
            response.append(f"**Available Shells**: {len(self.available_shells)}")
            for shell_type, shell_info in list(self.available_shells.items())[:5]:
                response.append(f"  • {shell_type}: {shell_info['name']}")
            response.append("")
            
            # System resources using psutil if available
            try:
                cpu_count = psutil.cpu_count()
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                response.append(f"**System Resources**:")
                response.append(f"  • CPU Cores: {cpu_count}")
                response.append(f"  • Total Memory: {memory.total / (1024**3):.1f} GB")
                response.append(f"  • Available Memory: {memory.available / (1024**3):.1f} GB")
                response.append(f"  • Memory Usage: {memory.percent:.1f}%")
                response.append(f"  • Disk Total: {disk.total / (1024**3):.1f} GB")
                response.append(f"  • Disk Free: {disk.free / (1024**3):.1f} GB")
                response.append("")
                
                if include_processes:
                    processes = psutil.process_iter(['pid', 'name', 'memory_percent'])
                    top_processes = sorted(processes, key=lambda p: p.info['memory_percent'], reverse=True)[:10]
                    
                    response.append("**Top Processes by Memory**:")
                    for proc in top_processes:
                        response.append(f"  • {proc.info['name']} (PID: {proc.info['pid']}) - {proc.info['memory_percent']:.1f}%")
                    response.append("")
                
                if include_network:
                    network = psutil.net_if_addrs()
                    response.append(f"**Network Interfaces**: {len(network)}")
                    for interface, addresses in list(network.items())[:3]:
                        response.append(f"  • {interface}: {len(addresses)} addresses")
                
            except Exception:
                response.append("**System Resources**: psutil not available for detailed info")
            
            return "\\n".join(response)
            
        except Exception as e:
            return f"❌ Error getting system info: {str(e)}"
    
    def bb7_manage_environment(self, arguments: Dict[str, Any]) -> str:
        """🌍 Manage environment variables and shell environments"""
        action = arguments.get('action', 'list')  # list, set, unset, export
        variable = arguments.get('variable', '')
        value = arguments.get('value', '')
        persistent = arguments.get('persistent', False)
        
        try:
            if action == 'list':
                # List current environment
                response = []
                response.append("🌍 **Environment Variables**\\n")
                
                # Current environment
                env_vars = dict(os.environ)
                if persistent and self.persistent_vars:
                    env_vars.update(self.persistent_vars)
                
                # Filter and sort
                important_vars = [k for k in env_vars.keys() if any(keyword in k.upper() for keyword in 
                                ['PATH', 'PYTHON', 'HOME', 'USER', 'TEMP', 'PROGRAM', 'SYSTEM', 'WIN'])]
                other_vars = [k for k in env_vars.keys() if k not in important_vars]
                
                response.append("**Important Variables**:")
                for var in sorted(important_vars)[:20]:
                    value_str = env_vars[var]
                    if len(value_str) > 80:
                        value_str = value_str[:80] + "..."
                    response.append(f"  • **{var}**: `{value_str}`")
                
                if persistent and self.persistent_vars:
                    response.append("\\n**Persistent Variables**:")
                    for var, val in self.persistent_vars.items():
                        response.append(f"  • **{var}**: `{val}`")
                
                response.append(f"\\n**Total Variables**: {len(env_vars)}")
                return "\\n".join(response)
            
            elif action == 'set':
                if not variable:
                    return "❌ Specify variable name to set"
                
                # Set environment variable
                os.environ[variable] = value
                
                if persistent:
                    self.persistent_vars[variable] = value
                
                return f"✅ **Environment variable set**: {variable} = `{value}`" + (
                    " (persistent)" if persistent else " (session only)")
            
            elif action == 'unset':
                if not variable:
                    return "❌ Specify variable name to unset"
                
                removed = []
                if variable in os.environ:
                    del os.environ[variable]
                    removed.append("current environment")
                
                if variable in self.persistent_vars:
                    del self.persistent_vars[variable]
                    removed.append("persistent storage")
                
                if removed:
                    return f"✅ **Environment variable removed**: {variable} (from {', '.join(removed)})"
                else:
                    return f"❌ Variable '{variable}' not found"
            
            elif action == 'export':
                if not variable:
                    return "❌ Specify variable name to export"
                
                # Export to all shell environments
                export_commands = []
                for shell_type, shell_info in self.available_shells.items():
                    shell_cmd_type = shell_info['type']
                    
                    if shell_cmd_type == 'powershell':
                        export_commands.append(f"PowerShell: $env:{variable} = '{value}'")
                    elif shell_cmd_type == 'cmd':
                        export_commands.append(f"CMD: set {variable}={value}")
                    elif shell_cmd_type in ['bash', 'wsl']:
                        export_commands.append(f"Bash/WSL: export {variable}='{value}'")
                
                # Set in current environment
                os.environ[variable] = value
                if persistent:
                    self.persistent_vars[variable] = value
                
                response = []
                response.append(f"✅ **Variable exported**: {variable} = `{value}`\\n")
                response.append("**Shell Commands**:")
                for cmd in export_commands:
                    response.append(f"  • {cmd}")
                
                return "\\n".join(response)
            
            else:
                return f"❌ Unknown action '{action}'. Available: list, set, unset, export"
                
        except Exception as e:
            return f"❌ Error managing environment: {str(e)}"
    
    def bb7_shell_scripting(self, arguments: Dict[str, Any]) -> str:
        """📜 Execute multi-line scripts in any shell environment"""
        script = arguments.get('script', '')
        shell_type = arguments.get('shell', self.default_shell)
        save_script = arguments.get('save_script', False)
        script_name = arguments.get('script_name', '')
        working_dir = arguments.get('working_dir', '.')
        
        if not script:
            return "❌ Provide script content to execute"
        
        try:
            # Get shell info
            shell_info = self._get_shell_info(shell_type)
            if not shell_info:
                return f"❌ Shell '{shell_type}' not available"
            
            # Create temporary script file
            script_dir = Path(tempfile.gettempdir()) / "claude_scripts"
            script_dir.mkdir(exist_ok=True)
            
            # Determine script extension based on shell type
            shell_cmd_type = shell_info['type']
            extensions = {
                'powershell': '.ps1',
                'cmd': '.bat',
                'bash': '.sh',
                'python': '.py',
                'wsl': '.sh'
            }
            
            ext = extensions.get(shell_cmd_type, '.txt')
            
            if script_name:
                script_file = script_dir / f"{script_name}{ext}"
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                script_file = script_dir / f"script_{timestamp}{ext}"
            
            # Write script
            with open(script_file, 'w', encoding='utf-8') as f:
                f.write(script)
            
            # Make executable for bash scripts
            if shell_cmd_type in ['bash', 'wsl']:
                os.chmod(script_file, 0o755)
            
            # Execute script
            if shell_cmd_type == 'powershell':
                command = f"& '{script_file}'"
            elif shell_cmd_type == 'cmd':
                command = f'"{script_file}"'
            elif shell_cmd_type in ['bash', 'wsl']:
                command = f"bash '{script_file}'"
            elif shell_cmd_type == 'python':
                command = f"exec(open('{script_file}').read())"
            else:
                command = str(script_file)
            
            # Execute the script
            result = self.bb7_execute_command({
                'command': command,
                'shell': shell_type,
                'working_dir': working_dir
            })
            
            # Clean up temporary file unless saving
            if not save_script:
                try:
                    script_file.unlink()
                except Exception:
                    pass
            
            # Build response
            response = []
            response.append(f"📜 **Script Executed**: {shell_info['name']}\\n")
            response.append(f"**Script Length**: {len(script)} characters")
            response.append(f"**Script File**: `{script_file}`")
            if save_script:
                response.append("💾 **Script saved for reuse**")
            response.append("\\n")
            response.append("**Execution Result**:")
            response.append(result)
            
            return "\\n".join(response)
            
        except Exception as e:
            return f"❌ Error executing script: {str(e)}"
    
    # ===== MCP TOOL REGISTRATION =====
    
    def get_tools(self) -> Dict[str, Any]:
        """Return all unleashed shell tools"""
        return {
            'bb7_execute_command': {
                'description': '⚡ Execute any command in any available Windows shell with full system access. Supports PowerShell, CMD, Git Bash, WSL, and Windows Terminal. No restrictions - maximum capability for true collaborative intelligence.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'command': {
                            'type': 'string',
                            'description': 'Command to execute'
                        },
                        'shell': {
                            'type': 'string',
                            'description': 'Shell environment to use',
                            'default': self.default_shell
                        },
                        'working_dir': {
                            'type': 'string',
                            'description': 'Working directory for command execution',
                            'default': '.'
                        },
                        'timeout': {
                            'type': 'integer',
                            'description': 'Command timeout in seconds',
                            'default': self.default_timeout,
                            'minimum': 1,
                            'maximum': self.max_timeout
                        },
                        'environment': {
                            'type': 'object',
                            'description': 'Additional environment variables',
                            'additionalProperties': {'type': 'string'}
                        },
                        'capture_output': {
                            'type': 'boolean',
                            'description': 'Capture command output',
                            'default': True
                        },
                        'show_analysis': {
                            'type': 'boolean',
                            'description': 'Include command analysis',
                            'default': True
                        }
                    },
                    'required': ['command']
                },
                'function': self.bb7_execute_command
            },
            'bb7_list_shells': {
                'description': '🔧 List all available shell environments with capabilities, versions, and system integration. Shows PowerShell, CMD, Git Bash, WSL distributions, and Windows Terminal.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'show_details': {
                            'type': 'boolean',
                            'description': 'Show detailed information about each shell',
                            'default': True
                        },
                        'test_shells': {
                            'type': 'boolean',
                            'description': 'Test shell availability and get versions',
                            'default': False
                        }
                    }
                },
                'function': self.bb7_list_shells
            },
            'bb7_set_default_shell': {
                'description': '🎯 Set the default shell environment for command execution. Choose between PowerShell, CMD, Git Bash, WSL, or any available shell.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'shell': {
                            'type': 'string',
                            'description': 'Shell type to set as default'
                        }
                    },
                    'required': ['shell']
                },
                'function': self.bb7_set_default_shell
            },
            'bb7_command_history': {
                'description': '📊 View command execution history with analysis, success rates, and usage patterns. Track all shell activity for intelligent workflow optimization.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'limit': {
                            'type': 'integer',
                            'description': 'Number of recent commands to show',
                            'default': 20
                        },
                        'shell_filter': {
                            'type': 'string',
                            'description': 'Filter by specific shell type'
                        },
                        'show_analysis': {
                            'type': 'boolean',
                            'description': 'Include detailed analysis and statistics',
                            'default': True
                        }
                    }
                },
                'function': self.bb7_command_history
            },
            'bb7_get_system_info': {
                'description': '💻 Get comprehensive system information including OS details, hardware specs, environment variables, and available shells. Complete system analysis.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'include_processes': {
                            'type': 'boolean',
                            'description': 'Include running processes information',
                            'default': False
                        },
                        'include_network': {
                            'type': 'boolean',
                            'description': 'Include network interfaces information',
                            'default': False
                        }
                    }
                },
                'function': self.bb7_get_system_info
            },
            'bb7_manage_environment': {
                'description': '🌍 Manage environment variables across all shell environments. Set, unset, export, and persist variables with cross-shell compatibility.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'action': {
                            'type': 'string',
                            'description': 'Action to perform',
                            'enum': ['list', 'set', 'unset', 'export'],
                            'default': 'list'
                        },
                        'variable': {
                            'type': 'string',
                            'description': 'Environment variable name'
                        },
                        'value': {
                            'type': 'string',
                            'description': 'Environment variable value'
                        },
                        'persistent': {
                            'type': 'boolean',
                            'description': 'Make variable persistent across sessions',
                            'default': False
                        }
                    }
                },
                'function': self.bb7_manage_environment
            },
            'bb7_shell_scripting': {
                'description': '📜 Execute multi-line scripts in any shell environment. Supports PowerShell scripts, batch files, bash scripts, Python scripts, and WSL scripts.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'script': {
                            'type': 'string',
                            'description': 'Multi-line script content to execute'
                        },
                        'shell': {
                            'type': 'string',
                            'description': 'Shell environment for script execution',
                            'default': self.default_shell
                        },
                        'save_script': {
                            'type': 'boolean',
                            'description': 'Save script file for reuse',
                            'default': False
                        },
                        'script_name': {
                            'type': 'string',
                            'description': 'Name for saved script file'
                        },
                        'working_dir': {
                            'type': 'string',
                            'description': 'Working directory for script execution',
                            'default': '.'
                        }
                    },
                    'required': ['script']
                },
                'function': self.bb7_shell_scripting
            }
        }


# Create global instance
unleashed_shell_tool = UnleashedShellTool()

# Export for MCP server
def get_tools():
    return unleashed_shell_tool.get_tools()


# Testing
if __name__ == "__main__":
    def test_unleashed_shell():
        tool = UnleashedShellTool()
        
        print("=== Testing Unleashed Shell Tool ===")
        
        # Test shell discovery
        result = tool.bb7_list_shells({'show_details': True})
        print(f"Available shells:\\n{result}\\n")
        
        # Test system info
        result = tool.bb7_get_system_info({})
        print(f"System info:\\n{result}\\n")
        
        # Test simple command
        result = tool.bb7_execute_command({'command': 'echo Hello World', 'shell': 'cmd'})
        print(f"Command result:\\n{result}\\n")
    
    test_unleashed_shell()