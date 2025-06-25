"""
Guard Agent for Bug Reporting System

This agent provides comprehensive incident management with specialized tools for:
- Level assignment and classification
- Duplicate detection and prevention
- Support escalation and email notifications
- Pattern analysis and escalation detection

The agent follows best practices with modular tool organization.
"""

from google.adk.agents import Agent
from typing import Dict, Any
from datetime import datetime

# Import tools from the tools package
from .tools import (
    assign_incident_level,
    detect_duplicate_issues,
    send_support_email,
    get_classification_history,
    analyze_escalation_pattern
)


class GuardAgent(Agent):
    """
    Guard Agent with specialized tools for comprehensive incident management.
    
    This agent uses dedicated tools for:
    1. Assigning incident levels (assign_incident_level)
    2. Detecting duplicate issues (detect_duplicate_issues) 
    3. Sending support email alerts (send_support_email)
    4. Analyzing escalation patterns (analyze_escalation_pattern)
    """
    
    def __init__(self):
        # Define specialized tools
        tools = [
            assign_incident_level,
            detect_duplicate_issues,
            send_support_email,
            get_classification_history,
            analyze_escalation_pattern,
        ]
        
        # Enhanced agent configuration
        agent_config = """
        You are a Guard Agent with specialized tools for comprehensive incident management.
        
        Your primary functions:
        1. **Level Assignment**: Use assign_incident_level tool to classify user input and assign appropriate severity levels (1-5) to incidents
        2. **Duplicate Detection**: Use detect_duplicate_issues tool to identify if users are reporting the same issue multiple times
        3. **Support Escalation**: Use send_support_email tool to alert support team about repeated issues after resolution
        4. **Pattern Analysis**: Use analyze_escalation_pattern tool to detect escalation patterns requiring human intervention
        
        **Workflow Guidelines:**
        
        **For Level Assignment:**
        - Analyze user input thoroughly for keywords and patterns
        - Assign appropriate levels: Level 1 (FAQ), Level 2 (Technical), Level 3 (Complex), Level 4 (Security), Level 5 (Critical)
        - Update incident database with classified level
        - Provide clear reasoning for level assignment
        
        **For Duplicate Detection:**
        - Compare new user input against existing open incidents
        - Calculate similarity scores and detect potential duplicates
        - Provide detailed summary of duplicate issues found
        - Recommend actions (update existing vs. create new)
        
        **For Support Escalation:**
        - Monitor for repeated issues after resolution
        - Send detailed email alerts to support team
        - Include original incident context and new issue details
        - Track escalation patterns
        
        **For Pattern Analysis:**
        - Monitor classification trends over time
        - Detect escalation patterns (increasing severity, high-level concentration)
        - Recommend appropriate interventions
        - Alert on critical patterns requiring immediate attention
        
        Always provide clear, actionable recommendations and maintain detailed logs of all activities.
        Use the appropriate tool for each specific task rather than attempting to handle everything manually.
        """
        
        super().__init__(
            name="guard_agent",
            model="gemini-2.0-flash",
            description="Guard Agent with specialized tools for incident management, duplicate detection, and support escalation",
            instruction=agent_config,
            tools=tools
        )


