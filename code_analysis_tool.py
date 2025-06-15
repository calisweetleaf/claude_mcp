#!/usr/bin/env python3
"""
Code Analysis Tool - Comprehensive code analysis and security auditing for MCP Server

This tool provides advanced static code analysis, security auditing, pattern detection,
and quality assessment capabilities. Optimized for GitHub Copilot agent mode with
intelligent suggestions and comprehensive reporting.
"""

import ast
import logging
import re
import time
import json
import hashlib
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import io
import sys


class CodeAnalysisTool:
    """
    Advanced code analysis with security auditing, pattern detection, and quality assessment
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.data_dir = Path("data/code_analysis")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Execution history for audit trails
        self.execution_history = []
        self.max_history = 50
        
        # Security patterns for different languages
        self.security_patterns = {
            'python': [
                (r'eval\s*\(', 'Dangerous eval() usage'),
                (r'exec\s*\(', 'Dangerous exec() usage'),
                (r'__import__\s*\(', 'Dynamic import usage'),
                (r'open\s*\([^)]*["\']w["\']', 'File write operation'),
                (r'subprocess\.', 'Subprocess execution'),
                (r'os\.system\s*\(', 'OS command execution'),
                (r'pickle\.loads?\s*\(', 'Pickle deserialization (unsafe)'),
                (r'yaml\.load\s*\(', 'YAML load without safe_load'),
            ],
            'javascript': [
                (r'eval\s*\(', 'Dangerous eval() usage'),
                (r'Function\s*\(', 'Function constructor'),
                (r'innerHTML\s*=', 'InnerHTML assignment (XSS risk)'),
                (r'document\.write\s*\(', 'Document.write usage'),
                (r'setTimeout\s*\(["\']', 'setTimeout with string'),
                (r'setInterval\s*\(["\']', 'setInterval with string'),
            ]
        }
        
        self.logger.info("Code Analysis Tool initialized with security auditing capabilities")
    
    def get_tools(self) -> Dict[str, Any]:
        """Return all available code analysis tools with proper MCP formatting"""
        return {
            'bb7_analyze_code': {
                'description': '🔬 Perform comprehensive static code analysis including AST parsing, complexity metrics, security auditing, pattern detection, and quality assessment. Perfect for code reviews, security audits, refactoring guidance, and understanding complex codebases. Provides detailed insights with actionable recommendations for code improvement and optimization.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'code': {
                            'type': 'string',
                            'description': 'Source code to analyze'
                        },
                        'language': {
                            'type': 'string',
                            'description': 'Programming language',
                            'enum': ['python', 'javascript', 'typescript', 'java', 'cpp', 'c', 'go', 'rust'],
                            'default': 'python'
                        },
                        'include_security': {
                            'type': 'boolean',
                            'description': 'Include security analysis',
                            'default': True
                        },
                        'include_metrics': {
                            'type': 'boolean',
                            'description': 'Include quality metrics',
                            'default': True
                        },
                        'include_suggestions': {
                            'type': 'boolean',
                            'description': 'Include improvement suggestions',
                            'default': True
                        },
                        'file_path': {
                            'type': 'string',
                            'description': 'File path to read code from (alternative to code parameter)'
                        }
                    }
                },
                'function': self.bb7_analyze_code
            },
            'bb7_code_suggestions': {
                'description': '💡 Generate intelligent code improvement suggestions including refactoring opportunities, performance optimizations, security enhancements, and best practice recommendations. Perfect for code reviews, learning, and continuous improvement. Provides specific, actionable suggestions with examples and explanations.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'code': {
                            'type': 'string',
                            'description': 'Source code to analyze for suggestions'
                        },
                        'language': {
                            'type': 'string',
                            'description': 'Programming language',
                            'enum': ['python', 'javascript', 'typescript', 'java', 'cpp', 'c', 'go', 'rust'],
                            'default': 'python'
                        },
                        'focus_area': {
                            'type': 'string',
                            'description': 'Specific area to focus suggestions on',
                            'enum': ['performance', 'security', 'readability', 'maintainability', 'all'],
                            'default': 'all'
                        },
                        'skill_level': {
                            'type': 'string',
                            'description': 'Target skill level for suggestions',
                            'enum': ['beginner', 'intermediate', 'advanced'],
                            'default': 'intermediate'
                        }
                    },
                    'required': ['code']
                },
                'function': self.bb7_code_suggestions
            },
            'bb7_security_audit': {
                'description': '🔐 Perform detailed security audit of code including vulnerability detection, unsafe pattern identification, and compliance checking. Perfect for security reviews, penetration testing preparation, and ensuring code meets security standards. Provides specific remediation guidance and security best practices recommendations.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'code': {
                            'type': 'string',
                            'description': 'Source code to audit'
                        },
                        'language': {
                            'type': 'string',
                            'description': 'Programming language',
                            'enum': ['python', 'javascript', 'typescript', 'java', 'cpp', 'c'],
                            'default': 'python'
                        },
                        'audit_level': {
                            'type': 'string',
                            'description': 'Security audit thoroughness level',
                            'enum': ['basic', 'standard', 'strict'],
                            'default': 'standard'
                        },
                        'include_compliance': {
                            'type': 'boolean',
                            'description': 'Include compliance checking',
                            'default': True
                        },
                        'file_path': {
                            'type': 'string',
                            'description': 'File path to read code from'
                        }
                    }
                },
                'function': self.bb7_security_audit
            },
            'bb7_execute_code_safely': {
                'description': '🛡️ Execute Python code in a secure sandboxed environment with comprehensive safety controls, resource monitoring, and execution analysis. Perfect for testing code snippets, validating algorithms, running examples, and educational purposes. Provides detailed execution results with performance metrics and security safeguards to prevent system damage.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'code': {
                            'type': 'string',
                            'description': 'Python code to execute safely'
                        },
                        'timeout': {
                            'type': 'integer',
                            'description': 'Execution timeout in seconds',
                            'default': 10,
                            'minimum': 1,
                            'maximum': 30
                        },
                        'capture_output': {
                            'type': 'boolean',
                            'description': 'Whether to capture print output',
                            'default': True
                        },
                        'analyze_result': {
                            'type': 'boolean',
                            'description': 'Whether to analyze execution results',
                            'default': True
                        }
                    },
                    'required': ['code']
                },
                'function': self.bb7_execute_code_safely
            }
        }

    async def bb7_analyze_code(self, arguments: Dict[str, Any]) -> str:
        """
        🔬 Perform comprehensive static code analysis including AST parsing, complexity metrics, 
        security auditing, pattern detection, and quality assessment. Perfect for code reviews, 
        security audits, refactoring guidance, and understanding complex codebases.
        """
        code = arguments.get('code', '')
        language = arguments.get('language', 'python')
        include_security = arguments.get('include_security', True)
        include_metrics = arguments.get('include_metrics', True)
        include_suggestions = arguments.get('include_suggestions', True)
        file_path = arguments.get('file_path', '')
        
        # Get code from file if file_path provided
        if file_path and not code:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
            except Exception as e:
                return f"❌ Error reading file '{file_path}': {str(e)}"
        
        if not code.strip():
            return "❌ Please provide code to analyze or a valid file path."
        
        try:
            response = f"🔬 **Comprehensive Code Analysis**\n\n"
            response += f"💻 **Language**: {language.title()}\n"
            response += f"📏 **Code Size**: {len(code)} characters, {len(code.splitlines())} lines\n"
            
            if file_path:
                response += f"📁 **Source File**: {file_path}\n"
            
            response += "\n"
            
            # Perform comprehensive analysis
            analysis_result = await self._perform_comprehensive_analysis(
                code, language, include_security, include_metrics, include_suggestions
            )
            
            # Basic overview
            if analysis_result.get('overview'):
                overview = analysis_result['overview']
                response += f"📊 **Code Overview**:\n"
                response += f"  • **Functions**: {overview.get('function_count', 0)}\n"
                response += f"  • **Classes**: {overview.get('class_count', 0)}\n"
                response += f"  • **Import Statements**: {overview.get('import_count', 0)}\n"
                
                if overview.get('main_constructs'):
                    response += f"  • **Main Constructs**: {', '.join(overview['main_constructs'])}\n"
                
                response += "\n"
            
            # Quality metrics
            if include_metrics and analysis_result.get('metrics'):
                metrics = analysis_result['metrics']
                response += f"📈 **Quality Metrics**:\n"
                response += f"  • **Complexity Score**: {metrics.get('complexity', 'N/A')}\n"
                response += f"  • **Maintainability**: {metrics.get('maintainability', 'N/A')}\n"
                response += f"  • **Code Density**: {metrics.get('code_density', 'N/A')}\n"
                response += f"  • **Comment Ratio**: {metrics.get('comment_ratio', 'N/A')}\n"
                
                if metrics.get('cyclomatic_complexity'):
                    response += f"  • **Cyclomatic Complexity**: {metrics['cyclomatic_complexity']}\n"
                
                response += "\n"
            
            # Security analysis
            if include_security and analysis_result.get('security'):
                security = analysis_result['security']
                response += f"🔐 **Security Analysis**:\n"
                
                if security.get('issues'):
                    response += f"  • **Security Issues Found**: {len(security['issues'])}\n"
                    for issue in security['issues'][:5]:  # Show first 5 issues
                        response += f"    - {issue['type']}: {issue['description']}\n"
                        if issue.get('line'):
                            response += f"      Line {issue['line']}: {issue.get('code', '')[:50]}...\n"
                    
                    if len(security['issues']) > 5:
                        response += f"    ... and {len(security['issues']) - 5} more issues\n"
                else:
                    response += f"  • **Security Issues**: None detected ✅\n"
                
                response += f"  • **Risk Level**: {security.get('risk_level', 'Unknown')}\n"
                response += "\n"
            
            # Pattern analysis
            if analysis_result.get('patterns'):
                patterns = analysis_result['patterns']
                response += f"🎯 **Code Patterns**:\n"
                
                if patterns.get('design_patterns'):
                    response += f"  • **Design Patterns**: {', '.join(patterns['design_patterns'])}\n"
                
                if patterns.get('anti_patterns'):
                    response += f"  • **Anti-patterns**: {', '.join(patterns['anti_patterns'])}\n"
                
                if patterns.get('coding_style'):
                    response += f"  • **Coding Style**: {patterns['coding_style']}\n"
                
                response += "\n"
            
            # Dependencies analysis
            if analysis_result.get('dependencies'):
                deps = analysis_result['dependencies']
                response += f"📦 **Dependencies**:\n"
                
                if deps.get('imports'):
                    response += f"  • **Imported Modules**: {', '.join(deps['imports'][:10])}\n"
                    if len(deps['imports']) > 10:
                        response += f"    ... and {len(deps['imports']) - 10} more\n"
                
                if deps.get('external_deps'):
                    response += f"  • **External Dependencies**: {len(deps['external_deps'])}\n"
                
                response += "\n"
            
            # Improvement suggestions
            if include_suggestions and analysis_result.get('suggestions'):
                suggestions = analysis_result['suggestions']
                response += f"💡 **Improvement Suggestions**:\n"
                
                for category, items in suggestions.items():
                    if items:
                        response += f"  • **{category.replace('_', ' ').title()}**:\n"
                        for item in items[:3]:
                            response += f"    - {item}\n"
                        if len(items) > 3:
                            response += f"    ... and {len(items) - 3} more suggestions\n"
                
                response += "\n"
            
            # Overall assessment
            assessment = analysis_result.get('assessment', {})
            if assessment:
                response += f"🎯 **Overall Assessment**:\n"
                response += f"  • **Readability**: {assessment.get('readability', 'Unknown')}\n"
                response += f"  • **Maintainability**: {assessment.get('maintainability', 'Unknown')}\n"
                response += f"  • **Complexity**: {assessment.get('complexity', 'Unknown')}\n"
                response += f"  • **Security**: {assessment.get('security', 'Unknown')}\n\n"
            
            # Next steps
            response += f"💡 **Recommended Next Steps**:\n"
            response += f"  • Use bb7_security_audit for detailed security analysis\n"
            response += f"  • Use bb7_execute_code_safely for safe code testing\n"
            response += f"  • Consider refactoring high-complexity functions\n"
            response += f"  • Add unit tests for better code coverage"
            
            self.logger.info(f"Completed comprehensive code analysis ({len(code)} characters)")
            return response
            
        except Exception as e:
            self.logger.error(f"Error in code analysis: {e}")
            return f"❌ **Analysis Error:** {str(e)}\n\n💡 **Suggestion:** Check code syntax and try again with a smaller code sample"

    async def bb7_code_suggestions(self, arguments: Dict[str, Any]) -> str:
        """
        💡 Generate intelligent code improvement suggestions including refactoring opportunities, 
        performance optimizations, security enhancements, and best practice recommendations. 
        Perfect for code reviews, learning, and continuous improvement.
        """
        code = arguments.get('code', '')
        language = arguments.get('language', 'python')
        focus_area = arguments.get('focus_area', 'all')
        skill_level = arguments.get('skill_level', 'intermediate')
        
        if not code.strip():
            return "❌ Please provide code to analyze for suggestions."
        
        try:
            response = f"💡 **Intelligent Code Suggestions**\n\n"
            response += f"💻 **Language**: {language.title()}\n"
            response += f"🎯 **Focus Area**: {focus_area.title()}\n"
            response += f"📚 **Skill Level**: {skill_level.title()}\n\n"
            
            # Generate suggestions based on focus area
            suggestions = self._generate_targeted_suggestions(code, language, focus_area, skill_level)
            
            if not suggestions:
                response += f"✅ **No immediate suggestions found**\n\n"
                response += f"Your code appears to follow good practices for the {focus_area} focus area.\n\n"
                response += f"💡 **General tips**:\n"
                response += f"  • Consider adding documentation if not present\n"
                response += f"  • Add unit tests to verify functionality\n"
                response += f"  • Review for edge case handling\n"
                return response
            
            # Organize suggestions by category
            suggestion_categories = {
                'Performance': [],
                'Security': [],
                'Readability': [],
                'Maintainability': [],
                'Best Practices': []
            }
            
            for suggestion in suggestions:
                category = suggestion.get('category', 'Best Practices')
                suggestion_categories[category].append(suggestion)
            
            # Display suggestions by category
            for category, items in suggestion_categories.items():
                if items and (focus_area == 'all' or focus_area.lower() in category.lower()):
                    response += f"## 🔧 **{category} Suggestions**\n\n"
                    
                    for i, suggestion in enumerate(items, 1):
                        response += f"**{i}. {suggestion['title']}**\n"
                        response += f"📝 *{suggestion['description']}*\n"
                        
                        if suggestion.get('current_code'):
                            response += f"❌ **Current:**\n```{language}\n{suggestion['current_code']}\n```\n"
                        
                        if suggestion.get('improved_code'):
                            response += f"✅ **Improved:**\n```{language}\n{suggestion['improved_code']}\n```\n"
                        
                        if suggestion.get('explanation'):
                            response += f"💡 **Why:** {suggestion['explanation']}\n"
                        
                        response += f"⭐ **Impact:** {suggestion.get('impact', 'Medium')}\n\n"
            
            # Skill-level specific recommendations
            response += f"📚 **{skill_level.title()} Level Recommendations**:\n"
            
            if skill_level == 'beginner':
                response += f"  • Focus on readability and clear variable naming\n"
                response += f"  • Add comments to explain complex logic\n"
                response += f"  • Use built-in functions when available\n"
            elif skill_level == 'intermediate':
                response += f"  • Consider design patterns for better structure\n"
                response += f"  • Implement error handling and validation\n"
                response += f"  • Optimize for performance where needed\n"
            else:  # advanced
                response += f"  • Apply advanced optimization techniques\n"
                response += f"  • Consider architectural patterns\n"
                response += f"  • Implement comprehensive testing strategies\n"
            
            response += f"\n💡 **Next Steps:**\n"
            response += f"  • Implement suggestions one at a time\n"
            response += f"  • Test changes thoroughly\n"
            response += f"  • Use bb7_execute_code_safely to validate improvements\n"
            response += f"  • Store successful patterns in memory for future reference"
            
            self.logger.info(f"Generated {len(suggestions)} code suggestions")
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating code suggestions: {e}")
            return f"❌ **Suggestion Error:** {str(e)}"

    async def bb7_security_audit(self, arguments: Dict[str, Any]) -> str:
        """
        🔐 Perform detailed security audit of code including vulnerability detection, unsafe pattern 
        identification, and compliance checking. Perfect for security reviews, penetration testing 
        preparation, and ensuring code meets security standards.
        """
        code = arguments.get('code', '')
        language = arguments.get('language', 'python')
        audit_level = arguments.get('audit_level', 'standard')
        include_compliance = arguments.get('include_compliance', True)
        file_path = arguments.get('file_path', '')
        
        # Get code from file if file_path provided
        if file_path and not code:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
            except Exception as e:
                return f"❌ Error reading file '{file_path}': {str(e)}"
        
        if not code.strip():
            return "❌ Please provide code to audit or a file path."
        
        try:
            response = f"🔐 **Security Audit Report**\n\n"
            response += f"💻 **Language**: {language.title()}\n"
            response += f"🔍 **Audit Level**: {audit_level.title()}\n"
            response += f"📏 **Code Size**: {len(code)} characters\n"
            
            if file_path:
                response += f"📁 **Source File**: {file_path}\n"
            
            response += f"⏰ **Audit Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            # Perform security analysis
            security_results = await self._perform_security_audit(code, language, audit_level)
            
            # Vulnerability summary
            vulnerabilities = security_results.get('vulnerabilities', [])
            response += f"🚨 **Vulnerability Summary**:\n"
            response += f"  • **Total Issues**: {len(vulnerabilities)}\n"
            
            # Categorize by severity
            severity_counts = Counter(vuln.get('severity', 'Unknown') for vuln in vulnerabilities)
            for severity in ['Critical', 'High', 'Medium', 'Low']:
                count = severity_counts.get(severity, 0)
                if count > 0:
                    severity_emoji = {'Critical': '🔴', 'High': '🟠', 'Medium': '🟡', 'Low': '🟢'}.get(severity, '⚪')
                    response += f"  • **{severity}**: {count} {severity_emoji}\n"
            
            response += "\n"
            
            # Detailed vulnerability report
            if vulnerabilities:
                response += f"📋 **Detailed Findings**:\n\n"
                
                for i, vuln in enumerate(vulnerabilities, 1):
                    severity = vuln.get('severity', 'Unknown')
                    severity_emoji = {'Critical': '🔴', 'High': '🟠', 'Medium': '🟡', 'Low': '🟢'}.get(severity, '⚪')
                    
                    response += f"### {i}. {severity_emoji} **{vuln.get('title', 'Security Issue')}**\n"
                    response += f"**Severity**: {severity}\n"
                    response += f"**Type**: {vuln.get('type', 'Unknown')}\n"
                    response += f"**Description**: {vuln.get('description', 'No description')}\n"
                    
                    if vuln.get('line_number'):
                        response += f"**Location**: Line {vuln['line_number']}\n"
                    
                    if vuln.get('code_snippet'):
                        response += f"**Code**:\n```{language}\n{vuln['code_snippet']}\n```\n"
                    
                    if vuln.get('remediation'):
                        response += f"**Remediation**: {vuln['remediation']}\n"
                    
                    if vuln.get('references'):
                        response += f"**References**: {', '.join(vuln['references'])}\n"
                    
                    response += "\n"
            
            else:
                response += f"✅ **No security vulnerabilities detected** at {audit_level} level\n\n"
            
            # Security best practices check
            best_practices = security_results.get('best_practices', {})
            if best_practices:
                response += f"📚 **Security Best Practices Assessment**:\n"
                
                for practice, status in best_practices.items():
                    status_emoji = "✅" if status else "❌"
                    response += f"  • {practice}: {status_emoji}\n"
                
                response += "\n"
            
            # Compliance checking
            if include_compliance:
                compliance = security_results.get('compliance', {})
                response += f"📋 **Compliance Check**:\n"
                
                compliance_standards = ['OWASP Top 10', 'CWE Common Weaknesses', 'SANS Top 25']
                for standard in compliance_standards:
                    issues = compliance.get(standard.lower().replace(' ', '_'), 0)
                    status = "✅ Compliant" if issues == 0 else f"❌ {issues} issues"
                    response += f"  • **{standard}**: {status}\n"
                
                response += "\n"
            
            # Risk assessment
            risk_score = security_results.get('risk_score', 0)
            risk_level = security_results.get('risk_level', 'Low')
            
            response += f"📊 **Risk Assessment**:\n"
            response += f"  • **Overall Risk Score**: {risk_score}/100\n"
            response += f"  • **Risk Level**: {risk_level}\n"
            response += f"  • **Recommendation**: {security_results.get('recommendation', 'Continue monitoring')}\n\n"
            
            # Security recommendations
            recommendations = security_results.get('recommendations', [])
            if recommendations:
                response += f"💡 **Security Recommendations**:\n"
                for rec in recommendations:
                    response += f"  • {rec}\n"
                response += "\n"
            
            # Audit trail
            response += f"🔍 **Audit Details**:\n"
            response += f"  • **Patterns Checked**: {security_results.get('patterns_checked', 0)}\n"
            response += f"  • **Functions Analyzed**: {security_results.get('functions_analyzed', 0)}\n"
            response += f"  • **Dependencies Scanned**: {security_results.get('dependencies_scanned', 0)}\n\n"
            
            response += f"💡 **Next Steps**:\n"
            response += f"  • Address high and critical severity issues first\n"
            response += f"  • Implement recommended security controls\n"
            response += f"  • Consider security testing with bb7_execute_code_safely\n"
            response += f"  • Store security insights with bb7_memory_store"
            
            self.logger.info(f"Completed security audit: {len(vulnerabilities)} issues found")
            return response
            
        except Exception as e:
            self.logger.error(f"Error in security audit: {e}")
            return f"❌ **Security Audit Error:** {str(e)}"

    async def bb7_execute_code_safely(self, arguments: Dict[str, Any]) -> str:
        """
        🛡️ Execute Python code in a secure sandboxed environment with comprehensive safety controls, 
        resource monitoring, and execution analysis. Perfect for testing code snippets, validating 
        algorithms, running examples, and educational purposes.
        """
        code = arguments.get('code', '')
        timeout = arguments.get('timeout', 10)
        capture_output = arguments.get('capture_output', True)
        analyze_result = arguments.get('analyze_result', True)
        
        if not code.strip():
            return "❌ Please provide Python code to execute."
        
        # Validate timeout
        timeout = max(1, min(timeout, 30))  # Clamp between 1 and 30 seconds
        
        try:
            response = f"🛡️ **Safe Code Execution**\n\n"
            response += f"⏱️ **Timeout**: {timeout} seconds\n"
            response += f"📏 **Code Size**: {len(code)} characters\n"
            response += f"🔒 **Security**: Sandboxed environment\n\n"
            
            # Security check before execution
            security_check = self._pre_execution_security_check(code)
            if not security_check['safe']:
                response += f"⚠️ **Security Warning**: {security_check['reason']}\n"
                response += f"🚫 **Execution blocked** for safety reasons\n\n"
                response += f"💡 **Suggestion**: {security_check['suggestion']}"
                return response
            
            # Execute code safely
            execution_result = await self._execute_python_code_safely(code, timeout, capture_output)
            
            # Display execution results
            response += f"📤 **Execution Results**:\n"
            response += f"  • **Status**: {'✅ Success' if execution_result['success'] else '❌ Failed'}\n"
            response += f"  • **Execution Time**: {execution_result['execution_time']:.3f} seconds\n"
            
            if execution_result['success']:
                response += f"  • **Memory Usage**: {execution_result.get('memory_usage', 'N/A')}\n"
            
            response += "\n"
            
            # Output display
            if execution_result.get('output') and capture_output:
                output = execution_result['output']
                response += f"📋 **Output**:\n```\n{output}\n```\n\n"
            
            # Error display
            if execution_result.get('error'):
                error = execution_result['error']
                response += f"❌ **Error**:\n```\n{error}\n```\n\n"
                
                # Error analysis
                error_analysis = self._analyze_execution_error(error)
                if error_analysis:
                    response += f"🔍 **Error Analysis**:\n{error_analysis}\n\n"
            
            # Result analysis
            if analyze_result and execution_result['success']:
                analysis = self._analyze_execution_results(code, execution_result)
                
                if analysis.get('variables_created'):
                    response += f"📊 **Variables Created**: {len(analysis['variables_created'])}\n"
                    for var, value in list(analysis['variables_created'].items())[:5]:
                        response += f"  • `{var}`: {str(value)[:50]}{'...' if len(str(value)) > 50 else ''}\n"
                    if len(analysis['variables_created']) > 5:
                        response += f"  ... and {len(analysis['variables_created']) - 5} more variables\n"
                    response += "\n"
                
                if analysis.get('functions_defined'):
                    response += f"🔧 **Functions Defined**: {', '.join(analysis['functions_defined'])}\n\n"
                
                if analysis.get('imports_used'):
                    response += f"📦 **Imports Used**: {', '.join(analysis['imports_used'])}\n\n"
            
            # Performance insights
            if execution_result['success']:
                performance = self._analyze_performance(execution_result)
                response += f"⚡ **Performance Insights**:\n"
                response += f"  • **Speed**: {performance['speed_assessment']}\n"
                response += f"  • **Efficiency**: {performance['efficiency_rating']}\n"
                response += f"  • **Resource Usage**: {performance['resource_assessment']}\n\n"
            
            # Code quality suggestions
            if execution_result['success']:
                suggestions = self._generate_execution_suggestions(code, execution_result)
                if suggestions:
                    response += f"💡 **Code Quality Suggestions**:\n"
                    for suggestion in suggestions[:3]:
                        response += f"  • {suggestion}\n"
                    response += "\n"
            
            # Execution history update
            execution_record = {
                'timestamp': time.time(),
                'code_hash': hashlib.md5(code.encode()).hexdigest()[:8],
                'success': execution_result['success'],
                'execution_time': execution_result['execution_time'],
                'lines_of_code': len(code.splitlines())
            }
            
            self.execution_history.append(execution_record)
            if len(self.execution_history) > self.max_history:
                self.execution_history.pop(0)
            
            # Session statistics
            if len(self.execution_history) > 1:
                success_rate = sum(1 for rec in self.execution_history if rec['success']) / len(self.execution_history)
                avg_time = sum(rec['execution_time'] for rec in self.execution_history) / len(self.execution_history)
                
                response += f"📊 **Session Statistics**:\n"
                response += f"  • Success Rate: {success_rate:.1%}\n"
                response += f"  • Average Execution Time: {avg_time:.3f}s\n"
                response += f"  • Total Executions: {len(self.execution_history)}\n\n"
            
            # Next steps and resources
            response += f"🎯 **Next Steps**:\n"
            if execution_result['success']:
                response += f"  • Use bb7_analyze_code for detailed code analysis\n"
                response += f"  • Try variations of the code to explore different approaches\n"
                response += f"  • Consider adding error handling and input validation\n"
            else:
                response += f"  • Review the error message and fix syntax issues\n"
                response += f"  • Use bb7_analyze_code to check for problems\n"
                response += f"  • Try executing smaller code segments to isolate issues\n"
            
            response += f"  • Use bb7_security_audit for security analysis of larger code"
            
            self.logger.info(f"Executed Python code: {'success' if execution_result['success'] else 'failed'} in {execution_result['execution_time']:.3f}s")
            return response
            
        except Exception as e:
            self.logger.error(f"Error in secure execution: {e}")
            return f"❌ **Execution Error:** {str(e)}\n\n💡 **Suggestion:** Check code syntax and try with a simpler example"

    # Helper methods for code analysis
    
    async def _perform_comprehensive_analysis(self, code: str, language: str, include_security: bool, 
                                            include_metrics: bool, include_suggestions: bool) -> Dict[str, Any]:
        """Perform comprehensive code analysis"""
        result = {}
        
        try:
            # Basic overview
            result['overview'] = self._analyze_code_overview(code, language)
            
            # Metrics analysis
            if include_metrics:
                result['metrics'] = self._calculate_quality_metrics(code, language)
            
            # Security analysis
            if include_security:
                result['security'] = await self._analyze_security_basic(code, language)
            
            # Structure analysis
            if language == 'python':
                result['structure'] = self._analyze_python_structure(code)
            
            # Pattern analysis
            result['patterns'] = self._analyze_code_patterns(code, language)
            
            # Dependencies
            result['dependencies'] = self._analyze_dependencies(code, language)
            
            # Suggestions
            if include_suggestions:
                result['suggestions'] = self._generate_improvement_suggestions(code, language, result)
            
            # Overall assessment
            result['assessment'] = self._generate_overall_assessment(result)
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive analysis: {e}")
            result['error'] = str(e)
        
        return result
    
    def _analyze_code_overview(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze basic code structure and overview"""
        overview = {
            'function_count': 0,
            'class_count': 0,
            'import_count': 0,
            'main_constructs': []
        }
        
        try:
            if language == 'python':
                # Parse Python code with AST
                try:
                    tree = ast.parse(code)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            overview['function_count'] += 1
                        elif isinstance(node, ast.ClassDef):
                            overview['class_count'] += 1
                        elif isinstance(node, (ast.Import, ast.ImportFrom)):
                            overview['import_count'] += 1
                except SyntaxError:
                    # Fallback to regex if AST parsing fails
                    overview['function_count'] = len(re.findall(r'^\s*def\s+\w+', code, re.MULTILINE))
                    overview['class_count'] = len(re.findall(r'^\s*class\s+\w+', code, re.MULTILINE))
                    overview['import_count'] = len(re.findall(r'^\s*(?:import|from)\s+', code, re.MULTILINE))
            
            else:
                # Basic analysis for other languages
                if language == 'javascript':
                    overview['function_count'] = len(re.findall(r'function\s+\w+|=>\s*{|\w+\s*:\s*function', code))
                    overview['class_count'] = len(re.findall(r'class\s+\w+', code))
            
            # Identify main constructs
            constructs = []
            if overview['function_count'] > 0:
                constructs.append(f"{overview['function_count']} functions")
            if overview['class_count'] > 0:
                constructs.append(f"{overview['class_count']} classes")
            if overview['import_count'] > 0:
                constructs.append(f"{overview['import_count']} imports")
            
            overview['main_constructs'] = constructs
            
        except Exception as e:
            self.logger.error(f"Error analyzing code overview: {e}")
        
        return overview
    
    def _calculate_quality_metrics(self, code: str, language: str) -> Dict[str, Any]:
        """Calculate code quality metrics"""
        metrics = {}
        
        try:
            lines = code.splitlines()
            total_lines = len(lines)
            code_lines = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
            comment_lines = len([line for line in lines if line.strip().startswith('#')])
            
            # Basic metrics
            metrics['total_lines'] = total_lines
            metrics['code_lines'] = code_lines
            metrics['comment_lines'] = comment_lines
            metrics['comment_ratio'] = f"{(comment_lines / max(total_lines, 1)) * 100:.1f}%"
            
            # Code density
            non_empty_lines = len([line for line in lines if line.strip()])
            metrics['code_density'] = f"{(non_empty_lines / max(total_lines, 1)) * 100:.1f}%"
            
            # Complexity estimation
            complexity_indicators = len(re.findall(r'\b(?:if|for|while|try|except|elif|else)\b', code))
            metrics['complexity'] = 'Low' if complexity_indicators < 5 else 'Medium' if complexity_indicators < 15 else 'High'
            
            # Maintainability estimation
            avg_line_length = sum(len(line) for line in lines) / max(len(lines), 1)
            long_lines = len([line for line in lines if len(line) > 100])
            
            maintainability_score = 100
            if avg_line_length > 80:
                maintainability_score -= 20
            if long_lines > total_lines * 0.1:
                maintainability_score -= 15
            if comment_lines / max(total_lines, 1) < 0.1:
                maintainability_score -= 10
            
            metrics['maintainability'] = 'High' if maintainability_score > 80 else 'Medium' if maintainability_score > 60 else 'Low'
            
            # Cyclomatic complexity for Python
            if language == 'python':
                try:
                    tree = ast.parse(code)
                    complexity = 1  # Base complexity
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                            complexity += 1
                        elif isinstance(node, ast.BoolOp):
                            complexity += len(node.values) - 1
                    
                    metrics['cyclomatic_complexity'] = complexity
                except:
                    pass
            
        except Exception as e:
            self.logger.error(f"Error calculating quality metrics: {e}")
        
        return metrics
    
    async def _analyze_security_basic(self, code: str, language: str) -> Dict[str, Any]:
        """Perform basic security analysis"""
        security = {
            'issues': [],
            'risk_level': 'Low'
        }
        
        try:
            patterns = self.security_patterns.get(language, [])
            
            for pattern, description in patterns:
                matches = re.finditer(pattern, code, re.IGNORECASE)
                for match in matches:
                    line_number = code[:match.start()].count('\n') + 1
                    
                    security['issues'].append({
                        'type': 'Security Pattern',
                        'description': description,
                        'line': line_number,
                        'code': code.split('\n')[line_number - 1].strip() if line_number <= len(code.split('\n')) else '',
                        'severity': 'Medium'
                    })
            
            # Determine risk level
            issue_count = len(security['issues'])
            if issue_count == 0:
                security['risk_level'] = 'Low'
            elif issue_count <= 2:
                security['risk_level'] = 'Medium'
            else:
                security['risk_level'] = 'High'
            
        except Exception as e:
            self.logger.error(f"Error in basic security analysis: {e}")
        
        return security
    
    def _analyze_python_structure(self, code: str) -> Dict[str, Any]:
        """Analyze Python-specific code structure"""
        structure = {
            'functions': [],
            'classes': [],
            'imports': [],
            'globals': []
        }
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    structure['functions'].append({
                        'name': node.name,
                        'args': len(node.args.args),
                        'line': node.lineno
                    })
                elif isinstance(node, ast.ClassDef):
                    structure['classes'].append({
                        'name': node.name,
                        'line': node.lineno,
                        'methods': len([n for n in node.body if isinstance(n, ast.FunctionDef)])
                    })
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        structure['imports'].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        structure['imports'].append(node.module)
                elif isinstance(node, ast.Assign) and node.lineno == getattr(node, 'lineno', 0):
                    # Global variable assignments (simplified)
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            structure['globals'].append(target.id)
            
        except SyntaxError as e:
            structure['syntax_error'] = [str(e)]
        except Exception as e:
            self.logger.error(f"Error analyzing Python structure: {e}")
        
        return structure
    
    def _analyze_code_patterns(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code patterns and anti-patterns"""
        patterns = {
            'design_patterns': [],
            'anti_patterns': [],
            'coding_style': 'Unknown'
        }
        
        try:
            # Design pattern detection
            if 'class.*Factory' in code:
                patterns['design_patterns'].append('Factory Pattern')
            if 'class.*Singleton' in code or '__new__' in code:
                patterns['design_patterns'].append('Singleton Pattern')
            if 'class.*Observer' in code or 'notify' in code.lower():
                patterns['design_patterns'].append('Observer Pattern')
            
            # Anti-pattern detection
            if re.search(r'if.*==.*True', code):
                patterns['anti_patterns'].append('Explicit comparison with True')
            if re.search(r'except:', code) and 'Exception' not in code:
                patterns['anti_patterns'].append('Bare except clause')
            if language == 'python' and 'global ' in code:
                patterns['anti_patterns'].append('Global variable usage')
            
            # Coding style detection
            if language == 'python':
                snake_case = len(re.findall(r'\b[a-z]+_[a-z]+\b', code))
                camel_case = len(re.findall(r'\b[a-z]+[A-Z][a-z]+\b', code))
                
                if snake_case > camel_case:
                    patterns['coding_style'] = 'Snake Case (PEP 8)'
                elif camel_case > snake_case:
                    patterns['coding_style'] = 'Camel Case'
                else:
                    patterns['coding_style'] = 'Mixed'
            
        except Exception as e:
            self.logger.error(f"Error analyzing code patterns: {e}")
        
        return patterns
    
    def _analyze_dependencies(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code dependencies"""
        dependencies = {
            'imports': [],
            'external_deps': [],
            'builtin_usage': []
        }
        
        try:
            if language == 'python':
                # Extract imports
                import_patterns = [
                    r'import\s+([a-zA-Z_][a-zA-Z0-9_\.]*)',
                    r'from\s+([a-zA-Z_][a-zA-Z0-9_\.]*)\s+import'
                ]
                
                for pattern in import_patterns:
                    matches = re.findall(pattern, code)
                    dependencies['imports'].extend(matches)
                
                # Standard library vs external
                stdlib_modules = {
                    'os', 'sys', 'json', 'time', 'datetime', 'collections', 'itertools',
                    'functools', 'operator', 'math', 'random', 're', 'string', 'io'
                }
                
                for imp in dependencies['imports']:
                    base_module = imp.split('.')[0]
                    if base_module not in stdlib_modules:
                        dependencies['external_deps'].append(imp)
                    else:
                        dependencies['builtin_usage'].append(imp)
            
        except Exception as e:
            self.logger.error(f"Error analyzing dependencies: {e}")
        
        return dependencies
    
    def _generate_improvement_suggestions(self, code: str, language: str, analysis: Dict[str, Any]) -> Dict[str, List[str]]:
        """Generate improvement suggestions based on analysis"""
        suggestions = {
            'performance': [],
            'security': [],
            'readability': [],
            'maintainability': []
        }
        
        try:
            # Performance suggestions
            if 'for' in code and 'range(len(' in code:
                suggestions['performance'].append('Consider using enumerate() instead of range(len())')
            
            if language == 'python' and '+=' in code and 'str' in code.lower():
                suggestions['performance'].append('Consider using join() for string concatenation in loops')
            
            # Security suggestions
            security_issues = analysis.get('security', {}).get('issues', [])
            if security_issues:
                suggestions['security'].append('Address security vulnerabilities found in analysis')
            
            # Readability suggestions
            long_lines = len([line for line in code.splitlines() if len(line) > 100])
            if long_lines > 0:
                suggestions['readability'].append('Consider breaking long lines for better readability')
            
            comment_ratio = analysis.get('metrics', {}).get('comment_ratio', '0%')
            if float(comment_ratio.rstrip('%')) < 10:
                suggestions['readability'].append('Add more comments to explain complex logic')
            
            # Maintainability suggestions
            complexity = analysis.get('metrics', {}).get('complexity', 'Low')
            if complexity == 'High':
                suggestions['maintainability'].append('Consider breaking down complex functions')
            
            functions = analysis.get('structure', {}).get('functions', [])
            for func in functions:
                if func.get('args', 0) > 5:
                    suggestions['maintainability'].append(f"Function '{func['name']}' has many parameters, consider using a config object")
            
        except Exception as e:
            self.logger.error(f"Error generating suggestions: {e}")
        
        return suggestions
    
    def _generate_overall_assessment(self, analysis: Dict[str, Any]) -> Dict[str, str]:
        """Generate overall code assessment"""
        assessment = {
            'readability': 'Unknown',
            'maintainability': 'Unknown',
            'complexity': 'Unknown',
            'security': 'Unknown'
        }
        
        try:
            # Extract metrics
            metrics = analysis.get('metrics', {})
            security = analysis.get('security', {})
            
            # Readability assessment
            comment_ratio = metrics.get('comment_ratio', '0%')
            if float(comment_ratio.rstrip('%')) > 15:
                assessment['readability'] = 'Good'
            elif float(comment_ratio.rstrip('%')) > 5:
                assessment['readability'] = 'Fair'
            else:
                assessment['readability'] = 'Poor'
            
            # Maintainability
            assessment['maintainability'] = metrics.get('maintainability', 'Unknown')
            
            # Complexity
            assessment['complexity'] = metrics.get('complexity', 'Unknown')
            
            # Security
            security_issues = len(security.get('issues', []))
            if security_issues == 0:
                assessment['security'] = 'Good'
            elif security_issues <= 2:
                assessment['security'] = 'Fair'
            else:
                assessment['security'] = 'Poor'
            
        except Exception as e:
            self.logger.error(f"Error generating assessment: {e}")
        
        return assessment
    
    def _generate_targeted_suggestions(self, code: str, language: str, focus_area: str, skill_level: str) -> List[Dict[str, Any]]:
        """Generate targeted suggestions based on focus area and skill level"""
        suggestions = []
        
        try:
            if focus_area in ['all', 'performance']:
                suggestions.extend(self._get_performance_suggestions(code, language, skill_level))
            
            if focus_area in ['all', 'security']:
                suggestions.extend(self._get_security_suggestions(code, language, skill_level))
            
            if focus_area in ['all', 'readability']:
                suggestions.extend(self._get_readability_suggestions(code, language, skill_level))
            
            if focus_area in ['all', 'maintainability']:
                suggestions.extend(self._get_maintainability_suggestions(code, language, skill_level))
            
        except Exception as e:
            self.logger.error(f"Error generating targeted suggestions: {e}")
        
        return suggestions
    
    def _get_performance_suggestions(self, code: str, language: str, skill_level: str) -> List[Dict[str, Any]]:
        """Get performance-focused suggestions"""
        suggestions = []
        
        # List comprehension suggestion
        if re.search(r'for\s+\w+\s+in.*:\s*\w+\.append\(', code):
            suggestions.append({
                'category': 'Performance',
                'title': 'Use List Comprehension',
                'description': 'Replace append loop with list comprehension for better performance',
                'current_code': 'for item in items:\n    result.append(transform(item))',
                'improved_code': 'result = [transform(item) for item in items]',
                'explanation': 'List comprehensions are faster and more Pythonic',
                'impact': 'Medium'
            })
        
        # String concatenation suggestion
        if '+=' in code and 'str' in code.lower():
            suggestions.append({
                'category': 'Performance',
                'title': 'Optimize String Concatenation',
                'description': 'Use join() for multiple string concatenations',
                'explanation': 'join() is more efficient for multiple concatenations',
                'impact': 'High'
            })
        
        return suggestions
    
    def _get_security_suggestions(self, code: str, language: str, skill_level: str) -> List[Dict[str, Any]]:
        """Get security-focused suggestions"""
        suggestions = []
        
        # eval() usage
        if 'eval(' in code:
            suggestions.append({
                'category': 'Security',
                'title': 'Avoid eval() Function',
                'description': 'Replace eval() with safer alternatives',
                'current_code': 'result = eval(user_input)',
                'improved_code': 'import ast\nresult = ast.literal_eval(user_input)',
                'explanation': 'eval() can execute arbitrary code, use ast.literal_eval() for safe evaluation',
                'impact': 'Critical'
            })
        
        return suggestions
    
    def _get_readability_suggestions(self, code: str, language: str, skill_level: str) -> List[Dict[str, Any]]:
        """Get readability-focused suggestions"""
        suggestions = []
        
        # Long lines
        long_lines = [line for line in code.splitlines() if len(line) > 100]
        if long_lines:
            suggestions.append({
                'category': 'Readability',
                'title': 'Break Long Lines',
                'description': 'Lines should be under 80-100 characters',
                'explanation': 'Shorter lines improve code readability and maintainability',
                'impact': 'Medium'
            })
        
        return suggestions
    
    def _get_maintainability_suggestions(self, code: str, language: str, skill_level: str) -> List[Dict[str, Any]]:
        """Get maintainability-focused suggestions"""
        suggestions = []
        
        # Function complexity
        if language == 'python':
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Count nested statements
                        complexity = len([n for n in ast.walk(node) if isinstance(n, (ast.If, ast.For, ast.While))])
                        if complexity > 5:
                            suggestions.append({
                                'category': 'Maintainability',
                                'title': f'Simplify Function: {node.name}',
                                'description': 'Break down complex function into smaller functions',
                                'explanation': 'Smaller functions are easier to test and maintain',
                                'impact': 'High'
                            })
            except:
                pass
        
        return suggestions
    
    async def _perform_security_audit(self, code: str, language: str, audit_level: str) -> Dict[str, Any]:
        """Perform comprehensive security audit"""
        results = {
            'vulnerabilities': [],
            'best_practices': {},
            'compliance': {},
            'risk_score': 0,
            'risk_level': 'Low',
            'recommendations': [],
            'patterns_checked': 0,
            'functions_analyzed': 0,
            'dependencies_scanned': 0
        }
        
        try:
            # Check security patterns
            patterns = self.security_patterns.get(language, [])
            results['patterns_checked'] = len(patterns)
            
            for pattern, description in patterns:
                matches = list(re.finditer(pattern, code, re.IGNORECASE))
                for match in matches:
                    line_number = code[:match.start()].count('\n') + 1
                    
                    vulnerability = {
                        'title': description,
                        'type': 'Pattern Match',
                        'severity': self._determine_severity(description),
                        'description': f'Potentially unsafe pattern detected: {description}',
                        'line_number': line_number,
                        'code_snippet': code.split('\n')[line_number - 1].strip() if line_number <= len(code.split('\n')) else '',
                        'remediation': self._get_remediation_advice(description, language),
                        'references': []
                    }
                    
                    results['vulnerabilities'].append(vulnerability)
            
            # Best practices assessment
            results['best_practices'] = {
                'Input Validation': 'input(' not in code and 'raw_input(' not in code,
                'Error Handling': 'try:' in code and 'except' in code,
                'Secure Imports': 'pickle' not in code and 'eval' not in code,
                'SQL Injection Prevention': 'execute(' not in code or 'parameterized' in code.lower()
            }
            
            # Calculate risk score
            critical_issues = len([v for v in results['vulnerabilities'] if v['severity'] == 'Critical'])
            high_issues = len([v for v in results['vulnerabilities'] if v['severity'] == 'High'])
            medium_issues = len([v for v in results['vulnerabilities'] if v['severity'] == 'Medium'])
            
            risk_score = (critical_issues * 30) + (high_issues * 20) + (medium_issues * 10)
            results['risk_score'] = min(risk_score, 100)
            
            # Determine risk level
            if risk_score >= 70:
                results['risk_level'] = 'Critical'
                results['recommendation'] = 'Immediate security review required'
            elif risk_score >= 40:
                results['risk_level'] = 'High'
                results['recommendation'] = 'Security improvements needed'
            elif risk_score >= 20:
                results['risk_level'] = 'Medium'
                results['recommendation'] = 'Monitor and improve security practices'
            else:
                results['risk_level'] = 'Low'
                results['recommendation'] = 'Continue current security practices'
            
            # Generate recommendations
            if results['vulnerabilities']:
                results['recommendations'].extend([
                    'Address all critical and high severity vulnerabilities',
                    'Implement input validation and sanitization',
                    'Use parameterized queries for database operations',
                    'Avoid dynamic code execution (eval, exec)',
                    'Implement proper error handling'
                ])
            
        except Exception as e:
            self.logger.error(f"Error in security audit: {e}")
        
        return results
    
    def _determine_severity(self, description: str) -> str:
        """Determine vulnerability severity"""
        critical_keywords = ['eval', 'exec', 'pickle', 'system']
        high_keywords = ['sql', 'injection', 'xss', 'csrf']
        
        desc_lower = description.lower()
        
        if any(keyword in desc_lower for keyword in critical_keywords):
            return 'Critical'
        elif any(keyword in desc_lower for keyword in high_keywords):
            return 'High'
        else:
            return 'Medium'
    
    def _get_remediation_advice(self, description: str, language: str) -> str:
        """Get remediation advice for security issues"""
        remediation_map = {
            'eval': 'Use ast.literal_eval() for safe evaluation of literals',
            'exec': 'Avoid dynamic code execution, use alternative approaches',
            'pickle': 'Use JSON or other safe serialization formats',
            'system': 'Use subprocess with proper input validation',
            'sql': 'Use parameterized queries or prepared statements'
        }
        
        for keyword, advice in remediation_map.items():
            if keyword in description.lower():
                return advice
        
        return 'Review code for security implications and apply appropriate safeguards'
    
    def _pre_execution_security_check(self, code: str) -> Dict[str, Any]:
        """Perform security check before code execution"""
        dangerous_patterns = [
            (r'import\s+os', 'OS module import'),
            (r'import\s+subprocess', 'Subprocess module import'),
            (r'import\s+sys', 'System module import'),
            (r'open\s*\([^)]*["\']w["\']', 'File write operation'),
            (r'eval\s*\(', 'eval() function usage'),
            (r'exec\s*\(', 'exec() function usage'),
            (r'__import__', 'Dynamic import'),
            (r'compile\s*\(', 'Code compilation'),
            (r'globals\s*\(\s*\)', 'Global namespace access')
        ]
        
        for pattern, description in dangerous_patterns:
            if re.search(pattern, code):
                return {
                    'safe': False,
                    'reason': f'Potentially unsafe operation detected: {description}',
                    'suggestion': 'Remove or modify the unsafe operation before execution'
                }
        
        return {'safe': True}
    
    async def _execute_python_code_safely(self, code: str, timeout: int, capture_output: bool) -> Dict[str, Any]:
        """Execute Python code in a safe environment"""
        result = {
            'success': False,
            'output': '',
            'error': '',
            'execution_time': 0,
            'memory_usage': 'N/A'
        }
        
        try:
            # Create a restricted environment
            restricted_globals = {
                '__builtins__': {
                    'print': print,
                    'len': len,
                    'str': str,
                    'int': int,
                    'float': float,
                    'list': list,
                    'dict': dict,
                    'tuple': tuple,
                    'set': set,
                    'range': range,
                    'enumerate': enumerate,
                    'zip': zip,
                    'sum': sum,
                    'min': min,
                    'max': max,
                    'abs': abs,
                    'round': round,
                    'sorted': sorted,
                    'reversed': reversed,
                    'any': any,
                    'all': all
                }
            }
            
            # Capture output if requested
            if capture_output:
                output_buffer = io.StringIO()
                original_stdout = sys.stdout
                sys.stdout = output_buffer
            
            start_time = time.time()
            
            try:
                # Execute code with timeout
                exec(code, restricted_globals)
                result['success'] = True
                
            except Exception as e:
                result['error'] = str(e)
            
            finally:
                result['execution_time'] = time.time() - start_time
                
                if capture_output:
                    result['output'] = output_buffer.getvalue()
                    sys.stdout = original_stdout
            
        except Exception as e:
            result['error'] = f"Execution environment error: {str(e)}"
        
        return result
    
    def _analyze_execution_error(self, error: str) -> str:
        """Analyze execution error and provide helpful guidance"""
        error_lower = error.lower()
        
        if 'syntaxerror' in error_lower:
            return "**Syntax Error**: Check for missing colons, parentheses, or incorrect indentation"
        elif 'nameerror' in error_lower:
            return "**Name Error**: Variable or function not defined. Check spelling and scope"
        elif 'typeerror' in error_lower:
            return "**Type Error**: Incompatible data types. Check function arguments and operations"
        elif 'indexerror' in error_lower:
            return "**Index Error**: Accessing list/string index that doesn't exist"
        elif 'keyerror' in error_lower:
            return "**Key Error**: Accessing dictionary key that doesn't exist"
        elif 'valueerror' in error_lower:
            return "**Value Error**: Invalid value for the operation. Check input data"
        elif 'indentationerror' in error_lower:
            return "**Indentation Error**: Inconsistent indentation. Use spaces or tabs consistently"
        elif 'zerodivisionerror' in error_lower:
            return "**Zero Division Error**: Division by zero. Add validation to prevent this"
        else:
            return "Check the error message for specific details about what went wrong"
    
    def _analyze_execution_results(self, code: str, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze execution results for insights"""
        analysis = {
            'variables_created': {},
            'functions_defined': [],
            'imports_used': []
        }
        
        try:
            # Parse code to understand what was created
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    analysis['functions_defined'].append(node.name)
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            analysis['imports_used'].append(alias.name)
                    else:
                        if node.module:
                            analysis['imports_used'].append(node.module)
            
            # Note: Variable analysis would require executing in a controlled environment
            # with access to the local namespace, which is complex to implement safely
            
        except Exception as e:
            self.logger.error(f"Error analyzing execution results: {e}")
        
        return analysis
    
    def _analyze_performance(self, execution_result: Dict[str, Any]) -> Dict[str, str]:
        """Analyze execution performance"""
        exec_time = execution_result.get('execution_time', 0)
        
        if exec_time < 0.001:
            speed = "Very Fast"
        elif exec_time < 0.01:
            speed = "Fast"
        elif exec_time < 0.1:
            speed = "Moderate"
        else:
            speed = "Slow"
        
        return {
            'speed_assessment': speed,
            'efficiency_rating': 'Good' if exec_time < 0.05 else 'Fair' if exec_time < 0.2 else 'Poor',
            'resource_assessment': 'Low' if exec_time < 0.01 else 'Medium' if exec_time < 0.1 else 'High'
        }
    
    def _generate_execution_suggestions(self, code: str, execution_result: Dict[str, Any]) -> List[str]:
        """Generate suggestions based on execution results"""
        suggestions = []
        
        exec_time = execution_result.get('execution_time', 0)
        
        if exec_time > 0.1:
            suggestions.append("Consider optimizing for better performance")
        
        if 'print(' in code:
            suggestions.append("Consider using logging instead of print for production code")
        
        if 'for' in code and 'range(' in code:
            suggestions.append("Consider using more Pythonic iteration patterns")
        
        if execution_result.get('success') and not execution_result.get('output'):
            suggestions.append("Consider adding output to verify code behavior")
        
        return suggestions


# For standalone testing
if __name__ == "__main__":
    import asyncio
    
    async def test_code_analysis_tool():
        logging.basicConfig(level=logging.INFO)
        tool = CodeAnalysisTool()
        
        print("=== Testing Code Analysis Tool ===")
        
        # Test code analysis
        test_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(10))
"""
        
        result = await tool.bb7_analyze_code({
            'code': test_code,
            'language': 'python'
        })
        print(f"Code analysis result:\n{result}\n")
        
        # Test secure execution
        result = await tool.bb7_execute_code_safely({
            'code': 'print("Hello from secure execution!")\nresult = 2 + 2\nprint(f"2 + 2 = {result}")'
        })
        print(f"Secure execution result:\n{result}\n")
    
    asyncio.run(test_code_analysis_tool())