#!/usr/bin/env python3
"""
Secure MCP HTTPS Server with API Key Authentication
Production-ready HTTPS wrapper for MCP server with full security

Features:
- API key authentication
- Rate limiting
- HTTPS with self-signed certificates
- Comprehensive logging and audit trail
- RESTful API endpoints
- Secure local-only access
"""

import base64
import hashlib
import hmac
import json
import logging
import secrets
import ssl
import threading
import time
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Set
import tempfile
import os
import re

# Standard library HTTP server
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import socketserver

# Import our existing MCP server
import sys
sys.path.insert(0, str(Path(__file__).parent))
from mcp_server import MCPServer


class SecurityConfig:
    """Security configuration for the HTTPS server"""
    
    def __init__(self):
        self.api_key = self._generate_api_key()
        self.rate_limit_requests = 100  # requests per minute
        self.rate_limit_window = 60  # seconds
        self.max_request_size = 10 * 1024 * 1024  # 10MB
        self.allowed_origins = ["https://localhost", "https://127.0.0.1"]
        self.session_timeout = 3600  # 1 hour
        
        # Create security directory
        self.security_dir = Path("data/security")
        self.security_dir.mkdir(exist_ok=True)
        
        # Save API key
        self._save_api_key()
    
    def _generate_api_key(self) -> str:
        """Generate a secure API key"""
        # Generate 32 bytes of random data and encode as base64
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('ascii').rstrip('=')
    
    def _save_api_key(self):
        """Save API key to secure file"""
        api_key_file = self.security_dir / "api_key.txt"
        with open(api_key_file, 'w') as f:
            f.write(self.api_key)
        
        # Set restrictive permissions (Windows equivalent)
        try:
            os.chmod(api_key_file, 0o600)
        except:
            pass  # Windows doesn't support chmod in the same way
        
        print(f"🔑 API Key saved to: {api_key_file}")
        print(f"🔑 API Key: {self.api_key}")


