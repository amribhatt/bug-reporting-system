"""
Guard Agent Tools Package

This package contains specialized tools for the Guard Agent:
- Level Assignment Tool: Classifies and assigns severity levels to incidents
- Duplicate Detection Tool: Detects duplicate issues from users
- Support Email Tool: Sends email notifications for repeated issues
"""

from .level_assignment_tool import assign_incident_level
from .duplicate_detection_tool import detect_duplicate_issues
from .support_email_tool import send_support_email
from .analysis_tools import get_classification_history, analyze_escalation_pattern

__all__ = [
    'assign_incident_level',
    'detect_duplicate_issues', 
    'send_support_email',
    'get_classification_history',
    'analyze_escalation_pattern'
] 