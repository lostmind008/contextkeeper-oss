# ContextKeeper v3 Environment Setup Guide

Complete step-by-step guide for setting up environment variables and API keys for ContextKeeper v3.

## Table of Contents

1. [Quick Setup](#quick-setup)
2. [Google AI API Key Setup](#google-ai-api-key-setup)
3. [Sacred Layer Configuration](#sacred-layer-configuration)
4. [Optional Configuration](#optional-configuration)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)
7. [Security Best Practices](#security-best-practices)

## Quick Setup

### Step 1: Copy Environment Template

```bash
cd /path/to/contextkeeper
cp .env.template .env
```

### Step 2: Edit the .env File

```bash
# Using nano (beginner-friendly)
nano .env

# Using vim (advanced users)
vim .env
```

**Important**: Remove the `export` statements when copying to your `.env` file. Use `KEY=value` format instead of `export KEY=value`.

### Step 3: Configure Required Variables

You need to set these **required** variables:

1. `GEMINI_API_KEY`
2. `SACRED_APPROVAL_KEY`

> **Note:** There is no default value for `SACRED_APPROVAL_KEY`. ContextKeeper will raise an error if this key is not set.

## Google AI API Key Setup

### Option 1: Google AI Studio (Recommended)

This is the **easiest and most straightforward** method for most users.

#### Step 1: Visit Google AI Studio

Go to: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

#### Step 2: Sign In

- Sign in with your Google account
- Accept the terms of service if prompted

#### Step 3: Create API Key

1. Click **"Create API Key"**
2. Choose **"Create API key in new project"** (recommended for new users)
3. Copy the generated API key immediately
4. **Important**: Store this key securely - Google won't show it again

#### Step 4: Configure Your .env File

Open your `.env` file and add:

```env
GEMINI_API_KEY=your-actual-api-key-here
```

### Option 2: Google Cloud Console (Advanced Users)

Only use this if you need advanced Google Cloud features or have existing Google Cloud projects.

#### Step 1: Enable APIs

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable these APIs:
   - **Generative Language API**
   - **Vertex AI API** (if using Vertex AI features)

#### Step 2: Create API Key

1. Navigate to **APIs & Services** > **Credentials**
2. Click **"Create Credentials"** > **"API Key"**
3. Copy the generated key
4. Optionally: Restrict the key to specific APIs for security

#### Step 3: Configure Environment

```env
GEMINI_API_KEY=your-google-cloud-api-key

# Optional: Google Cloud specific settings
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=global
```

## Sacred Layer Configuration

The Sacred Layer is a security feature in ContextKeeper v3 that requires approval for sensitive operations.

### Generate a Secure Key

**Option 1: Using OpenSSL (Recommended)**

```bash
# Generate a 32-character random hex string
openssl rand -hex 32
```

**Option 2: Using Python**

```python
import secrets
print(secrets.token_hex(32))
```

**Option 3: Using Online Generator**

Visit a reputable password generator and create a 32+ character random string.

### Configure Sacred Key

Add to your `.env` file:

```env
SACRED_APPROVAL_KEY=your-64-character-hex-string-here
```

This key is mandatory for plan approval; operations will fail if it is absent.

**Example:**
```env
SACRED_APPROVAL_KEY=<your-64-char-hex-key>
```

## Optional Configuration

### Service Configuration

Most users can skip this section. These settings have sensible defaults.

```env
# RAG Agent Service URL (default: http://localhost:5556)
RAG_AGENT_URL=http://localhost:5556

# Server Configuration (defaults usually work)
CONTEXTKEEPER_HOST=127.0.0.1
CONTEXTKEEPER_PORT=5556
```

### Development Settings

Only modify these if you're developing ContextKeeper itself:

```env
# Enable debug mode (development only)
FLASK_DEBUG=true

# Set log level (INFO, DEBUG, WARNING, ERROR)
LOG_LEVEL=DEBUG

# Custom ChromaDB directory
CHROMADB_PERSIST_DIR=./custom_db_path
```

## Verification

### Step 1: Check Environment Variables

```bash
# Source your environment (if using shell)
source .env

# Verify Google API key is set
echo $GEMINI_API_KEY

# Verify Sacred key is set
echo $SACRED_APPROVAL_KEY
```

### Step 2: Test ContextKeeper

```bash
# Test basic functionality
python3 rag_agent.py --help

# Test Sacred layer (should not error)
python3 -c "from sacred_layer_implementation import SacredLayerManager; print('Sacred Layer OK')"
```

### Step 3: Run Basic Test

```bash
# Start ContextKeeper (should not show API key errors)
python3 rag_agent.py

# In another terminal, test the API
curl http://localhost:5556/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-07-30T...",
  "version": "3.0"
}
```

## Troubleshooting

### Common Issues

#### "No API key found" Error

**Problem**: ContextKeeper can't find your Google API key.

**Solutions**:
1. Verify `.env` file exists in the correct directory
2. Check that variable name is correct (`GEMINI_API_KEY`)
3. Ensure no extra spaces around the `=` sign
4. Verify the API key is valid (no extra characters, correct length)

**Test your key**:
```bash
# Should show your key (first few characters)
head -c 20 <<< "$GEMINI_API_KEY"
```

#### "Sacred approval key invalid" Error

**Problem**: Sacred Layer key is missing or invalid.

**Solutions**:
1. Ensure `SACRED_APPROVAL_KEY` is at least 32 characters
2. Use only alphanumeric characters (avoid special symbols)
3. Generate a new key using `openssl rand -hex 32`

#### "Permission denied" or "Quota exceeded"

**Problem**: API key doesn't have proper permissions or you've hit usage limits.

**Solutions**:
1. Check your Google AI Studio dashboard for quota usage
2. Verify your API key hasn't been restricted
3. Try creating a new API key
4. Check billing settings if using paid tier

#### ChromaDB Permission Errors

**Problem**: ContextKeeper can't write to the database directory.

**Solutions**:
```bash
# Fix permissions on database directory
chmod 755 ./rag_knowledge_db
chown -R $USER ./rag_knowledge_db

# Or use a custom directory
mkdir ~/contextkeeper_db
chmod 755 ~/contextkeeper_db
```

Then add to `.env`:
```env
CHROMADB_PERSIST_DIR=~/contextkeeper_db
```

### Debug Mode

Enable detailed logging to diagnose issues:

```env
LOG_LEVEL=DEBUG
FLASK_DEBUG=true
```

Then restart ContextKeeper and check the logs for detailed error messages.

### Getting Help

If you're still having issues:

1. Check the [Troubleshooting Guide](TROUBLESHOOTING.md)
2. Review the [Installation Guide](INSTALLATION.md)
3. Search existing [GitHub Issues](https://github.com/lostmind008/contextkeeper/issues)
4. Create a new issue with:
   - Your operating system
   - Python version (`python3 --version`)
   - Error messages (remove API keys from logs)
   - Steps to reproduce

## Security Best Practices

### API Key Security

1. **Never commit `.env` files to version control**
   ```bash
   # Ensure .env is in .gitignore
   echo ".env" >> .gitignore
   ```

2. **Use environment-specific keys**
   - Development: Separate API key with limited quota
   - Production: Different key with appropriate limits
   - Testing: Mock keys or separate test project

3. **Restrict API key permissions**
   - In Google Cloud Console, restrict keys to only needed APIs
   - Set referrer restrictions if deploying to web
   - Monitor usage regularly

4. **Rotate keys periodically**
   - Generate new keys every 90 days
   - Keep old keys active briefly during transition
   - Update all deployment environments

### Sacred Layer Security

1. **Generate strong keys**
   ```bash
   # Use cryptographically secure random generation
   openssl rand -hex 32
   ```

2. **Unique keys per environment**
   - Different Sacred keys for dev/staging/production
   - Never reuse Sacred keys across projects

3. **Secure storage**
   - Use secret management systems in production
   - Never log Sacred keys
   - Restrict access to environment files

### File Permissions

```bash
# Secure your environment file
chmod 600 .env

# Only owner can read/write
ls -la .env
# Should show: -rw-------
```

### Environment Isolation

For production deployments:

1. **Use container secrets**
   ```dockerfile
   # In Docker
   ENV GEMINI_API_KEY_FILE=/run/secrets/gemini_api_key
   ENV SACRED_APPROVAL_KEY_FILE=/run/secrets/sacred_key
   ```

2. **Use cloud secret managers**
   - AWS: AWS Secrets Manager
   - Google Cloud: Secret Manager
   - Azure: Key Vault

3. **Avoid shell history**
   ```bash
   # Don't export secrets in shell
   # Use .env files or secret management instead
   ```

---

## Next Steps

After completing environment setup:

1. Follow the [Installation Guide](INSTALLATION.md) to complete ContextKeeper setup
2. Review the [Usage Guide](USAGE.md) to start using ContextKeeper
3. Read the [API Reference](api/API_REFERENCE.md) for advanced features
4. Check out [Examples](../examples/) for common use cases

---

**Need help?** Check the [Troubleshooting Guide](TROUBLESHOOTING.md) or create an issue on GitHub.
