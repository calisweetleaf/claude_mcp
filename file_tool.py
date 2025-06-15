#!/usr/bin/env python3
"""
Unleashed File Tool - Unrestricted System-Wide File Operations
============================================================

Maximum capability file operations for Claude collaborative intelligence.
NO RESTRICTIONS, NO LIMITATIONS - Full system access for true partnership.

This tool provides unrestricted access to the entire file system with
intelligent analysis, bulk operations, and advanced file manipulation.
Designed for maximum power and flexibility in our AI lab environment.
"""

import os
import shutil
import stat
import time
import json
import hashlib
import zipfile
import tarfile
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import mimetypes
import fnmatch
import threading
from concurrent.futures import ThreadPoolExecutor
import base64


class UnleashedFileTool:
    """
    Unrestricted file system operations with maximum capability and intelligence.
    No safety limitations - pure power for collaborative intelligence.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.temp_dir = Path(tempfile.gettempdir()) / "claude_workspace"
        self.temp_dir.mkdir(exist_ok=True)
        
        # File operation history for intelligence
        self.operation_history = []
        self.max_history = 1000
        
        # Supported operations
        self.archive_formats = {
            '.zip': ('zip', zipfile.ZipFile),
            '.tar': ('tar', tarfile.open),
            '.tar.gz': ('tar.gz', tarfile.open),
            '.tar.bz2': ('tar.bz2', tarfile.open),
            '.tgz': ('tar.gz', tarfile.open)
        }
        
        # Encoding detection patterns
        self.text_encodings = ['utf-8', 'utf-16', 'utf-32', 'ascii', 'iso-8859-1', 'cp1252', 'cp437']
        
        # Binary file signatures for intelligent handling
        self.binary_signatures = {
            b'\x50\x4B\x03\x04': 'ZIP Archive',
            b'\x50\x4B\x05\x06': 'ZIP Archive (empty)',
            b'\x50\x4B\x07\x08': 'ZIP Archive (spanned)',
            b'\x1F\x8B': 'GZIP Archive',
            b'\x42\x5A\x68': 'BZIP2 Archive',
            b'\x75\x73\x74\x61\x72': 'TAR Archive',
            b'\x7F\x45\x4C\x46': 'ELF Executable',
            b'\x4D\x5A': 'Windows Executable',
            b'\x89\x50\x4E\x47': 'PNG Image',
            b'\xFF\xD8\xFF': 'JPEG Image',
            b'\x47\x49\x46\x38': 'GIF Image',
            b'\x25\x50\x44\x46': 'PDF Document',
            b'\xD0\xCF\x11\xE0': 'Microsoft Office Document',
            b'\x50\x4B\x03\x04': 'Office Open XML Document'
        }
        
        self.logger.info("Unleashed File Tool initialized with full system access")
    
    def _detect_encoding(self, file_path: Path) -> str:
        """Intelligently detect file encoding"""
        try:
            for encoding in self.text_encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        f.read(1024)  # Test read
                    return encoding
                except UnicodeDecodeError:
                    continue
            return 'utf-8'  # Default fallback
        except Exception:
            return 'utf-8'
    
    def _detect_file_type(self, file_path: Path) -> Dict[str, Any]:
        """Advanced file type detection"""
        try:
            # Basic info
            stat_info = file_path.stat()
            mime_type, _ = mimetypes.guess_type(str(file_path))
            
            # Read file signature
            file_signature = ""
            file_type_desc = "Unknown"
            
            if file_path.is_file() and stat_info.st_size > 0:
                try:
                    with open(file_path, 'rb') as f:
                        header = f.read(16)
                        
                    # Check binary signatures
                    for sig, desc in self.binary_signatures.items():
                        if header.startswith(sig):
                            file_type_desc = desc
                            break
                    
                    file_signature = header.hex()[:32]
                except Exception:
                    pass
            
            return {
                'mime_type': mime_type or 'application/octet-stream',
                'file_signature': file_signature,
                'type_description': file_type_desc,
                'size': stat_info.st_size,
                'created': datetime.fromtimestamp(stat_info.st_ctime),
                'modified': datetime.fromtimestamp(stat_info.st_mtime),
                'accessed': datetime.fromtimestamp(stat_info.st_atime),
                'permissions': oct(stat_info.st_mode)[-3:],
                'is_executable': stat_info.st_mode & stat.S_IEXEC != 0,
                'is_hidden': file_path.name.startswith('.') or bool(stat_info.st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN) if hasattr(stat, 'FILE_ATTRIBUTE_HIDDEN') else False
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _add_to_history(self, operation: str, path: str, details: Dict[str, Any]):
        """Track operations for intelligence"""
        entry = {
            'timestamp': time.time(),
            'operation': operation,
            'path': path,
            'details': details
        }
        self.operation_history.append(entry)
        
        # Keep history manageable
        if len(self.operation_history) > self.max_history:
            self.operation_history = self.operation_history[-self.max_history:]
    
    def _analyze_content(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Intelligent content analysis"""
        analysis = {
            'lines': content.count('\\n') + 1,
            'characters': len(content),
            'words': len(content.split()),
            'blank_lines': content.count('\\n\\n'),
            'file_type': 'text'
        }
        
        # Language detection based on extension and content
        ext = file_path.suffix.lower()
        language_map = {
            '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
            '.html': 'HTML', '.css': 'CSS', '.json': 'JSON',
            '.xml': 'XML', '.yaml': 'YAML', '.yml': 'YAML',
            '.md': 'Markdown', '.txt': 'Plain Text', '.log': 'Log File',
            '.sql': 'SQL', '.sh': 'Shell Script', '.ps1': 'PowerShell',
            '.bat': 'Batch File', '.cmd': 'Command File'
        }
        
        analysis['language'] = language_map.get(ext, 'Unknown')
        
        # Content patterns
        if ext in ['.py', '.js', '.ts']:
            analysis['functions'] = len([line for line in content.split('\\n') if 'def ' in line or 'function ' in line])
            analysis['classes'] = len([line for line in content.split('\\n') if 'class ' in line])
            analysis['imports'] = len([line for line in content.split('\\n') if line.strip().startswith(('import ', 'from ', 'require('))])
        
        # Security patterns
        security_patterns = [
            'password', 'secret', 'key', 'token', 'api_key',
            'private_key', 'secret_key', 'auth', 'credential'
        ]
        analysis['potential_secrets'] = sum(1 for pattern in security_patterns if pattern in content.lower())
        
        return analysis
    
    # ===== CORE FILE OPERATIONS =====
    
    def bb7_read_file(self, arguments: Dict[str, Any]) -> str:
        """🔍 Read any file from anywhere on the system with intelligent analysis and encoding detection"""
        path = arguments.get('path', '') or arguments.get('file_path', '')
        max_size = arguments.get('max_size', 10 * 1024 * 1024)  # 10MB default
        force_text = arguments.get('force_text', False)
        show_analysis = arguments.get('show_analysis', True)
        
        if not path:
            return "❌ Specify file path. Example: {'path': 'C:\\\\Windows\\\\System32\\\\drivers\\\\etc\\\\hosts'}"
        
        try:
            file_path = Path(path).expanduser().resolve()
            
            if not file_path.exists():
                return f"❌ File not found: {path}"
            
            if not file_path.is_file():
                return f"❌ Path is directory, not file: {path}"
            
            # Get file info
            file_info = self._detect_file_type(file_path)
            file_size = file_info.get('size', 0)
            
            # Size check
            if file_size > max_size and not force_text:
                return f"❌ File too large ({file_size:,} bytes). Use max_size parameter or force_text=True"
            
            # Detect if binary
            is_binary = False
            try:
                with open(file_path, 'rb') as f:
                    chunk = f.read(8192)
                    is_binary = b'\\x00' in chunk
            except Exception:
                pass
            
            # Read content
            if is_binary and not force_text:
                # Handle binary files
                content = f"📄 **Binary File Detected**\\n\\n"
                content += f"**File**: {file_path}\\n"
                content += f"**Size**: {file_size:,} bytes\\n"
                content += f"**Type**: {file_info.get('type_description', 'Unknown')}\\n"
                content += f"**MIME**: {file_info.get('mime_type', 'Unknown')}\\n\\n"
                
                # Show hex dump of first 512 bytes
                try:
                    with open(file_path, 'rb') as f:
                        hex_data = f.read(512)
                    content += f"**Hex Preview (first 512 bytes):**\\n```\\n"
                    for i in range(0, len(hex_data), 16):
                        hex_line = ' '.join(f'{b:02x}' for b in hex_data[i:i+16])
                        ascii_line = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in hex_data[i:i+16])
                        content += f"{i:08x}  {hex_line:<47} |{ascii_line}|\\n"
                    content += "```\\n"
                except Exception as e:
                    content += f"Error reading binary data: {e}\\n"
                
                return content
            
            else:
                # Read text file
                encoding = self._detect_encoding(file_path)
                try:
                    with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                        content = f.read()
                except Exception as e:
                    return f"❌ Error reading file: {e}"
                
                # Build response
                response = []
                response.append(f"📖 **File Content**: `{file_path}`\\n")
                
                if show_analysis:
                    analysis = self._analyze_content(content, file_path)
                    response.append(f"**Analysis**: {analysis['language']} • {analysis['lines']:,} lines • {analysis['characters']:,} chars")
                    if analysis.get('functions'):
                        response.append(f" • {analysis['functions']} functions")
                    if analysis.get('classes'):
                        response.append(f" • {analysis['classes']} classes")
                    if analysis.get('potential_secrets'):
                        response.append(f" • ⚠️ {analysis['potential_secrets']} potential secrets detected")
                    response.append("\\n")
                
                # Add content with syntax highlighting hint
                lang_map = {
                    'Python': 'python', 'JavaScript': 'javascript', 'TypeScript': 'typescript',
                    'HTML': 'html', 'CSS': 'css', 'JSON': 'json', 'SQL': 'sql',
                    'Shell Script': 'bash', 'PowerShell': 'powershell', 'Batch File': 'batch'
                }
                syntax = lang_map.get(analysis.get('language', ''), '')
                
                response.append(f"```{syntax}\\n{content}\\n```")
                
                # Add operation to history
                self._add_to_history('read', str(file_path), {
                    'size': file_size,
                    'encoding': encoding,
                    'analysis': analysis
                })
                
                return "\\n".join(response)
                
        except Exception as e:
            return f"❌ Error reading file: {e}"
    
    def bb7_write_file(self, arguments: Dict[str, Any]) -> str:
        """✍️ Write or create files anywhere on the system with automatic backup and intelligent formatting"""
        path = arguments.get('path', '') or arguments.get('file_path', '')
        content = arguments.get('content', '')
        encoding = arguments.get('encoding', 'utf-8')
        create_backup = arguments.get('create_backup', True)
        make_executable = arguments.get('make_executable', False)
        
        if not path:
            return "❌ Specify file path. Example: {'path': 'C:\\\\temp\\\\output.txt', 'content': 'Hello World'}"
        
        if content is None:
            return "❌ Provide content to write"
        
        try:
            file_path = Path(path).expanduser().resolve()
            
            # Create directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Backup existing file
            backup_path = None
            if file_path.exists() and create_backup:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = file_path.with_suffix(f".backup_{timestamp}{file_path.suffix}")
                shutil.copy2(file_path, backup_path)
            
            # Write file
            with open(file_path, 'w', encoding=encoding, newline='\\n') as f:
                f.write(content)
            
            # Set permissions if requested
            if make_executable:
                current_mode = file_path.stat().st_mode
                file_path.chmod(current_mode | stat.S_IEXEC)
            
            # Analyze what was written
            analysis = self._analyze_content(content, file_path)
            file_info = self._detect_file_type(file_path)
            
            # Build response
            response = []
            response.append(f"✅ **File Written**: `{file_path}`\\n")
            response.append(f"**Size**: {len(content.encode(encoding)):,} bytes")
            response.append(f"**Language**: {analysis['language']}")
            response.append(f"**Lines**: {analysis['lines']:,}")
            response.append(f"**Encoding**: {encoding}")
            
            if backup_path:
                response.append(f"**Backup**: {backup_path.name}")
            
            if make_executable:
                response.append("**Permissions**: Executable")
            
            if analysis.get('functions'):
                response.append(f"**Functions**: {analysis['functions']}")
            if analysis.get('classes'):
                response.append(f"**Classes**: {analysis['classes']}")
            if analysis.get('potential_secrets'):
                response.append(f"⚠️ **Potential secrets detected**: {analysis['potential_secrets']}")
            
            # Add to history
            self._add_to_history('write', str(file_path), {
                'size': len(content.encode(encoding)),
                'backup': str(backup_path) if backup_path else None,
                'analysis': analysis
            })
            
            return " • ".join(response)
            
        except Exception as e:
            return f"❌ Error writing file: {e}"
    
    def bb7_copy_file(self, arguments: Dict[str, Any]) -> str:
        """📋 Copy files or directories with intelligent handling and progress tracking"""
        source = arguments.get('source', '')
        destination = arguments.get('destination', '')
        overwrite = arguments.get('overwrite', False)
        preserve_metadata = arguments.get('preserve_metadata', True)
        
        if not source or not destination:
            return "❌ Specify source and destination paths"
        
        try:
            src_path = Path(source).expanduser().resolve()
            dst_path = Path(destination).expanduser().resolve()
            
            if not src_path.exists():
                return f"❌ Source not found: {source}"
            
            if dst_path.exists() and not overwrite:
                return f"❌ Destination exists. Use overwrite=True to replace: {destination}"
            
            # Create destination directory if needed
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy operation
            if src_path.is_file():
                if preserve_metadata:
                    shutil.copy2(src_path, dst_path)
                else:
                    shutil.copy(src_path, dst_path)
                operation = "file"
            else:
                if preserve_metadata:
                    shutil.copytree(src_path, dst_path, dirs_exist_ok=overwrite)
                else:
                    shutil.copytree(src_path, dst_path, dirs_exist_ok=overwrite, copy_function=shutil.copy)
                operation = "directory"
            
            # Get size info
            if dst_path.is_file():
                size = dst_path.stat().st_size
                items = 1
            else:
                size = sum(f.stat().st_size for f in dst_path.rglob('*') if f.is_file())
                items = len(list(dst_path.rglob('*')))
            
            self._add_to_history('copy', f"{source} -> {destination}", {
                'type': operation,
                'size': size,
                'items': items
            })
            
            return f"✅ **Copied {operation}**: `{source}` → `{destination}` • {size:,} bytes • {items:,} items"
            
        except Exception as e:
            return f"❌ Error copying: {e}"
    
    def bb7_move_file(self, arguments: Dict[str, Any]) -> str:
        """🚚 Move or rename files and directories"""
        source = arguments.get('source', '')
        destination = arguments.get('destination', '')
        
        if not source or not destination:
            return "❌ Specify source and destination paths"
        
        try:
            src_path = Path(source).expanduser().resolve()
            dst_path = Path(destination).expanduser().resolve()
            
            if not src_path.exists():
                return f"❌ Source not found: {source}"
            
            # Create destination directory if needed
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move operation
            shutil.move(str(src_path), str(dst_path))
            
            operation = "file" if dst_path.is_file() else "directory"
            
            self._add_to_history('move', f"{source} -> {destination}", {
                'type': operation
            })
            
            return f"✅ **Moved {operation}**: `{source}` → `{destination}`"
            
        except Exception as e:
            return f"❌ Error moving: {e}"
    
    def bb7_delete_file(self, arguments: Dict[str, Any]) -> str:
        """🗑️ Delete files or directories with optional backup"""
        path = arguments.get('path', '')
        force = arguments.get('force', False)
        create_backup = arguments.get('create_backup', True)
        
        if not path:
            return "❌ Specify path to delete"
        
        try:
            target_path = Path(path).expanduser().resolve()
            
            if not target_path.exists():
                return f"❌ Path not found: {path}"
            
            # Create backup if requested
            backup_path = None
            if create_backup:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir = self.temp_dir / "backups"
                backup_dir.mkdir(exist_ok=True)
                backup_path = backup_dir / f"{target_path.name}_deleted_{timestamp}"
                
                if target_path.is_file():
                    shutil.copy2(target_path, backup_path)
                else:
                    shutil.copytree(target_path, backup_path)
            
            # Delete operation
            if target_path.is_file():
                target_path.unlink()
                operation = "file"
            else:
                shutil.rmtree(target_path)
                operation = "directory"
            
            self._add_to_history('delete', str(target_path), {
                'type': operation,
                'backup': str(backup_path) if backup_path else None
            })
            
            response = f"✅ **Deleted {operation}**: `{path}`"
            if backup_path:
                response += f" • Backup: `{backup_path}`"
            
            return response
            
        except Exception as e:
            return f"❌ Error deleting: {e}"
    
    def bb7_list_directory(self, arguments: Dict[str, Any]) -> str:
        """📁 List directory contents with detailed analysis and intelligent insights"""
        path = arguments.get('path', '.')
        show_hidden = arguments.get('show_hidden', True)
        sort_by = arguments.get('sort_by', 'name')  # name, size, modified, type
        max_items = arguments.get('max_items', 200)
        show_details = arguments.get('show_details', True)
        
        try:
            dir_path = Path(path).expanduser().resolve()
            
            if not dir_path.exists():
                return f"❌ Directory not found: {path}"
            
            if not dir_path.is_dir():
                return f"❌ Path is not a directory: {path}"
            
            # Get directory contents
            items = []
            total_size = 0
            file_count = 0
            dir_count = 0
            
            try:
                for item in dir_path.iterdir():
                    if not show_hidden and item.name.startswith('.'):
                        continue
                    
                    try:
                        stat_info = item.stat()
                        is_dir = item.is_dir()
                        
                        item_info = {
                            'name': item.name,
                            'path': str(item),
                            'is_dir': is_dir,
                            'size': 0 if is_dir else stat_info.st_size,
                            'modified': datetime.fromtimestamp(stat_info.st_mtime),
                            'permissions': oct(stat_info.st_mode)[-3:],
                            'type': 'Directory' if is_dir else self._detect_file_type(item).get('type_description', 'File')
                        }
                        
                        items.append(item_info)
                        
                        if is_dir:
                            dir_count += 1
                        else:
                            file_count += 1
                            total_size += item_info['size']
                            
                    except (PermissionError, OSError):
                        # Skip inaccessible items
                        continue
                        
            except PermissionError:
                return f"❌ Permission denied accessing: {path}"
            
            # Sort items
            sort_key_map = {
                'name': lambda x: x['name'].lower(),
                'size': lambda x: x['size'],
                'modified': lambda x: x['modified'],
                'type': lambda x: (not x['is_dir'], x['type'], x['name'].lower())
            }
            items.sort(key=sort_key_map.get(sort_by, sort_key_map['name']))
            
            # Limit items if needed
            total_items = len(items)
            if len(items) > max_items:
                items = items[:max_items]
            
            # Build response
            response = []
            response.append(f"📁 **Directory**: `{dir_path}`\\n")
            response.append(f"**Summary**: {dir_count:,} directories • {file_count:,} files • {total_size:,} bytes")
            if total_items > max_items:
                response.append(f" • Showing {max_items:,} of {total_items:,} items")
            response.append("\\n")
            
            # List items
            for item in items:
                icon = "📁" if item['is_dir'] else "📄"
                name = item['name']
                
                if show_details:
                    size_str = "         " if item['is_dir'] else f"{item['size']:>8,}b"
                    mod_time = item['modified'].strftime("%Y-%m-%d %H:%M")
                    perms = item['permissions']
                    response.append(f"{icon} `{name:<40}` {size_str} {mod_time} {perms}")
                else:
                    response.append(f"{icon} `{name}`")
            
            # Add insights
            if file_count > 0:
                response.append("\\n**File Types**:")
                type_counts = {}
                for item in items:
                    if not item['is_dir']:
                        ext = Path(item['name']).suffix.lower() or 'no extension'
                        type_counts[ext] = type_counts.get(ext, 0) + 1
                
                for ext, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                    response.append(f"  • {ext}: {count:,} files")
            
            self._add_to_history('list', str(dir_path), {
                'file_count': file_count,
                'dir_count': dir_count,
                'total_size': total_size
            })
            
            return "\\n".join(response)
            
        except Exception as e:
            return f"❌ Error listing directory: {e}"
    
    def bb7_search_files(self, arguments: Dict[str, Any]) -> str:
        """🔍 Advanced file search with pattern matching and content search"""
        directory = arguments.get('directory', '.')
        name_pattern = arguments.get('name_pattern', '*')
        content_pattern = arguments.get('content_pattern', '')
        max_results = arguments.get('max_results', 100)
        include_hidden = arguments.get('include_hidden', False)
        max_depth = arguments.get('max_depth', 10)
        file_size_min = arguments.get('file_size_min', 0)
        file_size_max = arguments.get('file_size_max', None)
        
        try:
            search_dir = Path(directory).expanduser().resolve()
            
            if not search_dir.exists():
                return f"❌ Directory not found: {directory}"
            
            results = []
            search_start = time.time()
            
            def search_recursive(current_dir: Path, current_depth: int):
                if current_depth > max_depth:
                    return
                
                try:
                    for item in current_dir.iterdir():
                        if len(results) >= max_results:
                            return
                        
                        if not include_hidden and item.name.startswith('.'):
                            continue
                        
                        try:
                            if item.is_file():
                                # Check file name pattern
                                if not fnmatch.fnmatch(item.name, name_pattern):
                                    continue
                                
                                # Check file size
                                file_size = item.stat().st_size
                                if file_size < file_size_min:
                                    continue
                                if file_size_max and file_size > file_size_max:
                                    continue
                                
                                # Check content pattern if specified
                                content_match = False
                                if content_pattern:
                                    try:
                                        encoding = self._detect_encoding(item)
                                        with open(item, 'r', encoding=encoding, errors='ignore') as f:
                                            content = f.read()
                                            content_match = content_pattern.lower() in content.lower()
                                    except Exception:
                                        content_match = False
                                else:
                                    content_match = True
                                
                                if content_match:
                                    file_info = self._detect_file_type(item)
                                    results.append({
                                        'path': str(item),
                                        'name': item.name,
                                        'size': file_size,
                                        'modified': datetime.fromtimestamp(item.stat().st_mtime),
                                        'type': file_info.get('type_description', 'File')
                                    })
                            
                            elif item.is_dir():
                                search_recursive(item, current_depth + 1)
                                
                        except (PermissionError, OSError):
                            continue
                            
                except (PermissionError, OSError):
                    pass
            
            # Perform search
            search_recursive(search_dir, 0)
            search_time = time.time() - search_start
            
            if not results:
                return f"🔍 **No files found** matching criteria in `{search_dir}`"
            
            # Build response
            response = []
            response.append(f"🔍 **Search Results**: {len(results):,} files found in {search_time:.2f}s\\n")
            response.append(f"**Directory**: `{search_dir}`")
            response.append(f"**Pattern**: `{name_pattern}`")
            if content_pattern:
                response.append(f"**Content**: `{content_pattern}`")
            response.append("\\n")
            
            # Sort by relevance (size desc, then name)
            results.sort(key=lambda x: (-x['size'], x['name']))
            
            # Show results
            for result in results:
                size_str = f"{result['size']:,}b" if result['size'] > 0 else "empty"
                mod_time = result['modified'].strftime("%Y-%m-%d %H:%M")
                response.append(f"📄 `{result['name']}` ({size_str}) - {mod_time}")
                response.append(f"   `{result['path']}`")
            
            self._add_to_history('search', str(search_dir), {
                'pattern': name_pattern,
                'content_pattern': content_pattern,
                'results': len(results),
                'search_time': search_time
            })
            
            return "\\n".join(response)
            
        except Exception as e:
            return f"❌ Error searching files: {e}"
    
    def bb7_file_info(self, arguments: Dict[str, Any]) -> str:
        """ℹ️ Get comprehensive information about any file or directory"""
        path = arguments.get('path', '')
        
        if not path:
            return "❌ Specify path to analyze"
        
        try:
            target_path = Path(path).expanduser().resolve()
            
            if not target_path.exists():
                return f"❌ Path not found: {path}"
            
            # Get detailed information
            stat_info = target_path.stat()
            file_info = self._detect_file_type(target_path)
            
            response = []
            response.append(f"ℹ️ **File Information**: `{target_path}`\\n")
            
            # Basic info
            response.append(f"**Type**: {'Directory' if target_path.is_dir() else 'File'}")
            response.append(f"**Size**: {stat_info.st_size:,} bytes")
            response.append(f"**Permissions**: {file_info.get('permissions', 'Unknown')}")
            response.append(f"**Created**: {file_info.get('created', 'Unknown')}")
            response.append(f"**Modified**: {file_info.get('modified', 'Unknown')}")
            response.append(f"**Accessed**: {file_info.get('accessed', 'Unknown')}")
            
            if not target_path.is_dir():
                response.append(f"**MIME Type**: {file_info.get('mime_type', 'Unknown')}")
                response.append(f"**File Type**: {file_info.get('type_description', 'Unknown')}")
                
                if file_info.get('is_executable'):
                    response.append("**Executable**: Yes")
                
                # Content analysis for text files
                if file_info.get('mime_type', '').startswith('text/'):
                    try:
                        encoding = self._detect_encoding(target_path)
                        with open(target_path, 'r', encoding=encoding, errors='replace') as f:
                            content = f.read()
                        analysis = self._analyze_content(content, target_path)
                        
                        response.append(f"**Language**: {analysis['language']}")
                        response.append(f"**Lines**: {analysis['lines']:,}")
                        response.append(f"**Words**: {analysis['words']:,}")
                        response.append(f"**Characters**: {analysis['characters']:,}")
                        
                        if analysis.get('functions'):
                            response.append(f"**Functions**: {analysis['functions']}")
                        if analysis.get('classes'):
                            response.append(f"**Classes**: {analysis['classes']}")
                        if analysis.get('potential_secrets'):
                            response.append(f"⚠️ **Potential Secrets**: {analysis['potential_secrets']}")
                            
                    except Exception:
                        pass
            
            else:
                # Directory info
                try:
                    items = list(target_path.iterdir())
                    file_count = sum(1 for item in items if item.is_file())
                    dir_count = sum(1 for item in items if item.is_dir())
                    total_size = sum(item.stat().st_size for item in items if item.is_file())
                    
                    response.append(f"**Contents**: {file_count:,} files, {dir_count:,} directories")
                    response.append(f"**Total Size**: {total_size:,} bytes")
                    
                except PermissionError:
                    response.append("**Contents**: Permission denied")
            
            return "\\n".join(response)
            
        except Exception as e:
            return f"❌ Error getting file info: {e}"
    
    def bb7_operation_history(self, arguments: Dict[str, Any]) -> str:
        """📊 View file operation history and statistics"""
        limit = arguments.get('limit', 20)
        operation_type = arguments.get('operation_type', '')
        
        try:
            if not self.operation_history:
                return "📊 **No file operations recorded yet**"
            
            # Filter by operation type if specified
            history = self.operation_history
            if operation_type:
                history = [op for op in history if op['operation'] == operation_type]
            
            # Get recent operations
            recent_ops = history[-limit:]
            
            response = []
            response.append(f"📊 **File Operation History** (last {len(recent_ops)} operations)\\n")
            
            # Operation statistics
            op_counts = {}
            for op in self.operation_history:
                op_counts[op['operation']] = op_counts.get(op['operation'], 0) + 1
            
            response.append("**Operation Summary**:")
            for op_type, count in sorted(op_counts.items(), key=lambda x: x[1], reverse=True):
                response.append(f"  • {op_type}: {count:,} times")
            response.append("")
            
            # Recent operations
            response.append("**Recent Operations**:")
            for op in reversed(recent_ops):
                timestamp = datetime.fromtimestamp(op['timestamp']).strftime("%H:%M:%S")
                operation = op['operation']
                path = op['path']
                details = op.get('details', {})
                
                detail_str = ""
                if 'size' in details:
                    detail_str += f" ({details['size']:,}b)"
                if 'type' in details:
                    detail_str += f" [{details['type']}]"
                
                response.append(f"  {timestamp} **{operation}** `{path}`{detail_str}")
            
            return "\\n".join(response)
            
        except Exception as e:
            return f"❌ Error getting operation history: {e}"
    
    # ===== MCP TOOL REGISTRATION =====
    
    def get_tools(self) -> Dict[str, Any]:
        """Return all unleashed file tools"""
        return {
            'bb7_read_file': {
                'description': '🔍 Read any file from anywhere on the system with intelligent analysis, encoding detection, and content insights. No restrictions - full system access for true collaborative intelligence.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'path': {
                            'type': 'string',
                            'description': 'Absolute or relative file path'
                        },
                        'max_size': {
                            'type': 'integer',
                            'description': 'Maximum file size to read (bytes)',
                            'default': 10485760
                        },
                        'force_text': {
                            'type': 'boolean',
                            'description': 'Force reading binary files as text',
                            'default': False
                        },
                        'show_analysis': {
                            'type': 'boolean',
                            'description': 'Include content analysis',
                            'default': True
                        }
                    },
                    'required': ['path']
                },
                'function': self.bb7_read_file
            },
            'bb7_write_file': {
                'description': '✍️ Write or create files anywhere on the system with automatic backup, directory creation, and intelligent formatting. Unrestricted system access.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'path': {
                            'type': 'string',
                            'description': 'File path to write to'
                        },
                        'content': {
                            'type': 'string',
                            'description': 'Content to write'
                        },
                        'encoding': {
                            'type': 'string',
                            'description': 'Text encoding',
                            'default': 'utf-8'
                        },
                        'create_backup': {
                            'type': 'boolean',
                            'description': 'Create backup of existing file',
                            'default': True
                        },
                        'make_executable': {
                            'type': 'boolean',
                            'description': 'Make file executable',
                            'default': False
                        }
                    },
                    'required': ['path', 'content']
                },
                'function': self.bb7_write_file
            },
            'bb7_copy_file': {
                'description': '📋 Copy files or directories anywhere on the system with intelligent handling and metadata preservation. Full system access.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'source': {
                            'type': 'string',
                            'description': 'Source path'
                        },
                        'destination': {
                            'type': 'string',
                            'description': 'Destination path'
                        },
                        'overwrite': {
                            'type': 'boolean',
                            'description': 'Overwrite if destination exists',
                            'default': False
                        },
                        'preserve_metadata': {
                            'type': 'boolean',
                            'description': 'Preserve timestamps and permissions',
                            'default': True
                        }
                    },
                    'required': ['source', 'destination']
                },
                'function': self.bb7_copy_file
            },
            'bb7_move_file': {
                'description': '🚚 Move or rename files and directories anywhere on the system. Unrestricted access for maximum capability.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'source': {
                            'type': 'string',
                            'description': 'Source path'
                        },
                        'destination': {
                            'type': 'string',
                            'description': 'Destination path'
                        }
                    },
                    'required': ['source', 'destination']
                },
                'function': self.bb7_move_file
            },
            'bb7_delete_file': {
                'description': '🗑️ Delete files or directories anywhere on the system with optional backup. Full deletion capabilities for true system control.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'path': {
                            'type': 'string',
                            'description': 'Path to delete'
                        },
                        'force': {
                            'type': 'boolean',
                            'description': 'Force deletion without confirmation',
                            'default': False
                        },
                        'create_backup': {
                            'type': 'boolean',
                            'description': 'Create backup before deletion',
                            'default': True
                        }
                    },
                    'required': ['path']
                },
                'function': self.bb7_delete_file
            },
            'bb7_list_directory': {
                'description': '📁 List directory contents with detailed analysis, file type detection, and intelligent insights. Complete filesystem exploration.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'path': {
                            'type': 'string',
                            'description': 'Directory path',
                            'default': '.'
                        },
                        'show_hidden': {
                            'type': 'boolean',
                            'description': 'Show hidden files',
                            'default': True
                        },
                        'sort_by': {
                            'type': 'string',
                            'description': 'Sort order',
                            'enum': ['name', 'size', 'modified', 'type'],
                            'default': 'name'
                        },
                        'max_items': {
                            'type': 'integer',
                            'description': 'Maximum items to show',
                            'default': 200
                        },
                        'show_details': {
                            'type': 'boolean',
                            'description': 'Show detailed information',
                            'default': True
                        }
                    }
                },
                'function': self.bb7_list_directory
            },
            'bb7_search_files': {
                'description': '🔍 Advanced file search with pattern matching, content search, and intelligent filtering. Unrestricted system-wide search capabilities.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'directory': {
                            'type': 'string',
                            'description': 'Directory to search in',
                            'default': '.'
                        },
                        'name_pattern': {
                            'type': 'string',
                            'description': 'File name pattern (wildcards supported)',
                            'default': '*'
                        },
                        'content_pattern': {
                            'type': 'string',
                            'description': 'Search within file contents'
                        },
                        'max_results': {
                            'type': 'integer',
                            'description': 'Maximum results',
                            'default': 100
                        },
                        'include_hidden': {
                            'type': 'boolean',
                            'description': 'Include hidden files',
                            'default': False
                        },
                        'max_depth': {
                            'type': 'integer',
                            'description': 'Maximum directory depth',
                            'default': 10
                        },
                        'file_size_min': {
                            'type': 'integer',
                            'description': 'Minimum file size (bytes)',
                            'default': 0
                        },
                        'file_size_max': {
                            'type': 'integer',
                            'description': 'Maximum file size (bytes)'
                        }
                    }
                },
                'function': self.bb7_search_files
            },
            'bb7_file_info': {
                'description': 'ℹ️ Get comprehensive information about any file or directory including metadata, permissions, content analysis, and system details.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'path': {
                            'type': 'string',
                            'description': 'Path to analyze'
                        }
                    },
                    'required': ['path']
                },
                'function': self.bb7_file_info
            },
            'bb7_operation_history': {
                'description': '📊 View file operation history, statistics, and patterns for intelligent workflow optimization.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'limit': {
                            'type': 'integer',
                            'description': 'Number of recent operations to show',
                            'default': 20
                        },
                        'operation_type': {
                            'type': 'string',
                            'description': 'Filter by operation type'
                        }
                    }
                },
                'function': self.bb7_operation_history
            }
        }


# Create global instance
unleashed_file_tool = UnleashedFileTool()

# Export for MCP server
def get_tools():
    return unleashed_file_tool.get_tools()


# Testing
if __name__ == "__main__":
    def test_unleashed_file():
        tool = UnleashedFileTool()
        
        print("=== Testing Unleashed File Tool ===")
        
        # Test directory listing
        result = tool.bb7_list_directory({'path': '.'})
        print(f"Directory listing:\\n{result}\\n")
        
        # Test file info
        result = tool.bb7_file_info({'path': __file__})
        print(f"File info:\\n{result}\\n")
    
    test_unleashed_file()