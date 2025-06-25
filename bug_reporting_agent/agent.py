from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta
import sys
import os
import re
import sqlite3
from typing import Dict, Any, Optional, List

# Add the parent directory to the path to import database module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import IncidentDatabase
from utils import format_bug_reports_table
from config import (
    get_bug_categories, get_bug_statuses, get_default_user_id,
    get_vague_date_expressions, DATE_CONFIG, AGENT_CONFIG
)
from a2a_integration import notify_bug_report_created


def parse_relative_date(date_text: str) -> str | None:
    """Parse relative date expressions into specific dates using dateutil."""
    if not date_text or not date_text.strip():
        return None
        
    today = datetime.now()
    date_text = date_text.lower().strip()
    
    # Handle common relative expressions first
    relative_expressions = {
        "yesterday": today - timedelta(days=1),
        "today": today,
        "tomorrow": today + timedelta(days=1),
    }
    
    for expr, date_obj in relative_expressions.items():
        if expr in date_text:
            return date_obj.strftime("%Y-%m-%d")
    
    # Handle "X days/weeks/months ago" patterns
    time_patterns = [
        (r'(\d+)\s*days?\s*ago', 'days'),
        (r'(\d+)\s*weeks?\s*ago', 'weeks'), 
        (r'(\d+)\s*months?\s*ago', 'months'),
    ]
    
    for pattern, unit in time_patterns:
        match = re.search(pattern, date_text)
        if match:
            amount = int(match.group(1))
            if unit == 'days':
                target_date = today - timedelta(days=amount)
            elif unit == 'weeks':
                target_date = today - timedelta(weeks=amount)
            elif unit == 'months':
                target_date = today - relativedelta(months=amount)
            return target_date.strftime("%Y-%m-%d")
    
    # Handle "last week" - return last Monday
    if "last week" in date_text:
        days_since_monday = today.weekday()  # Monday = 0, Sunday = 6
        last_monday = today - timedelta(days=days_since_monday + 7)
        return last_monday.strftime("%Y-%m-%d")
    
    # Handle "this week" - return this Monday
    if "this week" in date_text:
        days_since_monday = today.weekday()  # Monday = 0, Sunday = 6
        this_monday = today - timedelta(days=days_since_monday)
        return this_monday.strftime("%Y-%m-%d")
    
    # Handle specific weekdays like "last Monday", "last Friday"
    weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    for day_name in weekdays:
        if f"last {day_name}" in date_text:
            day_num = weekdays.index(day_name)  # 0 = Monday, 6 = Sunday
            days_since_target = (today.weekday() - day_num) % 7
            if days_since_target == 0:  # If today is the target day, go back a week
                days_since_target = 7
            target_date = today - timedelta(days=days_since_target)
            return target_date.strftime("%Y-%m-%d")
    
    # Return None for vague expressions that need clarification
    vague_expressions = get_vague_date_expressions()
    for expr in vague_expressions:
        if expr in date_text:
            return None
    
    # Try to parse using dateutil for more complex date formats
    try:
        # dateutil can handle many formats like "2024-01-15", "01/15/2024", "Jan 15, 2024", etc.
        parsed_date = date_parser.parse(date_text, default=today)
        
        # Only accept dates that are reasonable (not too far in the future)
        max_future_days = DATE_CONFIG["max_future_days"]
        if parsed_date.date() <= today.date() + timedelta(days=max_future_days):
            return parsed_date.strftime("%Y-%m-%d")
        else:
            return None  # Future dates are probably parsing errors
    except (ValueError, TypeError, OverflowError):
        pass
    
    # Return None if we can't parse it
    return None


