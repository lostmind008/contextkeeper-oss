# Security Implementation Guide for ContextKeeper v3.0

## Quick Start Security Fixes

This guide provides step-by-step instructions to implement the security fixes identified in the SECURITY_REPORT.md.

## 1. Install Security Dependencies

```bash
pip install flask-limiter flask-jwt-extended flask-talisman werkzeug
npm audit fix --force  # Fix npm vulnerabilities
```

## 2. Apply Critical Fixes to rag_agent.py

### Fix CORS Configuration (Line 1012)

Replace:
```python
self.socketio = SocketIO(self.app, cors_allowed_origins="*")
```

With:
```python
from src.security.security_config import SecurityConfig

self.socketio = SocketIO(
    self.app, 
    cors_allowed_origins=SecurityConfig.CORS_ORIGINS
)
```

### Fix Path Traversal (Lines 1632-1634)

Replace:
```python
dashboard_path = os.path.join(os.getcwd(), 'analytics_dashboard_live.html')
if os.path.exists(dashboard_path):
    return send_from_directory(os.getcwd(), 'analytics_dashboard_live.html')
```

With:
```python
from src.security.security_validator import SecurityValidator

try:
    dashboard_path = SecurityValidator.validate_file_path(
        'analytics_dashboard_live.html',
        base_dir=os.getcwd()
    )
    return send_from_directory(
        os.path.dirname(dashboard_path),
        os.path.basename(dashboard_path)
    )
except ValueError as e:
    logger.error(f"Path validation failed: {e}")
    return jsonify({'error': 'Dashboard not accessible'}), 403
```

### Add Input Validation to Query Endpoint (Lines 1031-1047)

Replace the query endpoint with:
```python
from src.security.security_validator import SecurityValidator, security_logger

@self.app.route('/query', methods=['POST'])
@limiter.limit("10 per minute")
def query():
    try:
        # Get client IP for logging
        client_ip = request.remote_addr
        
        # Validate and sanitise input
        data = SecurityValidator.validate_json_input(
            request.json,
            required_fields=['question']
        )
        
        question = SecurityValidator.sanitise_html_input(data.get('question', ''))
        k = min(int(data.get('k', 5)), 20)  # Limit max results
        
        # Validate project_id if provided
        project_id = data.get('project_id')
        if project_id:
            project_id = SecurityValidator.validate_project_id(project_id)
        
        # Log the query
        security_logger.log_access(
            user='anonymous',  # Add user when auth implemented
            resource='query',
            action='search',
            ip_address=client_ip
        )
        
        # Execute query
        results = self._run_async(self.agent.query(question, k, project_id))
        
        return jsonify(results)
        
    except ValueError as e:
        security_logger.log_validation_failure('query', str(e), client_ip)
        return jsonify({'error': 'Invalid input'}), 400
    except Exception as e:
        logger.error(f"Query error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500
```

## 3. Add Rate Limiting

Add to the top of rag_agent.py after imports:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from src.security.security_config import SecurityConfig

# Initialise rate limiter
limiter = Limiter(
    app=self.app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=os.environ.get('REDIS_URL', 'memory://')
)
```

Then add rate limiting decorators to endpoints:
```python
@limiter.limit("10 per minute")  # Add this line
@self.app.route('/query', methods=['POST'])

@limiter.limit("5 per minute")   # Add this line
@self.app.route('/ingest', methods=['POST'])

@limiter.limit("5 per hour")     # Add this line
@self.app.route('/sacred/approve', methods=['POST'])
```

## 4. Add Security Headers

Add after Flask app initialisation:
```python
from flask_talisman import Talisman
from src.security.security_config import SecurityConfig

# Apply security headers
if SecurityConfig.ENVIRONMENT == 'production':
    Talisman(
        self.app,
        force_https=True,
        strict_transport_security=True,
        content_security_policy={
            'default-src': "'self'",
            'script-src': "'self' 'unsafe-inline'",
            'style-src': "'self' 'unsafe-inline'",
            'img-src': "'self' data:",
            'connect-src': "'self' ws: wss:"
        }
    )
else:
    # Development mode - less strict
    @self.app.after_request
    def set_security_headers(response):
        for header, value in SecurityConfig.SECURITY_HEADERS.items():
            response.headers[header] = value
        return response
```

## 5. Fix XSS in Dashboard

Create a new file `analytics_dashboard_secure.html` with these changes:

Add DOMPurify library:
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/dompurify/3.0.6/purify.min.js"></script>
```

Replace all innerHTML usage with sanitised versions:
```javascript
// Instead of:
projectsGrid.innerHTML = htmlContent;

// Use:
projectsGrid.innerHTML = DOMPurify.sanitize(htmlContent);

// Or for text-only content:
element.textContent = textContent;  // Instead of innerHTML
```

## 6. Environment Variable Validation

