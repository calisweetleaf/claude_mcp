#!/usr/bin/env python3
"""
Fixed Project Context Tool - Claude Optimized
Simplified, reliable project analysis without complex dependencies or async issues
"""

import json
import logging
import os
import re
import subprocess
import time
import fnmatch # Import fnmatch
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple


class ProjectContextTool:
    """Simplified, reliable project context analysis for Claude MCP"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Language configurations
        self.language_configs = {
            'python': {
                'extensions': ['.py', '.pyw', '.pyx', '.pyi'],
                'dependency_files': ['requirements.txt', 'Pipfile', 'pyproject.toml', 'setup.py', 'environment.yml'],
                'config_files': ['.pylintrc', 'setup.cfg', 'pyproject.toml', 'tox.ini', '.flake8', 'mypy.ini', 'Dockerfile', 'docker-compose.yml'],
                'test_patterns': ['test_*.py', '*_test.py', 'tests/', 'test/'],
                'frameworks': {
                    # Added 'from fastapi import FastAPI' as a more specific indicator
                    'fastapi': ['main.py', 'app.py', 'from fastapi import FastAPI'],
                    'django': ['manage.py', 'settings.py', 'wsgi.py', 'from django.'],
                    'flask': ['app.py', 'application.py', 'from flask import Flask'],
                    'pytest': ['pytest.ini', 'conftest.py']
                }
            },
            'javascript': {
                'extensions': ['.js', '.jsx', '.mjs', '.cjs'],
                'dependency_files': ['package.json', 'package-lock.json', 'yarn.lock'],
                'config_files': ['.eslintrc', '.eslintrc.js', '.eslintrc.json', '.babelrc', 'webpack.config.js', '.prettierrc', 'babel.config.json', 'postcss.config.js', 'tailwind.config.js'],
                'test_patterns': ['*.test.js', '*.spec.js', '__tests__/', 'test/'],
                'frameworks': {
                    'react': ['react', 'src/App.js', 'public/index.html', 'from "react"'],
                    'vue': ['vue', 'src/main.js', 'vue.config.js', 'from "vue"'],
                    'angular': ['angular.json', 'src/main.ts', '@angular/core'], # main.ts is more TS but angular.json is key
                    'express': ['express', 'app.js', 'server.js', 'require("express")'],
                    'nextjs': ['next.config.js', 'pages/', '"next"', 'from "next"'], # Renamed from 'next'
                    'nestjs': ['@nestjs/core', 'nest-cli.json', 'main.ts'] # NestJS often uses TS
                }
            },
            'typescript': {
                'extensions': ['.ts', '.tsx', '.d.ts'],
                'dependency_files': ['package.json', 'package-lock.json', 'yarn.lock'], # Shared with JS
                'config_files': ['tsconfig.json', 'tslint.json', '.eslintrc.js'],
                'test_patterns': ['*.test.ts', '*.spec.ts', '__tests__/'],
                'frameworks': {
                    'angular': ['@angular/core', 'angular.json', 'src/main.ts'],
                    'react': ['@types/react', 'src/App.tsx', 'from "react"'], # For TSX files
                    'vue': ['@types/vue', 'vue.config.ts', 'from "vue"'],  # For TS with Vue
                    'nestjs': ['@nestjs/core', 'nest-cli.json', 'main.ts', 'import { NestFactory }']
                }
            },
            'java': {
                'extensions': ['.java', '.kt', '.scala'],
                'dependency_files': ['pom.xml', 'build.gradle', 'build.gradle.kts'],
                'config_files': ['application.properties', 'application.yml', 'logback.xml'],
                'test_patterns': ['*Test.java', '*Tests.java', 'src/test/'],
                'frameworks': {
                    'spring': ['@SpringBootApplication', 'src/main/java'],
                    'maven': ['pom.xml', 'src/main/java'],
                    'gradle': ['build.gradle', 'src/main/java']
                }
            },
            'go': {
                'extensions': ['.go'],
                'dependency_files': ['go.mod', 'go.sum', 'Gopkg.toml'],
                'config_files': ['.golangci.yml', 'Makefile'],
                'test_patterns': ['*_test.go', 'test/'],
                'frameworks': {
                    'gin': ['gin-gonic', 'main.go'],
                    'echo': ['echo', 'main.go'],
                    'fiber': ['fiber', 'main.go']
                }
            },
            # General project files (not language specific usually)
            'general_project_files': {
                'version_control': ['.git', '.hg', '.svn', '.gitignore', '.gitattributes', '.gitmodules'],
                'containerization': ['Dockerfile', 'docker-compose.yml', '.dockerignore', 'docker-compose.yaml', 'Containerfile'],
                'cicd': ['.gitlab-ci.yml', 'Jenkinsfile', '.travis.yml', 'circle.yml', 'azure-pipelines.yml', 'cloudbuild.yaml', '.github/workflows/'],
                'iac': ['terraform.tfvars', '*.tf', 'serverless.yml', 'Vagrantfile', 'ansible/'],
                'build_tools_general': ['Makefile', 'build.xml', 'Rakefile', 'CMakeLists.txt', 'WORKSPACE'],
                'documentation': ['README.md', 'CONTRIBUTING.md', 'CHANGELOG.md', 'LICENSE', 'docs/']
            }
        }
        
        # Security patterns for basic scanning
        self.security_patterns = {
            'python': [
                (r'eval\s*\(', 'Dangerous eval() usage'),
                (r'exec\s*\(', 'Dangerous exec() usage'),
                (r'os\.system\s*\(', 'OS command execution'),
                (r'subprocess\.call\([^)]*shell=True', 'Shell injection risk'),
                (r'pickle\.loads?\s*\(', 'Unsafe pickle deserialization'),
                (r'yaml\.load\s*\(', 'Unsafe YAML loading')
            ],
            'javascript': [
                (r'eval\s*\(', 'Dangerous eval() usage'),
                (r'innerHTML\s*=', 'XSS vulnerability risk'),
                (r'document\.write\s*\(', 'XSS vulnerability risk'),
                (r'setTimeout\s*\(["\']', 'Code injection risk'),
                (r'new Function\s*\(', 'Code injection risk')
            ]
        }
        
        self.logger.info("Project Context Tool initialized successfully")
    
    def _scan_directory(self, path: Path, max_depth: int = 4, include_hidden: bool = False) -> Dict[str, Any]:
        """Scan directory structure and collect file information"""
        file_info = {
            'total_files': 0,
            'directories': 0,
            'files_by_extension': defaultdict(int),
            'files_by_language': defaultdict(list),
            'config_files': [],
            'dependency_files': [],
            'test_files': [],
            'large_files': [],
            'structure': [],
            'total_size_bytes': 0 # Initialize total_size_bytes
        }
        
        # Expanded list of common excluded directories
        default_excluded_dirs = [
            'node_modules', '__pycache__', 'venv', '.git', '.svn', 'CVS',
            '.hg', 'build', 'dist', 'target', 'out', 'bin', 'obj',
            '.idea', '.vscode', '.project', '.settings', '*.pyc', '*.pyo',
            '*.class', '*.o', '*.obj', '*.so', '*.dylib', '*.dll',
            '.DS_Store', 'Thumbs.db', '*.log', 'logs/',
            '.next', '.cache', '*.egg-info' # Added from requirements
        ]

        # Common important dotfiles to include even if include_hidden is False
        common_dotfiles_to_include = [
            '.gitignore', '.gitattributes', '.gitmodules',
            '.env', '.env.example', '.env.local',
            '.prettierrc', '.prettierignore',
            '.eslintrc', '.eslintignore',
            '.babelrc', '.npmrc', '.yarnrc', '.pylintrc', 'pyproject.toml',
            'tox.ini', '.flake8', 'mypy.ini', 'tsconfig.json', 'tslint.json'
        ]

        try:
            for root, dirs, files in os.walk(path):
                current_depth = len(Path(root).relative_to(path).parts)
                if current_depth >= max_depth:
                    dirs.clear()
                    continue
                
                # Skip excluded and hidden directories
                if not include_hidden:
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in default_excluded_dirs]
                else: # If include_hidden is true, still skip some very common large/cache dirs
                    dirs[:] = [d for d in dirs if d not in ['node_modules', '__pycache__', '.cache', '.next', 'build', 'dist', 'target']]

                file_info['directories'] += len(dirs)
                
                for file in files:
                    if not include_hidden and file.startswith('.') and file not in common_dotfiles_to_include:
                        continue
                    
                    # Skip files if their parent directory is an excluded one (applies to top-level files in excluded dirs)
                    # This is a simple check; more robust would be to check full path against excluded patterns.
                    parent_dir_name = Path(root).name
                    if not include_hidden and parent_dir_name in default_excluded_dirs:
                        if file not in common_dotfiles_to_include: # unless it's an important dotfile itself
                            continue

                    file_path = Path(root) / file
                    relative_path = str(file_path.relative_to(path))
                    
                    file_info['total_files'] += 1
                    
                    # Get file extension
                    ext = file_path.suffix.lower()
                    if ext:
                        file_info['files_by_extension'][ext] += 1
                    
                    # Categorize by language
                    for language, config in self.language_configs.items():
                        if language == 'general_project_files': continue
                        if 'extensions' in config and ext in config['extensions']:
                            file_info['files_by_language'][language].append(relative_path)
                            break
                    
                    # Check for special file types
                    # More robust way to sum these lists from configs
                    all_dep_files = []
                    all_cfg_files = []
                    for lang_config in self.language_configs.values():
                        all_dep_files.extend(lang_config.get('dependency_files', []))
                        all_cfg_files.extend(lang_config.get('config_files', []))

                    if file in all_dep_files:
                        file_info['dependency_files'].append(relative_path)
                    
                    if file in all_cfg_files: # This includes Dockerfile etc. from python config for now
                        file_info['config_files'].append(relative_path)

                    # Also add general project files like Dockerfile, Makefile directly to config_files if found at root or common locations
                    if 'general_project_files' in self.language_configs:
                        for file_type_list in self.language_configs['general_project_files'].values():
                            if file in file_type_list and relative_path not in file_info['config_files']:
                                file_info['config_files'].append(relative_path)
                                break # Added to config_files once

                    # Check for test files
                    is_test_file = False
                    for lang_name, lang_config in self.language_configs.items():
                        if is_test_file: break
                        for pattern in lang_config.get('test_patterns', []):
                            if pattern.endswith('/'): # Directory-based pattern
                                if pattern.rstrip('/') in relative_path.split(os.sep):
                                    file_info['test_files'].append(relative_path)
                                    is_test_file = True
                                    break
                            elif '*' in pattern or '?' in pattern: # Glob pattern
                                if fnmatch.fnmatch(file, pattern):
                                    file_info['test_files'].append(relative_path)
                                    is_test_file = True
                                    break
                            else: # Exact match
                                if file == pattern:
                                    file_info['test_files'].append(relative_path)
                                    is_test_file = True
                                    break
                    
                    # Check file size & update total size
                    try:
                        size = file_path.stat().st_size
                        file_info['total_size_bytes'] += size
                        if size > 1024 * 1024:  # Files larger than 1MB
                            file_info['large_files'].append({
                                'path': relative_path,
                                'size_mb': round(size / (1024 * 1024), 2)
                            })
                    except (OSError, PermissionError) as e_stat:
                        self.logger.warning(f"Could not read size for file {file_path}: {e_stat}")
                        pass # Continue if a file's size cannot be read
        
        except Exception as e:
            self.logger.error(f"Error scanning directory: {e}")
        
        return file_info
    
    def _detect_frameworks(self, project_root: Path, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Detect frameworks, build tools, deployment configs, and other technologies."""
        detected_items = {
            'frameworks': [], # List of dicts: {'name': str, 'language': str, 'evidence': list, 'confidence': float}
            'build_tools': [], # List of strings or dicts
            'deployment_configs': [], # List of strings (e.g., Dockerfile, serverless.yml)
            'other_technologies': [] # List of strings
        }
        
        # Helper to manage framework detection and confidence
        framework_evidence_map = defaultdict(lambda: {'language': None, 'evidence': set(), 'confidence': 0.0})

        try:
            # 1. Check dependency files
            for dep_file_name in file_info['dependency_files']:
                dep_path = project_root / dep_file_name
                if not dep_path.exists():
                    continue
                
                try:
                    content = dep_path.read_text(encoding='utf-8', errors='ignore').lower() # Lowercase for case-insensitive match
                    
                    for lang, config in self.language_configs.items():
                        if lang == 'general_project_files': continue # Skip general section here

                        if dep_file_name in config.get('dependency_files', []):
                            for fw_name, fw_indicators in config.get('frameworks', {}).items():
                                for indicator in fw_indicators:
                                    # More specific check for dependency content
                                    if f'"{indicator.lower()}"' in content or f"'{indicator.lower()}'" in content or \
                                       indicator.lower() in content: # General check
                                        framework_evidence_map[fw_name]['language'] = lang
                                        framework_evidence_map[fw_name]['evidence'].add(f"{indicator} in {dep_file_name}")
                                        framework_evidence_map[fw_name]['confidence'] = min(1.0, framework_evidence_map[fw_name]['confidence'] + 0.6)
                except Exception as e_dep:
                    self.logger.warning(f"Could not parse dependency file {dep_path}: {e_dep}")
                    continue
            
            # 2. Check file structure and config files for framework/tool indicators
            # Create a combined list of all relevant file paths for searching
            all_project_files_relative = set(file_info['config_files'])
            for lang_files in file_info['files_by_language'].values():
                all_project_files_relative.update(lang_files)
            
            # Check language-specific frameworks by file presence/content snippets
            for lang, config in self.language_configs.items():
                if lang == 'general_project_files': continue
                for fw_name, fw_indicators in config.get('frameworks', {}).items():
                    for indicator in fw_indicators:
                        # Check if indicator is a file/path pattern or a content snippet
                        is_file_pattern = any(c in indicator for c in ['/', '.']) # Heuristic: if it has / or . it's likely a file/path

                        found_by_file = False
                        if is_file_pattern:
                            for proj_file_rel in all_project_files_relative:
                                if indicator.lower() in proj_file_rel.lower() or \
                                   (Path(indicator).name != indicator and indicator.lower() in proj_file_rel.lower()) or \
                                   fnmatch.fnmatch(proj_file_rel, indicator): # Match filename or path part
                                    framework_evidence_map[fw_name]['language'] = lang
                                    framework_evidence_map[fw_name]['evidence'].add(f"File/path match: {proj_file_rel} for indicator {indicator}")
                                    framework_evidence_map[fw_name]['confidence'] = min(1.0, framework_evidence_map[fw_name]['confidence'] + 0.3)
                                    found_by_file = True
                                    break

                        # If not found by file pattern, or if indicator is not a file pattern, try content search for some key files
                        if not found_by_file and not is_file_pattern and (indicator.startswith("from ") or indicator.startswith("import ") or indicator.startswith("@")):
                             # Limit content search to relevant language files
                            for code_file_rel in file_info['files_by_language'].get(lang, []):
                                code_file_path = project_root / code_file_rel
                                try:
                                    with open(code_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                        # Read first few lines for imports for efficiency
                                        file_head = "".join([next(f) for _ in range(20)]).lower()
                                        if indicator.lower() in file_head:
                                            framework_evidence_map[fw_name]['language'] = lang
                                            framework_evidence_map[fw_name]['evidence'].add(f"Content match: '{indicator}' in {code_file_rel}")
                                            framework_evidence_map[fw_name]['confidence'] = min(1.0, framework_evidence_map[fw_name]['confidence'] + 0.4)
                                            break # Found in this file
                                except (OSError, StopIteration): # StopIteration if file has < 20 lines
                                    pass


            # Convert map to list for frameworks
            for fw_name, data in framework_evidence_map.items():
                if data['confidence'] > 0.1: # Threshold for reporting
                     detected_items['frameworks'].append({
                        'name': fw_name.title(),
                        'language': data['language'].title() if data['language'] else 'Unknown',
                        'evidence': sorted(list(data['evidence'])),
                        'confidence': round(data['confidence'], 2)
                    })

            # 3. Detect general project files (CI/CD, Containerization, etc.)
            if 'general_project_files' in self.language_configs:
                general_config = self.language_configs['general_project_files']
                all_root_files = [f.name for f in project_root.glob('*')] + [f.name for f in project_root.glob('.*')]

                for category, patterns in general_config.items():
                    for pattern in patterns:
                        found = False
                        # Check against all project files (relative paths) collected by _scan_directory
                        for proj_file_rel in all_project_files_relative:
                            if fnmatch.fnmatch(proj_file_rel, pattern) or \
                               (pattern.endswith('/') and pattern.rstrip('/') in proj_file_rel) or \
                               (pattern.startswith('.') and Path(proj_file_rel).name == pattern):
                                if category == 'containerization':
                                    if Path(proj_file_rel).name not in detected_items['deployment_configs']:
                                        detected_items['deployment_configs'].append(Path(proj_file_rel).name)
                                elif category == 'cicd':
                                     if Path(proj_file_rel).name not in detected_items['other_technologies']: # Temp store here
                                        detected_items['other_technologies'].append(f"CI/CD: {Path(proj_file_rel).name}")
                                elif category == 'build_tools_general':
                                    if Path(proj_file_rel).name not in detected_items['build_tools']:
                                     detected_items['build_tools'].append(Path(proj_file_rel).name)
                                elif category == 'iac':
                                    if Path(proj_file_rel).name not in detected_items['deployment_configs']:
                                        detected_items['deployment_configs'].append(f"IaC: {Path(proj_file_rel).name}")
                                found = True
                                break
                        if found: continue

                        # Check against root level files by name (for files like Dockerfile at root)
                        for root_file_name in all_root_files:
                            if fnmatch.fnmatch(root_file_name, pattern) or \
                               (pattern.endswith('/') and root_file_name == pattern.rstrip('/')) or \
                               (pattern.startswith('.') and root_file_name == pattern):
                                if category == 'containerization':
                                    if root_file_name not in detected_items['deployment_configs']:
                                     detected_items['deployment_configs'].append(root_file_name)
                                elif category == 'cicd':
                                    if f"CI/CD: {root_file_name}" not in detected_items['other_technologies']:
                                     detected_items['other_technologies'].append(f"CI/CD: {root_file_name}")
                                elif category == 'build_tools_general':
                                    if root_file_name not in detected_items['build_tools']:
                                     detected_items['build_tools'].append(root_file_name)
                                elif category == 'iac':
                                    if f"IaC: {root_file_name}" not in detected_items['deployment_configs']:
                                     detected_items['deployment_configs'].append(f"IaC: {root_file_name}")
                                break # Found this pattern

        except Exception as e:
            self.logger.error(f"Error detecting frameworks/technologies: {e}", exc_info=True)
        
        # Sort frameworks by confidence
        detected_items['frameworks'] = sorted(detected_items['frameworks'], key=lambda x: x['confidence'], reverse=True)
        return detected_items
    
    def _analyze_code_quality(self, project_root: Path, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Basic code quality analysis"""
        quality_metrics = {
            'total_lines': 0,
            'code_lines': 0,
            'comment_lines': 0,
            'blank_lines': 0,
            'average_file_size': 0,
            'test_coverage_estimate': 0,
            'documentation_files': 0,
            'comment_to_code_ratio': 0.0,
            'code_to_total_ratio': 0.0,
            'todo_fixme_count': 0,
            'long_lines_count': 0,
            'very_large_code_files_count': 0
        }
        
        # Note: More advanced metrics like Cyclomatic Complexity or Halstead metrics
        # would require dedicated parsing libraries (e.g., Radon for Python)
        # and are out of scope for the current regex/stdlib-based approach.

        try:
            total_size = 0
            code_files = 0
            
            # Analyze code files
            for language, files in file_info['files_by_language'].items():
                for file_path in files:
                    full_path = project_root / file_path
                    if not full_path.exists():
                        continue
                    
                    try:
                        content = full_path.read_text(encoding='utf-8', errors='ignore')
                        lines = content.splitlines()
                        
                        file_lines = len(lines)
                        file_code_lines = 0
                        file_comment_lines = 0
                        file_blank_lines = 0
                        
                        for line in lines:
                            line = line.strip()
                            if not line:
                                file_blank_lines += 1
                            elif line.startswith('#') or line.startswith('//') or line.startswith('/*'):
                                file_comment_lines += 1
                            else:
                                file_code_lines += 1
                        
                        quality_metrics['total_lines'] += file_lines
                        quality_metrics['code_lines'] += file_code_lines
                        quality_metrics['comment_lines'] += file_comment_lines
                        quality_metrics['blank_lines'] += file_blank_lines
                        
                        # TODO/FIXME and long lines count
                        for line_content in lines:
                            if "TODO" in line_content.upper() or "FIXME" in line_content.upper():
                                quality_metrics['todo_fixme_count'] += 1
                            if len(line_content) > 120: # Long line threshold
                                quality_metrics['long_lines_count'] += 1

                        if file_code_lines > 1000: # Very large code file
                            quality_metrics['very_large_code_files_count'] += 1

                        total_size += len(content)
                        code_files += 1
                        
                    except Exception as e_file:
                        self.logger.warning(f"Could not analyze file {full_path}: {e_file}")
                        continue
            
            # Calculate averages and ratios
            if code_files > 0:
                quality_metrics['average_file_size'] = round(total_size / code_files if code_files > 0 else 0)

            if quality_metrics['code_lines'] > 0:
                quality_metrics['comment_to_code_ratio'] = round(quality_metrics['comment_lines'] / quality_metrics['code_lines'], 2)
            
            if quality_metrics['total_lines'] > 0:
                quality_metrics['code_to_total_ratio'] = round(quality_metrics['code_lines'] / quality_metrics['total_lines'], 2)

            # Estimate test coverage based on test files vs code files
            # Ensure code_files for language matches test file types (e.g. python code files vs python test files)
            # This is a simplified version. True coverage needs test execution analysis.
            # For now, using total code files as a proxy.
            if code_files > 0 and file_info.get('test_files'):
                test_file_count = len(file_info['test_files'])
                # This is a rough estimate: ratio of test files to primary code files.
                # It doesn't guarantee tests cover all code in those files.
                quality_metrics['test_coverage_estimate'] = min(100.0, (test_file_count / code_files) * 100.0)
            
            # Count documentation files
            doc_extensions = ['.md', '.rst', '.txt', '.doc', '.docx']
            for ext, count in file_info['files_by_extension'].items():
                if ext in doc_extensions:
                    quality_metrics['documentation_files'] += count
        
        except Exception as e:
            self.logger.error(f"Error analyzing code quality: {e}")
        
        return quality_metrics
    
    def _perform_security_scan(self, project_root: Path, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Basic security vulnerability scanning"""
        security_issues = []
        
        try:
            for language, files in file_info['files_by_language'].items():
                if language not in self.security_patterns:
                    continue
                
                patterns = self.security_patterns[language]
                
                for file_path in files[:20]:  # Limit to first 20 files for performance
                    full_path = project_root / file_path
                    if not full_path.exists():
                        continue
                    
                    try:
                        content = full_path.read_text(encoding='utf-8', errors='ignore')
                        
                        for pattern, description in patterns:
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            if matches:
                                security_issues.append({
                                    'file': file_path,
                                    'issue': description,
                                    'pattern': pattern,
                                    'language': language,
                                    'count': len(matches)
                                })
                    except Exception:
                        continue
        
        except Exception as e:
            self.logger.error(f"Error performing security scan: {e}")
        
        return {
            'issues_found': len(security_issues),
            'issues': security_issues,
            'security_score': max(0, 100 - (len(security_issues) * 10))
        }
    
    def _get_project_size_category(self, file_info: Dict[str, Any]) -> str:
        """Categorize project by size"""
        total_files = file_info['total_files']
        
        if total_files < 10:
            return "Small"
        elif total_files < 50:
            return "Medium"
        elif total_files < 200:
            return "Large"
        else:
            return "Enterprise"
    
    def _generate_recommendations(self, project_root: Path, file_info: Dict[str, Any], 
                                frameworks: Dict[str, Any], quality_metrics: Dict[str, Any]) -> List[str]:
        """Generate intelligent recommendations based on analysis"""
        recommendations = []
        
        try:
            # Test coverage recommendations
            if quality_metrics['test_coverage_estimate'] < 50:
                recommendations.append("Consider adding more test files to improve code coverage")
            
            # Documentation recommendations
            if quality_metrics['documentation_files'] == 0:
                recommendations.append("Add a README.md file to document your project")
            
            # Security recommendations
            if not any('security' in f.lower() for f in file_info['config_files']):
                recommendations.append("Consider adding security configuration files (.gitignore, security.md)")
            
            # Dependency management
            primary_languages = [lang for lang, files in file_info['files_by_language'].items() if len(files) > 5]
            for language in primary_languages:
                config = self.language_configs.get(language, {})
                dep_files = config.get('dependency_files', [])
                
                if not any(dep in file_info['dependency_files'] for dep in dep_files):
                    recommendations.append(f"Add dependency management for {language} (e.g., {dep_files[0] if dep_files else 'package file'})")
            
            # Framework-specific recommendations
            for language, fw_list in frameworks.items():
                if language == 'python' and 'django' in fw_list:
                    if 'requirements.txt' not in file_info['dependency_files']:
                        recommendations.append("Add requirements.txt for Django dependency management")
                elif language == 'javascript' and any(fw in fw_list for fw in ['react', 'vue', 'angular']):
                    if 'package.json' not in file_info['dependency_files']:
                        recommendations.append("Add package.json for JavaScript dependency management")
        
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
        
        return recommendations[:10]  # Limit to top 10 recommendations
    
    # ===== MCP TOOL METHODS =====
    
    def bb7_project_scan(self, arguments: Dict[str, Any]) -> str: # RENAMED from bb7_analyze_project_structure
        """🔍 Comprehensive project scan including structure, languages, frameworks, quality, and basic security."""
        max_depth = arguments.get('max_depth', 4)
        include_hidden = arguments.get('include_hidden', False)
        include_security = arguments.get('include_security', True)
        
        try:
            project_root = Path.cwd()
            analysis_start = time.time()
            
            # Scan directory structure
            file_info = self._scan_directory(project_root, max_depth, include_hidden)
            
            # Detect frameworks and technologies
            frameworks = self._detect_frameworks(project_root, file_info)
            
            # Analyze code quality
            quality_metrics = self._analyze_code_quality(project_root, file_info)
            
            # Security scanning
            security_results = {}
            if include_security:
                security_results = self._perform_security_scan(project_root, file_info)
            
            # Generate recommendations
            # Transform the 'frameworks' (which is detected_tech structure)
            # to the dict format expected by _generate_recommendations.
            framework_names_for_reco = defaultdict(list)
            if isinstance(frameworks, dict) and 'frameworks' in frameworks: # frameworks holds the detected_tech structure
                for fw_item in frameworks.get('frameworks', []):
                    lang_key = fw_item.get('language', 'unknown').lower()
                    framework_names_for_reco[lang_key].append(fw_item['name'])

            recommendations = self._generate_recommendations(project_root, file_info, dict(framework_names_for_reco), quality_metrics)
            
            analysis_time = time.time() - analysis_start
            
            # Build comprehensive response
            response = []
            response.append(f"🔍 **Project Structure Analysis**\\n")
            response.append(f"**Project Root**: {project_root}")
            response.append(f"**Analysis Time**: {analysis_time:.2f}s")
            response.append(f"**Project Size**: {self._get_project_size_category(file_info)}\\n")
            
            # File overview
            response.append(f"📁 **File Overview**:")
            response.append(f"  • **Total Files**: {file_info['total_files']}")
            response.append(f"  • **Directories**: {file_info['directories']}")
            response.append(f"  • **Configuration Files**: {len(file_info['config_files'])}")
            response.append(f"  • **Dependency Files**: {len(file_info['dependency_files'])}")
            response.append(f"  • **Test Files**: {len(file_info['test_files'])}\\n")
            
            # Languages detected
            if file_info['files_by_language']:
                response.append(f"💻 **Languages Detected**:")
                for language, files in file_info['files_by_language'].items():
                    response.append(f"  • **{language.title()}**: {len(files)} files")
                response.append("")
            
            # Frameworks and technologies
            if frameworks.get('frameworks'): # Use 'frameworks' variable which holds the detected_tech structure
                response.append(f"🚀 **Frameworks Detected**:")
                for fw in frameworks['frameworks']: # Iterate through list of framework dicts
                    response.append(f"  • **{fw['name']}** ({fw['language']}): Confidence {fw['confidence']:.2f} (Evidence: {', '.join(fw['evidence'][:2])}{'...' if len(fw['evidence']) > 2 else ''})")
            if frameworks.get('build_tools'):
                response.append(f"🛠️ **Build Tools Detected**: {', '.join(frameworks['build_tools'])}")
            if frameworks.get('deployment_configs'):
                response.append(f"🚢 **Deployment Configs**: {', '.join(frameworks['deployment_configs'])}")
            if frameworks.get('other_technologies'):
                 response.append(f"💡 **Other Technologies**: {', '.join(frameworks['other_technologies'])}")
            response.append("")
            
            # Code quality metrics
            response.append(f"📊 **Code Quality Metrics**:")
            response.append(f"  • **Total Lines**: {quality_metrics['total_lines']:,}")
            response.append(f"  • **Code Lines**: {quality_metrics['code_lines']:,}")
            response.append(f"  • **Comment Lines**: {quality_metrics['comment_lines']:,}")
            response.append(f"  • **Average File Size**: {quality_metrics['average_file_size']:,} chars")
            response.append(f"  • **Test Coverage Estimate**: {quality_metrics['test_coverage_estimate']:.1f}%")
            response.append(f"  • **Documentation Files**: {quality_metrics['documentation_files']}\\n")
            
            # Security results
            if security_results:
                response.append(f"🔒 **Security Analysis**:")
                response.append(f"  • **Security Score**: {security_results['security_score']}/100")
                response.append(f"  • **Issues Found**: {security_results['issues_found']}")
                
                if security_results['issues']:
                    response.append(f"  • **Top Issues**:")
                    for issue in security_results['issues'][:3]:
                        response.append(f"    - {issue['issue']} in {issue['file']}")
                response.append("")
            
            # File extensions
            if file_info['files_by_extension']:
                response.append(f"📄 **File Types**:")
                sorted_extensions = sorted(file_info['files_by_extension'].items(), 
                                         key=lambda x: x[1], reverse=True)
                for ext, count in sorted_extensions[:10]:
                    response.append(f"  • **{ext}**: {count} files")
                response.append("")
            
            # Large files
            if file_info['large_files']:
                response.append(f"📋 **Large Files** (>1MB):")
                for large_file in file_info['large_files'][:5]:
                    response.append(f"  • **{large_file['path']}**: {large_file['size_mb']}MB")
                response.append("")
            
            # Recommendations
            if recommendations:
                response.append(f"💡 **Recommendations**:")
                for rec in recommendations:
                    response.append(f"  • {rec}")
            
            return "\\n".join(response)
            
        except Exception as e:
            self.logger.error(f"Error analyzing project structure: {e}", exc_info=True) # Added exc_info
            return f"❌ Error analyzing project structure: {str(e)}"

    def bb7_project_frameworks(self, arguments: Dict[str, Any]) -> str:
        """Detects and lists frameworks, build tools, and other technologies in the project."""
        project_root = Path.cwd()
        max_depth = arguments.get('max_depth', 3) # Slightly shallower for focused tool
        try:
            file_info = self._scan_directory(project_root, max_depth=max_depth)
            detected_items = self._detect_frameworks(project_root, file_info)

            response = ["**Detected Frameworks & Technologies**:\n"]
            if detected_items.get('frameworks'):
                response.append("🚀 **Frameworks**:")
                for fw in detected_items['frameworks']:
                    evidence_str = ", ".join(fw['evidence'][:3]) # Show top 3 evidences
                    if len(fw['evidence']) > 3:
                        evidence_str += "..."
                    response.append(f"  • **{fw['name']}** ({fw['language']})")
                    response.append(f"    Confidence: {fw['confidence']:.2f}")
                    response.append(f"    Evidence: {evidence_str}")
            else:
                response.append("🚀 **Frameworks**: None detected or below confidence threshold.")

            if detected_items.get('build_tools'):
                response.append("\n🛠️ **Build Tools**:")
                response.extend([f"  • {bt}" for bt in detected_items['build_tools']])

            if detected_items.get('deployment_configs'):
                response.append("\n🚢 **Deployment & IaC Configs**:")
                response.extend([f"  • {dc}" for dc in detected_items['deployment_configs']])

            if detected_items.get('other_technologies'):
                response.append("\n💡 **Other Technologies (e.g., CI/CD)**:")
                response.extend([f"  • {ot}" for ot in detected_items['other_technologies']])

            if not any(val for val_list in detected_items.values() for val in val_list): # Check if all lists within detected_items are empty
                response.append("No specific frameworks or major technologies detected with current configuration.")

            return "\n".join(response)
        except Exception as e:
            self.logger.error(f"Error in bb7_project_frameworks: {e}", exc_info=True)
            return f"❌ Error detecting project frameworks: {str(e)}"

    def bb7_project_quality(self, arguments: Dict[str, Any]) -> str:
        """Analyzes code quality metrics, including LoC, comments, TODOs, and security scan results."""
        project_root = Path.cwd()
        max_depth = arguments.get('max_depth', 4)
        include_security = arguments.get('include_security', True)

        try:
            file_info = self._scan_directory(project_root, max_depth=max_depth)
            quality_metrics = self._analyze_code_quality(project_root, file_info)

            response = ["**Project Code Quality Analysis**:\n"]
            response.append(f"📊 **Lines of Code & Ratios**:")
            response.append(f"  • Total Lines: {quality_metrics['total_lines']:,}")
            response.append(f"  • Code Lines: {quality_metrics['code_lines']:,} ({quality_metrics['code_to_total_ratio']:.2%} of total)")
            response.append(f"  • Comment Lines: {quality_metrics['comment_lines']:,} ({quality_metrics['comment_to_code_ratio']:.2%} of code lines)")
            response.append(f"  • Blank Lines: {quality_metrics['blank_lines']:,}")

            response.append(f"\n📝 **Code Style & Maintainability**:")
            response.append(f"  • TODO/FIXME Count: {quality_metrics['todo_fixme_count']}")
            response.append(f"  • Lines >120 Chars: {quality_metrics['long_lines_count']}")
            response.append(f"  • Files with >1000 LoC: {quality_metrics['very_large_code_files_count']}")

            response.append(f"\n🧪 **Testing & Documentation**:")
            response.append(f"  • Test Files Found: {len(file_info['test_files'])}")
            response.append(f"  • Test Coverage Estimate: {quality_metrics['test_coverage_estimate']:.1f}% (based on file counts)")
            response.append(f"  • Documentation Files (.md, .rst, etc.): {quality_metrics['documentation_files']}")

            if include_security:
                security_results = self._perform_security_scan(project_root, file_info)
                response.append(f"\n🔒 **Basic Security Scan**:")
                response.append(f"  • Security Score: {security_results['security_score']}/100")
                response.append(f"  • Issues Found: {security_results['issues_found']}")
                if security_results['issues']:
                    response.append(f"  • Top Issues (max 3 shown):")
                    for issue in security_results['issues'][:3]:
                        response.append(f"    - {issue['issue']} in {str(issue['file'])} ({issue['count']} occurrences)") # Ensure issue['file'] is str

            return "\n".join(response)
        except Exception as e:
            self.logger.error(f"Error in bb7_project_quality: {e}", exc_info=True)
            return f"❌ Error assessing project quality: {str(e)}"

    def bb7_project_structure(self, arguments: Dict[str, Any]) -> str:
        """Provides a summary of the project's directory structure and file type distribution."""
        project_root = Path.cwd()
        max_depth = arguments.get('max_depth', 5)
        include_hidden = arguments.get('include_hidden', False)

        try:
            file_info = self._scan_directory(project_root, max_depth=max_depth, include_hidden=include_hidden)

            response = ["**Project File Structure & Composition**:\n"]
            response.append(f"📁 **Overall Stats**:")
            response.append(f"  • Total Files Scanned: {file_info['total_files']}")
            response.append(f"  • Total Directories Scanned: {file_info['directories']}")
            response.append(f"  • Total Size: {file_info['total_size_bytes'] / (1024*1024):.2f} MB")

            if file_info['files_by_language']:
                response.append(f"\n💻 **Files by Language**:")
                for lang, files in sorted(file_info['files_by_language'].items(), key=lambda item: len(item[1]), reverse=True):
                    response.append(f"  • {lang.title()}: {len(files)} files")

            if file_info['files_by_extension']:
                response.append(f"\n📄 **Top File Extensions (Top 10)**:")
                sorted_extensions = sorted(file_info['files_by_extension'].items(), key=lambda x: x[1], reverse=True)
                for ext, count in sorted_extensions[:10]:
                    response.append(f"  • {ext}: {count} files")

            key_config_files = file_info.get('config_files', [])
            if key_config_files:
                response.append(f"\n⚙️ **Key Configuration Files Found ({len(key_config_files)})**:")
                for cfg_file in sorted(key_config_files)[:10]: # Show top 10 sorted
                     response.append(f"  • {cfg_file}")
                if len(key_config_files) > 10:
                    response.append("  • ... and more.")

            response.append(f"\n🌳 **Top-Level Directory Contents** (max_depth={max_depth}):")
            top_level_items = []
            # Ensure project_root is used for iterdir, not a potentially different 'path'
            for item in Path.cwd().iterdir(): # Use Path.cwd() to align with how project_root is defined
                if item.name.startswith('.') and not include_hidden and item.name not in ['.git', '.env', '.env.example']: # Basic filter for hidden
                    continue
                if item.is_dir():
                     # Basic exclude for common large/unwanted dirs
                    if item.name in ['node_modules', '__pycache__', '.git', 'venv', 'build', 'dist', 'target', '.next', '.cache', '.vscode', '.idea']:
                        if not include_hidden: # Only skip if not explicitly asked to include hidden
                            continue
                    top_level_items.append(f"  • {item.name}/ (Directory)")
                else:
                    top_level_items.append(f"  • {item.name} (File)")

            response.extend(sorted(top_level_items)[:15])
            if len(top_level_items) > 15:
                response.append("  • ... and more.")

            return "\n".join(response)
        except Exception as e:
            self.logger.error(f"Error in bb7_project_structure: {e}", exc_info=True)
            return f"❌ Error describing project structure: {str(e)}"

    def bb7_project_suggestions(self, arguments: Dict[str, Any]) -> str:
        """Generates actionable suggestions and recommendations based on project analysis."""
        project_root = Path.cwd()
        max_depth = arguments.get('max_depth', 3) # Use a moderate depth for suggestion generation

        try:
            file_info = self._scan_directory(project_root, max_depth=max_depth)
            # For _generate_recommendations, detected_tech['frameworks'] is expected to be a list of dicts,
            # but _generate_recommendations expects a dict like {'python': ['Django'], 'javascript': ['React']}
            # So, we need to transform it or pass the raw detected_tech.
            # The current _generate_recommendations is expecting the old format from _detect_frameworks.
            # Let's pass the new detected_tech and adapt _generate_recommendations if needed, or simplify here.

            # Simplification for now: Pass framework names grouped by language
            detected_tech = self._detect_frameworks(project_root, file_info)
            framework_names_for_reco = defaultdict(list)
            for fw_item in detected_tech.get('frameworks', []):
                lang_key = fw_item['language'].lower()
                framework_names_for_reco[lang_key].append(fw_item['name'])

            quality_metrics = self._analyze_code_quality(project_root, file_info)
            recommendations = self._generate_recommendations(project_root, file_info, framework_names_for_reco, quality_metrics)

            response = ["**Project Improvement Suggestions**:\n"]
            if recommendations:
                for i, rec in enumerate(recommendations, 1):
                    response.append(f"{i}. {rec}")
            else:
                response.append("No specific recommendations generated at this time. Project looks generally well-structured or needs more specific analysis tools.")

            return "\n".join(response)
        except Exception as e:
            self.logger.error(f"Error in bb7_project_suggestions: {e}", exc_info=True)
            return f"❌ Error generating project suggestions: {str(e)}"
    
    def bb7_project_dependencies(self, arguments: Dict[str, Any]) -> str: # RENAMED from bb7_get_project_dependencies
        """📦 Extract and analyze project dependencies from various package managers."""
        include_dev = arguments.get('include_dev', True)
        # check_security argument is kept for schema compatibility but not fully used in this focused version.
        check_security = arguments.get('check_security', True)
        
        try:
            project_root = Path.cwd()
            # Call _scan_directory to get file_info
            file_info = self._scan_directory(project_root, max_depth=arguments.get('max_depth', 3)) # Use a reasonable depth for dep finding
            dependencies = {
                'production': [],
                'development': [],
                'total_count': 0,
                'languages': [],
                'security_issues': 0
            }
            
            # Scan for dependency files
            dependency_files = [] # This list will store Path objects
            # file_info['dependency_files'] stores relative string paths
            # We need to reconstruct full paths for parsing, or re-scan based on names.
            # For simplicity, let's use the already found relative paths.
            for rel_dep_file_path_str in file_info['dependency_files']:
                dependency_files.append(project_root / rel_dep_file_path_str)
            
            # Parse dependency files
            for dep_file in dependency_files:
                try:
                    content = dep_file.read_text(encoding='utf-8', errors='ignore')
                    file_name = dep_file.name
                    
                    # Parse different file types
                    if file_name == 'package.json':
                        self._parse_package_json(content, dependencies)
                    elif file_name in ['requirements.txt', 'Pipfile']:
                        self._parse_python_deps(content, dependencies)
                    elif file_name in ['pom.xml']:
                        self._parse_maven_deps(content, dependencies)
                    elif file_name in ['go.mod']:
                        self._parse_go_deps(content, dependencies)
                        
                except Exception as e:
                    self.logger.error(f"Error parsing {dep_file}: {e}")
                    continue
            
            # Build response
            response = []
            response.append(f"📦 **Project Dependencies Analysis**\\n")
            response.append(f"**Total Dependencies**: {dependencies['total_count']}")
            response.append(f"**Languages**: {', '.join(dependencies['languages']) if dependencies['languages'] else 'None detected'}")
            response.append(f"**Dependency Files Found**: {len(dependency_files)}\\n")
            
            # Production dependencies
            if dependencies['production']:
                response.append(f"🎯 **Production Dependencies** ({len(dependencies['production'])}):")
                for dep in dependencies['production'][:10]:
                    response.append(f"  • **{dep['name']}**: {dep.get('version', 'latest')}")
                if len(dependencies['production']) > 10:
                    response.append(f"  • ... and {len(dependencies['production']) - 10} more")
                response.append("")
            
            # Development dependencies
            if include_dev and dependencies['development']:
                response.append(f"🔧 **Development Dependencies** ({len(dependencies['development'])}):")
                for dep in dependencies['development'][:10]:
                    response.append(f"  • **{dep['name']}**: {dep.get('version', 'latest')}")
                if len(dependencies['development']) > 10:
                    response.append(f"  • ... and {len(dependencies['development']) - 10} more")
                response.append("")
            
            # Security analysis
            if check_security and dependencies['security_issues'] > 0:
                response.append(f"🔒 **Security Analysis**:")
                response.append(f"  • **Potential Issues**: {dependencies['security_issues']}")
                response.append(f"  • **Recommendation**: Run security audit tools")
                response.append("")
            
            # Dependency file details
            if dependency_files:
                response.append(f"📄 **Dependency Files**:")
                for dep_file in dependency_files:
                    relative_path = dep_file.relative_to(project_root)
                    response.append(f"  • **{relative_path}**")
            
            return "\\n".join(response)
            
        except Exception as e:
            self.logger.error(f"Error analyzing dependencies: {e}", exc_info=True) # Added exc_info
            return f"❌ Error analyzing dependencies: {str(e)}"
    
    def _parse_package_json(self, content: str, dependencies: Dict[str, Any]) -> None: # Made private
        """Parse package.json dependencies"""
        try:
            data = json.loads(content)
            dependencies['languages'].append('JavaScript/Node.js')
            
            # Production dependencies
            prod_deps = data.get('dependencies', {})
            for name, version in prod_deps.items():
                dependencies['production'].append({'name': name, 'version': version})
            
            # Development dependencies
            dev_deps = data.get('devDependencies', {})
            for name, version in dev_deps.items():
                dependencies['development'].append({'name': name, 'version': version})
            
            dependencies['total_count'] += len(prod_deps) + len(dev_deps)
            
        except json.JSONDecodeError:
            pass
    
    def _parse_python_deps(self, content: str, dependencies: Dict[str, Any]) -> None: # Made private
        """Parse Python dependencies (requirements.txt, Pipfile)"""
        dependencies['languages'].append('Python')
        
        lines = content.splitlines()
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                # Simple parsing - extract package name
                if '==' in line:
                    name, version = line.split('==', 1)
                elif '>=' in line:
                    name, version = line.split('>=', 1)
                else:
                    name, version = line, 'latest'
                
                dependencies['production'].append({'name': name.strip(), 'version': version.strip()})
                dependencies['total_count'] += 1
    
    def _parse_maven_deps(self, content: str, dependencies: Dict[str, Any]) -> None: # Made private
        """Parse Maven dependencies (pom.xml)"""
        dependencies['languages'].append('Java/Maven')
        # Simple regex-based parsing for demo
        import re
        
        artifact_pattern = r'<artifactId>([^<]+)</artifactId>'
        matches = re.findall(artifact_pattern, content)
        
        for match in matches:
            dependencies['production'].append({'name': match, 'version': 'unknown'})
            dependencies['total_count'] += 1
    
    def _parse_go_deps(self, content: str, dependencies: Dict[str, Any]) -> None: # Made private
        """Parse Go dependencies (go.mod)"""
        dependencies['languages'].append('Go')
        
        lines = content.splitlines()
        in_require = False
        
        for line in lines:
            line = line.strip()
            if line.startswith('require ('):
                in_require = True
                continue
            elif line == ')' and in_require:
                in_require = False
                continue
            elif in_require and line:
                parts = line.split()
                if len(parts) >= 2:
                    name, version = parts[0], parts[1]
                    dependencies['production'].append({'name': name, 'version': version})
                    dependencies['total_count'] += 1
    
    def bb7_project_health_check(self, arguments: Dict[str, Any]) -> str:
        """🏥 Comprehensive project health assessment with actionable insights"""
        include_recommendations = arguments.get('include_recommendations', True)
        check_performance = arguments.get('check_performance', True)
        
        try:
            project_root = Path.cwd()
            
            # Basic file scan
            file_info = self._scan_directory(project_root)
            
            # Health metrics
            health_score = 100
            issues = []
            recommendations = []
            
            # Check for essential files
            essential_files = ['README.md', 'README.rst', 'README.txt']
            has_readme = any((project_root / f).exists() for f in essential_files)
            if not has_readme:
                health_score -= 15
                issues.append("Missing README file")
                recommendations.append("Add a README.md file to document your project")
            
            # Check for version control
            if not (project_root / '.git').exists():
                health_score -= 10
                issues.append("No Git repository detected")
                recommendations.append("Initialize Git repository for version control")
            
            # Check for dependency management
            has_deps = len(file_info['dependency_files']) > 0
            if not has_deps:
                health_score -= 20
                issues.append("No dependency management files found")
                recommendations.append("Add dependency management (package.json, requirements.txt, etc.)")
            
            # Check for tests
            has_tests = len(file_info['test_files']) > 0
            if not has_tests:
                health_score -= 15
                issues.append("No test files detected")
                recommendations.append("Add unit tests to improve code reliability")
            
            # Check for configuration
            has_config = len(file_info['config_files']) > 0
            if not has_config:
                health_score -= 10
                issues.append("Limited configuration files")
                recommendations.append("Add configuration files for better project setup")
            
            # Calculate test-to-code ratio
            code_files = sum(len(files) for files in file_info['files_by_language'].values())
            test_ratio = len(file_info['test_files']) / max(code_files, 1) * 100
            
            if test_ratio < 20:
                health_score -= 10
                issues.append(f"Low test coverage ratio ({test_ratio:.1f}%)")
            
            # Check for large files
            if file_info['large_files']:
                health_score -= 5
                issues.append(f"{len(file_info['large_files'])} large files detected")
                recommendations.append("Consider splitting large files or using Git LFS")
            
            # Determine health level
            if health_score >= 90:
                health_level = "Excellent"
                health_emoji = "🟢"
            elif health_score >= 75:
                health_level = "Good"
                health_emoji = "🟡"
            elif health_score >= 60:
                health_level = "Fair"
                health_emoji = "🟠"
            else:
                health_level = "Needs Improvement"
                health_emoji = "🔴"
            
            # Build response
            response = []
            response.append(f"🏥 **Project Health Assessment**\\n")
            response.append(f"**Overall Health Score**: {health_score}/100")
            response.append(f"**Health Level**: {health_emoji} {health_level}\\n")
            
            # Project overview
            response.append(f"📊 **Project Overview**:")
            response.append(f"  • **Total Files**: {file_info['total_files']}")
            response.append(f"  • **Code Files**: {sum(len(files) for files in file_info['files_by_language'].values())}")
            response.append(f"  • **Test Files**: {len(file_info['test_files'])}")
            response.append(f"  • **Config Files**: {len(file_info['config_files'])}")
            response.append(f"  • **Test-to-Code Ratio**: {test_ratio:.1f}%\\n")
            
            # Issues found
            if issues:
                response.append(f"⚠️ **Issues Identified** ({len(issues)}):")
                for issue in issues:
                    response.append(f"  • {issue}")
                response.append("")
            
            # Recommendations
            if include_recommendations and recommendations:
                response.append(f"💡 **Recommendations** ({len(recommendations)}):")
                for rec in recommendations:
                    response.append(f"  • {rec}")
                response.append("")
            
            # Next steps
            response.append(f"🎯 **Next Steps**:")
            if health_score < 75:
                response.append(f"  • Focus on addressing the identified issues")
                response.append(f"  • Prioritize adding missing essential files")
                response.append(f"  • Improve test coverage")
            else:
                response.append(f"  • Project is in good shape!")
                response.append(f"  • Consider advanced optimizations")
                response.append(f"  • Maintain current best practices")
            
            return "\\n".join(response)
            
        except Exception as e:
            self.logger.error(f"Error performing health check: {e}")
            return f"❌ Error performing health check: {str(e)}"
    
    # ===== MCP TOOL REGISTRATION =====
    
    def get_tools(self) -> Dict[str, Any]:
        """Return all project context tools in MCP format"""
        return {
            'bb7_project_scan': { # Renamed
                'description': '🔍 Comprehensive project scan including structure, languages, frameworks, quality, and basic security.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'max_depth': {'type': 'integer', 'description': 'Maximum directory depth to analyze.', 'default': 4},
                        'include_hidden': {'type': 'boolean', 'description': 'Include hidden files/directories.', 'default': False},
                        'include_security': {'type': 'boolean', 'description': 'Include basic security scan.', 'default': True}
                    }
                },
                'function': self.bb7_project_scan
            },
            'bb7_project_dependencies': { # Renamed
                'description': '📦 Extract and analyze project dependencies from various package managers.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'include_dev': {'type': 'boolean', 'description': 'Include development dependencies.', 'default': True}
                        # 'check_security' argument removed from schema as it's not fully implemented in this focused tool.
                    }
                },
                'function': self.bb7_project_dependencies
            },
            'bb7_project_health_check': {
                'description': '🏥 Comprehensive project health assessment with actionable insights.',
                'inputSchema': { # Existing schema seems fine
                    'type': 'object',
                    'properties': {
                        'include_recommendations': {
                            'type': 'boolean',
                            'description': 'Include actionable recommendations',
                            'default': True
                        },
                        'check_performance': {
                            'type': 'boolean',
                            'description': 'Include performance-related checks',
                            'default': True
                        }
                    }
                },
                'function': self.bb7_project_health_check
            },
            'bb7_project_frameworks': {
                'description': '🛠️ Detects and lists frameworks, build tools, and other key technologies.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'max_depth': {'type': 'integer', 'description': 'Maximum directory depth for scanning.', 'default': 3}
                    }
                },
                'function': self.bb7_project_frameworks
            },
            'bb7_project_quality': {
                'description': '⭐ Assesses code quality including LoC, comments, TODOs, and basic security.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'max_depth': {'type': 'integer', 'description': 'Maximum directory depth for code scanning.', 'default': 4},
                        'include_security': {'type': 'boolean', 'description': 'Include basic security scan results.', 'default': True}
                    }
                },
                'function': self.bb7_project_quality
            },
            'bb7_project_structure': {
                'description': '🌳 Displays project file structure summary, languages, and key file types.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'max_depth': {'type': 'integer', 'description': 'Maximum directory depth for scanning file statistics.', 'default': 5},
                        'include_hidden': {'type': 'boolean', 'description': 'Include hidden files/directories in top-level listing.', 'default': False}
                    }
                },
                'function': self.bb7_project_structure
            },
            'bb7_project_suggestions': {
                'description': '💡 Provides actionable suggestions for project improvement based on analysis.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                         'max_depth': {'type': 'integer', 'description': 'Maximum directory depth for analysis.', 'default': 3}
                    }
                },
                'function': self.bb7_project_suggestions
            }
        }


