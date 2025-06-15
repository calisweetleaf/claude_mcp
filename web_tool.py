#!/usr/bin/env python3
"""
Web Tool - Advanced web content fetching and analysis for MCP Server

This tool provides comprehensive web interaction capabilities including
URL fetching, content analysis, search functionality, and intelligent
extraction. Optimized for GitHub Copilot agent mode with safety controls
and smart content processing.
"""

import asyncio
import logging
import re
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urljoin, urlparse, quote_plus
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import html
import xml.etree.ElementTree as ET


class WebTool:
    """
    Advanced web content fetching and analysis with intelligent processing
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache_dir = Path("data/web_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Web request settings
        self.default_timeout = 30
        self.max_content_size = 10 * 1024 * 1024  # 10MB limit
        self.user_agent = "Mozilla/5.0 (compatible; MCP-WebTool/1.0; Development Assistant)"
        
        # Content type handlers
        self.supported_content_types = {
            'text/html', 'text/plain', 'application/json', 'application/xml',
            'text/xml', 'application/rss+xml', 'application/atom+xml',
            'text/css', 'application/javascript', 'text/javascript'
        }
        
        # Search engines configuration
        self.search_engines = {
            'duckduckgo': 'https://duckduckgo.com/html/?q={}',
            'github': 'https://github.com/search?q={}&type=repositories',
            'stackoverflow': 'https://stackoverflow.com/search?q={}',
            'docs': 'https://docs.python.org/3/search.html?q={}'
        }
        
        self.logger.info("Web tool initialized with content analysis capabilities")
    
    async def bb7_fetch_url(self, arguments: Dict[str, Any]) -> str:
        """
        🌐 Fetch and intelligently analyze web content from any URL with automatic content type detection,
        smart text extraction, and comprehensive metadata analysis. Perfect for documentation research,
        API exploration, content analysis, and gathering information from web resources. Provides 
        structured output with actionable insights and extracted key information.
        """
        url = arguments.get('url', '')
        extract_text = arguments.get('extract_text', True)
        follow_redirects = arguments.get('follow_redirects', True)
        include_metadata = arguments.get('include_metadata', True)
        save_content = arguments.get('save_content', False)
        
        if not url:
            return "❌ Please provide a URL to fetch. Example: https://example.com or https://docs.python.org"
        
        # Validate and normalize URL
        normalized_url = self._normalize_url(url)
        if not normalized_url:
            return f"❌ Invalid URL format: '{url}'. Please provide a valid HTTP/HTTPS URL."
        
        try:
            start_time = time.time()
            
            # Fetch content
            content_info = await self._fetch_web_content(
                normalized_url, 
                follow_redirects=follow_redirects
            )
            
            fetch_time = time.time() - start_time
            
            # Build response
            response = f"🌐 **Web Content Retrieved:** `{normalized_url}`\n\n"
            
            # Basic info
            response += f"📊 **Fetch Statistics:**\n"
            response += f"  • Status: {content_info['status_code']}\n"
            response += f"  • Content Type: {content_info['content_type']}\n"
            response += f"  • Content Length: {self._format_bytes(content_info['content_length'])}\n"
            response += f"  • Fetch Time: {fetch_time:.2f}s\n"
            
            if content_info.get('final_url') != normalized_url:
                response += f"  • Redirected to: {content_info['final_url']}\n"
            
            response += "\n"
            
            # Metadata analysis
            if include_metadata and content_info.get('metadata'):
                metadata = content_info['metadata']
                response += f"🔍 **Page Metadata:**\n"
                
                if metadata.get('title'):
                    response += f"  • Title: {metadata['title']}\n"
                
                if metadata.get('description'):
                    response += f"  • Description: {metadata['description'][:200]}{'...' if len(metadata['description']) > 200 else ''}\n"
                
                if metadata.get('keywords'):
                    response += f"  • Keywords: {', '.join(metadata['keywords'][:10])}\n"
                
                if metadata.get('author'):
                    response += f"  • Author: {metadata['author']}\n"
                
                if metadata.get('lang'):
                    response += f"  • Language: {metadata['lang']}\n"
                
                response += "\n"
            
            # Content analysis
            content_analysis = await self._analyze_web_content(content_info)
            if content_analysis:
                response += f"🔬 **Content Analysis:**\n"
                for insight in content_analysis:
                    response += f"  • {insight}\n"
                response += "\n"
            
            # Extract and display content
            if extract_text and content_info.get('content'):
                extracted_content = await self._extract_readable_content(
                    content_info['content'], 
                    content_info['content_type']
                )
                
                if extracted_content:
                    response += f"📄 **Extracted Content:**\n"
                    
                    # Smart content preview
                    if len(extracted_content) > 3000:
                        response += f"```\n{extracted_content[:3000]}\n...\n```\n\n"
                        response += f"💡 **Note:** Content truncated to 3000 characters. Full content has {len(extracted_content):,} characters.\n"
                    else:
                        response += f"```\n{extracted_content}\n```\n"
                    
                    # Content insights
                    content_insights = self._get_content_insights(extracted_content, content_info['content_type'])
                    if content_insights:
                        response += f"\n📈 **Content Insights:**\n"
                        for insight in content_insights:
                            response += f"  • {insight}\n"
                else:
                    response += f"📄 **Content:** Unable to extract readable text from this content type\n"
            
            # Save content if requested
            if save_content and content_info.get('content'):
                saved_path = await self._save_cached_content(normalized_url, content_info)
                if saved_path:
                    response += f"\n💾 **Saved Content:** {saved_path}\n"
            
            # Related actions and suggestions
            suggestions = self._get_action_suggestions(content_info, normalized_url)
            if suggestions:
                response += f"\n💡 **Suggested Actions:**\n"
                for suggestion in suggestions:
                    response += f"  • {suggestion}\n"
            
            self.logger.info(f"Successfully fetched URL: {normalized_url} ({content_info['content_length']} bytes)")
            return response
            
        except HTTPError as e:
            error_analysis = self._analyze_http_error(e.code, str(e))
            return f"❌ **HTTP Error {e.code}:** {error_analysis['message']}\n\n💡 **Suggestion:** {error_analysis['suggestion']}"
        
        except URLError as e:
            return f"❌ **Network Error:** Unable to reach '{url}'\n\n💡 **Suggestions:**\n  • Check your internet connection\n  • Verify the URL is correct\n  • Try again in a few moments"
        
        except Exception as e:
            self.logger.error(f"Error fetching URL '{url}': {e}")
            return f"❌ **Fetch Error:** {str(e)}\n\n💡 **Suggestion:** Verify the URL format and try again"
    
    async def bb7_search_web(self, arguments: Dict[str, Any]) -> str:
        """
        🔍 Search the web using multiple search engines with intelligent result aggregation and analysis.
        Perfect for research, finding documentation, discovering code examples, and gathering information
        on development topics. Provides ranked results with content previews and actionable insights
        for each found resource.
        """
        query = arguments.get('query', '')
        search_engine = arguments.get('search_engine', 'duckduckgo')
        max_results = arguments.get('max_results', 10)
        include_snippets = arguments.get('include_snippets', True)
        
        if not query:
            return "❌ Please provide a search query. Example: 'Python async programming' or 'React hooks tutorial'"
        
        if search_engine not in self.search_engines:
            available_engines = ', '.join(self.search_engines.keys())
            return f"❌ Search engine '{search_engine}' not supported. Available: {available_engines}"
        
        try:
            start_time = time.time()
            
            # Perform search
            search_results = await self._perform_web_search(query, search_engine, max_results)
            
            search_time = time.time() - start_time
            
            if not search_results:
                return f"🔍 **Search Results:** No results found for '{query}' using {search_engine}\n\n💡 **Suggestions:**\n  • Try different keywords\n  • Use a different search engine\n  • Check spelling and try broader terms"
            
            # Build response
            response = f"🔍 **Web Search Results:** '{query}'\n"
            response += f"🔧 **Search Engine:** {search_engine}\n"
            response += f"📊 **Found:** {len(search_results)} results in {search_time:.2f}s\n\n"
            
            # Display results
            for i, result in enumerate(search_results, 1):
                response += f"**{i}. {result['title']}**\n"
                response += f"🔗 {result['url']}\n"
                
                if result.get('description') and include_snippets:
                    description = result['description'][:300]
                    response += f"📝 {description}{'...' if len(result['description']) > 300 else ''}\n"
                
                # Content type detection
                if result.get('content_type'):
                    response += f"📄 Type: {result['content_type']}\n"
                
                # Relevance scoring
                if result.get('relevance_score'):
                    score_emoji = "🔥" if result['relevance_score'] > 0.8 else "⭐" if result['relevance_score'] > 0.6 else "📌"
                    response += f"{score_emoji} Relevance: {result['relevance_score']:.1f}\n"
                
                response += "\n"
            
            # Search insights and recommendations
            insights = self._analyze_search_results(search_results, query)
            if insights:
                response += f"🔍 **Search Insights:**\n"
                for insight in insights:
                    response += f"  • {insight}\n"
                response += "\n"
            
            # Related search suggestions
            related_queries = self._generate_related_queries(query, search_results)
            if related_queries:
                response += f"🔗 **Related Searches:**\n"
                for related_query in related_queries[:5]:
                    response += f"  • {related_query}\n"
                response += "\n"
            
            response += f"💡 **Tips:**\n"
            response += f"  • Use bb7_fetch_url to get full content from specific results\n"
            response += f"  • Try different search engines for varied perspectives\n"
            response += f"  • Refine your query for more specific results"
            
            self.logger.info(f"Web search for '{query}': {len(search_results)} results")
            return response
            
        except Exception as e:
            self.logger.error(f"Error performing web search for '{query}': {e}")
            return f"❌ **Search Error:** {str(e)}\n\n💡 **Suggestion:** Try a different search engine or check your network connection"
    
    async def bb7_analyze_webpage(self, arguments: Dict[str, Any]) -> str:
        """
        🔬 Perform comprehensive analysis of webpage structure, content quality, SEO factors, and 
        technical characteristics. Perfect for web development, content auditing, competitor analysis,
        and understanding webpage architecture. Provides detailed insights into page performance,
        accessibility, and optimization opportunities.
        """
        url = arguments.get('url', '')
        include_links = arguments.get('include_links', True)
        include_images = arguments.get('include_images', True)
        include_scripts = arguments.get('include_scripts', False)
        analyze_seo = arguments.get('analyze_seo', True)
        
        if not url:
            return "❌ Please provide a URL to analyze. Example: https://example.com"
        
        # Validate URL
        normalized_url = self._normalize_url(url)
        if not normalized_url:
            return f"❌ Invalid URL format: '{url}'"
        
        try:
            # Fetch webpage content
            content_info = await self._fetch_web_content(normalized_url, follow_redirects=True)
            
            if content_info['content_type'] not in ['text/html', 'application/xhtml+xml']:
                return f"❌ URL does not point to a webpage (content type: {content_info['content_type']})"
            
            # Parse HTML content
            html_analysis = await self._analyze_html_structure(content_info['content'])
            
            # Build comprehensive analysis response
            response = f"🔬 **Webpage Analysis:** `{normalized_url}`\n\n"
            
            # Basic page information
            response += f"📊 **Page Overview:**\n"
            response += f"  • Status: {content_info['status_code']}\n"
            response += f"  • Content Length: {self._format_bytes(content_info['content_length'])}\n"
            response += f"  • Content Type: {content_info['content_type']}\n"
            
            if html_analysis.get('title'):
                response += f"  • Title: {html_analysis['title']}\n"
            
            if html_analysis.get('lang'):
                response += f"  • Language: {html_analysis['lang']}\n"
            
            response += "\n"
            
            # HTML structure analysis
            structure = html_analysis.get('structure', {})
            if structure:
                response += f"🏗️ **HTML Structure:**\n"
                response += f"  • HTML Elements: {structure.get('total_elements', 0)}\n"
                response += f"  • Text Content: {structure.get('text_length', 0)} characters\n"
                response += f"  • Headings: {structure.get('heading_count', 0)} (H1: {structure.get('h1_count', 0)})\n"
                response += f"  • Paragraphs: {structure.get('paragraph_count', 0)}\n"
                response += f"  • Forms: {structure.get('form_count', 0)}\n"
                response += f"  • Tables: {structure.get('table_count', 0)}\n"
                response += "\n"
            
            # Links analysis
            if include_links and html_analysis.get('links'):
                links = html_analysis['links']
                response += f"🔗 **Links Analysis:**\n"
                response += f"  • Total Links: {len(links['all'])}\n"
                response += f"  • Internal Links: {len(links['internal'])}\n"
                response += f"  • External Links: {len(links['external'])}\n"
                response += f"  • Email Links: {len(links['mailto'])}\n"
                
                if links['external']:
                    response += f"  • Top External Domains:\n"
                    domain_counts = {}
                    for link in links['external']:
                        domain = urlparse(link).netloc
                        domain_counts[domain] = domain_counts.get(domain, 0) + 1
                    
                    for domain, count in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                        response += f"    - {domain}: {count} links\n"
                
                response += "\n"
            
            # Images analysis
            if include_images and html_analysis.get('images'):
                images = html_analysis['images']
                response += f"🖼️ **Images Analysis:**\n"
                response += f"  • Total Images: {len(images)}\n"
                
                images_with_alt = [img for img in images if img.get('alt')]
                response += f"  • Images with Alt Text: {len(images_with_alt)} ({(len(images_with_alt)/len(images)*100):.1f}%)\n"
                
                if images:
                    avg_alt_length = sum(len(img.get('alt', '')) for img in images) / len(images)
                    response += f"  • Average Alt Text Length: {avg_alt_length:.1f} characters\n"
                
                response += "\n"
            
            # Scripts and resources analysis
            if include_scripts and html_analysis.get('scripts'):
                scripts = html_analysis['scripts']
                response += f"⚙️ **Scripts & Resources:**\n"
                response += f"  • Script Tags: {len(scripts['script_tags'])}\n"
                response += f"  • External Scripts: {len(scripts['external_scripts'])}\n"
                response += f"  • Inline Scripts: {len(scripts['inline_scripts'])}\n"
                response += f"  • CSS Files: {len(scripts['css_files'])}\n"
                response += "\n"
            
            # SEO analysis
            if analyze_seo:
                seo_analysis = self._analyze_seo_factors(html_analysis, content_info)
                response += f"🎯 **SEO Analysis:**\n"
                
                # SEO score calculation
                seo_score = seo_analysis.get('score', 0)
                score_emoji = "🔥" if seo_score > 80 else "⭐" if seo_score > 60 else "⚠️" if seo_score > 40 else "❌"
                response += f"  • SEO Score: {score_emoji} {seo_score}/100\n"
                
                # SEO factors
                factors = seo_analysis.get('factors', {})
                for factor, status in factors.items():
                    status_emoji = "✅" if status['status'] == 'good' else "⚠️" if status['status'] == 'warning' else "❌"
                    response += f"  • {factor}: {status_emoji} {status['message']}\n"
                
                # SEO recommendations
                recommendations = seo_analysis.get('recommendations', [])
                if recommendations:
                    response += f"\n💡 **SEO Recommendations:**\n"
                    for rec in recommendations:
                        response += f"  • {rec}\n"
                
                response += "\n"
            
            # Technical analysis
            tech_analysis = self._analyze_technical_aspects(content_info, html_analysis)
            if tech_analysis:
                response += f"⚙️ **Technical Analysis:**\n"
                for aspect in tech_analysis:
                    response += f"  • {aspect}\n"
                response += "\n"
            
            # Performance insights
            performance_insights = self._get_performance_insights(content_info, html_analysis)
            if performance_insights:
                response += f"📈 **Performance Insights:**\n"
                for insight in performance_insights:
                    response += f"  • {insight}\n"
                response += "\n"
            
            # Accessibility considerations
            accessibility_analysis = self._analyze_accessibility(html_analysis)
            if accessibility_analysis:
                response += f"♿ **Accessibility Analysis:**\n"
                for finding in accessibility_analysis:
                    response += f"  • {finding}\n"
                response += "\n"
            
            response += f"💡 **Suggestions:**\n"
            response += f"  • Use bb7_fetch_url to get specific page content\n"
            response += f"  • Compare with competitor pages for benchmarking\n"
            response += f"  • Monitor page changes over time for optimization tracking"
            
            self.logger.info(f"Completed webpage analysis for: {normalized_url}")
            return response
            
        except Exception as e:
            self.logger.error(f"Error analyzing webpage '{url}': {e}")
            return f"❌ **Analysis Error:** {str(e)}\n\n💡 **Suggestion:** Verify the URL is accessible and try again"
    
    async def bb7_download_file(self, arguments: Dict[str, Any]) -> str:
        """
        📥 Download files from web URLs with intelligent handling of different content types, 
        progress tracking, and automatic organization. Perfect for downloading documentation, 
        code samples, data files, and other web resources. Provides safety checks and 
        comprehensive download management with metadata preservation.
        """
        url = arguments.get('url', '')
        filename = arguments.get('filename', '')
        destination = arguments.get('destination', 'downloads')
        max_size = arguments.get('max_size', 100 * 1024 * 1024)  # 100MB default
        overwrite = arguments.get('overwrite', False)
        
        if not url:
            return "❌ Please provide a URL to download from. Example: https://example.com/file.pdf"
        
        # Validate URL
        normalized_url = self._normalize_url(url)
        if not normalized_url:
            return f"❌ Invalid URL format: '{url}'"
        
        try:
            # Create destination directory
            dest_path = Path(destination)
            dest_path.mkdir(parents=True, exist_ok=True)
            
            # Determine filename if not provided
            if not filename:
                filename = self._extract_filename_from_url(normalized_url)
                if not filename:
                    filename = f"download_{int(time.time())}"
            
            file_path = dest_path / filename
            
            # Check if file exists
            if file_path.exists() and not overwrite:
                return f"❌ File '{file_path}' already exists. Use overwrite=true to replace it."
            
            # Get file info first
            file_info = await self._get_file_info(normalized_url)
            
            # Size check
            if file_info.get('content_length', 0) > max_size:
                size_str = self._format_bytes(file_info['content_length'])
                max_size_str = self._format_bytes(max_size)
                return f"❌ File size ({size_str}) exceeds maximum allowed size ({max_size_str})"
            
            # Perform download
            start_time = time.time()
            download_result = await self._download_file_content(normalized_url, file_path)
            download_time = time.time() - start_time
            
            # Build response
            response = f"📥 **File Downloaded Successfully**\n\n"
            response += f"🔗 **Source:** {normalized_url}\n"
            response += f"💾 **Saved to:** {file_path}\n"
            response += f"📊 **File Size:** {self._format_bytes(download_result['file_size'])}\n"
            response += f"⏱️ **Download Time:** {download_time:.2f}s\n"
            response += f"📈 **Speed:** {self._format_bytes(download_result['file_size'] / download_time)}/s\n"
            
            if download_result.get('content_type'):
                response += f"📄 **Content Type:** {download_result['content_type']}\n"
            
            # File analysis
            file_analysis = self._analyze_downloaded_file(file_path, download_result)
            if file_analysis:
                response += f"\n🔍 **File Analysis:**\n"
                for analysis in file_analysis:
                    response += f"  • {analysis}\n"
            
            # Security considerations
            security_check = self._check_file_security(file_path, download_result)
            if security_check:
                response += f"\n🔐 **Security Notes:**\n"
                for note in security_check:
                    response += f"  • {note}\n"
            
            # Usage suggestions
            suggestions = self._get_file_usage_suggestions(file_path, download_result)
            if suggestions:
                response += f"\n💡 **Usage Suggestions:**\n"
                for suggestion in suggestions:
                    response += f"  • {suggestion}\n"
            
            self.logger.info(f"Downloaded file: {normalized_url} -> {file_path} ({download_result['file_size']} bytes)")
            return response
            
        except Exception as e:
            self.logger.error(f"Error downloading file from '{url}': {e}")
            return f"❌ **Download Error:** {str(e)}\n\n💡 **Suggestions:**\n  • Check URL accessibility\n  • Verify sufficient disk space\n  • Try a smaller file first"
    
    # Helper methods for web operations
    def _normalize_url(self, url: str) -> Optional[str]:
        """Normalize and validate URL"""
        url = url.strip()
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Basic URL validation
        try:
            parsed = urlparse(url)
            if not parsed.netloc:
                return None
            return url
        except Exception:
            return None
    
    async def _fetch_web_content(self, url: str, follow_redirects: bool = True) -> Dict[str, Any]:
        """Fetch web content with comprehensive metadata"""
        request = Request(url, headers={'User-Agent': self.user_agent})
        
        with urlopen(request, timeout=self.default_timeout) as response:
            # Get response metadata
            content_type = response.headers.get('Content-Type', '').split(';')[0]
            content_length = int(response.headers.get('Content-Length', 0))
            
            # Size check
            if content_length > self.max_content_size:
                raise ValueError(f"Content too large: {content_length} bytes")
            
            # Read content
            content = response.read()
            actual_length = len(content)
            
            # Decode text content
            if content_type.startswith('text/'):
                encoding = 'utf-8'
                charset_match = re.search(r'charset=([^;\s]+)', response.headers.get('Content-Type', ''))
                if charset_match:
                    encoding = charset_match.group(1)
                
                try:
                    content = content.decode(encoding)
                except UnicodeDecodeError:
                    content = content.decode('utf-8', errors='replace')
            
            # Extract metadata for HTML content
            metadata = {}
            if content_type == 'text/html' and isinstance(content, str):
                metadata = self._extract_html_metadata(content)
            
            return {
                'content': content,
                'content_type': content_type,
                'content_length': actual_length,
                'status_code': response.status,
                'final_url': response.url,
                'headers': dict(response.headers),
                'metadata': metadata
            }
    
    def _extract_html_metadata(self, html_content: str) -> Dict[str, Any]:
        """Extract metadata from HTML content"""
        metadata = {}
        
        # Title
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
        if title_match:
            metadata['title'] = html.unescape(title_match.group(1).strip())
        
        # Meta tags
        meta_pattern = r'<meta\s+([^>]+)>'
        for meta_match in re.finditer(meta_pattern, html_content, re.IGNORECASE):
            meta_attrs = meta_match.group(1)
            
            # Extract name and content
            name_match = re.search(r'name=["\']([^"\']+)["\']', meta_attrs, re.IGNORECASE)
            content_match = re.search(r'content=["\']([^"\']+)["\']', meta_attrs, re.IGNORECASE)
            
            if name_match and content_match:
                name = name_match.group(1).lower()
                content = html.unescape(content_match.group(1))
                
                if name == 'description':
                    metadata['description'] = content
                elif name == 'keywords':
                    metadata['keywords'] = [k.strip() for k in content.split(',')]
                elif name == 'author':
                    metadata['author'] = content
        
        # Language
        lang_match = re.search(r'<html[^>]+lang=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
        if lang_match:
            metadata['lang'] = lang_match.group(1)
        
        return metadata
    
    async def _analyze_web_content(self, content_info: Dict[str, Any]) -> List[str]:
        """Analyze web content for insights"""
        insights = []
        content = content_info.get('content', '')
        content_type = content_info.get('content_type', '')
        
        # Content type specific analysis
        if content_type == 'application/json':
            try:
                json_data = json.loads(content)
                if isinstance(json_data, dict):
                    insights.append(f"JSON object with {len(json_data)} top-level keys")
                elif isinstance(json_data, list):
                    insights.append(f"JSON array with {len(json_data)} items")
            except:
                insights.append("Invalid JSON format detected")
        
        elif content_type == 'text/html':
            # HTML analysis
            if '<DOCTYPE html' in content or '<html' in content:
                insights.append("Valid HTML document structure")
            
            # Framework detection
            if 'react' in content.lower():
                insights.append("React framework detected")
            if 'vue' in content.lower():
                insights.append("Vue.js framework detected")
            if 'angular' in content.lower():
                insights.append("Angular framework detected")
            
            # CMS detection
            if 'wordpress' in content.lower():
                insights.append("WordPress CMS detected")
        
        elif content_type.startswith('text/'):
            # Text content analysis
            word_count = len(content.split())
            line_count = content.count('\n')
            insights.append(f"Text content: {word_count} words, {line_count} lines")
        
        # Size analysis
        size = content_info.get('content_length', 0)
        if size > 1024 * 1024:  # > 1MB
            insights.append("Large content size - may affect loading performance")
        elif size < 1024:  # < 1KB
            insights.append("Very small content - might be a lightweight resource")
        
        return insights
    
    async def _extract_readable_content(self, content: str, content_type: str) -> Optional[str]:
        """Extract readable text content from web content"""
        if content_type == 'text/plain':
            return content
        
        elif content_type == 'text/html':
            # Simple HTML text extraction
            # Remove script and style content
            content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
            content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
            
            # Remove HTML tags
            content = re.sub(r'<[^>]+>', '', content)
            
            # Clean up whitespace
            content = re.sub(r'\s+', ' ', content)
            content = content.strip()
            
            return content if content else None
        
        elif content_type == 'application/json':
            try:
                # Pretty format JSON
                json_data = json.loads(content)
                return json.dumps(json_data, indent=2, ensure_ascii=False)
            except:
                return content
        
        elif content_type in ['application/xml', 'text/xml']:
            try:
                # Format XML
                root = ET.fromstring(content)
                return ET.tostring(root, encoding='unicode')
            except:
                return content
        
        return content if isinstance(content, str) else None
    
    def _get_content_insights(self, content: str, content_type: str) -> List[str]:
        """Generate insights about extracted content"""
        insights = []
        
        if not content:
            return insights
        
        # General content analysis
        word_count = len(content.split())
        char_count = len(content)
        
        if word_count > 1000:
            insights.append(f"Substantial content: {word_count:,} words")
        elif word_count < 50:
            insights.append(f"Brief content: {word_count} words")
        
        # Content quality indicators
        if content_type == 'text/html':
            # Check for common quality indicators
            if 'tutorial' in content.lower() or 'guide' in content.lower():
                insights.append("Educational content detected")
            
            if 'api' in content.lower() and 'documentation' in content.lower():
                insights.append("API documentation detected")
            
            if 'example' in content.lower() or 'sample' in content.lower():
                insights.append("Contains code examples or samples")
        
        # Language detection (simple)
        if re.search(r'[^\x00-\x7F]', content):
            insights.append("Contains non-ASCII characters (likely non-English)")
        
        return insights
    
    def _get_action_suggestions(self, content_info: Dict[str, Any], url: str) -> List[str]:
        """Generate action suggestions based on content analysis"""
        suggestions = []
        content_type = content_info.get('content_type', '')
        
        if content_type == 'application/json':
            suggestions.append("Use bb7_analyze_webpage for structured JSON data analysis")
        
        elif content_type == 'text/html':
            suggestions.append("Use bb7_analyze_webpage for comprehensive page analysis")
            
            # Check for documentation
            if 'docs' in url or 'documentation' in url:
                suggestions.append("This appears to be documentation - consider bookmarking for reference")
        
        elif content_type.startswith('text/'):
            suggestions.append("Consider saving content locally for offline reference")
        
        # General suggestions
        if content_info.get('content_length', 0) > 100000:  # > 100KB
            suggestions.append("Large content detected - consider extracting specific sections")
        
        return suggestions
    
    async def _perform_web_search(self, query: str, search_engine: str, max_results: int) -> List[Dict[str, Any]]:
        """Perform web search using specified search engine"""
        # This is a simplified search implementation
        # In a real implementation, you'd integrate with actual search APIs
        
        search_url_template = self.search_engines.get(search_engine)
        if not search_url_template:
            return []
        
        # Encode query for URL
        encoded_query = quote_plus(query)
        search_url = search_url_template.format(encoded_query)
        
        try:
            # Fetch search results page
            content_info = await self._fetch_web_content(search_url)
            
            # Parse search results (simplified implementation)
            results = self._parse_search_results(content_info['content'], search_engine)
            
            # Limit results and add relevance scoring
            limited_results = results[:max_results]
            
            # Add relevance scoring based on query matching
            for result in limited_results:
                result['relevance_score'] = self._calculate_relevance_score(result, query)
            
            return limited_results
            
        except Exception as e:
            self.logger.error(f"Error performing search: {e}")
            return []
    
    def _parse_search_results(self, search_page_content: str, search_engine: str) -> List[Dict[str, Any]]:
        """Parse search results from search engine page (simplified)"""
        results = []
        
        # This is a very basic implementation
        # Real implementation would parse actual search engine results
        
        if search_engine == 'duckduckgo':
            # Basic DuckDuckGo result parsing
            result_pattern = r'<a[^>]+href="([^"]+)"[^>]*>([^<]+)</a>'
            matches = re.findall(result_pattern, search_page_content)
            
            for url, title in matches[:20]:  # Limit to first 20 matches
                if url.startswith('http'):
                    results.append({
                        'title': html.unescape(title.strip()),
                        'url': url,
                        'description': 'Search result from DuckDuckGo'
                    })
        
        return results
    
    def _calculate_relevance_score(self, result: Dict[str, Any], query: str) -> float:
        """Calculate relevance score for search result"""
        score = 0.0
        query_words = query.lower().split()
        
        # Check title relevance
        title = result.get('title', '').lower()
        title_matches = sum(1 for word in query_words if word in title)
        score += (title_matches / len(query_words)) * 0.6
        
        # Check description relevance
        description = result.get('description', '').lower()
        desc_matches = sum(1 for word in query_words if word in description)
        score += (desc_matches / len(query_words)) * 0.3
        
        # URL relevance
        url = result.get('url', '').lower()
        url_matches = sum(1 for word in query_words if word in url)
        score += (url_matches / len(query_words)) * 0.1
        
        return min(1.0, score)
    
    def _analyze_search_results(self, results: List[Dict[str, Any]], query: str) -> List[str]:
        """Analyze search results for insights"""
        insights = []
        
        if not results:
            return insights
        
        # Domain analysis
        domains = [urlparse(result['url']).netloc for result in results]
        unique_domains = set(domains)
        
        insights.append(f"Results span {len(unique_domains)} unique domains")
        
        # Common domain patterns
        domain_counts = {}
        for domain in domains:
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        top_domain = max(domain_counts.items(), key=lambda x: x[1])
        if top_domain[1] > 1:
            insights.append(f"Most common domain: {top_domain[0]} ({top_domain[1]} results)")
        
        # Content type diversity
        content_types = set()
        for result in results:
            if 'github.com' in result['url']:
                content_types.add('code_repository')
            elif 'stackoverflow.com' in result['url']:
                content_types.add('q_and_a')
            elif 'docs.' in result['url'] or 'documentation' in result['url']:
                content_types.add('documentation')
            else:
                content_types.add('general_content')
        
        if len(content_types) > 1:
            insights.append(f"Diverse result types: {', '.join(content_types)}")
        
        return insights
    
    def _generate_related_queries(self, original_query: str, results: List[Dict[str, Any]]) -> List[str]:
        """Generate related search queries based on results"""
        related_queries = []
        
        # Extract common terms from titles
        all_titles = ' '.join(result.get('title', '') for result in results)
        words = re.findall(r'\b[a-zA-Z]{4,}\b', all_titles.lower())
        
        # Count word frequency
        word_counts = {}
        for word in words:
            if word not in original_query.lower():
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # Generate related queries
        common_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        
        for word, count in common_words[:3]:
            if count > 1:
                related_queries.append(f"{original_query} {word}")
        
        return related_queries
    
    async def _analyze_html_structure(self, html_content: str) -> Dict[str, Any]:
        """Analyze HTML structure comprehensively"""
        analysis = {}
        
        # Extract title
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
        if title_match:
            analysis['title'] = html.unescape(title_match.group(1).strip())
        
        # Extract language
        lang_match = re.search(r'<html[^>]+lang=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
        if lang_match:
            analysis['lang'] = lang_match.group(1)
        
        # Structure analysis
        structure = {
            'total_elements': len(re.findall(r'<[^>]+>', html_content)),
            'text_length': len(re.sub(r'<[^>]+>', '', html_content)),
            'heading_count': len(re.findall(r'<h[1-6][^>]*>', html_content, re.IGNORECASE)),
            'h1_count': len(re.findall(r'<h1[^>]*>', html_content, re.IGNORECASE)),
            'paragraph_count': len(re.findall(r'<p[^>]*>', html_content, re.IGNORECASE)),
            'form_count': len(re.findall(r'<form[^>]*>', html_content, re.IGNORECASE)),
            'table_count': len(re.findall(r'<table[^>]*>', html_content, re.IGNORECASE))
        }
        analysis['structure'] = structure
        
        # Links analysis
        link_pattern = r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>'
        all_links = re.findall(link_pattern, html_content, re.IGNORECASE)
        
        links = {
            'all': all_links,
            'internal': [],
            'external': [],
            'mailto': []
        }
        
        for link in all_links:
            if link.startswith('mailto:'):
                links['mailto'].append(link)
            elif link.startswith(('http://', 'https://')):
                links['external'].append(link)
            else:
                links['internal'].append(link)
        
        analysis['links'] = links
        
        # Images analysis
        img_pattern = r'<img\s+[^>]*src=["\']([^"\']+)["\'][^>]*'
        img_matches = re.finditer(img_pattern, html_content, re.IGNORECASE)
        
        images = []
        for match in img_matches:
            img_tag = match.group(0)
            alt_match = re.search(r'alt=["\']([^"\']*)["\']', img_tag)
            images.append({
                'src': match.group(1),
                'alt': alt_match.group(1) if alt_match else ''
            })
        
        analysis['images'] = images
        
        # Scripts and resources
        scripts = {
            'script_tags': re.findall(r'<script[^>]*>', html_content, re.IGNORECASE),
            'external_scripts': re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html_content, re.IGNORECASE),
            'inline_scripts': re.findall(r'<script[^>]*>(.*?)</script>', html_content, re.IGNORECASE | re.DOTALL),
            'css_files': re.findall(r'<link[^>]+href=["\']([^"\']+\.css[^"\']*)["\']', html_content, re.IGNORECASE)
        }
        analysis['scripts'] = scripts
        
        return analysis
    
    def _analyze_seo_factors(self, html_analysis: Dict[str, Any], content_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze SEO factors"""
        seo_score = 0
        factors = {}
        recommendations = []
        
        # Title analysis
        title = html_analysis.get('title', '')
        if title:
            if 10 <= len(title) <= 60:
                factors['title_length'] = {'status': 'good', 'message': 'Title length is optimal'}
                seo_score += 20
            else:
                factors['title_length'] = {'status': 'warning', 'message': f'Title length ({len(title)}) should be 10-60 characters'}
                recommendations.append('Optimize title length to 10-60 characters')
        else:
            factors['title_length'] = {'status': 'error', 'message': 'Missing page title'}
            recommendations.append('Add a descriptive page title')
        
        # Meta description analysis
        metadata = content_info.get('metadata', {})
        description = metadata.get('description', '')
        if description:
            if 120 <= len(description) <= 160:
                factors['meta_description'] = {'status': 'good', 'message': 'Meta description length is optimal'}
                seo_score += 15
            else:
                factors['meta_description'] = {'status': 'warning', 'message': f'Meta description length ({len(description)}) should be 120-160 characters'}
        else:
            factors['meta_description'] = {'status': 'error', 'message': 'Missing meta description'}
            recommendations.append('Add a meta description')
        
        # Heading structure
        structure = html_analysis.get('structure', {})
        h1_count = structure.get('h1_count', 0)
        if h1_count == 1:
            factors['h1_structure'] = {'status': 'good', 'message': 'Proper H1 structure (1 H1 tag)'}
            seo_score += 15
        elif h1_count == 0:
            factors['h1_structure'] = {'status': 'error', 'message': 'Missing H1 tag'}
            recommendations.append('Add exactly one H1 tag')
        else:
            factors['h1_structure'] = {'status': 'warning', 'message': f'Multiple H1 tags ({h1_count}) found'}
            recommendations.append('Use only one H1 tag per page')
        
        # Images with alt text
        images = html_analysis.get('images', [])
        if images:
            images_with_alt = len([img for img in images if img.get('alt')])
            alt_percentage = (images_with_alt / len(images)) * 100
            
            if alt_percentage >= 90:
                factors['image_alt'] = {'status': 'good', 'message': f'{alt_percentage:.1f}% of images have alt text'}
                seo_score += 10
            else:
                factors['image_alt'] = {'status': 'warning', 'message': f'Only {alt_percentage:.1f}% of images have alt text'}
                recommendations.append('Add alt text to all images')
        
        # Content length
        text_length = structure.get('text_length', 0)
        if text_length >= 300:
            factors['content_length'] = {'status': 'good', 'message': f'Sufficient content length ({text_length} characters)'}
            seo_score += 10
        else:
            factors['content_length'] = {'status': 'warning', 'message': f'Content is short ({text_length} characters)'}
            recommendations.append('Consider adding more content (aim for 300+ characters)')
        
        # Page speed (simplified based on size)
        content_length = content_info.get('content_length', 0)
        if content_length < 500000:  # < 500KB
            factors['page_size'] = {'status': 'good', 'message': 'Page size is reasonable for fast loading'}
            seo_score += 10
        else:
            factors['page_size'] = {'status': 'warning', 'message': 'Large page size may affect loading speed'}
            recommendations.append('Optimize page size for better performance')
        
        return {
            'score': min(100, seo_score),
            'factors': factors,
            'recommendations': recommendations
        }
    
    def _analyze_technical_aspects(self, content_info: Dict[str, Any], html_analysis: Dict[str, Any]) -> List[str]:
        """Analyze technical aspects of the webpage"""
        aspects = []
        
        # HTTP status
        status_code = content_info.get('status_code', 0)
        if status_code == 200:
            aspects.append("✅ HTTP 200 - Page loads successfully")
        else:
            aspects.append(f"⚠️ HTTP {status_code} - Non-standard response code")
        
        # Content encoding
        headers = content_info.get('headers', {})
        if 'gzip' in headers.get('Content-Encoding', ''):
            aspects.append("✅ GZIP compression enabled")
        else:
            aspects.append("⚠️ GZIP compression not detected")
        
        # HTTPS
        final_url = content_info.get('final_url', '')
        if final_url.startswith('https://'):
            aspects.append("✅ HTTPS enabled for secure connection")
        else:
            aspects.append("⚠️ HTTP only - consider HTTPS for security")
        
        # Responsive design indicators
        html_content = content_info.get('content', '')
        if isinstance(html_content, str):
            if 'viewport' in html_content:
                aspects.append("✅ Viewport meta tag found (mobile-friendly)")
            else:
                aspects.append("⚠️ No viewport meta tag (may not be mobile-friendly)")
        
        return aspects
    
    def _get_performance_insights(self, content_info: Dict[str, Any], html_analysis: Dict[str, Any]) -> List[str]:
        """Get performance insights"""
        insights = []
        
        content_length = content_info.get('content_length', 0)
        
        # Size analysis
        if content_length > 1024 * 1024:  # > 1MB
            insights.append(f"⚠️ Large page size ({self._format_bytes(content_length)}) - consider optimization")
        elif content_length < 10 * 1024:  # < 10KB
            insights.append(f"✅ Small page size ({self._format_bytes(content_length)}) - fast loading")
        
        # Resource analysis
        scripts = html_analysis.get('scripts', {})
        external_scripts = scripts.get('external_scripts', [])
        css_files = scripts.get('css_files', [])
        
        total_external_resources = len(external_scripts) + len(css_files)
        if total_external_resources > 10:
            insights.append(f"⚠️ Many external resources ({total_external_resources}) - may affect loading speed")
        
        # Image analysis
        images = html_analysis.get('images', [])
        if len(images) > 20:
            insights.append(f"⚠️ Many images ({len(images)}) - consider lazy loading")
        
        return insights
    
    def _analyze_accessibility(self, html_analysis: Dict[str, Any]) -> List[str]:
        """Analyze accessibility factors"""
        findings = []
        
        # Image alt text
        images = html_analysis.get('images', [])
        if images:
            images_without_alt = [img for img in images if not img.get('alt')]
            if images_without_alt:
                findings.append(f"⚠️ {len(images_without_alt)} images missing alt text")
            else:
                findings.append("✅ All images have alt text")
        
        # Form analysis (simplified)
        structure = html_analysis.get('structure', {})
        form_count = structure.get('form_count', 0)
        if form_count > 0:
            findings.append(f"📝 {form_count} forms detected - ensure proper labeling")
        
        # Heading structure
        heading_count = structure.get('heading_count', 0)
        if heading_count > 0:
            findings.append(f"✅ {heading_count} headings found - good for screen readers")
        else:
            findings.append("⚠️ No headings found - consider adding heading structure")
        
        return findings
    
    def _analyze_http_error(self, error_code: int, error_message: str) -> Dict[str, str]:
        """Analyze HTTP error and provide helpful information"""
        error_info = {
            400: {
                'message': 'Bad Request - The server couldn\'t understand the request',
                'suggestion': 'Check the URL format and any parameters'
            },
            401: {
                'message': 'Unauthorized - Authentication is required',
                'suggestion': 'This resource requires login or API key'
            },
            403: {
                'message': 'Forbidden - Access to this resource is denied',
                'suggestion': 'You don\'t have permission to access this resource'
            },
            404: {
                'message': 'Not Found - The requested resource doesn\'t exist',
                'suggestion': 'Check the URL spelling and path'
            },
            429: {
                'message': 'Too Many Requests - Rate limit exceeded',
                'suggestion': 'Wait a few moments before trying again'
            },
            500: {
                'message': 'Internal Server Error - Server encountered an error',
                'suggestion': 'This is a server-side issue, try again later'
            },
            502: {
                'message': 'Bad Gateway - Server received invalid response',
                'suggestion': 'Server configuration issue, try again later'
            },
            503: {
                'message': 'Service Unavailable - Server is temporarily unavailable',
                'suggestion': 'Server is down for maintenance, try again later'
            }
        }
        
        return error_info.get(error_code, {
            'message': f'HTTP Error {error_code}: {error_message}',
            'suggestion': 'Check the URL and try again'
        })
    
    async def _get_file_info(self, url: str) -> Dict[str, Any]:
        """Get file information without downloading"""
        request = Request(url, headers={'User-Agent': self.user_agent})
        request.get_method = lambda: 'HEAD'  # HEAD request for metadata only
        
        try:
            with urlopen(request, timeout=self.default_timeout) as response:
                return {
                    'content_length': int(response.headers.get('Content-Length', 0)),
                    'content_type': response.headers.get('Content-Type', ''),
                    'last_modified': response.headers.get('Last-Modified', ''),
                    'status_code': response.status
                }
        except Exception:
            # Fall back to GET request if HEAD fails
            return await self._fetch_web_content(url)
    
    async def _download_file_content(self, url: str, file_path: Path) -> Dict[str, Any]:
        """Download file content to specified path"""
        request = Request(url, headers={'User-Agent': self.user_agent})
        
        with urlopen(request, timeout=self.default_timeout) as response:
            content_type = response.headers.get('Content-Type', '')
            
            with open(file_path, 'wb') as f:
                content = response.read()
                f.write(content)
            
            return {
                'file_size': len(content),
                'content_type': content_type
            }
    
    def _extract_filename_from_url(self, url: str) -> str:
        """Extract filename from URL"""
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        if path and path != '/':
            filename = Path(path).name
            if filename and '.' in filename:
                return filename
        
        # Generate filename based on domain
        domain = parsed_url.netloc.replace('www.', '')
        return f"{domain}_download"
    
    def _analyze_downloaded_file(self, file_path: Path, download_result: Dict[str, Any]) -> List[str]:
        """Analyze downloaded file"""
        analysis = []
        
        # File extension analysis
        extension = file_path.suffix.lower()
        if extension:
            file_types = {
                '.pdf': 'PDF document',
                '.doc': 'Word document',
                '.docx': 'Word document',
                '.txt': 'Text file',
                '.json': 'JSON data file',
                '.xml': 'XML data file',
                '.csv': 'CSV data file',
                '.zip': 'ZIP archive',
                '.tar': 'TAR archive',
                '.gz': 'GZIP archive'
            }
            
            file_type = file_types.get(extension, f'{extension[1:].upper()} file')
            analysis.append(f"File type: {file_type}")
        
        # Size analysis
        file_size = download_result.get('file_size', 0)
        if file_size > 10 * 1024 * 1024:  # > 10MB
            analysis.append("Large file - consider storage space")
        elif file_size < 1024:  # < 1KB
            analysis.append("Very small file - verify content completeness")
        
        return analysis
    
    def _check_file_security(self, file_path: Path, download_result: Dict[str, Any]) -> List[str]:
        """Check file security considerations"""
        security_notes = []
        
        # Executable file warning
        executable_extensions = {'.exe', '.msi', '.dmg', '.pkg', '.deb', '.rpm', '.sh', '.bat', '.cmd'}
        if file_path.suffix.lower() in executable_extensions:
            security_notes.append("⚠️ Executable file - scan with antivirus before running")
        
        # Script file warning
        script_extensions = {'.js', '.py', '.php', '.pl', '.rb', '.ps1'}
        if file_path.suffix.lower() in script_extensions:
            security_notes.append("⚠️ Script file - review content before executing")
        
        # Archive file warning
        archive_extensions = {'.zip', '.rar', '.7z', '.tar', '.gz'}
        if file_path.suffix.lower() in archive_extensions:
            security_notes.append("💡 Archive file - scan contents before extracting")
        
        return security_notes
    
    def _get_file_usage_suggestions(self, file_path: Path, download_result: Dict[str, Any]) -> List[str]:
        """Get usage suggestions for downloaded file"""
        suggestions = []
        extension = file_path.suffix.lower()
        
        usage_suggestions = {
            '.pdf': 'Open with PDF reader for viewing documents',
            '.json': 'Use bb7_read_file to parse and analyze JSON data',
            '.csv': 'Import into spreadsheet application or use for data analysis',
            '.txt': 'Use bb7_read_file to view plain text content',
            '.md': 'View as Markdown formatted documentation',
            '.zip': 'Extract contents to access individual files',
            '.tar': 'Extract using tar command or archive utility'
        }
        
        suggestion = usage_suggestions.get(extension)
        if suggestion:
            suggestions.append(suggestion)
        
        # General suggestions
        suggestions.append(f"File saved to: {file_path}")
        suggestions.append("Use bb7_get_file_info to check file metadata")
        
        return suggestions
    
    async def _save_cached_content(self, url: str, content_info: Dict[str, Any]) -> Optional[str]:
        """Save content to cache"""
        try:
            # Create cache filename based on URL hash
            url_hash = hashlib.md5(url.encode()).hexdigest()
            cache_file = self.cache_dir / f"{url_hash}.cache"
            
            # Save content and metadata
            cache_data = {
                'url': url,
                'timestamp': time.time(),
                'content_info': content_info
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            return str(cache_file)
            
        except Exception as e:
            self.logger.error(f"Error saving cached content: {e}")
            return None
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes in human readable format"""
        value = float(bytes_value)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if value < 1024:
                return f"{value:.1f} {unit}"
            value /= 1024
        return f"{value:.1f} TB"
    
    def get_tools(self) -> Dict[str, Any]:
        """Return all available web tools with proper MCP formatting"""
        return {
            'bb7_fetch_url': {
                'description': '🌐 Fetch and intelligently analyze web content from any URL with automatic content type detection, smart text extraction, and comprehensive metadata analysis. Perfect for documentation research, API exploration, content analysis, and gathering information from web resources. Provides structured output with actionable insights and extracted key information.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'url': {
                            'type': 'string',
                            'description': 'URL to fetch content from (HTTP/HTTPS)'
                        },
                        'extract_text': {
                            'type': 'boolean',
                            'description': 'Whether to extract readable text content',
                            'default': True
                        },
                        'follow_redirects': {
                            'type': 'boolean',
                            'description': 'Whether to follow HTTP redirects',
                            'default': True
                        },
                        'include_metadata': {
                            'type': 'boolean',
                            'description': 'Whether to include HTML metadata analysis',
                            'default': True
                        },
                        'save_content': {
                            'type': 'boolean',
                            'description': 'Whether to save content to cache',
                            'default': False
                        }
                    },
                    'required': ['url']
                },
                'function': self.bb7_fetch_url
            },
            'bb7_search_web': {
                'description': '🔍 Search the web using multiple search engines with intelligent result aggregation and analysis. Perfect for research, finding documentation, discovering code examples, and gathering information on development topics. Provides ranked results with content previews and actionable insights for each found resource.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'query': {
                            'type': 'string',
                            'description': 'Search query or keywords'
                        },
                        'search_engine': {
                            'type': 'string',
                            'description': 'Search engine to use',
                            'enum': ['duckduckgo', 'github', 'stackoverflow', 'docs'],
                            'default': 'duckduckgo'
                        },
                        'max_results': {
                            'type': 'integer',
                            'description': 'Maximum number of results to return',
                            'default': 10
                        },
                        'include_snippets': {
                            'type': 'boolean',
                            'description': 'Whether to include content snippets',
                            'default': True
                        }
                    },
                    'required': ['query']
                },
                'function': self.bb7_search_web
            },
            'bb7_analyze_webpage': {
                'description': '🔬 Perform comprehensive analysis of webpage structure, content quality, SEO factors, and technical characteristics. Perfect for web development, content auditing, competitor analysis, and understanding webpage architecture. Provides detailed insights into page performance, accessibility, and optimization opportunities.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'url': {
                            'type': 'string',
                            'description': 'URL of webpage to analyze'
                        },
                        'include_links': {
                            'type': 'boolean',
                            'description': 'Whether to analyze page links',
                            'default': True
                        },
                        'include_images': {
                            'type': 'boolean',
                            'description': 'Whether to analyze images',
                            'default': True
                        },
                        'include_scripts': {
                            'type': 'boolean',
                            'description': 'Whether to analyze scripts and resources',
                            'default': False
                        },
                        'analyze_seo': {
                            'type': 'boolean',
                            'description': 'Whether to perform SEO analysis',
                            'default': True
                        }
                    },
                    'required': ['url']
                },
                'function': self.bb7_analyze_webpage
            },
            'bb7_download_file': {
                'description': '📥 Download files from web URLs with intelligent handling of different content types, progress tracking, and automatic organization. Perfect for downloading documentation, code samples, data files, and other web resources. Provides safety checks and comprehensive download management with metadata preservation.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'url': {
                            'type': 'string',
                            'description': 'URL of file to download'
                        },
                        'filename': {
                            'type': 'string',
                            'description': 'Custom filename (auto-detected if not provided)'
                        },
                        'destination': {
                            'type': 'string',
                            'description': 'Destination directory',
                            'default': 'downloads'
                        },
                        'max_size': {
                            'type': 'integer',
                            'description': 'Maximum file size in bytes',
                            'default': 104857600
                        },
                        'overwrite': {
                            'type': 'boolean',
                            'description': 'Whether to overwrite existing files',
                            'default': False
                        }
                    },
                    'required': ['url']
                },
                'function': self.bb7_download_file
            }
        }


# For standalone testing
if __name__ == "__main__":
    import asyncio
    
    async def test_web_tool():
        logging.basicConfig(level=logging.INFO)
        tool = WebTool()
        
        print("=== Testing Web Tool ===")
        
        # Test URL fetching
        result = await tool.bb7_fetch_url({'url': 'https://httpbin.org/json'})
        print(f"URL fetch result:\n{result}\n")
        
        # Test web search (note: this is a simplified implementation)
        result = await tool.bb7_search_web({'query': 'python programming', 'max_results': 3})
        print(f"Search result:\n{result}\n")
    
    asyncio.run(test_web_tool())
