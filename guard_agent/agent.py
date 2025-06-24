from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
import sys
import os
import re
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional, List

# Add the parent directory to the path to import database module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_bug_levels, get_default_level
from a2a_integration import notify_classification_complete, notify_escalation_detected
from database import IncidentDatabase


def classify_input_level(user_input: str, tool_context: ToolContext) -> dict:
    """
    Classify user input into one of five levels based on content analysis.
    
    Level 1: Simple FAQ questions (how-to, information requests)
    Level 2: Common technical/account issues (crashes, login problems)  
    Level 3: Unstructured but solvable problems (save corruption, gameplay issues)
    Level 4: Security/fraud issues (hacking, stolen items)
    Level 5: Critical emergencies (doxxing, legal issues, server outages)
    
    Args:
        user_input: The user's input text to classify
        tool_context: Context for accessing session state
        
    Returns:
        Dictionary containing level, confidence, and reasoning
    """
    print(f"--- Tool: classify_input_level called ---")
    
    if not user_input or not user_input.strip():
        return {
            "action": "classify_input",
            "level": get_default_level(),
            "confidence": 0.0,
            "reasoning": "Empty input provided",
            "message": "No input to classify"
        }
    
    input_lower = user_input.lower()
    
    # Level 5: Critical emergencies (doxxing, legal issues, server outages)
    level_5_keywords = [
        "doxx", "dox", "personal info", "address leak", "phone number leak",
        "legal", "lawsuit", "court", "police", "attorney", "lawyer",
        "server down", "complete outage", "total failure", "system crash",
        "data breach", "hack", "hacked", "stolen data", "privacy violation",
        "emergency", "urgent", "critical", "immediate help"
    ]
    
    level_5_patterns = [
        r"server.*down", r"complete.*outage", r"total.*failure",
        r"data.*breach", r"personal.*information.*leaked",
        r"legal.*action", r"court.*case", r"emergency.*situation"
    ]
    
    # Level 4: Security/fraud issues (hacking, stolen items)  
    level_4_keywords = [
        "hack", "hacker", "compromised", "stolen", "fraud", "scam",
        "unauthorized", "suspicious activity", "account taken",
        "password changed", "logged out", "can't login", "security",
        "malware", "virus", "phishing", "suspicious email"
    ]
    
    level_4_patterns = [
        r"account.*compromised", r"password.*changed.*me",
        r"suspicious.*activity", r"unauthorized.*access",
        r"can't.*log.*in", r"logged.*out.*automatically"
    ]
    
    # Level 3: Unstructured but solvable problems (save corruption, gameplay issues)
    level_3_keywords = [
        "save", "corrupt", "progress lost", "game crash", "freeze", "lag",
        "performance", "slow", "bug", "glitch", "error", "broken",
        "not working", "weird", "strange behavior", "unexpected"
    ]
    
    level_3_patterns = [
        r"save.*corrupt", r"progress.*lost", r"game.*crash",
        r"not.*working.*properly", r"weird.*behavior", r"strange.*issue"
    ]
    
    # Level 2: Common technical/account issues (crashes, login problems)
    level_2_keywords = [
        "crash", "login", "sign in", "password", "reset", "forgot",
        "technical", "support", "help", "issue", "problem",
        "won't start", "loading", "connection", "sync"
    ]
    
    level_2_patterns = [
        r"can't.*login", r"forgot.*password", r"won't.*start",
        r"loading.*problem", r"connection.*issue", r"sync.*problem"
    ]
    
    # Level 1: Simple FAQ questions (how-to, information requests)
    level_1_keywords = [
        "how", "what", "when", "where", "why", "explain", "tell me",
        "information", "guide", "tutorial", "help", "learn",
        "feature", "function", "work", "use", "setup"
    ]
    
    level_1_patterns = [
        r"how.*do.*i", r"how.*to", r"what.*is", r"how.*does.*work",
        r"can.*you.*explain", r"tell.*me.*about", r"information.*about"
    ]
    
    # Classification logic with scoring
    level_scores = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}
    
    # Check Level 5 first (highest priority)
    for keyword in level_5_keywords:
        if keyword in input_lower:
            level_scores[5] += 3.0
    
    for pattern in level_5_patterns:
        if re.search(pattern, input_lower):
            level_scores[5] += 4.0
    
    # Check Level 4
    for keyword in level_4_keywords:
        if keyword in input_lower:
            level_scores[4] += 2.5
    
    for pattern in level_4_patterns:
        if re.search(pattern, input_lower):
            level_scores[4] += 3.0
    
    # Check Level 3
    for keyword in level_3_keywords:
        if keyword in input_lower:
            level_scores[3] += 2.0
    
    for pattern in level_3_patterns:
        if re.search(pattern, input_lower):
            level_scores[3] += 2.5
    
    # Check Level 2
    for keyword in level_2_keywords:
        if keyword in input_lower:
            level_scores[2] += 1.5
    
    for pattern in level_2_patterns:
        if re.search(pattern, input_lower):
            level_scores[2] += 2.0
    
    # Check Level 1
    for keyword in level_1_keywords:
        if keyword in input_lower:
            level_scores[1] += 1.0
    
    for pattern in level_1_patterns:
        if re.search(pattern, input_lower):
            level_scores[1] += 1.5
    
    # Determine final level
    max_score = max(level_scores.values())
    if max_score == 0:
        # Default to level 2 if no clear classification
        final_level = get_default_level()
        confidence = 0.3
        reasoning = "No clear indicators found, defaulting to level 2"
    else:
        # Get level with highest score
        final_level = max(level_scores.keys(), key=lambda k: level_scores[k])
        confidence = min(max_score / 5.0, 1.0)  # Normalize to 0-1 range
        reasoning = f"Classified based on keyword and pattern analysis (score: {max_score})"
    
    # Get level descriptions for context
    level_descriptions = get_bug_levels()
    level_description = level_descriptions.get(final_level, "Unknown level")
    
    # Store classification in session state for potential use by bug reporting agent
    classification_data = {
        "level": final_level,
        "confidence": confidence,
        "input": user_input[:100],  # Store first 100 chars for reference
        "timestamp": tool_context.state.get("_timestamp", "unknown")
    }
    
    tool_context.state["last_classification"] = classification_data
    
    # Add to classification history
    history = tool_context.state.get("classification_history", [])
    history.append(classification_data)
    # Keep only last 20 classifications
    tool_context.state["classification_history"] = history[-20:]
    
    result = {
        "action": "classify_input",
        "level": final_level,
        "confidence": round(confidence, 2),
        "reasoning": reasoning,
        "description": level_description,
        "message": f"Input classified as Level {final_level}: {level_description}",
        "all_scores": level_scores
    }
    
    # Notify A2A protocol
    try:
        notify_classification_complete(result)
        _guard_agent_a2a_callback.on_classification_complete(result)
    except Exception as e:
        print(f"[Guard Agent] A2A notification failed: {e}")
    
    return result


