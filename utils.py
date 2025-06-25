from google.genai import types
from typing import List, Dict, Any


def format_bug_reports_table(bug_reports: List[Dict[str, Any]]) -> str:
    """Format bug reports in a clean tabular format."""
    if not bug_reports:
        return "No bug reports found."
    
    # Define column headers and widths
    headers = ["ID", "Category", "Status", "Date Observed", "Date Created", "Description"]
    col_widths = [10, 12, 12, 12, 12, 50]  # Minimum widths
    
    # Calculate actual column widths based on content
    for report in bug_reports:
        col_widths[0] = max(col_widths[0], len(str(report.get("id", ""))))
        col_widths[1] = max(col_widths[1], len(str(report.get("category", ""))))
        col_widths[2] = max(col_widths[2], len(str(report.get("status", ""))))
        col_widths[3] = max(col_widths[3], len(str(report.get("date_observed", ""))))
        col_widths[4] = max(col_widths[4], len(str(report.get("date_created", ""))[:10]))  # Only date part
        # Description is truncated to max 50 chars
        
    # Create table header
    header_row = "┌" + "┬".join("─" * (width + 2) for width in col_widths) + "┐"
    header_text = "│"
    for i, header in enumerate(headers):
        header_text += f" {header:<{col_widths[i]}} │"
    
    separator = "├" + "┼".join("─" * (width + 2) for width in col_widths) + "┤"
    
    # Create table rows
    rows = []
    for report in bug_reports:
        row = "│"
        
        # Format each column
        bug_id = str(report.get("id", ""))
        category = str(report.get("category", ""))
        status = str(report.get("status", ""))
        date_obs = str(report.get("date_observed", ""))
        date_created = str(report.get("date_created", ""))[:10]  # Only date part
        description = str(report.get("description", ""))
        
        # Truncate description if too long
        if len(description) > col_widths[5]:
            description = description[:col_widths[5]-3] + "..."
        
        # Add status icon
        status_icon = "🔴" if status == "Open" else "🟡" if status == "In Progress" else "🟢" if status == "Resolved" else "⚫"
        status_with_icon = f"{status_icon} {status}"
        
        row += f" {bug_id:<{col_widths[0]}} │"
        row += f" {category:<{col_widths[1]}} │"
        row += f" {status_with_icon:<{col_widths[2]+2}} │"  # +2 for emoji
        row += f" {date_obs:<{col_widths[3]}} │"
        row += f" {date_created:<{col_widths[4]}} │"
        row += f" {description:<{col_widths[5]}} │"
        
        rows.append(row)
    
    # Create table footer
    footer = "└" + "┴".join("─" * (width + 2) for width in col_widths) + "┘"
    
    # Combine all parts
    table = [header_row, header_text, separator] + rows + [footer]
    return "\n".join(table)


# ANSI color codes for terminal output
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"


async def display_state(
    session_service, app_name, user_id, session_id, label="Current State"
):
    """Display the current session state in a formatted way."""
    try:
        session = await session_service.get_session(
            app_name=app_name, user_id=user_id, session_id=session_id
        )

        # Format the output with clear sections
        print(f"\n{'-' * 10} {label} {'-' * 10}")

        # Handle the user info
        user_name = session.state.get("user_name", "Not provided")
        user_email = session.state.get("user_email", "Not provided")
        print(f"👤 User: {user_name}")
        print(f"📧 Email: {user_email}")

        # Note: Bug reports table removed from state display as requested
        # Users can view reports by asking "show my bug reports"

        print("-" * (22 + len(label)))
    except Exception as e:
        print(f"Error displaying state: {e}")


async def process_agent_response(event):
    """Process and display agent response events."""
    # Log basic event info
    print(f"Event ID: {event.id}, Author: {event.author}")

    # Check for specific parts first
    has_specific_part = False
    if event.content and event.content.parts:
        for part in event.content.parts:
            if hasattr(part, "executable_code") and part.executable_code:
                # Access the actual code string via .code
                print(
                    f"  Debug: Agent generated code:\n```python\n{part.executable_code.code}\n```"
                )
                has_specific_part = True
            elif hasattr(part, "code_execution_result") and part.code_execution_result:
                # Access outcome and output correctly
                print(
                    f"  Debug: Code Execution Result: {part.code_execution_result.outcome} - Output:\n{part.code_execution_result.output}"
                )
                has_specific_part = True
            elif hasattr(part, "tool_response") and part.tool_response:
                # Print tool response information
                print(f"  Tool Response: {part.tool_response.output}")
                has_specific_part = True
            # Also print any text parts found in any event for debugging
            elif hasattr(part, "text") and part.text and not part.text.isspace():
                print(f"  Text: '{part.text.strip()}'")

    # Check for final response after specific parts
    final_response = None
    if event.is_final_response():
        if (
            event.content
            and event.content.parts
            and hasattr(event.content.parts[0], "text")
            and event.content.parts[0].text
        ):
            final_response = event.content.parts[0].text.strip()
            # Use colors and formatting to make the final response stand out
            print(
                f"\n{Colors.BG_BLUE}{Colors.WHITE}{Colors.BOLD}╔══ BUG REPORTING AGENT ═══════════════════════════════════{Colors.RESET}"
            )
            print(f"{Colors.CYAN}{Colors.BOLD}{final_response}{Colors.RESET}")
            print(
                f"{Colors.BG_BLUE}{Colors.WHITE}{Colors.BOLD}╚════════════════════════════════════════════════════════════{Colors.RESET}\n"
            )
        else:
            print(
                f"\n{Colors.BG_RED}{Colors.WHITE}{Colors.BOLD}==> Final Agent Response: [No text content in final event]{Colors.RESET}\n"
            )

    return final_response