def validate_bug_report_info(category: str | None = None, description: str | None = None, date_observed: str | None = None) -> dict:
    """Validate if we have all required information for a bug report."""
    missing = []
    
    if not category:
        missing.append("category")
    elif category not in get_bug_categories():
        valid_categories = ", ".join(get_bug_categories())
        return {
            "valid": False,
            "message": f"Invalid category '{category}'. Please choose from: {valid_categories}."
        }
    
    if not description:
        missing.append("description")
    
    if not date_observed:
        missing.append("date when you first noticed the issue")
    else:
        # Check if date can be parsed
        parsed_date = parse_relative_date(date_observed)
        if parsed_date is None:
            return {
                "valid": False,
                "message": f"I need a more specific date. You mentioned '{date_observed}' - could you please provide a specific date? For example: 'yesterday', '2024-01-15', or '3 days ago'."
            }
    
    if missing:
        missing_str = ", ".join(missing)
        return {
            "valid": False,
            "message": f"To create your bug report, I still need: {missing_str}. Could you please provide this information?"
        }
    
    return {"valid": True, "message": "All required information collected!"}


def create_bug_report(
    category: str, description: str, date_observed: str, tool_context: ToolContext
) -> dict:
    """Create a new bug report.

    Args:
        category: The category of the bug (Software, Platform, Account, Other)
        description: Description of the bug issue
        date_observed: Date when the issue was first observed
        tool_context: Context for accessing and updating session state

    Returns:
        A confirmation message with bug report ID
    """
    print(f"--- Tool: create_bug_report called for category '{category}' ---")

    # Validate category
    valid_categories = get_bug_categories()
    if category not in valid_categories:
        return {
            "action": "create_bug_report",
            "status": "error",
            "message": f"Invalid category. Please choose from: {', '.join(valid_categories)}",
        }
    
    # Parse and validate date
    parsed_date = parse_relative_date(date_observed)
    if parsed_date is None:
        return {
            "action": "create_bug_report",
            "status": "error", 
            "message": f"I need a more specific date. You mentioned '{date_observed}' - could you please provide a specific date? For example: 'yesterday', '2024-01-15', or '3 days ago'.",
        }
    
    date_observed = parsed_date

    # Use default level for initial creation - Guard Agent will update it later
    level = 2  # Default level for new incidents

    # Get user information from session state
    user_name = tool_context.state.get("user_name", "")
    user_email = tool_context.state.get("user_email", "")
    
    # Get user_id from session context - try multiple ways to get it
    user_id = getattr(tool_context, 'user_id', None)
    if not user_id:
        # Try to get from session state
        user_id = tool_context.state.get("_user_id", get_default_user_id())
    
    # Initialize database
    db = IncidentDatabase()
    
    # Create incident in database
    incident = db.create_incident(
        user_id=user_id,
        user_name=user_name,
        user_email=user_email,
        category=category,
        description=description,
        date_observed=date_observed,
        level=level
    )
    
    # Also update session state for backward compatibility
    bug_reports = tool_context.state.get("bug_reports", [])
    bug_reports.append(incident)
    tool_context.state["bug_reports"] = bug_reports

    result = {
        "action": "create_bug_report",
        "bug_report": incident,
        "message": f"Bug report {incident['id']} has been created successfully! I've recorded your {category.lower()} issue in our incident tracking system and will ensure it gets proper attention.",
    }
    
    # Notify A2A protocol - include the original description so Guard Agent can classify it
    try:
        notify_bug_report_created({
            "bug_id": incident['id'],
            "level": incident['level'],
            "category": incident['category'],
            "user_id": incident['user_id'],
            "user_input": description  # Original user input for classification
        })
    except Exception as e:
        print(f"[Bug Reporting Agent] A2A notification failed: {e}")

    return result


