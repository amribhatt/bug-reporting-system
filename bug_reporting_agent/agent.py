from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta
import sys
import os
import re

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


def update_bug_status(bug_id: str, new_status: str, tool_context: ToolContext) -> dict:
    """Update the status of a bug report.

    Args:
        bug_id: The ID of the bug report to update
        new_status: The new status (Open, In Progress, Resolved, Closed)
        tool_context: Context for accessing and updating session state

    Returns:
        A confirmation message
    """
    print(f"--- Tool: update_bug_status called for {bug_id} to {new_status} ---")

    # Validate status
    valid_statuses = get_bug_statuses()
    if new_status not in valid_statuses:
        return {
            "action": "update_bug_status",
            "status": "error",
            "message": f"Invalid status. Please choose from: {', '.join(valid_statuses)}",
        }

    # Get user_id from session context - try multiple ways to get it
    user_id = getattr(tool_context, 'user_id', None)
    if not user_id:
        # Try to get from session state
        user_id = tool_context.state.get("_user_id", get_default_user_id())
    
    # Initialize database
    db = IncidentDatabase()
    
    # Update incident in database
    updated_incident = db.update_incident_status(bug_id, user_id, new_status)
    
    if updated_incident:
        # Update session state for backward compatibility
        incidents = db.get_incidents_for_user(user_id)
        tool_context.state["bug_reports"] = incidents
        
        return {
            "action": "update_bug_status",
            "bug_id": bug_id,
            "old_status": updated_incident["old_status"],
            "new_status": new_status,
            "message": f"Updated bug report {bug_id} status from '{updated_incident['old_status']}' to '{new_status}' in our incident tracking system",
        }

    return {
        "action": "update_bug_status",
        "status": "error",
        "message": f"Bug report {bug_id} not found",
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

    6. **Additional Capabilities:**
       - View existing bug reports for the user (always display in tabular format)
       - Update bug report statuses
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