async def call_agent_async(runner, user_id, session_id, query):
    """Call the agent asynchronously with the user's query."""
    content = types.Content(role="user", parts=[types.Part(text=query)])
    print(
        f"\n{Colors.BG_GREEN}{Colors.BLACK}{Colors.BOLD}--- Processing: {query} ---{Colors.RESET}"
    )
    final_response_text = None

    # State display removed as requested

    try:
        async for event in runner.run_async(
            user_id=user_id, session_id=session_id, new_message=content
        ):
            # Process each event and get the final response if available
            response = await process_agent_response(event)
            if response:
                final_response_text = response
    except Exception as e:
        print(f"Error during agent call: {e}")

    # State display removed as requested

    return final_response_text


async def call_agent_async_with_callbacks(runner, user_id, session_id, query):
    """
    Enhanced agent call with pre and post callback support.
    This version integrates with the Guard Agent callbacks for duplicate detection and level assignment.
    """
    from bug_reporting_agent.agent import get_bug_reporting_callbacks
    
    content = types.Content(role="user", parts=[types.Part(text=query)])
    print(
        f"\n{Colors.BG_GREEN}{Colors.BLACK}{Colors.BOLD}--- Processing with Callbacks: {query} ---{Colors.RESET}"
    )
    final_response_text = None

    # State display removed as requested

    # Get user information for callbacks
    try:
        session = await runner.session_service.get_session(
            app_name=runner.app_name, user_id=user_id, session_id=session_id
        )
        user_email = session.state.get("user_email", "") if session else ""
    except:
        user_email = ""

    # PRE-AGENT CALLBACK: Check for duplicates
    callbacks = get_bug_reporting_callbacks()
    pre_callback_result = callbacks.pre_agent_callback(query, user_id, user_email)
    
    if not pre_callback_result.get("proceed", True):
        # Duplicate detected - don't proceed with bug report creation
        print(f"\n{Colors.BG_YELLOW}{Colors.BLACK}{Colors.BOLD}=== DUPLICATE DETECTED ==={Colors.RESET}")
        
        if pre_callback_result.get("is_repeated_issue"):
            print(f"{Colors.RED}{Colors.BOLD}🚨 REPEATED ISSUE ALERT 🚨{Colors.RESET}")
            print(f"{Colors.YELLOW}Support team has been notified about this recurring problem.{Colors.RESET}")
        
        print(f"{Colors.CYAN}{pre_callback_result.get('summary', '')}{Colors.RESET}")
        
        # Display message to user instead of creating bug report
        duplicate_message = pre_callback_result.get("message", "Duplicate issue detected")
        print(f"\n{Colors.BG_BLUE}{Colors.WHITE}{Colors.BOLD}╔══ BUG REPORTING AGENT ═══════════════════════════════════{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD}{duplicate_message}{Colors.RESET}")
        print(f"{Colors.BG_BLUE}{Colors.WHITE}{Colors.BOLD}╚════════════════════════════════════════════════════════════{Colors.RESET}\n")
        
        return duplicate_message

    try:
        # Proceed with normal agent processing
        async for event in runner.run_async(
            user_id=user_id, session_id=session_id, new_message=content
        ):
            # Process each event and get the final response if available
            response = await process_agent_response(event)
            if response:
                final_response_text = response
                
                # POST-AGENT CALLBACK: Check if a bug report was created and trigger level assignment
                if "bug report" in response.lower() and "created successfully" in response.lower():
                    # Extract incident ID from response if possible
                    import re
                    bug_id_match = re.search(r'BUG-\d+', response)
                    if bug_id_match:
                        bug_id = bug_id_match.group()
                        print(f"\n{Colors.BG_MAGENTA}{Colors.WHITE}{Colors.BOLD}🔄 Triggering Post-Callback for {bug_id}{Colors.RESET}")
                        
                        post_callback_result = callbacks.post_agent_callback(bug_id, query)
                        
                        if post_callback_result.get("status") == "success":
                            print(f"{Colors.GREEN}✅ Guard Agent triggered for level assignment{Colors.RESET}")
                        else:
                            print(f"{Colors.YELLOW}⚠️ {post_callback_result.get('message', 'Post-callback warning')}{Colors.RESET}")
                
    except Exception as e:
        print(f"Error during agent call: {e}")

    # State display removed as requested

    return final_response_text 