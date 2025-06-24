"""
A2A Protocol Integration Module

This module provides basic A2A (Agent-to-Agent) protocol support for communication
between the Guard Agent and Bug Reporting Agent via callbacks and events.
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import json
from dataclasses import dataclass
from enum import Enum
import asyncio


class A2AEventType(Enum):
    """Types of A2A events that can be triggered."""
    CLASSIFICATION_COMPLETE = "classification_complete"
    ESCALATION_DETECTED = "escalation_detected"
    BUG_REPORT_CREATED = "bug_report_created"
    METRICS_UPDATE = "metrics_update"


@dataclass
class A2AEvent:
    """Represents an A2A protocol event."""
    event_type: A2AEventType
    timestamp: str
    source_agent: str
    target_agent: Optional[str]
    payload: Dict[str, Any]
    correlation_id: Optional[str] = None


class A2AEventBus:
    """Simple event bus for A2A communication."""
    
    def __init__(self):
        self.event_history: List[A2AEvent] = []
        self.subscribers: Dict[A2AEventType, List[Callable]] = {}
        self.metrics = {
            "total_events": 0,
            "events_by_type": {},
            "last_event_time": None
        }
    
    def subscribe(self, event_type: A2AEventType, callback: Callable[[A2AEvent], None]) -> None:
        """Subscribe to a specific event type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
    
    def publish(self, event: A2AEvent) -> None:
        """Publish an event to all subscribers."""
        # Store event in history
        self.event_history.append(event)
        
        # Update metrics
        self.metrics["total_events"] += 1
        self.metrics["last_event_time"] = event.timestamp
        
        event_type_str = event.event_type.value
        if event_type_str not in self.metrics["events_by_type"]:
            self.metrics["events_by_type"][event_type_str] = 0
        self.metrics["events_by_type"][event_type_str] += 1
        
        # Notify subscribers
        if event.event_type in self.subscribers:
            for callback in self.subscribers[event.event_type]:
                try:
                    callback(event)
                except Exception as e:
                    print(f"[A2A] Error in callback for {event.event_type}: {e}")
    
    def get_events(self, event_type: Optional[A2AEventType] = None, 
                   limit: Optional[int] = None) -> List[A2AEvent]:
        """Get events, optionally filtered by type and limited in count."""
        events = self.event_history
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if limit:
            events = events[-limit:]  # Get most recent events
        
        return events
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get event bus metrics."""
        return self.metrics.copy()


class A2AProtocolHandler:
    """Handles A2A protocol communication between agents."""
    
    def __init__(self):
        self.event_bus = A2AEventBus()
        self.agent_registry: Dict[str, Dict[str, Any]] = {}
        self.guard_agent_callback = None  # Will be set by the agent callback handler
        self.setup_default_subscriptions()
    
    def register_agent(self, agent_name: str, agent_info: Dict[str, Any]) -> None:
        """Register an agent in the A2A protocol."""
        self.agent_registry[agent_name] = {
            "name": agent_name,
            "registered_at": datetime.now().isoformat(),
            **agent_info
        }
    
    def register_guard_agent_callback(self, callback_handler) -> None:
        """Register the Guard agent callback handler for actual agent invocation."""
        self.guard_agent_callback = callback_handler
        print("[A2A] Guard Agent callback handler registered")
    
    def setup_default_subscriptions(self) -> None:
        """Setup default event subscriptions for cross-agent communication."""
        
        # Bug Reporting Agent listens for classification results
        def on_classification_complete(event: A2AEvent) -> None:
            """Handle classification completion from Guard Agent."""
            print(f"[A2A] Bug Reporting Agent received classification: Level {event.payload.get('level')}")
            # Classification result received - no action needed as Guard Agent will update directly
        
        # Guard Agent listens for bug report creation and triggers actual classification
        def on_bug_report_created(event: A2AEvent) -> None:
            """Handle bug report creation notification and trigger Guard Agent."""
            bug_id = event.payload.get('bug_id', 'unknown')
            user_input = event.payload.get('user_input', '')
            
            print(f"[A2A] Guard Agent notified: Bug report {bug_id} created - triggering classification")
            
            # Actually invoke the Guard Agent to classify and update
            if self.guard_agent_callback:
                try:
                    self.guard_agent_callback.classify_and_update_incident(bug_id, user_input)
                    print(f"[A2A] Guard Agent successfully processed classification for {bug_id}")
                except Exception as e:
                    print(f"[A2A] Error invoking Guard Agent for {bug_id}: {e}")
            else:
                print(f"[A2A] Warning: Guard Agent callback not registered, cannot classify {bug_id}")
        
        # Setup escalation monitoring
        def on_escalation_detected(event: A2AEvent) -> None:
            """Handle escalation detection."""
            recommendation = event.payload.get('recommendation', 'Unknown')
            print(f"[A2A] ESCALATION ALERT: {recommendation}")
            # In a full implementation, this would trigger alerts to human operators
        
        # Register subscriptions
        self.event_bus.subscribe(A2AEventType.CLASSIFICATION_COMPLETE, on_classification_complete)
        self.event_bus.subscribe(A2AEventType.BUG_REPORT_CREATED, on_bug_report_created)
        self.event_bus.subscribe(A2AEventType.ESCALATION_DETECTED, on_escalation_detected)
    
    def publish_classification_result(self, source_agent: str, classification_result: Dict[str, Any]) -> None:
        """Publish a classification result from Guard Agent."""
        event = A2AEvent(
            event_type=A2AEventType.CLASSIFICATION_COMPLETE,
            timestamp=datetime.now().isoformat(),
            source_agent=source_agent,
            target_agent="bug_reporting_agent",
            payload=classification_result
        )
        self.event_bus.publish(event)
    
    def publish_bug_report_created(self, source_agent: str, bug_report: Dict[str, Any]) -> None:
        """Publish a bug report creation event."""
        event = A2AEvent(
            event_type=A2AEventType.BUG_REPORT_CREATED,
            timestamp=datetime.now().isoformat(),
            source_agent=source_agent,
            target_agent="guard_agent",
            payload=bug_report
        )
        self.event_bus.publish(event)
    
    def publish_escalation_alert(self, source_agent: str, escalation_data: Dict[str, Any]) -> None:
        """Publish an escalation alert."""
        event = A2AEvent(
            event_type=A2AEventType.ESCALATION_DETECTED,
            timestamp=datetime.now().isoformat(),
            source_agent=source_agent,
            target_agent=None,  # Broadcast to all
            payload=escalation_data
        )
        self.event_bus.publish(event)
    
    def get_agent_metrics(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics for a specific agent or all agents."""
        if agent_name:
            agent_events = [e for e in self.event_bus.event_history 
                          if e.source_agent == agent_name or e.target_agent == agent_name]
            return {
                "agent_name": agent_name,
                "total_events": len(agent_events),
                "events_by_type": {},
                "registered": agent_name in self.agent_registry
            }
        else:
            return {
                "registered_agents": list(self.agent_registry.keys()),
                "total_events": self.event_bus.metrics["total_events"],
                "event_bus_metrics": self.event_bus.get_metrics()
            }
    
    def get_communication_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent A2A communication log."""
        recent_events = self.event_bus.get_events(limit=limit)
        return [
            {
                "timestamp": event.timestamp,
                "event_type": event.event_type.value,
                "source": event.source_agent,
                "target": event.target_agent,
                "payload_summary": str(event.payload)[:100] + "..." if len(str(event.payload)) > 100 else str(event.payload)
            }
            for event in recent_events
        ]


# Global A2A protocol handler instance
a2a_handler = A2AProtocolHandler()


def get_a2a_handler() -> A2AProtocolHandler:
    """Get the global A2A protocol handler."""
    return a2a_handler


def initialize_a2a_agents() -> None:
    """Initialize A2A protocol for both agents."""
    # Register agents
    a2a_handler.register_agent("guard_agent", {
        "type": "classifier",
        "capabilities": ["input_classification", "escalation_detection"],
        "levels": [1, 2, 3, 4, 5]
    })
    
    a2a_handler.register_agent("bug_reporting_agent", {
        "type": "reporter",
        "capabilities": ["bug_report_creation", "persistent_storage"],
        "categories": ["Software", "Platform", "Account", "Other"]
    })
    
    print("[A2A] Protocol initialized with Guard Agent and Bug Reporting Agent")


# Convenience functions for agents to use
def notify_classification_complete(classification_result: Dict[str, Any]) -> None:
    """Convenience function for Guard Agent to notify classification completion."""
    a2a_handler.publish_classification_result("guard_agent", classification_result)


def notify_bug_report_created(bug_report: Dict[str, Any]) -> None:
    """Convenience function for Bug Reporting Agent to notify bug report creation."""
    a2a_handler.publish_bug_report_created("bug_reporting_agent", bug_report)


def notify_escalation_detected(escalation_data: Dict[str, Any]) -> None:
    """Convenience function for Guard Agent to notify escalation detection."""
    a2a_handler.publish_escalation_alert("guard_agent", escalation_data)


def register_guard_agent_callback(callback_handler) -> None:
    """Register the Guard agent callback handler."""
    a2a_handler.register_guard_agent_callback(callback_handler) 