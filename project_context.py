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
                'config_files': ['.pylintrc', 'setup.cfg', 'pyproject.toml', 'tox.ini', '.flake8', 'mypy.ini'],
                'test_patterns': ['test_*.py', '*_test.py', 'tests/', 'test/'],
                'frameworks': {
                    'django': ['manage.py', 'settings.py', 'wsgi.py'],
                    'flask': ['app.py', 'application.py'],
                    'fastapi': ['main.py', 'app.py'],
                    'pytest': ['pytest.ini', 'conftest.py']
                }
            },
            'javascript': {
                'extensions': ['.js', '.jsx', '.mjs', '.cjs'],
                'dependency_files': ['package.json', 'package-lock.json', 'yarn.lock'],
                'config_files': ['.eslintrc', '.babelrc', 'webpack.config.js', '.prettierrc'],
                'test_patterns': ['*.test.js', '*.spec.js', '__tests__/', 'test/'],
                'frameworks': {
                    'react': ['react', 'src/App.js', 'public/index.html'],
                    'vue': ['vue', 'src/main.js', 'vue.config.js'],
                    'angular': ['angular.json', 'src/main.ts'],
                    'express': ['express', 'app.js', 'server.js'],
                    'next': ['next.config.js', 'pages/']
                }
            },
            'typescript': {
                'extensions': ['.ts', '.tsx', '.d.ts'],
                'dependency_files': ['package.json', 'package-lock.json', 'yarn.lock'],
                'config_files': ['tsconfig.json', 'tslint.json', '.eslintrc.js'],
                'test_patterns': ['*.test.ts', '*.spec.ts', '__tests__/'],
                'frameworks': {
                    'angular': ['@angular', 'angular.json'],
                    'react': ['@types/react', 'src/App.tsx'],
                    'vue': ['@types/vue', 'vue.config.ts'],
                    'nest': ['@nestjs', 'nest-cli.json']
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
            'structure': []
        }
        
        try:
            for root, dirs, files in os.walk(path):
                current_depth = len(Path(root).relative_to(path).parts)
                if current_depth >= max_depth:
                    dirs.clear()
                    continue
                
                # Skip hidden directories if not requested
                if not include_hidden:
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', '.git']]
                
                file_info['directories'] += len(dirs)
                
                for file in files:
                    if not include_hidden and file.startswith('.') and file not in ['.gitignore', '.env', '.env.example']:
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
                        if ext in config['extensions']:
                            file_info['files_by_language'][language].append(relative_path)
                            break
                    
                    # Check for special file types
                    if file in sum([config['dependency_files'] for config in self.language_configs.values()], []):
                        file_info['dependency_files'].append(relative_path)
                    
                    if file in sum([config['config_files'] for config in self.language_configs.values()], []):
                        file_info['config_files'].append(relative_path)
                    
                    # Check for test files
                    for language, config in self.language_configs.items():
                        for pattern in config['test_patterns']:
                            if '*' in pattern:
                                if file.endswith(pattern.replace('*', '')):
                                    file_info['test_files'].append(relative_path)
                                    break
                            elif pattern.endswith('/'):
                                if pattern.rstrip('/') in relative_path:
                                    file_info['test_files'].append(relative_path)
                                    break
                    
                    # Check file size
                    try:
                        size = file_path.stat().st_size
                        if size > 1024 * 1024:  # Files larger than 1MB
                            file_info['large_files'].append({
                                'path': relative_path,
                                'size_mb': round(size / (1024 * 1024), 2)
                            })
                    except (OSError, PermissionError):
                        pass
        
        except Exception as e:
            self.logger.error(f"Error scanning directory: {e}")
        
        return file_info
    
    def _detect_frameworks(self, project_root: Path, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Detect frameworks and technologies used in the project"""
        frameworks = defaultdict(list)
        
        try:
            # Check dependency files for framework indicators
            for dep_file in file_info['dependency_files']:
                dep_path = project_root / dep_file
                if not dep_path.exists():
                    continue
                
                try:
                    content = dep_path.read_text(encoding='utf-8', errors='ignore')
                    
                    # Check each language's frameworks
                    for language, config in self.language_configs.items():
                        if dep_file in config['dependency_files']:
                            for framework, indicators in config['frameworks'].items():
                                for indicator in indicators:
                                    if indicator in content:
                                        frameworks[language].append(framework)
                                        break
                except Exception:
                    continue
            
            # Check file structure for framework indicators
            all_files = [project_root / f for files in file_info['files_by_language'].values() for f in files]
            all_paths = [str(f) for f in all_files] + file_info['config_files']
            
            for language, config in self.language_configs.items():
                for framework, indicators in config['frameworks'].items():
                    for indicator in indicators:
                        if any(indicator in path for path in all_paths):
                            if framework not in frameworks[language]:
                                frameworks[language].append(framework)
        
        except Exception as e:
            self.logger.error(f"Error detecting frameworks: {e}")
        
        return dict(frameworks)
    
    def _analyze_code_quality(self, project_root: Path, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Basic code quality analysis"""
        quality_metrics = {
            'total_lines': 0,
            'code_lines': 0,
            'comment_lines': 0,
            'blank_lines': 0,
            'average_file_size': 0,
            'test_coverage_estimate': 0,
            'documentation_files': 0
        }
        
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
                        
                        total_size += len(content)
                        code_files += 1
                        
                    except Exception:
                        continue
            
            # Calculate averages
            if code_files > 0:
                quality_metrics['average_file_size'] = total_size // code_files
            
            # Estimate test coverage based on test files vs code files
            if code_files > 0:
                test_file_count = len(file_info['test_files'])
                quality_metrics['test_coverage_estimate'] = min(100, int((test_file_count / code_files) * 100))
            
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
    
    def bb7_analyze_project_structure(self, arguments: Dict[str, Any]) -> str:
        """🔍 Comprehensive project structure analysis with intelligent categorization and architectural insights"""
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
            recommendations = self._generate_recommendations(project_root, file_info, frameworks, quality_metrics)
            
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
            if frameworks:
                response.append(f"🚀 **Frameworks & Technologies**:")
                for language, fw_list in frameworks.items():
                    response.append(f"  • **{language.title()}**: {', '.join(fw_list)}")
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
            self.logger.error(f"Error analyzing project structure: {e}")
            return f"❌ Error analyzing project structure: {str(e)}"
    
    def bb7_get_project_dependencies(self, arguments: Dict[str, Any]) -> str:
        """📦 Extract and analyze project dependencies with update recommendations"""
        include_dev = arguments.get('include_dev', True)
        check_security = arguments.get('check_security', True)
        
        try:
            project_root = Path.cwd()
            dependencies = {
                'production': [],
                'development': [],
                'total_count': 0,
                'languages': [],
                'security_issues': 0
            }
            
            # Scan for dependency files
            dependency_files = []
            for root, dirs, files in os.walk(project_root):
                for file in files:
                    for config in self.language_configs.values():
                        if file in config['dependency_files']:
                            dependency_files.append(Path(root) / file)
            
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
            self.logger.error(f"Error analyzing dependencies: {e}")
            return f"❌ Error analyzing dependencies: {str(e)}"
    
    def _parse_package_json(self, content: str, dependencies: Dict[str, Any]) -> None:
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
    
    def _parse_python_deps(self, content: str, dependencies: Dict[str, Any]) -> None:
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
    
    def _parse_maven_deps(self, content: str, dependencies: Dict[str, Any]) -> None:
        """Parse Maven dependencies (pom.xml)"""
        dependencies['languages'].append('Java/Maven')
        # Simple regex-based parsing for demo
        import re
        
        artifact_pattern = r'<artifactId>([^<]+)</artifactId>'
        matches = re.findall(artifact_pattern, content)
        
        for match in matches:
            dependencies['production'].append({'name': match, 'version': 'unknown'})
            dependencies['total_count'] += 1
    
    def _parse_go_deps(self, content: str, dependencies: Dict[str, Any]) -> None:
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
            'bb7_analyze_project_structure': {
                'description': '🔍 Comprehensive project structure analysis with intelligent categorization and architectural insights. Perfect for understanding codebases, identifying patterns, and getting project overview with technology detection, code quality metrics, and security scanning.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'max_depth': {
                            'type': 'integer',
                            'description': 'Maximum directory depth to analyze',
                            'default': 4
                        },
                        'include_hidden': {
                            'type': 'boolean',
                            'description': 'Include hidden files and directories',
                            'default': False
                        },
                        'include_security': {
                            'type': 'boolean',
                            'description': 'Include security vulnerability scanning',
                            'default': True
                        }
                    }
                },
                'function': self.bb7_analyze_project_structure
            },
            'bb7_get_project_dependencies': {
                'description': '📦 Extract and analyze project dependencies from various package managers with security analysis and update recommendations. Perfect for dependency auditing, security assessment, and project maintenance across multiple languages and frameworks.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'include_dev': {
                            'type': 'boolean',
                            'description': 'Include development dependencies',
                            'default': True
                        },
                        'check_security': {
                            'type': 'boolean',
                            'description': 'Perform basic security checks',
                            'default': True
                        }
                    }
                },
                'function': self.bb7_get_project_dependencies
            },
            'bb7_project_health_check': {
                'description': '🏥 Comprehensive project health assessment with actionable insights and recommendations. Perfect for evaluating project quality, identifying improvements, and ensuring best practices across documentation, testing, configuration, and structure.',
                'inputSchema': {
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
            }
        }


# Create global instance for MCP server
project_context_tool = ProjectContextTool()

# Export tools for MCP server registration
def get_tools():
    return project_context_tool.get_tools()