class RateLimiter:
    """Rate limiting implementation"""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.clients = defaultdict(list)
        self._lock = threading.Lock()
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if client is within rate limits"""
        with self._lock:
            now = time.time()
            
            # Clean old requests
            self.clients[client_id] = [
                req_time for req_time in self.clients[client_id]
                if now - req_time < self.window_seconds
            ]
            
            # Check if under limit
            if len(self.clients[client_id]) >= self.max_requests:
                return False
            
            # Add current request
            self.clients[client_id].append(now)
            return True
    
    def get_reset_time(self, client_id: str) -> int:
        """Get when rate limit resets for client"""
        with self._lock:
            if not self.clients[client_id]:
                return 0
            
            oldest_request = min(self.clients[client_id])
            return int(oldest_request + self.window_seconds)


class SecurityLogger:
    """Security-focused logging"""
    
    def __init__(self):
        self.log_file = Path("data/security/security.log")
        self.log_file.parent.mkdir(exist_ok=True)
        
        # Setup security logger
        self.logger = logging.getLogger("security")
        self.logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler(self.log_file)
        formatter = logging.Formatter(
            '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_auth_attempt(self, client_ip: str, success: bool, api_key_hash: str = ""):
        """Log authentication attempt"""
        self.logger.info(
            f"AUTH_ATTEMPT - IP: {client_ip} - Success: {success} - KeyHash: {api_key_hash[:8]}"
        )
    
    def log_rate_limit(self, client_ip: str, endpoint: str):
        """Log rate limit violation"""
        self.logger.warning(
            f"RATE_LIMIT - IP: {client_ip} - Endpoint: {endpoint}"
        )
    
    def log_suspicious_activity(self, client_ip: str, activity: str, details: str):
        """Log suspicious activity"""
        self.logger.warning(
            f"SUSPICIOUS - IP: {client_ip} - Activity: {activity} - Details: {details}"
        )
    
    def log_tool_usage(self, client_ip: str, tool_name: str, success: bool):
        """Log tool usage"""
        self.logger.info(
            f"TOOL_USAGE - IP: {client_ip} - Tool: {tool_name} - Success: {success}"
        )


class SecureMCPHandler(BaseHTTPRequestHandler):
    """Secure HTTP handler with API key authentication"""
    
    def __init__(self, *args, mcp_server=None, security_config=None, 
                 rate_limiter=None, security_logger=None, **kwargs):
        self.mcp_server = mcp_server
        self.security_config = security_config
        self.rate_limiter = rate_limiter
        self.security_logger = security_logger
        super().__init__(*args, **kwargs)
    
    def _get_client_ip(self) -> str:
        """Get client IP address"""
        # Check for forwarded headers first
        forwarded = self.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0].strip()
        
        real_ip = self.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return self.client_address[0]
    
    def _validate_api_key(self) -> bool:
        """Validate API key from request"""
        client_ip = self._get_client_ip()
        
        # Check Authorization header
        auth_header = self.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            provided_key = auth_header[7:]  # Remove 'Bearer ' prefix
        else:
            # Check query parameter as fallback
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            provided_key = query_params.get('api_key', [''])[0]
        
        if not provided_key:
            self.security_logger.log_auth_attempt(client_ip, False, "no_key")
            return False
        
        # Constant-time comparison to prevent timing attacks
        expected_key = self.security_config.api_key
        is_valid = hmac.compare_digest(provided_key, expected_key)
        
        # Log attempt
        key_hash = hashlib.sha256(provided_key.encode()).hexdigest()
        self.security_logger.log_auth_attempt(client_ip, is_valid, key_hash)
        
        return is_valid
    
    def _check_rate_limit(self) -> bool:
        """Check rate limiting"""
        client_ip = self._get_client_ip()
        
        if not self.rate_limiter.is_allowed(client_ip):
            self.security_logger.log_rate_limit(client_ip, self.path)
            return False
        
        return True
    
    def _validate_request_size(self) -> bool:
        """Validate request size"""
        content_length = int(self.headers.get('Content-Length', 0))
        
        if content_length > self.security_config.max_request_size:
            self.security_logger.log_suspicious_activity(
                self._get_client_ip(),
                "large_request",
                f"Size: {content_length} bytes"
            )
            return False
        
        return True
    
    def _security_check(self) -> Optional[str]:
        """Perform comprehensive security checks"""
        client_ip = self._get_client_ip()
        
        # Only allow localhost connections
        if client_ip not in ['127.0.0.1', '::1', 'localhost']:
            self.security_logger.log_suspicious_activity(
                client_ip, "non_localhost", f"Attempted access from {client_ip}"
            )
            return "Forbidden: Only localhost connections allowed"
        
        # Check rate limiting
        if not self._check_rate_limit():
            return "Rate limit exceeded"
        
        # Check request size
        if not self._validate_request_size():
            return "Request too large"
        
        # Validate API key
        if not self._validate_api_key():
            return "Invalid or missing API key"
        
        return None  # All checks passed
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self._send_security_headers()
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            # Security check
            security_error = self._security_check()
            if security_error:
                self._send_error(403, security_error)
                return
            
            parsed_path = urlparse(self.path)
            
            if parsed_path.path == '/':
                self._send_server_info()
            elif parsed_path.path == '/tools':
                self._send_tools_list()
            elif parsed_path.path == '/health':
                self._send_health_check()
            elif parsed_path.path == '/metrics':
                self._send_metrics()
            elif parsed_path.path == '/api-info':
                self._send_api_info()
            else:
                self._send_error(404, "Endpoint not found")
                
        except Exception as e:
            self._send_error(500, f"Server error: {str(e)}")
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            # Security check
            security_error = self._security_check()
            if security_error:
                self._send_error(403, security_error)
                return
            
            if self.path == '/mcp':
                self._handle_mcp_request()
            elif self.path.startswith('/tools/'):
                self._handle_tool_call()
            else:
                self._send_error(404, "Endpoint not found")
                
        except Exception as e:
            self._send_error(500, f"Server error: {str(e)}")
    
    def _handle_mcp_request(self):
        """Handle MCP JSON-RPC requests"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            request_data = self.rfile.read(content_length)
            request_json = json.loads(request_data.decode('utf-8'))
            
            # Process MCP request
            if self.mcp_server:
                from mcp_server import handle_jsonrpc_request
                response = handle_jsonrpc_request(self.mcp_server, request_json)
            else:
                response = {"error": "MCP server not available"}
            
            self._send_json_response(response)
            
        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON")
        except Exception as e:
            self._send_error(500, str(e))
    
    def _handle_tool_call(self):
        """Handle direct tool calls"""
        try:
            # Extract tool name
            tool_name = self.path.split('/')[-1]
            client_ip = self._get_client_ip()
            
            # Validate tool name (security)
            if not re.match(r'^[a-zA-Z0-9_]+$', tool_name):
                self.security_logger.log_suspicious_activity(
                    client_ip, "invalid_tool_name", tool_name
                )
                self._send_error(400, "Invalid tool name")
                return
            
            content_length = int(self.headers.get('Content-Length', 0))
            request_data = self.rfile.read(content_length) if content_length > 0 else b'{}'
            
            try:
                params = json.loads(request_data.decode('utf-8'))
            except json.JSONDecodeError:
                params = {}
            
            # Call the tool
            if self.mcp_server and tool_name in self.mcp_server.tools:
                result = self.mcp_server.call_tool(tool_name, **params)
                success = result.get("success", False)
                
                # Log tool usage
                self.security_logger.log_tool_usage(client_ip, tool_name, success)
                
                self._send_json_response(result)
            else:
                self.security_logger.log_tool_usage(client_ip, tool_name, False)
                self._send_error(404, f"Tool '{tool_name}' not found")
                
        except Exception as e:
            self.security_logger.log_tool_usage(self._get_client_ip(), tool_name, False)
            self._send_error(500, str(e))
    
    def _send_server_info(self):
        """Send server information"""
        if self.mcp_server:
            info = self.mcp_server.get_server_info()
            info.update({
                "https_wrapper": True,
                "security_enabled": True,
                "api_version": "1.0",
                "authentication": "API Key required",
                "rate_limit": f"{self.security_config.rate_limit_requests}/minute",
                "endpoints": {
                    "GET /": "Server information",
                    "GET /tools": "List available tools",
                    "GET /health": "Health check",
                    "GET /metrics": "Server metrics",
                    "GET /api-info": "API documentation",
                    "POST /mcp": "MCP JSON-RPC endpoint",
                    "POST /tools/{tool_name}": "Direct tool execution"
                }
            })
            self._send_json_response(info)
        else:
            self._send_error(500, "MCP server not available")
    
    def _send_tools_list(self):
        """Send tools list"""
        if self.mcp_server:
            tools = list(self.mcp_server.tools.keys())
            tool_info = {}
            
            for tool_name in tools:
                tool_info[tool_name] = self.mcp_server.get_tool_info(tool_name)
            
            response = {
                "tools": tools,
                "tool_count": len(tools),
                "tool_details": tool_info
            }
            self._send_json_response(response)
        else:
            self._send_error(500, "MCP server not available")
    
    def _send_health_check(self):
        """Send health check"""
        if self.mcp_server:
            health = self.mcp_server.health_check()
            health.update({
                "security_status": "enabled",
                "https_status": "active",
                "rate_limiter_status": "active"
            })
            self._send_json_response(health)
        else:
            self._send_error(500, "MCP server not available")
    
    def _send_metrics(self):
        """Send server metrics"""
        if self.mcp_server:
            metrics = self.mcp_server.get_server_info()
            
            # Add security metrics
            metrics.update({
                "security_metrics": {
                    "api_key_configured": bool(self.security_config.api_key),
                    "rate_limit_active": True,
                    "https_enabled": True,
                    "localhost_only": True
                }
            })
            
            self._send_json_response(metrics)
        else:
            self._send_error(500, "MCP server not available")
    
    def _send_api_info(self):
        """Send API documentation"""
        api_docs = {
            "api_version": "1.0",
            "authentication": {
                "type": "API Key",
                "header": "Authorization: Bearer YOUR_API_KEY",
                "query_param": "?api_key=YOUR_API_KEY"
            },
            "endpoints": {
                "GET /": "Server information and status",
                "GET /tools": "List all available MCP tools",
                "GET /health": "Server health check",
                "GET /metrics": "Server performance metrics",
                "GET /api-info": "This API documentation",
                "POST /mcp": "MCP JSON-RPC protocol endpoint",
                "POST /tools/{tool_name}": "Execute specific tool directly"
            },
            "rate_limits": {
                "requests_per_minute": self.security_config.rate_limit_requests,
                "window_seconds": self.security_config.rate_limit_window
            },
            "security": {
                "https_only": True,
                "localhost_only": True,
                "api_key_required": True,
                "request_size_limit": f"{self.security_config.max_request_size} bytes"
            }
        }
        self._send_json_response(api_docs)
    
    def _send_json_response(self, data: Dict[str, Any], status_code: int = 200):
        """Send JSON response with security headers"""
        self.send_response(status_code)
        self._send_security_headers()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        response_json = json.dumps(data, indent=2)
        self.wfile.write(response_json.encode('utf-8'))
    
    def _send_error(self, status_code: int, message: str):
        """Send error response"""
        error_response = {
            "error": message,
            "status_code": status_code,
            "timestamp": time.time()
        }
        self._send_json_response(error_response, status_code)
    
    def _send_security_headers(self):
        """Send security headers"""
        # CORS headers
        self.send_header('Access-Control-Allow-Origin', 'https://localhost:*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        
        # Security headers
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('X-XSS-Protection', '1; mode=block')
        self.send_header('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
        
        # Rate limit headers
        if self.rate_limiter:
            client_ip = self._get_client_ip()
            reset_time = self.rate_limiter.get_reset_time(client_ip)
            self.send_header('X-RateLimit-Limit', str(self.security_config.rate_limit_requests))
            self.send_header('X-RateLimit-Reset', str(reset_time))
    
    def log_message(self, format, *args):
        """Override logging to use our security logger"""
        message = format % args
        self.security_logger.logger.info(f"HTTP: {message}")


class SecureMCPHTTPSServer:
    """Secure HTTPS MCP server with API key authentication"""
    
    def __init__(self, host: str = "localhost", port: int = 8443, debug: bool = False):
        self.host = host
        self.port = port
        self.debug = debug
        self.logger = logging.getLogger(__name__)
        
        # Initialize security components
        self.security_config = SecurityConfig()
        self.rate_limiter = RateLimiter(
            self.security_config.rate_limit_requests,
            self.security_config.rate_limit_window
        )
        self.security_logger = SecurityLogger()
        
        # Initialize MCP server
        self.mcp_server = MCPServer(debug=debug)
        
        # Server components
        self.httpd = None
        self.server_thread = None
        
        # Setup logging
        logging.basicConfig(
            level=logging.DEBUG if debug else logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        self.logger.info(f"Secure MCP HTTPS Server initialized on {host}:{port}")
        self.logger.info(f"API Key: {self.security_config.api_key}")
    
    def create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context with self-signed certificate"""
        cert_dir = Path("data/security/certs")
        cert_dir.mkdir(exist_ok=True)
        
        cert_file = cert_dir / "server.crt"
        key_file = cert_dir / "server.key"
        
        # Generate certificate if not exists
        if not cert_file.exists() or not key_file.exists():
            self._generate_ssl_certificate(cert_file, key_file)
        
        # Create SSL context with strong security
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
        context.load_cert_chain(cert_file, key_file)
        
        return context
    
    def _generate_ssl_certificate(self, cert_file: Path, key_file: Path):
        """Generate SSL certificate"""
        try:
            from cryptography import x509
            from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            import datetime
            
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            
            # Create certificate
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Local"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Local"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "MCP Server"),
                x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
            ])
            
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.datetime.utcnow()
            ).not_valid_after(
                datetime.datetime.utcnow() + datetime.timedelta(days=365)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName("localhost"),
                    x509.IPAddress("127.0.0.1"),
                ]),
                critical=False,
            ).add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_encipherment=True,
                    key_agreement=False,
                    key_cert_sign=False,
                    crl_sign=False,
                    content_commitment=False,
                    data_encipherment=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            ).add_extension(
                x509.ExtendedKeyUsage([
                    ExtendedKeyUsageOID.SERVER_AUTH,
                ]),
                critical=True,
            ).sign(private_key, hashes.SHA256())
            
            # Write private key
            with open(key_file, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            # Write certificate
            with open(cert_file, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            # Set restrictive permissions
            try:
                os.chmod(key_file, 0o600)
                os.chmod(cert_file, 0o644)
            except:
                pass
            
            self.logger.info("Generated SSL certificate for HTTPS")
            
        except ImportError:
            self.logger.error("cryptography library required for SSL certificate generation")
            raise RuntimeError("Install 'cryptography' package: pip install cryptography")
    
    def start_server(self) -> bool:
        """Start the secure HTTPS server"""
        try:
            # Create handler factory
            def handler_factory(*args, **kwargs):
                return SecureMCPHandler(
                    *args,
                    mcp_server=self.mcp_server,
                    security_config=self.security_config,
                    rate_limiter=self.rate_limiter,
                    security_logger=self.security_logger,
                    **kwargs
                )
            
            # Create HTTP server
            self.httpd = HTTPServer((self.host, self.port), handler_factory)
            
            # Wrap with SSL
            ssl_context = self.create_ssl_context()
            self.httpd.socket = ssl_context.wrap_socket(
                self.httpd.socket, server_side=True
            )
            
            # Start server in background
            self.server_thread = threading.Thread(
                target=self.httpd.serve_forever,
                daemon=True
            )
            self.server_thread.start()
            
            self.logger.info(f"Secure MCP HTTPS server started on https://{self.host}:{self.port}")
            self.security_logger.logger.info("Secure HTTPS server started")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start secure HTTPS server: {e}")
            return False
    
    def stop_server(self):
        """Stop the HTTPS server"""
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
        
        if self.server_thread:
            self.server_thread.join(timeout=5)
        
        self.security_logger.logger.info("Secure HTTPS server stopped")
        self.logger.info("Secure MCP HTTPS server stopped")
    
    def get_server_url(self) -> str:
        """Get server URL"""
        return f"https://{self.host}:{self.port}"
    
    def get_api_key(self) -> str:
        """Get API key"""
        return self.security_config.api_key
    
    def get_claude_desktop_config(self) -> Dict[str, Any]:
        """Generate Claude Desktop configuration"""
        return {
            "mcpServers": {
                "sovereign-mcp-https": {
                    "url": self.get_server_url(),
                    "api_key": self.get_api_key(),
                    "headers": {
                        "Authorization": f"Bearer {self.get_api_key()}"
                    }
                }
            }
        }


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Secure MCP HTTPS Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8443, help="Port to bind to") 
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Create secure server
    server = SecureMCPHTTPSServer(host=args.host, port=args.port, debug=args.debug)
    
    try:
        if server.start_server():
            print("🔒 Secure MCP HTTPS Server Started Successfully!")
            print("=" * 60)
            print(f"🌐 Server URL: {server.get_server_url()}")
            print(f"🔑 API Key: {server.get_api_key()}")
            print("📋 Available endpoints:")
            print("   GET  / - Server information")
            print("   GET  /tools - List all tools")
            print("   GET  /health - Health check")
            print("   GET  /metrics - Server metrics")
            print("   GET  /api-info - API documentation")
            print("   POST /mcp - MCP JSON-RPC endpoint")
            print("   POST /tools/{tool_name} - Direct tool execution")
            print("\n🔐 Security Features:")
            print("   ✅ API Key Authentication")
            print("   ✅ Rate Limiting (100 req/min)")
            print("   ✅ HTTPS with TLS 1.2+")
            print("   ✅ Localhost-only access")
            print("   ✅ Comprehensive logging")
            print("   ✅ Security headers")
            print("\n💾 Configuration saved to:")
            print("   📁 API Key: data/security/api_key.txt")
            print("   📁 Security Log: data/security/security.log")
            print("   📁 SSL Certs: data/security/certs/")
            
            # Generate Claude Desktop config
            config = server.get_claude_desktop_config()
            config_file = Path("claude_desktop_config.json")
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"\n⚙️  Claude Desktop Config: {config_file}")
            
            print("\nPress Ctrl+C to stop...")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Stopping server...")
                server.stop_server()
                print("✅ Server stopped securely")
        else:
            print("❌ Failed to start server")
            return 1
            
    except Exception as e:
        print(f"❌ Server error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
