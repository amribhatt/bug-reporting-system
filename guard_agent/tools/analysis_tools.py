"""
Analysis Tools for Guard Agent

This module contains tools for analyzing classification patterns and retrieving
historical data for escalation detection and reporting.
"""

import sys
import os
from datetime import datetime
from typing import Dict, Any
from google.adk.tools.tool_context import ToolContext

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from a2a_integration import notify_escalation_detected


def get_classification_history(tool_context: ToolContext) -> dict:
    """Get the classification history from session state."""
    print("--- Tool: get_classification_history called ---")
    
    history = tool_context.state.get("classification_history", [])
    
    if not history:
        return {
            "action": "get_classification_history",
            "history": [],
            "count": 0,
            "message": "No classification history found"
        }
    
    return {
        "action": "get_classification_history", 
        "history": history,
        "count": len(history),
        "message": f"Retrieved {len(history)} classification records"
    }


def analyze_escalation_pattern(tool_context: ToolContext) -> dict:
    """Analyze recent classifications for escalation patterns."""
    print("--- Tool: analyze_escalation_pattern called ---")
    
    history = tool_context.state.get("classification_history", [])
    
    if len(history) < 3:
        return {
            "action": "analyze_escalation",
            "escalation_detected": False,
            "message": "Insufficient history for escalation analysis"
        }
    
    # Analyze recent classifications (last 10)
    recent_history = history[-10:]
    levels = [item.get("level", 2) for item in recent_history]
    
    escalation_detected = False
    
    # Check for escalation patterns
    if len(levels) >= 3:
        # Check if last 3 classifications show increasing severity
        last_three = levels[-3:]
        if last_three == sorted(last_three) and last_three[-1] > last_three[0]:
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
        except Exception as e:
            print(f"[Analysis Tools] A2A escalation notification failed: {e}")
    
    return result 