def get_classification_history(tool_context: ToolContext) -> dict:
    """
    Get the history of recent classifications for this session.
    
    Args:
        tool_context: Context for accessing session state
        
    Returns:
        Dictionary containing classification history
    """
    print(f"--- Tool: get_classification_history called ---")
    
    # Get classification history from session state
    history = tool_context.state.get("classification_history", [])
    last_classification = tool_context.state.get("last_classification", None)
    
    return {
        "action": "get_history",
        "history": history,
        "last_classification": last_classification,
        "total_classifications": len(history),
        "message": f"Retrieved {len(history)} previous classifications"
    }


def analyze_escalation_pattern(tool_context: ToolContext) -> dict:
    """
    Analyze if there's an escalation pattern in recent classifications.
    
    Args:
        tool_context: Context for accessing session state
        
    Returns:
        Dictionary containing escalation analysis
    """
    print(f"--- Tool: analyze_escalation_pattern called ---")
    
    history = tool_context.state.get("classification_history", [])
    
    if len(history) < 2:
        return {
            "action": "analyze_escalation",
            "escalation_detected": False,
            "message": "Not enough data to analyze escalation patterns",
            "recommendation": "Continue monitoring"
        }
    
    # Look at last 5 classifications
    recent = history[-5:]
    levels = [item.get("level", 2) for item in recent]
    
    # Check for escalation (increasing levels)
    escalation_detected = False
    if len(levels) >= 3:
        # Check if levels are generally increasing
        increasing_count = sum(1 for i in range(1, len(levels)) if levels[i] > levels[i-1])
        if increasing_count >= len(levels) // 2:
            escalation_detected = True
    
    # Check for high-level concentration
    high_level_count = sum(1 for level in levels if level >= 4)
    high_level_ratio = high_level_count / len(levels) if levels else 0
    
    recommendation = "Continue normal monitoring"
    if escalation_detected or high_level_ratio > 0.5:
        recommendation = "Consider immediate human intervention"
    elif high_level_ratio > 0.3:
        recommendation = "Escalate to senior support"
    
    result = {
        "action": "analyze_escalation",
        "escalation_detected": escalation_detected,
        "high_level_ratio": round(high_level_ratio, 2),
        "recent_levels": levels,
        "recommendation": recommendation,
        "message": f"Escalation analysis: {'Detected' if escalation_detected else 'Not detected'}"
    }
    
    # Notify A2A protocol if escalation detected
    if escalation_detected or high_level_ratio > 0.5:
        try:
            notify_escalation_detected(result)
            _guard_agent_a2a_callback.on_escalation_detected(result)
        except Exception as e:
            print(f"[Guard Agent] A2A escalation notification failed: {e}")
    
    return result


