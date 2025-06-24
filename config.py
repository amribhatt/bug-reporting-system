"""
Configuration settings for the Bug Reporting Agent system.
"""

import os
from typing import Dict, Any

# User Configuration
USER_CONFIG = {
    "default_user_id": "user001",
    "session_timeout_minutes": 60,
    "max_bug_reports_per_user": 1000,
}

# Database Configuration
DATABASE_CONFIG = {
    "db_name": "bug_reports.db",
    "table_name": "incidents",
    "backup_enabled": True,
    "backup_interval_hours": 24,
}

# Bug Report Configuration
BUG_REPORT_CONFIG = {
    "valid_categories": ["Software", "Platform", "Account", "Other"],
    "valid_statuses": ["Open", "In Progress", "Resolved", "Closed"],
    "default_status": "Open",
    "bug_id_prefix": "BUG-",
    "bug_id_format": "{prefix}{id:04d}",  # e.g., BUG-0001
}

# Date Parsing Configuration
DATE_CONFIG = {
    "vague_expressions": [
        "last month", "few weeks ago", "some time ago", 
        "a while ago", "recently", "long time ago"
    ],
    "max_future_days": 1,  # Allow dates up to 1 day in the future
    "default_timezone": "UTC",
}

# UI Configuration
UI_CONFIG = {
    "colors_enabled": True,
    "show_debug_info": False,
    "table_width": 120,
    "max_description_length": 100,  # For table display
}

# Agent Configuration
AGENT_CONFIG = {
    "model": "gemini-2.0-flash",
    "agent_name": "bug_reporting_agent",
    "max_retries": 3,
    "timeout_seconds": 30,
}

# Environment Variables
def get_env_config() -> Dict[str, Any]:
    """Get configuration from environment variables."""
    return {
        "google_api_key": os.getenv("GOOGLE_API_KEY"),
        "debug_mode": os.getenv("DEBUG", "false").lower() == "true",
        "log_level": os.getenv("LOG_LEVEL", "INFO").upper(),
    }

# Combined Configuration
def get_config() -> Dict[str, Any]:
    """Get the complete configuration dictionary."""
    config = {
        "user": USER_CONFIG,
        "database": DATABASE_CONFIG,
        "bug_report": BUG_REPORT_CONFIG,
        "date": DATE_CONFIG,
        "ui": UI_CONFIG,
        "agent": AGENT_CONFIG,
        "env": get_env_config(),
    }
    return config

# Helper functions for easy access
def get_user_config(key: str | None = None):
    """Get user configuration value."""
    if key:
        return USER_CONFIG.get(key)
    return USER_CONFIG

def get_bug_categories():
    """Get valid bug categories."""
    return BUG_REPORT_CONFIG["valid_categories"]

def get_bug_statuses():
    """Get valid bug statuses."""
    return BUG_REPORT_CONFIG["valid_statuses"]

def get_default_user_id():
    """Get default user ID."""
    return USER_CONFIG["default_user_id"]

def get_database_name():
    """Get database filename."""
    return DATABASE_CONFIG["db_name"]

def get_vague_date_expressions():
    """Get list of vague date expressions that need clarification."""
    return DATE_CONFIG["vague_expressions"] 