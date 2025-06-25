#!/usr/bin/env python3
"""
Bug Reporting System - Production Entry Point

This is the main entry point for running the bug reporting system in production.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def main():
    """Main entry point for the bug reporting system."""
    
    print("🚀 Bug Reporting System v1.0.0")
    print("=" * 50)
    
    # Check for environment configuration
    if not os.path.exists(".env"):
        print("⚠️  Environment file (.env) not found!")
        print("📝 Run setup: python setup_env.py")
        print("📝 Or copy: cp env_config.example .env")
        return 1
    
    try:
        # Import and run the main application
        import asyncio
        from main import main_async
        asyncio.run(main_async())
        return 0
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all dependencies are installed: pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"❌ Application error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 