def update_incident_level(incident_id: str, level: int, tool_context: ToolContext) -> dict:
    """
    Update the level of an existing incident in the database.
    
    Args:
        incident_id: The ID of the incident to update
        level: The new level to assign (1-5)
        tool_context: Context for accessing session state
        
    Returns:
        Dictionary containing update result
    """
    print(f"--- Tool: update_incident_level called for {incident_id} with level {level} ---")
    
    if not incident_id or not incident_id.strip():
        return {
            "action": "update_incident_level",
            "status": "error",
            "message": "Incident ID is required"
        }
    
    if not isinstance(level, int) or level < 1 or level > 5:
        return {
            "action": "update_incident_level", 
            "status": "error",
            "message": f"Invalid level {level}. Level must be between 1 and 5"
        }
    
    # Initialize database
    db = IncidentDatabase()
    
    try:
        # Update level directly in database
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.execute("""
                UPDATE incidents 
                SET level = ?, last_updated = ?
                WHERE id = ?
            """, (level, datetime.now().isoformat(), incident_id))
            
            if cursor.rowcount == 0:
                return {
                    "action": "update_incident_level",
                    "status": "error", 
                    "message": f"Incident {incident_id} not found"
                }
            
            conn.commit()
        
        level_description = get_bug_levels().get(level, "Unknown level")
        
        return {
            "action": "update_incident_level",
            "status": "success",
            "incident_id": incident_id,
            "new_level": level,
            "level_description": level_description,
            "message": f"Successfully updated incident {incident_id} to Level {level}: {level_description}"
        }
        
    except Exception as e:
        return {
            "action": "update_incident_level",
            "status": "error",
            "message": f"Database error: {str(e)}"
        }


