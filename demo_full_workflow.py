#!/usr/bin/env python3

import sys
from database import IncidentDatabase
from guard_agent.agent import GuardAgent, update_incident_level

def demo_full_workflow():
    """Demonstrate the full workflow of creating and updating incidents."""
    
    print("=== Demo: Bug Reporting + Guard Agent Workflow ===\n")
    
    # Clear any existing data
    db = IncidentDatabase()
    try:
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
            conn.execute("DELETE FROM incidents WHERE user_id LIKE 'demo_%'")
            conn.commit()
        print("✓ Cleaned up demo data")
    except Exception as e:
        print(f"Note: {e}")
    
    # Initialize agents
    guard_agent = GuardAgent()
    print("✓ Guard Agent initialized")
    
    # Test cases with different severities
    test_cases = [
        {
            "input": "How do I reset my password?",
            "user_id": "demo_user1", 
            "expected_level": 1
        },
        {
            "input": "The game keeps crashing when I try to load my save file",
            "user_id": "demo_user2",
            "expected_level": 2
        },
        {
            "input": "My progress was completely lost and I think my save is corrupted",
            "user_id": "demo_user3", 
            "expected_level": 3
        },
        {
            "input": "Someone hacked my account and stole all my items",
            "user_id": "demo_user4",
            "expected_level": 4
        },
        {
            "input": "URGENT: The entire server is down and customers are angry",
            "user_id": "demo_user5",
            "expected_level": 5
        }
    ]
    
    print(f"\n--- Processing {len(test_cases)} test cases ---")
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. Input: \"{case['input']}\"")
        
        # Step 1: Guard Agent classifies the input
        class MockToolContext:
            def __init__(self):
                self.state = {}
        
        mock_context = MockToolContext()
        
        # Import and call the classification function directly
        from guard_agent.agent import classify_input_level
        classification = classify_input_level(case['input'], mock_context)
        predicted_level = classification['level']
        print(f"   Guard Agent Classification: Level {predicted_level} (confidence: {classification['confidence']})")
        
        # Step 2: Simulate bug report creation (simplified)
        incident = db.create_incident(
            user_id=case['user_id'],
            user_name=f"Demo User {i}",
            user_email=f"demo{i}@example.com", 
            category="Software",
            description=case['input'],
            date_observed="2024-01-15",
            level=2  # Default level from Bug Reporting Agent
        )
        print(f"   Bug Report Created: {incident['id']} (initial level: {incident['level']})")
        
        # Step 3: Guard Agent updates the incident level
        update_result = update_incident_level(
            incident_id=incident['id'],
            level=predicted_level,
            tool_context=mock_context
        )
        
        if update_result['status'] == 'success':
            print(f"   Level Updated: {incident['id']} → Level {predicted_level}")
        else:
            print(f"   Update Failed: {update_result['message']}")
        
        # Step 4: Verify the update
        updated_incident = db.get_incident_by_id(incident['id'], case['user_id'])
        if updated_incident and updated_incident['level'] == predicted_level:
            print(f"   ✓ Verification: Level correctly set to {updated_incident['level']}")
        else:
            print(f"   ✗ Verification failed")
    
    # Show final database state
    print(f"\n--- Final Database State ---")
    all_incidents = db.get_all_incidents()
    demo_incidents = [inc for inc in all_incidents if inc['user_id'].startswith('demo_')]
    
    for inc in demo_incidents:
        print(f"  {inc['id']}: Level {inc['level']} - \"{inc['description'][:50]}...\"")
    
    print(f"\n✓ Demo completed successfully!")
    print(f"Created and processed {len(demo_incidents)} incidents with Guard Agent level updates.")
    
    return True

if __name__ == "__main__":
    success = demo_full_workflow()
    sys.exit(0 if success else 1) 