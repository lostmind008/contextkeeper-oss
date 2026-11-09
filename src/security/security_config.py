#!/usr/bin/env python3
"""
Security Configuration for ContextKeeper v3.0
Implements OWASP Top 10 2021 security controls
"""

import os
from datetime import timedelta
from typing import Dict, List, Any


class SecurityConfig:
    """Central security configuration following OWASP guidelines"""
    
    # CORS Configuration - OWASP A05:2021
    # Reference: https://owasp.org/www-community/attacks/CORS_OriginHeaderScrutiny
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5556').split(',')
    CORS_ALLOW_CREDENTIALS = True
    CORS_MAX_AGE = 3600
    
    # Session Security - OWASP A07:2021
    # Reference: https://owasp.org/www-community/attacks/Session_hijacking_attack
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    SESSION_COOKIE_NAME = '__Host-session' if SESSION_COOKIE_SECURE else 'session'
    
    # JWT Configuration - OWASP A02:2021
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', os.urandom(32).hex())
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    JWT_ALGORITHM = 'HS256'
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    # Rate Limiting - OWASP A04:2021
    # Reference: https://owasp.org/www-community/controls/Rate_Limiting
    RATE_LIMIT_ENABLED = True
    RATE_LIMITS = {
        'default': '200 per day, 50 per hour',
        'query': '10 per minute',
        'ingest': '5 per minute',
        'sacred': '5 per hour',
        'auth': '5 per minute'
    }
    
    # Security Headers - OWASP A05:2021
    # Reference: https://owasp.org/www-project-secure-headers/
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
    }
    
    # Input Validation - OWASP A03:2021
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max request size
    ALLOWED_EXTENSIONS = {'.py', '.js', '.ts', '.jsx', '.tsx', '.json', '.md', '.txt', '.yml', '.yaml'}
    ALLOWED_CONTENT_TYPES = ['application/json', 'text/plain', 'multipart/form-data']
    
    # File Upload Security - OWASP A01:2021
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/tmp/contextkeeper_uploads')
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    SCAN_UPLOADS = True
    
    # API Key Requirements - OWASP A02:2021
    API_KEY_MIN_LENGTH = 32
    API_KEY_REQUIRE_MIXED_CASE = True
    API_KEY_REQUIRE_NUMBERS = True
    API_KEY_REQUIRE_SPECIAL = False  # Optional for compatibility
    
    # Sacred Key Requirements
    SACRED_KEY_MIN_LENGTH = 32
    SACRED_KEY_MAX_AGE_DAYS = 90  # Rotate every 90 days
    
    # Logging Configuration - OWASP A09:2021
    SECURITY_LOG_FILE = 'security_audit.log'
    SECURITY_LOG_LEVEL = 'INFO'
    LOG_SENSITIVE_DATA = False  # Never log passwords, keys, etc.
    
    # Database Security
    DB_CONNECTION_TIMEOUT = 30
    DB_POOL_SIZE = 10
    DB_MAX_OVERFLOW = 20
    
    # ChromaDB Security
    CHROMADB_PERSIST_DIRECTORY = os.environ.get('CHROMADB_PERSIST_DIR', './rag_knowledge_db')
    CHROMADB_ANONYMIZE_TELEMETRY = True
    
    # Environment-specific settings
    ENVIRONMENT = os.environ.get('FLASK_ENV', 'development')
    DEBUG = ENVIRONMENT == 'development'
    TESTING = ENVIRONMENT == 'testing'
    
    @classmethod
    def get_flask_config(cls) -> Dict[str, Any]:
        """Get Flask-specific configuration"""
        return {
            'SECRET_KEY': os.environ.get('FLASK_SECRET_KEY', os.urandom(32).hex()),
            'SESSION_COOKIE_SECURE': cls.SESSION_COOKIE_SECURE,
            'SESSION_COOKIE_HTTPONLY': cls.SESSION_COOKIE_HTTPONLY,
            'SESSION_COOKIE_SAMESITE': cls.SESSION_COOKIE_SAMESITE,
            'PERMANENT_SESSION_LIFETIME': cls.PERMANENT_SESSION_LIFETIME,
            'MAX_CONTENT_LENGTH': cls.MAX_CONTENT_LENGTH,
            'JWT_SECRET_KEY': cls.JWT_SECRET_KEY,
            'JWT_ACCESS_TOKEN_EXPIRES': cls.JWT_ACCESS_TOKEN_EXPIRES,
            'DEBUG': cls.DEBUG,
            'TESTING': cls.TESTING
        }
    
    @classmethod
    def get_cors_config(cls) -> Dict[str, Any]:
        """Get CORS configuration"""
        return {
            'origins': cls.CORS_ORIGINS,
            'allow_credentials': cls.CORS_ALLOW_CREDENTIALS,
            'max_age': cls.CORS_MAX_AGE,
            'supports_credentials': cls.CORS_ALLOW_CREDENTIALS
        }
    
    @classmethod
    def validate_environment(cls) -> List[str]:
        """Validate security-critical environment variables"""
        issues = []
        
        # Check API keys
        if not os.environ.get('GEMINI_API_KEY'):
            issues.append("GEMINI_API_KEY not set")
        
        if not os.environ.get('SACRED_APPROVAL_KEY'):
            issues.append("SACRED_APPROVAL_KEY not set")
        elif len(os.environ.get('SACRED_APPROVAL_KEY', '')) < cls.SACRED_KEY_MIN_LENGTH:
            issues.append(f"SACRED_APPROVAL_KEY must be at least {cls.SACRED_KEY_MIN_LENGTH} characters")
        
        # Check JWT secret in production
        if cls.ENVIRONMENT == 'production':
            if not os.environ.get('JWT_SECRET_KEY'):
                issues.append("JWT_SECRET_KEY must be set in production")
            
            if not os.environ.get('FLASK_SECRET_KEY'):
                issues.append("FLASK_SECRET_KEY must be set in production")
        
        # Check file permissions
        if os.path.exists(cls.CHROMADB_PERSIST_DIRECTORY):
            stat_info = os.stat(cls.CHROMADB_PERSIST_DIRECTORY)
            if stat_info.st_mode & 0o777 > 0o755:
                issues.append(f"ChromaDB directory has excessive permissions: {oct(stat_info.st_mode)[-3:]}")
        
        return issues


# Security middleware configuration
SECURITY_MIDDLEWARE = {
    'rate_limiter': {
        'enabled': True,
        'storage_url': os.environ.get('REDIS_URL', 'memory://'),
        'default_limits': ['200 per day', '50 per hour']
    },
    'csrf_protection': {
        'enabled': True,
        'token_length': 32,
        'time_limit': 3600  # 1 hour
    },
    'request_validation': {
        'enabled': True,
        'max_json_depth': 10,
        'max_array_length': 1000,
        'max_string_length': 10000
    }
}

# Allowed hosts for production
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# IP-based access control
IP_WHITELIST = os.environ.get('IP_WHITELIST', '').split(',') if os.environ.get('IP_WHITELIST') else []
IP_BLACKLIST = os.environ.get('IP_BLACKLIST', '').split(',') if os.environ.get('IP_BLACKLIST') else []

# Export configuration
__all__ = [
    'SecurityConfig',
    'SECURITY_MIDDLEWARE',
    'ALLOWED_HOSTS',
    'IP_WHITELIST',
    'IP_BLACKLIST'
]