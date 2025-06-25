"""
Configuration settings for the Bug Reporting Agent system.
"""

import os
from typing import Dict, Any

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, skip loading .env file
    pass

# User Configuration
USER_CONFIG = {
    "default_user_id": "user001",
    "session_timeout_minutes": int(os.getenv("SESSION_TIMEOUT", "60")),
    "max_bug_reports_per_user": int(os.getenv("MAX_REPORTS_PER_USER", "1000")),
}

# Database Configuration
DATABASE_CONFIG = {
    "db_name": os.getenv("DB_NAME", "bug_reports.db"),
    "table_name": "incidents",
    "backup_enabled": os.getenv("DB_BACKUP_ENABLED", "true").lower() == "true",
    "backup_interval_hours": int(os.getenv("DB_BACKUP_INTERVAL", "24")),
}

# Bug Report Configuration
BUG_REPORT_CONFIG = {
    "valid_categories": ["Software", "Platform", "Account", "Other"],
    "valid_statuses": ["Open", "In Progress", "Resolved", "Closed"],
    "default_status": "Open",
    "bug_id_prefix": "BUG-",
    "bug_id_format": "{prefix}{id:05d}",  # e.g., BUG-0001
    "valid_levels": {
        1: "Simple FAQ questions (how-to, information requests)",
        2: "Common technical/account issues (crashes, login problems)",
        3: "Unstructured but solvable problems (save corruption, gameplay issues)",
        4: "Security/fraud issues (hacking, stolen items)",
        5: "Critical emergencies (doxxing, legal issues, server outages)"
    },
    "default_level": 2,
}

# Date Parsing Configuration
DATE_CONFIG = {
    "vague_expressions": [
        "last month", "few weeks ago", "some time ago", 
        "a while ago", "recently", "long time ago"
    ],
    "max_future_days": 0,  # Allow dates up to 0 day in the future
    "default_timezone": "UTC",
}

# UI Configuration
UI_CONFIG = {
    "colors_enabled": True,
    "show_debug_info": os.getenv("DEBUG", "false").lower() == "true",
    "table_width": 120,
    "max_description_length": 100,  # For table display
}

# Agent Configuration
AGENT_CONFIG = {
    "model": os.getenv("MODEL_NAME", "gemini-2.0-flash"),
    "agent_name": "bug_reporting_agent",
    "max_retries": int(os.getenv("AGENT_MAX_RETRIES", "3")),
    "timeout_seconds": int(os.getenv("AGENT_TIMEOUT", "30")),
}

# Email Configuration
EMAIL_CONFIG = {
            "support_email": os.getenv("SUPPORT_EMAIL", "support@example.com"),
    "sender_email": os.getenv("EMAIL_USER", "noreply@example.com"),
    "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": int(os.getenv("SMTP_PORT", "587")),
    "email_password": os.getenv("EMAIL_PASSWORD"),  # No default - must be set via env
    "email_enabled": os.getenv("EMAIL_ENABLED", "false").lower() == "true",
    "max_email_alerts": 50,  # Keep last 50 email alerts in memory
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
        "email": EMAIL_CONFIG,
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

def get_bug_levels():
    """Get valid bug levels."""
    return BUG_REPORT_CONFIG["valid_levels"]

def get_default_level():
    """Get default bug level."""
    return BUG_REPORT_CONFIG["default_level"]

def get_email_config(key: str | None = None):
    """Get email configuration value."""
    if key:
        return EMAIL_CONFIG.get(key)
    return EMAIL_CONFIG

def get_support_email():
    """Get support team email address."""
    return EMAIL_CONFIG["support_email"]

def get_sender_email():
    """Get sender email address."""
    return EMAIL_CONFIG["sender_email"]

def is_email_enabled():
    """Check if email notifications are enabled."""
    return EMAIL_CONFIG["email_enabled"] 