# A2A Protocol Integration
class GuardAgentA2ACallback:
    """Callback handler for A2A protocol integration."""
    
    def __init__(self):
        self.classification_count = 0
        self.escalation_alerts = []
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
            
            # Perform classification
            classification_result = classify_input_level(user_input, mock_context)  # type: ignore
            
            if classification_result.get("action") == "classify_input":
                level = classification_result.get("level", 2)
                confidence = classification_result.get("confidence", 0.0)
                reasoning = classification_result.get("reasoning", "")
                
                print(f"[Guard Agent A2A] Classification result: Level {level} (confidence: {confidence})")
                print(f"[Guard Agent A2A] Reasoning: {reasoning}")
                
                # Update the incident level in the database
                update_result = update_incident_level(incident_id, level, mock_context)  # type: ignore
                
                if update_result.get("status") == "success":
                    print(f"[Guard Agent A2A] Successfully updated incident {incident_id} to level {level}")
                    
                    # Notify A2A protocol of classification completion
                    try:
                        notify_classification_complete({
                            "incident_id": incident_id,
                            "level": level,
                            "confidence": confidence,
                            "reasoning": reasoning,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        # Update internal metrics
                        self.on_classification_complete({
                            "level": level,
                            "confidence": confidence,
                            "timestamp": datetime.now().isoformat(),
                            "input": user_input
                        })
                        
                    except Exception as e:
                        print(f"[Guard Agent A2A] Error notifying classification completion: {e}")
                        
                else:
                    print(f"[Guard Agent A2A] Error updating incident level: {update_result.get('message', 'Unknown error')}")
                    
            else:
                print(f"[Guard Agent A2A] Classification failed: {classification_result.get('message', 'Unknown error')}")
                
        except Exception as e:
            print(f"[Guard Agent A2A] Error in classify_and_update_incident: {e}")
            import traceback
            traceback.print_exc()
    
    def on_classification_complete(self, result: Dict[str, Any]) -> None:
        """Called when a classification is completed."""
        self.classification_count += 1
        
        # Log high-priority classifications
        if result.get("level", 0) >= 4:
            self.escalation_alerts.append({
                "level": result["level"],
                "confidence": result["confidence"],
                "timestamp": result.get("timestamp"),
                "input_preview": result.get("input", "")[:50]
            })
    
    def on_escalation_detected(self, analysis: Dict[str, Any]) -> None:
        """Called when escalation pattern is detected."""
        if analysis.get("escalation_detected") or analysis.get("high_level_ratio", 0) > 0.5:
            # This could trigger notifications to human operators
            print(f"[A2A ALERT] Escalation detected: {analysis['recommendation']}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics for A2A reporting."""
        return {
            "total_classifications": self.classification_count,
            "escalation_alerts": len(self.escalation_alerts),
            "recent_alerts": self.escalation_alerts[-5:]  # Last 5 alerts
        }


class GuardAgent(Agent):
    """
    Guard Agent for classifying user inputs into bug severity levels.
    
    This agent intercepts user inputs and classifies them into one of five levels:
    Level 1: Simple FAQ questions
    Level 2: Common technical/account issues  
    Level 3: Unstructured but solvable problems
    Level 4: Security/fraud issues
    Level 5: Critical emergencies
    """
    
    def __init__(self):
        # Define agent tools
        tools = [
            classify_input_level,
            get_classification_history,
            analyze_escalation_pattern,
            update_incident_level,
        ]
        
        # Agent configuration
        agent_config = """
        You are a Guard Agent responsible for classifying user inputs into appropriate severity levels.
        
        Your primary functions:
        1. Analyze user input to determine the appropriate classification level (1-5)
        2. Provide confidence scores and reasoning for classifications
        3. Monitor for escalation patterns that might require human intervention
        4. Update incident levels in the database after bug reports are created
        5. Support A2A protocol communication for integration with other agents
        
        Classification Levels:
        - Level 1: Simple FAQ questions (how-to, information requests)
        - Level 2: Common technical/account issues (crashes, login problems)
        - Level 3: Unstructured but solvable problems (save corruption, gameplay issues)
        - Level 4: Security/fraud issues (hacking, stolen items)
        - Level 5: Critical emergencies (doxxing, legal issues, server outages)
        
        Workflow:
        1. When a user provides input, classify it using classify_input_level
        2. If a bug report ID is mentioned or provided, use update_incident_level to assign the appropriate level
        3. Monitor for escalation patterns using analyze_escalation_pattern
        
        Always be thorough in your analysis and provide clear reasoning for your classifications.
        If you detect patterns suggesting escalation, recommend appropriate action.
        """
        
        super().__init__(
            name="guard_agent",
            model="gemini-2.0-flash",
            description="Guard Agent for classifying user inputs into bug severity levels",
            instruction=agent_config,
            tools=tools
        )


# Global A2A callback handler for Guard Agent (outside the class)
_guard_agent_a2a_callback = GuardAgentA2ACallback()


def get_guard_agent_a2a_metrics() -> Dict[str, Any]:
    """Get A2A metrics for the Guard Agent."""
    return _guard_agent_a2a_callback.get_metrics() 