"""
Level Assignment Tool for Guard Agent

This tool is responsible for classifying user input and assigning appropriate 
severity levels (1-5) to incidents based on keyword and pattern analysis.
"""

import sys
import os
import re
import sqlite3
from datetime import datetime
from google.adk.tools.tool_context import ToolContext

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import get_bug_levels, get_default_level
from a2a_integration import notify_classification_complete
from database import IncidentDatabase


def assign_incident_level(user_input: str, incident_id: str, tool_context: ToolContext) -> dict:
    """
    Dedicated tool to assign incident levels based on user input classification.
    This tool contains all the classification logic and database update functionality.
    
    Args:
        user_input: The user's input text to classify
        incident_id: The incident ID to update with the classified level
        tool_context: Context for accessing session state
        
    Returns:
        Dictionary containing level assignment result
    """
    print(f"--- Tool: assign_incident_level called for incident {incident_id} ---")
    
    if not user_input or not user_input.strip():
        return {
            "action": "assign_incident_level",
            "status": "error",
            "message": "No user input provided for classification"
        }
    
    if not incident_id or not incident_id.strip():
        return {
            "action": "assign_incident_level",
            "status": "error",
            "message": "No incident ID provided"
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
        final_level = get_default_level()
        confidence = 0.3
        reasoning = "No clear indicators found, defaulting to level 2"
    else:
        final_level = max(level_scores.keys(), key=lambda k: level_scores[k])
        confidence = min(max_score / 5.0, 1.0)
        reasoning = f"Classified based on keyword and pattern analysis (score: {max_score})"
    
    # Update the incident level in the database
    try:
        db = IncidentDatabase()
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.execute("""
                UPDATE incidents 
                SET level = ?, last_updated = ?
                WHERE id = ?
            """, (final_level, datetime.now().isoformat(), incident_id))
            
            if cursor.rowcount == 0:
                return {
                    "action": "assign_incident_level",
                    "status": "error",
                    "message": f"Incident {incident_id} not found"
                }
            
            conn.commit()
        
        level_description = get_bug_levels().get(final_level, "Unknown level")
        
        # Store classification result
        classification_data = {
            "incident_id": incident_id,
            "level": final_level,
            "confidence": confidence,
            "reasoning": reasoning,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add to classification history
        history = tool_context.state.get("classification_history", [])
        history.append(classification_data)
        tool_context.state["classification_history"] = history[-20:]
        
        # Notify A2A protocol
        try:
            notify_classification_complete(classification_data)
        except Exception as e:
            print(f"[Level Assignment Tool] A2A notification failed: {e}")
        
        return {
            "action": "assign_incident_level",
            "status": "success",
            "incident_id": incident_id,
            "level": final_level,
            "confidence": round(confidence, 2),
            "reasoning": reasoning,
            "level_description": level_description,
            "message": f"Successfully assigned Level {final_level} to incident {incident_id}: {level_description}"
        }
        
    except Exception as e:
        return {
            "action": "assign_incident_level",
            "status": "error",
            "message": f"Database error: {str(e)}"
        } 