Add to the start of rag_agent.py main():
```python
from src.security.security_config import SecurityConfig
from src.security.security_validator import SecurityValidator

# Validate environment on startup
issues = SecurityConfig.validate_environment()
if issues:
    logger.error(f"Security configuration issues: {issues}")
    if SecurityConfig.ENVIRONMENT == 'production':
        raise RuntimeError(f"Cannot start in production with security issues: {issues}")
    else:
        logger.warning("Running in development with security issues")

# Validate Sacred key
try:
    sacred_key = os.environ.get('SACRED_APPROVAL_KEY')
    if sacred_key:
        SecurityValidator.validate_sacred_key(sacred_key)
except ValueError as e:
    logger.error(f"Sacred key validation failed: {e}")
    if SecurityConfig.ENVIRONMENT == 'production':
        raise
```

## 7. Add Authentication (Optional - for production)

```python
from flask_jwt_extended import JWTManager, jwt_required, create_access_token

# Initialise JWT
jwt = JWTManager(self.app)
self.app.config.update(SecurityConfig.get_flask_config())

# Add login endpoint
@self.app.route('/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    data = request.json
    # Implement your authentication logic here
    # This is a placeholder
    if authenticate_user(data.get('username'), data.get('password')):
        access_token = create_access_token(identity=data.get('username'))
        return jsonify({'access_token': access_token})
    return jsonify({'error': 'Invalid credentials'}), 401

# Protect endpoints
@self.app.route('/query', methods=['POST'])
@jwt_required()  # Add this decorator
@limiter.limit("10 per minute")
def query():
    # ... existing code
```

## 8. Update Requirements

Add to requirements.txt:
```
flask-limiter>=3.5.0
flask-jwt-extended>=4.5.3
flask-talisman>=1.1.0
werkzeug>=3.0.0
cryptography>=41.0.0
```

## 9. Create Security Test Script

Create `test_security.py`:
```python
#!/usr/bin/env python3
"""Security test suite for ContextKeeper"""

import os
import sys
from src.security.security_validator import SecurityValidator
from src.security.security_config import SecurityConfig

def test_security():
    """Run security tests"""
    
    print("🔒 Running Security Tests...")
    
    # Test environment
    issues = SecurityConfig.validate_environment()
    if issues:
        print(f"❌ Environment issues: {issues}")
        return False
    else:
        print("✅ Environment validation passed")
    
    # Test path traversal protection
    try:
        SecurityValidator.validate_file_path('../../../etc/passwd', '/app')
        print("❌ Path traversal not blocked!")
        return False
    except ValueError:
        print("✅ Path traversal blocked")
    
    # Test XSS protection
    malicious = '<script>alert("XSS")</script>'
    sanitised = SecurityValidator.sanitise_html_input(malicious)
    if '<script>' in sanitised:
        print("❌ XSS not sanitised!")
        return False
    else:
        print("✅ XSS sanitisation working")
    
    # Test project ID validation
    try:
        SecurityValidator.validate_project_id('../../etc/passwd')
        print("❌ Invalid project ID accepted!")
        return False
    except ValueError:
        print("✅ Project ID validation working")
    
    print("\n✅ All security tests passed!")
    return True

if __name__ == '__main__':
    if not test_security():
        sys.exit(1)
```

## 10. Deployment Checklist

Before deploying to production:

- [ ] Run `python test_security.py`
- [ ] Run `npm audit` and fix all vulnerabilities
- [ ] Set strong values for all environment variables
- [ ] Enable HTTPS with valid certificates
- [ ] Configure firewall rules
- [ ] Set up monitoring and alerting
- [ ] Review and test all endpoints
- [ ] Enable authentication for production
- [ ] Set up regular security updates
- [ ] Configure backup and recovery

## Testing the Fixes

```bash
# Test CORS is restricted
curl -H "Origin: http://evil.com" http://localhost:5556/query

# Test rate limiting
for i in {1..15}; do curl -X POST http://localhost:5556/query -H "Content-Type: application/json" -d '{"question":"test"}'; done

# Test path traversal protection
curl -X GET http://localhost:5556/../../../../etc/passwd

# Run security tests
python test_security.py
```

## Monitoring

Set up monitoring for:
- Failed authentication attempts
- Rate limit violations
- Input validation failures
- Unusual access patterns
- Error rates

## Regular Security Tasks

- Weekly: Review security logs
- Monthly: Update dependencies (`npm audit`, `pip-audit`)
- Quarterly: Security assessment
- Annually: Penetration testing

## Support

For security issues or questions:
1. Check SECURITY_REPORT.md for detailed vulnerability information
2. Review OWASP guidelines at https://owasp.org/Top10/
3. Contact security team for critical issues

---

Remember: Security is an ongoing process, not a one-time fix. Stay vigilant and keep your dependencies updated.