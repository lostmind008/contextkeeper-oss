#!/usr/bin/env python3
"""
Test script to verify ContextKeeper v3 DevContainer setup
"""

import sys
import os
import importlib.util

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return version.major >= 3 and version.minor >= 9

def check_environment_variables():
    """Check required environment variables"""
    env_vars = {
        "PYTHONPATH": "Python module path",
        "FLASK_ENV": "Flask environment",
        "WORKSPACE_FOLDER": "Workspace folder"
    }
    
    all_good = True
    for var, desc in env_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✓ {var} is set: {value}")
        else:
            print(f"✗ {var} is not set ({desc})")
            all_good = False
    
    return all_good

def check_required_packages():
    """Check if required packages are installed"""
    packages = {
        "google.genai": "Google AI SDK",
        "chromadb": "ChromaDB",
        "flask": "Flask",
        "watchdog": "File watcher",
        "tiktoken": "Token counter",
        "git": "GitPython",
        "sklearn": "Scikit-learn"
    }
    
    all_good = True
    for package, name in packages.items():
        spec = importlib.util.find_spec(package.split('.')[0])
        if spec is not None:
            print(f"✓ {name} installed")
        else:
            print(f"✗ {name} not found")
            all_good = False
    
    return all_good

def check_directories():
    """Check if required directories exist"""
    dirs = [
        "rag_knowledge_db",
        "logs",
        "scripts",
        "tests",
        "docs",
        "mcp-server"
    ]
    
    all_good = True
    for dir_name in dirs:
        if os.path.exists(dir_name):
            print(f"✓ Directory '{dir_name}' exists")
        else:
            print(f"✗ Directory '{dir_name}' not found")
            all_good = False
    
    return all_good

def check_config_files():
    """Check if configuration files exist"""
    files = {
        ".env": "Environment configuration",
        ".env.template": "Environment template",
        "requirements.txt": "Python dependencies",
        ".devcontainer/devcontainer.json": "DevContainer config",
        ".devcontainer/setup.sh": "Setup script"
    }
    
    all_good = True
    for file_name, desc in files.items():
        if os.path.exists(file_name):
            print(f"✓ {desc} exists ({file_name})")
        else:
            print(f"✗ {desc} not found ({file_name})")
            all_good = False
    
    # Check if .env has placeholder values
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            content = f.read()
            if "your-google-ai-api-key-here" in content:
                print("⚠️  WARNING: .env contains placeholder API keys - please update!")
    
    return all_good

def main():
    """Run all checks"""
    print("=" * 60)
    print("ContextKeeper v3 DevContainer Setup Verification")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Environment Variables", check_environment_variables),
        ("Required Packages", check_required_packages),
        ("Project Directories", check_directories),
        ("Configuration Files", check_config_files)
    ]
    
    all_passed = True
    for name, check_func in checks:
        print(f"\n{name}:")
        print("-" * 40)
        passed = check_func()
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All checks passed! ContextKeeper v3 is ready to use.")
    else:
        print("❌ Some checks failed. Please run setup.sh or check the errors above.")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())