def view_bug_reports(tool_context: ToolContext) -> dict:
    """View all bug reports for the user.

    Args:
        tool_context: Context for accessing session state

    Returns:
        The list of bug reports
    """
    print("--- Tool: view_bug_reports called ---")

    # Get user_id from session context - try multiple ways to get it
    user_id = getattr(tool_context, 'user_id', None)
    if not user_id:
        # Try to get from session state
        user_id = tool_context.state.get("_user_id", get_default_user_id())
    
    # Initialize database
    db = IncidentDatabase()
    
    # Get incidents from database
    incidents = db.get_incidents_for_user(user_id)
    
    # Also update session state for backward compatibility
    tool_context.state["bug_reports"] = incidents
    
    # Format the bug reports as a table
    if incidents:
        table_output = format_bug_reports_table(incidents)
        message = f"Here are your current bug reports:\n\n{table_output}\n\nTotal: {len(incidents)} report(s)"
    else:
        message = "You currently have no bug reports. Feel free to report any issues you encounter!"

    return {
        "action": "view_bug_reports",
        "bug_reports": incidents,
        "count": len(incidents),
        "message": message,
        "formatted_table": table_output if incidents else None,
    }


def get_status_options() -> str:
    """Get formatted status options for user guidance."""
    statuses = get_bug_statuses()
    status_descriptions = {
        "Open": "Initial status for new issues (default)",
        "In Progress": "Issue is being actively worked on", 
        "Resolved": "Issue has been fixed or addressed",
        "Closed": "Issue is resolved and verified/no longer relevant"
    }
    
    options = []
    for status in statuses:
        description = status_descriptions.get(status, "")
        options.append(f"• **{status}:** {description}")
    
    return "\n".join(options)


def update_bug_status(bug_id: str, new_status: str, tool_context: ToolContext) -> dict:
    """Update the status of an existing bug report with sophisticated business rules.

    Business Rules:
    - Closed issues can only be reopened (to "Open")
    - Other transitions follow normal flow
    
    Args:
        bug_id: The bug report ID to update
        new_status: The new status to set
        tool_context: Context for accessing session state

    Returns:
        A confirmation message with update details
    """
    print(f"--- Tool: update_bug_status called for {bug_id} -> {new_status} ---")

    # Validate new status
    valid_statuses = get_bug_statuses()
    if new_status not in valid_statuses:
        return {
            "action": "update_bug_status",
            "status": "error",
            "message": f"""❌ **Invalid Status**

'{new_status}' is not a valid status. Please choose from one of these options:

{get_status_options()}

**To update the status, please specify:**
- The bug ID (e.g., BUG-00001)
- One of the exact status names above

**Example:** "Update BUG-00001 to In Progress" """,
        }

    # Get user information from session state
    user_id = getattr(tool_context, 'user_id', None)
    if not user_id:
        user_id = tool_context.state.get("_user_id", get_default_user_id())

    # Initialize database
    db = IncidentDatabase()
    
    # Get current incident to check existing status
    current_incident = db.get_incident_by_id(bug_id, user_id)
    if not current_incident:
        return {
            "action": "update_bug_status",
            "status": "error",
            "message": f"Bug report {bug_id} not found or you don't have permission to update it.",
        }
    
    current_status = current_incident['status']
    
    # Check if status is already the same
    if current_status.lower() == new_status.lower():
        return {
            "action": "update_bug_status",
            "status": "warning",
            "message": f"""📋 **Status Already Set**
            
Bug report {bug_id} is already marked as '{current_status}'.

**Current status:** {current_status}
**Requested status:** {new_status}

No changes were made since the status is already correct.

**Available status options:**
{get_status_options()}

**Would you like to:**
• Update to a different status using one of the options above
• View the full details of this bug report
• Check the status of other bug reports by typing 'show my bug reports'""",
            "current_status": current_status,
            "requested_status": new_status,
            "no_change_needed": True
        }

    # BUSINESS RULE: Closed issues can only be reopened to "Open"
    if current_status == "Closed" and new_status != "Open":
        return {
            "action": "update_bug_status",
            "status": "error",
            "message": f"""🚫 **Invalid Status Transition**

Bug report {bug_id} is currently **Closed** and can only be **reopened** (changed to "Open").

**Current status:** {current_status}
**Requested status:** {new_status}

**Business Rule:** Once an issue is closed, it can only be reopened for further investigation. If you need to track progress on a reopened issue, first reopen it, then update to "In Progress" or other statuses.

**To reopen this issue, say:** "Update {bug_id} to Open"

**Available status options:**
{get_status_options()}""",
            "current_status": current_status,
            "requested_status": new_status,
            "business_rule_violated": True
        }

    # Update the incident status
    updated_incident = db.update_incident_status(bug_id, user_id, new_status)
    
    if updated_incident:
        # Update session state if needed
        bug_reports = tool_context.state.get("bug_reports", [])
        for report in bug_reports:
            if report.get("id") == bug_id:
                report["status"] = new_status
                break
        
        return {
            "action": "update_bug_status",
            "status": "success",
            "message": f"""✅ **Status Updated Successfully**

Bug report {bug_id} has been updated:

**Previous status:** {updated_incident.get('old_status', 'Unknown')}
**New status:** {new_status}
**Updated on:** {updated_incident['last_updated'][:10]}

Your bug report status has been successfully changed. 

**Available status options for future updates:**
{get_status_options()}

You can view all your reports by typing 'show my bug reports'.""",
            "bug_id": bug_id,
            "old_status": updated_incident.get('old_status', 'Unknown'),
            "new_status": new_status,
            "last_updated": updated_incident['last_updated']
        }
    else:
        return {
            "action": "update_bug_status",
            "status": "error",
            "message": f"Failed to update status for bug report {bug_id}. Please try again or contact support.",
        }