# Create global instance for MCP server
project_context_tool = ProjectContextTool()

# Export tools for MCP server registration
def get_tools():
    return project_context_tool.get_tools()

# TODO: This is a test TODO
# This is a very long line of code or comment for testing purposes, it should absolutely exceed the 120 character limit by a good margin to ensure this check works fine. This is just a sample line.

if __name__ == "__main__":
    import shutil # For test cleanup

    def test_project_context_tool():
        # Configure logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logger = logging.getLogger(__name__)

        tool = ProjectContextTool()

        # --- Setup Test Project ---
        test_project_dir = Path("test_project")
        if test_project_dir.exists():
            shutil.rmtree(test_project_dir) # Clean up if exists
        test_project_dir.mkdir(parents=True, exist_ok=True)

        (test_project_dir / "main.py").write_text(
            "# test_project/main.py\n"
            "import flask\n\n"
            "app = flask.Flask(__name__)\n\n"
            "@app.route('/')\n"
            "def hello_world():\n"
            "    # This is a very long line for testing purposes, it should exceed 120 characters to check the long line detection in code quality analysis tool. This is just a sample.\n"
            "    return 'Hello, World! This is a Flask application running in the test_project. We are testing project context analysis.'\n\n"
            "# TODO: Add more routes later for full testing.\n"
            "# FIXME: This is a test FIXME comment.\n\n"
            "if __name__ == '__main__':\n"
            "    app.run(debug=True)\n"
        )
        (test_project_dir / "requirements.txt").write_text(
            "flask>=2.0\n"
            "requests<3.0 # Example with version specifier\n"
            "# This is a comment in requirements.txt\n"
            "# TODO: Consider adding a database ORM like SQLAlchemy later.\n"
            "# FIXME: Ensure compatibility with Python 3.10+ for all dependencies.\n"
        )
        (test_project_dir / "README.md").write_text(
            "# Test Project\n\n"
            "This is a simple test project to validate the `ProjectContextTool`.\n\n"
            "## Features\n"
            "- Flask application (`main.py`)\n"
            "- Dependencies listed in `requirements.txt`\n\n"
            "## TODO\n"
            "- Add more complex scenarios.\n"
            "- This is another test TODO in a Markdown file.\n"
        )

        logger.info(f"Test project created at {test_project_dir.resolve()}")

        original_cwd = Path.cwd()
        os.chdir(test_project_dir)
        logger.info(f"Changed CWD to {Path.cwd()}")

        print("\n\n--- Testing Project Context Tools on test_project ---")

        print("\n--- Testing bb7_project_scan ---")
        result_scan = tool.bb7_project_scan({'max_depth': 3})
        print(result_scan)

        print("\n--- Testing bb7_project_frameworks ---")
        result_frameworks = tool.bb7_project_frameworks({'max_depth': 2})
        print(result_frameworks)

        print("\n--- Testing bb7_project_quality ---")
        result_quality = tool.bb7_project_quality({'max_depth': 2, 'include_security': True})
        print(result_quality)

        print("\n--- Testing bb7_project_dependencies ---")
        result_dependencies = tool.bb7_project_dependencies({})
        print(result_dependencies)

        print("\n--- Testing bb7_project_structure ---")
        result_structure = tool.bb7_project_structure({'max_depth': 2})
        print(result_structure)

        print("\n--- Testing bb7_project_suggestions ---")
        result_suggestions = tool.bb7_project_suggestions({'max_depth': 2})
        print(result_suggestions)

        print("\n--- Testing bb7_project_health_check ---")
        result_health = tool.bb7_project_health_check({})
        print(result_health)

        os.chdir(original_cwd)
        logger.info(f"Restored CWD to {Path.cwd()}")

        # Clean up test project
        try:
            shutil.rmtree(test_project_dir)
            logger.info(f"Test project directory {test_project_dir} removed successfully.")
        except Exception as e_rm:
            logger.error(f"Error removing test project directory {test_project_dir}: {e_rm}")

    test_project_context_tool()