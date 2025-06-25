"""
Duplicate Detection Tool for Guard Agent

This tool acts as an agent-as-a-tool to intelligently detect duplicate issues
from the same user and provide detailed summaries for decision making.
"""

import sys
import os
import re
import sqlite3
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional
from google.adk.tools.tool_context import ToolContext

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database import IncidentDatabase


def detect_duplicate_issues(user_input: str, user_id: str, tool_context: ToolContext) -> dict:
    """
    Agent-as-a-tool to detect duplicate issues from the same user.
    This tool analyzes user input against existing open incidents to identify potential duplicates.
    
    Args:
        user_input: The user's current input describing their issue
        user_id: The user's ID to check against their previous incidents
        tool_context: Context for accessing session state
        
    Returns:
        Dictionary containing duplicate detection results
    """
    print(f"--- Tool: detect_duplicate_issues called for user {user_id} ---")
    
    if not user_input or not user_input.strip():
        return {
            "action": "detect_duplicate_issues",
            "is_duplicate": False,
            "message": "No input provided for duplicate detection"
        }
    
    if not user_id or not user_id.strip():
        return {
            "action": "detect_duplicate_issues",
            "is_duplicate": False,
            "message": "No user ID provided"
        }
    
    try:
        db = IncidentDatabase()
        
        # Get all open incidents for this user
        open_incidents = []
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM incidents 
                WHERE user_id = ? AND status IN ('Open', 'In Progress')
                ORDER BY date_created DESC
            """, (user_id,))
            
            for row in cursor.fetchall():
                open_incidents.append(dict(row))
        
        if not open_incidents:
            return {
                "action": "detect_duplicate_issues",
                "is_duplicate": False,
                "message": "No open incidents found for this user"
            }
        
        # Create a simplified hash of the current input for comparison
        current_input_hash = _create_issue_hash(user_input)
        
        duplicates_found = []
        
        for incident in open_incidents:
            existing_hash = _create_issue_hash(incident['description'])
            
            # Check for similarity using enhanced methods
            similarity_score = _calculate_enhanced_similarity(user_input.lower(), incident['description'].lower())
            
            # Lowered threshold to 50% and added exact hash matching
            if similarity_score > 0.5 or current_input_hash == existing_hash:
                duplicates_found.append({
                    "incident_id": incident['id'],
                    "description": incident['description'],
                    "date_created": incident['date_created'],
                    "status": incident['status'],
                    "level": incident['level'],
                    "similarity_score": round(similarity_score, 2)
                })
        
        if duplicates_found:
            # Find the most similar incident
            best_match = max(duplicates_found, key=lambda x: x['similarity_score'])
            
            # Create summary of the duplicate issue
            summary = f"""
            **Potential Duplicate Issue Detected**
            
            Your current request: "{user_input[:100]}..."
            
            Similar open incident found:
            - Incident ID: {best_match['incident_id']}
            - Original description: "{best_match['description'][:100]}..."
            - Status: {best_match['status']}
            - Level: {best_match['level']}
            - Created: {best_match['date_created'][:10]}
            - Similarity: {best_match['similarity_score']*100:.1f}%
            
            This appears to be related to your existing incident {best_match['incident_id']}. 
            Instead of creating a new report, would you like to:
            1. Update the existing incident with additional details
            2. Check the status of your previous report
            3. Proceed with a new report if this is actually a different issue
            """
            
            return {
                "action": "detect_duplicate_issues",
                "is_duplicate": True,
                "duplicate_incident_id": best_match['incident_id'],
                "similarity_score": best_match['similarity_score'],
                "summary": summary.strip(),
                "prevent_new_report": True,
                "message": f"Duplicate issue detected with {best_match['similarity_score']*100:.1f}% similarity to incident {best_match['incident_id']}"
            }
        
        return {
            "action": "detect_duplicate_issues",
            "is_duplicate": False,
            "message": "No duplicate issues detected - user can proceed with new report"
        }
        
    except Exception as e:
        print(f"[Duplicate Detection Tool] Error: {e}")
        return {
            "action": "detect_duplicate_issues",
            "is_duplicate": False,
            "message": f"Error during duplicate detection: {str(e)} - allowing new report"
        }


def _create_issue_hash(text: str) -> str:
    """Create a hash of the issue text for comparison."""
    # Normalize text: lowercase, remove extra spaces, basic words only
    normalized = re.sub(r'[^\w\s]', '', text.lower())
    normalized = ' '.join(normalized.split())
    
    # Create hash
    return hashlib.md5(normalized.encode()).hexdigest()[:8]


def _calculate_enhanced_similarity(text1: str, text2: str) -> float:
    """Calculate enhanced similarity between two texts with semantic patterns."""
    # Basic word overlap
    words1 = set(text1.split())
    words2 = set(text2.split())
    
    if not words1 or not words2:
        return 0.0
    
    # Base similarity using word overlap
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    base_similarity = len(intersection) / len(union) if union else 0.0
    
    # Semantic similarity patterns
    semantic_bonus = 0.0
    
    # Define semantic equivalence groups
    login_terms = {'login', 'signin', 'sign-in', 'log-in', 'access', 'authenticate'}
    password_terms = {'password', 'pass', 'pwd', 'reset', 'forgot'}
    account_terms = {'account', 'profile', 'user'}
    locked_terms = {'locked', 'blocked', 'disabled', 'suspended', 'frozen'}
    unable_terms = {'unable', 'cannot', 'can\'t', 'failed', 'error', 'issue', 'problem'}
    game_terms = {'game', 'play', 'gaming', 'playing'}
    
    semantic_groups = [login_terms, password_terms, account_terms, locked_terms, unable_terms, game_terms]
    
    # Check for semantic matches between groups
    for group in semantic_groups:
        group1_match = bool(words1.intersection(group))
        group2_match = bool(words2.intersection(group))
        
        if group1_match and group2_match:
            semantic_bonus += 0.3  # 30% bonus for each semantic group match
    
    # Common phrase patterns
    phrase_patterns = [
        (['cannot', 'login'], ['unable', 'access']),
        (['password', 'reset'], ['forgot', 'password']),
        (['account', 'locked'], ['cannot', 'access']),
        (['unable', 'play'], ['game', 'not', 'working']),
        (['doxxing', 'user'], ['user', 'information', 'exposed']),
    ]
    
    for pattern1, pattern2 in phrase_patterns:
        if all(word in text1 for word in pattern1) and all(word in text2 for word in pattern2):
            semantic_bonus += 0.4  # 40% bonus for phrase pattern matches
        elif all(word in text2 for word in pattern1) and all(word in text1 for word in pattern2):
            semantic_bonus += 0.4
    
    # Calculate final similarity (cap at 1.0)
    final_similarity = min(1.0, base_similarity + semantic_bonus)
    
    return final_similarity


def _calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts using simple word overlap."""
    words1 = set(text1.split())
    words2 = set(text2.split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0 