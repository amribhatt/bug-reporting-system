#!/usr/bin/env python3
"""
Environment Setup Script for Bug Reporting System

This script helps users set up their environment configuration by:
1. Copying the example configuration file
2. Prompting for essential settings
3. Validating the configuration
"""

import os
import shutil
from pathlib import Path

def setup_environment():
    """Set up the environment configuration for the bug reporting system."""
    
    print("🚀 Bug Reporting System - Environment Setup")
    print("=" * 50)
    
    # Check if .env already exists
    env_file = Path(".env")
    example_file = Path("env_config.example")
    
    if env_file.exists():
        print("✅ .env file already exists")
        overwrite = input("Do you want to overwrite it? (y/N): ").lower().strip()
        if overwrite != 'y':
            print("Setup cancelled.")
            return
    
    # Copy example file
    if example_file.exists():
        shutil.copy(example_file, env_file)
        print("✅ Created .env file from example")
    else:
        print("❌ env_config.example file not found!")
        return
    
    # Prompt for essential settings
    print("\n📝 Essential Configuration (press Enter to skip):")
    
    # Google API Key
    api_key = input("Google API Key (required): ").strip()
    if api_key:
        update_env_file(env_file, "GOOGLE_API_KEY", api_key)
    
    # Email settings
    print("\n📧 Email Configuration:")
    support_email = input("Support team email: ").strip()
    if support_email:
        update_env_file(env_file, "SUPPORT_EMAIL", support_email)
    
    sender_email = input("Sender email: ").strip()
    if sender_email:
        update_env_file(env_file, "EMAIL_USER", sender_email)
    
    enable_email = input("Enable email notifications? (y/N): ").lower().strip()
    if enable_email == 'y':
        update_env_file(env_file, "EMAIL_ENABLED", "true")
    
    # Debug mode
    debug_mode = input("Enable debug mode? (y/N): ").lower().strip()
    if debug_mode == 'y':
        update_env_file(env_file, "DEBUG", "true")
    
    print("\n✅ Environment setup complete!")
    print(f"📁 Configuration saved to: {env_file.absolute()}")
    print("\n🔧 Next steps:")
    print("1. Edit .env file to add any missing configuration")
    print("2. Ensure GOOGLE_API_KEY is set for the system to work")
    print("3. Run: python main.py")

def update_env_file(env_file: Path, key: str, value: str):
    """Update a specific key in the .env file."""
    lines = []
    key_found = False
    
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Update existing key or add new one
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{key}="):
            lines[i] = f"{key}={value}\n"
            key_found = True
            break
    
    if not key_found:
        lines.append(f"{key}={value}\n")
    
    with open(env_file, 'w') as f:
        f.writelines(lines)

if __name__ == "__main__":
    setup_environment() 