# A2A Protocol Integration
class GuardAgentA2ACallback:
    """Callback handler for A2A protocol integration."""
    
    def __init__(self):
        self.classification_count = 0
        self.escalation_alerts = []
        self.duplicate_checks = 0
        self.support_emails_sent = 0
        self.guard_agent_instance = None
    
    def set_guard_agent_instance(self, guard_agent):
        """Set the Guard Agent instance for direct invocation."""
        self.guard_agent_instance = guard_agent
    
    def classify_and_update_incident(self, incident_id: str, user_input: str) -> None:
        """
        Classify user input and update the incident level in the database.
        This is called by the A2A system after a bug report is created.
        """
        try:
            print(f"[Guard Agent A2A] Starting classification for incident {incident_id}")
            print(f"[Guard Agent A2A] User input: {user_input[:100]}...")
            
            # Create a minimal tool context for classification
            class MockToolContext:
                def __init__(self):
                    self.state = {}
                    self.user_id = "system"
                
                def __getattr__(self, name):
                    # Return None for any missing attributes to avoid errors
                    return None
            
            mock_context = MockToolContext()
            
            # Use the assign_incident_level tool
            result = assign_incident_level(user_input, incident_id, mock_context)  # type: ignore
            
            if result.get("status") == "success":
                level = result.get("level", 2)
                confidence = result.get("confidence", 0.0)
                reasoning = result.get("reasoning", "")
                
                print(f"[Guard Agent A2A] Successfully assigned Level {level} to incident {incident_id}")
                print(f"[Guard Agent A2A] Confidence: {confidence}, Reasoning: {reasoning}")
                
                # Update internal metrics
                self.on_classification_complete({
                    "level": level,
                    "confidence": confidence,
                    "timestamp": datetime.now().isoformat(),
                    "input": user_input,
                    "incident_id": incident_id
                })
                
            else:
                print(f"[Guard Agent A2A] Level assignment failed: {result.get('message', 'Unknown error')}")
                
        except Exception as e:
            print(f"[Guard Agent A2A] Error in classify_and_update_incident: {e}")
            import traceback
            traceback.print_exc()
    
    def check_for_duplicates(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        Check for duplicate issues before allowing bug report creation.
        This is called by the pre-agent callback.
        """
        try:
            print(f"[Guard Agent A2A] Checking for duplicates for user {user_id}")
            self.duplicate_checks += 1
            
            # Create a minimal tool context
            class MockToolContext:
                def __init__(self):
                    self.state = {}
                    self.user_id = user_id
                
                def __getattr__(self, name):
                    return None
            
            mock_context = MockToolContext()
            
            # Use the duplicate detection tool
            result = detect_duplicate_issues(user_input, user_id, mock_context)  # type: ignore
            
            if result.get("is_duplicate"):
                print(f"[Guard Agent A2A] Duplicate detected: {result.get('duplicate_incident_id')}")
            else:
                print(f"[Guard Agent A2A] No duplicates found - user can proceed")
            
            return result
            
        except Exception as e:
            print(f"[Guard Agent A2A] Error in duplicate check: {e}")
            return {
                "action": "detect_duplicate_issues",
                "is_duplicate": False,
                "message": f"Error during duplicate detection: {str(e)} - allowing new report"
            }
    
    def handle_repeated_issue(self, user_id: str, user_email: str, repeated_issue: str, original_incident_id: str) -> None:
        """
        Handle repeated issues by sending support email.
        """
        try:
            print(f"[Guard Agent A2A] Handling repeated issue for user {user_id}")
            
            class MockToolContext:
                def __init__(self):
                    self.state = {}
                
                def __getattr__(self, name):
                    return None
            
            mock_context = MockToolContext()
            
            # Use the email notification tool
            result = send_support_email(user_id, user_email, repeated_issue, original_incident_id, mock_context)  # type: ignore
            
            if result.get("status") == "success":
                self.support_emails_sent += 1
                print(f"[Guard Agent A2A] Support email sent for repeated issue")
            else:
                print(f"[Guard Agent A2A] Failed to send support email: {result.get('message')}")
                
        except Exception as e:
            print(f"[Guard Agent A2A] Error handling repeated issue: {e}")
    
    def on_classification_complete(self, result: Dict[str, Any]) -> None:
        """Called when a classification is completed."""
        self.classification_count += 1
        
        # Log high-priority classifications
        if result.get("level", 0) >= 4:
            self.escalation_alerts.append({
                "level": result["level"],
                "confidence": result["confidence"],
                "timestamp": result.get("timestamp"),
                "input_preview": result.get("input", "")[:50],
                "incident_id": result.get("incident_id")
            })
    
    def on_escalation_detected(self, analysis: Dict[str, Any]) -> None:
        """Called when escalation pattern is detected."""
        if analysis.get("escalation_detected") or analysis.get("high_level_ratio", 0) > 0.5:
            print(f"[A2A ALERT] Escalation detected: {analysis['recommendation']}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics for A2A reporting."""
        return {
            "total_classifications": self.classification_count,
            "duplicate_checks": self.duplicate_checks,
            "support_emails_sent": self.support_emails_sent,
            "escalation_alerts": len(self.escalation_alerts),
            "recent_alerts": self.escalation_alerts[-5:]  # Last 5 alerts
        }


# Global A2A callback handler for Guard Agent
_guard_agent_a2a_callback = GuardAgentA2ACallback()


def get_guard_agent_a2a_metrics() -> Dict[str, Any]:
    """Get A2A metrics for the Guard Agent."""
    return _guard_agent_a2a_callback.get_metrics() 