def update_user_info(name: str, email: str, tool_context: ToolContext) -> dict:
    """Update the user's contact information.

    Args:
        name: The user's name
        email: The user's email address
        tool_context: Context for accessing and updating session state

    Returns:
        A confirmation message
    """
    print(f"--- Tool: update_user_info called with name '{name}' and email '{email}' ---")

    # Update the user info in state
    tool_context.state["user_name"] = name
    tool_context.state["user_email"] = email

    return {
        "action": "update_user_info",
        "name": name,
        "email": email,
        "message": f"Updated your contact information. Name: {name}, Email: {email}",
    }


# Enhanced Bug Reporting Agent with Callbacks
class BugReportingAgentCallbacks:
    """Callback system for the Bug Reporting Agent to integrate with Guard Agent."""
    
    def __init__(self):
        self.guard_agent_callback = None
        self.pre_callback_checks = 0
        self.post_callback_triggers = 0
        self.duplicates_prevented = 0
        self.repeated_issues_detected = 0
    
    def set_guard_agent_callback(self, guard_callback):
        """Set the Guard Agent callback handler."""
        self.guard_agent_callback = guard_callback
        print("[Bug Reporting Callbacks] Guard Agent callback registered")
    
    def pre_agent_callback(self, user_input: str, user_id: str, user_email: str = "") -> Dict[str, Any]:
        """
        Pre-agent callback to check for duplicates before creating bug reports.
        This is called before the bug reporting agent processes the user input.
        
        Args:
            user_input: The user's input describing their issue
            user_id: The user's ID
            user_email: The user's email address
            
        Returns:
            Dictionary containing pre-callback results and whether to proceed
        """
        print(f"[Bug Reporting Pre-Callback] Checking user input for user {user_id}")
        self.pre_callback_checks += 1
        
        # Check if this is a status update request or viewing request - allow these through
        status_keywords = ['resolve', 'resolved', 'close', 'closed', 'update', 'status', 'view', 'show', 'list', 'see my', 'my reports', 'my bugs']
        bug_id_pattern = r'BUG-\d+'
        
        user_input_lower = user_input.lower()
        
        # If user is asking to view/list their bugs, always allow
        if any(keyword in user_input_lower for keyword in ['view', 'show', 'list', 'see my', 'my reports', 'my bugs']):
            return {
                "proceed": True,
                "message": "User requesting to view bugs - proceeding without duplicate check"
            }
        
        # If user is updating status of an existing bug (contains BUG-ID + status keyword), allow
        if any(keyword in user_input_lower for keyword in status_keywords) and re.search(bug_id_pattern, user_input, re.IGNORECASE):
            return {
                "proceed": True,
                "message": "User updating existing bug status - proceeding without duplicate check"
            }
        
        # Only perform duplicate detection for NEW bug report creation
        if not self.guard_agent_callback:
            print("[Bug Reporting Pre-Callback] Warning: Guard Agent callback not available")
            return {
                "proceed": True,
                "message": "No guard agent available - proceeding with bug report creation"
            }
        
        try:
            # Check for duplicates using Guard Agent
            duplicate_result = self.guard_agent_callback.check_for_duplicates(user_input, user_id)
            
            if duplicate_result.get("is_duplicate"):
                self.duplicates_prevented += 1
                
                # Check if this is a repeated issue after resolution
                duplicate_incident_id = duplicate_result.get("duplicate_incident_id")
                
                if duplicate_incident_id:
                    # Get the duplicate incident details
                    db = IncidentDatabase()
                    duplicate_incident = db.get_incident_by_id(duplicate_incident_id, user_id)
                    
                    if duplicate_incident:
                        duplicate_status = duplicate_incident['status']
                        
                        # If duplicate is Open or In Progress, inform user about existing open issue
                        if duplicate_status in ['Open', 'In Progress']:
                            return {
                                "proceed": False,
                                "is_duplicate": True,
                                "is_repeated_issue": False,
                                "duplicate_incident_id": duplicate_incident_id,
                                "summary": duplicate_result.get("summary", ""),
                                "message": f"""📋 **Existing Open Issue Found**

I found an existing **{duplicate_status.lower()}** incident ({duplicate_incident_id}) that appears to be the same issue.

**Current incident status:** {duplicate_status}
**Created:** {duplicate_incident['date_created'][:10]}

**No new issue will be created.** A support representative will reach out to you regarding the existing open incident.

**Would you like to:**
1. **Check the status** of incident {duplicate_incident_id}
2. **Add details** to the existing incident by contacting support
3. **View all your reports** by typing 'show my bug reports'

**Support Contact:** support@example.com (Reference: {duplicate_incident_id})""",
                                "similarity_score": duplicate_result.get("similarity_score", 0),
                                "existing_open_issue": True
                            }
                        
                        # If duplicate is Resolved or Closed, check for other open issues
                        elif duplicate_status in ['Resolved', 'Closed']:
                            # Check if user has any other open/in-progress issues for same type
                            open_issues = self._check_for_open_similar_incidents(user_input, user_id)
                            
                            if open_issues:
                                # User has existing open issues - don't create new, inform about existing
                                existing_issue = open_issues[0]  # Get the first open issue
                                return {
                                    "proceed": False,
                                    "is_duplicate": True,
                                    "is_repeated_issue": False,
                                    "existing_open_incident_id": existing_issue['id'],
                                    "resolved_incident_id": duplicate_incident_id,
                                    "summary": duplicate_result.get("summary", ""),
                                    "message": f"""📋 **Existing Open Issue Found**

While your previous incident {duplicate_incident_id} was {duplicate_status.lower()}, you already have an **open** incident ({existing_issue['id']}) for a similar issue.

**Existing open incident:** {existing_issue['id']} (Status: {existing_issue['status']})
**Previous resolved incident:** {duplicate_incident_id} (Status: {duplicate_status})

**No new issue will be created.** A support representative will reach out to you regarding your existing open incident {existing_issue['id']}.

**Support Contact:** support@example.com (Reference: {existing_issue['id']})

**Would you like to:**
• View details of incident {existing_issue['id']}
• Check all your reports by typing 'show my bug reports'""",
                                    "existing_open_issue": True
                                }
                            else:
                                # No open issues exist - create new issue and notify support about recurrence
                                self.repeated_issues_detected += 1
                                self.guard_agent_callback.handle_repeated_issue(
                                    user_id, user_email, user_input, duplicate_incident_id
                                )
                                
                                return {
                                    "proceed": True,  # Allow new issue creation
                                    "is_duplicate": False,  # Don't block, but flag as repeat
                                    "is_repeated_issue": True,
                                    "resolved_incident_id": duplicate_incident_id,
                                    "summary": duplicate_result.get("summary", ""),
                                    "message": f"""🚨 **Recurring Issue Detected**

This appears to be the same issue as your previously {duplicate_status.lower()} incident {duplicate_incident_id}. Since you have no other open issues for this problem, a new incident will be created.

**Our support team has been automatically notified** about this recurring issue and will prioritize your case.

**Previous incident:** {duplicate_incident_id} (Status: {duplicate_status})

**Support Contact:** support@example.com""",
                                    "support_notified": True,
                                    "create_new_issue": True
                                }
                
                # Regular duplicate (not a repeat of resolved issue)
                return {
                    "proceed": False,
                    "is_duplicate": True,
                    "is_repeated_issue": False,
                    "duplicate_incident_id": duplicate_incident_id,
                    "summary": duplicate_result.get("summary", ""),
                    "message": f"""📋 **Similar Issue Found**

I found an existing open incident ({duplicate_incident_id}) that appears to be the same issue.

**Would you like to:**
1. **Update the existing incident** with additional details
2. **Check the status** of incident {duplicate_incident_id}
3. **View all your reports** by typing 'show my bug reports'
4. **Continue anyway** if this is actually a different issue

To avoid duplicate reports, please check your existing incident first.""",
                    "similarity_score": duplicate_result.get("similarity_score", 0)
                }
            
            return {
                "proceed": True,
                "is_duplicate": False,
                "message": "No duplicates detected - proceeding with bug report creation"
            }
            
        except Exception as e:
            print(f"[Bug Reporting Pre-Callback] Error: {e}")
            return {
                "proceed": True,
                "message": f"Error in pre-callback check: {str(e)} - proceeding with bug report creation"
            }
    
    def post_agent_callback(self, incident_id: str, user_input: str) -> Dict[str, Any]:
        """
        Post-agent callback to trigger Guard Agent level assignment after bug report creation.
        This is called after the bug reporting agent successfully creates a bug report.
        
        Args:
            incident_id: The ID of the created incident
            user_input: The original user input that led to the bug report
            
        Returns:
            Dictionary containing post-callback results
        """
        print(f"[Bug Reporting Post-Callback] Triggering level assignment for incident {incident_id}")
        self.post_callback_triggers += 1
        
        if not self.guard_agent_callback:
            print("[Bug Reporting Post-Callback] Warning: Guard Agent callback not available")
            return {
                "status": "warning",
                "message": "Guard Agent callback not available - incident level not updated"
            }
        
        try:
            # Trigger Guard Agent to classify and update incident level
            self.guard_agent_callback.classify_and_update_incident(incident_id, user_input)
            
            return {
                "status": "success",
                "message": f"Guard Agent triggered to assign level for incident {incident_id}",
                "incident_id": incident_id
            }
            
        except Exception as e:
            print(f"[Bug Reporting Post-Callback] Error: {e}")
            return {
                "status": "error",
                "message": f"Error in post-callback: {str(e)}"
            }
    
    def _check_for_resolved_similar_incident(self, user_input: str, user_id: str, exclude_incident_id: str) -> Optional[Dict[str, Any]]:
        """
        Check if user has a resolved incident similar to the current input.
        
        Args:
            user_input: Current user input
            user_id: User's ID
            exclude_incident_id: Incident ID to exclude from search
            
        Returns:
            Dictionary of resolved incident if found, None otherwise
        """
        try:
            db = IncidentDatabase()
            
            with sqlite3.connect(db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM incidents 
                    WHERE user_id = ? AND status IN ('Resolved', 'Closed') AND id != ?
                    ORDER BY date_created DESC
                """, (user_id, exclude_incident_id))
                
                for row in cursor.fetchall():
                    resolved_incident = dict(row)
                    
                    # Calculate similarity with resolved incident
                    similarity = self._calculate_simple_similarity(
                        user_input.lower(), resolved_incident['description'].lower()
                    )
                    
                    # If similarity > 60%, consider it the same issue
                    if similarity > 0.6:
                        return resolved_incident
            
            return None
            
        except Exception as e:
            print(f"[Bug Reporting Callbacks] Error checking resolved incidents: {e}")
            return None

    def _check_for_open_similar_incidents(self, user_input: str, user_id: str) -> List[Dict[str, Any]]:
        """
        Check if user has any open/in-progress incidents similar to the current input.
        
        Args:
            user_input: Current user input
            user_id: User's ID
            
        Returns:
            List of open/in-progress incidents if found, empty list otherwise
        """
        try:
            db = IncidentDatabase()
            open_incidents = []
            
            with sqlite3.connect(db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM incidents 
                    WHERE user_id = ? AND status IN ('Open', 'In Progress')
                    ORDER BY date_created DESC
                """, (user_id,))
                
                for row in cursor.fetchall():
                    open_incident = dict(row)
                    
                    # Calculate similarity with open incident
                    similarity = self._calculate_simple_similarity(
                        user_input.lower(), open_incident['description'].lower()
                    )
                    
                    # If similarity > 50%, consider it similar
                    if similarity > 0.5:
                        open_incidents.append(open_incident)
            
            return open_incidents
            
        except Exception as e:
            print(f"[Bug Reporting Callbacks] Error checking open incidents: {e}")
            return []
    
    def _calculate_simple_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple similarity between two texts."""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get callback metrics."""
        return {
            "pre_callback_checks": self.pre_callback_checks,
            "post_callback_triggers": self.post_callback_triggers,
            "duplicates_prevented": self.duplicates_prevented,
            "repeated_issues_detected": self.repeated_issues_detected
        }


