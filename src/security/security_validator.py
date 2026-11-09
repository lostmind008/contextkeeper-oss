#!/usr/bin/env python3
"""
Security Validator Module for ContextKeeper v3.0
Implements input validation, sanitisation, and security checks
Following OWASP Top 10 2021 guidelines
"""

import re
import os
import secrets
import string
from pathlib import Path
from typing import Any, Dict, List, Optional
from werkzeug.security import safe_join
from markupsafe import escape  # Flask 3.0+ uses markupsafe directly
import logging

logger = logging.getLogger(__name__)


class SecurityValidator:
    """Central security validation and sanitisation class"""
    
    # OWASP recommended patterns
    # Reference: https://owasp.org/www-community/OWASP_Validation_Regex_Repository
    PATTERNS = {
        'project_id': r'^[a-zA-Z0-9][a-zA-Z0-9_-]{2,63}$',
        'filename': r'^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,254}$',
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'url': r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$',
        'alphanumeric': r'^[a-zA-Z0-9]+$',
        'safe_text': r'^[a-zA-Z0-9\s.,!?()-]{1,1000}$'
    }
    
    # Dangerous path patterns
    PATH_BLACKLIST = [
        '..',
        '~',
        '\\',
        '\x00',  # Null byte
        '%2e%2e',  # URL encoded ..
        '%252e%252e',  # Double URL encoded
        '..;',
        '..\\',
        '../',
        '..%2f',
        '..%5c',
    ]
    
    @classmethod
    def validate_project_id(cls, project_id: str) -> str:
        """
        Validate and sanitise project ID
        OWASP A03:2021 - Injection prevention
        """
        if not project_id:
            raise ValueError("Project ID cannot be empty")
        
        if not re.match(cls.PATTERNS['project_id'], project_id):
            raise ValueError(f"Invalid project ID format: {project_id}")
        
        return project_id
    
    @classmethod
    def validate_file_path(cls, file_path: str, base_dir: Optional[str] = None) -> str:
        """
        Validate and sanitise file paths to prevent path traversal
        OWASP A01:2021 - Broken Access Control prevention
        Reference: https://owasp.org/www-community/attacks/Path_Traversal
        """
        if not file_path:
            raise ValueError("File path cannot be empty")
        
        # Check for dangerous patterns
        for pattern in cls.PATH_BLACKLIST:
            if pattern in file_path:
                raise ValueError(f"Dangerous path pattern detected: {pattern}")
        
        # Convert to Path object for normalisation
        path = Path(file_path)
        
        # Resolve to absolute path and check if it's within base_dir
        if base_dir:
            base = Path(base_dir).resolve()
            try:
                resolved = (base / path).resolve()
                if not resolved.is_relative_to(base):
                    raise ValueError(f"Path traversal detected: {file_path}")
                return str(resolved)
            except Exception as e:
                raise ValueError(f"Invalid file path: {e}")
        
        # If no base_dir, just return normalised path
        return str(path.resolve())
    
    @classmethod
    def sanitise_html_input(cls, text: str) -> str:
        """
        Sanitise HTML input to prevent XSS
        OWASP A03:2021 - Injection prevention
        Reference: https://owasp.org/www-project-proactive-controls/v3/en/c4-encode-escape-data
        """
        if not text:
            return ""
        
        # Remove dangerous patterns first
        dangerous_patterns = [
            (r'javascript:', ''),
            (r'on\w+\s*=', ''),  # Remove event handlers like onerror=, onload=
            (r'<script[^>]*>.*?</script>', ''),  # Remove script tags
            (r'<iframe[^>]*>.*?</iframe>', ''),  # Remove iframes
        ]
        
        cleaned = text
        for pattern, replacement in dangerous_patterns:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE | re.DOTALL)
        
        # Then escape HTML entities
        return escape(cleaned)
    
    @classmethod
    def validate_api_key(cls, api_key: str, min_length: int = 32) -> bool:
        """
        Validate API key strength
        OWASP A02:2021 - Cryptographic Failures prevention
        """
        if not api_key:
            return False
        
        if len(api_key) < min_length:
            logger.warning(f"API key too short: {len(api_key)} < {min_length}")
            return False
        
        # Check for minimum entropy (mix of characters)
        has_upper = any(c.isupper() for c in api_key)
        has_lower = any(c.islower() for c in api_key)
        has_digit = any(c.isdigit() for c in api_key)
        
        if not (has_upper or has_lower) or not has_digit:
            logger.warning("API key lacks sufficient entropy")
            return False
        
        return True
    
    @classmethod
    def generate_secure_key(cls, length: int = 64) -> str:
        """
        Generate cryptographically secure random key
        OWASP A02:2021 - Cryptographic Failures prevention
        """
        alphabet = string.ascii_letters + string.digits + string.punctuation
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @classmethod
    def validate_json_input(cls, data: Dict[str, Any], required_fields: List[str] = None) -> Dict[str, Any]:
        """
        Validate JSON input structure and content
        OWASP A03:2021 - Injection prevention
        """
        if not isinstance(data, dict):
            raise ValueError("Input must be a JSON object")
        
        # Check required fields
        if required_fields:
            missing = [field for field in required_fields if field not in data]
            if missing:
                raise ValueError(f"Missing required fields: {', '.join(missing)}")
        
        # Sanitise string values
        sanitised = {}
        for key, value in data.items():
            if isinstance(value, str):
                # Remove null bytes and control characters
                value = value.replace('\x00', '')
                value = ''.join(char for char in value if char.isprintable() or char.isspace())
                # Also sanitise HTML to prevent XSS
                value = cls.sanitise_html_input(value)
                sanitised[key] = value[:10000]  # Limit string length
            elif isinstance(value, (int, float, bool)):
                sanitised[key] = value
            elif isinstance(value, list):
                # Recursively sanitise list items
                sanitised[key] = [cls.sanitise_value(item) for item in value[:1000]]  # Limit array size
            elif isinstance(value, dict):
                # Recursively sanitise nested objects
                sanitised[key] = cls.validate_json_input(value)
            else:
                # Skip unknown types
                continue
        
        return sanitised
    
    @classmethod
    def sanitise_value(cls, value: Any) -> Any:
        """Helper method to sanitise individual values"""
        if isinstance(value, str):
            value = value.replace('\x00', '')
            value = ''.join(char for char in value if char.isprintable() or char.isspace())
            # Also sanitise HTML 
            value = cls.sanitise_html_input(value)
            return value[:10000]
        elif isinstance(value, (int, float, bool)):
            return value
        elif isinstance(value, list):
            return [cls.sanitise_value(item) for item in value[:1000]]
        elif isinstance(value, dict):
            return cls.validate_json_input(value)
        return None
    
    @classmethod
    def validate_content_type(cls, content_type: str, allowed_types: List[str]) -> bool:
        """
        Validate Content-Type header
        OWASP A05:2021 - Security Misconfiguration prevention
        """
        if not content_type:
            return False
        
        # Extract main type (ignore charset and other parameters)
        main_type = content_type.split(';')[0].strip().lower()
        
        return main_type in [t.lower() for t in allowed_types]
    
    @classmethod
    def validate_sacred_key(cls, key: str) -> bool:
        """
        Validate SACRED_APPROVAL_KEY strength
        OWASP A02:2021 - Cryptographic Failures prevention
        """
        if not key:
            raise ValueError("SACRED_APPROVAL_KEY is not set")
        
        if len(key) < 32:
            raise ValueError("SACRED_APPROVAL_KEY must be at least 32 characters")
        
        # Check character diversity
        has_upper = any(c.isupper() for c in key)
        has_lower = any(c.islower() for c in key)
        has_digit = any(c.isdigit() for c in key)
        has_special = any(c in string.punctuation for c in key)
        
        diversity_score = sum([has_upper, has_lower, has_digit, has_special])
        
        if diversity_score < 3:
            raise ValueError("SACRED_APPROVAL_KEY lacks sufficient character diversity")
        
        # Check for common weak patterns
        weak_patterns = ['1234', 'abcd', 'password', 'secret', 'admin', 'test']
        key_lower = key.lower()
        for pattern in weak_patterns:
            if pattern in key_lower:
                raise ValueError(f"SACRED_APPROVAL_KEY contains weak pattern: {pattern}")
        
        return True
    
    @classmethod
    def sanitise_log_message(cls, message: str) -> str:
        """
        Sanitise log messages to prevent log injection
        OWASP A09:2021 - Security Logging and Monitoring Failures prevention
        """
        if not message:
            return ""
        
        # Remove line breaks and control characters
        sanitised = message.replace('\n', ' ').replace('\r', ' ')
        sanitised = ''.join(char for char in sanitised if char.isprintable() or char == ' ')
        
        # Limit length
        return sanitised[:1000]


