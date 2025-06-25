"""
Bug Reporting System

An intelligent bug reporting system with Guard Agent for input classification
and A2A protocol integration.

Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "Bug Reporting System Team"
__description__ = "Intelligent bug reporting system with Guard Agent and A2A integration"

# Core imports for easy access
from .config import get_config, get_email_config, get_support_email
from .database import IncidentDatabase
from .guard_agent.agent import GuardAgent
from .bug_reporting_agent.agent import bug_reporting_agent

__all__ = [
    "get_config",
    "get_email_config", 
    "get_support_email",
    "IncidentDatabase",
    "GuardAgent",
    "bug_reporting_agent",
] 