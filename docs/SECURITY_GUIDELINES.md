# ContextKeeper v3 Security Guidelines

Comprehensive security best practices for deploying and managing ContextKeeper v3 in production environments.

## Table of Contents

1. [API Key Security](#api-key-security)
2. [Sacred Layer Security](#sacred-layer-security)
3. [Environment Management](#environment-management)
4. [Network Security](#network-security)
5. [Data Protection](#data-protection)
6. [Deployment Security](#deployment-security)
7. [Monitoring and Auditing](#monitoring-and-auditing)
8. [Incident Response](#incident-response)

## API Key Security

### Google AI API Key Management

#### 1. Key Generation and Storage

**✅ Best Practices:**
```bash
# Generate keys in Google AI Studio (recommended)
# Visit: https://aistudio.google.com/app/apikey

# Store keys securely - never in code
GEMINI_API_KEY=your-secure-api-key-here
```

**❌ Avoid:**
```python
# NEVER hardcode API keys in source code
genai.configure(api_key="AIzaSyC123...") # DON'T DO THIS

# NEVER commit keys to version control
git add .env  # DANGEROUS - ensure .env is in .gitignore
```

#### 2. Key Rotation Strategy

**Implement regular key rotation:**

```bash
#!/bin/bash
# key_rotation.sh - Run every 90 days

# 1. Generate new key in Google AI Studio
NEW_KEY="your-new-api-key"

# 2. Test new key before deployment
export GEMINI_API_KEY_NEW=$NEW_KEY
python3 -c "import genai; genai.configure(api_key='$NEW_KEY'); print('New key works')"

# 3. Update production environment (with rollback plan)
cp .env .env.backup.$(date +%Y%m%d)
sed -i "s/GEMINI_API_KEY=.*/GEMINI_API_KEY=$NEW_KEY/" .env

# 4. Restart services
systemctl restart contextkeeper

# 5. Verify functionality
curl http://localhost:5556/health

# 6. Delete old key from Google AI Studio (after 24h grace period)
```

#### 3. Key Restriction and Monitoring

**Configure API key restrictions:**

```bash
# In Google Cloud Console (if using Cloud keys):
# 1. API restrictions: Limit to only required APIs
#    - Generative Language API
#    - (Optional) Vertex AI API

# 2. Application restrictions:
#    - HTTP referrers (for web deployments)
#    - IP addresses (for server deployments)

# 3. Set usage quotas and alerts
#    - Daily request limits
#    - Monthly spending caps
#    - Alert thresholds at 80% usage
```

**Monitor API usage:**

```python
# Usage monitoring script
import requests
import os
from datetime import datetime

def check_api_usage():
    """Monitor Google AI API usage and send alerts."""
    
    # This would integrate with Google Cloud Monitoring
    # or custom usage tracking
    
    usage_data = {
        'timestamp': datetime.now().isoformat(),
        'requests_today': get_daily_request_count(),
        'quota_remaining': get_quota_remaining(),
        'cost_estimate': calculate_daily_cost()
    }
    
    # Alert if approaching limits
    if usage_data['quota_remaining'] < 1000:
        send_alert("API quota running low", usage_data)
    
    return usage_data
```

## Sacred Layer Security

The Sacred Layer provides additional security for sensitive operations in ContextKeeper v3.

### 1. Sacred Key Generation

**Generate cryptographically secure keys:**

```bash
# Method 1: OpenSSL (recommended)
openssl rand -hex 32
# Output: 64-character hex string

# Method 2: Python secrets module
python3 -c "import secrets; print(secrets.token_hex(32))"

# Method 3: /dev/urandom (Linux/macOS)
head -c 32 /dev/urandom | xxd -p -c 32
```

**Key requirements:**
- Minimum 32 characters (64 hex characters recommended)
- Cryptographically random generation
- Unique per environment (dev/staging/production)
- Never derived from predictable sources

### 2. Sacred Key Management

**✅ Secure Configuration:**

```env
# .env file (600 permissions)
SACRED_APPROVAL_KEY=<your-64-char-hex-key>
```

**Production Secret Management:**

```yaml
# Docker Compose with secrets
version: '3.8'
services:
  contextkeeper:
    image: contextkeeper:v3
    secrets:
      - sacred_key
      - gemini_api_key
    environment:
      - SACRED_APPROVAL_KEY_FILE=/run/secrets/sacred_key
      - GEMINI_API_KEY_FILE=/run/secrets/gemini_api_key

secrets:
  sacred_key:
    external: true
  gemini_api_key:
    external: true
```

```bash
# Create Docker secrets
echo "your-sacred-key" | docker secret create sacred_key -
echo "your-api-key" | docker secret create gemini_api_key -
```

### 3. Sacred Layer Validation

**Implement proper validation:**

```python
# Example secure Sacred Layer implementation
import os
import hashlib
import hmac
from datetime import datetime
import logging

class SecureSacredLayer:
    def __init__(self):
        self.sacred_key = os.environ.get('SACRED_APPROVAL_KEY')
        if not self.sacred_key or len(self.sacred_key) < 32:
            raise ValueError("Sacred key must be at least 32 characters")
        
        # Log access attempts (without exposing key)
        self.logger = logging.getLogger('sacred_layer')
        
    def validate_approval(self, operation, user_key):
        """Validate Sacred Layer approval with timing attack protection."""
        
        # Log the attempt
        self.logger.info(f"Sacred approval attempted for operation: {operation}")
        
        # Use constant-time comparison to prevent timing attacks
        expected_hash = hashlib.sha256(self.sacred_key.encode()).hexdigest()
        provided_hash = hashlib.sha256(user_key.encode()).hexdigest()
        
        is_valid = hmac.compare_digest(expected_hash, provided_hash)
        
        if is_valid:
            self.logger.info(f"Sacred approval granted for operation: {operation}")
        else:
            self.logger.warning(f"Sacred approval DENIED for operation: {operation}")
            
        return is_valid
```

## Environment Management

### 1. Environment Isolation

**Separate environments with different credentials:**

```bash
# Development environment
cp .env.template .env.dev
# Set dev-specific keys with limited quotas

# Staging environment  
cp .env.template .env.staging
# Set staging keys that mirror production setup

# Production environment
cp .env.template .env.prod
# Set production keys with full capabilities
```

**Environment-specific configuration:**

```python
# config.py - Environment-based configuration
import os

class Config:
    """Base configuration class."""
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    SACRED_APPROVAL_KEY = os.environ.get('SACRED_APPROVAL_KEY')
    
class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    RATE_LIMIT = '1000/hour'
    
class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    RATE_LIMIT = '10000/hour'
    ENABLE_METRICS = True
    
# Select configuration based on environment
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
}
```

### 2. File Permissions

**Secure environment files:**

```bash
# Set restrictive permissions on sensitive files
chmod 600 .env .env.prod .env.staging
chmod 700 ~/.contextkeeper/

# Verify permissions
ls -la .env*
# Should show: -rw------- (600 permissions)

# Set up directory structure with proper permissions
mkdir -p ~/.contextkeeper/{configs,logs,data}
chmod 700 ~/.contextkeeper
chmod 600 ~/.contextkeeper/configs/*
chmod 644 ~/.contextkeeper/logs/*
```

### 3. Environment Validation

**Validate environment on startup:**

```python
# env_validator.py
import os
import sys
import re
from typing import List, Dict

class EnvironmentValidator:
    """Validate environment configuration for security compliance."""
    
    REQUIRED_VARS = [
        'GEMINI_API_KEY',
        'SACRED_APPROVAL_KEY'
    ]
    
    SECURITY_CHECKS = {
        'GEMINI_API_KEY': {
            'min_length': 30,
            'pattern': r'^AIza[0-9A-Za-z_-]{35}$',  # Google API key format
            'description': 'Gemini API key format'
        },
        'SACRED_APPROVAL_KEY': {
            'min_length': 32,
            'pattern': r'^[a-fA-F0-9]{64}$',  # 64-char hex
            'description': '64-character hexadecimal string'
        }
    }
    
    def validate_environment(self) -> Dict[str, any]:
        """Comprehensive environment validation."""
        
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'checks_passed': 0,
            'total_checks': 0
        }
        
        # Check required variables exist
        for var in self.REQUIRED_VARS:
            results['total_checks'] += 1
            value = os.environ.get(var)
            
            if not value:
                results['valid'] = False
                results['errors'].append(f"Missing required environment variable: {var}")
                continue
                
            # Security validation for each variable
            if var in self.SECURITY_CHECKS:
                check = self.SECURITY_CHECKS[var]
                
                # Length check
                if len(value) < check['min_length']:
                    results['valid'] = False
                    results['errors'].append(
                        f"{var} is too short (minimum {check['min_length']} characters)"
                    )
                    continue
                
                # Pattern check
                if 'pattern' in check and not re.match(check['pattern'], value):
                    results['valid'] = False
                    results['errors'].append(
                        f"{var} format invalid. Expected: {check['description']}"
                    )
                    continue
            
            results['checks_passed'] += 1
        
        # File permission checks
        env_files = ['.env', '.env.prod', '.env.staging']
        for env_file in env_files:
            if os.path.exists(env_file):
                stat = os.stat(env_file)
                permissions = oct(stat.st_mode)[-3:]
                
                if permissions != '600':
                    results['warnings'].append(
                        f"{env_file} has permissions {permissions}, should be 600"
                    )
        
        return results

# Usage in application startup
def startup_security_check():
    """Run security validation on application startup."""
    
    validator = EnvironmentValidator()
    results = validator.validate_environment()
    
    if not results['valid']:
        print("❌ SECURITY VALIDATION FAILED")
        for error in results['errors']:
            print(f"   ERROR: {error}")
        sys.exit(1)
    
    if results['warnings']:
        print("⚠️  SECURITY WARNINGS:")
        for warning in results['warnings']:
            print(f"   WARNING: {warning}")
    
    print(f"✅ Security validation passed ({results['checks_passed']}/{results['total_checks']} checks)")
```

## Network Security

### 1. TLS/HTTPS Configuration

**Always use TLS in production:**

```python
# secure_server.py
from flask import Flask
import ssl

app = Flask(__name__)

def create_secure_context():
    """Create SSL context for HTTPS."""
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain('cert.pem', 'key.pem')
    
    # Security hardening
    context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
    context.options |= ssl.OP_NO_SSLv2
    context.options |= ssl.OP_NO_SSLv3
    context.options |= ssl.OP_NO_TLSv1
    context.options |= ssl.OP_NO_TLSv1_1
    
    return context

if __name__ == '__main__':
    # Production HTTPS server
    context = create_secure_context()
    app.run(host='0.0.0.0', port=5556, ssl_context=context)
```

### 2. Firewall Configuration

**Configure restrictive firewall rules:**

```bash
# Ubuntu/Debian UFW configuration
ufw default deny incoming
ufw default allow outgoing

# Allow SSH (adjust port as needed)
ufw allow 22/tcp

# Allow ContextKeeper HTTPS only
ufw allow 5556/tcp

# Allow outbound Google AI API calls
ufw allow out 443/tcp

# Enable firewall
ufw enable

# Verify configuration
ufw status verbose
```

### 3. Rate Limiting

**Implement API rate limiting:**

```python
# rate_limiter.py
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis

app = Flask(__name__)

# Redis-backed rate limiter for distributed deployments
limiter = Limiter(
    app,
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379",
    default_limits=["1000 per hour", "100 per minute"]
)

@app.route('/api/query')
@limiter.limit("10 per minute")  # Stricter limit for expensive operations
def query_api():
    """Rate-limited API endpoint."""
    return jsonify({"status": "ok"})

@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded."""
    return jsonify({
        "error": "Rate limit exceeded",
        "message": str(e.description),
        "retry_after": e.retry_after
    }), 429
```

## Data Protection

### 1. Data Encryption

**Encrypt sensitive data at rest:**

```python
# encryption.py
from cryptography.fernet import Fernet
import os
import base64

class DataEncryption:
    """Handle encryption of sensitive data."""
    
    def __init__(self):
        # Generate or load encryption key
        key = os.environ.get('ENCRYPTION_KEY')
        if not key:
            key = Fernet.generate_key()
            print(f"Generated new encryption key: {key.decode()}")
            print("Store this securely in ENCRYPTION_KEY environment variable")
        else:
            key = key.encode()
        
        self.cipher = Fernet(key)
    
    def encrypt_text(self, text: str) -> str:
        """Encrypt text data."""
        return self.cipher.encrypt(text.encode()).decode()
    
    def decrypt_text(self, encrypted_text: str) -> str:
        """Decrypt text data."""
        return self.cipher.decrypt(encrypted_text.encode()).decode()

# Usage for sensitive data storage
encryptor = DataEncryption()

# Encrypt user queries before storing
encrypted_query = encryptor.encrypt_text("sensitive user query")

# Store in database/logs with encryption
# Always decrypt before processing
original_query = encryptor.decrypt_text(encrypted_query)
```

### 2. Database Security

**Secure ChromaDB configuration:**

```python
# secure_chromadb.py
import chromadb
from chromadb.config import Settings
import os

# Secure ChromaDB settings
secure_settings = Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./secure_chromadb",
    chroma_server_auth_credentials_provider="token",
    chroma_server_auth_credentials="your-secure-token",
    chroma_server_auth_token_transport_header="X-Chroma-Token"
)

# Create client with authentication
client = chromadb.Client(secure_settings)

# Set up access control
def setup_database_security():
    """Configure database security settings."""
    
    # Set restrictive file permissions
    os.chmod("./secure_chromadb", 0o700)
    
    # Configure backup encryption
    backup_key = os.environ.get('BACKUP_ENCRYPTION_KEY')
    if backup_key:
        # Implement encrypted backups
        pass
```

### 3. Logging and Auditing

**Implement secure logging:**

```python
# secure_logging.py
import logging
import logging.handlers
import hashlib
import json
from datetime import datetime

class SecureFormatter(logging.Formatter):
    """Custom formatter that sanitizes sensitive data."""
    
    SENSITIVE_FIELDS = ['api_key', 'sacred_key', 'password', 'token']
    
    def format(self, record):
        # Sanitize log message 
        message = super().format(record)
        
        # Redact sensitive information
        for field in self.SENSITIVE_FIELDS:
            if field in message.lower():
                # Replace with hash of first/last 4 characters
                message = self._redact_sensitive_field(message, field)
        
        return message
    
    def _redact_sensitive_field(self, message, field):
        """Redact sensitive fields while preserving some identification."""
        import re
        
        # Pattern to match field=value or field: value
        pattern = rf'({field}[=:]\s*)([^\s,}}]+)'
        
        def redact_match(match):
            prefix = match.group(1)
            value = match.group(2)
            
            if len(value) > 8:
                # Show first 4 and last 4 characters, hash the middle
                visible = f"{value[:4]}...{value[-4:]}"
                hashed = hashlib.sha256(value.encode()).hexdigest()[:8]
                return f"{prefix}{visible}[{hashed}]"
            else:
                return f"{prefix}[REDACTED]"
        
        return re.sub(pattern, redact_match, message, flags=re.IGNORECASE)

# Configure secure logging
def setup_secure_logging():
    """Set up secure, auditable logging."""
    
    # Create logger
    logger = logging.getLogger('contextkeeper_security')
    logger.setLevel(logging.INFO)
    
    # Rotating file handler with secure permissions
    handler = logging.handlers.RotatingFileHandler(
        '/var/log/contextkeeper/security.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10,
        mode='a'
    )
    
    # Set secure file permissions
    os.chmod('/var/log/contextkeeper/security.log', 0o640)
    
    # Use secure formatter
    formatter = SecureFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

# Usage
security_logger = setup_secure_logging()

def log_security_event(event_type, details):
    """Log security-relevant events."""
    
    event = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'details': details,
        'source_ip': request.remote_addr if 'request' in globals() else 'unknown'
    }
    
    security_logger.info(json.dumps(event))

# Example usage
log_security_event('api_key_rotation', {'old_key_hash': 'abc123', 'new_key_hash': 'def456'})
log_security_event('sacred_approval_attempt', {'operation': 'plan_approval', 'success': True})
```

## Deployment Security

### 1. Container Security

**Secure Docker deployment:**

```dockerfile
# Dockerfile.secure
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r contextkeeper && useradd -r -g contextkeeper contextkeeper

# Set up secure directories
RUN mkdir -p /app /app/data /app/logs && \
    chown -R contextkeeper:contextkeeper /app

# Install security updates
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy application
COPY --chown=contextkeeper:contextkeeper . /app/
WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Switch to non-root user
USER contextkeeper

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5556/health || exit 1

# Secure defaults
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

EXPOSE 5556
CMD ["python3", "rag_agent.py"]
```

**Docker Compose with security:**

```yaml
# docker-compose.secure.yml
version: '3.8'

services:
  contextkeeper:
    build: 
      context: .
      dockerfile: Dockerfile.secure
    
    # Security settings
    read_only: true
    tmpfs:
      - /tmp:rw,noexec,nosuid,size=50m
    
    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
    
    # Network security
    networks:
      - contextkeeper_net
    
    # Secrets management
    secrets:
      - gemini_api_key
      - sacred_approval_key

    environment:
      - GEMINI_API_KEY_FILE=/run/secrets/gemini_api_key
      - SACRED_APPROVAL_KEY_FILE=/run/secrets/sacred_approval_key
    
    # Volume security
    volumes:
      - contextkeeper_data:/app/data:rw
      - contextkeeper_logs:/app/logs:rw
    
    # Health monitoring
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5556/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

networks:
  contextkeeper_net:
    driver: bridge
    internal: false

volumes:
  contextkeeper_data:
    driver: local
  contextkeeper_logs:
    driver: local

secrets:
  gemini_api_key:
    external: true
  sacred_approval_key:
    external: true
```

### 2. Kubernetes Security

**Secure Kubernetes deployment:**

```yaml
# k8s-security.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: contextkeeper
  namespace: contextkeeper
spec:
  replicas: 2
  selector:
    matchLabels:
      app: contextkeeper
  template:
    metadata:
      labels:
        app: contextkeeper
    spec:
      # Security context
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        runAsGroup: 1000
        fsGroup: 1000
      
      containers:
      - name: contextkeeper
        image: contextkeeper:secure
        
        # Container security
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        
        # Resource limits
        resources:
          limits:
            cpu: "2"
            memory: "2Gi"
          requests:
            cpu: "500m"
            memory: "512Mi"
        
        # Environment from secrets
        env:
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: contextkeeper-secrets
              key: gemini-api-key
        - name: SACRED_APPROVAL_KEY
          valueFrom:
            secretKeyRef:
              name: contextkeeper-secrets
              key: sacred-approval-key
        
        # Volumes
        volumeMounts:
        - name: data-volume
          mountPath: /app/data
        - name: logs-volume
          mountPath: /app/logs
        - name: tmp-volume
          mountPath: /tmp
        
        # Health checks
        livenessProbe:
          httpGet:
            path: /health
            port: 5556
          initialDelaySeconds: 30
          periodSeconds: 10
        
        readinessProbe:
          httpGet:
            path: /ready
            port: 5556
          initialDelaySeconds: 5
          periodSeconds: 5
      
      volumes:
      - name: data-volume
        persistentVolumeClaim:
          claimName: contextkeeper-data
      - name: logs-volume
        persistentVolumeClaim:
          claimName: contextkeeper-logs
      - name: tmp-volume
        emptyDir:
          sizeLimit: 50Mi

---
# Network policy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: contextkeeper-network-policy
  namespace: contextkeeper
spec:
  podSelector:
    matchLabels:
      app: contextkeeper
  policyTypes:
  - Ingress
  - Egress
  
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: frontend
    ports:
    - protocol: TCP
      port: 5556
  
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 443  # HTTPS for Google API calls
    - protocol: TCP
      port: 53   # DNS
  - to: []
    ports:
    - protocol: UDP
      port: 53   # DNS
```

## Monitoring and Auditing

### 1. Security Monitoring

**Implement comprehensive monitoring:**

```python
# security_monitor.py
import psutil
import logging
import requests
from datetime import datetime
import threading
import time

class SecurityMonitor:
    """Monitor system security metrics and alert on anomalies."""
    
    def __init__(self):
        self.logger = logging.getLogger('security_monitor')
        self.metrics = {
            'api_requests': 0,
            'failed_auth': 0,
            'resource_usage': {},
            'network_connections': []
        }
        
    def monitor_api_usage(self):
        """Monitor API usage patterns for anomalies."""
        
        # Check request rate
        if self.metrics['api_requests'] > 10000:  # per hour
            self.alert('HIGH_API_USAGE', {
                'requests_per_hour': self.metrics['api_requests'],
                'threshold': 10000
            })
        
        # Check authentication failures
        if self.metrics['failed_auth'] > 10:  # per hour
            self.alert('HIGH_AUTH_FAILURES', {
                'failures_per_hour': self.metrics['failed_auth'],
                'threshold': 10
            })
    
    def monitor_resource_usage(self):
        """Monitor system resource usage."""
        
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        self.metrics['resource_usage'] = {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'disk_percent': disk.percent,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Alert on high usage
        if cpu_percent > 90:
            self.alert('HIGH_CPU_USAGE', {'cpu_percent': cpu_percent})
        
        if memory.percent > 90:
            self.alert('HIGH_MEMORY_USAGE', {'memory_percent': memory.percent})
    
    def monitor_network_connections(self):
        """Monitor network connections for suspicious activity."""
        
        connections = psutil.net_connections(kind='inet')
        
        # Track connections to unexpected destinations
        external_connections = []
        for conn in connections:
            if conn.status == 'ESTABLISHED' and conn.raddr:
                # Check if connection is to expected services
                if not self.is_expected_connection(conn.raddr[0]):
                    external_connections.append({
                        'remote_ip': conn.raddr[0],
                        'remote_port': conn.raddr[1],
                        'local_port': conn.laddr[1]
                    })
        
        if external_connections:
            self.alert('UNEXPECTED_CONNECTIONS', {
                'connections': external_connections
            })
    
    def is_expected_connection(self, ip):
        """Check if IP is in allowlist of expected connections."""
        
        expected_ranges = [
            '142.250.',  # Google services
            '172.217.',  # Google services
            '216.58.',   # Google services
            '8.8.8.8',   # Google DNS
            '8.8.4.4'    # Google DNS
        ]
        
        return any(ip.startswith(range_prefix) for range_prefix in expected_ranges)
    
    def alert(self, alert_type, details):
        """Send security alert."""
        
        alert = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': alert_type,
            'severity': self.get_alert_severity(alert_type),
            'details': details,
            'hostname': os.uname().nodename
        }
        
        # Log the alert
        self.logger.warning(f"Security Alert: {alert_type}", extra=alert)
        
        # Send to monitoring system
        self.send_to_monitoring(alert)
    
    def get_alert_severity(self, alert_type):
        """Determine alert severity level."""
        
        high_severity = ['HIGH_AUTH_FAILURES', 'UNEXPECTED_CONNECTIONS']
        medium_severity = ['HIGH_API_USAGE', 'HIGH_MEMORY_USAGE']
        
        if alert_type in high_severity:
            return 'HIGH'
        elif alert_type in medium_severity:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def send_to_monitoring(self, alert):
        """Send alert to monitoring system."""
        
        # Example: Send to Slack, PagerDuty, etc.
        webhook_url = os.environ.get('SECURITY_WEBHOOK_URL')
        if webhook_url:
            try:
                requests.post(webhook_url, json=alert, timeout=10)
            except Exception as e:
                self.logger.error(f"Failed to send alert: {e}")

# Start monitoring
monitor = SecurityMonitor()

def start_security_monitoring():
    """Start security monitoring threads."""
    
    def monitoring_loop():
        while True:
            monitor.monitor_api_usage()
            monitor.monitor_resource_usage() 
            monitor.monitor_network_connections()
            time.sleep(60)  # Check every minute
    
    thread = threading.Thread(target=monitoring_loop, daemon=True)
    thread.start()
```

### 2. Audit Logging

**Comprehensive audit trail:**

```python
# audit_logger.py
import json
import logging
from datetime import datetime
from functools import wraps
from flask import request, g

class AuditLogger:
    """Comprehensive audit logging for security events."""
    
    def __init__(self):
        self.logger = logging.getLogger('audit')
        
        # Configure audit log handler
        handler = logging.handlers.RotatingFileHandler(
            '/var/log/contextkeeper/audit.log',
            maxBytes=50*1024*1024,  # 50MB
            backupCount=20
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - AUDIT - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_event(self, event_type, **kwargs):
        """Log audit event with standardized format."""
        
        audit_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'user_id': getattr(g, 'user_id', 'anonymous'),
            'session_id': getattr(g, 'session_id', None),
            'source_ip': request.remote_addr if request else None,
            'user_agent': request.headers.get('User-Agent') if request else None,
            **kwargs
        }
        
        self.logger.info(json.dumps(audit_record))
    
    def audit_api_call(self, func):
        """Decorator to audit API calls."""
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            
            try:
                result = func(*args, **kwargs)
                
                # Log successful API call
                self.log_event(
                    'API_CALL_SUCCESS',
                    endpoint=request.endpoint,
                    method=request.method,
                    duration_ms=(datetime.utcnow() - start_time).total_seconds() * 1000,
                    status_code=getattr(result, 'status_code', 200)
                )
                
                return result
                
            except Exception as e:
                # Log failed API call
                self.log_event(
                    'API_CALL_FAILURE',
                    endpoint=request.endpoint,
                    method=request.method,
                    duration_ms=(datetime.utcnow() - start_time).total_seconds() * 1000,
                    error_type=type(e).__name__,
                    error_message=str(e)
                )
                
                raise
        
        return wrapper
    
    def audit_sacred_operation(self, operation, success, **details):
        """Audit Sacred Layer operations."""
        
        self.log_event(
            'SACRED_OPERATION',
            operation=operation,
            success=success,
            **details
        )
    
    def audit_auth_event(self, event_type, success, **details):
        """Audit authentication events."""
        
        self.log_event(
            f'AUTH_{event_type}',
            success=success,
            **details
        )

# Global audit logger instance
audit = AuditLogger()

# Usage examples:
@audit.audit_api_call
def sensitive_api_endpoint():
    """Example API endpoint with audit logging."""
    return {"status": "ok"}

# Manual audit logging
audit.audit_sacred_operation('plan_approval', True, plan_id='123')
audit.audit_auth_event('API_KEY_VALIDATION', False, reason='invalid_key')
```

## Incident Response

### 1. Incident Response Plan

**Preparation for security incidents:**

```python
# incident_response.py
import json
import smtplib
from email.mime.text import MimeText
from datetime import datetime
import subprocess

class IncidentResponse:
    """Automated incident response system."""
    
    SEVERITY_LEVELS = {
        'LOW': 1,
        'MEDIUM': 2, 
        'HIGH': 3,
        'CRITICAL': 4
    }
    
    def __init__(self):
        self.response_team_emails = [
            'security@yourcompany.com',
            'devops@yourcompany.com'
        ]
    
    def handle_incident(self, incident_type, severity, details):
        """Handle security incident with appropriate response."""
        
        incident = {
            'id': f"INC-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            'timestamp': datetime.utcnow().isoformat(),
            'type': incident_type,
            'severity': severity,
            'details': details,
            'status': 'ACTIVE'
        }
        
        # Log incident
        self.log_incident(incident)
        
        # Execute response based on severity
        if self.SEVERITY_LEVELS.get(severity, 1) >= 3:  # HIGH or CRITICAL
            self.execute_immediate_response(incident)
        
        # Notify response team
        self.notify_team(incident)
        
        return incident
    
    def execute_immediate_response(self, incident):
        """Execute immediate response for high-severity incidents."""
        
        incident_type = incident['type']
        
        if incident_type == 'API_KEY_COMPROMISE':
            self.revoke_api_access()
            self.rotate_sacred_keys()
            
        elif incident_type == 'UNAUTHORIZED_ACCESS':
            self.block_suspicious_ips(incident['details'].get('source_ips', []))
            
        elif incident_type == 'DATA_BREACH':
            self.enable_emergency_mode()
            self.create_data_backup()
        
        # Update incident status
        incident['response_actions'] = self.get_response_actions(incident_type)
        incident['status'] = 'RESPONDING'
    
    def revoke_api_access(self):
        """Revoke API access in emergency."""
        
        try:
            # Disable API endpoints
            subprocess.run(['systemctl', 'stop', 'contextkeeper'], check=True)
            
            # Create temporary firewall block
            subprocess.run([
                'iptables', '-A', 'INPUT', '-p', 'tcp', 
                '--dport', '5556', '-j', 'DROP'
            ], check=True)
            
            return True
            
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to revoke API access: {e}")
            return False
    
    def rotate_sacred_keys(self):
        """Emergency Sacred Layer key rotation."""
        
        # Generate new key
        new_key = secrets.token_hex(32)
        
        # Update environment (requires restart)
        with open('.env.emergency', 'w') as f:
            f.write(f"SACRED_APPROVAL_KEY={new_key}\n")
        
        # Log key rotation
        audit.audit_sacred_operation(
            'emergency_key_rotation', 
            True, 
            reason='security_incident'
        )
    
    def block_suspicious_ips(self, ip_addresses):
        """Block suspicious IP addresses."""
        
        for ip in ip_addresses:
            try:
                subprocess.run([
                    'iptables', '-A', 'INPUT', '-s', ip, '-j', 'DROP'
                ], check=True)
                
                logging.info(f"Blocked suspicious IP: {ip}")
                
            except subprocess.CalledProcessError as e:
                logging.error(f"Failed to block IP {ip}: {e}")
    
    def notify_team(self, incident):
        """Notify incident response team."""
        
        subject = f"SECURITY INCIDENT - {incident['severity']} - {incident['type']}"
        
        body = f"""
        Security Incident Alert
        
        Incident ID: {incident['id']}
        Timestamp: {incident['timestamp']}
        Type: {incident['type']}
        Severity: {incident['severity']}
        Status: {incident['status']}
        
        Details:
        {json.dumps(incident['details'], indent=2)}
        
        Response Actions:
        {json.dumps(incident.get('response_actions', []), indent=2)}
        
        This is an automated alert from ContextKeeper Security System.
        """
        
        # Send email notification
        self.send_email_alert(subject, body)
        
        # Send to Slack/Teams if configured
        self.send_chat_alert(incident)
    
    def send_email_alert(self, subject, body):
        """Send email alert to response team."""
        
        try:
            msg = MimeText(body)
            msg['Subject'] = subject
            msg['From'] = 'security@contextkeeper.local'
            msg['To'] = ', '.join(self.response_team_emails)
            
            # Configure SMTP
            smtp_server = os.environ.get('SMTP_SERVER', 'localhost')
            server = smtplib.SMTP(smtp_server)
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            logging.error(f"Failed to send email alert: {e}")

# Usage
incident_response = IncidentResponse()

def detect_security_incident():
    """Example incident detection."""
    
    # Detect API key compromise
    if suspicious_api_usage_detected():
        incident_response.handle_incident(
            'API_KEY_COMPROMISE',
            'CRITICAL',
            {
                'suspicious_requests': 1000,
                'timeframe': '5 minutes',
                'source_ips': ['192.168.1.100', '10.0.1.50']
            }
        )
```

### 2. Recovery Procedures

**Recovery and restoration procedures:**

```bash
#!/bin/bash
# recovery_procedures.sh

# ContextKeeper Security Incident Recovery

set -e

BACKUP_DIR="/var/backups/contextkeeper"
LOG_FILE="/var/log/contextkeeper/recovery.log"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# 1. Assessment Phase
assess_damage() {
    log "Starting damage assessment..."
    
    # Check system integrity
    if ! systemctl is-active --quiet contextkeeper; then
        log "WARNING: ContextKeeper service is not running"
    fi
    
    # Check database integrity
    if [ -f "./rag_knowledge_db/chroma.sqlite3" ]; then
        sqlite3 ./rag_knowledge_db/chroma.sqlite3 "PRAGMA integrity_check;" > /tmp/db_check.txt
        if grep -q "ok" /tmp/db_check.txt; then
            log "Database integrity: OK"
        else
            log "ERROR: Database corruption detected"
        fi
    fi
    
    # Check file permissions
    if [ -f ".env" ]; then
        PERMS=$(stat -c "%a" .env)
        if [ "$PERMS" != "600" ]; then
            log "WARNING: .env file has incorrect permissions: $PERMS"
        fi
    fi
}

# 2. Isolation Phase
isolate_system() {
    log "Isolating compromised system..."
    
    # Stop services
    systemctl stop contextkeeper || true
    
    # Block network access temporarily
    iptables -A INPUT -p tcp --dport 5556 -j DROP
    
    # Create system snapshot
    tar -czf "$BACKUP_DIR/emergency_snapshot_$(date +%Y%m%d_%H%M%S).tar.gz" \
        --exclude='.env' \
        --exclude='*.log' \
        .
    
    log "System isolated and snapshot created"
}

# 3. Evidence Collection
collect_evidence() {
    log "Collecting forensic evidence..."
    
    EVIDENCE_DIR="/var/log/contextkeeper/incident_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$EVIDENCE_DIR"
    
    # Collect logs
    cp /var/log/contextkeeper/*.log "$EVIDENCE_DIR/"
    
    # Collect system information
    ps aux > "$EVIDENCE_DIR/processes.txt"
    netstat -tulpn > "$EVIDENCE_DIR/network.txt"
    ss -tulpn > "$EVIDENCE_DIR/sockets.txt"
    
    # Collect configuration
    cp .env.template "$EVIDENCE_DIR/"
    
    # Hash evidence files
    find "$EVIDENCE_DIR" -type f -exec sha256sum {} \; > "$EVIDENCE_DIR/evidence_hashes.txt"
    
    log "Evidence collected in $EVIDENCE_DIR"
}

# 4. Clean Recovery
clean_recovery() {
    log "Starting clean recovery process..."
    
    # Remove compromised environment
    if [ -f ".env" ]; then
        cp .env .env.compromised
        rm .env
    fi
    
    # Generate new secrets
    NEW_SACRED_KEY=$(openssl rand -hex 32)
    
    # Create new environment file
    cp .env.template .env
    sed -i "s/your-secret-approval-key-minimum-32-characters/$NEW_SACRED_KEY/" .env
    
    # Prompt for new API key
    echo "Please enter new Google API key:"
    read -s NEW_API_KEY
    sed -i "s/your-google-ai-api-key-here/$NEW_API_KEY/" .env
    
    # Set secure permissions
    chmod 600 .env
    
    # Clear and rebuild database
    if [ -d "./rag_knowledge_db" ]; then
        mv ./rag_knowledge_db ./rag_knowledge_db.compromised
        mkdir ./rag_knowledge_db
        chmod 700 ./rag_knowledge_db
    fi
    
    log "Environment cleaned and secrets rotated"
}

# 5. Secure Restart
secure_restart() {
    log "Restarting with enhanced security..."
    
    # Remove temporary firewall blocks
    iptables -D INPUT -p tcp --dport 5556 -j DROP || true
    
    # Update system packages
    apt update && apt upgrade -y
    
    # Restart with new configuration
    systemctl start contextkeeper
    
    # Verify health
    sleep 10
    if curl -f http://localhost:5556/health; then
        log "Recovery successful - ContextKeeper is healthy"
    else
        log "ERROR: Recovery failed - ContextKeeper health check failed"
        exit 1
    fi
    
    # Enable enhanced monitoring
    systemctl enable contextkeeper-monitor
    systemctl start contextkeeper-monitor
    
    log "Recovery completed successfully"
}

# 6. Post-Incident Actions
post_incident_actions() {
    log "Executing post-incident actions..."
    
    # Create incident report
    cat > "$EVIDENCE_DIR/incident_report.md" << EOF
# Security Incident Report

## Timeline
- Detection: $(date)
- Response: $(date)
- Recovery: $(date)

## Actions Taken
- System isolated
- Evidence collected
- Secrets rotated
- Database rebuilt
- Services restarted

## Recommendations
1. Review access logs for breach indicators
2. Implement additional monitoring
3. Update incident response procedures
4. Conduct security awareness training

## Evidence Location
$EVIDENCE_DIR
EOF
    
    # Schedule security audit
    echo "0 2 * * 0 /usr/local/bin/security_audit.sh" >> /etc/crontab
    
    log "Post-incident actions completed"
}

# Main recovery workflow
main() {
    log "Starting ContextKeeper security incident recovery"
    
    assess_damage
    isolate_system
    collect_evidence
    clean_recovery
    secure_restart
    post_incident_actions
    
    log "Recovery process completed successfully"
    
    echo "
    RECOVERY COMPLETED
    
    Next Steps:
    1. Review incident report: $EVIDENCE_DIR/incident_report.md
    2. Update monitoring and alerting
    3. Conduct post-incident review
    4. Update security documentation
    
    New secrets have been generated. Ensure they are backed up securely.
    "
}

# Run recovery if called directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

---

## Summary

This security guide provides comprehensive protection for ContextKeeper v3 deployments:

### Key Security Controls
- **API Key Management**: Secure generation, storage, rotation, and monitoring
- **Sacred Layer Security**: Cryptographically secure approval system
- **Environment Isolation**: Separate configurations for dev/staging/production
- **Network Security**: TLS, firewall rules, and rate limiting
- **Data Protection**: Encryption at rest and in transit
- **Monitoring**: Real-time security monitoring and alerting
- **Incident Response**: Automated response and recovery procedures

### Implementation Priority
1. **Immediate** (Deploy first):
   - API key security and rotation
   - Environment file permissions
   - Sacred Layer key generation
   - Basic monitoring

2. **Short-term** (First month):
   - TLS/HTTPS configuration
   - Rate limiting
   - Audit logging
   - Container security

3. **Long-term** (Ongoing):
   - Advanced monitoring
   - Incident response automation
   - Security testing
   - Team training

### Compliance Considerations
This guide addresses common security frameworks:
- **SOC 2**: Logging, monitoring, access controls
- **ISO 27001**: Risk management, incident response
- **NIST**: Framework implementation, continuous monitoring
- **GDPR**: Data protection, encryption, audit trails

**Remember**: Security is an ongoing process, not a one-time setup. Regularly review and update these procedures based on new threats and organizational changes.