class RateLimiter:
    """
    Simple in-memory rate limiter
    OWASP A04:2021 - Insecure Design prevention
    """
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed based on rate limit"""
        import time
        current_time = time.time()
        
        # Clean old entries
        self.requests = {
            k: v for k, v in self.requests.items()
            if current_time - v[-1] < self.window_seconds
        }
        
        # Check rate limit
        if identifier not in self.requests:
            self.requests[identifier] = [current_time]
            return True
        
        # Filter requests within window
        recent_requests = [
            t for t in self.requests[identifier]
            if current_time - t < self.window_seconds
        ]
        
        if len(recent_requests) < self.max_requests:
            recent_requests.append(current_time)
            self.requests[identifier] = recent_requests
            return True
        
        return False


class SecurityAuditLogger:
    """
    Security event logging
    OWASP A09:2021 - Security Logging and Monitoring Failures prevention
    Reference: https://owasp.org/www-project-logging-cheat-sheet/
    """
    
    def __init__(self, log_file: str = 'security_audit.log'):
        self.logger = logging.getLogger('security_audit')
        self.logger.setLevel(logging.INFO)
        
        # Create handler if it doesn't exist
        if not self.logger.handlers:
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def log_auth_attempt(self, user: str, success: bool, ip_address: str, reason: str = None):
        """Log authentication attempts"""
        message = f"AUTH_ATTEMPT: user={user}, success={success}, ip={ip_address}"
        if reason:
            message += f", reason={reason}"
        
        if success:
            self.logger.info(SecurityValidator.sanitise_log_message(message))
        else:
            self.logger.warning(SecurityValidator.sanitise_log_message(message))
    
    def log_access(self, user: str, resource: str, action: str, ip_address: str):
        """Log resource access"""
        message = f"ACCESS: user={user}, resource={resource}, action={action}, ip={ip_address}"
        self.logger.info(SecurityValidator.sanitise_log_message(message))
    
    def log_security_event(self, event_type: str, severity: str, details: str, ip_address: str = None):
        """Log security events"""
        message = f"SECURITY_EVENT: type={event_type}, severity={severity}, details={details}"
        if ip_address:
            message += f", ip={ip_address}"
        
        if severity == 'CRITICAL':
            self.logger.critical(SecurityValidator.sanitise_log_message(message))
        elif severity == 'HIGH':
            self.logger.error(SecurityValidator.sanitise_log_message(message))
        elif severity == 'MEDIUM':
            self.logger.warning(SecurityValidator.sanitise_log_message(message))
        else:
            self.logger.info(SecurityValidator.sanitise_log_message(message))
    
    def log_validation_failure(self, input_type: str, value: str, ip_address: str):
        """Log input validation failures"""
        # Truncate value for logging
        safe_value = str(value)[:50] if value else 'None'
        message = f"VALIDATION_FAILURE: type={input_type}, value={safe_value}, ip={ip_address}"
        self.logger.warning(SecurityValidator.sanitise_log_message(message))


# Initialise global instances
security_validator = SecurityValidator()
security_logger = SecurityAuditLogger()

# Export for easy import
__all__ = [
    'SecurityValidator',
    'RateLimiter', 
    'SecurityAuditLogger',
    'security_validator',
    'security_logger'
]