# Global callback handler for Bug Reporting Agent
_bug_reporting_agent_callbacks = BugReportingAgentCallbacks()


def get_bug_reporting_callbacks() -> BugReportingAgentCallbacks:
    """Get the Bug Reporting Agent callbacks handler."""
    return _bug_reporting_agent_callbacks


def set_guard_agent_callback(guard_callback):
    """Set the Guard Agent callback for the Bug Reporting Agent."""
    _bug_reporting_agent_callbacks.set_guard_agent_callback(guard_callback)


# Create the bug reporting agent
bug_reporting_agent = Agent(
    name=AGENT_CONFIG["agent_name"],
    model=AGENT_CONFIG["model"],
    description="A helpful bug reporting agent that manages user issues with empathy and efficiency",
    instruction="""
    You are a compassionate and professional bug reporting assistant. Your primary role is to help users report technical issues while providing emotional support and reassurance.

    **CORE PERSONALITY:**
    - Always be empathetic and understanding when users report problems
    - Acknowledge their frustration and reassure them that you'll help resolve the issue
    - Be professional but warm in your communication
    - Show that you take their concerns seriously

    **USER INFORMATION:**
    - User's name: {user_name}
    - User's email: {user_email}
    - Bug reports: {bug_reports}

    **MAIN RESPONSIBILITIES:**

    1. **Issue Detection & Empathy:**
       - When a user mentions any problem, issue, bug, error, or frustration, immediately:
         * Acknowledge their concern with empathy
         * Reassure them that you'll help create a proper bug report
         * Express understanding of how frustrating technical issues can be

    2. **Bug Report Creation Process:**
       When creating a bug report, you MUST collect ONLY these 3 essential details (matching the incidents table):
       - **Category:** User must choose from exactly these 4 options:
         * Software (application bugs, crashes, features not working)
         * Platform (infrastructure, server, performance issues)
         * Account (login, permissions, user account related)
         * Other (anything that doesn't fit the above categories)
       - **Description:** Detailed description of the issue
       - **Date Observed:** When they first noticed the issue (be smart about date parsing)

       **IMPORTANT:** Only ask for these 3 pieces of information. Do NOT ask for additional details like:
       - Steps to reproduce
       - Browser information
       - Operating system
       - Priority level
       - Expected vs actual behavior
       These are NOT stored in the incidents table and should not be collected.

    3. **Conversation Flow:**
       **INTELLIGENT DESCRIPTION HANDLING:**
       - If user gives a generic statement like "I want to report an issue" or "I have a problem", ask for a brief description
       - If user provides a specific issue description (e.g., "My login keeps failing" or "The app crashes when I click save"), use that as the base description and ask: "I've noted that [repeat their issue]. Would you like to add any additional details to this description?"
       - If they say no or confirm it's complete, use the original description as-is
       - If they provide additional details, append them to the original description
       
       **GENERAL FLOW:**
       - Always present the 4 categories clearly and ask them to choose
       - Be patient if they need clarification about categories  
       - Once you have all information, create the bug report immediately

    4. **Smart Date Handling:**
       - Accept relative dates: "yesterday", "today", "3 days ago", "last week"
       - Accept specific dates: "2024-01-15", "01/15/2024", "15-01-2024"
       - If user says vague terms like "last month", "recently", "a while ago", ask for a specific date
       - Example: "You mentioned 'last month' - could you give me a specific date when you first noticed this issue?"

    5. **Category Guidance:**
       Help users choose the right category:
       - **Software:** App crashes, buttons not working, features broken, UI issues
       - **Platform:** Website slow, server errors, connectivity problems, system outages
       - **Account:** Can't log in, wrong permissions, profile issues, password problems
       - **Other:** Hardware issues, general questions, anything else

    6. **Status Update Guidance:**
       When users want to update bug report statuses, guide them with available options:
       - **Open:** Initial status for new issues (default)
       - **In Progress:** Issue is being actively worked on
       - **Resolved:** Issue has been fixed or addressed
       - **Closed:** Issue is resolved and verified/no longer relevant
       
       Always present these 4 status options clearly when updating statuses.

    7. **Additional Capabilities:**
       - View existing bug reports for the user (always display in tabular format)
       - Update bug report statuses (with clear status options)
       - Update user contact information
       - Provide status updates on previously reported issues

    **IMPORTANT GUIDELINES:**
    - Always start by being empathetic when someone reports an issue
    - Don't overwhelm users with too many questions at once
    - Make the bug reporting process feel supportive, not bureaucratic
    - Reassure users that their issue will be properly tracked and addressed
    - If you don't have their contact info, collect their name and email
    - Keep conversation friendly and solution-focused
    - **ALWAYS display bug reports in a clean tabular format** when showing them to users

    **CALLBACK INTEGRATION:**
    - The system now includes advanced duplicate detection and level assignment
    - Guard Agent will automatically classify issues and assign severity levels
    - Duplicate issues will be detected and users will be guided appropriately
    - Support team will be automatically notified for recurring issues

    **SAMPLE RESPONSES:**
    - "I'm sorry to hear you're experiencing this issue. That must be frustrating! Let me help you create a proper bug report so our team can address this."
    - "I understand how annoying technical problems can be. Don't worry - I'll make sure your issue gets the attention it deserves."
    - "Thank you for bringing this to my attention. Let's get this documented properly so we can get it resolved for you."

    **DATE HANDLING EXAMPLES:**
    - User: "I've been having this issue since yesterday" → Accept and convert to specific date
    - User: "This started last month" → Ask: "Could you give me a specific date in last month when you first noticed this?"
    - User: "It's been happening recently" → Ask: "When exactly did you first notice this issue? Please provide a specific date."
    - User: "3 days ago" → Accept and convert to specific date

    Remember: Your goal is to make users feel heard, supported, and confident that their issues will be resolved.
    """,
    tools=[
        create_bug_report,
        view_bug_reports,
        update_bug_status,
        update_user_info,
    ],
) 